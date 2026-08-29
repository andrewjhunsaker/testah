# /help — Help Center index

Status: **new** page map (first capture 2026-08-29).
Judged live at 1280x800 and 390x844 via Playwright MCP.

## What the page is for

The documentation landing page for Vizaeo. Public (no auth): reachable
anonymously, unlike `/` which 307s to `/login` on staging. It is a hub — it
holds no help content of its own, only an index into nine `/help/*` articles,
plus a persistent left sidebar that repeats the same set grouped into four
sections.

## User-visible features

1. **Doc-shell top bar.** "Vizaeo" wordmark link → `/dashboard`, a `|`
   separator, the static label "Documentation", and a right-aligned
   "← Back to app" link → `/dashboard`.
2. **Sectioned sidebar navigation** (`<aside><nav>`, 11 links) grouped under
   four static headings:
   - Overview — Help Center, What is Vizaeo?, How AI Visibility Works
   - Using Vizaeo — Getting Started, Understanding Your Results,
     Competitor Deep Reports
   - Reference — The 11 Visibility Metrics, The Five AI Platforms,
     Account & Settings
   - Support — FAQ, Contact Support
3. **Page heading + subtitle.** `h1` "Help Center" and the line "Everything you
   need to understand AI visibility and use Vizaeo effectively."
4. **Card grid of nine article cards.** Each card is a single `<a>` wrapping an
   emoji, a title, and a one-line description: Getting Started 🚀, What is
   Vizaeo? 💡, How AI Visibility Works 🧠, Understanding Your Results 📊, The 11
   Visibility Metrics 📏, The Five AI Platforms 🤖, Account & Settings ⚙️, FAQ
   ❓, Contact Support 💬.
5. **Mobile navigation drawer (interaction-revealed).** Below the sidebar
   breakpoint a hamburger `button[aria-label="Toggle navigation"]`
   (`.help-hamburger`, 44x44, `display:none` at desktop width) appears in the
   top bar. Clicking it shows a fixed 260px-wide `<aside>` (`z-index:50`)
   carrying all 11 nav links over a full-viewport backdrop
   (`.layout-module__…__overlay`, `z-index:40`). Clicking the backdrop closes
   the drawer. Verified at 390x844.
6. **Theme bootstrap.** An inline head script reads
   `localStorage['vizaeo-theme-preference']` (falling back to
   `prefers-color-scheme`) and stamps `theme-light` / `theme-dark` on `<html>`
   before paint. No theme control is exposed on this page — it inherits only.

## Broken / suspect

- **CLS 0.2788 — "poor" by Core Web Vitals (>0.25), reproducible.** A single
  layout shift at t≈203ms whose sources are `MAIN.help-content` and four
  `A.…__card` elements: the card grid reflows after first paint. Same value on
  two independent loads. This is the one real perf defect on the page (LCP is
  fine at 240–1316ms).
- **"Competitor Deep Reports" is missing from the card grid.** The sidebar
  links `/help/deep-reports` (which returns 200), but no card exists for it —
  the grid has 9 cards against the sidebar's 10 articles. Content/nav
  inconsistency.
- **Both top-bar links dead-end for anonymous visitors.** The "Vizaeo"
  wordmark and "← Back to app" both point at `/dashboard`, which 307s to
  `/login?redirect_url=%2Fdashboard`. `/help` is publicly reachable, so a
  logged-out reader has no working way back to marketing content — there is no
  `<footer>` on the page either.
- **Mobile drawer a11y/behavior gaps** (all verified at 390x844):
  - `Escape` does **not** close the drawer (aside stays `display:block`).
  - No body scroll lock while open (`body { overflow: visible }`), so the page
    scrolls behind the drawer.
  - The toggle carries no `aria-expanded`, and focus is not moved into the
    drawer on open (`document.activeElement` stays the hamburger).
- **Console (anonymous load):**
  - `GET /favicon.ico` → **404**
  - `GET /icon-192.png` → **404**, followed by
    `Error while trying to use the following icon from the Manifest: …/icon-192.png`
  - `[PostHog] API key not found. Analytics disabled. Set NEXT_PUBLIC_POSTHOG_KEY`
    — analytics is off on staging.
  - Two `preloaded using link preload but not used` warnings for
    `0o12a5rsd6q5k.css` and `1-781vpk_zf4c.css`.
- **No dead links.** All 10 `/help/*` targets return 200 (checked by HTTP
  status only, not crawled).

## Capture note

`page.json.status_code` reads `307` for this URL, but a direct request returns
`200` with no redirect, and `final_url` matches the request. It is not
trailing-slash canonicalization either (`/help/` → **308**), and a Chrome UA
also gets 200. Treat the recorded `307` as a `scripts/crawl.py` reporting
artifact, not a real redirect. Raised to the Steward in the run summary.
