#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required to provision GitHub triage labels" >&2
  exit 1
fi

gh label create needs-triage --color D4C5F9 \
  --description "Maintainer needs to evaluate this issue" --force
gh label create needs-info --color FBCA04 \
  --description "Waiting on reporter for more information" --force
gh label create ready-for-agent --color 0E8A16 \
  --description "Fully specified and ready for an agent" --force
gh label create ready-for-human --color 5319E7 \
  --description "Requires human implementation" --force
gh label create wontfix --color FFFFFF \
  --description "Will not be actioned" --force
