"""Generate the per-target coverage maps under docs/coverage/.

Usage: uv run python -m scripts.coverage_map   (from the repo root)

For every target in targets.yaml this writes two files:

  docs/coverage/<target>.html — the primary visual. Self-contained (inline CSS
    and JS, zero external requests), one section per page, a card per feature,
    the individual tests that implement it, and a pan/zoom surface.
  docs/coverage/<target>.md  — a plain GitHub-readable companion table.

Reads targets.yaml, requirements/, tests/specs/, tickets/drafts/, and (when
present) reports/last-run.json + flake-history.json. Deterministic — no
judgment here; the Author (Mode B) regenerates the maps after every triage
pass and commits them, so what is in git always reflects the last run.
"""

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.flake_tracker import extract_outcomes, over_threshold

STATUS_ORDER = {"fail": 0, "flaky": 1, "pass": 2, "unknown": 3}
PW_STATUS = {
    "unexpected": "fail",
    "flaky": "flaky",
    "expected": "pass",
    "skipped": "pass",
}
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
# Plain-language wording for humans — no "stage"/"approved" jargon.
PILL = {
    "fail": "failing",
    "flaky": "flaky",
    "pass": "passing",
    "unknown": "not run",
    "criteria-only": "no tests yet",
    "draft": "draft only",
}
LAST_RUN_CELL = {
    "fail": "✗ failing",
    "flaky": "≈ flaky",
    "pass": "✓ passing",
    "unknown": "not run",
    "criteria-only": "not run",
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
        status = PW_STATUS.get(o["status"], "unknown")
        current = per_file.get(fname, "unknown")
        if STATUS_ORDER[status] < STATUS_ORDER[current]:
            per_file[fname] = status
        else:
            per_file.setdefault(fname, status)
    return per_file


def tests_by_spec(report: dict) -> dict:
    """spec filename -> [{title, status, id}] for every test in the report.

    `title` is the human-readable path inside the file (describe blocks joined
    with ' › ', project name dropped); `id` is the flake-tracker id
    ('<file>.spec.ts > <titles…> > <project>') so flake history can be matched.
    """
    per_file: dict = {}

    def walk(suite: dict, path: list[str]) -> None:
        for spec in suite.get("specs", []):
            for t in spec.get("tests", []):
                titles = path[1:] + [spec["title"]]
                parts = [path[0]] + titles
                if t.get("projectName"):
                    parts.append(t["projectName"])
                per_file.setdefault(path[0], []).append(
                    {
                        "title": " › ".join(titles),
                        "status": PW_STATUS.get(t.get("status"), "unknown"),
                        "id": " > ".join(parts),
                    }
                )
        for child in suite.get("suites", []):
            walk(child, path + [child["title"]])

    for suite in report.get("suites", []):
        walk(suite, [suite["title"]])
    return per_file


def feature_notes(feature: dict) -> list[str]:
    """Plain-language notes for one feature card (empty when there is nothing
    to say). Drafts, pending approvals and flake-threshold crossings are the
    only things a human has to act on."""
    notes = []
    if feature["status"] == "draft":
        notes.append("ticket draft only — no criteria or tests yet")
    elif feature.get("requirements") and feature.get("approved") != "true":
        notes.append(
            "criteria awaiting your approval — see Judgment calls in "
            f"{feature['requirements']}"
        )
    if feature.get("flaky_over_threshold"):
        notes.append("⚠ over flake threshold")
    return notes


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
    per_test = tests_by_spec(report) if report else {}
    history_path = root / "flake-history.json"
    history = (
        json.loads(history_path.read_text(encoding="utf-8"))
        if history_path.exists()
        else {}
    )
    over = set(over_threshold(history)) if history else set()

    model = {
        "targets": {},
        "scaffolding": [],
        "meta": {
            "generated_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
            "run_started": _run_started(report),
            "run_id": _last_run_id(history),
            "stats": report.get("stats", {}),
        },
    }
    spec_by_criteria = {v: k for k, v in links.items() if v}
    for fname, implements in links.items():
        if implements is None:
            model["scaffolding"].append(
                {
                    "spec": fname,
                    "status": outcomes.get(fname, "unknown"),
                    "tests": per_test.get(fname, []),
                }
            )

    for tkey, tconf in targets.items():
        pages = {}
        for page in tconf.get("pages", []):
            pages[page["slug"]] = {"path": page["path"], "features": {}}
        model["targets"][tkey] = {
            "name": tconf.get("name", tkey),
            "base_url": tconf.get("base_url", ""),
            "pages": pages,
        }

        for crit in sorted((root / "requirements" / tkey).glob("*/*.md")):
            slug, feature = crit.parent.name, crit.stem
            meta = parse_frontmatter(crit.read_text(encoding="utf-8"))
            rel = f"requirements/{tkey}/{slug}/{feature}.md"
            spec = spec_by_criteria.get(rel)
            status = outcomes.get(spec, "unknown") if spec else "criteria-only"
            tests = per_test.get(spec, []) if spec else []
            pages.setdefault(slug, {"path": f"({slug})", "features": {}})
            pages[slug]["features"][feature] = {
                "approved": meta.get("approved", "unset"),
                "requirements": rel,
                "spec": spec,
                "status": status,
                "tests": [dict(t, flaky_over_threshold=t["id"] in over) for t in tests],
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
                    "approved": meta.get("status", "draft"),
                    "requirements": None,
                    "draft": f"tickets/drafts/{draft.name}",
                    "spec": None,
                    "status": "draft",
                    "tests": [],
                    "flaky_over_threshold": False,
                },
            )

    for tval in model["targets"].values():
        for pval in tval["pages"].values():
            for f in pval["features"].values():
                f["notes"] = feature_notes(f)
    return model


