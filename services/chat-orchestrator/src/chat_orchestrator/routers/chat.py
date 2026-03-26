"""Chat endpoints — the main user-facing API."""

import logging

from fastapi import APIRouter, HTTPException, Query, Request, status
from sse_starlette.sse import EventSourceResponse

from chat_orchestrator.runtime import ensure_runtime_ready
from shared.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, fastapi_request: Request) -> ChatResponse:
    """Process a chat message — routes to appropriate tools via LLM."""
    await ensure_runtime_ready(fastapi_request.app)
    client_key = fastapi_request.headers.get("x-forwarded-for") or fastapi_request.client.host or "unknown"
    allowed, retry_after = await fastapi_request.app.state.rate_limiter.allow(client_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry in {retry_after}s.",
        )

    return await fastapi_request.app.state.chat_service.process_message(
        message=request.message,
        conversation_id=request.conversation_id,
    )


@router.get("/chat/stream")
async def chat_stream(
    fastapi_request: Request,
    message: str = Query(..., min_length=1),
    conversation_id: str | None = Query(default=None),
) -> EventSourceResponse:
    """Stream a chat response via Server-Sent Events."""
    await ensure_runtime_ready(fastapi_request.app)
    client_key = fastapi_request.headers.get("x-forwarded-for") or fastapi_request.client.host or "unknown"
    allowed, retry_after = await fastapi_request.app.state.rate_limiter.allow(f"{client_key}:stream")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry in {retry_after}s.",
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
