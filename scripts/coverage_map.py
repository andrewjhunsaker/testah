"""Generate docs/coverage-map.md — a living, visual map of test coverage.

Usage: uv run python -m scripts.coverage_map   (from the repo root)
Reads targets.yaml, requirements/, tests/specs/, tickets/drafts/, and (when
present) reports/last-run.json + flake-history.json, then emits a mermaid
object-graph plus a status table. Deterministic — no judgment here; the
Author (Mode B) regenerates it after every triage pass and commits it, so
the map in git always reflects the last run. GitHub renders the mermaid
natively.
"""

import json
import re
import sys
from pathlib import Path

import yaml

from scripts.flake_tracker import extract_outcomes, over_threshold

STATUS_ORDER = {"fail": 0, "flaky": 1, "pass": 2, "unknown": 3}
CLASS_FOR = {
    "fail": "fail",
    "flaky": "flaky",
    "pass": "pass",
    "unknown": "unknown",
    "criteria-only": "nospec",
    "draft": "draft",
}
BADGE = {
    "fail": "✗ failing",
    "flaky": "≈ flaky",
    "pass": "✓ passing",
    "unknown": "? not run",
    "criteria-only": "criteria only",
    "draft": "draft",
}


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


def spec_links(specs_dir: Path) -> dict:
    """spec filename -> implements path (or None for scaffolding specs)."""
    links = {}
    for spec in sorted(specs_dir.glob("*.spec.ts")):
        m = re.search(r"//\s*implements:\s*(\S+)", spec.read_text(encoding="utf-8"))
        links[spec.name] = m.group(1) if m else None
    return links


def run_outcomes(report: dict) -> dict:
    """spec filename -> worst status across its tests: fail > flaky > pass."""
    per_file: dict = {}
    for o in extract_outcomes(report):
        fname = o["id"].split(" > ")[0]
        status = {
            "unexpected": "fail",
            "flaky": "flaky",
            "expected": "pass",
            "skipped": "pass",
        }.get(o["status"], "unknown")
        current = per_file.get(fname, "unknown")
        if STATUS_ORDER[status] < STATUS_ORDER[current]:
            per_file[fname] = status
        else:
            per_file.setdefault(fname, status)
    return per_file


def build_model(root: Path) -> dict:
    targets = yaml.safe_load((root / "targets.yaml").read_text(encoding="utf-8"))[
        "targets"
    ]
    links = spec_links(root / "tests" / "specs")
    report_path = root / "reports" / "last-run.json"
    report = (
        json.loads(report_path.read_text(encoding="utf-8"))
        if report_path.exists()
        else {}
    )
    outcomes = run_outcomes(report) if report else {}
    history_path = root / "flake-history.json"
    over = (
        set(over_threshold(json.loads(history_path.read_text(encoding="utf-8"))))
        if history_path.exists()
        else set()
    )

    model = {"targets": {}, "scaffolding": []}
    spec_by_criteria = {v: k for k, v in links.items() if v}
    for fname, implements in links.items():
        if implements is None:
            model["scaffolding"].append(
                {"spec": fname, "status": outcomes.get(fname, "unknown")}
            )

    for tkey, tconf in targets.items():
        pages = {}
        for page in tconf.get("pages", []):
            pages[page["slug"]] = {"path": page["path"], "features": {}}
        model["targets"][tkey] = {"pages": pages}

        for crit in sorted((root / "requirements" / tkey).glob("*/*.md")):
            slug, feature = crit.parent.name, crit.stem
            meta = parse_frontmatter(crit.read_text(encoding="utf-8"))
            rel = f"requirements/{tkey}/{slug}/{feature}.md"
            spec = spec_by_criteria.get(rel)
            status = outcomes.get(spec, "unknown") if spec else "criteria-only"
            pages.setdefault(slug, {"path": f"({slug})", "features": {}})
            pages[slug]["features"][feature] = {
                "stage": "spec" if spec else "criteria",
                "approved": meta.get("approved", "unset"),
                "spec": spec,
                "status": status,
                "flaky_over_threshold": any(
                    tid.startswith(spec + " > ") for tid in over
                )
                if spec
                else False,
            }

        for draft in sorted((root / "tickets" / "drafts").glob("*.md")):
            meta = parse_frontmatter(draft.read_text(encoding="utf-8"))
            if meta.get("type") != "test-feature" or meta.get("target") != tkey:
                continue
            if "implemented" in meta:
                continue  # consumed by the Author; the criteria/spec node covers it
            slug = meta.get("source", "").rstrip("/").split("/")[-1]
            feature = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", draft.stem)
            pages.setdefault(slug, {"path": f"({slug})", "features": {}})
            pages[slug]["features"].setdefault(
                feature,
                {
                    "stage": "draft",
                    "approved": meta.get("status", "draft"),
                    "spec": None,
                    "status": "draft",
                    "flaky_over_threshold": False,
                },
            )
    return model