def _run_started(report: dict) -> str:
    raw = report.get("stats", {}).get("startTime")
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return raw


def _last_run_id(history: dict) -> str:
    for runs in history.values():
        if runs:
            return runs[-1]["run"]
    return ""


# --------------------------------------------------------------------------
# markdown companion
# --------------------------------------------------------------------------


def render_md(model: dict, tkey: str) -> str:
    tval = model["targets"][tkey]
    meta = model["meta"]
    rows = []
    for pval in tval["pages"].values():
        if not pval["features"]:
            rows.append(f"| `{pval['path']}` | _(no features mapped yet)_ | — | — | — |")
            continue
        for feature, f in sorted(pval["features"].items()):
            if f["spec"]:
                n = len(f["tests"])
                tests = f"`{f['spec']}` ({n} test{'' if n == 1 else 's'})"
            else:
                tests = "—"
            notes = "; ".join(f["notes"]) or "—"
            rows.append(
                f"| `{pval['path']}` | {feature} | {tests} "
                f"| {LAST_RUN_CELL[f['status']]} | {notes} |"
            )

    scaffolding = [
        f"- `{s['spec']}` ({len(s['tests'])} tests) — {BADGE[s['status']]}"
        for s in model["scaffolding"]
    ]
    run_line = f"Last run: {meta['run_started'] or 'never'}"
    if meta["run_id"]:
        run_line += f" · flake history through run `{meta['run_id']}`"
    return "\n".join(
        [
            f"# Coverage map — {tval['name']}",
            "",
            f"> [`{tkey}.html`](./{tkey}.html) is the real map — **open it locally**",
            "> for the interactive (pan, zoom, per-test) view. This page is the",
            "> flat companion so GitHub can render something.",
            ">",
            f"> Generated by `uv run python -m scripts.coverage_map` "
            f"on {meta['generated_at']} — do not hand-edit.",
            f"> {run_line}",
            "",
            "| page | feature | tests | last run | notes |",
            "|---|---|---|---|---|",
            *rows,
            "",
            "## Scaffolding specs (no criteria by design)",
            "",
            *(scaffolding or ["- none"]),
            "",
        ]
    )


# --------------------------------------------------------------------------
# html map
# --------------------------------------------------------------------------

