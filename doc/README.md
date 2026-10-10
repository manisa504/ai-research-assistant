# Project showcase

A buildless, responsive portfolio site at `index.html`. All images, diagrams,
sample PDFs and video files are local assets. It makes no inference calls.

```bash
python3.12 -m http.server 8765 --directory doc
```

Open http://localhost:8765. Walkthrough and architecture tabs support keyboard
arrows, Home and End. The site honors reduced-motion preferences. Screenshots
are real browser captures of the fictional sample PDF; metrics link to recorded
results rather than representing live monitoring.

## Refresh evidence

From the repository root:

```bash
python -m pytest -q --junitxml=doc/evidence/pytest.xml
AWS_PROFILE=research python evaluate.py
python scripts/browser_smoke.py --url https://YOUR_APP_ENDPOINT
python scripts/draw_architecture.py
```

Export each `.drawio` with the draw.io desktop CLI; for example on macOS:

```bash
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -b 10 \
  -o doc/diagrams/aws-deployment.drawio.png doc/diagrams/aws-deployment.drawio
```

Repeat for `document-pipeline` and `answer-flow`. Review every export visually.
The embedded-XML PNGs can be reopened and edited in draw.io.

The BRAG plan, composition and share copy are in `brag-output/`. The website
serves the rendered MP4 and selected poster from `assets/`. See the composition
README for reproducible rendering. The film is intentionally silent for viewing
in a recruiter feed; no third-party soundtrack is redistributed.

## Hosting

Upload the contents of `doc/` to any static host. Relative URLs work under a
repository subpath. GitHub Pages accepts `/docs` or `/` on its publishing branch,
so publishing this requested singular `doc/` directory requires copying its
contents to the root of a dedicated Pages branch. No Node app runtime or CI/CD
pipeline is necessary.

## Deployed Bedrock flow

| Component | Current configuration |
|---|---|
| Chunk and query embeddings | Amazon Bedrock `amazon.titan-embed-text-v2:0`, InvokeModel, normalized 256-dimensional vectors |
| Document and general answers | Amazon Bedrock `amazon.nova-lite-v1:0`, Converse |
| Region | `us-east-2`; direct regional calls, no cross-region inference profile |
| Search and metadata | Session-local FAISS IndexFlatIP with filenames and one-based page references |
| Runtime identity | Dedicated ECS task role permitting InvokeModel on the two model ARNs |

The static `index.html` explains this flow; indexing and inference run in the
separate Streamlit application linked from its live-demo buttons. Supporting
evidence and source quotes are checked before the app renders document
citations. General mode bypasses document retrieval. Session data is ephemeral.

Before pushing an architecture change, update the diagram generator, editable
draw.io files, PNG exports, companion guides, README, deployment documentation
and website together. Review the drawings and rerun `scripts/check_showcase.py`
against the locally served site.
