# testah

Multi-agent QA testing loop: agents map a target webapp, generate an
agentless Playwright suite, triage failures, and draft tickets. The repo is
the message bus; the human gates every consequential step.

## Ground rules (all sessions)

- Run every command from the repo root.
- `RULES.md`, `targets.yaml`, `CLAUDE.md`, and `.claude/` are HUMAN-OWNED —
  agents never edit them (permission ask-gates enforce this; do not work
  around them via Bash).
- No AI attribution in commits or PRs.
- Work on a feature branch (`scout/<date>`, `author/<date>`, or another
  descriptive name) and open a PR into `staging`.
- Never push directly to `master`. Never merge into `master`: GitHub Actions
  maintains a bot-authored draft `staging` → `master` promotion PR. After local
  validation, mark it ready and stop for the human to approve and merge it.
- Follow the delivery and review policy in `AGENTS.md`, including the single
  staging CI + Codex review gate.
- Agent instructions live in `agents/*.md` — the single, harness-agnostic
  source of truth. Never restate them elsewhere; point to them.
- Any harness change (`.claude/`, `CLAUDE.md`, `.mcp.json`, hooks) updates
  `docs/running-the-loop.md` in the SAME commit; framework changes sync to
  the `template` branch automatically.

## Running the loop on Claude Code

- Start passes with the slash commands: `/scout <target>`,
  `/author <target>`, `/triage <run-id>`, `/steward`, and `/loop-status`
  (read-only state report). They are human-only triggers.
- The Author's reviewer checkpoint = spawn the `reviewer` agent type (fresh
  context; tools restricted to Read/Grep/Glob/Write).
- Operating procedure + gates: `docs/running-the-loop.md`. Design:
  `docs/spec.md`. Testing law: `RULES.md`. Designated targets:
  `targets.yaml`.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for the repository identified by
`git remote`. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the five default canonical labels. See `docs/agents/triage-labels.md`.

### Domain docs

Domain documentation uses a single-context layout. See `docs/agents/domain.md`.
