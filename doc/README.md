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

Live showcase: https://manisa504.github.io/ai-research-assistant/

The workflow in `.github/workflows/pages.yml` uploads `doc/` directly as the
Pages artifact. There is no Jekyll or Node build. In repository **Settings →
Pages → Build and deployment**, select **GitHub Actions** as the source.
Pushes to `main` that change `doc/` or the workflow publish automatically; use
**Actions → Publish project showcase → Run workflow** to republish manually.

The previous branch source `/docs` failed because this project uses singular
`doc/`. Keep that directory and the workflow's `path: doc` consistent. Do not
select `/docs` or add a Jekyll theme. Relative assets work under the repository
subpath, including diagrams, evidence, the sample PDF and the project video.
The static site makes no AWS calls; the live-demo buttons open the separate
Bedrock application on ECS. Only `doc/` is included in the Pages artifact.

See [GitHub's custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

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
