"""File ticket drafts from the local queue to the configured tracker.

Usage: uv run python -m scripts.file_tickets [--all-drafts] [--dry-run]

Local-first doctrine: `tickets/drafts/` IS the ticket queue. testah works
fully offline from a tracker; this script drains the queue when one is
connected. It reads the top-level `tracker:` block of targets.yaml; for
`kind: linear` it files via Linear's public GraphQL API using LINEAR_API_KEY
(environment variable, or a `LINEAR_API_KEY=...` line in a gitignored .env
at the repo root — never committed).

By default only `status: approved` drafts are filed (the human gate).
--all-drafts also files `status: draft` and `status: scout-observed` —
use only when the human has blanket-approved the queue. Drafts whose
frontmatter has an `implemented:` key (consumed test-feature drafts) or a
`status: filed:*` stamp are always skipped. Each filed draft is stamped
`status: filed:<identifier>` in place.
"""

import json
import re
import sys
import urllib.request
from os import environ
from pathlib import Path

import yaml

API_URL = "https://api.linear.app/graphql"
FILEABLE = {"approved"}
FILEABLE_ALL = {"approved", "draft", "scout-observed"}


def load_api_key(root: Path) -> str | None:
    if environ.get("LINEAR_API_KEY"):
        return environ["LINEAR_API_KEY"]
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("LINEAR_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def parse_draft(text: str) -> dict:
    """Frontmatter meta + title (first '# ' line) + body (everything after it)."""
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip()
            body = parts[2]
    m = re.search(r"^# (.+)$", body, flags=re.MULTILINE)
    title = m.group(1).strip() if m else "(untitled draft)"
    body_after_title = body[m.end() :].strip() if m else body.strip()
    return {"meta": meta, "title": title, "body": body_after_title}


def fileable(meta: dict, all_drafts: bool) -> bool:
    status = meta.get("status", "")
    if status.startswith("filed:") or "implemented" in meta:
        return False
    return status in (FILEABLE_ALL if all_drafts else FILEABLE)


def stamp_filed(text: str, identifier: str) -> str:
    return re.sub(
        r"^status:.*$",
        f"status: filed:{identifier}",
        text,
        count=1,
        flags=re.MULTILINE,
    )


def _gql(api_key: str, query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": api_key},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = json.loads(resp.read())
    if out.get("errors"):
        raise RuntimeError(f"Linear API error: {out['errors']}")
    return out["data"]


def resolve_team_id(api_key: str, project_hint: str) -> str:
    teams = _gql(api_key, "query { teams { nodes { id name key } } }")["teams"][
        "nodes"
    ]
    if not teams:
        raise RuntimeError("no teams visible to this API key")
    hint = project_hint.lower()
    for t in teams:
        if hint in t["name"].lower() or hint == t["key"].lower():
            return t["id"]
    return teams[0]["id"]


def file_to_linear(api_key: str, team_id: str, draft: dict, source_path: str) -> str:
    description = (
        f"{draft['body']}\n\n---\n"
        f"type: `{draft['meta'].get('type', '?')}` · target: "
        f"`{draft['meta'].get('target', '?')}` · source: "
        f"`{draft['meta'].get('source', '?')}` · queue file: `{source_path}`\n"
        f"Filed by testah (scripts/file_tickets.py)."
    )
    data = _gql(
        api_key,
        """mutation($input: IssueCreateInput!) {
             issueCreate(input: $input) { success issue { identifier } } }""",
        {"input": {"teamId": team_id, "title": draft["title"], "description": description}},
    )
    result = data["issueCreate"]
    if not result["success"]:
        raise RuntimeError(f"issueCreate failed for {source_path}")
    return result["issue"]["identifier"]


def main() -> int:
    root = Path(".")
    all_drafts = "--all-drafts" in sys.argv
    dry_run = "--dry-run" in sys.argv
    tracker = yaml.safe_load((root / "targets.yaml").read_text(encoding="utf-8")).get(
        "tracker", {}
    )
    if tracker.get("kind") != "linear":
        print(f"tracker kind {tracker.get('kind')!r} not supported; queue stays local")
        return 0
    api_key = load_api_key(root)
    if not api_key:
        print(
            "no LINEAR_API_KEY (env or .env) — tracker not connected; "
            "tickets/drafts/ remains the local queue"
        )
        return 0

    queue = sorted((root / "tickets" / "drafts").glob("*.md"))
    to_file = []
    for path in queue:
        text = path.read_text(encoding="utf-8")
        draft = parse_draft(text)
        if fileable(draft["meta"], all_drafts):
            to_file.append((path, text, draft))
    if not to_file:
        print("nothing fileable in the queue")
        return 0
    if dry_run:
        for path, _, draft in to_file:
            print(f"would file: {path.name} — {draft['title']}")
        return 0

    team_id = resolve_team_id(api_key, tracker.get("project", ""))
    for path, text, draft in to_file:
        identifier = file_to_linear(api_key, team_id, draft, str(path))
        path.write_text(stamp_filed(text, identifier), encoding="utf-8")
        print(f"filed {identifier}: {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
