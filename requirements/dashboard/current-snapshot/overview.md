---
approved: true
---
# Dashboard — Current Snapshot Overview

- target: dashboard
- slug: current-snapshot
- source: GitHub Issue #2; `docs/adr/0001-live-local-control-plane.md`;
  `docs/adr/0002-project-external-history-locally.md`

## Scenario 1 — the operator can read current repository evidence

**Given** a repository with one configured Target and a completed report
**When** a QA Operator opens the loopback dashboard
**Then** the Overview identifies the repository and Target
**And** it displays the completed report counts, Evidence State, and last-check time.

## Scenario 2 — changed evidence refreshes automatically

**Given** the operator is viewing a completed Current Snapshot
**When** repository report evidence changes
**Then** the displayed counts refresh without a full-page navigation.

## Scenario 3 — a failed refresh retains the last good snapshot

**Given** the operator has already loaded a valid Current Snapshot
**When** the local dashboard interface becomes unavailable during refresh
**Then** the last good repository evidence remains visible
**And** the Overview displays an unavailable notice.

## Scenario 4 — background tabs do not poll

**Given** the operator has loaded a valid Current Snapshot
**When** its browser document becomes hidden and repository evidence changes
**Then** the displayed snapshot does not refresh while hidden
**And** it refreshes immediately when the document becomes visible again.
