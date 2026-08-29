# testah

A multi-agent QA testing loop: agents map a target webapp, generate an
agentless Playwright suite from the map, triage failures, and draft tickets —
with a human approving every consequential step.

- **Design:** [docs/spec.md](docs/spec.md)
- **How to run each pass:** [docs/running-the-loop.md](docs/running-the-loop.md)
- **Agents:** [agents/](agents/) — Scout · Author · Reviewer · Steward (+ Gauge, phase 2)
- **Run the suite (no agents needed):** `pnpm exec playwright test`
- **Human-owned config:** [targets.yaml](targets.yaml) (what to map), [RULES.md](RULES.md) (how to test)

## Connect your tools

testah is **project- and tracker-agnostic**: point `targets.yaml` at any
website/webapp (multiple targets side by side are supported) and configure
its top-level `tracker:` block for wherever approved tickets should be
filed. Ticket drafts are plain markdown in `tickets/drafts/` — only the
Steward's filing step touches a tracker, so any issue tracker can slot in.
The reference implementation is Linear via MCP (see `.mcp.json`; the first
session prompts an OAuth flow where you pick your workspace). Live-browser
work uses Chrome DevTools MCP (also in `.mcp.json`), with any
Playwright-capable browser MCP as a drop-in fallback.
