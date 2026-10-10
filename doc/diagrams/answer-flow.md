# Question answering

1. Auto uses documents when uploaded; General and Documents explicitly override.
2. Embed a document question and retrieve top four cosine matches.
3. Nova Lite receives the question and retrieved evidence.
4. Validate its JSON, source IDs and verbatim quotes before showing a cited answer.
5. Abstain for missing/unverifiable support; use direct inference for General mode.

Citation checks prove provenance, not semantic correctness. Exact-match evidence and prompt instructions do not guarantee resistance to every malicious PDF. Inspect source text and evaluate behavior.
