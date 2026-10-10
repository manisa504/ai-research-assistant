"""Run the small real-Bedrock evaluation; incurs API charges, never runs in pytest."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from bedrock_client import BedrockClient
from document_processor import extract_pdf_pages, chunk_pages
from rag import RAGIndex


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "doc/evidence/evaluation_results.csv")
    args = parser.parse_args()
    client = BedrockClient()
    pages = extract_pdf_pages((ROOT / "sample_docs/research_notes.pdf").read_bytes(), "research_notes.pdf")
    index = RAGIndex.build(chunk_pages(pages), client)
    cases = json.loads((ROOT / "tests/evaluation_cases.json").read_text())
    rows = []
    for case in cases:
        result = index.answer(case["question"], client)
        absent = case.get("absent", False)
        retrieval = absent or any(hit["page"] in case.get("accepted_pages", [case.get("page")]) for hit in result.retrieved[:2])
        citation = (not result.sources and not result.supported) if absent else (
            bool(result.sources) and all(source["quote"] in source["text"] for source in result.sources)
            and any(source["page"] in case.get("accepted_pages", [case.get("page")]) for source in result.sources))
        correct = not result.supported if absent else result.supported and all(
            re.search(term, result.text, re.I) for term in case["terms"])
        row = {"id": case["id"], "question": case["question"], "expected": "absent" if absent else " & ".join(case["terms"]),
               "retrieval_pass": bool(retrieval), "citation_pass": bool(citation), "correctness_pass": bool(correct),
               "passed": bool(retrieval and citation and correct), "answer": result.text,
               "region": client.region, "chat_model": client.chat_model,
               "embedding_model": client.embedding_model, "timestamp_utc": datetime.now(timezone.utc).isoformat()}
        rows.append(row)
        print(f'{case["id"]}: {"PASS" if row["passed"] else "FAIL"} — {result.text}', flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f'{sum(row["passed"] for row in rows)}/{len(rows)} passed; results: {args.output}')
    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
