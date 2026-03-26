"""Server-Sent Events streaming logic."""

import logging
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


async def stream_chat_response(conversation_id: str, message: str) -> AsyncGenerator[str]:
    """Generate SSE events for a streaming chat response.

    Yields JSON-encoded SSE data chunks.
    """
    # TODO: Implement actual LLM streaming with OpenAI's stream API
    import json

    yield json.dumps({"type": "start", "conversation_id": conversation_id})
    yield json.dumps({"type": "content", "delta": message})
    yield json.dumps({"type": "done"})
