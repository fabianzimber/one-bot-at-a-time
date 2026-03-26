"""Document ingestion endpoint."""

import logging

from fastapi import APIRouter, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    message: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile) -> IngestResponse:
    """Upload and process a document for RAG."""
    logger.info("Document upload received", extra={"filename": file.filename})

    # TODO: Validate file type/size, parse, chunk, embed, store in ChromaDB
    return IngestResponse(
        document_id="stub-doc-id",
        filename=file.filename or "unknown",
        chunks_created=0,
        message="Document ingestion stub — implementation pending",
    )
