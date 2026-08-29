---
type: product-bug
target: vizaeo
source: page-maps/vizaeo/help
status: draft
---
# Fix the mobile help drawer accessibility

**Observed behavior.** At 390×844, the `/help` mobile navigation drawer
(opened via the `button[aria-label="Toggle navigation"]` hamburger) has four
distinct accessibility/behavior gaps, all directly verified:
- `Escape` does not close the drawer (the `<aside>` stays `display:block`).
- No body scroll lock while open (`body { overflow: visible }`), so the page
  scrolls behind the open drawer.
- The toggle button carries no `aria-expanded` attribute.
- Focus is never moved into the drawer on open — `document.activeElement`
  stays the hamburger button.

**Where.** `/help`, mobile navigation drawer, viewport ≤ sidebar breakpoint
(verified at 390x844).

**Evidence** (`page-maps/vizaeo/help/features.md`):
"**Mobile drawer a11y/behavior gaps** (all verified at 390x844): `Escape`
does **not** close the drawer (aside stays `display:block`). No body scroll
lock while open (`body { overflow: visible }`), so the page scrolls behind
the drawer. The toggle carries no `aria-expanded`, and focus is not moved into
the drawer on open (`document.activeElement` stays the hamburger)."

**Expected behavior.** Standard disclosure-pattern behavior: `Escape` closes
the open drawer; body scroll is locked while the drawer is open; the toggle
button reflects state via `aria-expanded`; focus moves into the drawer's
first focusable element on open (and returns to the toggle on close).

**Impact.** Keyboard and assistive-tech users on mobile cannot reliably
operate or dismiss the only navigation surface available below the sidebar
breakpoint — the drawer traps neither focus correctly nor communicates its
own state, and the page scrolls unexpectedly behind it while open.
