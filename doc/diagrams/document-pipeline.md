# Document ingestion

1. Validate PDF bytes and extract pages in memory.
2. Preserve blank pages and one-based metadata.
3. Split text into overlapping windows without crossing pages.
4. On explicit Build index, send chunks to Amazon Bedrock Titan V2 (amazon.titan-embed-text-v2:0) via InvokeModel in us-east-2.
5. Store normalized 256-dimensional vectors in the session-local FAISS IndexFlatIP beside filename/page metadata.

Malformed/encrypted files are rejected individually. Upload or settings changes invalidate old evidence. The 200-chunk cap bounds demonstration usage; there is no durable/shared store.
