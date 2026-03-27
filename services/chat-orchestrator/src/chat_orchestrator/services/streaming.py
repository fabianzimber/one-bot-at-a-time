"""Server-Sent Events streaming logic."""

import json
from collections.abc import AsyncGenerator
from typing import Any


async def stream_chat_response(event_source: AsyncGenerator[dict[str, Any]]) -> AsyncGenerator[dict]:
    """Convert ChatService stream events into SSE-formatted dicts.

    Expects an async generator yielding dicts with a ``type`` key:
    - ``{"type": "start", "conversation_id": str}``
    - ``{"type": "delta", "content": str}``
    - ``{"type": "done", "conversation_id": str}``
    """
    async for event in event_source:
        event_type = event.get("type")

        if event_type == "start":
            yield {
                "event": "start",
                "data": json.dumps({"conversation_id": event["conversation_id"]}),
            }

        elif event_type == "delta":
            yield {
                "event": "content",
                "data": json.dumps({"delta": event["content"]}),
            }

        elif event_type == "done":
            yield {
                "event": "done",
                "data": json.dumps({"conversation_id": event["conversation_id"]}),
            }
