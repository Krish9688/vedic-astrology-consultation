#!/usr/bin/env python3
"""Structured Report Model (JSON) → checked HTML → PDF.

usage: python3 render_report.py report.json [--out DIR] [--check-only] [--facts calc.json] [--fact-ids derived.json]
       python3 render_report.py --selftest
Validates against assets/report/report.schema.json (a stdlib subset of JSON Schema), runs consistency and
life-first checks, renders assets/report/template.html.j2 with Jinja2, and writes a PDF with WeasyPrint when it is
installed (otherwise the HTML prints to PDF from any browser). Needs: jinja2; optional: weasyprint.
"""
import datetime as dt
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
               "The chart details behind each conclusion are in the technical appendix. The small label under a "
               "heading says what it rests on — a calculated fact, a cited rule or an interpretation; a source's text, "
               "an author's commentary, a disputed point or a guess — and which system produced it. 'Source text' means "
               "a book says so, not that it has been tested. A reading about your past is marked 'not confirmed' until "
               "you confirm it.")
# plain-language labels for unit.claim_type and unit.system (EVID-F11, REP-F1): computed facts, cited rules and
# judgements must stay distinguishable on the page
CLAIM_LABELS = {"fact": "Calculated fact", "rule": "Traditional rule (cited)", "interpretation": "Interpretation",
                "prediction": "Prediction (interpretive)", "speculation": "Speculative"}
BASIS_LABELS = {"TEXT": "Source text", "COMMENTARY": "Commentary", "DISPUTED": "Disputed between sources",
                "COMPUTED": "Calculated", "TESTED": "Tested", "SPECULATIVE": "Speculative"}
TEXT_KEYS = ("theme", "meaning", "manifestation", "timing", "nuance", "counter", "watch")   # what the client reads
PROVEN = re.compile(r"\b(?:tested|proven|proved|proof|validated|statistically|scientifically|confirmed by (?:data|research|stud(?:y|ies)))\b", re.I)
SYSTEM_LABELS = {"parashari": "Parashari", "jaimini": "Jaimini", "lal_kitab": "Lal Kitab",
                 "combined": "Combined (each system separately)"}


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
    if "pattern" in schema and isinstance(obj, str) and not re.search(schema["pattern"], obj):
        errs.append(f"{path}: {obj!r} does not match {schema['pattern']}")
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


