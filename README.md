# testah

A multi-agent QA testing loop: agents map a target webapp, generate an
agentless Playwright suite from the map, triage failures, and draft Linear
tickets — with a human approving every consequential step.

- **Design:** [docs/spec.md](docs/spec.md)
- **How to run each pass:** [docs/running-the-loop.md](docs/running-the-loop.md)
- **Agents:** [agents/](agents/) — Scout · Author · Reviewer · Steward (+ Gauge, phase 2)
- **Run the suite (no agents needed):** `pnpm exec playwright test`
- **Human-owned config:** [targets.yaml](targets.yaml) (what to map), [RULES.md](RULES.md) (how to test)
