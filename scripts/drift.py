"""Drift detection for page-map artifacts.

Usage: uv run python scripts/drift.py <target> <slug> <url>
Reads page-maps/<target>/<slug>/ (page.md + page.json), compares against
meta.json, updates meta.json, and records new/changed pages in
changed-pages.json (the Author's mailbox). Prints the status:
new | changed | unchanged.
"""

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def content_hash(text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    return hashlib.sha256(normalized.encode()).hexdigest()


def page_content(page_dir: Path) -> str:
    """Hash input: page.md plus page.json (selectors/structure count as drift)."""
    md = (page_dir / "page.md").read_text(encoding="utf-8")
    json_path = page_dir / "page.json"
    structure = json_path.read_text(encoding="utf-8") if json_path.exists() else ""
    return md + "\n\x00\n" + structure


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def detect(page_dir: Path, new_hash: str) -> str:
    meta_path = page_dir / "meta.json"
    if not meta_path.exists():
        return "new"
    old = json.loads(meta_path.read_text(encoding="utf-8"))
    return "unchanged" if old.get("content_hash") == new_hash else "changed"


def write_meta(page_dir: Path, url: str, new_hash: str, crawled_at: str) -> None:
    meta_path = page_dir / "meta.json"
    meta = (
        json.loads(meta_path.read_text(encoding="utf-8"))
        if meta_path.exists()
        else {}
    )
    meta.update({"url": url, "content_hash": new_hash, "crawled_at": crawled_at})
    _write_atomic(meta_path, json.dumps(meta, indent=2) + "\n")


def append_changed(changed_path: Path, target: str, slug: str, status: str) -> None:
    entries = (
        json.loads(changed_path.read_text(encoding="utf-8"))
        if changed_path.exists()
        else []
    )
    existing = [e for e in entries if e["target"] == target and e["slug"] == slug]
    # Sticky-new: an unconsumed "new" never downgrades to "changed" — the
    # Author treats new (write a spec) and changed (repair a spec) differently.
    if existing and existing[0]["status"] == "new" and status == "changed":
        status = "new"
    entries = [e for e in entries if not (e["target"] == target and e["slug"] == slug)]
    entries.append({"target": target, "slug": slug, "status": status})
    _write_atomic(changed_path, json.dumps(entries, indent=2) + "\n")


if __name__ == "__main__":
    target, slug, url = sys.argv[1], sys.argv[2], sys.argv[3]
    page_dir = Path("page-maps") / target / slug
    new_hash = content_hash(page_content(page_dir))
    status = detect(page_dir, new_hash)
    if status != "unchanged":
        append_changed(Path("changed-pages.json"), target, slug, status)
    write_meta(page_dir, url, new_hash, datetime.now(timezone.utc).isoformat())
    print(status)
