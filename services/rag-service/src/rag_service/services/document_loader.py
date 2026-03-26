"""Document parsing — extracts text from various file formats."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


async def load_document(file_path: Path) -> str:
    """Extract text content from a document file.

    Supports: PDF, TXT, MD, DOCX
    """
    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    logger.info("Loading document", extra={"path": str(file_path), "type": ext})

    # TODO: Implement parsers for each format
    # PDF: PyMuPDF or pdfplumber
    # DOCX: python-docx
    # TXT/MD: direct read
    return f"Stub content from {file_path.name}"
