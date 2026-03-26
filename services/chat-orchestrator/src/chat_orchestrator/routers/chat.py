"""Chat endpoints — the main user-facing API."""

import logging
import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from shared.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message — routes to appropriate tools via LLM."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    logger.info("Chat request received", extra={"conversation_id": conversation_id})

    # TODO: LLM routing, tool execution, response generation
    return ChatResponse(
        message="Chat Orchestrator is running. Full implementation coming soon.",
        conversation_id=conversation_id,
        model_used="stub",
    )


@router.get("/chat/stream")
async def chat_stream() -> JSONResponse:
    """Stream a chat response via Server-Sent Events."""
    # TODO: Implement SSE streaming with sse-starlette
    return JSONResponse(
        content={"message": "SSE streaming endpoint — implementation pending"},
        status_code=501,
    )
