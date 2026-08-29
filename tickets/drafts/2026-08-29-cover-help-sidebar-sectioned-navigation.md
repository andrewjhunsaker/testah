---
type: test-feature
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Cover the sectioned help sidebar navigation

**Feature.** The `/help` doc shell renders a persistent `<aside><nav>` with 11
links grouped under four static headings: Overview (Help Center, What is
Vizaeo?, How AI Visibility Works), Using Vizaeo (Getting Started, Understanding
Your Results, Competitor Deep Reports), Reference (The 11 Visibility Metrics,
The Five AI Platforms, Account & Settings), Support (FAQ, Contact Support).

**Why it needs coverage.** The sidebar is shared chrome across every `/help/*`
page, so a single regression takes down navigation for the whole documentation
section. Grouping and order are editorial decisions that no other test pins.
Cover: the four section headings render in order, each group holds its expected
links, every href resolves 200, and the current page ("Help Center") is
distinguishable from the rest.

**Source.** `page-maps/vizaeo/help/features.md` (feature 2),
`page-maps/vizaeo/help/page.json` (`nav` array).