CSS = """
*{box-sizing:border-box}
html,body{height:100%;margin:0;overflow:hidden}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica \
Neue",Arial,sans-serif;font-size:14px;line-height:1.5;color:#1f2328;
background:#f7f7f8;display:flex;flex-direction:column}
body.dragging{user-select:none}
header{flex:0 0 auto;background:#fff;border-bottom:1px solid #e6e6e9;
padding:14px 20px 12px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
h1{margin:0;font-size:17px;font-weight:650;letter-spacing:-.01em}
.sub{margin-top:2px;color:#6b7280;font-size:12.5px}
.sub code{background:#f3f4f6;border-radius:4px;padding:1px 5px;font-size:11.5px}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:10px;font-size:12px;
color:#4b5563}
.legend span{display:inline-flex;align-items:center;gap:6px}
.key{width:10px;height:10px;border-radius:3px;background:var(--accent);
border:1px solid var(--accent)}
.key.hollow{background:transparent;border-style:dashed}
.stage{position:relative;flex:1 1 auto;overflow:hidden;cursor:grab;
touch-action:none;background-image:radial-gradient(#dcdce1 1px,transparent 1px);
background-size:22px 22px}
.stage.dragging{cursor:grabbing}
.canvas{position:absolute;top:0;left:0;transform-origin:0 0;width:1180px;
padding:4px 0 40px}
section{margin:0 0 26px}
h2{margin:0 0 4px;font-size:15px;font-weight:640;letter-spacing:-.01em}
h2 .count{font-weight:400;color:#8b8b95;font-size:12px;margin-left:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));
gap:12px;margin-top:10px;align-items:start}
.card{background:#fff;border:1px solid #e6e6e9;border-left:4px solid var(--accent);
border-radius:10px;padding:12px 14px;
box-shadow:0 1px 2px rgba(16,24,40,.04),0 1px 3px rgba(16,24,40,.06)}
.card.is-draft{border-style:dashed;background:#fcfcfd}
.top{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.name{font-weight:600;font-size:13.5px;word-break:break-word}
.pill{flex:0 0 auto;font-size:11px;font-weight:600;border-radius:999px;
padding:2px 9px;background:var(--soft);color:var(--ink);white-space:nowrap}
.note{margin-top:8px;font-size:12px;color:#7a4b00;background:#fff8e6;
border-radius:6px;padding:6px 8px;word-break:break-word}
.note.info{color:#1d4ed8;background:#eef3ff}
.note.muted{color:#6b7280;background:#f3f3f5}
.spec{margin-top:10px;font-size:11.5px;color:#6b7280;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}
.spec .suite{font-family:inherit;color:#9ca3af}
ul{list-style:none;margin:6px 0 0;padding:0}
li{display:flex;gap:7px;align-items:baseline;font-size:12.2px;color:#4b5563;
padding:1px 0}
.dot{flex:0 0 auto;width:7px;height:7px;border-radius:50%;
background:var(--accent);transform:translateY(-1px)}
.empty{margin-top:10px;font-size:12px;color:#9ca3af;font-style:italic}
.s-pass{--accent:#16a34a;--soft:#e7f6ec;--ink:#136b32}
.s-fail{--accent:#dc2626;--soft:#fdeceb;--ink:#a4181a}
.s-flaky{--accent:#d97706;--soft:#fdf3e3;--ink:#8a4d05}
.s-nospec{--accent:#2563eb;--soft:#eaf0ff;--ink:#1a49b8}
.s-draft{--accent:#b6b6bf;--soft:#f1f1f4;--ink:#6b7280}
.s-unknown{--accent:#8e8e98;--soft:#f1f1f4;--ink:#5f6368}
.toolbar{position:absolute;right:16px;bottom:16px;display:flex;align-items:center;
gap:6px;background:#fff;border:1px solid #e0e0e5;border-radius:10px;padding:5px;
box-shadow:0 2px 8px rgba(16,24,40,.10)}
.toolbar button{width:30px;height:30px;border:0;border-radius:7px;background:#f3f4f6;
color:#333;font-size:15px;line-height:1;cursor:pointer;font-family:inherit}
.toolbar button.wide{width:auto;padding:0 10px;font-size:12px}
.toolbar button:hover{background:#e7e8ec}
.zoom{min-width:42px;text-align:center;font-size:11.5px;color:#6b7280;
font-variant-numeric:tabular-nums}
.hint{position:absolute;left:16px;bottom:16px;background:rgba(31,35,40,.82);
color:#fff;font-size:11.5px;border-radius:8px;padding:6px 10px;pointer-events:none;
transition:opacity .35s}
body.engaged .hint{opacity:0}
"""

