"""Browser smoke check of the actual generated static Pages report (PR CI only)."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--screenshots", type=Path, required=True)
    args = parser.parse_args()
    args.screenshots.mkdir(parents=True, exist_ok=True)
    report = json.loads((args.site / "progress.json").read_text(encoding="utf-8"))
    count = len(report["corpora"])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        for width, height in ((1440, 900), (768, 1024), (375, 812)):
            for mode in ("light", "dark"):
                page = browser.new_page(viewport={"width": width, "height": height},
                                        color_scheme=mode)
                page.goto((args.site / "index.html").resolve().as_uri())
                assert page.locator(".corpus").count() == count
                assert page.locator(".ontology-cell").count() == count * 7
                assert page.locator(".research-row").count() == count
                assert page.locator('a[href$=".xml"]').count() == 0
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                    f"Horizontal overflow at {width}px / {mode}"
                )
                page.screenshot(path=args.screenshots / f"overview-{width}-{mode}.png")
                page.locator('a[href="#ontologies"]').click()
                assert page.locator("#ontologies").is_visible()
                page.screenshot(path=args.screenshots / f"ontologies-{width}-{mode}.png")
                details = page.locator(".corpus > details").first
                summary = details.locator("summary").first
                summary.focus()
                summary.press("Enter")
                assert details.evaluate("(element) => element.open")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                    f"Expanded corpus overflows at {width}px / {mode}"
                )
                tlh = page.locator(".corpus").filter(
                    has=page.get_by_role("heading", name="TLHdig", exact=True))
                assert tlh.count() == 1
                assert tlh.get_by_role("heading", name="Morphological analysis tags").is_visible()
                morph = next(d for c in report["corpora"] if c["corpus"] == "tlhdig-tf"
                             for d in c["scoped"]["domains"] if d["node"] == "analysis" and d["feature"] == "morph")
                assert f'{morph["positive_occurrences"]:,} / {morph["occurrences"]:,}' in tlh.inner_text()
                tlh.locator(":scope > details > summary").click()
                gaps = tlh.get_by_text("Node-value gaps", exact=False)
                gaps.click()
                assert tlh.get_by_text("Download full gap data", exact=True).first.is_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=args.screenshots / f"morphology-{width}-{mode}.png")
                page.close()
        browser.close()


if __name__ == "__main__":
    main()
