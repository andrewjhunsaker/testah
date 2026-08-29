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

**No tracker connected? Nothing breaks.** `tickets/drafts/` is a
fully-functional local ticket queue — agents draft into it, the human
approves in it. When a tracker comes online, drain the queue:
`uv run python -m scripts.file_tickets` (CLI-first; for Linear it uses
`LINEAR_API_KEY` from the environment or a gitignored `.env`). Filed drafts
get stamped `status: filed:<id>` in place.

## Running the agents on your LLM platform

The agents are plain markdown instruction files in `agents/` — there is no
testah-specific runtime. Any agentic harness that can (1) read/write files
and run shell commands, (2) drive a browser (an MCP or its own tooling), and
(3) spawn a fresh-context subagent for the Reviewer can run the loop: start
a session in this repo and give it one agent file as its instructions
(e.g. "Follow agents/scout.md for target <key>"). Claude Code is the
reference harness (`.mcp.json` wires Chrome DevTools + Linear MCPs), but
Cursor, Copilot CLI, Codex, Gemini CLI, or a custom Agent-SDK program work
the same way — the repo's committed artifacts are the only interface between
passes, and the Playwright suite itself runs with no LLM at all.
