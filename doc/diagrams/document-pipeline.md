# Document ingestion

1. Validate PDF bytes and extract pages in memory.
2. Preserve blank pages and one-based metadata.
3. Split text into overlapping windows without crossing pages.
4. Send chunks to Titan V2 on explicit Build index.
5. Normalize vectors and store them in FAISS beside metadata.

Malformed/encrypted files are rejected individually. Upload or settings changes invalidate old evidence. The 200-chunk cap bounds demonstration usage; there is no durable/shared store.
