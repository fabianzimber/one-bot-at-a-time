"""Semantic search endpoint."""

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from rag_service.database import get_session_factory
from rag_service.runtime import ensure_runtime_ready

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
async def search_documents(request: SearchRequest, fastapi_request: Request) -> SearchResponse:
    """Search indexed documents for relevant chunks."""
    await ensure_runtime_ready(fastapi_request.app)
    logger.info("Search request", extra={"query": request.query[:50], "top_k": request.top_k})

    query_embedding = await fastapi_request.app.state.embedder.embed_query(request.query)
    session_factory = get_session_factory()
    async with session_factory() as session:  # type: AsyncSession
        results = await fastapi_request.app.state.vector_store.search(
            query_embedding=query_embedding,
            session=session,
            top_k=request.top_k,
        )
    return SearchResponse(
        results=[SearchResult(**result) for result in results],
        query=request.query,
        total_results=len(results),
    )
