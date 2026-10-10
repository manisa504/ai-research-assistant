import pymupdf
import pytest

import document_processor
from document_processor import (
    DocumentPage, DocumentProcessingError, chunk_pages, extract_pdf_pages,
)


def make_pdf(texts: list[str], password: str | None = None) -> bytes:
    with pymupdf.open() as document:
        for text in texts:
            page = document.new_page()
            if text:
                page.insert_text((72, 72), text)
        if password:
            return document.tobytes(
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw=password, user_pw=password,
            )
        return document.tobytes()


def test_extract_preserves_filename_page_numbers_and_blank_pages():
    pages = extract_pdf_pages(make_pdf(["First page", "", "Third page"]), "paper.pdf")
    assert pages == [
        DocumentPage("paper.pdf", 1, "First page"),
        DocumentPage("paper.pdf", 2, ""),
        DocumentPage("paper.pdf", 3, "Third page"),
    ]


@pytest.mark.parametrize("data", [b"", b"not a PDF", b"%PDF-1.7\nbroken"])
def test_bad_uploads_raise_friendly_errors(data):
    with pytest.raises(DocumentProcessingError):
        extract_pdf_pages(data, "bad.pdf")


def test_rejects_password_protected_pdf():
    with pytest.raises(DocumentProcessingError, match="password-protected"):
        extract_pdf_pages(make_pdf(["Private"], password="secret"), "locked.pdf")


def test_rejects_oversized_upload(monkeypatch):
    monkeypatch.setattr(document_processor, "MAX_PDF_BYTES", 4)
    with pytest.raises(DocumentProcessingError, match="20 MB"):
        extract_pdf_pages(b"%PDF-1.7", "large.pdf")


def test_chunk_overlap_coverage_and_page_boundaries():
    words = [f"word{number}" for number in range(11)]
    pages = [
        DocumentPage("paper.pdf", 1, " ".join(words)),
        DocumentPage("paper.pdf", 2, ""),
        DocumentPage("paper.pdf", 3, "Last page"),
    ]
    chunks = chunk_pages(pages, chunk_size=5, overlap=2)
    assert [chunk.text for chunk in chunks] == [
        " ".join(words[0:5]), " ".join(words[3:8]),
        " ".join(words[6:11]), "Last page",
    ]
    assert [chunk.page_number for chunk in chunks] == [1, 1, 1, 3]
    assert [chunk.chunk_number for chunk in chunks] == [1, 2, 3, 4]
    assert all(chunk.filename == "paper.pdf" for chunk in chunks)


def test_zero_overlap_and_short_final_chunk():
    chunks = chunk_pages([DocumentPage("x.pdf", 1, "a b c d e")], 3, 0)
    assert [chunk.text for chunk in chunks] == ["a b c", "d e"]


def test_blank_input_has_no_chunks():
    assert chunk_pages([]) == []
    assert chunk_pages([DocumentPage("blank.pdf", 1, " \n\t")]) == []


@pytest.mark.parametrize("size,overlap", [(0, 0), (-1, 0), (5, -1), (5, 5), (5, 6)])
def test_invalid_chunk_settings(size, overlap):
    with pytest.raises(ValueError):
        chunk_pages([], size, overlap)
