"""Tests for tool execution and HR name resolution."""

from urllib.parse import urlsplit

import httpx
import pytest

from chat_orchestrator.services.tool_executor import ToolExecutor
from shared.models import ToolCall
from shared.models.tools import ToolStatus


def build_response(
    method: str,
    url: str,
    *,
    status_code: int = 200,
    json_data: object | None = None,
    text: str = "",
) -> httpx.Response:
    request = httpx.Request(method, url)
    if json_data is not None:
        return httpx.Response(status_code, request=request, json=json_data)
    return httpx.Response(status_code, request=request, text=text)


def exact_path(expected_suffix: str):
    def matcher(url: str, _kwargs: dict) -> bool:
        return urlsplit(url).path.endswith(expected_suffix)

    return matcher


class StubClient:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, object]] = []
        self.requests: list[tuple[str, str, dict]] = []

    def add_route(self, method: str, matcher: object, result: object) -> None:
        self.routes.append((method, matcher, result))

    async def get(self, url: str, **kwargs: dict) -> httpx.Response:
        return self._dispatch("GET", url, kwargs)

    async def post(self, url: str, **kwargs: dict) -> httpx.Response:
        return self._dispatch("POST", url, kwargs)

    async def aclose(self) -> None:
        return None

    def _dispatch(self, method: str, url: str, kwargs: dict) -> httpx.Response:
        self.requests.append((method, url, kwargs))
        for route_method, matcher, result in self.routes:
            matches = matcher(url, kwargs) if callable(matcher) else matcher in url
            if route_method != method or not matches:
                continue

            current = result.pop(0) if isinstance(result, list) else result
            if callable(current) and not isinstance(current, httpx.Response):
                current = current(url, kwargs)
            if isinstance(current, Exception):
                raise current
            assert isinstance(current, httpx.Response)
            return current

        raise AssertionError(f"No stubbed response for {method} {url}")


def make_executor() -> ToolExecutor:
    return ToolExecutor(
        rag_service_url="https://rag.example",
        hr_service_url="https://hr.example",
        internal_api_key="internal-secret",
        rag_service_share_token="rag-share",
        hr_service_share_token="hr-share",
    )


@pytest.mark.asyncio
async def test_build_url_and_headers_include_internal_auth() -> None:
    executor = make_executor()

    url = executor._build_url("https://hr.example", "/api/v1/employees", "share-token")

    assert url == "https://hr.example/api/v1/employees?_vercel_share=share-token"
    assert executor._headers()["x-internal-api-key"] == "internal-secret"


@pytest.mark.asyncio
async def test_resolve_employee_reference_supports_honorific_and_first_name() -> None:
    executor = make_executor()
    client = StubClient()
    employees = [
        {"id": "emp-001", "first_name": "Felicitas", "last_name": "Dowerg"},
        {"id": "emp-007", "first_name": "Rosalie", "last_name": "Ritter"},
    ]
    client.add_route(
        "GET",
        exact_path("/api/v1/employees"),
        lambda *_: build_response("GET", "https://hr.example/api/v1/employees", json_data=employees),
    )
    executor._client = client

    last_name_match = await executor._resolve_employee_reference("", "Frau Dowerg")
    first_name_match = await executor._resolve_employee_reference("", "Rosalie")

    assert last_name_match == ("emp-001", "Felicitas Dowerg")
    assert first_name_match == ("emp-007", "Rosalie Ritter")


@pytest.mark.asyncio
async def test_execute_search_documents_returns_success_payload() -> None:
    executor = make_executor()
    client = StubClient()
    client.add_route(
        "POST",
        "/api/v1/search",
        build_response(
            "POST",
            "https://rag.example/api/v1/search",
            json_data={"results": [{"chunk_text": "Homeoffice ist erlaubt.", "source_file": "policy.md"}]},
        ),
    )
    executor._client = client

    result = await executor.execute(
        ToolCall(id="search-1", name="search_documents", arguments={"query": "Homeoffice", "top_k": 3})
    )

    assert result.status == ToolStatus.SUCCESS
    assert result.data["results"][0]["source_file"] == "policy.md"


