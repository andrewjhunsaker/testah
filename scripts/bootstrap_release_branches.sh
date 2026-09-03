#!/usr/bin/env bash
set -euo pipefail

source_ref="${1:-HEAD}"

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "no origin remote; release branches not created" >&2
  exit 0
fi
git rev-parse --verify "${source_ref}^{commit}" >/dev/null

for release_branch in master staging; do
  if git ls-remote --exit-code --heads origin "refs/heads/${release_branch}" \
    >/dev/null 2>&1; then
    continue
  fi
  if ! git show-ref --verify --quiet "refs/heads/${release_branch}"; then
    git branch "$release_branch" "$source_ref"
  fi
  git push origin "refs/heads/${release_branch}:refs/heads/${release_branch}"
done
