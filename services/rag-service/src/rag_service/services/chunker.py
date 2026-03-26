"""Text chunking — splits documents into embeddable chunks."""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict[str, Any]


def recursive_character_split(text: str, chunk_size: int = 512, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping chunks using recursive character splitting.

    Strategy:
    1. Try splitting on paragraphs (\\n\\n)
    2. Fall back to sentences (. ! ?)
    3. Fall back to characters

    Raises:
        ValueError: If overlap >= chunk_size (would cause infinite loop).
    """
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")

    if len(text) <= chunk_size:
        return [Chunk(text=text, index=0, metadata={})]

    # TODO: Implement recursive splitting with proper separators
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(Chunk(text=text[start:end], index=idx, metadata={}))
        if end == len(text):
            break
        start = end - overlap
        idx += 1

    logger.info("Text chunked", extra={"total_chunks": len(chunks), "chunk_size": chunk_size})
    return chunks


def build_document_chunks(
    *,
    document_id: str,
    source_file: str,
    sections: list[tuple[str, int | None]],
    chunk_size: int = 512,
    overlap: int = 50,
) -> list[Chunk]:
    """Split document sections while enriching each chunk with metadata."""
    chunks: list[Chunk] = []
    chunk_index = 0

    for section_text, page_number in sections:
        for chunk in recursive_character_split(section_text, chunk_size=chunk_size, overlap=overlap):
            chunk.metadata = {
                "document_id": document_id,
                "source_file": source_file,
                "page_number": page_number,
                "chunk_index": chunk_index,
            }
            chunks.append(Chunk(text=chunk.text, index=chunk_index, metadata=chunk.metadata))
            chunk_index += 1

    return chunks
