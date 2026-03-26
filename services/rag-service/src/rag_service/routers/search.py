"""Semantic search endpoint."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_text: str
    source_file: str
    page_number: int | None = None
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    total_results: int


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """Search indexed documents for relevant chunks."""
    logger.info("Search request", extra={"query": request.query[:50], "top_k": request.top_k})

    # TODO: Embed query, search ChromaDB, return ranked results
    return SearchResponse(
        results=[],
        query=request.query,
        total_results=0,
    )