def _mid(*parts: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", "_".join(parts))


def render(model: dict) -> str:
    lines = [
        "flowchart LR",
        "  classDef pass fill:#e6f4ea,stroke:#137333,color:#137333",
        "  classDef fail fill:#fce8e6,stroke:#c5221f,color:#c5221f",
        "  classDef flaky fill:#fef7e0,stroke:#b06000,color:#b06000",
        "  classDef unknown fill:#f1f3f4,stroke:#5f6368,color:#5f6368",
        "  classDef nospec fill:#e8f0fe,stroke:#1a73e8,color:#174ea6",
        "  classDef draft fill:#f1f3f4,stroke:#5f6368,color:#5f6368,stroke-dasharray:4 3",
    ]
    rows = []
    for tkey, tval in model["targets"].items():
        lines.append(f'  subgraph {_mid("t", tkey)}["{tkey}"]')
        for slug, pval in tval["pages"].items():
            lines.append(f'    subgraph {_mid("p", tkey, slug)}["{pval["path"]}"]')
            if not pval["features"]:
                nid = _mid("f", tkey, slug, "unmapped")
                lines.append(f'      {nid}["(no features yet)"]:::unknown')
            for feature, f in sorted(pval["features"].items()):
                nid = _mid("f", tkey, slug, feature)
                badge = BADGE[f["status"]]
                if f["flaky_over_threshold"]:
                    badge += " ⚠ flake threshold"
                lines.append(f'      {nid}["{feature}<br/>{badge}"]:::{CLASS_FOR[f["status"]]}')
                rows.append(
                    f"| {tkey} | {pval['path']} | {feature} | {f['stage']} "
                    f"| {f['approved']} | {BADGE[f['status']]} "
                    f"| {'⚠ yes' if f['flaky_over_threshold'] else '—'} |"
                )
            lines.append("    end")
        lines.append("  end")

    table = [
        "| target | page | feature | stage | approved | last run | flake ≥ threshold |",
        "|---|---|---|---|---|---|---|",
        *rows,
    ]
    scaffolding = [
        f"- `{s['spec']}` — {BADGE[s['status']]}" for s in model["scaffolding"]
    ]
    return "\n".join(
        [
            "# Coverage map",
            "",
            "> Generated by `uv run python -m scripts.coverage_map` — do not hand-edit.",
            "> Colors: green = passing · red = failing · amber = flaky · blue = criteria without spec · dashed = ticket draft only.",
            "",
            "```mermaid",
            *lines,
            "```",
            "",
            "## Status detail",
            "",
            *table,
            "",
            "## Scaffolding specs (no criteria by design)",
            "",
            *(scaffolding or ["- none"]),
            "",
        ]
    )


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out = root / "docs" / "coverage-map.md"
    out.write_text(render(build_model(root)), encoding="utf-8")
    print(f"wrote {out}")
