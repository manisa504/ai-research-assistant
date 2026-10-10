"""Extract PDF pages and split their text without losing source references."""

from dataclasses import dataclass

import pymupdf


MAX_PDF_BYTES = 20 * 1024 * 1024


class DocumentProcessingError(ValueError):
    """A PDF could not be processed; the message is suitable for the UI."""


@dataclass(frozen=True)
class DocumentPage:
    filename: str
    page_number: int  # One-based, matching the PDF viewer.
    text: str


@dataclass(frozen=True)
class TextChunk:
    filename: str
    page_number: int
    chunk_number: int  # One-based within this document.
    text: str


def extract_pdf_pages(pdf_bytes: bytes, filename: str) -> list[DocumentPage]:
    """Read a PDF in memory, including blank pages. Scans require future OCR."""
    if not pdf_bytes:
        raise DocumentProcessingError("The uploaded file is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise DocumentProcessingError("PDFs must be 20 MB or smaller.")
    # PyMuPDF also supports other formats; explicitly require PDF input.
    if not pdf_bytes.lstrip().startswith(b"%PDF-"):
        raise DocumentProcessingError("The uploaded file is not a valid PDF.")
    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
            if not document.is_pdf:
                raise DocumentProcessingError("The uploaded file is not a valid PDF.")
            if document.needs_pass:
                raise DocumentProcessingError(
                    "This PDF is password-protected. Upload an unlocked copy."
                )
            if document.page_count == 0:
                raise DocumentProcessingError("This PDF contains no pages.")
            return [
                DocumentPage(filename, number, page.get_text("text", sort=True).strip())
                for number, page in enumerate(document, start=1)
            ]
    except DocumentProcessingError:
        raise
    except (RuntimeError, ValueError) as error:
        raise DocumentProcessingError(
            "Could not read this PDF. It may be damaged or unsupported."
        ) from error


def chunk_pages(
    pages: list[DocumentPage], chunk_size: int = 200, overlap: int = 40
) -> list[TextChunk]:
    """Split each page into overlapping word windows; never cross pages.

    Sizes count whitespace-separated words, not model tokens. Blank pages
    produce no chunks. Chunk numbering restarts on each call.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between zero and chunk_size - 1.")

    chunks = []
    for page in pages:
        words = page.text.split()
        for start in range(0, len(words), chunk_size - overlap):
            end = start + chunk_size
            chunks.append(
                TextChunk(
                    page.filename, page.page_number, len(chunks) + 1,
                    " ".join(words[start:end]),
                )
            )
            if end >= len(words):
                break  # Avoid a redundant tail containing only overlap.
    return chunks
