"""Real-browser RAG smoke test; uses public fictional notes and incurs Bedrock charges.

Install: pip install playwright; playwright install chromium
Run: python scripts/browser_smoke.py --url https://your-app.example
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8501")
    parser.add_argument("--channel", default=None, help="Optional installed browser, e.g. chrome")
    args = parser.parse_args()
    output = ROOT / "doc/evidence"
    output.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.goto(args.url, wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="AI Research Assistant", exact=True)).to_be_visible(timeout=30000)
        expect(page.get_by_role("button", name="Build index", exact=True)).to_be_disabled()
        checks.append("empty session has no index")
        page.screenshot(path=str(output / "01-upload.png"), full_page=True)
        page.locator('input[type=file]').set_input_files(str(ROOT / "sample_docs/research_notes.pdf"))
        summary = page.get_by_text("research_notes.pdf — 3 pages, 2 chunks", exact=True)
        expect(summary).to_be_visible(timeout=30000)
        summary.click()
        expect(page.get_by_test_id("stMetricValue").nth(1)).to_have_text("3")
        expect(page.get_by_test_id("stMetricValue").nth(2)).to_have_text("2")
        checks.append("sample upload preserves 3 pages and produces 2 chunks")
        page.screenshot(path=str(output / "02-pages.png"), full_page=True)
        page.get_by_role("button", name="Build index", exact=True).click()
        expect(page.get_by_text("Indexed 2 chunks. Ready for document questions.", exact=True)).to_be_visible(timeout=120000)
        checks.append("real Titan embeddings build FAISS index")
        page.get_by_role("textbox", name="Your question", exact=True).fill("What was the average temperature?")
        page.get_by_role("button", name="Ask", exact=True).click()
        expect(page.get_by_text("Answer mode: documents", exact=True)).to_be_visible(timeout=120000)
        answer = page.get_by_test_id("stText").filter(has_text="[research_notes.pdf, p. 2]").first
        expect(answer).to_contain_text("[research_notes.pdf, p. 2]")
        checks.append("real Nova answer gives 18 Celsius with page 2 citation")
        page.get_by_role("heading", name="Ask a question", exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(output / "03-answer.png"), full_page=False)
        page.get_by_test_id("stMain").screenshot(path=str(output / "answer-panel.png"))
        page.get_by_role("textbox", name="Your question", exact=True).fill("What was the research budget in dollars?")
        page.get_by_role("button", name="Ask", exact=True).click()
        expect(page.get_by_text("I couldn't find supporting information in the uploaded documents.", exact=True)).to_be_visible(timeout=120000)
        checks.append("absent budget produces explicit abstention")
        page.screenshot(path=str(output / "04-abstention.png"), full_page=True)
        page.get_by_test_id("stRadio").get_by_text("General", exact=True).click()
        page.get_by_role("textbox", name="Your question", exact=True).fill("What is retrieval augmented generation? Answer in one sentence.")
        page.get_by_role("button", name="Ask", exact=True).click()
        expect(page.get_by_text("Answer mode: general", exact=True)).to_be_visible(timeout=120000)
        checks.append("General mode routes directly to Bedrock")
        browser.close()
    report = {"passed": True, "checks": checks, "url": args.url,
              "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    (output / "browser-smoke.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
