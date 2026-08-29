# /pricing — public pricing / primary-offer landing page

Status: **new** page map (first capture 2026-08-29).
Judged live at 1280x800 via Playwright MCP.

## What the page is for

The public, unauthenticated sales page for the single paid product: a one-time
AI Visibility Report. Its whole job is to move a visitor to `/signup` — it is a
single-column `<main>` with exactly one link on the entire page and no chrome
at all (no `<header>`, no `<footer>`, no `<nav>`).

## User-visible features

1. **Hero.** Eyebrow "Stop guessing how AI sees your business", `h1` "Your
   competitors are showing up in AI answers. Are you?", and a supporting
   paragraph about ranking vs competitors.
2. **Primary offer card.** Labeled "Primary offer"; `h2` "YOUR AI VISIBILITY
   REPORT"; price **$89**; note "one-time purchase"; badge "Early Adopter
   Pricing — Limited Time".
3. **The only CTA on the page.** "Get Your Visibility Scoreboard" → `/signup`.
   Signup-first flow (no direct-to-Stripe path from this page).
4. **Four inclusion bullets.** "🏆 10 competitors included, $10 each for more",
   "📋 Visibility Improvement Checklist — what to fix first", "✅ No
   subscription — one-time purchase", "⚡ Delivery in minutes for most
   businesses". The `10` and `$10` render as separate interpolated children in
   the RSC payload (`["🏆 ", 10, " competitors included, ", "$10", …]`), i.e.
   they come from pricing config rather than being hardcoded prose — that
   binding is exactly what a test should pin.
5. **"Know exactly what to do next" section.** Explains the Visibility
   Improvement Checklist as a prioritized, points-ranked action list.
6. **"How it works" — three numbered steps.** (1) enter business + competitors,
   (2) "We check how 5 AI platforms rank you vs competitors", (3) get the
   scoreboard + checklist.
7. **Sample scoreboard preview.** Three static stat tiles: "Overall AI
   visibility 72 / 100", "Competitor benchmark +14%", "Highest-impact action
   Improve service page intent matching". Illustrative sample data, not live.
8. **FAQ accordion (interaction-revealed).** Four native
   `<details>/<summary>` items, all collapsed on load; the answer body is
   absent from the a11y tree until expanded. Verified by clicking "What do I get
   after purchase?" — it expanded and revealed its paragraph; items open
   independently (no single-open group behavior). Questions: what you get after
   purchase / is it a subscription / delivery speed / payment + data security.

## Broken / suspect

- **No navigation whatsoever.** Zero `<nav>`, no header, no footer, and one
  single `<a>` on the page. A visitor who does not want to sign up has no
  in-page route anywhere else — including no link to `/help`, which matches the
  known help-discoverability gap.
- **Console (anonymous load):**
  - `GET /icon-192.png` → **404**, followed by the manifest icon warning. (No
    `/favicon.ico` 404 here — it was already cached from the `/help` visit in
    the same session, so treat the favicon 404 as site-wide, not help-only.)
  - `[PostHog] API key not found. Analytics disabled.`
  - Two `preloaded … but not used` CSS warnings (same two chunks as `/help`).
- **No dead links** — the sole link `/signup` is in-app and not exercised
  (read-only pass, no account creation).
- Perf is clean: LCP 352ms, CLS 0, INP 112ms (measured off the FAQ click).

## Capture note

`page.json.status_code` reads `307` here too while a direct request returns
`200` and `final_url` matches. Same `scripts/crawl.py` reporting artifact as on
`/help`, not a real redirect. Raised to the Steward in the run summary.
