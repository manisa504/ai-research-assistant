# AI Research Assistant

A beginner-friendly Python 3.12 application for preparing PDF documents for
retrieval-augmented generation (RAG). **Only Steps 1 and 2 are implemented.**
You can upload PDFs, read extracted pages, and inspect overlapping text chunks.
Question answering is visibly disabled until Bedrock is integrated.

## Run locally

Clone the repository, then create a local environment:

```bash
git clone https://github.com/manisa504/ai-research-assistant.git
cd ai-research-assistant
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open http://localhost:8501. No AWS account, credentials, or environment variables
are needed for these steps. The app makes no Bedrock calls.

## Step 1: Streamlit interface

Implemented a multi-PDF uploader, document/page/chunk counts, sidebar chunk
settings, and a disabled question input explaining the current scope.

Verify: open the app without uploading anything. Counts should be zero, the
upload prompt should appear, and the question input and Ask button should be
disabled. Automated verification:

```bash
python -m pytest tests/test_app.py -q
```

## Step 2: PDF extraction and chunking

`document_processor.py` uses PyMuPDF to extract text in approximate reading order
and keeps the filename and one-based PDF page number. Blank pages remain in the
page list, so references do not shift. Chunks use whitespace-separated words:
200 words with 40 words of overlap by default. They never span pages; these are
word counts, not Bedrock token counts. Whitespace is normalized inside chunks.

Verify:

1. Upload `sample_docs/research_notes.pdf`: expect one document, three pages,
   and two chunks with the default settings.
2. Expand the document and select each page. The first two contain notes; the
   third is blank and triggers a warning. Chunks reference pages 1 and 2.
3. Adjust the sidebar settings or upload a longer PDF to inspect overlapping
   chunks. Upload multiple PDFs to check separate filenames.
4. Remove all files: previews and counts should clear.
5. Upload an invalid file renamed with a `.pdf` extension or a password-protected
   PDF: an error should appear while other valid files still work.

```bash
python -m pytest tests/test_document_processor.py -q
python -m pytest -q
```

Tests construct PDFs in memory and cover extraction, page references, blank
pages, invalid/encrypted/oversized files, chunk overlap and boundaries, invalid
settings, and the Streamlit interface including upload removal.

## Files and limits

```text
ai-research-assistant/
├── app.py
├── document_processor.py
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/config.toml
├── Dockerfile
├── .dockerignore
├── deploy_aws.py
├── AWS_DEPLOYMENT.md
├── README.md
├── sample_docs/
│   └── research_notes.pdf
└── tests/
    ├── test_app.py
    └── test_document_processor.py
```

PDFs are limited to 20 MB each by Streamlit and the processor. Uploads and parsed text stay
in session memory; nothing is saved to disk or shared through a global cache.
Removing a file clears its parsed state on the next rerun. Refreshing or ending
the session can discard the documents. Upload only files that fit the memory
available on your machine; there is no aggregate upload quota yet.

Image-only scans need OCR, which is not implemented. Complex columns, tables,
and equations may extract imperfectly. No retrieval, embeddings, answers, or
citations are generated in this version.

## AWS deployment

The PDF preparation app is deployed to ECS Express Mode in `us-east-2` (Ohio):
https://ai-9cc795dd20a04970bca0dd0293f8831e.ecs.us-east-2.on.aws

The deployment completed successfully. HTTPS health and a real browser PDF
upload/page/chunk preview were verified. Question answering remains disabled.
See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for authentication, deployment,
verification, costs, and cleanup. This is a single-task demonstration with
session-only document storage.

## Later application steps (not implemented)

- Step 3: Bedrock embeddings and local FAISS indexing.
- Step 4: Evidence-based answers with filename/page citations and explicit
  insufficient-evidence responses.
- Step 5: A simple rule-based document/general-question router.
- Step 6: 10–15 question-answer evaluation cases and CSV results.

Those steps will add `bedrock_client.py`, `rag.py`, `agent.py`, RAG
and routing tests, and evaluation cases as their behavior becomes available.
Deployment documentation will cover model access, IAM permissions, costs, and
service identity. Local AWS development will use the standard credential chain;
deployment will use a supported service role. Never commit AWS access keys.
The initial deployment will be single-instance: local FAISS indexes and uploads
will not provide durable or shared storage.

API references: [Streamlit file uploads](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
and [PyMuPDF file handling](https://pymupdf.readthedocs.io/en/latest/how-to-open-a-file.html).
