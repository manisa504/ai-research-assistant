"""Steps 1–2: local PDF upload, extraction, and chunk preview."""

from dataclasses import asdict

import streamlit as st

from document_processor import DocumentProcessingError, chunk_pages, extract_pdf_pages


def main() -> None:
    st.set_page_config(page_title="AI Research Assistant", page_icon="📚", layout="wide")
    st.title("AI Research Assistant")
    st.write("Upload PDFs and inspect their text before asking questions in a later step.")
    st.info("Steps 1–2: PDF upload and text preparation. Question answering is not connected yet.")

    with st.sidebar:
        st.header("Text preparation")
        chunk_size = st.slider("Words per chunk", 50, 500, 200, 25)
        overlap = st.slider("Overlap in words", 0, chunk_size - 1, min(40, chunk_size - 1))
        st.caption("Chunks stay within a single page to preserve page references.")

    uploaded_files = st.file_uploader(
        "Upload PDF documents", type=["pdf"], accept_multiple_files=True,
        help="Up to 20 MB per PDF. Text-based PDFs only; OCR is not included.",
    )
    st.caption("Files are processed in memory for this session and are not saved to disk.")

    # Session state avoids reparsing unchanged uploads on every widget rerun.
    # Unlike a global cache, it does not share document text between users.
    previous = st.session_state.get("parsed_documents", {})
    current = {}
    all_chunks = []
    total_pages = 0
    for position, uploaded in enumerate(uploaded_files):
        data = uploaded.getvalue()
        key = (uploaded.name, data)
        try:
            pages = previous.get(key)
            if pages is None:
                with st.spinner(f"Reading {uploaded.name}…"):
                    pages = extract_pdf_pages(data, uploaded.name)
            current[key] = pages
            chunks = chunk_pages(pages, chunk_size, overlap)
        except DocumentProcessingError as error:
            st.error(f"{uploaded.name}: {error}")
            continue

        total_pages += len(pages)
        all_chunks.extend(chunks)
        with st.expander(f"{uploaded.name} — {len(pages)} pages, {len(chunks)} chunks"):
            blank_pages = [str(page.page_number) for page in pages if not page.text.strip()]
            if blank_pages:
                st.warning(
                    "No extractable text on page(s): " + ", ".join(blank_pages)
                    + ". These may be blank or scanned; OCR is not included."
                )
            if chunks:
                st.dataframe([asdict(chunk) for chunk in chunks], hide_index=True)
            page_number = st.selectbox(
                "Preview page", [page.page_number for page in pages], key=f"page_{position}"
            )
            st.text(pages[page_number - 1].text or "No extractable text on this page.")

    st.session_state["parsed_documents"] = current
    st.session_state["chunks"] = all_chunks
    documents_column, pages_column, chunks_column = st.columns(3)
    documents_column.metric("Readable documents", len(current))
    pages_column.metric("Pages", total_pages)
    chunks_column.metric("Chunks", len(all_chunks))
    if not uploaded_files:
        st.info("Upload a PDF to see its pages and text chunks.")

    st.subheader("Ask a question")
    st.text_input("Your question", disabled=True, placeholder="Available after Bedrock integration")
    st.button("Ask", disabled=True)


if __name__ == "__main__":
    main()
