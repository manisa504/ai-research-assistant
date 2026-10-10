"""Check locally served showcase assets, tabs, media and responsive layout."""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets, self.ids = [], set()
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.ids.add(attributes.get("id", ""))
        for name in ["href", "src", "poster"]:
            if attributes.get(name):
                self.targets.append(attributes[name])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8765")
    parser.add_argument("--channel", default=None)
    args = parser.parse_args()
    links = Links()
    links.feed((ROOT / "doc/index.html").read_text())
    relative_count = 0
    for target in links.targets:
        parts = urlsplit(target)
        if parts.scheme or parts.netloc:
            continue
        if parts.path:
            assert (ROOT / "doc" / unquote(parts.path)).is_file(), target
        elif parts.fragment:
            assert parts.fragment in links.ids, target
        relative_count += 1
    checks = [f"{relative_count} relative asset/fragment links resolve"]
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel)
        for width, height, label in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
            page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda response: errors.append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
            page.goto(args.url)
            assert page.evaluate("document.documentElement.scrollWidth") == width
            for tab in page.get_by_role("tab").all():
                tab.click()
                expect(tab).to_have_attribute("aria-selected", "true")
                panel = page.locator("#" + tab.get_attribute("aria-controls"))
                expect(panel).to_be_visible()
                image = panel.locator("img")
                image.scroll_into_view_if_needed()
                expect(image).to_be_visible()
                page.wait_for_function("[...document.querySelectorAll('[role=tabpanel]:not([hidden]) img')].every(i=>i.complete&&i.naturalWidth>0)")
            first = page.locator("#step-1")
            first.click()
            first.press("ArrowDown")
            expect(page.locator("#step-2")).to_be_focused()
            expect(page.locator("#step-2")).to_have_attribute("aria-selected", "true")
            page.locator("#arch-1").click()
            page.locator("#arch-1").press("ArrowRight")
            expect(page.locator("#arch-2")).to_have_attribute("aria-selected", "true")
            video = page.locator("video")
            video.scroll_into_view_if_needed()
            page.wait_for_function("document.querySelector('video').readyState >= 1")
            assert page.evaluate("document.querySelector('video').duration") == 20
            assert video.get_attribute("controls") is not None
            assert page.evaluate("document.documentElement.scrollWidth") == width
            checks += [f"{label}: no horizontal overflow", f"{label}: all tabs, images and keyboard navigation pass", f"{label}: 20-second video loads with playback controls"]
            page.locator("#step-1").click()
            page.locator("#arch-1").click()
            page.evaluate("window.scrollTo(0,0)")
            page.screenshot(path=str(ROOT / f"doc/evidence/showcase-{label}.png"), full_page=True)
            page.close()
        browser.close()
    assert not errors, errors
    checks.append("no browser JavaScript errors or HTTP errors")
    report = {"passed": True, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
              "scope": "Local static site; external sites not audited"}
    (ROOT / "doc/evidence/showcase-checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
