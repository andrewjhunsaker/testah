---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/help
status: draft
implemented: requirements/vizaeo/help/card-grid.md
---
# Cover the Help Center article card grid on /help

**Feature.** `/help` renders a grid of nine article cards, each an `<a>`
wrapping an emoji, a title, and a one-line description, linking to
`/help/getting-started`, `/help/what-is-vizaeo`, `/help/how-ai-visibility-works`,
`/help/understanding-results`, `/help/metrics`, `/help/platforms`,
`/help/account`, `/help/faq`, `/help/support`.

**Why it needs coverage.** This grid is the only discovery surface for the docs
on desktop, and it is already out of sync with the sidebar: the sidebar links
`/help/deep-reports` (HTTP 200) but no card exists for it — 9 cards against 10
articles. A test asserting card-set == sidebar-article-set would have caught
that, and will catch the next article added to one list but not the other. All
nine hrefs should also be asserted to resolve (200, not 404) so a renamed help
route can't silently rot the index.

**Source.** `page-maps/vizaeo/help/features.md` (feature 4, "Broken / suspect"
item 2), `page-maps/vizaeo/help/page.json`.
