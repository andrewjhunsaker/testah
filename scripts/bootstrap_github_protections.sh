#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required to provision GitHub branch protection" >&2
  exit 1
fi

gh api --method PUT "repos/{owner}/{repo}/branches/staging/protection" \
  --input - >/dev/null <<'JSON'
{"required_status_checks":{"strict":true,"contexts":["scripts-unit","e2e","dashboard","codex-review"]},"enforce_admins":true,"required_pull_request_reviews":{"dismiss_stale_reviews":false,"require_code_owner_reviews":false,"required_approving_review_count":0,"require_last_push_approval":false},"restrictions":null,"required_linear_history":true,"allow_force_pushes":false,"allow_deletions":false,"required_conversation_resolution":true}
JSON

gh api --method PUT "repos/{owner}/{repo}/branches/master/protection" \
  --input - >/dev/null <<'JSON'
{"required_status_checks":null,"enforce_admins":true,"required_pull_request_reviews":{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1,"require_last_push_approval":true},"restrictions":null,"required_linear_history":true,"allow_force_pushes":false,"allow_deletions":false,"required_conversation_resolution":true}
JSON

gh api --method PUT "repos/{owner}/{repo}/actions/permissions/workflow" \
  --input - >/dev/null <<'JSON'
{"default_workflow_permissions":"read","can_approve_pull_request_reviews":true}
JSON
