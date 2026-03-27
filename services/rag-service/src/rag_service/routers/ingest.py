"""Document ingestion endpoint."""

import logging
import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from rag_service.database import DocumentRecord, get_session_factory
from rag_service.runtime import ensure_runtime_ready
from rag_service.services.chunker import build_document_chunks
from rag_service.services.document_loader import SUPPORTED_EXTENSIONS, load_document

logger = logging.getLogger(__name__)

router = APIRouter()
upload_file = File(...)


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    message: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: Request, file: UploadFile = upload_file) -> IngestResponse:
    """Upload and process a document for RAG."""
    await ensure_runtime_ready(request.app)
    logger.info("Document upload received", extra={"filename": file.filename})
    filename = file.filename or "unknown"
    suffix = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    settings = request.app.state.settings
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    loaded_document = await load_document(filename, content)
    document_id = f"doc-{uuid.uuid4().hex[:12]}"
    chunks = build_document_chunks(
        document_id=document_id,
        source_file=filename,
        sections=[(section.text, section.page_number) for section in loaded_document.sections],
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    embeddings = await request.app.state.embedder.embed_texts([chunk.text for chunk in chunks])

    session_factory = get_session_factory()
    async with session_factory() as session:  # type: AsyncSession
        session.add(
            DocumentRecord(
                id=document_id,
                filename=filename,
                chunk_count=len(chunks),
                uploaded_at=request.app.state.now_factory(),
            )
        )
        await request.app.state.vector_store.add_documents(
            ids=[f"{document_id}-chunk-{chunk.index}" for chunk in chunks],
            texts=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[chunk.metadata for chunk in chunks],
            session=session,
        )
        await session.commit()

    return IngestResponse(
        document_id=document_id,
        filename=filename,
        chunks_created=len(chunks),
        message="Document ingested successfully",
    )