MON = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
MOD = r"(?:the (?:end|start|beginning) of |early |mid-?|late )?"
SEP = r"\s?(?:–|-|—| to | until | through )\s?"
WIN = re.compile(rf"\b{MOD}{MON}\.?(?: 20\d\d)?{SEP}{MOD}{MON}\.? 20\d\d\b"      # late January to June 2027
                 rf"|\b{MOD}(?:{MON}\.? )?20\d\d{SEP}{MOD}(?:{MON}\.? )?20\d\d\b", re.I)  # 2027 – mid-2028


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
            name, basis = f"[{s['id']}] '{u['theme'][:50]}'", u.get("claim_basis")
            if basis == "TESTED" and not u.get("test_result"):
                errs.append(f"{name} is TESTED but has no test_result (prediction-log results only)")
            if u.get("claim_type") == "fact" and basis not in (None, "COMPUTED"):
                errs.append(f"{name} is a calculated fact but its claim_basis is {basis}")
            if basis in ("TEXT", "COMMENTARY") and (m := PROVEN.search(" ".join(str(u.get(k, "")) for k in TEXT_KEYS))):   # qc.md: a book is not a test
                errs.append(f"{name} rests on {basis} but is phrased as tested or proven ('{m.group()}')")
            if u.get("temporal_mode") == "past" and not u.get("history_status"):
                warns.append(f"{name} is about the past but has no history_status: it is shown as not confirmed")
            if not u.get("watch") and u.get("timing"):
                warns.append(f"[{s['id']}] '{u['theme'][:50]}' is timed but has nothing to watch")
        txt = report_text({"sections": [s]})
        facts = sum(1 for line in txt.splitlines() if FACT.search(line))
        if facts > BUDGET["report"]:
            warns.append(f"[{s['id']}] {facts} chart-fact lines — move detail to the appendix")
    # one timing framework per report (reports.md): a window's dates appear in at most three places
    places = [k.get("text", "") + " " + k.get("window", "") for k in r["summary"]["key_points"]]
    places += [report_text({"sections": [s]}) for s in r["sections"] if s["id"] != "windows"]
    places += r.get("practical_summary", []) + [w.get("when", "") + " " + w.get("meaning", "") for w in r.get("watch_list", [])]
    def key(text):   # "late January to June 2027" and "January–June 2027" are the same window
        ms = [m.lower()[:3] for m in re.findall(MON, text, re.I)]
        ys = re.findall(r"20\d\d", text)
        return (ms[0] if len(ms) == 2 else "", ys[0], ms[-1] if ms else "", ys[-1])
    seen, label = {}, {}
    for p in places:
        for m in {key(m.group()): m.group() for m in WIN.finditer(p)}.items():
            seen[m[0]] = seen.get(m[0], 0) + 1
            label.setdefault(m[0], m[1])
    seen = {label[k]: n for k, n in seen.items()}
    for w, n in seen.items():
        if n > 3:
            warns.append(f"window '{w}' is restated in {n} places — give its dates under Main windows, then name it in words "
                        "and refer to it by name")
    codes = sorted({m.group() for m in re.finditer(r"\b(?:W\d{1,2}|P\d)\b", report_text(r))})   # H9 etc. are houses
    if codes:   # round 10: coded windows in client text cost every report comparison
        errs.append(f"window codes in client text ({', '.join(codes)}) — use plain names and dates")
    res = lint(report_text(r), "report")
    errs += [i for i in res["issues"] if i.startswith("SAFETY")]
    # safety covers every string in the model — appendix, timeline labels, watch list, practical summary too
    rest = lint("\n".join(_strings(r)), "report")   # every string, incl. unit basis and section titles (council 5 R7-1)
    errs += [i for i in rest["issues"] if i.startswith("SAFETY") and i not in errs]
    warns += [f"life-first: {i}" for i in res["issues"] if not i.startswith("SAFETY")]
    cites = re.findall(r"\bp\.?\s?\d{1,4}\b|\bsl\.\s?\d+", report_text(r))
    if cites:
        warns.append(f"page/verse references in client text ({', '.join(cites[:4])}) — keep them in appendix.sources")
    return errs, warns


# ---- grounding, citations, fact_refs (P3-3): invented dates and citations are caught before a report goes out ----
# A window is grounded when a dasha boundary, ingress or exact contact lies within the window widened by this many days
# each side: report windows are periods (months), the facts are exact days, and a window rounded to whole months
# should not fail for sitting a few weeks off its trigger.
TOLERANCE_DAYS = 45
BROAD_YEARS = 5          # longer windows match almost any anchor, so they are flagged rather than trusted
FACT_REF = re.compile(r"^F\.[A-Za-z0-9_]+(\.[A-Za-z0-9_\-]+)*$")
MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def _d(s):
    return dt.date.fromisoformat(s[:10])


def _half(text, year, start):
    m, y = re.search(MON, text, re.I), re.search(r"20\d\d", text)
    y = int(y.group()) if y else year
    mo = MONTHS[m.group().lower()[:3]] if m else (1 if start else 12)
    if start:
        return dt.date(y, mo, 1)
    return dt.date(y + (mo == 12), mo % 12 + 1, 1) - dt.timedelta(days=1)


