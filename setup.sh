#!/usr/bin/env bash
# testah interactive setup — run once after cloning:  bash setup.sh
# Every step is skippable and the script is safe to re-run.
set -o pipefail

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
ask()  { # ask "Question" [default y|n]
  local q="$1" d="${2:-y}" a
  if [ "$d" = y ]; then read -r -p "$q [Y/n] " a; a=${a:-y}
  else read -r -p "$q [y/N] " a; a=${a:-n}; fi
  case "$a" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

cd "$(dirname "$0")" || exit 1
if [ ! -t 0 ] && [ -z "$TESTAH_SETUP_TEST" ]; then
  echo "setup.sh is interactive — run it in a terminal: bash setup.sh"
  exit 1
fi

say "testah setup"
note "A few questions; everything is skippable and re-runnable (Ctrl-C any time)."

# ---------------------------------------------------------------- 1) remote
say "1/5 — Git remote"
remote_ready=n
if git remote get-url origin >/dev/null 2>&1; then
  origin_url=$(git remote get-url origin)
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo template)
  origin_default=y
  [ "$branch" = template ] && origin_default=n
  note "origin is currently: $origin_url"
  if ask "  Use this as the project remote?" "$origin_default"; then
    remote_ready=y
  else
    read -r -p "  Correct project remote URL (blank to skip): " url
    if [ -n "$url" ]; then
      git remote set-url origin "$url" && git push -u origin "$branch" \
        && remote_ready=y
    else
      note "remote setup skipped; origin was left unchanged."
    fi
  fi
else
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo master)
  read -r -p "  Connect a remote? [github/skip] " prov
  case "$prov" in
    github)
      if have gh; then
        read -r -p "  Repo (owner/name): " slug
        gh repo create "$slug" --private --source . --push \
          && { note "created and pushed."; remote_ready=y; } \
          || note "gh failed — add a remote manually later."
      else
        read -r -p "  Remote URL (git@github.com:you/repo.git): " url
        git remote add origin "$url" && git push -u origin "$branch" \
          && remote_ready=y
      fi ;;
    *) note "skipped — later: git remote add origin <url> && git push -u origin $branch" ;;
  esac
fi

if [ "$remote_ready" = y ]; then
  if bash scripts/bootstrap_release_branches.sh; then
    note "staging ready: feature PRs -> staging -> human-approved master."
  else
    note "staging needs a human-initialized remote master based on the pushed"
    note "template branch. Create it in GitHub, then run:"
    note "bash scripts/bootstrap_release_branches.sh"
  fi
fi

# ------------------------------------------------------------ 2) toolchain
say "2/5 — Dependencies (Playwright suite + Python toolchain for the Scout)"
if ask "  Install now?" y; then
  have pnpm || { have corepack && corepack enable >/dev/null 2>&1; }
  if have pnpm; then
    pnpm install && pnpm exec playwright install chromium \
      || { note "Playwright install failed — fix and re-run."; exit 1; }
  else
    note "pnpm not found. Install Node 20+ (with corepack) and re-run. Stopping here."
    exit 1
  fi
  if ! have uv && ask "  uv (Python manager) is missing — install it now?" y; then
    curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH"
  fi
  if have uv; then
    uv sync --group dev && uv run crawl4ai-setup \
      && { note "verifying framework unit tests:"; uv run pytest -q; } \
      || { note "Python toolchain failed — fix and re-run."; exit 1; }
  else
    note "continuing without uv — the Playwright suite works, but the Scout's"
    note "crawler and the helper scripts need uv. Re-run setup when installed."
  fi
else
  note "skipped."
fi

# --------------------------------------------------------------- 3) target
say "3/5 — Your first target (the website testah will map and test)"
overwrite=y
if [ -f targets.yaml ] && ! grep -q "replace me\|replace-me\|Replace the example" targets.yaml; then
  ask "  targets.yaml is already customized — replace it?" n || overwrite=n
fi
if [ "$overwrite" = y ] && ask "  Point testah at your site now?" y; then
  read -r -p "  Target key (short slug, e.g. myapp): " tkey
  read -r -p "  Base URL (e.g. https://staging.myapp.com): " turl
  read -r -p "  First public page path [/]: " tpath; tpath=${tpath:-/}
  read -r -p "  Slug for that page [home]: " tslug; tslug=${tslug:-home}
  if [ -n "$tkey" ] && [ -n "$turl" ]; then
    cat > targets.yaml <<EOF
