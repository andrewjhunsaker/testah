# /pricing — FAQ accordion

- target: vizaeo
- slug: pricing
- source: `page-maps/vizaeo/pricing/features.md` (feature 8)
- ticket: `tickets/drafts/2026-08-29-cover-the-pricing-faq-accordion.md`

Four native `<details>/<summary>` items under the "FAQ" heading. The answers
carry commercial claims a buyer relies on — "not a subscription", "delivered in
minutes", "secure checkout" — and they are invisible to any static capture,
because the answer body is not rendered until the item is expanded.

## Scenario 1 — four questions, all collapsed on load

**Given** an anonymous visitor
**When** they open `/pricing`
**Then** a level-2 heading "FAQ" is visible
**And** exactly four FAQ items are present, with these summaries, in this order:
1. What do I get after purchase?
2. Is this a monthly subscription?
3. How quickly is the visibility scoreboard delivered?
4. Is my payment and business data secure?

**And** every item is collapsed, and none of the four answers is visible.

## Scenario 2 — expanding an item reveals its answer, verbatim

**Given** an anonymous visitor on `/pricing`
**When** they click a question summary
**Then** that item expands
**And** its answer becomes visible with exactly the copy of record:

| question | answer |
|---|---|
| What do I get after purchase? | You get a complete AI Visibility Scoreboard that shows where your brand appears, how often you are mentioned, and where you can improve your rankings. |
| Is this a monthly subscription? | No. This is a one-time purchase for a single visibility scoreboard run. You can come back and buy another run whenever you want a fresh read. |
| How quickly is the visibility scoreboard delivered? | Most visibility scoreboards are delivered in minutes after checkout. Complex businesses may take a bit longer, but we keep you updated throughout the run. |
| Is my payment and business data secure? | Yes. Checkout is processed through secure payment providers and your data is handled with encrypted transport and strict access controls. |

Asserting the exact answer text is the point: these are the commercial claims,
and a silent copy edit ("no subscription" → something weaker) should be a
conscious change.

## Scenario 3 — items open independently

**Given** an anonymous visitor on `/pricing`
**When** they expand "What do I get after purchase?" and then expand
"Is this a monthly subscription?"
**Then** both items are open at the same time and both answers are visible.

This pins the current independent-open behavior, so a redesign to single-open
accordion semantics is a conscious change rather than a silent one.