def _windows(r):
    """(label, start, end) for every timeline row and every date window in client text and summary windows."""
    out = [(f"{x['label']} {x['start']}..{x['end']}", _ym(x["start"], True),
            _ym(x["end"], False)) for x in r.get("timeline", [])]
    texts = [k.get("window", "") for k in r["summary"]["key_points"]] + [report_text(r)]
    for t in texts:
        found = list(WIN.finditer(t))
        for m in found:
            a, b = re.split(SEP, re.sub(r"\bmid-?", "", m.group(), flags=re.I), maxsplit=1, flags=re.I)
            yb = int(re.search(r"20\d\d", b).group())
            ya = re.search(r"20\d\d", a)
            ya = int(ya.group()) if ya else yb
            s, e = _half(a, ya, True), _half(b, yb, False)
            if not re.search(r"20\d\d", a) and s > e:
                s = _half(a, ya - 1, True)          # "November to February 2027"
            out.append((m.group(), s, e))
        if not found and t is not texts[-1] and (y := re.fullmatch(r"\s*(20\d\d)\s*", t)):
            out.append((y.group(1), dt.date(int(y.group(1)), 1, 1), dt.date(int(y.group(1)), 12, 31)))
    return out


def _ym(s, start):
    y, m = int(s[:4]), int(s[5:7])
    return dt.date(y, m, 1) if start else dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)


PLANETS = "Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu"
PERIOD = re.compile(rf"({PLANETS})(?:\s*[–-]\s*({PLANETS})| major period)\b")


def grounding(r, facts):
    """Every window must lie near a dasha/AD boundary, ingress or exact contact of the engine facts (calc.json)."""
    dasha = [_d(x[k]) for md in facts["vimshottari"] for x in [md] + md.get("sub", []) for k in ("start", "end")]
    other = [_d(x["date"]) for x in facts.get("ingresses", []) + facts.get("slow_contacts", [])]
    first = _d(facts["meta"]["transit_date"])
    last = max(other, default=first)             # calc.json does not store `months`; its last event bounds the horizon
    if facts["meta"].get("months"):
        last = max(last, first + dt.timedelta(days=30.44 * facts["meta"]["months"]))
    tol = dt.timedelta(days=TOLERANCE_DAYS)
    errs, warns, seen = [], [], set()
    periods = {(md["lord"],): md for md in facts["vimshottari"]}
    periods |= {(md["lord"], ad["lord"]): ad for md in facts["vimshottari"] for ad in md.get("sub", [])}
    for x in r.get("timeline", []):           # a row that names its dasha period must match that period's own dates
        m = PERIOD.match(x.get("basis", ""))
        p = m and periods.get((m[1][:2], m[2][:2]) if m[2] else (m[1][:2],))     # engine lords: Su, Mo, Ma, Me ...
        if p and not (abs(_ym(x["start"], True) - _d(p["start"])) <= tol
                      and abs(_ym(x["end"], False) - _d(p["end"])) <= tol):
            errs.append(f"row '{x['label']}' {x['start']}..{x['end']} does not match its {m.group()} "
                        f"({str(p['start'])[:10]} → {str(p['end'])[:10]})")
    for label, s, e in _windows(r):
        if (label, s, e) in seen:
            continue
        seen.add((label, s, e))
        if (e - s).days > 365.25 * BROAD_YEARS:
            warns.append(f"broad window '{label}' (over {BROAD_YEARS} years): grounding is weak")
        if any(s - tol <= a <= e + tol for a in dasha + other):
            continue
        if e > last or s < first and e < first:
            warns.append(f"window '{label}' is beyond the facts' range: unverified")
        else:
            errs.append(f"window '{label}' matches no dasha boundary, ingress or exact contact in the facts")
    return errs, warns


BOOK_REST = re.compile(r"(?:(?:ch\.?\s*)?(?:\d+|[IVXLC]+)(?:\.\d+)?(?:\s*sl\.?\s*\d+)?|p\.?\s*\d+(?:\s*[–-]\s*\d+)?)(?:[,;]?\s+|$)")
_CATALOG = os.path.join(HERE, "..", "..", "..", "knowledge", "catalog.json")


