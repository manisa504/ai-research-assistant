# Verification record — October 10, 2026

This is a recorded demonstration run, not continuous monitoring.

## Offline application tests

**39 passed**, 5 upstream SWIG/PyMuPDF deprecation warnings, no test failures.
Run: `python -m pytest -q --junitxml=doc/evidence/pytest.xml`.
See [JUnit output](pytest.xml).

Coverage includes actual PDF creation/extraction, preserved blank-page references,
invalid/encrypted/oversized input, word overlap, page boundaries, real FAISS vector
search, malformed/zero/nonfinite vectors, source IDs and verbatim quote validation,
insufficient support, routing, the Streamlit interface, indexing/answering with a
mock Bedrock adapter, and removing an upload invalidating the index and answer.
Offline tests do not require AWS credentials and do not make model calls.

## Real Bedrock evaluation

**12/12 cases passed** with Titan V2 embeddings and Nova Lite in `us-east-2`.
Run: `AWS_PROFILE=research python evaluate.py`.
[CSV: questions, expected terms, generated answers, check results, models, timestamps](evaluation_results.csv).

The cases cover measured quantity, station count, frequency, duration, mean
temperature, explicit negative findings, the fixture's fictional nature, its
purpose, and three absent facts (budget, researcher names, station coordinates).

An initial run scored 9/12: the model abstained on two explicit negative facts,
and the purpose question cited a different valid page than the test expected.
The prompt now demonstrates how to answer from negative evidence. The purpose
case accepts either page because both describe the demonstration/testing purpose.
The final run passed all cases. No model output is replaced with a canned answer.

Limits: the corpus contains two text chunks. Retrieval relevance checks for an
expected page among the top two results; this is a small sanity check, not a
challenging retrieval benchmark. Correctness uses expected phrase patterns, not
an LLM judge. Citation checks validate source identity and exact supporting
quotes, not full semantic entailment. Model output can vary between runs.

## Deployed browser verification

All **six checks passed** against the public HTTPS endpoint at
**2026-10-10 19:00:12 UTC**. [Machine-readable results](browser-smoke.json).
Run: `python scripts/browser_smoke.py --url https://YOUR_ENDPOINT`.

1. Fresh session has no searchable index.
2. Uploading the public sample yields 3 pages and 2 chunks.
3. Real Titan embeddings produce a usable FAISS index.
4. Real Nova inference answers 18 degrees Celsius with a valid page-2 citation.
5. A budget question absent from the source produces explicit abstention.
6. General mode returns a direct Bedrock answer without document evidence.

The browser uses the application, not direct test-only endpoints. Screenshots
show only fictional public sample data. During verification, automation locators
were corrected for Streamlit's styled radio labels and repeated evidence text.
The public hostname and ordinary certificate validation were used, without a
hardcoded address or disabled TLS verification.

## Infrastructure

The new ARM64 Fargate task uses a dedicated Bedrock task role scoped to the two
regional model ARNs. The ECS deployment reached SUCCESSFUL and the updated revision received 100% of production traffic.
`/_stcore/health` returned `ok`. See AWS_DEPLOYMENT.md at repository root for
configuration, credentials, costs and cleanup. A healthy HTTP server alone was
not used as proof of working RAG.

## Portfolio site and film

Desktop (1440px) and mobile (390px) preview checks cover responsive layout,
walkthrough tabs and architecture tabs. The final website QA record is
[showcase-checks.json](showcase-checks.json). Diagram exports were visually
reviewed; editable XML and companion guides are included.

The 20-second silent BRAG film uses real application captures and recorded
results. Hyperframes checks include runtime, layout and text contrast; the
recorded check report is [video-check.json](video-check.json). Structural advice
warnings about using sub-compositions are retained; they do not indicate failed
runtime, layout or contrast checks.
