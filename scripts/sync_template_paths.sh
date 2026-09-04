#!/usr/bin/env bash
set -euo pipefail

source_ref="${1:-origin/master}"
manifest_path="scripts/template_paths.txt"
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/testah-template-sync.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT

new_manifest="$work_dir/new-paths.txt"
old_manifest="$work_dir/old-paths.txt"
all_paths="$work_dir/all-paths.txt"

if ! git cat-file -e "${source_ref}:${manifest_path}"; then
  echo "template manifest missing from ${source_ref}: ${manifest_path}" >&2
  exit 1
fi
git show "${source_ref}:${manifest_path}" > "$new_manifest"

if git cat-file -e "HEAD:${manifest_path}" 2>/dev/null; then
  git show "HEAD:${manifest_path}" > "$old_manifest"
else
  : > "$old_manifest"
fi

validate_manifest() {
  local manifest="$1" path object_type
  while IFS= read -r path || [ -n "$path" ]; do
    [ -z "$path" ] && continue
    case "$path" in
      \#*) continue ;;
      /*|.|..|*/../*|../*|*/..|*.git/*|.git/*|*/|*//*|-*|*[!A-Za-z0-9._/-]*)
        echo "unsafe or non-file template path: $path" >&2
        exit 1
        ;;
    esac
    if [ "$manifest" = "$new_manifest" ]; then
      object_type=$(git cat-file -t "${source_ref}:${path}" 2>/dev/null || true)
      if [ "$object_type" != "blob" ]; then
        echo "template path is missing or not a file: $path" >&2
        exit 1
      fi
    fi
  done < "$manifest"
}

validate_manifest "$new_manifest"
validate_manifest "$old_manifest"

sed '/^$/d; /^#/d' "$new_manifest" > "$work_dir/new-active.txt"
sed '/^$/d; /^#/d' "$old_manifest" > "$work_dir/old-active.txt"
LC_ALL=C sort -u "$work_dir/new-active.txt" "$work_dir/old-active.txt" > "$all_paths"

while IFS= read -r path; do
  git rm -f --ignore-unmatch --quiet -- "$path"
  if grep -Fqx "$path" "$work_dir/new-active.txt"; then
    git checkout "$source_ref" -- "$path"
  fi
done < "$all_paths"