def _catalog():
    try:
        from paths import knowledge_file
        for p in (knowledge_file("ASTRO_CATALOG", "catalog.json"), _CATALOG):
            if os.path.exists(p):
                return {b["id"]: b for b in json.load(open(p, encoding="utf-8"))["books"]}
    except (ImportError, OSError, ValueError, KeyError):
        pass
    return None


def _graph():
    try:
        import kg
        return kg.load()[0]
    except (ImportError, SystemExit, OSError, ValueError, KeyError):
        return None


def citations(r, catalog=None, graph=None):
    """Resolve every unit's rule_refs. catalog: {book id: {pages}}; graph: container of node ids (None = look them up)."""
    refs = [(u, x) for s in r["sections"] for u in s.get("units", []) for x in u.get("rule_refs", [])]
    errs, warns = [], []
    for s in r["sections"]:
        for u in s.get("units", []):
            if u.get("claim_type") == "rule" and not u.get("rule_refs"):
                errs.append(f"[{s['id']}] rule claim '{u['theme'][:50]}' has no rule_refs")
    if not refs:
        return errs, warns
    register = open(os.path.join(HERE, "..", "references", "contradiction-register.md"), encoding="utf-8").read()
    cr = set(re.findall(r"^\|\s*(CR-[A-Z]+\d+)\s*\|", register, re.M))
    graph = _graph() if graph is None else graph
    catalog = _catalog() if catalog is None else catalog
    no_graph = no_cat = False
    for _, x in refs:
        x = x.strip()
        if re.fullmatch(r"CR-[A-Z]+\d+", x):
            if x not in cr:
                errs.append(f"unresolvable citation '{x}': not in the contradiction register")
        elif re.match(r"(?:rule|contradiction):|K[B]-", x):   # [B]: keeps the literal id prefix out of the shared scan
            if graph is None:
                no_graph = True
            elif x not in graph:
                errs.append(f"unresolvable citation '{x}': not in the knowledge graph")
        else:
            m = re.match(r"([A-Z][A-Za-z0-9]*)\s+(.+)$", x)
            rest, pos = (m.group(2), 0) if m else ("", 0)
            while m and pos < len(rest) and (t := BOOK_REST.match(rest, pos)):
                pos = t.end()
            if not m or pos != len(rest):
                errs.append(f"unresolvable citation '{x}'")
            elif catalog is None:
                no_cat = True
            elif m.group(1) not in catalog:
                errs.append(f"unresolvable citation '{x}': '{m.group(1)}' is not a catalog book")
            else:
                pages = catalog[m.group(1)].get("pages")
                for p in re.findall(r"\bp\.?\s*(\d+)", rest):
                    if pages and int(p) > pages:
                        errs.append(f"unresolvable citation '{x}': page {p} is beyond the book's {pages} pages")
    if no_graph:
        warns.append("citations unverified: no knowledge graph")
    if no_cat:
        warns.append("book citations unverified: no catalog")
    return errs, warns


def fact_refs(r, fact_ids):
    """Every unit fact_ref must be a key of derived_facts/1 `facts` (chart_facts.py --json)."""
    known = (fact_ids or {}).get("facts", {})
    return [f"[{s['id']}] fact_ref '{x}' is not in the derived facts" for s in r["sections"]
            for u in s.get("units", []) for x in u.get("fact_refs", []) if x not in known], []


def _strings(x):
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        return [s for v in x.values() for s in _strings(v)]
    if isinstance(x, list):
        return [s for v in x for s in _strings(v)]
    return []


def html_of(r):
    try:
        import jinja2
    except ImportError:
        raise RuntimeError("render needs jinja2 (pip install jinja2); the JSON itself was valid")   # not sys.exit: callers are servers (council R3 M4)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ASSETS), autoescape=True)
    bases = [dict(theme=u["theme"], basis=u["basis"]) for s in r["sections"] for u in s.get("units", []) if u.get("basis")]
    return env.get_template("template.html.j2").render(
        r=r, css=open(os.path.join(ASSETS, "report.css")).read(), type_name=TYPE_NAMES[r["report_type"]],
        default_how_to_read=HOW_TO_READ, tl=timeline(r.get("timeline", [])), bases=bases,
        appendix=bool(bases or r.get("appendix")), section_titles={s["id"]: s["title"] for s in r["sections"]},
        claim_labels=CLAIM_LABELS, system_labels=SYSTEM_LABELS, basis_labels=BASIS_LABELS)


