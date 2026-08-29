---
approved: false
---
# /pricing — primary CTA route

- target: vizaeo
- slug: pricing
- source: `page-maps/vizaeo/pricing/features.md` (feature 3, "Broken / suspect"
  item 1), `page-maps/vizaeo/pricing/page.json`
- ticket: `tickets/drafts/2026-08-29-cover-the-pricing-page-primary-cta-route.md`

"Get Your Visibility Scoreboard" → `/signup` is the entire conversion path of
the public site, and it is the only link on the page. If it breaks, `/pricing`
becomes a dead end and no other test in the suite touches it.

## Scenario 1 — the CTA renders and is the page's only link

**Given** an anonymous visitor
**When** they open `/pricing`
**Then** the page renders the `h1` "Your competitors are showing up in AI
answers. Are you?"
**And** a link labelled "Get Your Visibility Scoreboard" is visible
**And** its `href` is `/signup`
**And** it is the **only** link on the entire page — exactly one, pinning the
signup-first, no-direct-to-checkout flow. A second link appearing here (a
header, a footer, a direct-to-Stripe path) is a deliberate change, not an
accident.

## Scenario 2 — following the CTA reaches the signup page

**Given** an anonymous visitor on `/pricing`
**When** they click "Get Your Visibility Scoreboard"
**Then** the browser lands on `/signup`
**And** the signup page renders its account form — the `h1` "Welcome to
Vizaeo", an "Email" textbox, and a "Continue" button.

The rendered form is the observable form of "the signup page loaded"; a click
is a client-side navigation and exposes no HTTP status. No account is created:
the test stops at the rendered form and never submits.