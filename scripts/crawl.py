"""Crawl one designated page into page.md + page.json artifacts.

Usage: uv run python scripts/crawl.py <url> <output-dir>
Deterministic capture only — description/judgment is the Scout agent's job.
"""

import asyncio
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup


def _selector(el) -> str | None:
    if el.get("data-testid"):
        return f'[data-testid="{el["data-testid"]}"]'
    if el.get("id"):
        return f'[id="{el["id"]}"]'
    return None


def extract_elements(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    return {
        "title": soup.title.get_text(strip=True) if soup.title else None,
        "headings": [
            {"level": int(h.name[1]), "text": h.get_text(strip=True)}
            for h in soup.find_all(["h1", "h2", "h3"])
        ],
        "nav": [
            {"text": a.get_text(strip=True), "href": a.get("href")}
            for nav in soup.find_all("nav")
            for a in nav.find_all("a", href=True)
        ],
        "links": [
            {"text": a.get_text(strip=True), "href": a["href"]}
            for a in soup.find_all("a", href=True)
        ],
        "buttons": [
            {"text": b.get_text(strip=True), "selector": _selector(b)}
            for b in soup.find_all("button")
        ],
        "forms": [
            {
                "selector": _selector(f),
                "fields": [
                    {"name": i.get("name"), "type": i.get("type", "text")}
                    for i in f.find_all("input")
                ],
            }
            for f in soup.find_all("form")
        ],
    }


async def crawl_page(url: str, out_dir: Path) -> dict:
    from crawl4ai import AsyncWebCrawler  # lazy: heavy import, not needed by tests

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
    if not result.success:
        raise RuntimeError(f"crawl failed for {url}: {result.error_message}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "page.md").write_text(str(result.markdown), encoding="utf-8")
    page = {
        "url": url,
        "final_url": result.redirected_url or url,
        "status_code": result.status_code,
        **extract_elements(result.html),
    }
    (out_dir / "page.json").write_text(
        json.dumps(page, indent=2) + "\n", encoding="utf-8"
    )
    return page


if __name__ == "__main__":
    asyncio.run(crawl_page(sys.argv[1], Path(sys.argv[2])))
