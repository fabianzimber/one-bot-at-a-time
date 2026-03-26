"""Document management endpoints."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    uploaded_at: str


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents() -> list[DocumentInfo]:
    """List all indexed documents."""
    # TODO: Query document metadata from ChromaDB or database
    return []


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> dict:
    """Delete a document and its chunks from the index."""
    logger.info("Document deletion requested", extra={"document_id": document_id})

    # TODO: Remove chunks from ChromaDB, delete metadata
    return {"message": f"Document {document_id} deletion stub — implementation pending"}
