#!/usr/bin/env python3
"""Structured Report Model (JSON) → checked HTML → PDF.

usage: python3 render_report.py report.json [--out DIR] [--check-only]
       python3 render_report.py --selftest
Validates against assets/report/report.schema.json (a stdlib subset of JSON Schema), runs consistency and
life-first checks, renders assets/report/template.html.j2 with Jinja2, and writes a PDF with WeasyPrint when it is
installed (otherwise the HTML prints to PDF from any browser). Needs: jinja2; optional: weasyprint.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets", "report")
sys.path.insert(0, HERE)
from life_lint import BUDGET, FACT, lint, report_text  # noqa: E402

TYPE_NAMES = {"complete-life": "Complete life report", "career": "Career report", "relationship": "Relationship report",
              "marriage": "Marriage report", "dasha": "Dasha report", "12-month": "Twelve-month forecast",
              "relocation": "Relocation and foreign travel report", "compact": "Consultation summary"}
HOW_TO_READ = ("Each section starts from what a theme means in your life, then how it is likely to show, when, what "
               "argues against it and what to watch for. Confidence words — Strong, Moderate, Weak, Contradictory, "
               "Unknown — describe how much of the chart agrees, not a probability. Dates are periods, never exact days. "
               "The chart details behind each conclusion are in the technical appendix.")


def validate(obj, schema, root=None, path="$"):
    """Minimal JSON Schema: $ref, type, required, enum, properties, items, minItems, maxItems."""
    root = root or schema
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return validate(obj, node, root, path)
    errs = []
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str}
    if t and not isinstance(obj, types[t]):
        return [f"{path}: expected {t}"]
    if "enum" in schema and obj not in schema["enum"]:
        errs.append(f"{path}: {obj!r} not one of {schema['enum']}")
    if isinstance(obj, dict):
        errs += [f"{path}: missing '{k}'" for k in schema.get("required", []) if k not in obj or obj[k] in ("", None)]
        for k, sub in schema.get("properties", {}).items():
            if k in obj:
                errs += validate(obj[k], sub, root, f"{path}.{k}")
    if isinstance(obj, list):
        if len(obj) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} items")
        if len(obj) > schema.get("maxItems", 10**9):
            errs.append(f"{path}: at most {schema['maxItems']} items")
        for i, x in enumerate(obj):
            errs += validate(x, schema.get("items", {}), root, f"{path}[{i}]")
    return errs


def ym(s):
    p = [int(x) for x in re.findall(r"\d+", s)] + [1, 1]
    return p[0] + (p[1] - 1) / 12 + (p[2] - 1) / 365


def timeline(rows):
    """Bar positions for the timeline chart. When long chapters would squash the interpretive rows (windows,
    pressure, watch) into slivers, the axis zooms to those rows plus a year either side; chapters are clipped and
    marked as continuing, and rows wholly outside the axis are left to the table under the chart."""
    if not rows:
        return None
    lo, hi = int(min(ym(r["start"]) for r in rows)), int(max(ym(r["end"]) for r in rows)) + 1
    focus = [r for r in rows if r["kind"] != "chapter"]
    if focus:
        flo, fhi = int(min(ym(r["start"]) for r in focus)) - 1, int(max(ym(r["end"]) for r in focus)) + 2
        if (hi - lo) > 1.5 * (fhi - flo):
            lo, hi = max(lo, flo), min(hi, fhi)
    span = hi - lo
    bars = []
    for r in rows:
        s, e = ym(r["start"]), ym(r["end"])
        if e <= lo or s >= hi:
            continue
        x = (max(s, lo) - lo) / span * 100
        w = max(1.2, (min(e, hi) - max(s, lo)) / span * 100)
        bars.append(dict(kind=r["kind"], label=r["label"], x=round(x, 2), w=round(w, 2),
                         cut=("cut-l " if s < lo else "") + ("cut-r" if e > hi else ""),
                         lx=round(x + w + 1 if x + w < 62 else max(0, x - 38), 2)))
    step = 1 if span <= 8 else 2 if span <= 16 else 5
    years = [dict(label=y, x=round((y - lo) / span * 100, 2)) for y in range(lo, hi + 1, step)]
    return dict(bars=bars, years=years)


def checks(r):
    """Consistency and life-first checks; returns (errors, warnings)."""
    errs, warns = [], []
    ids = {s["id"] for s in r["sections"]}
    for k in r["summary"]["key_points"]:
        if k.get("section") and k["section"] not in ids:
            errs.append(f"summary point refers to unknown section '{k['section']}'")
        for y in re.findall(r"\b20\d\d\b", k.get("window", "") + " " + k["text"]):
            body = json.dumps(r["sections"]) + json.dumps(r.get("timeline", []))
            if y not in body:
                errs.append(f"summary mentions {y}, which no section or timeline row supports")
    for s in r["sections"]:
        if s["id"] == "windows":      # the Main windows overview: counters and signs live in the life-area sections
            continue
        for u in s.get("units", []):
            ev = (u.get("confidence") or {}).get("event")
            if not u.get("counter") and ev not in ("Unknown", None):
                warns.append(f"[{s['id']}] '{u['theme'][:50]}' has no counter-factor")
            if not u.get("watch") and u.get("timing"):
                warns.append(f"[{s['id']}] '{u['theme'][:50]}' is timed but has nothing to watch")
        txt = report_text({"sections": [s]})
        facts = sum(1 for line in txt.splitlines() if FACT.search(line))
        if facts > BUDGET["report"]:
            warns.append(f"[{s['id']}] {facts} chart-fact lines — move detail to the appendix")
    # one timing framework per report (reports.md): a window restated in ≥4 sections belongs in "Main windows"
    seen = {}
    for s in r["sections"]:
        for w in set(re.findall(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|"
                                r"December|20\d\d)[^.;]{0,25}?(?:–|-| to )\s?(?:[A-Z][a-z]+ )?20\d\d\b",
                                report_text({"sections": [s]}))):
            seen[w] = seen.get(w, 0) + 1
    for w, n in seen.items():
        if n >= 4:
            warns.append(f"window '{w}' is restated in {n} sections — explain it once under Main windows and refer to it")
    res = lint(report_text(r), "report")
    errs += [i for i in res["issues"] if i.startswith("SAFETY")]
    warns += [f"life-first: {i}" for i in res["issues"] if not i.startswith("SAFETY")]
    cites = re.findall(r"\bp\.?\s?\d{1,4}\b|\bsl\.\s?\d+", report_text(r))
    if cites:
        warns.append(f"page/verse references in client text ({', '.join(cites[:4])}) — keep them in appendix.sources")
    return errs, warns


def render(r, out_dir, base):
    try:
        import jinja2
    except ImportError:
        sys.exit("render needs jinja2 (pip install jinja2); the JSON itself was valid")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ASSETS), autoescape=True)
    bases = [dict(theme=u["theme"], basis=u["basis"]) for s in r["sections"] for u in s.get("units", []) if u.get("basis")]
    html = env.get_template("template.html.j2").render(
        r=r, css=open(os.path.join(ASSETS, "report.css")).read(), type_name=TYPE_NAMES[r["report_type"]],
        default_how_to_read=HOW_TO_READ, tl=timeline(r.get("timeline", [])), bases=bases,
        appendix=bool(bases or r.get("appendix")), section_titles={s["id"]: s["title"] for s in r["sections"]})
    os.makedirs(out_dir, exist_ok=True)
    hp = os.path.join(out_dir, base + ".html")
    open(hp, "w", encoding="utf-8").write(html)
    try:
        from weasyprint import HTML
    except Exception:  # ImportError, or missing system libraries (pango) on this machine
        return hp, None
    pp = os.path.join(out_dir, base + ".pdf")
    HTML(string=html, base_url=ASSETS).write_pdf(pp)
    return hp, pp


def main():
    if "--selftest" in sys.argv:
        return selftest()
    src = sys.argv[1]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.dirname(os.path.abspath(src))
    r = json.load(open(src, encoding="utf-8"))
    schema = json.load(open(os.path.join(ASSETS, "report.schema.json")))
    errs = validate(r, schema)
    if not errs:
        e2, warns = checks(r)
        errs += e2
        for w in warns:
            print("warning:", w)
    if errs:
        print("\n".join("error: " + e for e in errs))
        sys.exit(1)
    if "--check-only" in sys.argv:
        return print("report model ok")
    hp, pp = render(r, out, os.path.splitext(os.path.basename(src))[0])
    print(f"html → {hp}\n" + (f"pdf  → {pp}" if pp else "pdf  → not written (WeasyPrint not available); print the HTML to PDF"))


def selftest():
    ex = json.load(open(os.path.join(ASSETS, "example-synthetic.json")))
    schema = json.load(open(os.path.join(ASSETS, "report.schema.json")))
    assert validate(ex, schema) == [], validate(ex, schema)
    errs, warns = checks(ex)
    assert errs == [], errs
    bad = json.loads(json.dumps(ex))
    bad["report_type"] = "horoscope"
    bad["summary"]["key_points"][0]["window"] = "2041"
    del bad["sections"][0]["title"]
    e = validate(bad, schema)
    assert any("report_type" in x for x in e) and any("title" in x for x in e), e
    bad = json.loads(json.dumps(ex))
    bad["summary"]["key_points"][0]["window"] = "2041"
    assert any("2041" in x for x in checks(bad)[0])
    tl = timeline(ex["timeline"])
    assert all(0 <= b["x"] <= 100 and b["x"] + b["w"] <= 101 for b in tl["bars"]), tl
    rep = json.loads(json.dumps(ex))
    rep["sections"] = [dict(rep["sections"][0], id=f"s{i}", text="The step up comes in March 2027 – June 2028.") for i in range(4)]
    assert any("restated in 4 sections" in w for w in checks(rep)[1]), checks(rep)[1]
    long = [{"kind": "chapter", "label": "c", "start": "2024-04", "end": "2049-04"},
            {"kind": "window", "label": "w", "start": "2027-02", "end": "2027-07"}]
    z = timeline(long)
    assert z["years"][0]["label"] == 2026 and z["bars"][0]["cut"] == "cut-l cut-r" and z["bars"][1]["w"] > 5, z
    print(f"selftest ok ({len(warns)} advisory warnings on the example)")


if __name__ == "__main__":
    main()
