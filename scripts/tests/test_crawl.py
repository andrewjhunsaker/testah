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
    assert form["selector"] == "#signup"
    assert form["fields"] == [{"name": "email", "type": "email"}]


def test_nav_links_separate_from_all_links():
    out = extract_elements(HTML)
    assert out["nav"] == [{"text": "Pricing", "href": "/pricing"}]
    assert {"text": "External", "href": "https://example.com"} in out["links"]
    assert {"text": "Pricing", "href": "/pricing"} in out["links"]
