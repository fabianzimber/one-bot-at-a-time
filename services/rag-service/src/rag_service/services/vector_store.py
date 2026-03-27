"""Vector store — ChromaDB interface for document storage and search."""

import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

import chromadb
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from rag_service.database import DocumentChunkRecord

if TYPE_CHECKING:
    from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)


class VectorStore:
    """Abstraction over ChromaDB for document chunk storage and retrieval.

    Local dev: ChromaDB PersistentClient
    Production: ChromaDB HttpClient or pgvector
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8004,
        collection_name: str = "trenkwalder_docs",
        backend: str = "chroma",
    ) -> None:
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.backend = backend
        self._client = None
        self._collection: Collection | None = None
        logger.info("VectorStore initialized", extra={"backend": backend, "host": host, "port": port})

    async def initialize(self) -> None:
        """Connect to ChromaDB and get/create the collection."""
        if self.backend != "chroma":
            logger.info("VectorStore uses database backend")
            return

        if self.host not in {"localhost", "127.0.0.1"}:
            self._client = chromadb.HttpClient(host=self.host, port=self.port)
        else:
            path = Path("/tmp") / self.collection_name
            self._client = chromadb.PersistentClient(path=str(path))

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("VectorStore connected", extra={"backend": self.backend})

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)

    async def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        session: AsyncSession,
    ) -> None:
        """Add document chunks to the vector store."""
        if self.backend == "chroma":
            assert self._collection is not None
            sanitized_metadatas = [
                {key: value for key, value in metadata.items() if value is not None} for metadata in metadatas
            ]
            self._collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=sanitized_metadatas)

        session.add_all(
            [
                DocumentChunkRecord(
                    id=chunk_id,
                    document_id=metadata["document_id"],
                    source_file=metadata["source_file"],
                    page_number=metadata.get("page_number"),
                    chunk_index=metadata["chunk_index"],
                    chunk_text=text,
                    embedding=embedding,
                )
                for chunk_id, text, embedding, metadata in zip(ids, texts, embeddings, metadatas, strict=True)
            ]
        )
        logger.info("Documents added", extra={"count": len(ids), "backend": self.backend})

    async def search(
        self,
        query_embedding: list[float],
        session: AsyncSession,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for similar documents by embedding."""
        if self.backend == "chroma":
            assert self._collection is not None
            result = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            return [
                {
                    "chunk_text": document,
                    "source_file": metadata["source_file"],
                    "page_number": metadata.get("page_number"),
                    "score": round(1 - float(distance), 6),
                    "chunk_index": metadata["chunk_index"],
                    "document_id": metadata["document_id"],
                }
                for document, metadata, distance in zip(documents, metadatas, distances, strict=True)
            ]

        records = (await session.exec(select(DocumentChunkRecord))).all()
        ranked = sorted(
            records,
            key=lambda record: self._cosine_similarity(query_embedding, record.embedding),
            reverse=True,
        )[:top_k]
        return [
            {
                "chunk_text": record.chunk_text,
                "source_file": record.source_file,
                "page_number": record.page_number,
                "score": round(self._cosine_similarity(query_embedding, record.embedding), 6),
                "chunk_index": record.chunk_index,
                "document_id": record.document_id,
            }
            for record in ranked
        ]

    async def delete(self, document_id: str, session: AsyncSession) -> None:
        """Delete all chunks belonging to a document."""
        if self.backend == "chroma":
            assert self._collection is not None
            self._collection.delete(where={"document_id": document_id})

        await session.exec(delete(DocumentChunkRecord).where(DocumentChunkRecord.document_id == document_id))
        await session.commit()
        logger.info("Document deleted", extra={"document_id": document_id, "backend": self.backend})
