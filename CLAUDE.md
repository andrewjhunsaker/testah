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
- Branch per pass (`scout/<date>`, `author/<date>`, ISO dates) and open a
  PR; the human merges.
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