JS = """
(function(){
var stage=document.getElementById('stage');
var canvas=document.getElementById('canvas');
var zoomLabel=document.getElementById('zoom');
var s=1,tx=20,ty=16,engaged=false;
var pointers=new Map(),lastPan=null,pinchDist=0;
function apply(){
  canvas.style.transform='translate('+tx+'px,'+ty+'px) scale('+s+')';
  zoomLabel.textContent=Math.round(s*100)+'%';
}
function clamp(v){return Math.max(0.25,Math.min(3,v));}
function zoomAt(cx,cy,factor){
  var ns=clamp(s*factor),k=ns/s;
  tx=cx-(cx-tx)*k;ty=cy-(cy-ty)*k;s=ns;apply();
}
function local(e){var r=stage.getBoundingClientRect();
  return {x:e.clientX-r.left,y:e.clientY-r.top};}
function centre(){var r=stage.getBoundingClientRect();
  return {x:r.width/2,y:r.height/2};}
function engage(){if(!engaged){engaged=true;document.body.classList.add('engaged');}}
stage.addEventListener('pointerdown',function(e){
  // never capture the toolbar's own pointers — capture would retarget the
  // click and the buttons would go dead
  if(e.target.closest&&e.target.closest('.toolbar'))return;
  engage();
  try{stage.setPointerCapture(e.pointerId);}catch(err){}
  pointers.set(e.pointerId,local(e));
  if(pointers.size===1){lastPan=local(e);stage.classList.add('dragging');
    document.body.classList.add('dragging');}
  else if(pointers.size===2){var p=Array.from(pointers.values());
    pinchDist=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);lastPan=null;}
});
stage.addEventListener('pointermove',function(e){
  if(!pointers.has(e.pointerId))return;
  pointers.set(e.pointerId,local(e));
  if(pointers.size===1&&lastPan){
    var p=local(e);tx+=p.x-lastPan.x;ty+=p.y-lastPan.y;lastPan=p;apply();
  }else if(pointers.size===2){
    var q=Array.from(pointers.values());
    var d=Math.hypot(q[0].x-q[1].x,q[0].y-q[1].y);
    if(pinchDist>0&&d>0)zoomAt((q[0].x+q[1].x)/2,(q[0].y+q[1].y)/2,d/pinchDist);
    pinchDist=d;
  }
});
function release(e){
  pointers.delete(e.pointerId);
  try{stage.releasePointerCapture(e.pointerId);}catch(err){}
  if(pointers.size<2)pinchDist=0;
  if(pointers.size===1){lastPan=Array.from(pointers.values())[0];}
  if(pointers.size===0){lastPan=null;stage.classList.remove('dragging');
    document.body.classList.remove('dragging');}
}
stage.addEventListener('pointerup',release);
stage.addEventListener('pointercancel',release);
// Wheel only takes over once the map surface has actually been used (or the
// gesture is an explicit pinch-zoom) — it never steals a plain page scroll.
stage.addEventListener('wheel',function(e){
  if(!engaged&&!e.ctrlKey)return;
  e.preventDefault();
  var p=local(e);
  zoomAt(p.x,p.y,Math.exp(-e.deltaY*(e.ctrlKey?0.01:0.0018)));
},{passive:false});
document.getElementById('in').addEventListener('click',function(){
  engage();var c=centre();zoomAt(c.x,c.y,1.2);});
document.getElementById('out').addEventListener('click',function(){
  engage();var c=centre();zoomAt(c.x,c.y,1/1.2);});
document.getElementById('reset').addEventListener('click',function(){
  engage();s=1;tx=20;ty=16;apply();});
apply();
})();
"""


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _shared_suite(tests: list[dict]) -> tuple[str, list[str]]:
    """When every test sits under the same describe block, name it once and
    drop it from the individual titles (they are otherwise all prefix)."""
    titles = [t["title"] for t in tests]
    heads = {t.split(" › ")[0] for t in titles}
    if len(heads) == 1 and all(" › " in t for t in titles):
        head = heads.pop()
        return head, [t.split(" › ", 1)[1] for t in titles]
    return "", titles


def _card(feature: str, f: dict) -> str:
    cls = CLASS_FOR[f["status"]]
    parts = [
        f'<article class="card s-{cls}{" is-draft" if cls == "draft" else ""}">',
        '<div class="top"><div class="name">',
        _esc(feature),
        f'</div><div class="pill">{_esc(PILL[f["status"]])}</div></div>',
    ]
    for note in f["notes"]:
        if note.startswith("⚠"):
            style = ""
        elif f["status"] == "draft":
            style = " muted"
        else:
            style = " info"
        parts.append(f'<p class="note{style}">{_esc(note)}</p>')
    if f["spec"]:
        n = len(f["tests"])
        shared, titles = _shared_suite(f["tests"])
        suite = f' <span class="suite">· {_esc(shared)}</span>' if shared else ""
        parts.append(
            f'<p class="spec">{_esc(f["spec"])} · {n} test'
            f'{"" if n == 1 else "s"}{suite}</p>'
        )
        if f["tests"]:
            parts.append("<ul>")
            for t, title in zip(f["tests"], titles):
                warn = " ⚠" if t.get("flaky_over_threshold") else ""
                parts.append(
                    f'<li class="s-{CLASS_FOR[t["status"]]}"><span class="dot">'
                    f"</span><span>{_esc(title)}{warn}</span></li>"
                )
            parts.append("</ul>")
        else:
            parts.append('<p class="empty">no results in the last run</p>')
    elif f["status"] != "draft":
        parts.append('<p class="empty">no tests written yet</p>')
    parts.append("</article>")
    return "".join(parts)


