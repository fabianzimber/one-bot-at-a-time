"""Coverage-focused tests for RAG document processing and service routes."""

from datetime import UTC, datetime
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from rag_service import main as rag_main
from rag_service.database import DocumentChunkRecord, DocumentRecord
from rag_service.database import connection as rag_connection
from rag_service.services import chunker, document_loader
from rag_service.services.vector_store import VectorStore


class FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class FakePdfReader:
    def __init__(self, _buffer: BytesIO) -> None:
        self.pages = [FakePdfPage("PDF Seite eins."), FakePdfPage("")]


class FakeDocxParagraph:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeDocxDocument:
    def __init__(self, _buffer: BytesIO) -> None:
        self.paragraphs = [FakeDocxParagraph("Erste Zeile"), FakeDocxParagraph(""), FakeDocxParagraph("Zweite Zeile")]


def test_chunker_handles_overlap_validation_and_metadata() -> None:
    with pytest.raises(ValueError):
        chunker.recursive_character_split("abc", chunk_size=10, overlap=10)

    short_chunks = chunker.recursive_character_split("Kurzer Text", chunk_size=50, overlap=10)
    assert len(short_chunks) == 1
    assert short_chunks[0].text == "Kurzer Text"

    long_text = "abcdefghijklmnopqrstuvwxyz"
    chunks = chunker.recursive_character_split(long_text, chunk_size=10, overlap=3)
    assert [chunk.text for chunk in chunks] == ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]

    sections = [("abcdefghijklmno", 1), ("pqrstuvwxyz", 2)]
    document_chunks = chunker.build_document_chunks(
        document_id="doc-123",
        source_file="policy.txt",
        sections=sections,
        chunk_size=8,
        overlap=2,
    )
    assert document_chunks[0].metadata == {
        "document_id": "doc-123",
        "source_file": "policy.txt",
        "page_number": 1,
        "chunk_index": 0,
    }
    assert document_chunks[-1].metadata["page_number"] == 2
    assert [chunk.index for chunk in document_chunks] == list(range(len(document_chunks)))


@pytest.mark.asyncio
async def test_document_loader_supports_text_docx_pdf_and_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    txt = await document_loader.load_document("policy.txt", b"Urlaub\nHomeoffice")
    assert txt.text == "Urlaub\nHomeoffice"
    assert len(txt.sections) == 1

    md = await document_loader.load_document("policy.md", b"Urlaub \xdcbersicht")
    assert md.text == "Urlaub \xdcbersicht".encode("latin-1").decode("latin-1")

    monkeypatch.setattr(document_loader, "DocxDocument", FakeDocxDocument)
    docx = await document_loader.load_document("notes.docx", b"fake-docx")
    assert docx.text == "Erste Zeile\nZweite Zeile"
    assert len(docx.sections) == 1

    monkeypatch.setattr(document_loader, "PdfReader", FakePdfReader)
    pdf = await document_loader.load_document("policy.pdf", b"fake-pdf")
    assert pdf.sections[0].page_number == 1
    assert pdf.text == "PDF Seite eins."

    with pytest.raises(ValueError):
        await document_loader.load_document("policy.csv", b"bad")


@pytest.mark.asyncio
async def test_rag_database_model_and_connection_lifecycle(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "rag-manual.sqlite"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    original_url = rag_connection.settings.database_url
    engine = create_async_engine(
        db_url,
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with session_factory() as session:
            session.add(
                DocumentRecord(
                    id="doc-manual",
                    filename="policy.txt",
                    chunk_count=1,
                    uploaded_at=datetime(2026, 3, 27, 12, 0, 0, tzinfo=UTC),
                )
            )
            await session.commit()

            rows = await session.exec(select(DocumentRecord))
            assert rows.first().id == "doc-manual"

        monkeypatch.setattr(rag_connection.settings, "database_url", db_url)
        await rag_connection.close_database()
        await rag_connection.ensure_database_ready()

        async for session in rag_connection.get_session():
            assert session is not None
            break
    finally:
        await rag_connection.close_database()
        monkeypatch.setattr(rag_connection.settings, "database_url", original_url)
        await rag_connection.ensure_database_ready()
        await engine.dispose()


@pytest.mark.asyncio
async def test_rag_database_connection_and_vector_store_db_backend(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "rag.sqlite"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    original_url = rag_connection.settings.database_url

    monkeypatch.setattr(rag_connection.settings, "database_url", db_url)
    await rag_connection.close_database()
    await rag_connection.ensure_database_ready()

    session_factory = rag_connection.get_session_factory()
    store = VectorStore(backend="pgvector")
    await store.initialize()

    async with session_factory() as session:
        await store.add_documents(
            ids=["doc-1-chunk-0", "doc-1-chunk-1"],
            texts=["Homeoffice ist zwei Tage pro Woche moeglich.", "Urlaub ist 30 Tage pro Jahr."],
            embeddings=[[1.0, 0.0], [0.0, 1.0]],
            metadatas=[
                {"document_id": "doc-1", "source_file": "policy.txt", "page_number": 1, "chunk_index": 0},
                {"document_id": "doc-1", "source_file": "policy.txt", "page_number": 1, "chunk_index": 1},
            ],
            session=session,
        )
        await session.commit()

        results = await store.search(query_embedding=[1.0, 0.0], session=session, top_k=1)
        assert results[0]["document_id"] == "doc-1"
        assert results[0]["source_file"] == "policy.txt"

        await store.delete("doc-1", session=session)
        await session.commit()

        remaining = await session.exec(select(DocumentChunkRecord))
        assert remaining.all() == []

    async for session in rag_connection.get_session():
        assert session is not None
        break

    await rag_connection.close_database()
    monkeypatch.setattr(rag_connection.settings, "database_url", original_url)
    await rag_connection.ensure_database_ready()
    assert rag_connection.get_session_factory() is not None


def test_rag_service_ingest_search_and_delete_roundtrip() -> None:
    client = TestClient(rag_main.app)

    health = client.get("/health")
    assert health.status_code == 200

    upload = client.post(
        "/api/v1/ingest",
        files={"file": ("policy.txt", b"Homeoffice ist zwei Tage pro Woche moeglich.", "text/plain")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    documents = client.get("/api/v1/documents")
    assert documents.status_code == 200
    assert any(document["document_id"] == document_id for document in documents.json())

    search = client.post("/api/v1/search", json={"query": "Homeoffice", "top_k": 3})
    assert search.status_code == 200
    assert any(result["source_file"] == "policy.txt" for result in search.json()["results"])

    delete = client.delete(f"/api/v1/documents/{document_id}")
    assert delete.status_code == 200

    documents_after_delete = client.get("/api/v1/documents")
    assert all(document["document_id"] != document_id for document in documents_after_delete.json())


def test_rag_service_rejects_unsupported_upload_extension() -> None:
    client = TestClient(rag_main.app)
    response = client.post(
        "/api/v1/ingest",
        files={"file": ("policy.csv", b"not supported", "text/csv")},
    )
    assert response.status_code == 400
