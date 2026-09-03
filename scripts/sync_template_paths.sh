#!/usr/bin/env bash
set -euo pipefail

source_ref="${1:-origin/master}"

framework_paths=(
  ".gitignore"
  "agents"
  "scripts"
  ".github"
  ".claude"
  "CLAUDE.md"
  "setup.sh"
  ".mcp.json"
  "package.json"
  "pnpm-lock.yaml"
  "pyproject.toml"
  "uv.lock"
  "RULES.md"
  "README.md"
  "docs/spec.md"
  "docs/running-the-loop.md"
  "dashboard/__init__.py"
  "dashboard/__main__.py"
  "dashboard/server.py"
  "dashboard/snapshot.py"
  "dashboard/ui/app.ts"
  "dashboard/ui/index.html"
  "dashboard/ui/styles.css"
  "dashboard/e2e/current-snapshot.spec.ts"
  "dashboard.playwright.config.ts"
  "tsconfig.dashboard.json"
  "tests/pages/CurrentSnapshotPage.ts"
  "requirements/dashboard/current-snapshot/overview.md"
  "page-maps/dashboard/current-snapshot/page.json"
)

for path in "${framework_paths[@]}"; do
  git rm -r --ignore-unmatch --quiet -- "$path"
  if git cat-file -e "${source_ref}:${path}"; then
    git checkout "$source_ref" -- "$path"
  fi
done
