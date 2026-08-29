---
type: framework-update
target: vizaeo
source: reviews/2026-08-28.md
status: draft
---
# Resolve the SignupPage page-map gap

**What's wrong in our code.** `tests/pages/SignupPage.ts` exists and is used by
`tests/specs/pricing-primary-cta.spec.ts`, but `page-maps/vizaeo/signup/` does
not exist. RULES.md states, without qualification:

> Selectors come from the page-map (`page-maps/<target>/<slug>/page.json`).

So a POM in the suite is sourcing selectors from something other than a
page-map, and RULES.md — a human-owned file the Author and Reviewer treat as
law — has no provision for it. Raised by the Reviewer in
`reviews/2026-08-28.md` ("Notes", `SignupPage` bullet) and carried forward
unresolved into `reviews/2026-08-28-2.md`, explicitly marked as a Steward item.

**Where.**
- `tests/pages/SignupPage.ts` — three locators, all `getByRole`
  (`heading "Welcome to Vizaeo"`, `textbox "Email"`, `button "Continue"`).
- `RULES.md` — "Page Object Model" section, and the "Bootstrap exception"
  section, which currently ends "No other exemptions exist."
- `targets.yaml` — `/signup` is not a designated page.

**Why it is not simply a violation.** `/signup` is the *destination* of a
criterion about `/pricing`, not a page under test:
`requirements/vizaeo/pricing/primary-cta-route.md` Scenario 2 names all three
elements itself ("the `h1` 'Welcome to Vizaeo', an 'Email' textbox, and a
'Continue' button"), so the selectors trace to an approved criterion even
though they do not trace to a page-map. They are `getByRole`, the top of the
RULES.md preference order, the class documents the deviation in its docstring,
and nothing in it submits the form. The Reviewer verified the flow live and
passed it. The same shape already recurs elsewhere:
`tests/specs/help-anonymous-access.spec.ts:41` navigates to `/dashboard` with
no POM at all, as a deliberate control.

The gap is that the rule and the practice disagree, and no artifact records
which one is meant to win. Left alone, the next agent either invents a
precedent or blocks on it.

**Suggested direction — the human picks one; both are cheap.**

**Option A — designate `/signup`.** Add it to `targets.yaml` (`auth: none`) and
let Scout capture `page-maps/vizaeo/signup/`. Restores the rule literally, and
adds real value: `/signup` is the top of the conversion funnel and currently
has no map. Cost: Scout must judge a page carrying a live Clerk form without
submitting it (its guardrails already forbid destructive submissions), and the
suite gains a page-map it does not otherwise test, which then needs to be kept
current like any other.

**Option B — carve out destination-only pages in RULES.md.** Extend the Page
Object Model section with a bounded exception, roughly: *a POM for a page that
is only ever a navigation destination of another page's criterion may source
selectors from that approved criterion instead of a page-map, provided every
locator is `getByRole`, the class docstring states the deviation, and nothing
in it mutates state.* Cheaper, and it names a category that will recur (any
CTA that leaves a designated page). Cost: the exemption list stops being a
single grandfathered file, so it needs to stay narrow.

Whichever is chosen, RULES.md changes in the same PR — its "No other
exemptions exist" line is currently false, and that is the part an agent will
trip over first. This ticket asks for a decision, not for code: the human owns
RULES.md and `targets.yaml`, and agents never edit either.
