"""Chat endpoints — the main user-facing API."""

import logging

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from chat_orchestrator.runtime import ensure_runtime_ready
from shared.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class MockDataRow(BaseModel):
    employee_id: str
    name: str
    department: str
    position: str
    manager_name: str
    remaining_vacation_days: int | None = None
    pay_grade: str | None = None
    gross_annual: float | None = None
    currency: str = "EUR"


class MockDataOverview(BaseModel):
    employee_count: int
    departments: list[str]
    rows: list[MockDataRow]


class ChatStreamRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    conversation_id: str | None = None


def _client_key(request: Request, suffix: str = "") -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    forwarded_ip = forwarded_for.split(",", 1)[0].strip()
    base = forwarded_ip or (request.client.host if request.client is not None else "unknown")
    return f"{base}:{suffix}" if suffix else base


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, fastapi_request: Request) -> ChatResponse:
    """Process a chat message — routes to appropriate tools via LLM."""
    await ensure_runtime_ready(fastapi_request.app)
    client_key = _client_key(fastapi_request)
    allowed, retry_after = await fastapi_request.app.state.rate_limiter.allow(client_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    return await fastapi_request.app.state.chat_service.process_message(
        message=request.message,
        conversation_id=request.conversation_id,
    )


async def _stream_chat_response(
    fastapi_request: Request,
    *,
    message: str,
    conversation_id: str | None = None,
) -> EventSourceResponse:
    await ensure_runtime_ready(fastapi_request.app)
    allowed, retry_after = await fastapi_request.app.state.rate_limiter.allow(_client_key(fastapi_request, "stream"))
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    response = await fastapi_request.app.state.chat_service.process_message(
        message=message,
        conversation_id=conversation_id,
    )
    return EventSourceResponse(
        fastapi_request.app.state.streamer(
            conversation_id=response.conversation_id,
            message=response.message,
        )
    )


@router.get("/chat/stream")
async def chat_stream(
    fastapi_request: Request,
    message: str = Query(..., min_length=1, max_length=10_000),
    conversation_id: str | None = Query(default=None),
) -> EventSourceResponse:
    """Stream a chat response via Server-Sent Events."""
    return await _stream_chat_response(
        fastapi_request,
        message=message,
        conversation_id=conversation_id,
    )


@router.post("/chat/stream")
async def chat_stream_post(chat_request: ChatStreamRequest, fastapi_request: Request) -> EventSourceResponse:
    """Stream a chat response via Server-Sent Events using a JSON request body."""
    return await _stream_chat_response(
        fastapi_request,
        message=chat_request.message,
        conversation_id=chat_request.conversation_id,
    )


@router.get("/mock-data/hr-overview", response_model=MockDataOverview)
async def hr_mock_data_overview(fastapi_request: Request) -> MockDataOverview:
    """Expose a compact HR mock-data snapshot for the frontend."""
    await ensure_runtime_ready(fastapi_request.app)
    payload = await fastapi_request.app.state.chat_service.tool_executor.get_hr_showcase()
    return MockDataOverview.model_validate(payload)
