#!/usr/bin/env bash
set -euo pipefail

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "no origin remote; staging was not created" >&2
  exit 1
fi

if ! git ls-remote --exit-code --heads origin refs/heads/master \
  >/dev/null 2>&1; then
  echo "origin needs a human-initialized master branch; staging was not created" >&2
  exit 1
fi

git fetch origin refs/heads/master:refs/remotes/origin/master

if git ls-remote --exit-code --heads origin refs/heads/staging \
  >/dev/null 2>&1; then
  exit 0
fi

git push origin refs/remotes/origin/master:refs/heads/staging
