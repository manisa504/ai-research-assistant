# BRAG plan — AI Research Assistant

## Nine-question planning rubric

1. **App:** A working PDF research assistant with Bedrock embeddings, FAISS retrieval, and page citations.
2. **Strongest claim:** An answer you can trace back to a page, demonstrated with a real source and quote.
3. **Visual hook:** Editorial forest green (#183e32), warm paper (#f5f3eb), lime (#d8eb85), and a citation appearing beside the answer.
4. **Actual UI:** Real Streamlit upload, index, question and supporting evidence captures from the fictional public sample.
5. **Shortest satisfying video:** 20 seconds, 1280×720 landscape.
6. **Tone:** Polished; a restrained engineering product film with serif headlines and decisive, readable motion.
7. **Audio:** Intentional silence. This portfolio clip is designed for muted recruiter feeds; on-screen copy carries the full story. No music, SFX, narration, or audio-reactive visuals.
8. **Share caption:** I built a PDF research assistant that answers with Amazon Bedrock and links every supported claim back to a source page. Python, FAISS, a scoped AWS task role, and a reproducible evaluation.
9. **User flow:** Upload a PDF → build its embedding index → ask a question → inspect the answer and page quote.

## Storyboard — 20 seconds total

### 0–3s / Hook
“An answer. A page to prove it.” Large serif type, source-page motif, small project label. Fast settle, readable hold. No audio. Clean cut.

### 3–9s / Upload and index
Actual upload screenshot on the right, “Your PDF. Searchable evidence.” on the left. Sequential filename, 3 pages, 2 chunks annotation. Explain Titan + FAISS in one short footer. No simulated progress or fabricated timing. No audio. Clean cut.

### 9–16s / Ask and verify
Actual answer screenshot. Show the real question, 18 degrees Celsius answer, and research_notes.pdf / page 2. The quote is real fictional demonstration data, not scientific findings. A subtle screenshot reveal then a citation lockup. No audio. Clean cut.

### 16–20s / Proof and outro
“Built. Tested. Deployed.” with 39 passing offline tests and 12/12 live Bedrock cases, clearly labelled as demo evaluation. Project name and “Explore the source.” Hold the final frame. No audio.

## Source and limits
Read doc/index.html, doc/styles.css, app.py, rag.py, bedrock_client.py, README.md and recorded evaluation results. Use only the public fictional sample and application UI. No personal/customer data or secrets. Do not imply the 12-case evaluation establishes production accuracy.
