"""Server-Sent Events streaming logic."""

import json
from collections.abc import AsyncGenerator


async def stream_chat_response(*, conversation_id: str, message: str) -> AsyncGenerator[dict]:
    """Generate SSE-style events for a chat response."""
    yield {"event": "start", "data": json.dumps({"conversation_id": conversation_id})}
    for index in range(0, len(message), 48):
        yield {"event": "content", "data": json.dumps({"delta": message[index : index + 48]})}
    yield {"event": "done", "data": json.dumps({"conversation_id": conversation_id})}
