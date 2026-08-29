import asyncio
import json
import sys
import types

import pytest

from scripts.crawl import extract_elements

HTML = """<html><head><title>Acme</title></head><body>
<nav><a href="/pricing">Pricing</a></nav>
<h1>Welcome</h1>
<form id="signup"><input name="email" type="email">
<button data-testid="submit-btn">Sign up</button></form>
<a href="https://example.com">External</a>
</body></html>"""


def test_extracts_title_headings_buttons_forms():
    out = extract_elements(HTML)
    assert out["title"] == "Acme"
    assert out["headings"] == [{"level": 1, "text": "Welcome"}]
    assert {"text": "Sign up", "selector": '[data-testid="submit-btn"]'} in out["buttons"]
    form = out["forms"][0]
    assert form["selector"] == '[id="signup"]'
    assert form["fields"] == [{"name": "email", "type": "email"}]


def test_nav_links_separate_from_all_links():
    out = extract_elements(HTML)
    assert out["nav"] == [{"text": "Pricing", "href": "/pricing"}]
    assert {"text": "External", "href": "https://example.com"} in out["links"]
    assert {"text": "Pricing", "href": "/pricing"} in out["links"]


def _stub_crawl4ai(monkeypatch, result):
    class StubCrawler:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def arun(self, url):
            return result

    monkeypatch.setitem(
        sys.modules, "crawl4ai", types.SimpleNamespace(AsyncWebCrawler=StubCrawler)
    )


def test_crawl_page_writes_artifacts_with_final_url(tmp_path, monkeypatch):
    result = types.SimpleNamespace(
        success=True,
        error_message=None,
        status_code=200,
        redirected_url="https://x.test/login",
        markdown="# hi",
        html="<html><head><title>T</title></head><body></body></html>",
    )
    _stub_crawl4ai(monkeypatch, result)
    from scripts.crawl import crawl_page

    out = tmp_path / "pm"
    page = asyncio.run(crawl_page("https://x.test/", out))
    assert (out / "page.md").read_text() == "# hi"
    data = json.loads((out / "page.json").read_text())
    assert data["url"] == "https://x.test/"
    assert data["final_url"] == "https://x.test/login"
    assert data["status_code"] == 200
    assert page["title"] == "T"


def test_crawl_page_raises_on_failed_crawl_and_writes_nothing(tmp_path, monkeypatch):
    result = types.SimpleNamespace(
        success=False,
        error_message="boom",
        status_code=None,
        redirected_url=None,
        markdown=None,
        html="",
    )
    _stub_crawl4ai(monkeypatch, result)
    from scripts.crawl import crawl_page

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(crawl_page("https://x.test/", tmp_path / "pm"))
    assert not (tmp_path / "pm").exists()
