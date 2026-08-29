"""Drift detection for page-map artifacts.

Usage: uv run python scripts/drift.py <target> <slug> <url>
Reads page-maps/<target>/<slug>/page.md, compares against meta.json, updates
meta.json, and records new/changed pages in changed-pages.json (the Author's
mailbox). Prints the status: new | changed | unchanged.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def content_hash(markdown: str) -> str:
    normalized = "\n".join(
        line.strip() for line in markdown.splitlines() if line.strip()
    )
    return hashlib.sha256(normalized.encode()).hexdigest()


def detect(page_dir: Path, new_hash: str) -> str:
    meta_path = page_dir / "meta.json"
    if not meta_path.exists():
        return "new"
    old = json.loads(meta_path.read_text())
    return "unchanged" if old.get("content_hash") == new_hash else "changed"


def write_meta(page_dir: Path, url: str, new_hash: str, crawled_at: str) -> None:
    meta_path = page_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({"url": url, "content_hash": new_hash, "crawled_at": crawled_at})
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")


def append_changed(changed_path: Path, target: str, slug: str, status: str) -> None:
    entries = json.loads(changed_path.read_text()) if changed_path.exists() else []
    entries = [e for e in entries if not (e["target"] == target and e["slug"] == slug)]
    entries.append({"target": target, "slug": slug, "status": status})
    changed_path.write_text(json.dumps(entries, indent=2) + "\n")


if __name__ == "__main__":
    target, slug, url = sys.argv[1], sys.argv[2], sys.argv[3]
    page_dir = Path("page-maps") / target / slug
    new_hash = content_hash((page_dir / "page.md").read_text())
    status = detect(page_dir, new_hash)
    if status != "unchanged":
        append_changed(Path("changed-pages.json"), target, slug, status)
    write_meta(page_dir, url, new_hash, datetime.now(timezone.utc).isoformat())
    print(status)
