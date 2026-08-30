---
name: loop-status
description: Read-only report of the loop's state from committed artifacts — no pass, no edits
disable-model-invocation: true
---

Answer "what is the state of the loop?" per `agents/steward.md` duty 3 —
from artifacts ONLY, strictly read-only, no full pass: `changed-pages.json`,
the latest `triage/` doc, `tickets/drafts/` counts by status and type, the
latest `critiques/` entry, `docs/coverage/` maps, and open approvals
(`requirements/` files with `approved: false`). Report concisely.