@pytest.mark.asyncio
async def test_execute_hr_vacation_uses_resolved_employee_name() -> None:
    executor = make_executor()
    client = StubClient()
    employees = [{"id": "emp-007", "first_name": "Rosalie", "last_name": "Ritter"}]
    client.add_route(
        "GET",
        exact_path("/api/v1/employees"),
        lambda *_: build_response("GET", "https://hr.example/api/v1/employees", json_data=employees),
    )
    client.add_route(
        "GET",
        exact_path("/api/v1/employees/emp-007/vacation"),
        build_response(
            "GET",
            "https://hr.example/api/v1/employees/emp-007/vacation",
            json_data={"employee_id": "emp-007", "remaining_days": 24},
        ),
    )
    executor._client = client

    result = await executor.execute(
        ToolCall(
            id="tool-1",
            name="query_hr_system",
            arguments={"action": "vacation_balance", "employee_name": "Rosalie"},
        )
    )

    assert result.status == ToolStatus.SUCCESS
    assert result.data["remaining_days"] == 24
    assert any("/api/v1/employees/emp-007/vacation" in url for _, url, _ in client.requests)


@pytest.mark.asyncio
async def test_execute_hr_returns_not_found_for_unknown_name() -> None:
    executor = make_executor()
    client = StubClient()
    employees = [{"id": "emp-001", "first_name": "Felicitas", "last_name": "Dowerg"}]
    client.add_route(
        "GET",
        exact_path("/api/v1/employees"),
        lambda *_: build_response("GET", "https://hr.example/api/v1/employees", json_data=employees),
    )
    executor._client = client

    result = await executor.execute(
        ToolCall(
            id="tool-2",
            name="query_hr_system",
            arguments={"action": "salary_info", "employee_name": "Niemand"},
        )
    )

    assert result.status == ToolStatus.ERROR
    assert result.data["kind"] == "hr_not_found"
    assert result.data["employee_name"] == "Niemand"


@pytest.mark.asyncio
async def test_execute_handles_timeout_and_unknown_actions() -> None:
    executor = make_executor()
    client = StubClient()
    client.add_route("POST", "/api/v1/search", httpx.TimeoutException("timed out"))
    executor._client = client

    timeout_result = await executor.execute(
        ToolCall(id="search-2", name="search_documents", arguments={"query": "timeout"})
    )
    unknown_tool_result = await executor.execute(ToolCall(id="tool-3", name="unknown", arguments={}))
    unsupported_action_result = await executor.execute(
        ToolCall(id="tool-4", name="query_hr_system", arguments={"action": "unsupported"})
    )

    assert timeout_result.status == ToolStatus.TIMEOUT
    assert unknown_tool_result.error == "Unknown tool"
    assert unsupported_action_result.error == "Unsupported HR action: unsupported"


@pytest.mark.asyncio
async def test_get_hr_showcase_returns_named_rows() -> None:
    executor = make_executor()
    client = StubClient()
    employees = [
        {
            "id": "emp-001",
            "first_name": "Felicitas",
            "last_name": "Dowerg",
            "department": "HR",
            "position": "People Lead",
            "manager_id": None,
        },
        {
            "id": "emp-007",
            "first_name": "Rosalie",
            "last_name": "Ritter",
            "department": "IT",
            "position": "Software Engineer",
            "manager_id": "emp-001",
        },
    ]
    client.add_route(
        "GET",
        exact_path("/api/v1/employees"),
        lambda *_: build_response("GET", "https://hr.example/api/v1/employees", json_data=employees),
    )
    client.add_route(
        "GET",
        exact_path("/vacation"),
        lambda url, _: build_response(
            "GET",
            url,
            json_data={"remaining_days": 21 if "emp-001" in url else 26},
        ),
    )
    client.add_route(
        "GET",
        exact_path("/salary"),
        lambda url, _: build_response(
            "GET",
            url,
            json_data={
                "pay_grade": "E5" if "emp-001" in url else "E3",
                "gross_annual": 98000 if "emp-001" in url else 64000,
                "currency": "EUR",
            },
        ),
    )
    executor._client = client

    showcase = await executor.get_hr_showcase(limit=2)

    assert showcase["employee_count"] == 2
    assert showcase["departments"] == ["HR", "IT"]
    assert showcase["rows"][1]["name"] == "Rosalie Ritter"
    assert showcase["rows"][1]["manager_name"] == "Felicitas Dowerg"