def render(r, out_dir, base):
    html = html_of(r)
    os.makedirs(out_dir, exist_ok=True)
    hp = os.path.join(out_dir, base + ".html")
    with _owner_only(hp) as f:          # reports hold birth details: 0600 from the first byte, also on errors
        f.write(html.encode("utf-8"))
    try:
        from weasyprint import HTML
    except Exception:  # ImportError, or missing system libraries (pango) on this machine
        return hp, None
    pp = os.path.join(out_dir, base + ".pdf")
    doc = HTML(string=html, base_url=ASSETS).render()
    with _owner_only(pp) as f:
        doc.write_pdf(f)
    return hp, pp


def _owner_only(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)                 # an existing file keeps its old mode otherwise
    return os.fdopen(fd, "wb")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        return print(__doc__.strip())
    src = sys.argv[1]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.dirname(os.path.abspath(src))
    r = json.load(open(src, encoding="utf-8"))
    schema = json.load(open(os.path.join(ASSETS, "report.schema.json")))
    errs = validate(r, schema)
    if not errs:
        e2, warns = checks(r)
        errs += e2
        extra = [citations(r)]
        if "--facts" in sys.argv:
            extra.append(grounding(r, json.load(open(sys.argv[sys.argv.index("--facts") + 1], encoding="utf-8"))))
        else:
            warns.append("grounding not checked: pass --facts calc.json")
        if "--fact-ids" in sys.argv:
            extra.append(fact_refs(r, json.load(open(sys.argv[sys.argv.index("--fact-ids") + 1], encoding="utf-8"))))
        for e3, w3 in extra:
            errs += e3
            warns += w3
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
    assert any("restated in" in e for e in checks(rep)[1]) and not any("restated in" in e for e in checks(rep)[0])
    rep["sections"] = rep["sections"][:3]
    assert not any("restated in" in e for e in checks(rep)[1]), checks(rep)[1]
    long = [{"kind": "chapter", "label": "c", "start": "2024-04", "end": "2049-04"},
            {"kind": "window", "label": "w", "start": "2027-02", "end": "2027-07"}]
    z = timeline(long)
    assert z["years"][0]["label"] == 2026 and z["bars"][0]["cut"] == "cut-l cut-r" and z["bars"][1]["w"] > 5, z
    coded = json.loads(json.dumps(ex)); coded["summary"]["key_points"][0]["text"] += " See W2."
    assert any("window codes" in e for e in checks(coded)[0]) and not any("window codes" in e for e in checks(ex)[0])
    leak = dict(ex, appendix=dict(ex.get("appendix") or {}, sources=["fewer children (PD XII.3)"]))
    assert any(e.startswith("SAFETY") for e in checks(leak)[0]), "appendix safety"
    try:
        import jinja2  # noqa: F401
    except ImportError:
        pass                                   # labels are checked where jinja2 is installed (CI installs it)
    else:
        page = html_of(ex)
        assert 'class="basis">Interpretation · Source text · Parashari<' in page and "Prediction (interpretive)" in page, "unit labels"
        assert set(CLAIM_LABELS) == set(schema["$defs"]["unit"]["properties"]["claim_type"]["enum"])
        assert set(BASIS_LABELS) == set(schema["$defs"]["unit"]["properties"]["claim_basis"]["enum"])
        assert set(SYSTEM_LABELS) == set(schema["$defs"]["unit"]["properties"]["system"]["enum"])
    print(f"selftest ok ({len(warns)} advisory warnings on the example)")


if __name__ == "__main__":
    main()
