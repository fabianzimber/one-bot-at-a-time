"""Text chunking — splits documents into embeddable chunks."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict


def recursive_character_split(text: str, chunk_size: int = 512, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping chunks using recursive character splitting.

    Strategy:
    1. Try splitting on paragraphs (\\n\\n)
    2. Fall back to sentences (. ! ?)
    3. Fall back to characters
    """
    if len(text) <= chunk_size:
        return [Chunk(text=text, index=0, metadata={})]

    # TODO: Implement recursive splitting with proper separators
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(Chunk(text=text[start:end], index=idx, metadata={}))
        start = end - overlap
        idx += 1

    logger.info("Text chunked", extra={"total_chunks": len(chunks), "chunk_size": chunk_size})
    return chunks
