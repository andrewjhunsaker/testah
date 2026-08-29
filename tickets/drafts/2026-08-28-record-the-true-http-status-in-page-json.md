---
type: framework-update
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Record the true HTTP status in page.json

**What's wrong in our code.** `scripts/crawl.py` writes
`"status_code": result.status_code` straight from the crawl4ai result. Both
pages captured in the first Scout run carry `307`:

- `page-maps/vizaeo/help/page.json` → `"status_code": 307`
- `page-maps/vizaeo/pricing/page.json` → `"status_code": 307`

Neither page actually redirects. Scout verified independently (recorded in the
"Capture note" section of both `features.md` files) that a direct request to
each URL returns **200** with no redirect, and `final_url` in the same
`page.json` equals the requested URL. It is not trailing-slash
canonicalization — `/help/` returns 308, a different code — and a Chrome UA
also gets 200. So the recorded `307` is a capture artifact, not a property of
the target.

**Where.** `scripts/crawl.py`, `crawl_page()` — the `page` dict assembled
before `page.json` is written:

    page = {
        "url": url,
        "final_url": result.redirected_url or url,
        "status_code": result.status_code,
        **extract_elements(result.html),
    }

**Why it matters.** `page.json` is a contract surface, not a scratch file.
Every consumer that trusts `status_code` reads *every* designated page as a
redirect:

- `agents/scout.md` step 3 tells Scout to run a redirect check. It happens to
  compare `final_url` by normalized path rather than reading `status_code`, so
  the artifact did not quarantine two healthy pages this run — but the
  procedure is one edit away from doing exactly that.
- `requirements/vizaeo/help/anonymous-access.md` Scenario 1 asserts "the
  response status is 200". The criterion is grounded in Scout's live check, not
  in `page.json`; a future criterion generated from `page.json` alone would
  encode 307 as expected behavior and pin a fiction.
- `scripts/drift.py` hashes `page.json` as part of the drift input
  (`page_content()`), so a status value that wobbles between captures produces
  phantom drift and a spurious mailbox entry for the Author.

**Suggested direction.** Do not hand-patch the value; establish what the field
means and make it verifiable.

1. Determine why crawl4ai reports 307 for a 200 response (most likely it is
   surfacing the status of an intermediate/prefetch response from the browser
   session rather than the final document response for `url`).
2. Either take the status from the final document response, or record an
   authoritative status alongside it — e.g. a plain `httpx` GET of `url` with
   `follow_redirects=False`, written as `http_status`, keeping the
   crawler-reported value under a clearly-named key if it is still useful.
3. Add an internal consistency check in `crawl_page()`: when `final_url` equals
   `url` by normalized path, a 3xx `status_code` is contradictory — raise, or
   record it as an anomaly, rather than writing it silently. `crawl.py`
   already fails loudly on `not result.success`; this is the same principle.
4. Cover it in `scripts/tests/test_crawl.py`: a fixture where the crawl result
   claims 3xx while `final_url` matches the request must not produce a
   `page.json` that quietly asserts a redirect.
5. Re-capture both page-maps after the fix so the committed artifacts stop
   carrying the wrong value.
