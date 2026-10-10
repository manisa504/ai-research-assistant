# Project requirements

Build a working beginner-friendly RAG research assistant. The earlier restriction
“Step 1 and Step 2 only” is superseded: Amazon Bedrock question answering is core
functionality and is required for completion.

## Required behavior

- Upload PDFs, preserve filenames and one-based page numbers, and chunk within pages.
- Generate real Amazon Bedrock embeddings and search them with local FAISS.
- Answer document questions using retrieved evidence and filename/page citations.
- Explicitly report insufficient evidence; never present unsupported answers as sourced.
- Route general questions directly to Bedrock using a simple rule with a UI override.
- Keep the implementation straightforward: Python 3.12, Streamlit, PyMuPDF, boto3,
  FAISS, Docker, pytest. No database, Redis, autonomous agent loop or IaC framework.
- Use the standard AWS credential chain locally and a scoped ECS task role in AWS.
  Never embed access keys or copy credentials into Docker.
- Keep document data and indexes isolated per session. This single-task demo is not
  durable shared storage; document that limitation.

## Completion and evidence

Run offline unit tests, 10–15 real Bedrock evaluation cases with CSV results,
and an actual deployed browser flow: upload → index → ask → answer with valid
citations. A healthy web server alone does not establish RAG functionality.
Update README, deployment docs, architecture drawings, and the portfolio website
in doc/index.html to match verified behavior. Keep model IDs, model access,
permissions, costs, and local verification steps documented. Do not claim planned
features are shipped. Preserve the requested architecture skill and BRAG video
work as part of the project showcase.
