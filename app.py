"""PDF research assistant: Bedrock embeddings, FAISS retrieval and cited answers."""

from dataclasses import asdict
import hashlib
import json

from botocore.exceptions import BotoCoreError, ClientError

from agent import ask
from bedrock_client import BedrockClient
from rag import RAGIndex, MAX_CHUNKS

import streamlit as st

from document_processor import DocumentProcessingError, chunk_pages, extract_pdf_pages


def main() -> None:
    st.set_page_config(page_title="AI Research Assistant", page_icon="📚", layout="wide")
    st.title("AI Research Assistant")
    st.write("Upload PDFs, build a searchable index, and ask questions with page citations.")
    st.caption("Amazon Bedrock • Titan embeddings • Nova Lite answers • FAISS search")

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

    # Any upload/settings change invalidates old evidence before the next question.
    signature = hashlib.sha256(json.dumps(
        [asdict(chunk) for chunk in all_chunks], sort_keys=True
    ).encode()).hexdigest()
    if st.session_state.get("index_signature") != signature:
        st.session_state.pop("rag_index", None)
        st.session_state.pop("last_answer", None)
    st.subheader("Build the document index")
    st.caption(f"Sends extracted text to Amazon Bedrock in us-east-2 by default. "
               f"Up to {MAX_CHUNKS} chunks per session. Bedrock usage incurs charges.")
    if st.button("Build index", disabled=not all_chunks or len(all_chunks) > MAX_CHUNKS):
        try:
            with st.spinner("Embedding document chunks with Amazon Bedrock…"):
                index = RAGIndex.build(all_chunks, BedrockClient())
            st.session_state["rag_index"] = index
            st.session_state["index_signature"] = signature
            st.success(f"Indexed {len(all_chunks)} chunks. Ready for document questions.")
        except (BotoCoreError, ClientError, ValueError) as error:
            st.error(f"Could not build the index: {error}")
    index = st.session_state.get("rag_index")
    st.caption("Index ready." if index is not None else "Build the index to ask about your PDFs.")

    st.subheader("Ask a question")
    mode = st.radio("Question mode", ["Auto", "Documents", "General"], horizontal=True)
    st.caption("Auto uses your documents when uploaded. Use General or prefix ‘general:’ "
               "for a question outside your PDFs. General answers have no document citations.")
    with st.form("question_form"):
        question = st.text_input("Your question", max_chars=2000,
                                 placeholder="What are the findings in the uploaded notes?")
        submitted = st.form_submit_button("Ask")
    if submitted:
        try:
            with st.spinner("Asking Amazon Bedrock…"):
                st.session_state["last_answer"] = ask(
                    question, BedrockClient(), index, mode, bool(current)
                )
        except (BotoCoreError, ClientError, ValueError) as error:
            st.session_state.pop("last_answer", None)
            st.error(f"Could not answer: {error}")
    answer = st.session_state.get("last_answer")
    if answer is not None:
        st.caption(f"Answer mode: {answer.route}")
        st.text(answer.text)
        if answer.sources:
            with st.expander("Supporting evidence", expanded=True):
                for source in answer.sources:
                    st.text(f'{source["filename"]}, page {source["page"]} — {source["quote"]}')
        if answer.retrieved:
            with st.expander("Retrieved chunks"):
                st.dataframe(answer.retrieved, hide_index=True)


if __name__ == "__main__":
    main()
