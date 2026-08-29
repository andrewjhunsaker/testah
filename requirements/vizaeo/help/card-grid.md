# /help — Help Center article card grid

- target: vizaeo
- slug: help
- source: `page-maps/vizaeo/help/features.md` (feature 4, "Broken / suspect" item 2),
  `page-maps/vizaeo/help/page.json`
- ticket: `tickets/drafts/2026-08-29-cover-help-center-article-card-grid.md`

The card grid is the only discovery surface for the documentation on desktop.
It is already out of sync with the sidebar — the sidebar links
`/help/deep-reports` but no card exists for it — so the criteria below pin
**today's** shape of both lists. Fixing the gap, or opening a second one, must
be a conscious change that turns these tests red on purpose.

## Scenario 1 — the grid renders exactly nine article cards

**Given** an anonymous visitor
**When** they open `/help`
**Then** the main content region shows the `h1` "Help Center" and its subtitle
"Everything you need to understand AI visibility and use Vizaeo effectively."
**And** the grid contains exactly nine article cards — no more, no fewer
**And** each card shows its emoji, its title, and its one-line description, and
links to its article:

| # | emoji | title | description | href |
|---|---|---|---|---|
| 1 | 🚀 | Getting Started | Set up your business and run your first AI visibility analysis. | `/help/getting-started` |
| 2 | 💡 | What is Vizaeo? | Understand AI visibility and why it matters for your business. | `/help/what-is-vizaeo` |
| 3 | 🧠 | How AI Visibility Works | The theory behind AI recommendations, scoring, and Share of Voice. | `/help/how-ai-visibility-works` |
| 4 | 📊 | Understanding Your Results | Learn what your Score, Gaps, Fix, and Watch tabs mean. | `/help/understanding-results` |
| 5 | 📏 | The 11 Visibility Metrics | What each metric measures and how to improve it. | `/help/metrics` |
| 6 | 🤖 | The Five AI Platforms | ChatGPT, Claude, Gemini, Grok, Perplexity — and how they differ. | `/help/platforms` |
| 7 | ⚙️ | Account & Settings | Themes, API keys, billing, privacy, and accessibility. | `/help/account` |
| 8 | ❓ | FAQ | Common questions about AI visibility, pricing, and features. | `/help/faq` |
| 9 | 💬 | Contact Support | Submit a ticket and track your support requests. | `/help/support` |

## Scenario 2 — every card routes to its article

**Given** an anonymous visitor on `/help`
**When** they click any one of the nine cards
**Then** the browser lands on that card's article path
**And** that article renders its own `h1`, which is the card's title for every
card except FAQ, whose article heading is "Frequently Asked Questions".

A card whose `href` still points somewhere but whose route has been renamed
would land on a 404 shell with a different (or no) `h1` — that is the failure
this scenario catches.

## Scenario 3 — the grid and the sidebar cover the same articles, minus one known gap

**Given** an anonymous visitor on `/help`
**When** they compare the card grid against the sidebar navigation
**Then** the sidebar lists eleven links — the `/help` index itself plus ten
articles
**And** the sidebar carries "Competitor Deep Reports" → `/help/deep-reports`
**And** the card grid carries **no** card for Deep Reports — the single known
content/nav inconsistency, pinned deliberately
**And** because the grid is also pinned at nine named cards (Scenario 1), the
next article added to one list but not the other turns this red.
