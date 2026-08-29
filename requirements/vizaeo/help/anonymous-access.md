---
approved: false
---
# /help — anonymous access to the Help Center

- target: vizaeo
- slug: help
- source: `page-maps/vizaeo/help/features.md` ("What the page is for",
  "Broken / suspect" item 3)
- ticket: `tickets/drafts/2026-08-29-cover-anonymous-access-to-the-help-center.md`

The docs are a public sales/support surface and a deliberate exception to the
app's default posture. An auth-middleware matcher change that accidentally
swallows `/help` would gate the whole help center behind login with no loud
failure, and nothing else in the suite would notice.

## Scenario 1 — the Help Center index is public

**Given** a visitor with no session
**When** they request `/help`
**Then** the response status is 200
**And** the browser stays on `/help` — it is not redirected to `/login`
**And** the page renders the `h1` "Help Center".

## Scenario 2 — every help article is public

**Given** a visitor with no session
**When** they request each of the ten article routes —
`/help/getting-started`, `/help/what-is-vizaeo`, `/help/how-ai-visibility-works`,
`/help/understanding-results`, `/help/deep-reports`, `/help/metrics`,
`/help/platforms`, `/help/account`, `/help/faq`, `/help/support`
**Then** each response status is 200
**And** the browser stays on the requested path — none is redirected to `/login`
**And** each article renders a level-1 heading.

`/help/deep-reports` is included even though no card links to it (see
`card-grid.md`), because the sidebar does.

## Scenario 3 — control: the same anonymous session is still gated elsewhere

**Given** the same visitor with no session
**When** they request `/dashboard`
**Then** they are redirected to `/login?redirect_url=%2Fdashboard`.

Without this control, Scenarios 1 and 2 would also pass for an accidentally
authenticated session, and would therefore prove nothing about public access.
## Judgment calls
- Treats public anonymous access to /help and all ten articles as the
  intended contract (not an oversight), and pins /dashboard remaining
  Clerk-gated as the control.
