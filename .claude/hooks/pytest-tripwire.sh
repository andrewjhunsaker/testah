#!/bin/bash
# testah regression tripwire: after any Edit/Write to scripts/*.py, run the
# (sub-second) unit suite. Exit 2 + stderr on failure so the model sees it.
# Fails open when uv is missing (template adopters without the toolchain).

f=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)
case "$f" in
  *scripts/*.py) ;;
  *) exit 0 ;;
esac
command -v uv >/dev/null 2>&1 || exit 0
cd "$(dirname "$0")/../.." || exit 0
out=$(uv run pytest -q 2>&1)
status=$?
if [ $status -ne 0 ]; then
  {
    echo "pytest tripwire FAILED after edit to $f:"
    echo "$out" | tail -25
  } >&2
  exit 2
fi
exit 0