# Human-owned. Agents never crawl or test beyond what is designated here.

# Where approved tickets get filed. testah is tracker-agnostic — drafts are
# plain markdown in tickets/drafts/; only the Steward's filing step touches
# this. \`kind: linear\` (via the local queue filer) is the reference impl.
tracker:
  kind: linear
  project: replace-me
  url: https://linear.app/replace-me

targets:
  $tkey:
    name: $tkey
    base_url: $turl
    ticketing: draft # draft | direct — draft requires human approval per ticket
    roles: [] # e.g. [admin, member] — a page's \`auth:\` value is the role key
    pages:
      - slug: $tslug
        path: $tpath
        auth: none
EOF
    sed -i.bak "s|process.env.TESTAH_BASE_URL ?? '[^']*'|process.env.TESTAH_BASE_URL ?? '$turl'|" playwright.config.ts \
      && rm -f playwright.config.ts.bak
    note "targets.yaml written; playwright baseURL -> $turl"
    if [ -d node_modules ] && ask "  Run the smoke test against $turl now?" y; then
      pnpm exec playwright test --grep @smoke \
        || note "smoke failed — edit tests/specs/smoke.spec.ts to assert something true about YOUR site, then re-run."
    fi
  else
    note "missing key or URL — skipped; edit targets.yaml by hand."
  fi
else
  note "skipped — designate pages in targets.yaml whenever you're ready."
fi

# --------------------------------------------------------------- 4) tracker
say "4/5 — Ticket tracker (Linear supported; skipping is fine — the local"
note "queue in tickets/drafts/ works with no tracker at all)"
if ask "  Connect Linear now?" n; then
  note "Create a personal API key: Linear -> Settings -> Security & access -> API keys"
  read -r -s -p "  Paste LINEAR_API_KEY (input hidden): " lkey; echo
  if [ -n "$lkey" ]; then
    v=$(curl -s -m 10 -H "Authorization: $lkey" -H "Content-Type: application/json" \
      -d '{"query":"{ viewer { name } }"}' https://api.linear.app/graphql)
    if printf '%s' "$v" | grep -q '"viewer"'; then
      touch .env && chmod 600 .env
      grep -q '^LINEAR_API_KEY=' .env && { sed -i.bak '/^LINEAR_API_KEY=/d' .env; rm -f .env.bak; }
      printf 'LINEAR_API_KEY=%s\n' "$lkey" >> .env
      note "key verified against api.linear.app and saved to .env (gitignored)."
      read -r -p "  Linear team/project name for tickets [testah]: " lproj; lproj=${lproj:-testah}
      sed -i.bak "s|project: replace-me|project: $lproj|" targets.yaml && rm -f targets.yaml.bak
    else
      note "key did NOT validate — nothing saved. Re-run setup to retry."
    fi
  fi
else
  note "skipped. Drain the queue later with: uv run python -m scripts.file_tickets"
fi
note "MCP tools: your first Claude Code session in this repo will offer the"
note "chrome-devtools and linear MCP servers from .mcp.json — approve them"
note "(the Linear MCP opens a browser OAuth where you pick your workspace)."

# ------------------------------------------------------------------ 5) menu
say "5/5 — You're set. The loop, in order:"
cat <<'MENU'
  In a Claude Code session opened in this repo (slash commands are LLM
  skills — instructions the session follows, not API calls):

    /scout <target>    map the designated pages: crawl, judge, drift-check,
                       flag defects and test-worthy features
    /author <target>   write acceptance criteria (you approve them), then
                       POMs + specs, checked by an independent reviewer agent
    /triage <run-id>   classify test failures: product-bug | behavior-change
                       | script-issue | flake; refresh the coverage maps
    /steward           validate Scout flags, draft tickets, critique the
                       loop, keep the docs honest
    /loop-status       read-only "where are we?" report from the artifacts

  No LLM needed (the suite is plain Playwright):

    pnpm exec playwright test                 run the whole suite
    pnpm exec playwright test --grep @smoke   just the smoke checks
    uv run pytest -q                          framework unit tests
    uv run python -m scripts.coverage_map     regenerate coverage maps
    uv run python -m scripts.file_tickets     file approved ticket drafts

  Full procedure and human gates: docs/running-the-loop.md
MENU
