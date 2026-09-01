"""Normalize repository evidence for the Current Snapshot."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPORT_PATH = Path("reports/last-run.json")
SOURCE_DIRECTORIES = (Path("tests"), Path("requirements"))
SOURCE_FILES = (Path("targets.yaml"), Path("playwright.config.ts"))


def build_snapshot(root: Path, checked_at: datetime | None = None) -> dict[str, object]:
    """Return the complete normalized Current Snapshot for one repository."""
    root = root.resolve()
    targets = _read_targets(root)
    report_path = root / REPORT_PATH
    report_state, report = _read_report(report_path)
    report_is_stale = report_state == "completed" and _sources_are_newer(root, report_path)
    attributed_target = _attributed_target(report, targets) if report else None

    normalized_targets = []
    for target in targets:
        state = report_state
        target_report = report
        if state == "completed":
            if attributed_target is None:
                state = "partial"
            elif attributed_target != target["key"]:
                state = "never-run"
                target_report = None
            elif report_is_stale:
                state = "stale"
        normalized_targets.append(
            {
                **target,
                "latest_run": _latest_run(target_report, state),
            }
        )

    return {
        "checked_at": _iso_timestamp(checked_at or datetime.now(timezone.utc)),
        "repository": _repository_identity(root),
        "targets": normalized_targets,
    }


def snapshot_version(root: Path) -> str:
    """Return a cheap metadata fingerprint for repository evidence used by the snapshot."""
    root = root.resolve()
    digest = hashlib.sha256()
    for relative_path, size, modified_at in _evidence_fingerprint_entries(root):
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(modified_at).encode("ascii"))
        digest.update(b"\0")
    identity = _repository_identity(root)
    digest.update(json.dumps(identity, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def _read_targets(root: Path) -> list[dict[str, object]]:
    config_path = root / "targets.yaml"
    if not config_path.exists():
        return []
    try:
        document = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    configured = document.get("targets", {}) if isinstance(document, dict) else {}
    if not isinstance(configured, dict):
        return []
    targets = []
    for key, value in configured.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        base_url = value.get("base_url")
        targets.append(
            {
                "key": key,
                "name": value.get("name") if isinstance(value.get("name"), str) else key,
                "base_url": base_url if isinstance(base_url, str) else None,
                "environment": (
                    value.get("environment")
                    if isinstance(value.get("environment"), str)
                    else None
                ),
            }
        )
    return targets


def _read_report(path: Path) -> tuple[str, dict[str, Any] | None]:
    if not path.exists():
        return "never-run", None
    try:
        report = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (OSError, json.JSONDecodeError, ValueError):
        return "unavailable", None
    if not isinstance(report, dict) or not _has_complete_stats(report):
        return "incomplete", report if isinstance(report, dict) else None
    return "completed", report


def _has_complete_stats(report: dict[str, Any]) -> bool:
    stats = report.get("stats")
    if not isinstance(stats, dict):
        return False
    return (
        all(
            _is_count(stats.get(key))
            for key in ("expected", "unexpected", "flaky", "skipped")
        )
        and _is_duration(stats.get("duration"))
        and _parse_iso_timestamp(stats.get("startTime")) is not None
    )


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def _attributed_target(
    report: dict[str, Any] | None, targets: list[dict[str, object]]
) -> str | None:
    if not report or not targets:
        return None
    if len(targets) == 1:
        return str(targets[0]["key"])
    report_urls = {_normal_url(url) for url in _strings_in(report) if _looks_like_url(url)}
    matched = [
        target["key"]
        for target in targets
        if isinstance(target["base_url"], str)
        and _normal_url(target["base_url"]) in report_urls
    ]
    return str(matched[0]) if len(matched) == 1 else None


def _strings_in(value: object):
    if isinstance(value, dict):
        for child in value.values():
            yield from _strings_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings_in(child)
    elif isinstance(value, str):
        yield value


def _looks_like_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _normal_url(value: str) -> str:
    return value.rstrip("/")


def _latest_run(report: dict[str, Any] | None, state: str) -> dict[str, object]:
    stats = report.get("stats") if report else None
    if not isinstance(stats, dict):
        return {
            "state": state,
            "started_at": None,
            "duration_ms": None,
            "counts": None,
        }
    started_at = _parse_iso_timestamp(stats.get("startTime"))
    return {
        "state": state,
        "started_at": (
            _iso_timestamp(started_at, timespec="milliseconds") if started_at else None
        ),
        "duration_ms": (
            stats.get("duration") if _is_duration(stats.get("duration")) else None
        ),
        "counts": {
            "passed": (
                stats.get("expected") if _is_count(stats.get("expected")) else None
            ),
            "failed": (
                stats.get("unexpected")
                if _is_count(stats.get("unexpected"))
                else None
            ),
            "flaky": stats.get("flaky") if _is_count(stats.get("flaky")) else None,
            "skipped": (
                stats.get("skipped") if _is_count(stats.get("skipped")) else None
            ),
        },
    }


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_duration(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _parse_iso_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or "T" not in value:
        return None
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _sources_are_newer(root: Path, report_path: Path) -> bool:
    try:
        report_time = report_path.stat().st_mtime_ns
    except OSError:
        return False
    return any(path.stat().st_mtime_ns > report_time for path in _source_paths(root))


def _source_paths(root: Path) -> list[Path]:
    paths = [root / path for path in SOURCE_FILES if (root / path).is_file()]
    for directory in SOURCE_DIRECTORIES:
        source_root = root / directory
        if source_root.exists():
            paths.extend(path for path in source_root.rglob("*") if path.is_file())
    return paths


def _evidence_fingerprint_entries(root: Path) -> list[tuple[str, int | None, int | None]]:
    paths = [*SOURCE_FILES, REPORT_PATH]
    entries = [_fingerprint_entry(root, path) for path in paths]
    for directory in SOURCE_DIRECTORIES:
        source_root = root / directory
        if not source_root.is_dir():
            entries.append((f"{directory}/", None, None))
            continue
        entries.extend(
            _fingerprint_entry(root, path.relative_to(root))
            for path in source_root.rglob("*")
            if path.is_file()
        )
    return sorted(entries)


def _fingerprint_entry(root: Path, relative_path: Path) -> tuple[str, int | None, int | None]:
    path = root / relative_path
    try:
        status = path.stat()
    except OSError:
        return (str(relative_path), None, None)
    if not path.is_file():
        return (str(relative_path), None, None)
    return (str(relative_path), status.st_size, status.st_mtime_ns)


def _repository_identity(root: Path) -> dict[str, str | None]:
    return {
        "branch": _git(root, "branch", "--show-current"),
        "commit": _git(root, "rev-parse", "HEAD"),
    }


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def _iso_timestamp(value: datetime, *, timespec: str = "auto") -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec=timespec)
        .replace("+00:00", "Z")
    )
