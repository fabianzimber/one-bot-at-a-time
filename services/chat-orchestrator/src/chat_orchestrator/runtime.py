"""Runtime initialization helpers for the chat orchestrator."""

import asyncio

from fastapi import FastAPI

from chat_orchestrator.config import settings
from chat_orchestrator.services.chat_service import ChatService
from chat_orchestrator.services.conversation import ConversationStore
from chat_orchestrator.services.llm_router import LLMRouter
from chat_orchestrator.services.rate_limit import RateLimiter
from chat_orchestrator.services.streaming import stream_chat_response
from chat_orchestrator.services.tool_executor import ToolExecutor
from chat_orchestrator.tools.hr_tool import HRTool
from chat_orchestrator.tools.rag_tool import RAGTool
from chat_orchestrator.tools.registry import ToolRegistry
from shared.middleware import setup_logging

_init_lock = asyncio.Lock()


async def ensure_runtime_ready(app: FastAPI) -> None:
    if hasattr(app.state, "chat_service") and hasattr(app.state, "rate_limiter") and hasattr(app.state, "streamer"):
        return

    async with _init_lock:
        if hasattr(app.state, "chat_service") and hasattr(app.state, "rate_limiter") and hasattr(app.state, "streamer"):
            return

        setup_logging(settings.log_level)
        llm_router = LLMRouter(
            primary=settings.llm_model,
            fallback=settings.llm_fallback_model,
            emergency=settings.llm_emergency_model,
            api_key=settings.openai_api_key,
        )
        tool_registry = ToolRegistry()
        tool_registry.register(RAGTool())
        tool_registry.register(HRTool())
        conversation_store = ConversationStore(settings.redis_url)
        await conversation_store.connect()
        rate_limiter = RateLimiter(settings.redis_url)
        await rate_limiter.connect()
        tool_executor = ToolExecutor(
            rag_service_url=settings.rag_service_url,
            hr_service_url=settings.hr_service_url,
            internal_api_key=settings.internal_api_key,
        )
        app.state.chat_service = ChatService(
            llm_router=llm_router,
            tool_registry=tool_registry,
            tool_executor=tool_executor,
            conversation_store=conversation_store,
        )
        app.state.rate_limiter = rate_limiter
        app.state.streamer = stream_chat_response


async def close_runtime(app: FastAPI) -> None:
    if hasattr(app.state, "chat_service"):
        await app.state.chat_service.tool_executor.close()
        await app.state.chat_service.conversation_store.close()
    if hasattr(app.state, "rate_limiter"):
        await app.state.rate_limiter.close()