LEGEND = [
    ("s-pass", "", "passing"),
    ("s-fail", "", "failing"),
    ("s-flaky", "", "flaky"),
    ("s-nospec", "", "criteria written, no tests yet"),
    ("s-draft", " hollow", "ticket draft only"),
    ("s-unknown", "", "not run"),
]


def render_html(model: dict, tkey: str) -> str:
    tval = model["targets"][tkey]
    meta = model["meta"]
    sections = []
    for pval in tval["pages"].values():
        cards = [
            _card(name, f) for name, f in sorted(pval["features"].items())
        ] or ['<article class="card s-unknown"><div class="top"><div class="name">'
              "no features mapped yet</div></div></article>"]
        n = len(pval["features"])
        sections.append(
            f"<section><h2>{_esc(pval['path'])}"
            f'<span class="count">{n} feature{"" if n == 1 else "s"}</span></h2>'
            f'<div class="grid">{"".join(cards)}</div></section>'
        )
    if model["scaffolding"]:
        cards = [
            _card(s["spec"], dict(s, spec=s["spec"], notes=[], tests=s["tests"]))
            for s in model["scaffolding"]
        ]
        sections.append(
            '<section><h2>scaffolding specs<span class="count">no criteria by '
            f'design</span></h2><div class="grid">{"".join(cards)}</div></section>'
        )

    stats = meta["stats"]
    counted = (
        f"{stats.get('expected', 0) + stats.get('unexpected', 0) + stats.get('flaky', 0)}"
        " tests"
        if stats
        else "no run on disk"
    )
    sub = [f"{_esc(tval['base_url'])} · generated {_esc(meta['generated_at'])}"]
    sub.append(
        f"last run {_esc(meta['run_started'])} · {counted}"
        if meta["run_started"]
        else "no run on disk"
    )
    if meta["run_id"]:
        sub.append(f"flake history through <code>{_esc(meta['run_id'])}</code>")
    legend = "".join(
        f'<span class="{cls}"><i class="key{extra}"></i>{_esc(label)}</span>'
        for cls, extra, label in LEGEND
    )
    return "".join(
        [
            "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n",
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n',
            f"<title>Coverage map — {_esc(tval['name'])}</title>\n<style>",
            CSS,
            "</style>\n</head>\n<body>\n<header>\n",
            f"<h1>Coverage map — {_esc(tval['name'])}</h1>\n",
            f'<div class="sub">{" · ".join(sub)}</div>\n',
            f'<div class="legend">{legend}</div>\n</header>\n',
            '<div class="stage" id="stage">\n<div class="canvas" id="canvas">\n',
            "\n".join(sections),
            '\n</div>\n<div class="hint">drag to pan · click the map, then scroll '
            "to zoom · pinch on touch</div>\n",
            '<div class="toolbar">',
            '<button id="out" type="button" title="zoom out">−</button>',
            '<span class="zoom" id="zoom">100%</span>',
            '<button id="in" type="button" title="zoom in">+</button>',
            '<button id="reset" type="button" class="wide" title="reset view">'
            "reset</button>",
            "</div>\n</div>\n<script>",
            JS,
            "</script>\n</body>\n</html>\n",
        ]
    )


def main(root: Path) -> list[Path]:
    model = build_model(root)
    out_dir = root / "docs" / "coverage"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for tkey in model["targets"]:
        html_path = out_dir / f"{tkey}.html"
        md_path = out_dir / f"{tkey}.md"
        html_path.write_text(render_html(model, tkey), encoding="utf-8")
        md_path.write_text(render_md(model, tkey), encoding="utf-8")
        written += [html_path, md_path]
    return written


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    for path in main(root):
        print(f"wrote {path}")
