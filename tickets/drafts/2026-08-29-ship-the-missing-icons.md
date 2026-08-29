---
type: product-bug
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Ship the missing icons

**Observed behavior.** Both public pages checked (`/help` and `/pricing`)
throw console errors for missing icon assets on anonymous load:
`GET /favicon.ico` → 404, and `GET /icon-192.png` → 404 followed by a manifest
icon-resolution warning. The favicon 404 was only captured once (on `/help`;
already cached by the time `/pricing` was visited in the same session), but
the page map explicitly flags it as site-wide, not page-specific.

**Where.** Site-wide — reproduced independently on `/help` and `/pricing`.

**Evidence** (`page-maps/vizaeo/help/features.md`): "**Console (anonymous
load):** `GET /favicon.ico` → **404**. `GET /icon-192.png` → **404**, followed
by `Error while trying to use the following icon from the Manifest:
…/icon-192.png`."
(`page-maps/vizaeo/pricing/features.md`): "`GET /icon-192.png` → **404**,
followed by the manifest icon warning. (No `/favicon.ico` 404 here — it was
already cached from the `/help` visit in the same session, so treat the
favicon 404 as site-wide, not help-only.)"

**Expected behavior.** `/favicon.ico` and `/icon-192.png` should exist and
return 200, matching whatever the web app manifest declares, with no manifest
icon-resolution warnings in the console.

**Impact.** Every anonymous visitor to any page gets two 404s and a manifest
warning on first load — a visible browser-tab icon regression and a broken
PWA/manifest icon reference, on both pages checked so far.
