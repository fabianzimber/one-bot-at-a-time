"""Executes tool calls returned by the LLM."""

import json
import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from shared.models import ToolCall, ToolResult
from shared.models.tools import ToolStatus

logger = logging.getLogger(__name__)


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
            employee_id = tool_call.arguments.get("employee_id", "emp-001")
            parameters = tool_call.arguments.get("parameters", {})

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

            response.raise_for_status()
            payload = response.json()
            logger.info("Tool execution succeeded", extra={"tool": tool_call.name, "payload": json.dumps(payload)})
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
