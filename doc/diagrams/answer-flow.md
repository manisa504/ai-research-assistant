# Question answering

1. Auto uses documents when uploaded; General and Documents explicitly override.
2. Embed the question with Bedrock Titan V2 (amazon.titan-embed-text-v2:0) and retrieve up to four cosine matches from the session-local FAISS index.
3. Bedrock Nova Lite (amazon.nova-lite-v1:0) receives the question and retrieved evidence through Converse in us-east-2.
4. Validate its JSON, source IDs and verbatim quotes before showing a cited answer.
5. Abstain for missing/unverifiable support; use direct inference for General mode.

Citation checks prove provenance, not semantic correctness. Exact-match evidence and prompt instructions do not guarantee resistance to every malicious PDF. Inspect source text and evaluate behavior.
