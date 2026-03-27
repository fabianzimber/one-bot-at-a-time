"""Document management endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from rag_service.database import DocumentRecord, get_session_factory
from rag_service.runtime import ensure_runtime_ready

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    uploaded_at: str


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents(request: Request) -> list[DocumentInfo]:
    """List all indexed documents."""
    await ensure_runtime_ready(request.app)
    session_factory = get_session_factory()
    async with session_factory() as session:  # type: AsyncSession
        result = await session.exec(select(DocumentRecord).order_by(DocumentRecord.uploaded_at.desc()))
        documents = result.all()
    return [
        DocumentInfo(
            document_id=document.id,
            filename=document.filename,
            chunk_count=document.chunk_count,
            uploaded_at=document.uploaded_at.isoformat(),
        )
        for document in documents
    ]


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, request: Request) -> dict:
    """Delete a document and its chunks from the index."""
    await ensure_runtime_ready(request.app)
    logger.info("Document deletion requested", extra={"document_id": document_id})

    session_factory = get_session_factory()
    async with session_factory() as session:  # type: AsyncSession
        document = await session.get(DocumentRecord, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        await request.app.state.vector_store.delete(document_id, session=session)
        await session.exec(delete(DocumentRecord).where(DocumentRecord.id == document_id))
        await session.commit()

    return {"message": f"Document {document_id} deleted successfully"}
