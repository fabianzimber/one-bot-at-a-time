"""Executes tool calls returned by the LLM."""

import asyncio
import logging
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from shared.models import ToolCall, ToolResult
from shared.models.tools import ToolStatus

logger = logging.getLogger(__name__)
HONORIFICS = {"frau", "herr", "mr", "mrs", "ms"}


class ToolExecutor:
    """Dispatches tool calls to the appropriate service."""

    def __init__(
        self,
        rag_service_url: str,
        hr_service_url: str,
        internal_api_key: str = "",
        rag_service_share_token: str = "",
        hr_service_share_token: str = "",
    ) -> None:
        self.rag_service_url = rag_service_url
        self.hr_service_url = hr_service_url
        self.internal_api_key = internal_api_key
        self.rag_service_share_token = rag_service_share_token
        self.hr_service_share_token = hr_service_share_token
        self._client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {"x-request-id": "tool-executor"}
        if self.internal_api_key:
            headers["x-internal-api-key"] = self.internal_api_key
        return headers

    @staticmethod
    def _build_url(base_url: str, path: str, share_token: str = "") -> str:
        parts = urlsplit(f"{base_url.rstrip('/')}{path}")
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        if share_token:
            query["_vercel_share"] = share_token
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("error")
            if isinstance(detail, str) and detail:
                return detail

        return response.text or response.reason_phrase or "Unknown error"

    @staticmethod
    def _normalize_employee_name(employee_name: str) -> str:
        normalized = re.sub(r"[^\wÄÖÜäöüß-]+", " ", employee_name, flags=re.UNICODE)
        parts = [part for part in normalized.casefold().split() if part not in HONORIFICS]
        return " ".join(parts)

    @staticmethod
    def _payload_summary(payload: object) -> dict[str, object]:
        if isinstance(payload, dict):
            if isinstance(payload.get("results"), list):
                return {"result_count": len(payload["results"])}
            return {"keys": sorted(payload.keys())[:5]}
        if isinstance(payload, list):
            return {"result_count": len(payload)}
        return {"payload_type": type(payload).__name__}

    def _build_hr_not_found_result(
        self,
        *,
        tool_call: ToolCall,
        action: str,
        employee_id: str = "",
        employee_name: str = "",
        response: httpx.Response | None = None,
        detail: str | None = None,
    ) -> ToolResult:
        message = detail
        if message is None and response is not None:
            message = self._extract_error_detail(response)
        if message is None:
            message = "Employee not found"

        return ToolResult(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            status=ToolStatus.ERROR,
            data={
                "kind": "hr_not_found",
                "action": action,
                "employee_id": employee_id,
                "employee_name": employee_name,
                "detail": message,
            },
            error=message,
        )

    async def _resolve_employee_reference(self, employee_id: str, employee_name: str) -> tuple[str, str]:
        if employee_id:
            return employee_id, employee_name

        if not employee_name:
            return "", ""

        response = await self._client.get(
            self._build_url(self.hr_service_url, "/api/v1/employees", self.hr_service_share_token),
            headers=self._headers(),
        )
        response.raise_for_status()

        normalized_target = self._normalize_employee_name(employee_name)
        if not normalized_target:
            return "", employee_name

        exact_matches: list[tuple[str, str]] = []
        partial_matches: list[tuple[str, str]] = []
        for employee in response.json():
            full_name = f"{employee['first_name']} {employee['last_name']}"
            normalized_full_name = self._normalize_employee_name(full_name)
            first_name = self._normalize_employee_name(employee["first_name"])
            last_name = self._normalize_employee_name(employee["last_name"])
            if normalized_target in {normalized_full_name, first_name, last_name}:
                exact_matches.append((employee["id"], full_name))
                continue
            if normalized_target in normalized_full_name:
                partial_matches.append((employee["id"], full_name))

        if len(exact_matches) == 1:
            return exact_matches[0]
        if len(partial_matches) == 1:
            return partial_matches[0]

        return "", employee_name

    async def get_hr_showcase(self, limit: int = 12) -> dict:
        """Return a compact overview of seeded HR mock data for the frontend."""
        employees_response = await self._client.get(
            self._build_url(self.hr_service_url, "/api/v1/employees", self.hr_service_share_token),
            headers=self._headers(),
        )
        employees_response.raise_for_status()

        employees = employees_response.json()
        limited_employees = employees[: max(1, min(limit, len(employees)))]
        employee_lookup = {
            employee["id"]: f"{employee['first_name']} {employee['last_name']}" for employee in employees
        }

        async def enrich_employee(employee: dict) -> dict:
            vacation_url = self._build_url(
                self.hr_service_url,
                f"/api/v1/employees/{employee['id']}/vacation",
                self.hr_service_share_token,
            )
            salary_url = self._build_url(
                self.hr_service_url,
                f"/api/v1/employees/{employee['id']}/salary",
                self.hr_service_share_token,
            )

            vacation_response, salary_response = await asyncio.gather(
                self._client.get(vacation_url, headers=self._headers()),
                self._client.get(salary_url, headers=self._headers()),
            )

            vacation = vacation_response.json() if vacation_response.is_success else {}
            salary = salary_response.json() if salary_response.is_success else {}

            return {
                "employee_id": employee["id"],
                "name": f"{employee['first_name']} {employee['last_name']}",
                "department": employee["department"],
                "position": employee["position"],
                "manager_name": employee_lookup.get(employee.get("manager_id") or "", "Executive"),
                "remaining_vacation_days": vacation.get("remaining_days"),
                "pay_grade": salary.get("pay_grade"),
                "gross_annual": salary.get("gross_annual"),
                "currency": salary.get("currency", "EUR"),
            }

        rows = await asyncio.gather(*(enrich_employee(employee) for employee in limited_employees))
        departments = sorted({employee["department"] for employee in employees})

        return {
            "rows": rows,
            "employee_count": len(employees),
            "departments": departments,
        }

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call and return the result."""
        logger.info("Executing tool", extra={"tool": tool_call.name, "id": tool_call.id})

        try:
            if tool_call.name == "search_documents":
                response = await self._client.post(
                    self._build_url(
                        self.rag_service_url,
                        "/api/v1/search",
                        self.rag_service_share_token,
                    ),
                    json={
                        "query": tool_call.arguments.get("query", ""),
                        "top_k": int(tool_call.arguments.get("top_k", 5)),
                    },
                    headers=self._headers(),
                )
                response.raise_for_status()
                return ToolResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    status=ToolStatus.SUCCESS,
                    data=response.json(),
                )

            if tool_call.name != "query_hr_system":
                return ToolResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    status=ToolStatus.ERROR,
                    error="Unknown tool",
                )

            action = tool_call.arguments.get("action", "")
            employee_id = tool_call.arguments.get("employee_id", "")
            employee_name = tool_call.arguments.get("employee_name", "")
            parameters = tool_call.arguments.get("parameters", {})

            if action in {"vacation_balance", "salary_info", "time_tracking"} or (
                action == "employee_lookup" and (employee_id or employee_name)
            ):
                employee_id, employee_name = await self._resolve_employee_reference(employee_id, employee_name)
                if not employee_id:
                    return self._build_hr_not_found_result(
                        tool_call=tool_call,
                        action=action,
                        employee_name=employee_name,
                        detail=f"Employee {employee_name} not found",
                    )

            if action == "vacation_balance":
                path = f"/api/v1/employees/{employee_id}/vacation"
                response = await self._client.get(
                    self._build_url(self.hr_service_url, path, self.hr_service_share_token),
                    params={"year": parameters.get("year")} if parameters.get("year") else None,
                    headers=self._headers(),
                )
            elif action == "salary_info":
                response = await self._client.get(
                    self._build_url(
                        self.hr_service_url,
                        f"/api/v1/employees/{employee_id}/salary",
                        self.hr_service_share_token,
                    ),
                    headers=self._headers(),
                )
            elif action == "employee_lookup":
                if employee_id:
                    response = await self._client.get(
                        self._build_url(
                            self.hr_service_url,
                            f"/api/v1/employees/{employee_id}",
                            self.hr_service_share_token,
                        ),
                        headers=self._headers(),
                    )
                else:
                    response = await self._client.get(
                        self._build_url(self.hr_service_url, "/api/v1/employees", self.hr_service_share_token),
                        params={"department": parameters.get("department")} if parameters.get("department") else None,
                        headers=self._headers(),
                    )
            elif action == "org_chart":
                department = parameters.get("department")
                path = f"/api/v1/org/{department}" if department else "/api/v1/org"
                response = await self._client.get(
                    self._build_url(self.hr_service_url, path, self.hr_service_share_token),
                    headers=self._headers(),
                )
            elif action == "time_tracking":
                response = await self._client.get(
                    self._build_url(
                        self.hr_service_url,
                        f"/api/v1/employees/{employee_id}/timetracking",
                        self.hr_service_share_token,
                    ),
                    params={key: value for key, value in parameters.items() if key in {"start", "end"}},
                    headers=self._headers(),
                )
            else:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    status=ToolStatus.ERROR,
                    error=f"Unsupported HR action: {action}",
                )

            if response.status_code == 404:
                return self._build_hr_not_found_result(
                    tool_call=tool_call,
                    action=action,
                    employee_id=employee_id,
                    employee_name=employee_name,
                    response=response,
                )

            response.raise_for_status()
            payload = response.json()
            logger.info(
                "Tool execution succeeded",
                extra={"tool": tool_call.name, "action": action, **self._payload_summary(payload)},
            )
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                status=ToolStatus.SUCCESS,
                data=payload,
            )
        except httpx.TimeoutException:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                status=ToolStatus.TIMEOUT,
                error="Tool request timed out",
            )
        except httpx.HTTPError as exc:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                status=ToolStatus.ERROR,
                error=str(exc),
            )
