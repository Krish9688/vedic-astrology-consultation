#!/usr/bin/env python3
"""Structured Report Model (JSON) → checked HTML → PDF.

usage: python3 render_report.py report.json [--out DIR] [--check-only] [--facts calc.json] [--fact-ids derived.json]
                                [--outlook outlook.json]
       python3 render_report.py --outlook-draft outlook.json      (checked skeleton of a personal outlook)
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
import chart_svg  # noqa: E402
import lk_remedies  # noqa: E402  (REP-X7 remedy cards)
from life_lint import BUDGET, FACT, lint, report_text  # noqa: E402

TYPE_NAMES = {"complete-life": "Complete life report", "career": "Career report", "relationship": "Relationship report",
              "marriage": "Marriage report", "dasha": "Dasha report", "12-month": "Twelve-month forecast",
              "relocation": "Relocation and foreign travel report", "compact": "Consultation summary",
              "outlook": "Personal outlook"}
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


LK_NAME = re.compile(r"\b(?:LK\w*|Shrimali|Lal[- ]?Kitab)\b", re.I)   # names and aliases of the Lal Kitab family
LK_BOOKS = {"LKS", "KB", "VT"}          # source-index.md: Shrimali's Lal Kitab, the knowledge base, the Varshaphal table; LK1952 below


def separation(u, section_id):
    """Errors that keep Parashari/Jaimini and Lal Kitab claims apart (the schema validator has no conditionals)."""
    errs, system = [], u.get("system")
    if system == "lal_kitab" and not u.get("edition"):
        errs.append("is a Lal Kitab unit with no edition (shrimali, lk1952 or both)")
    if system == "lal_kitab" and not section_id.startswith("lk-"):
        errs.append("is a Lal Kitab unit outside an 'lk-' section (REPORT-STANDARD §7)")
    if u.get("rule_refs") and not system:
        errs.append("has rule_refs but no system")
    if u.get("claim_basis") == "TEXT" and u.get("claim_type") != "rule":
        errs.append("has claim_basis TEXT but is not a rule (an interpretation or prediction is COMMENTARY)")
    if system == "combined" and "compar" not in section_id:
        errs.append("is a combined unit outside the closing comparison section (its id must contain 'compar')")
    for x in u.get("rule_refs", []):
        x = x.strip()
        book = (re.match(r"[A-Z][A-Za-z0-9]*", x) or [""])[0]
        lk = book in LK_BOOKS or book.startswith("LK") or bool(LK_NAME.search(x))   # id first token, or a name anywhere, page or not
        if not lk and not re.match(r"[A-Z][A-Za-z0-9]*\s+\S", x):
            continue                     # CR-, rule: and node ids are not book citations
        if system in ("parashari", "jaimini") and lk:
            errs.append(f"is a {system} unit but cites the Lal Kitab book '{x}'")
        if system == "lal_kitab" and not lk:
            errs.append(f"is a Lal Kitab unit but cites the Parashari text '{x}'")
        ed = u.get("edition")
        if system == "lal_kitab" and lk and ed in ("shrimali", "lk1952"):
            fam = "lk1952" if re.search(r"1952|\bLK(?!S\b)\w*", x) and book != "KB" else "shrimali" if re.search(r"\b(?:LKS|KB|Shrimali)\b", x) else None
            if fam and fam != ed:
                errs.append(f"is a {ed} unit but cites the {fam} reference '{x}'")
    return errs


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
            errs += [f"{name} {e}" for e in separation(u, s["id"])]
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
    errs += [i for i in res["issues"] if i.startswith(("SAFETY", "CERTAINTY"))]
    # safety covers every string in the model — appendix, timeline labels, watch list, practical summary too
    rest = lint("\n".join(_strings(r)), "report")   # every string, incl. unit basis and section titles (council 5 R7-1)
    errs += [i for i in rest["issues"] if i.startswith(("SAFETY", "CERTAINTY")) and i not in errs]
    warns += [f"life-first: {i}" for i in res["issues"] if not i.startswith(("SAFETY", "CERTAINTY"))]
    errs += lk_remedies.card_checks(r)
    if hits := lk_remedies.never_hits(_strings({k: v for k, v in r.items() if k != "remedies"})):   # cards report their own
        errs.append(f"client text matches never-recommend items ({', '.join(hits[:4])}; remedy-safety.md §2)")
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
    out = [(f"{x['label']} {x['start']}..{x['end']}", _ym(x["start"], True), _ym(x["end"], False),
            f"{x['label']} {x.get('basis', '')}") for x in r.get("timeline", [])]
    sm = r["summary"]
    texts = [(sm.get("headline", ""), sm.get("headline", ""))]
    for k in sm["key_points"]:               # a key point's window is grounded by the planets its own text names
        texts += [(k.get("window", ""), f"{k.get('text', '')} {k.get('window', '')}"), (k.get("text", ""), f"{k.get('text', '')} {k.get('window', '')}")]
    for sec in r["sections"]:               # prose windows are grounded by the unit (or section text) that holds them
        texts += [(t, t) for t in [report_text({"sections": [dict(sec, units=[u])]}) for u in sec.get("units", [])]
                  + [report_text({"sections": [dict(sec, units=[])]})]]
    for t, ctx in texts:
        found = list(WIN.finditer(t))
        for m in found:
            a, b = re.split(SEP, re.sub(r"\bmid-?", "", m.group(), flags=re.I), maxsplit=1, flags=re.I)
            yb = int(re.search(r"20\d\d", b).group())
            ya = re.search(r"20\d\d", a)
            ya = int(ya.group()) if ya else yb
            s, e = _half(a, ya, True), _half(b, yb, False)
            if not re.search(r"20\d\d", a) and s > e:
                s = _half(a, ya - 1, True)          # "November to February 2027"
            out.append((m.group(), s, e, ctx))
        if not found and (y := re.fullmatch(r"\s*(20\d\d)\s*", t)):
            out.append((y.group(1), dt.date(int(y.group(1)), 1, 1), dt.date(int(y.group(1)), 12, 31), ctx))
    return out


def _ym(s, start):
    y, m = int(s[:4]), int(s[5:7])
    return dt.date(y, m, 1) if start else dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)


PLANETS = "Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu"
PERIOD = re.compile(rf"({PLANETS})(?:\s*[–-]\s*({PLANETS})| major period)\b")


def grounding(r, facts):
    """Every window must lie near a dasha/AD boundary, ingress or exact contact of a planet its own text names (calc.json)."""
    first = _d(facts["meta"]["transit_date"])
    last = max([_d(x["date"]) for x in facts.get("ingresses", []) + facts.get("slow_contacts", [])], default=first)
    if facts["meta"].get("months"):         # calc.json does not store `months`; its last event bounds the horizon otherwise
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
    for label, s, e, ctx in _windows(r):
        if (label, s, e, ctx) in seen:
            continue
        seen.add((label, s, e, ctx))
        named = {n[:2] for n in re.findall(PLANETS, ctx)}      # engine lord codes: Su, Mo, Ma, Me ...
        if not named:
            errs.append(f"window '{label}' cites no dasha period or planet to ground it")
            continue
        anchors = [_d(x[k]) for md in facts["vimshottari"] for x in [md] + md.get("sub", []) if x["lord"] in named
                   for k in ("start", "end")]
        anchors += [_d(x["date"]) for x in facts.get("ingresses", []) + facts.get("slow_contacts", [])
                    if {x.get("planet"), x.get("transit"), x.get("natal")} & named]
        if (e - s).days > 365.25 * BROAD_YEARS:
            warns.append(f"broad window '{label}' (over {BROAD_YEARS} years): grounding is weak")
        if any(s - tol <= a <= e + tol for a in anchors):
            continue
        if e > last or s < first and e < first:
            warns.append(f"window '{label}' is beyond the facts' range: unverified")
        else:
            errs.append(f"window '{label}' matches no dasha boundary, ingress or exact contact of the planets it names")
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


# ---- periodic outlook (P7-2): chart-anchored, texture last, nothing event-level when the window has no trigger ----
OUTLOOK_DAYS = (28, 92)      # monthly to quarterly; daily and sun-sign feeds are refused (PRED-X10)
OUTLOOK_WORDS = 900          # with the cover and appendix this keeps the PDF to two pages (tests/test_outlook_report.py)
NAMES = {"Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury", "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn",
         "Ra": "Rahu", "Ke": "Ketu"}
TRANSIT = re.compile(r"\b(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|transit\w*|retrograde|station\w*)\b", re.I)
ANCHOR = re.compile(r"\b(?:\d{1,2}(?:st|nd|rd|th)\b|natal|birth star|your (?:moon|lagna|ascendant)|lagna|ascendant"
                    r"|(?:maha|antar|pratyantar)?dasha|Vimshottari|Yogini)", re.I)
NO_EVENT = re.compile(r"no event-level timing", re.I)


def _nth(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def outlook_checks(r, o=None):
    """Errors for an outlook report: window, factor anchors, generic transit sentences, length; with the get_outlook
    output `o`, unknown factor ids and event-level claims in a window that has no event-level factor."""
    if r.get("report_type") != "outlook":
        return [], []
    errs, units = [], [u for s in r["sections"] for u in s.get("units", [])]
    p = r.get("period") or {}
    if not p:
        errs.append("an outlook report needs period.from and period.to")
    elif not OUTLOOK_DAYS[0] <= (_d(p["to"]) - _d(p["from"])).days <= OUTLOOK_DAYS[1]:
        errs.append(f"outlook window must be {OUTLOOK_DAYS[0]}-{OUTLOOK_DAYS[1]} days (monthly to quarterly)")
    errs += [f"'{u['theme'][:50]}' names no outlook factor (factor_refs)" for u in units if not u.get("factor_refs")]
    text = report_text(r)
    for line in text.splitlines():
        for sent in re.split(r"(?<=[.!?;])\s+", line):
            if TRANSIT.search(sent) and not ANCHOR.search(sent):
                errs.append(f"generic transit sentence (no chart anchor): '{sent[:70]}'")
    if len(text.split()) > OUTLOOK_WORDS:
        errs.append(f"outlook client text is {len(text.split())} words; the limit is {OUTLOOK_WORDS} (two pages)")
    if o is not None:
        by_id = {f["id"]: f for f in o["factors"]}
        errs += [f"factor_ref {x} is not in the outlook" for u in units for x in u.get("factor_refs", []) if x not in by_id]
        if not any(f.get("layer") == "event" for f in o["factors"]):
            if not NO_EVENT.search(text):
                errs.append("no event-level factor falls in this window: say plainly that no event-level timing is indicated")
            for u in units:
                c = u.get("confidence") or {}
                if u.get("claim_type") == "prediction" or c.get("event") in ("Strong", "Moderate") \
                        or c.get("timing") in ("Strong", "Moderate"):
                    errs.append(f"'{u['theme'][:50]}' makes an event-level claim in a texture-only window")
    return errs, []


def outlook_draft(o, prepared_for="(name)", prepared_on=None):
    """A checked skeleton from get_outlook output: dasha first, then event-level factors (or the texture-only
    statement), texture last. Facts only; the consultant writes the meaning, in life terms, around them."""
    fs = o["factors"]
    unit = lambda theme, meaning, refs, **kw: dict(theme=theme, meaning=meaning, factor_refs=refs, claim_type="fact",
                                                   claim_basis="COMPUTED", system="parashari", **kw)
    ds = [f for f in fs if f["kind"] == "dasha"]
    name = lambda f: f"{'Vimshottari' if 'Vimshottari' in f['fact'] else 'Yogini'} " + "-".join(NAMES.get(x, x) for x in f["lords"])
    dasha = [unit("Running dasha periods", "; ".join(f"{name(f)}, {f['when']}" for f in ds) + ".", [f["id"] for f in ds])] if ds else []
    def ev(f):
        k, n = f["kind"], NAMES.get(f.get("planet") or f.get("transit"), "")
        if k == "ingress":
            return f"{n} moves into a new sign, the {_nth(f['house_from_moon'])} from your Moon and the " \
                   f"{_nth(f['house_from_lagna'])} from your lagna"
        if k == "station_natal":
            return f"{n} turns {f['stations'][0]['station']} within {f['orb']} degrees of your natal {NAMES.get(f['natal'], f['natal'])}"
        if k == "contact":
            return f"{n} makes an exact {f['aspect']} to your natal {NAMES.get(f['natal'], f['natal'])}"
        return f"Saturn and your natal Moon: {f['fact']}"
    events = [unit(ev(f), f"Dated {f['when']}; a trigger only inside the running dasha.", [f["id"]],
                   confidence={"event": "Weak", "timing": "Weak"}) for f in fs if f.get("layer") == "event"]
    if not events:
        events = [unit("No event-level timing", "No exact contact with a natal point, no turning point near one and no "
                       "slow sign change falls in this window, so no event-level timing is indicated; what follows is texture.",
                       [f["id"] for f in fs if f["kind"] == "dasha"][:1], confidence={"event": "Unknown"})]
    near = {(f["planet"], s["date"]) for f in fs if f["kind"] == "station_natal" for s in f["stations"]}
    groups = {}                                            # one unit per kind keeps a quarter inside two pages
    for f in sorted(fs, key=lambda f: f["when"]):
        if f.get("layer") != "texture" or (f["kind"] == "station" and (f["planet"], f["when"]) in near):
            continue
        if f["kind"] == "ingress":
            line = (f"{f['when']} {NAMES[f['planet']]} into {f['fact'].split('-> ')[1].split(' (')[0]} "
                    f"({_nth(f['house_from_moon'])} from your Moon, {_nth(f['house_from_lagna'])} from your lagna)")
        elif f["kind"] == "station":
            line = f"{f['when']} {NAMES[f['planet']]} turns {f['fact'].split('turns ')[1]} ({_nth(f['house_from_moon'])} from your Moon)"
        elif f["kind"] == "chandrashtama":
            line = f["when"]
        elif f["kind"] == "tara":
            hard = [d for d, t in f["days"].items() if t in ("Vipat", "Pratyak", "Naidhana")]
            line = f"the Moon's tara is a harder one on {len(hard)} of {len(f['days'])} days"
        else:
            continue
        groups.setdefault(f["kind"], ([], []))[0].append(line)
        groups[f["kind"]][1].append(f["id"])
    heads = {"ingress": ("Sign changes", "Faster planets change sign: "),
             "station": ("Turning points", "Turning points away from your natal points: "),
             "chandrashtama": ("Low-key spells", "The Moon in the 8th sign from your natal Moon, not a time to start "
                               "something new: "),
             "tara": ("Rhythm of the days", "Counted from your birth star, ")}
    tex = [unit(heads[k][0], heads[k][1] + "; ".join(lines) + ". Low weight.", refs)
           for k, (lines, refs) in sorted(groups.items(), key=lambda kv: list(heads).index(kv[0]))]
    lead = f"{name(ds[0])} dasha" if ds else "running dasha (none in the outlook)"
    return {"report_type": "outlook", "title": "Personal outlook", "prepared_for": prepared_for,
            "prepared_on": prepared_on or o["from"], "period": {"from": o["from"], "to": o["to"]},
            "how_to_read": "Every item is a dated fact from your chart. The running dasha is the backdrop; texture is low "
                           "weight and never an event. Confidence words say how much of the chart agrees, not a probability.",
            "summary": {"headline": f"{o['from']} to {o['to']} under the {lead}.",
                        "key_points": [{"text": f"The {lead} sets the backdrop.", "confidence": "Moderate"}]},
            "sections": [{"id": "period", "title": "The period you are in", "units": dasha},
                         {"id": "events", "title": "What the window holds", "units": events},
                         {"id": "texture", "title": "Texture (low weight)", "units": tex}]}


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
    style = r.get("chart_style", "north")
    chart = chart_svg.chart((r.get("appendix") or {}).get("positions", []), style)   # P7-1; None without a lagna row
    calc = (r.get("engine") or {}).get("calculation", "")
    extra = {}
    extra["remedy_cards"], extra["remedy_sources"] = lk_remedies.cards_html(r)
    caption = f"{style.capitalize()} Indian rasi chart (signs only; degrees in the table below)" + (f"; {calc}" if calc else "")
    return env.get_template("template.html.j2").render(
        r=r, css=open(os.path.join(ASSETS, "report.css")).read(), type_name=TYPE_NAMES[r["report_type"]],
        default_how_to_read=HOW_TO_READ, tl=timeline(r.get("timeline", [])), bases=bases,
        appendix=bool(bases or r.get("appendix") or extra.get("remedy_sources")), section_titles={s["id"]: s["title"] for s in r["sections"]},
        claim_labels=CLAIM_LABELS, system_labels=SYSTEM_LABELS, basis_labels=BASIS_LABELS,
        chart=chart, chart_caption=caption, **extra)


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


def report_checks(r, schema, facts=None, fact_ids=None, outlook=None):
    """The one check sequence behind render_report.py, create_report (MCP, REST, CLI): (errors, warnings)."""
    errs = validate(r, schema)
    if errs:
        return errs, []
    e2, warns = checks(r)
    errs += e2
    extra = [citations(r)]
    if facts is not None:
        extra.append(grounding(r, facts))
    else:
        warns.append("grounding not checked: pass --facts calc.json")
    extra.append(outlook_checks(r, outlook))
    if fact_ids is not None:
        extra.append(fact_refs(r, fact_ids))
    for e3, w3 in extra:
        errs += e3
        warns += w3
    return errs, warns


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if "--outlook-draft" in sys.argv:
        return print(json.dumps(outlook_draft(json.load(open(sys.argv[sys.argv.index("--outlook-draft") + 1], encoding="utf-8"))),
                                indent=1, ensure_ascii=False))
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        return print(__doc__.strip())
    src = sys.argv[1]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.dirname(os.path.abspath(src))
    r = json.load(open(src, encoding="utf-8"))
    schema = json.load(open(os.path.join(ASSETS, "report.schema.json")))
    facts = json.load(open(sys.argv[sys.argv.index("--facts") + 1], encoding="utf-8")) if "--facts" in sys.argv else None
    o = json.load(open(sys.argv[sys.argv.index("--outlook") + 1], encoding="utf-8")) if "--outlook" in sys.argv else None
    ids = json.load(open(sys.argv[sys.argv.index("--fact-ids") + 1], encoding="utf-8")) if "--fact-ids" in sys.argv else None
    errs, warns = report_checks(r, schema, facts, ids, o)
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
        assert 'class="basis">Interpretation · Commentary · Parashari<' in page and "Prediction (interpretive)" in page, "unit labels"
        assert set(CLAIM_LABELS) == set(schema["$defs"]["unit"]["properties"]["claim_type"]["enum"])
        assert set(BASIS_LABELS) == set(schema["$defs"]["unit"]["properties"]["claim_basis"]["enum"])
        assert set(SYSTEM_LABELS) == set(schema["$defs"]["unit"]["properties"]["system"]["enum"])
    print(f"selftest ok ({len(warns)} advisory warnings on the example)")


if __name__ == "__main__":
    main()
