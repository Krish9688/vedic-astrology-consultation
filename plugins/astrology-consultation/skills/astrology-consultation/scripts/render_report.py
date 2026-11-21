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
import calendar
import copy
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
import medical_words  # noqa: E402  (the one medical and death word list)
import vocab  # noqa: E402  (the project's term list: houses, vargas, dasha names and their spellings)
from life_lint import BUDGET, FACT, lint, report_text  # noqa: E402

TYPE_NAMES = {"kundli": "Kundli report", "complete-life": "Complete life report", "career": "Career report", "relationship": "Relationship report",
              "marriage": "Marriage report", "dasha": "Dasha report", "12-month": "Twelve-month forecast",
              "relocation": "Relocation and foreign travel report", "compact": "Consultation summary",
              "outlook": "Personal outlook", "wealth": "Wealth report", "education": "Education report",
              "reputation": "Reputation report", "spirituality": "Spirituality report", "self": "Self report",
              "family": "Family report", "challenges": "Challenges report", "children": "Children report",
              "intimacy": "Intimacy report", "affairs": "Affairs and fidelity report (own chart)",
              "jupiter-transit": "Jupiter transit report", "rahu-ketu": "Rahu-Ketu transit report",
              "varshaphal": "Varshaphal (annual chart) report", "sade-sati": "Sade Sati and Saturn report",
              "mangal-dosha": "Mangal Dosha report", "raj-yoga": "Raj Yoga report", "match": "Couples match report",
              "lal-kitab": "Lal Kitab report"}
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
HOW_TO_READ_NOTIME = ("Each section starts from what a theme means in your life, then how it is likely to show, what argues "
                      "against it and what to watch for. Confidence words — Strong, Moderate, Weak, Contradictory, Unknown — "
                      "describe how much of the chart agrees, not a probability. The chart details behind each conclusion are in "
                      "the technical appendix. The small label under a heading says what it rests on — a calculated fact, a cited "
                      "rule or an interpretation; a source's text, an author's commentary, a disputed point or a guess — and which "
                      "system produced it. 'Source text' means a book says so, not that it has been tested.")
TEXT_KEYS = ("theme", "meaning", "manifestation", "timing", "nuance", "counter", "watch")   # what the client reads
PROVEN = re.compile(r"\b(?:tested|proven|proved|proof|validated|statistically|scientifically|confirmed by (?:data|research|stud(?:y|ies)))\b", re.I)
SYSTEM_LABELS = {"parashari": "Parashari", "jaimini": "Jaimini", "lal_kitab": "Lal Kitab",
                 "combined": "Combined (each system separately)"}
# the question each type answers, what each chip and mark means (one legend)
ANSWERS = {
    "kundli": "What does my birth chart show about who I am, where my strengths lie and which period I am in now?",
    "compact": "What did the chart say to the questions I asked, and what should I watch next?",
    "outlook": "What is the running period asking of me in the coming weeks, and is any event actually timed?",
    "career": "What kind of work suits me, which chapter am I in, and when are the next windows for a move or step up?",
    "relationship": "How do I relate to others, and when is a relationship most likely to form or deepen?",
    "marriage": "Is marriage supported, when is the main commitment window, and what themes shape married life?",
    "dasha": "What is the running major period like in life terms, and which turning points follow?",
    "12-month": "What is the theme of the coming year, and which stretches bring opportunity or pressure?",
    "relocation": "Does the chart point to living or working far from home, in what form, and when?",
    "complete-life": "What is the core pattern of this chart, and how does it show across life areas now and ahead?",
    "wealth": "How does money come and stay in this chart, when are the stronger and the tighter stretches, and what are the sudden-gain tendencies?",
    "education": "How do I learn, which fields suit the chart, and which periods favour study?",
    "reputation": "How do others see me, what does my standing rest on, and when is recognition or a setback more likely?",
    "spirituality": "What does the chart lean to in my inner life, what practice fits, and which periods turn me inward?",
    "self": "Who am I in this chart: my core, my temperament, my broad appearance and where I grow?",
    "family": "How do I relate to my home, my mother and my father, and when are home and property matters more likely to move?",
    "challenges": "Where does the chart show pressure, how do disputes tend to show up, and how can I respond?",
    "children": "How do I relate to children, what is my parenting style, and where else does the care for the next generation show?",
    "intimacy": "How does closeness show in my chart: comfort, warmth, what steadies it and what holds it back?",
    "affairs": "What do my own tendencies toward ties outside a committed relationship look like, and what steadies them?",
    "jupiter-transit": "Where is Jupiter moving through my chart, what does each stay open up, and does my running period agree?",
    "rahu-ketu": "Where does the axis of the nodes fall in my chart, what does it stir and release, and does my running period agree?",
    "varshaphal": "What does the annual chart for this year show, season by season, and which areas does it confirm?",
    "sade-sati": "When does Saturn pass over my Moon, what does each phase press on, and how can I meet it?",
    "mangal-dosha": "Does Mars sit where four named rules count a Mangal dosha, what cancels it under each, and what does it mean in plain terms?",
    "raj-yoga": "Which kendra-kona combinations does my chart hold, where do the sources disagree about them, and when do their periods run?",
    "match": "How do two charts compare under the computed kootas and the Prasna Marga counts, what does Mars show in each, and how do the charts fit as tendencies?",
    "lal-kitab": "What does the Lal Kitab chart show house by house, which debts (rin) does it mark, and what does that system say on its own terms?",
}
SENS_LABELS = {"stable": "Birth time: stable", "may_shift": "Birth time: may shift",
               "depends": "Birth time: depends on exact time"}
LEGEND = {
    "claim": {"fact": "Computed by the engine from the birth data; no judgement involved.",
              "rule": "A traditional rule from a named source, stated as that source states it.",
              "interpretation": "The reader's judgement of what the chart relationships mean for you.",
              "prediction": "An interpretive statement about what may happen and when; never a certainty.",
              "speculation": "A guess the chart permits but does not support; weigh it lightly."},
    "grade": {"Strong": "most of the chart's relevant factors agree.",
              "Moderate": "the factors lean one way but some do not agree.",
              "Weak": "little supports it; kept because the question was asked.",
              "Contradictory": "the chart argues both ways; both sides are shown.",
              "Unknown": "the chart or the data cannot settle it."},
    "sens": {"stable": "unchanged across the plausible birth-time range; the bar has crisp ends.",
             "may_shift": "a date edge or detail moves within that range; the bar has dotted ends.",
             "depends": "changes with the exact birth time; the bar fades out at both ends."},
    "line": {"chapter": "Calculated period (a dasha or other supplied span).",
             "window": "Interpretive window (a judgement, not a calculation).",
             "pressure": "Pressure period (cost, delay or strain).",
             "watch": "Something to watch."},
}
TEMPLATE_GLOBALS = dict(sens_labels=SENS_LABELS, legend=LEGEND)


def sens_state(x):
    """Birth-time sensitivity of a unit, window or key point: an explicit `sensitivity` wins; the consultation model's
    boolean time_sensitive means 'depends'. None = nothing to show (no state given)."""
    s = x.get("sensitivity")
    return s if s in SENS_LABELS else ("depends" if x.get("time_sensitive") else None)


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
        bars.append(dict(kind=r["kind"], label=r["label"], x=round(x, 2), w=round(w, 2), sens=sens_state(r),
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


# ---- T10 spec reports (references/report-specs/<id>.md): the owner's frame and QC checklist, automated ----------------
# batch 6 (T11.36): the Lal Kitab report's sections (owner decision 11)
LK_SECTIONS = ["lk-chart", "lk-houses", "lk-rin"]
# Body section ids per type and depth, in order. A section may be left out only with a `dropped` entry and its reason.
SPEC_SECTIONS = {
    "kundli": {"standard": ["foundation", "windows", "self", "strengths", "current"],
               "full": ["foundation", "windows", "self", "career", "relationship", "partner", "intimacy", "wealth",
                        "family", "friends", "education", "home", "travel", "inner", "challenges", "remedies"]},
    "relationship": {"standard": ["windows", "relate", "partner"]},
    "career": {"standard": ["windows", "pattern", "chapter", "next", "money", "choices"]},
    "wealth": {"standard": ["windows", "pattern", "retention", "sudden", "choices"]},
    "education": {"standard": ["windows", "learning", "fields", "next"]},
    "reputation": {"standard": ["windows", "standing", "image", "setbacks", "choices"]},
    "spirituality": {"standard": ["windows", "path", "practice", "inner"]},
    "self": {"standard": ["core", "temperament", "appearance", "growth"]},
    "family": {"standard": ["windows", "home", "mother", "father", "siblings"]},
    "challenges": {"standard": ["windows", "pressure", "disputes", "response"]},
    "children": {"standard": ["theme", "parenting", "alternatives"]},
    "intimacy": {"standard": ["comfort", "venus", "bond", "phases", "steadiers"]},
    "affairs": {"standard": ["pulls", "pressures", "private", "steadiers"]},
    "jupiter-transit": {"standard": ["windows", "moon", "lagna", "fit"]},
    "rahu-ketu": {"standard": ["windows", "axis", "contacts", "fit"]},
    "varshaphal": {"standard": ["seasons", "year", "areas"]},
    "sade-sati": {"standard": ["windows", "areas", "fit", "kantaka", "response"]},
    "mangal-dosha": {"standard": ["rules", "meaning", "steadiers"]},
    "raj-yoga": {"standard": ["windows", "lines", "strength"]},
    "match": {"standard": ["kootas", "counts", "mangal", "fit"]},
    "lal-kitab": {"standard": LK_SECTIONS},
}
# batch 4 (T11.34): the transit and annual types. Each carries one required sentence in `scope`; a window or pressure row
# must name the running dasha in its basis (a transit or the year chart alone never gives a window)
TRANSIT_TYPES = ("jupiter-transit", "rahu-ketu", "varshaphal", "sade-sati")
TRANSIT_SCOPE = {
    "jupiter-transit": "A transit alone never gives an event: it only confirms what the running period already shows.",
    "rahu-ketu": "Library support for reading the nodes' transit is thin, so these are tendencies only.",
    "varshaphal": "The year chart confirms a window the birth chart and its running periods already show; it never creates one.",
    "sade-sati": "Sade sati is a broad lens, never a verdict: it counts only where the running period agrees.",
}
KANTAKA_NOTE = ("Kantaka Shani (Saturn in the 4th, 7th or 10th from the Moon) and Ashtama Shani (Saturn in the 8th from the "
                "Moon) have no rule text in this library: CRUX p424 and p464 call Saturn in the 8th from the Moon 'Kantaka Sani' "
                "in case studies only, and the 4th, 7th and 10th convention has no book source here. Both are a modern "
                "convention, always graded Weak.")
KANTAKA = re.compile(r"\b(?:kantaka|ashtama)\b", re.I)
# Node aspects (owner decision 13): a node word and an aspect word in one clause. aspect, drishti and glance count alone; the
# looser sight words count only with a target after them (a house or sign count, a trine or angle, a planet). A clause that
# reports the dispute or attributes the view to some writers is not a claim (NODE_META).
_NODE = r"(?:rahu|ketu|nodes?|nodal)(?:['’]s)?"
_NV = r"(?:aspect\w*|drishti|glanc\w*)"
_NV_SOFT = r"(?:looks?|looking|looked|see[sn]?|seeing|saw|sights?|views?|viewing|behold\w*|gaz\w*|cast\w*|influenc\w*|throw\w*|threw|project\w*)"
_NODE_TARGET = (r"(?:\d{1,2}(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|"
                r"trines?|trikonas?|kendras?|angles?|natal|sun|moon|mars|mercury|jupiter|venus|saturn|lagna|ascendant)")
NODE_ASPECT = re.compile(rf"\b(?:{_NODE}|axis)\b[^.!?;]*\b{_NV}\b|\b{_NV}\b[^.!?;]*\b{_NODE}\b|"
                         rf"\b{_NODE}\b[^.!?;]*\b{_NV_SOFT}\b[^.!?;]*\b{_NODE_TARGET}\b|"
                         rf"\b{_NODE}\b[^.!?;]*\b{_NODE_TARGET}\b[^.!?;]*\b(?:its|their|full)\s+(?:full\s+)?(?:sight|gaze|view|look|glance)\b",
                         re.I)
NODE_META = re.compile(r"\b(?:disput\w*|debat\w*|contested|not agreed|school-?dependent|omit\w*|not (?:used|counted|read|shown|"
                       r"computed|applied|given)|no node aspects?|some (?:writers|authors|astrologers|jyotishis|sources|texts|schools|"
                       r"traditions)|others? (?:do not|don't|disagree|differ|read)|according to some|one view|another view|one side|"
                       r"either side|whether|the view that|some hold|said by some)\b", re.I)
NODE_SETTLE = re.compile(r"\b(?:settled|settles(?!\s+neither)|certainly|definitely|surely|undoubtedly|clearly|in fact|proven|proved|"
                         r"(?:correct|right|true|only) view|is (?:correct|right|true)|does aspect|do aspect|truly|without doubt)\b", re.I)
# Lal Kitab words outside the lal-kitab report (README §5): the names and editions, the LK houses and debts, the sleeping
# houses and planets, the year table. next_step.follow_ups may point at the lal-kitab report.
LK_TERMS = re.compile(r"\b(?:LK\w*|Shrimali|Lal[- ]?Kitab|pakk[ae] ghar|takra+v\w*|takrao|rin|rinas?|"
                      r"sleep\w*\s+(?:house|planet)s?|(?:house|planet)s?(?:\s+\d+)?\s+(?:is |are )?asleep|sleeps? in|soya (?:ghar|grah)|"
                      r"kayam grah|andh[ae] grah|mangal badh|(?:varshaphal|annual|year)\s+(?:lal kitab\s+)?table)\b", re.I)
# Unknown birth time: the sections each spec drops (report-specs/<t>.md, "unknown time"). When every section is dropped one
# house-free 'note' section stays, since a report needs one section.
UNKNOWN_DROP = {"jupiter-transit": ("moon", "lagna", "fit"), "rahu-ketu": ("axis", "fit"), "varshaphal": ("seasons", "year", "areas"),
                "sade-sati": ("windows", "areas", "fit", "kantaka"), "mangal-dosha": ("rules", "meaning"),
                "raj-yoga": ("windows", "lines", "strength")}
# batch 5 (T11.35): the two yoga types and the Kaal Sarp unit inside the kundli
YOGA_TYPES = ("mangal-dosha", "raj-yoga")
YOGA_SCOPE = {
    "mangal-dosha": "This reads Mars's placement under four named rules as a tendency toward drive and intensity in close ties; it says nothing about how a marriage will go.",
    "raj-yoga": "A yoga is a combination in the chart, not a promise: it shows a result only where the strength of its planets and the running period agree.",
}
KAAL_NOTE = ("Kaal Sarp is a modern combination: no classical text in this library names it, its effect is not agreed and no "
             "cancellation is known.")
KAAL = re.compile(r"\bka(?:a)?l[ -]?sarp\w*|\bkala[ -]?sarp\w*", re.I)
MANGAL_NAME = re.compile(r"\bmangal(?:ik)?\b|\bmanglik\b|\bkuja[ -]?dosha\b|\bmars dosha\b", re.I)
# the four engine rules, in this order: a pattern for the unit theme of each (chart_facts KUJA-BPHS80, POPULAR, PD11.3, HJH2)
MANGAL_RULES = (("classical", re.compile(r"\bclassical\b|\bBPHS\b", re.I)), ("popular", re.compile(r"\bpopular\b", re.I)),
                ("Phaladeepika", re.compile(r"\bPhaladeepika\b|\bPD\b", re.I)), ("HJH2", re.compile(r"\bHJH2\b|\bRaman\b", re.I)))
BASE_RATE_RX = re.compile(r"\b(?:about|roughly)\s+\w+\s+(?:random\s+)?(?:charts?\s+)?in\s+(?:10|100)\b|\bbase rate not checked\b", re.I)
CANCEL_RX = re.compile(r"cancel|exempt|no cancellation|not assessed", re.I)
# Dual lordship (CR-V22): a planet that owns an angle or trine and also a 6th, 8th or 12th. Read from the engine's lordships
# (F.<p>.owns) for the planets a unit's RAJA ids or fact ids name; without engine facts, from the lordships its text states
# ("owns the 9th and the 12th", "lord of the 8th as well as the 9th", "the 6th and 7th lord", "owns H6,7").
GOOD_HOUSES, DUSTHANAS = {1, 4, 5, 7, 9, 10}, {6, 8, 12}
_ORDW = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth")
_ORD1 = rf"(?:\d{{1,2}}(?:st|nd|rd|th)|H\d{{1,2}}(?:,\d{{1,2}})*|{'|'.join(_ORDW)})"
_ORDS = rf"{_ORD1}(?:\s*(?:,|and|&|as well as|plus)\s*(?:the\s+)?{_ORD1})*"
LORD_RX = re.compile(rf"\b(?:owns?|owning|owner of|lord(?:ship)?s? of|rules?|ruling)\s+(?:both\s+)?(?:the\s+)?({_ORDS})|"
                     rf"\b({_ORDS})(?:[- ]house)?\s+lord", re.I)
RAJA_ID = re.compile(r"\bRAJA-(?:KK|KKP|YK)-((?:[A-Z][a-z]){1,2})\b")
PLANET_CODE = {"sun": "Su", "moon": "Mo", "mars": "Ma", "mercury": "Me", "jupiter": "Ju", "venus": "Ve", "saturn": "Sa"}


def dual_lords(u, fact_ids=None):
    """Planets (codes) in a unit that own a good house and a dusthana, from the engine's lordships when given, else from
    the lordships the unit's text states."""
    text = " ".join(_strings({k: u.get(k) for k in TEXT_KEYS + ("basis", "fact_refs")}))
    owns = (fact_ids or {}).get("facts", {})
    if owns:
        named = {c for m in RAJA_ID.finditer(text) for c in re.findall(r"[A-Z][a-z]", m.group(1))}
        named |= set(re.findall(r"\bF\.([A-Z][a-z])\.", text)) | {PLANET_CODE[w.lower()] for w in re.findall(
            r"\b(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn)\b", str(u.get("theme", "")))}
        return sorted(p for p in named if set(owns.get(f"F.{p}.owns") or []) & GOOD_HOUSES and set(owns.get(f"F.{p}.owns") or []) & DUSTHANAS)
    out = []
    for m in LORD_RX.finditer(text):
        hs = {int(x) for x in re.findall(r"\d+", m.group(1) or m.group(2))} | {
            _ORDW.index(w.lower()) + 1 for w in re.findall("|".join(_ORDW), m.group(1) or m.group(2), re.I)}
        if hs & GOOD_HOUSES and hs & DUSTHANAS:
            out.append(m.group())
    return out
# batch 6 (T11.36). match: consent and neutral names (owner decision 10); four kootas with their exceptions and never a total;
# Mars per chart under the four engine rules; fit as tendencies. lal-kitab: its own frame and sections (owner decisions 2, 11)
MATCH_CONSENT = "The person who asked for this report confirmed that both people agreed to have their charts compared."
MATCH_ROLES = "The koota tables keep the tradition's roles: Person A is read in the bride's place and Person B in the groom's."
MATCH_NOSUM = "The four kootas are not added up: there is no total out of 36, and vashya, yoni, gana and varna are not computed."
KOOTAS = (("tara", re.compile(r"\btara\b", re.I)), ("bhakoot", re.compile(r"\bbhak(?:oo|u)t\b", re.I)),
          ("graha maitri", re.compile(r"\bmaitri\b", re.I)), ("nadi", re.compile(r"\bnadi\b", re.I)))
EXCEPT_RX = re.compile(r"exception|not evaluated|not assessed", re.I)
ROLE_WORDS = re.compile(r"\b(?:brides?|(?:bride)?grooms?|girls?|boys?|husbands?|wi(?:fe|ves)|kanya)\b", re.I)
PERSONS = ("Person A", "Person B")
MATCH_NAME_OK = {"person", "prasna", "marga", "kashyapa", "garga", "phaladeepika", "mantreswara", "muhurta", "chintamani", "parasara",
                 "brihat", "hora", "sastra", "narada", "vasishtha", "kuja", "manglik", "mangalik", "dosha", "koota", "kootas", "tara",
                 "bhakoot", "bhakut", "graha", "maitri", "nadi", "adi", "madhya", "antya", "vashya", "yoni", "gana", "varna",
                 "lal", "kitab"}
LK_SCOPE = "This is a Lal Kitab reading, kept apart from the Parashari reports: its houses, debts and remedies are Lal Kitab's own."
RIN_NOTE = ("A rin (debt) here is traditional family symbolism read from the birth chart only: it names no debt, blames no one "
            "and is not a curse.")
PITRI = re.compile(r"\bpit(?:r|ri|ru)\s?rin\b", re.I)
DASHA_BASIS = re.compile(r"\w*dasha\b|\b(?:periods?|sub-periods?|bhukti|MD|AD)\b", re.I)
LEDGER = {"fact": "Confirmed", "rule": "Inferred", "interpretation": "Inferred", "prediction": "Hypothesis",
          "speculation": "Hypothesis"}
PARTNER_CAVEAT = ("This is an archetype derived from the chart. It is not a description of a real person. Appearance "
                  "and age, where given, are the lowest-confidence parts and are graded Weak.")
# copied exactly from astro/service.py (the skill runs without the engine); tests/test_report_specs.py keeps them equal
UNKNOWN_TIME = re.compile(r"^\s*(unknown|not known|n/?a|none|no (birth )?time)\s*($|[;,(:.-])"
                          r"|\b(birth )?time\s+(is\s+)?(unknown|not known)\b|\bno birth time\b", re.I)
SELF_APPEARANCE_CAVEAT = ("This is the tradition's description, untested and graded Weak: family and region decide "
                          "more, and it is not a measurement.")
PERCENT = re.compile(r"\d\s?%|\bper ?cent\b|\bpercentage\b", re.I)
ORGANS = re.compile(r"\b(?:liver|kidneys?|lungs?|stomach|intestin\w*|bowels?|colon|bladder|uterus|womb|ovar\w*|testic\w*|"
                    r"prostate|thyroid|pancrea\w*|spleen|gall ?bladder|genital\w*)\b", re.I)
DAY = re.compile(rf"\b\d{{4}}-\d{{2}}-\d{{2}}\b|\b\d{{1,2}}(?:st|nd|rd|th)? {MON}\.? \d{{4}}\b|\b{MON}\.? \d{{1,2}}(?:st|nd|rd|th)?,? \d{{4}}\b", re.I)
HOUSE = re.compile(r"\b(?:\d{1,2}(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
                   r"eleventh|twelfth) (?:house|lord)\b|\bhouses?\b|\blagna\b|\bascendant\b|\bD-?(?:9|10)\b|\bnavamsa\b|"
                   r"\bdasamsa\b|\bdasha\b|\bmajor period\b|\bsub-period\b", re.I)
TIME_DEP = re.compile(r"\b(?:house|lord|lagna|ascendant|D-?\d+|navamsa|dasamsa|dasha|period)\b", re.I)
LOOKS = re.compile(r"\b(?:height|(?<!stand )(?<!stands )(?<!standing )tall|complexion|appearance(?! of)|good-looking|handsome|beautiful|physique|stature|hair|age gap|"
                   r"(?:slim|slender|stocky|athletic|sturdy|heavy|medium|lean) build)\b", re.I)
LOOKS_TOPIC = re.compile(LOOKS.pattern.replace("appearance(?! of)|", ""), re.I)   # outside units the bare topic word "appearance" is fine
# self only: further looks words, refused in every section but 'appearance' (idioms such as "short-term" are left alone)
SELF_LOOKS = re.compile(r"\b(?:short(?![- ](?:term|lived|stretch|period|time|run|list|notice))|thin|heavy(?!\s+(?:work\w*|load\w*|responsibilit\w*|dut\w*))|plump|attractive|pretty|ugly|petite|tiny|small-framed|big-boned|"
                        r"wheatish|looks(?! like)|dark(?![- ](?:times|days|phase|period|moods?|thoughts|humou?r))|"
                        r"fair(?!-minded| in\b| to\b| with\b| (?:share|chance|deal|way|view|amount|enough))|good[- ]looking|lovely|gorgeous|"
                        r"your (?:\w+ )?face(?!\s+(?:lights|up\b|shows)))\b", re.I)
# family: a dated row or line that names a parent or sibling is refused only with a harm word (neutral forecasts may be dated)
PARSIB = re.compile(r"\b(?:mothers?|fathers?|parents?|mom|mum|dad|brothers?|sisters?|siblings?|grand\w+|granny|nana|nani|dada|dadi|"
                    r"bhai\w*|didi|behen|chacha|chachi|mama|mami|bua|mausi|step(?:dad|mom|mum))\b", re.I)
DATEISH = re.compile(r"\b(?:19|20)\d{2}\b|\b(?:January|February|March|April|June|July|August|September|October|November|December|"
                     r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\b|\bMay \d")
KUNDLI_GATES = {"family": ("family", "children_kundli"), "challenges": ("challenges",), "inner": ("spirituality",), "self": ("self",),
                "intimacy": ("intimacy",), "relationship": ("affairs",)}   # full kundli section id -> gate sets
AGE = re.compile(r"\b(?:older|younger)\b", re.I)            # an age claim only in a sentence about a partner
PARTNER = re.compile(r"\b(?:partner|spouse|husband|wife)\b", re.I)
AFFAIR = re.compile(r"\b(?:affairs?|cheat\w*|unfaithful\w*|infidelit\w*|fidelity|extramarital)\b", re.I)
OWN = re.compile(r"\byour own (?:chart|tendenc\w*)\b", re.I)     # the caveat itself ("your own tendencies, never ...")
OTHER = re.compile(r"\b(?:partner|spouse|husband|wife|boyfriend|girlfriend|he|she|his|her|they|them|their)\b", re.I)


# type gates (batch 1): refused wording per report type, run on the client text of a spec report. A negated clause is
# excused (the spec caveats: "This is not investment advice"), as life_lint does for its certainty probes.
_S = r"[^.!?;]*"
_EYE = r"black|brown|dark|light|hazel|green|blue|gr[ae]y|amber|golden|honey|pale|dark brown|light brown"   # eye colour words (allowed in self 'appearance' only)
_NEG_WORDS = {"not", "cannot", "can't", "won't", "don't", "never", "no", "nor", "neither", "none", "nothing", "without"}
_NEG_VERB = re.compile(r"\b(?:never|not|no)\s+(?:be\s+)?(?:predict\w*|read|said|stated|given|made|claimed|promised|shown|implied|inferred)\b", re.I)
# emphatic idioms never excuse a match ("Without doubt you will win" is a claim, not a caveat)
_EMPH = re.compile(r"\b(?:no|without(?: a)?) (?:doubt|question|worry)\b|\bnot a worry\b|\bno cause for (?:alarm|worry)\b|\bnothing to fear\b|\bwithout fail\b", re.I)
# a legal referral ("see a lawyer") excuses its own clause; a medical referral never does (owner rule 2026-11-15)
_DEFER = re.compile(r"\b(?:ask|see|consult|speak to|talk to)\s+(?:a|your|the)\s+(?:lawyer|solicitor|attorney|"
                    r"legal professional)\b", re.I)
_CLAUSE = re.compile(r"[;:—–]|[.!?]\s+(?=[A-Z])|,\s+(?:so|but|yet|and so)\b")   # a match never spans a break
_NUMW = (r"(?:(?:twenty|thirty|forty|fifty|sixty|seventy)(?:[-\s](?:one|two|three|four|five|six|seven|eight|nine))?|"
         r"eighteen|nineteen)")
_BUY = r"(?:now|stocks?|shares|gold|property|land|tickets?|crypto\w*|futures|options)"
# slang, affectionate and Indian-language kin words that name a parent, grandparent or in-law (a relative all the same)
_SLANG = (r"old man|old lady|old folks|folks|pops|pitaji|papaji|babuji|bauji|amma|ammi|appa|abba|abbu|baba|bapu|maa|maiya|mataji|taiji|tauji|masi|"
          r"bhabhi|jija|jiju|sasur|saas|(?:dear|dearest) (?:mother|father|mom|dad)|(?:mother|father|mom|dad|mum) dear")
_PAR = (_SLANG + "|" + r"mothers?|fathers?|parents?|grand\w*|brothers?|sisters?|siblings?|relatives?|family|mom|mum|dad|maternal|paternal|"
        r"stepmother|stepfather|mother-in-law|father-in-law|aunts?|aunties?|uncles?|cousins?|nieces?|nephews?|in-laws?|family members?|"
        r"step(?:son|daughter|brother|sister|parents?|dad|mom|mum)|brother-in-law|sister-in-law|ma|pa|"
        r"granny|nana|nani|dada|dadi|bhai\w*|didi|behen|chacha|chachi|mama|mami|bua|mausi")
_PERSON = rf"(?:you|he|she|they|persons?|someone|colleagues?|friends?|partners?|spouses?|husbands?|wife|boss|mentor|neighbou?rs?|{_PAR})"
# the medical and death words, shared by _HARM (relative clauses) and _FORBID (every string) so the two lists cannot drift.
# Known limits (over-blocks the owner accepts): "operation(s)" in a work sense, "heart" in other idioms, "terminal" in a place.
_MED = (medical_words.STRONG + "|" + medical_words.REPORT_WORDS + "|"
        r"{PERSON}\s+(?:[\w'’]+\s+){0,3}?recover\w*|"
        r"{PERSON}\s+(?:[\w'’]+\s+){0,2}?pass(?:es|ed)? into (?:the )?next (?:phase|life|world|stage)").replace("{PERSON}", _PERSON)
_HARM = (_MED + r"|ill|illness\w*|sick\w*|diseas\w*|death|deaths|dies|die|dying|dead|deceased|pass\w* away|passing(?!\s+phase)|"
         r"passes(?!\s+(?:on|down|by|through))|leaves? this world|lifespans?|life spans?|longevity|"
         r"(?:long|short)(?:-| )?(?:life|lives|lived)|live (?:long|short)|health|ailment\w*|cancer|surger\w*|operation|hospital\w*|"
         r"bereave\w*|mourn\w*|griev\w*|grief|funeral|widow\w*|fatal\w*|accidents?|frail\w*|bedridden|well-?being|"
         r"bod(?:y|ily)|unwell|recover\w*|years left|bury|buried|crisis|decline[sd]?|surviv\w+|numbered|much longer|fad(?:es|ed|ing)|time on earth|old age|taken from|final (?:years|days|illness)|"
         r"last (?:days|years|breath)|nursing|care home|heart (?:may |could |will |might )?(?:weak\w*|attack|trouble|problem\w*|"
         r"condition|failure)|weak(?:en|ens|ened|ening)|misfortune|danger|harm|"
         r"leav(?:es|ing) us|injur\w*|hurt|mishap\w*|wound\w*|treatment|(?<!as a )(?<!as an )doctors?|operated on|worsen\w*|laid up|breathe\w* (?:his|her|their) last|"
         r"not wake|goodbye|in memory of|footing|unkind|blow|final chapter|last chapter|intensive care|(?:be|been|is|are|was|were|get|gets|got) gone|gone by|gone for good|coma|bedside|last rites|carers?|"
         r"end is near|downhill|faint\w*|falls? from|gives? out|pain|break(?:s|ing)? (?:her|his|their) \w+|bitten|procedure|pneumonia|tumble|disabled|forever|"
         r"final journey|clinic|stretcher|slip\w* away|use of (?:his|her|their) legs|see the year out|never come back|virus|laid low|"
         r"time (?:may |will |could |might |has )come|next world|called home|ebb\w*|stroke|tragedy|collapse\w*|drown\w*|wheelchair|fever|miscarr\w*|eyesight|blind\w*|memory loss|dement\w*|paraly\w*|come down with|turn for the worse|"
         r"pass(?:es|ed)? on(?!\s+" + medical_words.PASS_ON_OK + r"\b)|rest in peace|icu|emergency|burn(?:ed|t)|crippl\w*|confined|struck down|lose (?:his|her|their) (?:sight|memory|hearing|mind|life)|vitality|(?:her|his|their) end|[’']s condition|(?:her|his|their) condition|(?:hard|difficult|tough|rough|trying)\s+(?:stretch|years?|times?|periods?|phases?|patch|spell)|trouble\w*|suffer\w*|at risk")
# A relative may be the subject or possessor of a sentence only in one fixed forecast shape (report-specs/family.md);
# anything else is written from the person's side ("you ..."). Sentences with "you" as the subject stay free, but the
# relative + harm layer (_PAR/_HARM) still runs on every sentence.
# shortcut: closed shapes over-block anything else about a relative; widen the PHRASE list only through review.
_REL = (r"(?:" + _SLANG + r"|(?:mothers?|fathers?|parents?|dad|mom|mum|ma|pa|brothers?|sisters?|siblings?|aunts?|aunties?|uncles?|cousins?|"
        r"nieces?|nephews?|grand\w+|relatives?|in-laws?|family members?)(?:-in-law)?|step(?:mother|father|brother|sister|parents?|son|daughter|dad|mom|mum)|"
        r"granny|nana|nani|dada|dadi|bhai(?:ya)?|didi|behen|chacha|chachi|mama|mami|bua|mausi)")
_PHRASE = ("visit you|visit your home|come to stay with you|stay with you for a while|move house|move to a new city|move abroad|"
           "move closer to you|move for work|travel for work|travel with you|go on a holiday|change jobs|start a new job|be promoted|"
           "retire|plan a family gathering|host a family gathering|plan a trip|help you with the move|help you with your home|"
           "get married|study abroad|graduate|welcome a baby|have a baby|become a mother|become a father|become a parent|become parents|"
           "become grandparents|become a grandparent")    # a relative's baby: a neutral dated line is allowed (owner 2026-11-19)
_PLANET = r"(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)"
_TIME = (rf"(?:in {MON} \d{{4}}|in \d{{4}}|between \d{{4}} and \d{{4}}|from \d{{4}}|later in \d{{4}}|"
         rf"during the {_PLANET} (?:sub-)?period)")
_SHAPE = re.compile(rf"(?:your (?:[a-z]+ )?{_REL}(?: and (?:you|his wife|her husband|his partner|her partner))?|she|he|they) (?:may|might|could|would|is likely to|are likely to) "
                    rf"(?:{_PHRASE})(?: {_TIME})?\.?", re.I)
_VERBISH = r"(?!(?:or|and|nor|tie|figures?|windows?|rows?|sections?|readings?|themes?|role|pattern)\b)\w+"   # any word that is not a topic noun
_BARE = (r"(?:pops|pitaji|papaji|babuji|bauji|amma|ammi|appa|abba|abbu|baba|bapu|maa|maiya|mataji|mum|mom|mummy|mommy|mama|dad|daddy|papa|ma|pa|grandpa|grandma|granny|nana|nani|nanny|dada|dadi|"
         r"father|mother|brother|sister|aunt|auntie|uncle|stepdad|stepmom|stepmum|bhai|bhaiya|didi|behen|chacha|chachi|mami|bua|mausi)")
_AUX = r"(?:will|may|might|could|would|shall|can|should|must|is|are|was|were|has|have|had|does|did)"
_POSS = r"(?:['’]s?(?:\s+[\w-]+){1,3}?)?"
# a relative as the subject, anywhere in a piece: "your father may", "In 2029 your father may", "Mum may", "Grandpa slips"
_HEADS = re.compile(rf"\b(?:(?:your|the|a|an|his|her|their)\s+(?:[\w'’-]+\s+){{0,2}}?{_REL}{_POSS}(?:\s+{_VERBISH}|\s*,\s+{_AUX}\b)"
                    rf"|{_BARE}{_POSS}\s+{_AUX}\b|(?:she|he|they)\b|(?:her|his|their)\s+[\w-]+(?:\s+[\w-]+)?\s+{_VERBISH})", re.I)
_BAREHEAD = re.compile(rf"^{_BARE}{_POSS}\s+{_VERBISH}", re.I)       # a bare relative at the start of a piece: "Grandpa slips ..."
_PIECE = re.compile(r"\s*[;,]\s*(?:and |but )?|\s+(?:although|when|while|after|before|because|if|but)\s+", re.I)
_ALLOWWHAT = "a relative or pronoun as the subject outside the fixed forecast shapes"
_ALLOWHINT = " -- a relative may appear only in a fixed forecast shape (see family.md); otherwise write it from your side ('you ...')"
_LABEL_SPLIT = re.compile(r"\s+-\s+|:")
_BARELABEL = re.compile(rf"(?:(?:your|the|his|her|their)\s+)?(?:[\w'’-]+['’]s\s+)?(?:(?:elder|younger|older|big|little|eldest|youngest|maternal|paternal)\s+)?(?:{_REL}|{_BARE})", re.I)
_QUOTED = re.compile(r"(?<![A-Za-z])(['\"“‘„«`])([^'\"“”‘’„«»`]{1,40}?)['\"”’»`](?![A-Za-z])")
_TRIM = re.compile(r"^[\s\-–—•*·\"'“”‘’()\[\]]+|[\s\"'“”‘’()\[\]]+$")


def _has_head(x):
    return bool(_HEADS.search(x) or _BAREHEAD.match(x))


def _shape_hits(strings):
    """Shape hits for the strings as written, plus the hits found in disguised readings when the text as written names no
    relative at all: doubled letters squashed ("fatherr"), a kin word split by spaces ("fathe r"), a symbol or dot inside it
    ("f@ther", "f.ather"), and "your" glued to it ("Yourfather")."""
    out = _shape_hits_one(strings)
    for x in strings:
        if _heads_in(x):
            continue
        for y in _disguises(x):
            if y != x:
                out += _shape_hits_one([y])
    return out


_KIN_WORDS = {"father", "mother", "brother", "sister", "parent", "parents", "uncle", "aunt", "auntie", "mum", "mom", "dad", "papa", "mama",
              "mummy", "mommy", "daddy", "grandfather", "grandmother", "grandpa", "grandma", "granny", "sibling", "siblings", "cousin",
              "niece", "nephew", "stepfather", "stepmother", "stepdad", "stepmom", "stepmum", "nana", "nani", "dada", "dadi", "bhai",
              "bhaiya", "didi", "behen", "chacha", "chachi", "mami", "bua", "mausi", "pops", "pitaji", "amma", "appa", "baba", "ammi"}


def _join_split_kin(text):
    """Join a kin word split into 2 or 3 pieces by spaces ("fathe r", "mo ther"): only when the join is a kin word and no
    piece is one itself."""
    toks = re.split(r"(\s+)", text)
    words = [i for i, t in enumerate(toks) if t.strip()]
    out, i = [], 0
    while i < len(toks):
        if toks[i].strip():
            k = words.index(i)
            done = False
            for n in (3, 2):
                piece = [toks[w] for w in words[k:k + n]]
                core = [re.sub(r"[^A-Za-z]", "", t) for t in piece]
                if len(piece) == n and "".join(core).lower() in _KIN_WORDS and not any(c.lower() in _KIN_WORDS for c in core) and all(core):
                    out.append("".join(core))
                    i = words[k + n - 1] + 1
                    done = True
                    break
            if done:
                continue
        out.append(toks[i])
        i += 1
    return "".join(out)


def _disguises(x):
    """Readings of a string with the usual disguises undone, each only when it differs from the string."""
    glued = re.sub(rf"\b(your|his|her|their|the|my)(?=(?:{_REL}|{_BARE})\b)", r"\1 ", x, flags=re.I)
    dotted = re.sub(r"(?<=[A-Za-z])[.\-_*](?=[A-Za-z])", "", x)
    leet = [medical_words._leet(x, "i"), medical_words._leet(x, "l")]
    ji = _KIN_JI.sub(r"\1", x)       # "fatherji", "papaji", "mummyji": a kin word with the -ji respect suffix
    out = [_SQUASH.sub(r"\1", x), glued, dotted, _join_split_kin(x), ji, _SQUASH.sub(r"\1", ji)] + leet
    out += [_SQUASH.sub(r"\1", _join_split_kin(medical_words._leet(x, "i"))), glued_join(dotted)]
    return list(dict.fromkeys(out))


def glued_join(x):
    return re.sub(rf"\b(your|his|her|their|the|my)(?=(?:{_REL}|{_BARE})\b)", r"\1 ", x, flags=re.I)


_KIN_JI = re.compile(r"\b(father|mother|papa|mummy|mommy|mom|mum|dad|daddy|brother|sister|uncle|aunt|auntie|bhai|didi|nana|nani|dada|dadi|"
                    r"chacha|chachi|mama|mami|grandfather|grandmother|grandpa|grandma|parents?)(?:ji|jee)\b", re.I)
_SQUASH = re.compile(r"([A-Za-z])\1+")


def _heads_in(x):
    return any(_has_head(_TRIM.sub("", b)) for whole in re.split(r"(?<=[.!?])\s+", x) for b in _LABEL_SPLIT.split(whole))


def _shape_hits_one(strings):
    """(what, sentence) for each sentence or label piece in which a relative or he/she/they is the subject of a clause but the
    whole piece is not one fixed forecast shape. Text is cut at line breaks, ":" and sentence ends, and quotes, brackets and
    bullets are stripped. A piece that starts with "you" is free unless it also names he/she/they or a later clause with a
    relative subject; a relative as the object is not read here (the medical and death gate and _HARM cover it)."""
    out = []
    for text in strings:
        text = _QUOTED.sub(r"\2", text)       # "Your 'father' may": a word in quote marks is read as if it stood bare
        if medical_words.DEVA_KIN_RX.search(text):      # a relative named in Devanagari cannot be shape-checked: write it from your side
            out.append((_ALLOWWHAT, "a relative in Devanagari"))
        text = re.sub(r"(?<=\w)\s*\([^()]{0,60}\)", "", text)     # "your father (Ramesh) may": the aside is not part of the shape
        text = re.sub(rf"\b({_REL}|{_BARE})\s*,\s*[^,.;:!?]{{1,40}},", r"\1", text, flags=re.I)   # "your father, God bless him, may": a comma aside
        text = re.sub(r"\s*[—–]\s*|\s*\n\s*", " ", text)     # a line break or an inner dash is a space, not a break
        for whole in re.split(r"(?<=[.!?])\s+", text):
            bits = _LABEL_SPLIT.split(whole)
            if len(bits) > 1 and _BARELABEL.fullmatch(_TRIM.sub("", bits[0])):     # "<Relative>: ..." or "<Relative> - ...": out of shape
                joined = re.sub(r"\s+", " ", _TRIM.sub("", bits[0] + " " + " ".join(bits[1:])))        # unless the text after it completes a shape
                if not _SHAPE.fullmatch(joined):
                    out.append((_ALLOWWHAT, bits[0].strip().lower()[:40]))
                    continue
        for sent in (b for whole in re.split(r"(?<=[.!?])\s+", text) for b in _LABEL_SPLIT.split(whole)):
            sent = _TRIM.sub("", sent)
            if not sent or _SHAPE.fullmatch(sent):
                continue
            if re.match(r"you\b", sent, re.I):
                bad = re.search(r"\b(?:she|he|they)\b", sent, re.I) or any(_has_head(x) for x in _PIECE.split(sent)[1:])
            else:
                bad = _has_head(sent)
            if bad:
                out.append((_ALLOWWHAT, sent[:40].lower()))
    return out


def _no_ids(x):
    """x without the "id" keys (section ids are structure, not text)."""
    if isinstance(x, dict):
        return {k: _no_ids(v) for k, v in x.items() if k != "id"}
    return [_no_ids(v) for v in x] if isinstance(x, list) else x


# Medical and death wording, refused in every string of every spec report, whoever it is about (owner rule 2026-11-15).
# shortcut: a word and phrase list, no parser; it is the floor for "you" and object sentences. A synonym that is missing
# gets through; add it here.
FORBID_MSG = ("Health and death are not read in this practice. Such predictions can harm the reader and are not good for their "
              "health. I can help with another area of your life instead.")
_FORBID = re.compile(
    r"\b(?:" + _MED + r"|lo(?:se|ses|sing|st) (?:a |an |your |the |one of your )?" + _REL
    + r"|(?<!\byou )(?:may|might|could|will|would) (?:take|call) (?:your|his|her|their) " + _REL + r")\b|" + ORGANS.pattern, re.I)


_LEGAL = r"court(?! of public opinion)|judge|case|lawsuit|legal|justice|trial|tribunal|ruling|claim|petition|oppos\w+|bench|opponents?|rivals?|enem\w*|foes?|adversar\w*|other side|opposing party"
_OUTCOME = (r"win|wins|won|winning|lose|loses|lost|losing|favou?r\w*|your side|sides? with|resolv\w*|crush\w*|defeat\w*|beat|beats|"
            r"prevail\w*|triumph\w*|humbl\w*|victor\w*|verdict|judg(?:e)?ment|ruling|award\w*|upheld|uphold\w*|granted|allowed|dismissed|rejected|silenc\w*|in your pocket|everything you asked for|pay|pays|paid|settle\w*")
# batch 3 (T11.30, fix round 1): children, intimacy, affairs. A gate with a third item True is "hard": a negation does not
# excuse it, because a claim about the person ("You will not have children") is not a caveat. Fertility, pregnancy, potency
# and birth-health words are in medical_words.REPORT_WORDS (the one list), not here; these gates read the forms around
# them. Contractions are folded first ("you'll" -> "you will", see _fold).
_KID = (r"(?:children|child|kids?|babies|baby|sons?|daughters?|progeny|offspring|heirs?|descendants?|twins?|triplets?|"
        r"little ones?|cradle|stork)")
_KIDX = _KID[:-1] + r"|parent(?:hood|ing)|(?:mother|father)hood|lineage|family line|family name)"
_OBJ = r"(?:(?:a|an|the|any|your|no|one|two|three|four|five|more|another|some|several|many|few|own|first|second|next|new)\s+){0,2}(?:\w+\s+)?"
_NUM = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+|a couple of|a pair of|several|many|few|multiple|both)"
_MODAL = (r"(?:will|shall|may|might|could|would|can|won't|cannot|can't|(?:are|is) (?:going|likely|unlikely|bound|destined|able|sure|"
          r"not able|prone|set|about) to|(?:will|may|might|could) (?:end|wind) up)")
_MORAL = (r"\b(?:immoral\w*|promiscuous\w*|promiscuity|licentious\w*|lecherous|debauch\w*|depraved|pervert\w*|perversion\w*|sinful|"
          r"shameful|shameless|adulter\w*|harlot\w*|whor\w*|slut\w*|loose (?:morals|character|woman|man)|bad (?:person|character|morals)|"
          r"characterless|low morals|wanton\w*|vulgar|unchaste|lewd\w*|indecent\w*|degenerate\w*|dishonou?r\w*|immodest\w*|home-?wreck\w*|"
          r"cheaters?|flirt\w*|prude\w*|prudish|fallen (?:woman|man)|wicked\w*|disgrac\w*|corrupt\w*|womani[sz]\w*|easy (?:woman|man|virtue)|"
          r"temptress|seductress|scandalous|trampy|slutty|improper|dirty|teas(?:e|es|ing|er)|unseemly|filthy|sleazy|sordid|obscene|vile|trashy|"
          r"loose (?:streak|ways|living|habits|nature)|two-?timer\w*|playboy|casanova|gigolo|lothario|rogue|cad|rake|hussy|floozy|strumpet|"
          r"naughty|raunchy|sinner|sinful|philander\w*|womaniz\w*)\b")
_CERTAIN = (r"\b(?:guarantee\w*|certainly|definitely|surely|inevitabl\w*|destined|fated|doomed|bound to|sure to|without fail|for certain|"
            r"no doubt|cannot fail|absolutely|undeniabl\w*|without question|unquestionabl\w*|beyond (?:any )?doubt|undoubted\w*|indisputabl\w*|"
            r"unmistakabl\w*|for sure|no question|assured\w*|ensured|unavoidabl\w*|inescapabl\w*|unfailing\w*|no mistake|without a doubt|"
            r"sure thing|beyond question|written (?:in|for)\b|meant to be|a matter of time|sooner or later|cannot be (?:avoided|escaped|helped)|"
            r"certainty|certain to|for certain|(?:is|are|was|be|seems?|remains?|feels?)\s+(?:absolutely |very |quite |almost |fairly |entirely |"
            r"completely |totally )?certain)\b")
_PLN = r"(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|Surya|Chandra|Mangal|Budh|Guru|Shukra|Shani)"
# periods, windows, seasons and ages, refused in all three types (soft: a negated caveat such as "no window" is fine)
_TIME_CORE = (
    rf"windows?|(?:good|best|right|favou?rable|risky|dangerous|louder|peak\w*) (?:time|year|years|months?|stretch)|this (?:year|month|season)|"
    rf"next (?:year|month|season|spring|summer|autumn|winter)|spring|summer|autumn|winter|monsoon|seasons?|time comes|"
    rf"(?:around|at|by|before|after|until|till|near)\s+(?:the )?(?:ages? (?:of )?)?(?:\d{{2}}|{_NUMW})\b(?!\s+(?:minutes?|hours?|days?|weeks?|months?|per ?cent))|"
    rf"ages? \d{{2}}|(?:in|during) your (?:early |mid |late )?(?:teens|twenties|thirties|forties|fifties|sixties)|"
    rf"(?:early|mid|late) (?:twenties|thirties|forties|fifties|sixties)")
_TIME_PERIOD = rf"{_PLN}(?:['’]s)?\s+(?:major |sub-|minor )?(?:periods?|time|dasha|phase|years?|turn)|(?:major|sub|minor)[- ]?periods?|running periods? (?:of|under|in)"
_TIMEWORDS_NP = re.compile(rf"\b(?:{_TIME_CORE})\b", re.I)                       # intimacy: phases are read by chapter, so periods are named
_TIMEWORDS = re.compile(rf"\b(?:{_TIME_CORE}|{_TIME_PERIOD})\b", re.I)
_DASHA = re.compile(r"\b(?:dasha|mahadasha|antardasha|bhukti|periods?|sub-periods?|transit\w*)\b", re.I)
_CHILDREN_FORMS = [
    (re.compile(rf"\b(?:you|your chart|the chart|your 5th house|the 5th house)\b[^.!?;]*?\b(?:{_MODAL}|shows?|indicates?|promises?|denies|gives)\b[^.!?;]*?"
                rf"\b(?:have|bear|conceive|welcome|expect|be (?:blessed|given|granted)(?: with)?)\s+{_OBJ}{_KID}\b", re.I),
     "a forecast of having children", True),
    (re.compile(rf"\b(?:chart|house|lord|jupiter|venus|moon)\b[^.!?;]*?\b(?:shows?|indicates?|promises?|denies|gives|grants|blesses)\s+(?:you\s+)?{_OBJ}{_KID}\b", re.I),
     "a promise or denial of children", True),
    (re.compile(rf"\byou\b[^.!?;]*?\b{_MODAL}\b[^.!?;]*?\bbecom(?:e|ing) (?:a )?(?:parents?|mothers?|fathers?|mums?|moms?|dads?)\b", re.I),
     "a forecast of becoming a parent", True),
    (re.compile(rf"\byour (?:(?:first|second|third|next|new|future|unborn|own) )?{_KID}\s+(?:{_MODAL}|is going to)\b", re.I),
     "a forecast about a future child", True),
    (re.compile(rf"\b(?:are |be |is |been |am )?(?:blessed|gifted|granted|given) (?:with )?{_OBJ}{_KID}\b|"
                rf"\b(?:filled|full) (?:with|of) {_OBJ}{_KID}\b", re.I),
     "a promise of children", True),
    (re.compile(rf"\b(?:never|cannot|can't|unable to|won't|will not)\s+(?:\w+\s+){{0,3}}?(?:hold|have|bear|raise|get|see|welcome)\b[^.!?;]*?\b{_KID}\b", re.I),
     "a childless statement", True),
    (re.compile(rf"\b(?:limited progeny|childless\w*|child-?free|issueless|barren\w*|without (?:any )?{_KID}|no {_KID}|lack of {_KID}|"
                rf"denial of {_KID}|{_KID} (?:is|are|will be|may be|might be) (?:denied|blocked|refused|absent|missing|lacking)|"
                rf"empty (?:nest|arms|house)|cradle|stork|(?:lineage|family line)\b[^.!?;]*?\b(?:end|ends|ending|stops?|not continue|may not|will not|cannot|dies|breaks?|grows?|continues?|extends?))\b", re.I),
     "a childless or limited-progeny statement", True),
    (re.compile(rf"\b(?:number|count|total) of (?:your )?{_KID}|\b{_NUM}\s+(?:of\s+your\s+)?(?:own\s+)?{_KID}|\b(?:twins?|triplets?)\b|"
                rf"\b(?:a|one)\s+(?:son|daughter)\s+and\s+(?:a|one)\s+(?:son|daughter)|\bonly child\b|\bhow many {_KID}|"
                rf"\b{_KID}\s+(?:is|are|will be)\s+(?:few|many|several|numerous|plenty|scarce|rare|two|three|four|five|\d+)\b", re.I),
     "a number of children"),
    (re.compile(rf"\b{_KID}\b[^.!?;]*?\b(?:delay\w*|late|later|slow\w*|wait\w*|takes? (?:time|longer)|after (?:some |much )?(?:effort|waiting|time)|"
                rf"with effort|obstruct\w*|denied|denial)\b|\b(?:delay\w*|late|later|slow\w*|wait\w*|obstruct\w*|denial)\b[^.!?;]*?\b{_KID}\b|"
                rf"\b(?:postpon\w*|deferred|put off|on hold|pushed back|held back)\b[^.!?;]*?\b{_KIDX}\b|\b{_KIDX}\b[^.!?;]*?\b(?:postpon\w*|deferred|put off|on hold|pushed back|held back)\b", re.I),
     "a delay or obstruction of children"),
    (re.compile(rf"\b(?:conceiv\w*|conception|expect(?:ing|s|ed)?\s+{_OBJ}{_KID}|gives? birth|giving birth|birth of (?:a|your|the|any) (?:\w+ )?{_KID}|"
                rf"(?:first|second|third|next|new) (?:child|baby)|become (?:a )?parents?|become (?:a )?(?:mother|father|mum|mom|dad)|"
                rf"parenthood (?:in|by|around|before|after|during|at)|becoming (?:a )?(?:parent|mother|father)|(?:start|starting|begin|grow|growing|complete|completing|"
                rf"expand\w*) (?:a |your |the )?family|family planning|(?:have|having|bear|bearing)\s+{_OBJ}{_KID}|"
                rf"{_KID}\s+(?:will|may|might|could|would|shall|are going to|are likely to)\s+(?:come|arrive|appear|follow|be born|join|enter|increase)|"
                rf"when (?:will |would |do |can |might )?you (?:have|become|conceive|welcome|start|get))\b", re.I),
     "a forecast of conceiving, having or becoming a parent"),
    (re.compile(rf"\b{_KID}\b[^.!?;]*?\b(?:likel(?:y|ihood)|unlikely|probab\w*|chances?|odds|possib\w*|promised|guarantee\w*)\b|"
                rf"\b(?:likel(?:y|ihood)|unlikely|probab\w*|chances?|odds|possib\w*|promised|guarantee\w*)\b[^.!?;]*?\b{_KID}\b|"
                rf"\b(?:little|no|slim|poor|low|small|zero) (?:chance|hope|prospect)s? (?:of|for)\b[^.!?;]*?\b(?:family|{_KID})\b", re.I),
     "a likelihood of children"),
    (re.compile(rf"\b{_KIDX}\b[^.!?;]*?\b(?:at|by|before|after|around|until|till)\s+(?:the )?(?:ages? (?:of )?)?(?:\d{{2}}|{_NUMW})\b|"
                rf"\b(?:at|by|before|after|around|until|till)\s+(?:the )?(?:ages? (?:of )?)?(?:\d{{2}}|{_NUMW})\b[^.!?;]*?\b{_KIDX}\b|"
                rf"\b{_KIDX}\b[^.!?;]*?\b(?:in|during) your (?:early |mid |late )?(?:twenties|thirties|forties)\b|"
                rf"\b{_KIDX}\b[^.!?;]*?\b(?:19|20)\d\d\b|\b(?:19|20)\d\d\b[^.!?;]*?\b{_KIDX}\b", re.I),
     "an age or year of parenthood"),
]
_CHILDREN_FORMS.append(
    (re.compile(r"\b(?:family|household)\b[^.!?;]*?\b(?:grow(?:s|n)?|expand\w*|enlarg\w*|widen\w*|increas\w*|doubles?|swell\w*)\b(?!\s+(?:closer|stronger|"
                r"together|warmer|tighter|more (?:close|patient|warm)))|\b(?:grow(?:s|n)?|expand\w*)\s+(?:to|by)\s+" + _NUM + r"\b|"
                r"\barms\b[^.!?;]*?\b(?:empty|full|hold\w*|fill\w*)\b|\b(?:empty|full)\b[^.!?;]*?\barms\b", re.I),
     "a family that grows, or empty or full arms", True))
_CHILDREN_FORMS.append(
    (re.compile(r"\byou\b[^.!?;]*?\b(?:mother|father|parent|mum|mom|dad)\b[^.!?;]*?\b(?:one day|someday|eventually|in time|later in life|down the line|soon)\b|"
                r"\b(?:one day|someday|eventually|in time|later in life|down the line)\b[^.!?;]*?\byou\b[^.!?;]*?\b(?:mother|father|parent|mum|mom|dad)\b", re.I),
     "a parent role with a future time", True))
_CHILDREN_EXTRA = [
    (_TIMEWORDS, "a window, period, season, age or dated timing"),
    (_DASHA, "a dasha, period or transit word"),
    (re.compile(r"\bdelay\w*", re.I), "the word delay"),
]
# a kundli family section: the children forms, and a timing word only beside a children word (relatives may keep their fixed forecasts)
_CHILDREN_KUNDLI = _CHILDREN_FORMS + [
    (re.compile(rf"\b{_KIDX}\b[^.!?;]*?(?:{_TIMEWORDS.pattern}|{_DASHA.pattern})|(?:{_TIMEWORDS.pattern}|{_DASHA.pattern})[^.!?;]*?\b{_KIDX}\b", re.I),
     "a window, period or timing word beside children")]
_INTIMACY_FORMS = [
    (re.compile(r"\b(?:explicit\w*|erotic\w*|pornograph\w*|porn|orgasm\w*|kink\w*|fetish\w*|bdsm|foreplay|arous\w*|naked|nude|nudity|seduc\w*|"
                r"sex|sexual\w*|sexy|sensual\w*|lust\w*|libido|sex drive|in bed|bedroom|between the sheets|"
                r"climax\w*|intercourse|oral|one[- ]night stands?|hook-?ups?|casual sex|virgin\w*|stamina|performance (?:in|at) bed|"
                r"love-?making|make love|making love|physical union|manhood|womanhood|consummat\w*|coitus|copulat\w*|"
                r"carnal\w*|making out|make out|touched all over|under the (?:sheets|covers)|physical (?:pleasures?|craving\w*|desire\w*)|"
                r"bodily (?:pleasures?|desire\w*)|sensual|pleasures? of the (?:flesh|body|bed)|flesh(?:ly)?|kiss\w*|caress\w*|fondl\w*|grop\w*|"
                r"cuddl\w*|snuggl\w*|moan\w*|thrust\w*|steamy|racy|raunchy|naughty|undress\w*|strip(?:s|ped|ping|tease)|skin[- ]to[- ]skin|"
                r"genital\w*|breasts?|nipples?|thighs?|lingerie|hot and heavy|heat of the moment|erogenous|touch(?:ed|es|ing)? (?:you )?all over)\b", re.I),
     "explicit or sexual wording"),
    (re.compile(r"\b(?:sexual orientation|sexuality|gay|lesbian|bisexual|homosexual\w*|heterosexual\w*|queer|transgender|gender\w*|"
                r"non-?binary|lgbt\w*|asexual|pansexual|orientation|trans|straight(?! (?:answer|forward|away|line|talk))|"
                r"same[- ]sex|opposite[- ]sex|(?:drawn|attracted) to (?:men|women|males?|females?|boys|girls)|prefer\w* (?:men|women|males?|females?))\b", re.I),
     "orientation or gender wording"),
    # an attraction or preference aimed at a gender or sex, even negated ("not interested in men"): the chart is not read for it
    (re.compile(r"\b(?:attract\w*|interest\w*|drawn|prefer\w*|fanc(?:y|ies|ied)|desire\w*|into|crush\w*|love[sd]?|dat(?:e|es|ed|ing)|pull\w*|lean\w*)"
                r"\s+(?:to|in|by|toward|towards|for|on)?\s*(?:\w+\s+){0,3}?(?:men|women|males?|females?|boys|girls|guys|ladies|gentlemen|"
                r"same sex|both sexes|both genders|(?:your )?own (?:sex|gender)|either (?:sex|gender)|any (?:sex|gender)|man|woman)\b|"
                r"\bpartners? of (?:your own|the same|both|either|any|the opposite) (?:sex|gender)\b|\bwhich (?:sex|gender)\b", re.I),
     "an attraction aimed at a gender or sex", True),
    (re.compile(_MORAL, re.I), "moral labels"),
]
# "your <someone>" followed by a desire or conduct word is refused by default (a neighbour, fiancee, coworker, mistress, anyone not
# in this closed list of the person's own traits and chart words); T11.32.
_OWN_NOUN = (r"own|chart|horoscope|birth|natal|lagna|style|manner|nature|temperament|mind|heart|body|home|house|warmth|closeness|affection|"
             r"tenderness|trust|privacy|comfort|rest|routine|habits?|needs?|desires?|feelings?|love|passion|attraction|side|pace|approach|way|"
             r"energy|moods?|spirit|self|soul|personality|character|sense|capacity|ease|care|kindness|reserve|openness|patience|gentleness|"
             r"loyalty|ambitions?|dreams?|work|days?|evenings?|life|relationships?|bond|partnership|marriage|intimacy|time|space|words?|voice|"
             r"touch|attention|presence|reading|report|\d+(?:st|nd|rd|th)|venus|moon|sun|mars|jupiter|saturn|mercury|rahu|ketu|lords?|planets?|"
             r"placements?|signs?|dasha|periods?|strengths?|tendenc\w*|pull|pulls|restlessness|curiosity|independence|freedom|boundaries|"
             r"expectations|standards|values|principles|faith|promises?|commitment|first|second|instinct|instincts|reactions?|responses?|"
             r"inner|private|quiet|deepest|real|true")


def _your_other(words):
    """`your <someone>` + a desire or conduct word within four words, unless <someone> is one of the person's own traits."""
    return re.compile(rf"\byour\s+(?!(?:{_OWN_NOUN})\b)(?:[a-z-]+\s+)?[a-z-]+(?:['’]s)?\s+(?:[\w'’-]+\s+){{0,3}}?(?:{words})", re.I)


_DESIRE = (r"desire\w*|intima\w*|passion\w*|attract\w*|affection\w*|cheat\w*|faithful\w*|unfaithful\w*|lust\w*|wants?|needs?|crav\w*|"
           r"satisf\w*|conduct\w*|behaviou?r\w*|private|bed\b|fanc(?:y|ies|ied)|long(?:s|ing)|yearn\w*|adore[sd]?|love[sd]?|admir\w*|fond\w*|"
           r"enamou?r\w*|smitten|infatuat\w*|devot\w*|tempt\w*|drawn|draws?|pulled|miss(?:es)?|hugg?\w*")
_INTIMACY_EXTRA = [
    (_your_other(_DESIRE), "a third person's desires or conduct"),
    (re.compile(r"\b(?:your (?:partner|spouse|husband|wife|boyfriend|girlfriend|lover|ex|date|colleague|boss|friend|crush|neighbou?r|teacher)['’]?s?|"
                r"(?:he|she|they|him|her|them|his|their|someone|anyone)(?:['’]s)?)\b"
                rf"[^.!?;]*?\b(?:{_DESIRE})", re.I),
     "a third person's desires or conduct"),
    (re.compile(_CERTAIN, re.I), "certainty wording"),
    (_TIMEWORDS_NP, "a window, season, age or dated timing"),
]
_CONDUCT = (r"(?:affairs?|cheat\w*|stray\w*|betray\w*|unfaithful\w*|infidelit\w*|extramarital\w*|fling|liaisons?|sleep(?:s|ing)? around|two-?tim\w*|"
            r"philander\w*|disloyal\w*|cross the line|(?:be|stay|remain) (?:faithful|loyal)|someone on the side|"
            r"secret (?:lovers?|relationships?|partners?|romances?)|love triangles?|romance|wander\w*|lovers?|mistress\w*|paramour\w*|"
            r"keeps? (?:a |another )(?:lover|partner|woman|man|girl|boy)|sees? (?:someone|another)|playing around|fool(?:s|ing)? around|"
            r"play(?:s|ing)? away|step(?:s|ping)? out|run(?:s|ning)? around|fancy (?:woman|man)|toy ?boy|sugar (?:daddy|mommy))")
_AFFAIRS_FORMS = [
    (re.compile(rf"\byou\b[^.!?;]*?\b(?:{_MODAL}|are prone to|tend to|tends to|are inclined to|are apt to|are liable to|are capable of|are willing to|"
                rf"are the (?:type|sort|kind) to|are ready to|do)\b[^.!?;]*?\b{_CONDUCT}\b|"
                rf"\byou (?:often |sometimes |always |never |do )?(?:cheat|stray|wander|betray|two-?time|philander|sleep around|play around)\b", re.I),
     "a forecast or claim of conduct (you will, may, tend to, do ...)", True),
    (re.compile(rf"\b(?:expect|await\w*|on the cards|in store|lies ahead|is coming|on the way|beckons?)\b[^.!?;]*?\b{_CONDUCT}\b|"
                rf"\b{_CONDUCT}\b[^.!?;]*?\b(?:awaits?|on the cards|in store|lies ahead|is coming|is on the way|beckons?)\b|"
                r"\b(?:love triangle|secret romance|secret affair|double life|other (?:woman|man))\b", re.I),
     "a forecast of conduct (expect, awaits, on the cards ...)", True),
    (re.compile(_MORAL, re.I), "moral labels"),
]
_AFFAIRS_EXTRA = [
    (_your_other(_CONDUCT + r"|faithful\w*|loyal\w*|lie[sd]?|lying|secret\w*|hid\w*|sleep\w*|flirt\w*|mistress\w*|paramour\w*|keeps?|"
                 r"text(?:s|ing|ed)?|messag\w*|ghost\w*|" + _DESIRE), "a real partner's or another person's conduct"),
    (re.compile(rf"\b(?:your (?:partner|spouse|husband|wife|boyfriend|girlfriend|fianc\w*|lover|ex|date|colleague|boss|friend|neighbou?r|crush)['’]?s?|"
                rf"he|she|they|him|her|them|someone|anyone)\b[^.!?;]*?\b(?:{_CONDUCT}|faithful\w*|loyal\w*|loyalty|lie[sd]?|lying|secret\w*|hid\w*|"
                rf"(?:sees?|seeing) someone|sleep\w*|has (?:a|another) (?:lover|partner))\b|"
                rf"\b(?:{_CONDUCT}|faithful\w*|loyal\w*)\b[^.!?;]*?\b(?:of|by|from|with) "
                rf"(?:your (?:partner|spouse|husband|wife|boyfriend|girlfriend|fianc\w*|lover|ex)|him|her|them)\b", re.I),
     "a real partner's or another person's conduct"),
    (re.compile(rf"\b(?:{_CONDUCT})\b[^.!?;]*?\b(?:is|are|will|is (?:coming|likely|unavoidable|certain|shown|promised|indicated))\b[^.!?;]*?\b(?:coming|likely|unavoidable|certain|shown|promised|indicated|happen\w*|occur\w*)\b", re.I),
     "a forecast that an affair happens"),
    (re.compile(r"\byou(?: are| were| have been| remain| stay)\s+(?:\w+\s+)?(?:unfaithful|faithful|disloyal|loyal|adulterous|a cheat\w*|a philander\w*|"
                r"a flirt\w*|a two-?tim\w*)\b", re.I),
     "a verdict on the person's fidelity", True),
    (re.compile(_CERTAIN[:-3] + r"|verdicts?|judg(?:e)?ments?)\b", re.I), "certainty or verdict wording"),
    (_TIMEWORDS, "a window, period, season, age or dated timing"),
    (_DASHA, "a dasha, period or transit word"),
]
_NAME_OK = None
_NAME_VERB = re.compile(r"^(?:cheats?|lies|sleeps?|hides?|(?:is|was|are) (?:un)?faithful|(?:has|had) (?:a|another) (?:lover|affair))\b|"
                        r"^(?:desires?|wants?|needs?|craves?|loves?|adores?|longs?)\b.{0,12}\b(?:you|your|him|her|them|us|me)\b", re.I)


def _name_ok(w):
    """True for a capitalised word that is not a person's name: planets, signs, nakshatras, grade words, school names."""
    global _NAME_OK
    if _NAME_OK is None:
        parts = [PLANET_ANY] + [p for _, _, ps in vocab.SIGNS for p in ps] + [p for _, ps in vocab.NAKSHATRAS for p in ps]
        parts += ["Parashari", "Jaimini", "Lahiri", "Weak", "Moderate", "Strong", "Unknown", "Contradictory", "Raman", "Parashara",
                  "Lagna", "Navamsa", "Dasha", "Mahadasha", "Vimshottari", "Upapada", "Arudha", "Karakamsa", "Darakaraka", "Confirmed",
                  "Inferred", "Hypothesis", "Sanskrit", "Hindu", "Indian", "Vedic", "Synthetic", "Jataka", "Parijata"]
        _NAME_OK = re.compile(r"(?:" + "|".join(parts) + r")$", re.I)
    return bool(_NAME_OK.match(w))


def _name_hits(strings):
    """A capitalised word that looks like a given name, as subject or possessor, in intimacy and affairs text (owner decision:
    nothing about a named third person). Mid-sentence capitals count; a sentence-initial word counts only with a possessive or a
    desire or conduct verb after it. Write text in sentence case."""
    out = []
    for s in strings:
        for sent in re.split(r"(?<=[.!?;:])\s+|\n", s):
            toks = sent.split()
            for i, w in enumerate(toks):
                poss = bool(re.search(r"['’]s?$", w))
                core = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", re.sub(r"['’]s?$", "", w))
                if not re.fullmatch(r"[A-Z][a-z]{2,}", core) or _name_ok(core):
                    continue
                if i > 0 or poss or _NAME_VERB.search(" ".join(toks[i + 1:i + 5])):
                    out.append(("a named third person", core.lower()))
    return out


def _fold(s):
    """Contractions written out, so a gate that reads 'you will' also reads "you'll"."""
    s = re.sub(r"(?i)\bcan[’']t\b", "cannot", str(s))
    return re.sub(r"(?i)\b(\w+)[’']ll\b", r"\1 will", re.sub(r"(?i)\b(\w+)[’']re\b", r"\1 are",
                  re.sub(r"(?i)\b(\w+)[’']ve\b", r"\1 have", re.sub(r"(?i)\b(you|we|they|he|she|i)[’']d\b", r"\1 would", s))))


# --- children allow-list (T11.32, owner decision 2026-11-19) -----------------------------------------------------------------------
# A clause about the person's child or children may only DESCRIBE: a bond, a parenting style, an alternative. The verbs allowed there
# are a closed list (_AL_BASE, with their inflections); arrival, giving, having and becoming verbs, modals before any other verb,
# future forms, counts, ages, decades, pregnancy and newborn phrasings and closed, quiet or empty family metaphors are refused.
# shortcut: a word list plus two adjacency checks (the word after a child word, the word before it), not a parser. A verb that is
# in neither list and has no verb-like ending (-s, -ed, -ing) passes, and an over-block (an ordinary clause with "have" or "one"
# beside a child word) is accepted; widen _AL_BASE only through review.
_AL_BASE = ("bond connect guide teach mentor nurture encourage support enjoy share play learn listen understand inspire care spend adopt foster raise "
            "relate relax delight value love like appreciate respect protect comfort motivate reassure nourish reward tend find feel seem look make suit fit "
            "show reflect suggest mark read set shape help balance notice remember admire trust talk explain build create lead prefer deal cope work "
            "interact communicate engage parent attend supervise coach tutor entertain amuse charm calm soothe discipline manage handle treat speak joke "
            "laugh smile sing tell draw paint cook bake garden walk travel host train educate instruct empower uplift defend shelter watch observe serve "
            "volunteer assist advise counsel correct limit study cherish adore bring_up lookafter getalong geton stay remain keep stand sit grow "
            "respond react approach regard see consider sound").split()
_AL_IRREG = {"taught", "spent", "found", "felt", "made", "led", "understood", "built", "learnt", "shown", "told", "kept", "stood", "sat", "saw",
             "seen", "spoke", "spoken", "drawn", "read", "set", "cared", "loved"}


def _al_forms(b):
    f = {b, b + "s", b + "es", b + "ed", b + "d", b + "ing"}
    if b.endswith("e"):
        f.add(b[:-1] + "ing")
    if b.endswith("y"):
        f |= {b[:-1] + "ies", b[:-1] + "ied"}
    if b[-1:] not in "aeiouywx" and len(b) > 2:
        f |= {b + b[-1] + "ed", b + b[-1] + "ing"}
    return f


_AL_VERBS = set().union(*[_al_forms(b) for b in _AL_BASE]) | _AL_IRREG
# "show" and its kin describe only when a child word is not their object ("shows through care" yes, "shows you a son" no): they are
# allowed after a child word and not before it
_AL_NOSHOW = _AL_VERBS - {"show", "shows", "showing", "shown", "suggest", "suggests", "suggested", "suggesting", "mark", "marks", "marked",
                          "marking", "reflect", "reflects", "reflected", "reflecting", "sound", "sounds", "sounded", "see", "sees", "seen"}
_AL_PREP = set(("with for of to about by and or from like among around toward towards between in on at than as that which who whom whose when while "
                "so but nor yet into onto over under through during across along within without despite near beside upon per this these those "
                "his its us yours themselves always sometimes perhaps besides thus less unless plus whereas also often really simply quickly "
                "gradually naturally usually generally still even rarely not very quite too more most much all both each every other another "
                "their they them you your he she it we i the a an my our me him her").split())
_AL_COP = {"is", "are", "was", "were", "be", "been", "being", "am", "isn't", "aren't", "'s"}
_AL_MODAL = r"\b(?:may|might|could|would|can|should|must|cannot|won't|will|shall)\b"
_AL_ADV = {"not", "also", "often", "sometimes", "easily", "really", "always", "simply", "quickly", "gradually", "naturally", "usually",
           "generally", "still", "even", "rarely", "just", "only", "never", "well", "mostly", "mainly"}
_AL_SKIP = set(("a an the your my our his her their its you them him us me own first second third next new another any some no more other little "
                "baby young small big step grown older younger adult whole all both").split())
_KIDAL = re.compile(r"\b(?:children|child|kids?|babies|baby|newborns?|infants?|toddlers?|sons?|daughters?|little ones?|little feet|tiny feet|"
                    r"nursery|brood|quiver|boys?|girls?|footsteps|(?:small|tiny|little|pitter-patter) (?:feet|hands|toes)|heirs?|progeny|offspring|twins?|triplets?|lineage|bloodline|family line|cradle|stork|parenthood|"
                    r"motherhood|fatherhood|(?:the|your) line)\b")
_AL_REFUSE = re.compile(
    r"\b(?:come[sd]?|coming|came|arriv\w*|brings?|bringing|brought|giv(?:e|es|en|ing)|gave|bless\w*|welcom\w*|have|has|having|had|get|gets|getting|"
    r"got|gift\w*|grant\w*|join\w*|appear\w*|born|birth\w*|bear|bears|bearing|bore|carry|carries|carrying|receiv\w*|conceiv\w*|expect\w*|await\w*|"
    r"due|becom\w*|with child|trying|tries|try|belly|bump|empty|quiet|closed|shut|silent|barren|hollow|vacant|bare|locked|sealed|written|fated|"
    r"destined|meant|promis\w*|den(?:y|ies|ied)|will|shall|going to|about to|soon|eventually|someday|one day|ahead|future|later|early|late|next|"
    r"before|after|until|till|since|once|likely|unlikely|chance\w*|odds|pregnan\w*|\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"couple|pair|dozen|several|many|few|only|single|both|twice|twenties|thirties|forties|fifties|teens|age|ages|aged|decades?|years?|months?|"
    r"weeks?|season|winter|summer|spring|autumn|arrows?|grows? to|on (?:its|the|their) way|on the cards|in store|round|shown|indicated|seen|"
    r"visible|foretold|predicted|present|absent|missing|lacking|footsteps?|patter|(?:in|on) (?:the|your) (?:cards|stars)|"
    r"not in (?:your|the|this) (?:chart|cards|stars|fate|destiny|horoscope|future)|in your (?:future|destiny|fate)|not for you)\b")
_AL_CAVEAT_NEG = re.compile(r"\b(?:no|not|never|nothing|none|without|neither|nor)\b")
_AL_CAVEAT_NOUN = re.compile(r"\b(?:timing|count|counts|number|forecast|forecasts|window|windows|date|dates|prediction|predictions|verdict|"
                             r"promise|promises|claim|claims)\b")
_AL_CAVEAT_SAYS = re.compile(r"\b(?:says|said|states?|claims?|reads?|predicts?|forecasts?|promises?|implies|decides?)\b")


def _al_caveat(low):
    """A scope sentence that says what is NOT given ("No timing, count or forecast about children is given", "Nothing here says when or
    whether children come"): a negation beside a caveat noun, or beside a saying verb in a sentence that is not about "you"."""
    if not _AL_CAVEAT_NEG.search(low):
        return False
    if _AL_CAVEAT_NOUN.search(low):
        return True
    return bool(_AL_CAVEAT_SAYS.search(low)) and not re.search(r"\byou(?:r)?\b", low)


def _verbish(t):
    return bool(re.search(r"(?:ed|ing|(?<![sui])s)$", t)) and not re.search(r"(?:ss|us|is|ous|ness)$", t)


def _rel_baby(sent):
    """A neutral line about a relative's baby in the one fixed shape of family.md ("Your sister may welcome a baby in 2028."); it starts
    with "your" and names a relative, so the person's own children are never exempt."""
    x = _TRIM.sub("", sent.strip())
    return x.lower().startswith("your ") and bool(_SHAPE.fullmatch(x)) and bool(re.search(r"\b(?:baby|mother|father|parents?|grandparents?)\b", x, re.I))


def _kid_hits(strings):
    """(what, word) for each clause about a child that is not a plain description (see the allow-list note above)."""
    out = []
    what = "wording about children that is not a bond, a parenting style or an alternative (only describing those is allowed)"
    for s in strings:
        for sent in re.split(r"(?<=[.!?])\s+|[;:—–]|\n", s):
            low = sent.lower()
            if not _KIDAL.search(low):
                continue
            if _al_caveat(low):
                continue
            for part in re.split(r",|\s(?:which|while|but)\s", low):
                if not _KIDAL.search(part):
                    continue
                part = re.sub(r"\b(?:look|looks|looking|looked) after\b", " lookafter ", part)
                part = re.sub(r"\b(?:get|gets|getting|got) along\b", " getalong ", part)
                part = re.sub(r"\b(?:get|gets|getting|got) on\b", " geton ", part)
                part = re.sub(r"\b(?:bring|brings|bringing|brought) up\b", " bring_up ", part)
                bad = [m.group() for m in _AL_REFUSE.finditer(part)]
                for m in re.finditer(_AL_MODAL, part):         # a modal may only stand before a describing verb
                    nxt = [w for w in re.findall(r"[a-z'’_-]+", part[m.end():]) if w not in _AL_ADV][:1]
                    if nxt and nxt[0] not in _AL_VERBS:
                        bad.append(f"{m.group()} {nxt[0]}")
                for k in _KIDAL.finditer(part):
                    after = re.findall(r"[a-z'’_-]+", re.sub(r"^['’]s\b", "", part[k.end():]))[:1]
                    if after and not (after[0] in _AL_VERBS | _AL_PREP | _AL_COP | _AL_ADV or after[0].endswith("ly")
                                      or re.fullmatch(_AL_MODAL, after[0]) or _KIDAL.fullmatch(after[0])) and _verbish(after[0]):
                        bad.append(f"{k.group()} {after[0]}")
                    before = [w for w in re.findall(r"[a-z'’_-]+", part[:k.start()])
                              if not (w in _AL_SKIP or re.fullmatch(r"\d+(?:st|nd|rd|th)?", w))][-1:]
                    if before:
                        w = re.sub(r"['’]s$", "", before[0])
                        if (not (w in _AL_NOSHOW | _AL_PREP | _AL_COP | _AL_ADV or w.endswith("ly") or re.fullmatch(_AL_MODAL, w))
                                and _verbish(w) and before[0] == w):
                            bad.append(f"{w} {k.group()}")
                out += [(what, b) for b in dict.fromkeys(bad)]
    return out


# batch 4: a transit, the nodes, the year chart or Saturn's passage is never read as danger, ruin or a curse (medical and
# death words are refused for every type by the shared list)
# T11.38: the families below are meaning classes (stems with their inflections), not lists of the words seen so far: fear
# and catastrophe; partner failure and parting; match rules; remedies; verdicts and totals; promises and certainty. The
# strings are folded first (you'll, you're going to -> you will). shortcut: stems, not a reading for meaning, so a new
# synonym outside a class still passes; widen the class through review.
_FEAR = [(re.compile(r"\b(?:accident\w*|danger\w*|disaster\w*|calamit\w*|catastroph\w*|cataclysm\w*|trag(?:edy|edies|ic)|doom\w*|"
                     r"ruin\w*|destroy\w*|destruct\w*|devastat\w*|shatter\w*|crush\w*|wreck\w*|wreak\w*|smash\w*|crippl\w*|collaps\w*|"
                     r"crumbl\w*|(?:falls?|falling|fell) apart|havoc|mayhem|chao(?:s|tic)|turmoil|upheaval\w*|"
                     r"curse[sd]?|jinx\w*|hexed|misfortunes?|bad luck|ill[- ](?:fated|starred|omened|boding|luck|timed)|inauspicious\w*|"
                     r"unlucky|omens?|forebod\w*|baleful|sinister|ominous|evil|"
                     r"terribl\w*|terrif\w*|terror\w*|horri\w*|harrow\w*|fear\w*|frighten\w*|fright|scar(?:y|ed|e)|dread\w*|panic\w*|"
                     r"alarm\w*|petrif\w*|haunt\w*|demon\w*|malevol\w*|menac\w*|threat\w*|endanger\w*|jeopard\w*|at risk|harm(?:s|ed|ing|ful\w*)?|damag\w*|"
                     r"peril\w*|hazard\w*|treacher\w*|shock\w*|victim\w*|"
                     r"grim(?:mer|mest)?|bleak\w*|dire(?:st)?|darkest|(?:dark|black|evil) (?:period|phase|time|days|years?|spell|chapter|stretch)|"
                     r"miser(?:y|ies|able|ably)|wretch\w*|woe(?:s|ful)?|agon(?:y|ies|i[sz]\w*)|anguish\w*|ordeal\w*|scourge\w*|blight\w*|"
                     r"hell(?:ish)?|brutal\w*|savage\w*|vicious\w*|merciless\w*|unbearabl\w*|intolerabl\w*|cruel\w*|torment\w*|"
                     r"suffer\w*|punish\w*|wrath|downfall|bankrupt\w*|nightmar\w*|disgrac\w*|humiliat\w*|scandal\w*|"
                     r"(?:heavy|huge|great|big|severe|major|massive|terrible|serious|grave) (?:loss|losses|setbacks?|blows?|trouble|crisis|"
                     r"crises|debts?)|spells? (?:trouble|the end)|lose everything|bad years?|worst (?:time|years?|period|phase))\b", re.I),
          "danger, ruin, curse or fear framing")]
# batch 5 (T11.35). Mangal dosha: no marriage-failure or partner-harm wording, no match rule, no remedy (death and illness
# words are refused by the shared list). Raj yoga: no promise of fame, wealth, rank or certainty.
_PARTNER = (r"(?:spouses?|partners?|husbands?|wi(?:fe|ves)|marriages?|married life|marital|matrimon\w*|wedlock|relationships?|"
            r"unions?|couples?|weddings?|engagements?|betroth\w*|alliances?|bonds?)")
_FAIL = (r"(?:harm|hurt|damag|endanger|threat|afflict|suffer|ruin|doom|destroy|spoil|jeopardi[sz]|fail|break|broke|collaps|unhappy|"
         r"misfortune|loss|los(?:e|es|t|ing)\b|ends?\b|ended|ending|split|sour|wreck|shatter|crumbl|crack|dissolv|postpon|delay|"
         r"block|obstruct|prevent|den(?:y|ies|ied)\b|stormy|tempestuous|turbulent|rocky|troubled|bitter|discord|strife|quarrel|"
         r"fight|feud|(?:falls?|falling|fell|drift\w*|grow\w*|grew|come|came|break|broke|tear|torn) (?:apart|through)|called off|"
         r"broken off|on the rocks)")
_MANGAL = [(re.compile(rf"\b(?:divorc\w*|separat(?:ed|ing|ion|ions)\b|separates?\s+(?:from|them|you|the couple)|split(?:s|ting)? up|break-?ups?|breaking up|broke up|"
                       rf"break up|estrang\w*|desert(?:s|ed|ing|ion)\b|abandon\w*|walk(?:s|ed|ing)? out|part(?:s|ed|ing)? ways|"
                       rf"leav(?:e|es|ing)\s+(?:you|him|her|them|home|the home|the house|the marriage)|left (?:you|him|her|them)\b|"
                       rf"widow\w*|bereave\w*|remarr\w*|(?:second|another|two|multiple) marriages?|more than one marriage|"
                       rf"discord\w*|strife|quarrel\w*|feud\w*|(?:constant|frequent|endless|bitter|violent|full of) "
                       rf"(?:fights?|fighting|arguments?|rows|clashes|conflicts?)|lonel\w*|alone (?:later )?in life|end (?:up )?alone|"
                       rf"left alone|single for life|stays? single|remains? (?:single|unmarried)|unmarried|called off|"
                       rf"(?:falls?|falling|fell) through|unlucky (?:bride|groom|{_PARTNER})|"
                       rf"{_FAIL}\w*{_S}\b{_PARTNER}|\b{_PARTNER}{_S}\b{_FAIL}\w*|"
                       rf"\b(?:takes?|took|taking|claims?|removes?|lose|loses|losing|lost)\s+(?:your|the|a|his|her|their)\s+{_PARTNER}|"
                       rf"(?:fail\w*|break\w*|collaps\w*|trouble\w*|crisis|crises)\s+(?:of\s+)?(?:a |the |your )?{_PARTNER})\b", re.I),
            "marriage-failure or partner-harm wording"),
           (re.compile(r"\b(?:(?:must|should|only|never|do not|don't|avoid|can only|ought to|has to|have to|needs? to|is to)\s+"
                       r"(?:\w+\s+){0,2}?(?:marr(?:y|ies|ied|ying)\b|wed(?:s|ded|ding)?\b|get married|tie the knot)|"
                       r"(?:marr(?:y|ies|ied|ying)|wed(?:s|ded|ding)?)\s+(?:\w+\s+){0,2}?(?:mang(?:a)?lik|mangli)\w*|"
                       r"(?:mang(?:a)?lik|mangli)\w*\b[^.!?;]*\b(?:must|should|only|safe|unsafe|required|ought|best|ideal)|"
                       r"only (?:a |an )?(?:mang(?:a)?lik|mangli)\w*)\b", re.I),
            "marriage advice or a match rule"),
           (re.compile(r"\b(?:gem(?:stone)?s?|corals?|pearls?|sapphires?|emeralds?|rub(?:y|ies)|diamonds?|hessonite|gomed|moonga|neelam|"
                       r"panna|pukhraj|manik\w*|topaz|opals?|cat'?s[- ]eye|rudraksha\w*|mantras?|stotra\w*|chant\w*|recit\w*|jap(?:a|am)\b|"
                       r"jaap|homa\w*|havan\w*|yagy?as?|yajnas?|pooja|puja\w*|shanti|pacif\w*|propitiat\w*|appeas\w*|rituals?|fasting|"
                       r"fast on|kumbh|vivah|hanuman|donat\w*|charity|amulets?|yantras?|talisman\w*|temple visits?|visit\w* (?:a |the )?temple|"
                       r"peepal|pipal|banana tree|(?:tree|pot|banana|plantain|vishnu|idol|statue) (?:marriage|wedding)|"
                       r"marr(?:y|ies|ied|ying)\s+(?:\w+\s+){0,2}?(?:tree|pot|idol|statue)|"
                       r"offer(?:ing)?s?\s+(?:of\s+)?(?:water|milk|sweets|red|jaggery|lentils|food)|"
                       r"wear\w*\s+(?:a |an |the )?(?:\w+\s+){0,2}(?:stone|ring|gem|pendant|thread|bracelet|locket)|remed(?:y|ies)|"
                       r"(?:remov|neutrali[sz]|nullif|lift|eras|counter|get rid of|ward\w* off)\w*\s+(?:the |this |your |its )?"
                       r"(?:dosha|mars|mangal|effect|affliction))\b", re.I), "remedies (asked for in their own request, never in this report)")]
_KSUM = r"(?:9|[1-9]\d)(?:\.\d+)?"          # above the largest one-koota maximum (nadi, 8): only a sum reaches it
_MATCH = [(re.compile(rf"\b(?:36|thirty-six|totals?|totall?ed|sum(?:s|med|ming)?|summ\w*|add(?:s|ed|ing)? up|aggregate\w*|"
                      rf"tall(?:y|ies)|cumulative|altogether|all told|grand total|combined (?:score|total|points|kootas)|"
                      rf"(?:overall|match|compatibility) (?:scores?|points|tally|result)|koota (?:scores?|tally|result)s?|guna milan|gunas?|ashtakoot\w*|compatib\w*|"
                      rf"cut-?off|threshold|pass mark|minimum (?:score|points)|(?:comes?|came|amounts?|adds?|added) to\s+\d|"
                      rf"{_KSUM}\s*(?:points?|pts|marks)|(?:of|out of)\s+(?:a possible\s+|the\s+)?{_KSUM}\b"
                      rf"(?!\s*(?:st|nd|rd|th|signs?|stars?|nakshatras?|from|back)))", re.I),
           "a koota total or score (the four kootas are never added up)"),
          (re.compile(r"\b(?:(?:good|bad|poor|perfect|ideal|excellent|great|weak|strong|right|wrong|fine|sound|solid|happy|lucky|"
                      r"unlucky|blessed|doomed|favou?rable|unfavou?rable|auspicious|inauspicious|promising) (?:match|pair(?:ing)?|couple|"
                      r"union|marriage|alliance|wedding)|"
                      r"(?:match|union|marriage|alliance|pairing|pair|couple)\s+(?:is|looks|seems|appears|would be|will be)\s+(?:\w+\s+)?"
                      r"(?:favou?rable|unfavou?rable|auspicious|inauspicious|promising|good|bad|poor|excellent|ideal|perfect|strong|weak|"
                      r"approved|blessed|doomed|fine|unsuitable|suitable|right|wrong)|"
                      r"(?:well|ill|badly|poorly|perfectly|ideally|nicely)[- ](?:suited|matched)|suit(?:s|ed)? (?:each other|one another)|"
                      r"(?:un)?suitab\w*|mismatch\w*|matched (?:pair|couple)|unwise|(?:in)?advisab\w*|"
                      r"recommend\w*\s+(?:the |this |that )?(?:match|marriage|union|alliance|proposal|wedding|pair\w*)|"
                      r"(?:match|marriage|union|alliance|proposal|wedding)\s+(?:is |are |comes )?(?:\w+\s+)?recommended|"
                      r"advis(?:e|es|ed|ing)\s+(?:\w+\s+){0,3}?(?:to\s+(?:proceed|marry|wed|go ahead)|against)|"
                      r"favou?r(?:s|ed|ing)?\s+(?:the |this )?(?:match|marriage|union|alliance|wedding)|"
                      r"(?:approv|reject|accept)\w*\s+(?:the |this )?(?:match|marriage|alliance|proposal|union)|approv\w*|bless\w*|"
                      r"green light|go(?:es)? ahead|(?:to|should|can|may|must)\s+proceed|proceed with|tie the knot|call\w* off|"
                      r"rul(?:e|es|ed|ing)\s+(?:\w+\s+){0,3}?out|"
                      r"(?:right|ideal|perfect|best|wrong|suitable|good|bad) (?:partner|person|one|spouse|husband|wife|bride|groom|choice)|"
                      r"(?:fine|good|great|perfect|poor|bad|ideal|excellent|strong|weak|right|wrong) fit (?:for|between)|"
                      r"(?:should|must|can|cannot|can't|ought to)\s+(?:not\s+)?(?:marry|wed|get married)|(?:made|meant) for each other|"
                      r"soul ?mates?)\b", re.I), "a verdict to marry or not (fit is given as tendencies)", "hard"),
          (re.compile(r"\b(?:povert\w*|sorrow\w*|quarrel\w*|hidden harm|loss of (?:money|wealth|children|progeny))\b", re.I),
           "the sources' grave readings of a count (not repeated)")]
_LK_COSTLY = [(re.compile(r"\b(?:gem(?:stone)?s?|sapphires?|emeralds?|rub(?:y|ies)|diamonds?|cat'?s[- ]eye|hessonite|corals?|"
                          r"yagy?as?|yajnas?|havans?|homams?|(?:paid|costly|expensive)\s+\w+)\b", re.I),
               "gems or costly rituals (remedy-safety.md §1)")]
_GAIN = r"(?:successful|known|renowned|recogni[sz]ed|honou?red|rich|wealthy|famous|powerful|prosperous|celebrated|elevated|promoted|a leader)"
_RAJ_PROMISE = [(re.compile(
    r"\b(?:famous|fame|renown\w*|celebrit\w*|celebrated|well-?known|household name|big name|stardom|superstar\w*|"
    r"known (?:across|throughout|all over|everywhere|worldwide|far and wide|nationwide|globally)|prestig\w*|eminen\w*|illustrious|"
    r"legendary|elite|VIP|aristocra\w*|high society|rich(?:es)?|wealth\w*|affluen\w*|opulen\w*|prosper\w*|abundan\w*|luxur\w*|"
    r"lavish\w*|(?:multi)?millionaire\w*|billionaire\w*|fortunes?|kingly|kings?|queens?|royal\w*|rulers?|minist\w+|presidents?|"
    r"governors?|head of state|throne|high (?:office|rank|post|position|status|standing|authority)|"
    r"(?:top|highest|lofty) (?:post|rank|position|job|office|seat)|top of (?:your|the|his|her|their) (?:field|profession|career|tree|game|class)|"
    r"(?:reach\w*|ris(?:e|es|ing)|rose|climb\w*|get|gets|got|make it|end\w* up|go|goes|went)\s+(?:\w+\s+){0,2}?(?:to |at )?the top|"
    r"(?:great|immense|vast|enormous|huge|real|tremendous) (?:influence|power|authority|wealth|riches|status|success|standing|fame|recognition)|"
    r"(?:rise|rises|rising|rose) to power|power and (?:prosperity|wealth|status|fame|position)|powerful (?:position|person|figure|leader|post)|"
    r"wield\w* power|(?:big|major|huge|great|sure|certain|guaranteed) promotion|"
    r"guarante\w*|destin(?:y|ed)|fated|assur(?:e|es|ed)|a given|in store|on the cards|in the cards|born to|await\w*|lies? ahead|"
    r"is yours|will be yours|com(?:e|es|ing) your way|"
    rf"will\s+(?:\w+\s+)?(?:become|rise|achieve|attain|prosper|succeed|be (?:\w+\s+)?{_GAIN})|"
    rf"(?:make|makes|made|making) you (?:\w+\s+)?{_GAIN}|"
    r"(?:money|wealth|riches|success|status|recognition|honou?rs?|rank|promotion|power|authority|fame|position|standing|leadership)\s+"
    r"(?:will|shall)\s+(?:\w+\s+)?(?:come|flow|pour|follow|arrive|be yours|find you|rain))\b|" + _CERTAIN, re.I),
                 "a promise of fame, wealth, rank or certainty")]
# the families above read folded strings: you'll -> you will, (you are) going to -> will
_GOING = re.compile(r"\b(?:am|is|are|was|were)\s+going\s+to\b|\bgonna\b", re.I)
FOLD_TYPES = (*("jupiter-transit", "rahu-ketu", "varshaphal", "sade-sati"), "mangal-dosha", "raj-yoga", "match", "lal-kitab", "kaal_sarp")
TYPE_GATES = {
    "wealth": [(re.compile(r"[₹$€£]|\bRs\.?\s?\d|\b(?:lakhs?|crores?|rupees?|dollars?|USD|INR)\b", re.I), "money amounts"),
               (re.compile(rf"\b(?:invest\w*|stocks?|bets?|betting|gambl\w*|lotter(?:y|ies)|tickets?|crypto\w*|mutual funds?|"
                           rf"(?:stock|share) market|time to (?:buy|sell)|(?:buy|sell)(?:ing)?\s+{_BUY}\b|"
                           rf"trad(?:e|es|ed|ing)\s+(?:in\s+)?(?:stocks?|shares|futures|options|crypto\w*|the market)|"
                           rf"shares?\s+(?:in|of)\s+(?:a |the )?(?:company|companies|market)\b)", re.I),
                "investment, trading, bet or lottery wording"),
               (re.compile(rf"\b(?:inherit\w*|legac(?:y|ies)){_S}\b(?:dies?|death|dead|passes? away|passing)\b|"
                           rf"\b(?:dies?|death|dead|passes? away|passing){_S}\b(?:inherit\w*|legac(?:y|ies))", re.I),
                "an inheritance tied to a relative's death")],
    "education": [(re.compile(r"\bguarantee\w*|\b(?:will|shall|surely|definitely)\s+(?:(?:surely|definitely)\s+)?(?:"
                              r"get\s+(?:\w+\s+){0,2}?(?:admission|seat|rank|marks|scholarship|degree)|gain admission|"
                              r"win\s+(?:\w+\s+)?(?:seat|scholarship|rank|admission)|"
                              r"(?:clear|pass|crack)\s+(?:the |your )?(?:exams?|tests?|papers?|courses?|entrance)|"
                              r"top\s+(?:the |your )?(?:class|exams?)|score|be admitted)\b", re.I),
                   "an admission, pass or result promise"),
                  (re.compile(rf"\b(?:scores?|scored|marks|rank|percentile|c?gpa){_S}\d|\d{_S}\b(?:marks|scores?|rank|c?gpa)\b", re.I),
                   "scores, marks or rank figures")],
    "reputation": [(re.compile(r"\b(?:famous|fame|celebrity|stardom|elections?|elected|public office|scandals?|go(?:es)? viral)\b", re.I),
                    "fame, election or scandal wording"),
                   (re.compile(r"\b(?:courts?\b(?!-)|lawsuits?|sue[ds]?|convict\w*|acquit\w*|verdicts?|jail|prison|arrest\w*|litigation)\b", re.I),
                    "legal outcomes")],
    "spirituality": [(re.compile(r"\b(?:enlighten\w*|(?:old|young|advanced|evolved|elevated|high(?:er)?) souls?|"
                                 r"spiritually (?:advanced|evolved|superior|elevated|gifted)|highly (?:spiritual|evolved)|"
                                 r"spiritual (?:rank|level|grade|attainment|superiority)|more spiritual than|"
                                 r"realis(?:ed|ation)\s+(?:being|soul|master|yogi|person|one)|self-?realis\w*|self-?realiz\w*|"
                                 r"siddhis?|psychic\w*|attainment of|born an? (?:sage|saint|yogi|master)|reborn (?:master|sage|saint|yogi)|awakening complete\w*|(?:final|full|complete|ultimate) (?:liberation|awakening|realisation|moksha|enlightenment)|"
                                 r"awaken\w*\s+fully|"
                                 r"(?:attain|reach|achieve|gain)\w*\s+(?:moksha|liberation|enlightenment|nirvana|samadhi)|"
                                 r"(?:moksha|liberation|nirvana|samadhi)\b[^.!?;]*\b(?:in|by|before|during|around)\s+"
                                 r"(?:this life|(?:\w+\s+)?\d{4}))\b", re.I),
                      "spiritual rank or level claims"),
                     (re.compile(r"\b(?:(?:past|previous|former|prior|last)[\s-]+(?:life|lives|lifetimes?|births?|incarnations?)|"
                                 r"final (?:birth|incarnation)|earlier (?:births?|lifetimes?|incarnations?)|before this life|before (?:this )?birth|from before\b|walked this path|"
                                 r"many (?:lives|lifetimes|times before)|reincarnat\w*|karma from before|karmic debts?)\b", re.I),
                      "past-life claims"),
                     (re.compile(r"\b(?:curses?[ds]?|shaap|shrapa|hexed?|black magic|evil eye|nazar|witchcraft|jinx\w*|"
                                 r"negative energy\b[^.!?;]*\b(?:sent|from others)|pitr[ai]?\s?dosh\w*|pitr[ai]? rin|cast\w*\s+(?:a |the )?spell|(?:under|put) a spell|spells? on you)\b", re.I), "curse claims"),
                     (re.compile(r"\b(?:should|must|ought to|need to|have to)\s+(?:renounce|abandon|leave (?:your )?(?:family|home|job)|"
                                 r"become an? (?:monk|nun|sannyasi\w*|renunciate|sadhu))\b", re.I), "advice to renounce")],
    "self": [(re.compile(rf"\b(?:at|by|before|after|around|until|till|from) (?:the )?ages? (?:of )?(?:\d|{_NUMW})|\bages? \d{{1,2}}\b|"
                         rf"\b(?:at|after|before|by|around|until|till|from) (?:\d{{2}}\b|{_NUMW}\b(?!\s+(?:minutes?|hours?|days?|weeks?|months?)))|"
                         rf"\b(?:in )?(?:your|the) (?:early |mid |mid-|late )?(?:teens|twenties|thirties|forties|fifties|sixties)\b|"
                         rf"\b(?:when|once) you (?:are|turn|reach) (?:\d{{2}}|{_NUMW})\b|\b(?:hit|turn|reach)\w*\s+(?:\d{{2}}|{_NUMW})\b|\b\d{{2}}(?:st|nd|rd|th) (?:year|birthday)\b", re.I),
              "fixed-age claims"),
             (re.compile(r"\b(?:skin\w*|teeth|nose|lips|neck|chest|shoulders?|legs?|knees?|forehead|scars?|moles?|birthmarks?|"
                         rf"spine|bones?|throat|joints?|limbs|bald\w*|hair (?:loss|fall)|receding|eyes? (?:are|is|of)\b(?!\s+(?:\w+\s+)?(?:{_EYE})\b))", re.I),
              "body-part claims"),
             (re.compile(r"\b(?:attractive\w*|pretty(?!\s+(?:sure|much|well|good|soon|clear|likely|quickly))|ugly|good[- ]looking|good looks|"
                         r"gorgeous|handsome|(?:strikingly |very )?beautiful(?= (?:face|woman|man|looks?|eyes|person))|lovely (?:face|looks?|eyes|smile)|"
                         r"strikingly (?:beautiful|handsome|good)|stunning|(?:charming|striking|fine|nice|great|stunning|pleasing) (?:looks|appearance|features))\b", re.I),
              "attractiveness claims"),
             (re.compile(r"\b(?:weigh(?:s|ed|ing)?\s+(?:little|a lot|much|more|less|too|\d)|weight(?!\s+of)|overweight|underweight|obese|obesity|fat|diet|plump|heavy-?set|bulky|kilos?|kgs?|pounds)\b", re.I),
              "weight claims")],
    # self, outside the 'appearance' section: hair and eye colour are refused there (hair is also a LOOKS word)
    "self_outside": [(re.compile(rf"\bhair\b|\beye[- ]colou?r\b|\beyes? (?:are|is|of)\s+(?:\w+\s+)?(?:{_EYE})\b|\b(?:{_EYE})[- ]eyed\b|\b(?:{_EYE})\s+eyes\b", re.I),
                      "hair or eye colour")],
    # family: a section about one relative (mother, father, siblings) names that relative by context, so a harm word alone is refused there
    "family_sec": [(re.compile(rf"\b(?:{_HARM})\b", re.I), "a parent's or sibling's illness, health, life span or death")],
    "family": [(re.compile(rf"(?<!\byou )\b(?:may|might|could|will|would) (?:take|call) (?:your|his|her|their) (?:{_REL})\b", re.I),
                "a parent's or sibling's illness, health, life span or death"),
               (re.compile(rf"\b(?:{_PAR})\b{_S}\b(?:{_HARM})\b|\b(?:{_HARM})\b{_S}\b(?:{_PAR})\b", re.I),
                "a parent's or sibling's illness, health, life span or death"),
               (re.compile(rf"\b(?:los(?:e|es|ing|t)|loss of)\s+(?:a |an |your |the |one of your )?(?:{_PAR})\b", re.I),
                "a parent's or sibling's illness, health, life span or death")],
    "challenges": [(re.compile(
        r"\b(?:(?:(?:never|won't|will not|cannot|can't)\s+)?(?:win|won|winning|lose|lost|losing)\s+(?:out\s+)?"
        r"(?:the |your |a |this |that |any )?(?:\w+\s+)?"
        r"(?:cases?|suits?|lawsuits?|trials?|disputes?|litigation|appeals?|hearings?)|never\s+(?:lose|fail|be defeated)|"
        r"verdicts?|acquit\w*|convict\w*|sentenc(?:ed|ing)|jail\w*|prison\w*|imprison\w*|arrest\w*|"
        r"(?:courts?(?!-)|judges?|tribunals?|magistrates?)\b[^.!?;]*\b(?:rul(?:e|es|ed|ing)|decid\w*|favou?r\w*|sides?|"
        r"finds?|award\w*|order\w*|grant\w*|dismiss\w*)|"
        r"(?:case|suit|lawsuit|trial|appeal|claim|dispute|hearing|litigation)\b[^.!?;]*\b(?:your way|in your favou?r|against you|"
        r"for you|(?:is|are|will be|gets?|was) (?:won|lost|decided|settled|dismissed)|(?:will|shall) (?:end|go|succeed|fail|be (?:won|lost|decided)))|"
        r"(?:succeed|prevail|triumph)\w*\s+(?:in|over)\s+(?:court|the case|the dispute)|"
        r"(?:victory|victorious|defeat\w*|destroy\w*|vanquish\w*|crush\w*)\b[^.!?;]*\b(?:enem\w*|opponents?|rivals?|foes?)|"
        r"(?:enem\w*|opponents?|rivals?|foes?)\b[^.!?;]*\b(?:defeat\w*|destroy\w*|vanquish\w*|crush\w*|ruined)|"
        r"come out on top|(?:favou?rable|adverse|unfavou?rable) (?:judg(?:e)?ments?|rulings?|orders?|decisions?)|"
        r"compensation\b[^.!?;]*\b(?:paid|granted|awarded)|(?:pays?|paid) you|backs? down|"
        r"(?:triumph|prevail|victory)\w*\s+over\s+(?:them|him|her)\b|you win\b(?!\s+(?:people|friends|trust|hearts?|respect|support|over))|"
        r"file\s+(?:the |a |your )?(?:case|suit|lawsuit|claim|complaint|petition)|su(?:e|es|ed|ing)\s+(?:him|her|them|your|the)|"
        r"(?:get|gain|keep|receive|obtain)\w*\b[^.!?;]*\b(?:in|from|through) the (?:legal|court)|"
        r"guarantee\w*\s+(?:a |the |your )?(?:settlement|outcome|compensation|win)|"
        r"(?:settlement|outcome)\s+(?:is|will be)\s+guaranteed|"
        r"(?:court|hearing|trial|judg(?:e)?ment|verdict)\s+dates?|"
        r"date of (?:the |your )?(?:hearing|trial|judg(?:e)?ment|verdict))\b", re.I),
        "legal outcomes or court timing"),
        (re.compile(rf"\b(?:{_LEGAL})\b{_S}\b(?:{_OUTCOME})\b|\b(?:{_OUTCOME})\b{_S}\b(?:{_LEGAL})\b", re.I),
         "a legal or opponent word with an outcome word")],
    "children_forms": _CHILDREN_FORMS,
    "children_kundli": _CHILDREN_KUNDLI,
    "children": _CHILDREN_FORMS + _CHILDREN_EXTRA,
    "intimacy_forms": _INTIMACY_FORMS,
    "intimacy": _INTIMACY_FORMS + _INTIMACY_EXTRA,
    "affairs_forms": _AFFAIRS_FORMS,
    "affairs": _AFFAIRS_FORMS + _AFFAIRS_EXTRA,
    **{t: _FEAR for t in ("jupiter-transit", "rahu-ketu", "varshaphal", "sade-sati")},
    "mangal-dosha": _FEAR + _MANGAL,
    "raj-yoga": _FEAR + _RAJ_PROMISE,
    "match": _FEAR + _MANGAL + _MATCH,
    "lal-kitab": _FEAR + _LK_COSTLY,
    "kaal_sarp": _FEAR,                 # a kundli unit that names Kaal Sarp
}


def _clauses(s):
    """Pieces of s split at clause breaks; a gate match never spans a break."""
    pos = 0
    for m in _CLAUSE.finditer(s):
        yield s[pos:m.start()]
        pos = m.end()
    yield s[pos:]


def _excused(before, hit):
    """A negation excuses a match only when it sits just before it (within about six words, eight across an
    'or'/'and' list) and is not an emphatic idiom ('without doubt', 'no worry'). 'never predicted' inside a match
    ('A legacy is never predicted from a death') also counts."""
    if _NEG_VERB.search(hit):
        return True
    words = re.findall(r"[\w'’-]+", _EMPH.sub(" ", before))
    pos, n = len(words), 6
    while True:
        win = words[max(0, pos - n):pos]
        if any(w.lower() in _NEG_WORDS or w.lower().endswith("n't") for w in win):
            return True
        conj = [i for i, w in enumerate(win) if w.lower() in ("or", "and", "nor")]
        if not conj:
            return False
        pos, n = pos - len(win) + conj[-1], 8


def gate_hits(t, strings):
    """(what, word) for each gate match in a clause that no negation just before it excuses (a referral such as
    'ask a doctor' excuses its clause)."""
    out = []
    if t.split("_")[0] in ("children", "intimacy", "affairs"):
        strings = [_fold(x) for x in strings]
    if t in FOLD_TYPES:
        strings = [_GOING.sub("will", _fold(x)) for x in strings]
    if t in ("children_kundli", "children_forms"):      # a kundli family section keeps a neutral dated line about a relative's baby (fixed shape)
        strings = [" ".join(x for x in re.split(r"(?<=[.!?])\s+", y) if not _rel_baby(x)) for y in strings]
    for rx, what, *hard in TYPE_GATES.get(t, []):
        for s in strings:
            for c in _clauses(s):
                if _DEFER.search(c):
                    continue
                out += [(what, m.group().lower()) for m in rx.finditer(c) if hard or not _excused(c[:m.start()], m.group())]
    return (out + (_shape_hits(strings) if t == "family" else []) + (_name_hits(strings) if t in ("intimacy", "affairs") else [])
            + (_kid_hits(strings) if t in ("children", "children_kundli", "children_forms") else []))


def is_marker(x):
    """A labelled monthly transit marker: a one-month 'watch' row whose label says 'marker' (= service.is_marker)."""
    return (x.get("kind") == "watch" and len(str(x.get("start", ""))) == 7 and x.get("start") == x.get("end")
            and "marker" in str(x.get("label", "")).lower())


PLANET_NAMES = "|".join(l for _, l, _, _ in vocab.PLANETS)
PLANET_ANY = "|".join(p for _, _, lat, _ in vocab.PLANETS for p in lat)     # English and Sanskrit names (vocab.py)
# Unknown birth time: the refused vocabulary comes from vocab.py (houses and Sanskrit lord names via house_refs; every
# varga but D1; every dasha system and level; chart-angle techniques), plus the few words vocab has no entity for.
TIME_BOUND_IDS = {"varga:" + d.lower() for d, _, _ in vocab.VARGAS if d != "D1"} | {
    "technique:" + vocab._slug(t) for t in ("Vimshottari dasha", "Antardasha (bhukti)", "Pratyantardasha", "Chara dasha",
                                            "Narayana dasha", "Yogini dasha", "Ashtottari dasha", "Kalachakra dasha",
                                            "Sookshma dasha", "Bhava chalit / cusps", "Karakamsa", "Arudha",
                                            "Moon chart (Chandra lagna)")}
TIME_BOUND_WORDS = re.compile(
    r"\w*das(?:h)?a\b|\w*ams(?:h)?a\b|\bbhavas?\b|\bkendras?\b|\b(?:tri)?konas?\b|\brising (?:sign|degree)\b|\bcusps?\b|\bD\d{1,2}\b|"
    rf"\b(?:{PLANET_NAMES}|period|sub|major|minor)(?:'s)?\s+(?:major |sub-|minor )?periods?\b|\b(?:major|sub|minor)-?periods?\b|"
    r"\bperiod lords?\b|\bantar\b|\byogini\b|\bperiods? of (?:the )?(?:" + PLANET_ANY + r")\b|\bbhukti\b|\bhouses?\b|\blords?\b|\bfrom the (?:Moon|Sun|lagna)\b", re.I)
MOON_WORDS = re.compile(r"\bMoon(?:'s)?\s+(?:sign|nakshatra|star)\b|\bbirth star\b|\bjanma\b|\bnakshatras?\b|\brash?is?\b"
                        r"|\bMoon (?:is )?in (?:" + "|".join(l for _, l, _ in vocab.SIGNS) + r")\b", re.I)
FACT_TIME_BOUND = re.compile(r"^F\.(asc|H\d+)\.|^F\.\w+\.(house|dispositor_house|owns|deg|d\d+\w*)$|^F\.yoga\.|^F\.moon\.elongation")


def _time_bound_terms(text):
    """Terms in text that need the birth time. Hyphens and spaces inside a compound are folded first ("maha-dasha",
    "antar dasha", "nav amsha") so spelling cannot slip past."""
    folded = re.sub(r"(?<=[a-z])-(?=(?:dash?a|ams?h?a|bhukti)\b)", "", text, flags=re.I)
    folded = re.sub(r"\b(maha|antar|pratyantar|nav|das|dash|vims|sapt)\s+(dash?a|ams?h?a)\b", r"\1\2", folded, flags=re.I)
    hits = {m.group().lower() for m in TIME_BOUND_WORDS.finditer(folded)}
    hits |= {f"house {n}" for n, _ in vocab.house_refs(folded)}
    hits |= {e for e in vocab.find_entities(folded) if e in TIME_BOUND_IDS or e.startswith("yoga:")}   # yogas: mostly lagna-based
    return hits


def unknown_time_errors(r):
    """Unknown birth time (owner decision 2026-11-14, any report type): no house, lagna, varga or dasha claims, no
    time-dependent fact ids or dasha event ids, the Moon's sign or star only when the writer marked the Moon stable
    across the day (birth.moon_stable; create_report verifies it), no date ranges, and a timeline of labelled monthly
    transit markers only. create_report runs it too."""
    errs = []
    free = _strings([v for k, v in r.items() if k not in ("appendix", "birth", "engine", "uncertainty", "dropped",
                                                          "prepared_on", "report_type")])
    if hits := sorted({h for s in free for h in _time_bound_terms(s)}):
        errs.append(f"birth time unknown: no house, lagna, varga or dasha claims ({', '.join(hits[:5])}); drop those "
                    "sections with the reason")
    units = [u for s in r.get("sections", []) for u in s.get("units", [])]
    if refs := sorted({x for u in units for x in u.get("fact_refs", []) if FACT_TIME_BOUND.search(x)}):
        errs.append(f"birth time unknown: time-dependent fact ids cannot be cited ({', '.join(refs[:5])})")
    if any(k.get("event_refs") for k in (r.get("summary") or {}).get("key_points", [])):
        errs.append("birth time unknown: event_refs depend on the birth time")
    moon = any(MOON_WORDS.search(s) or any(e.startswith("nakshatra:") for e in vocab.find_entities(s)) for s in free)
    if moon and not (r.get("birth") or {}).get("moon_stable"):
        errs.append("birth time unknown: the Moon's sign or nakshatra is used only when it is the same across the whole "
                    "birth day (set birth.moon_stable after checking; inputs.md)")
    errs += [f"birth time unknown: timeline row '{x.get('label')}' must be a one-month 'watch' row labelled as a "
             "transit marker" for x in r.get("timeline", []) if not is_marker(x)]
    if any(WIN.search(s) for s in free):
        errs.append("birth time unknown: no date ranges, only labelled monthly transit markers")
    return errs


def time_class(r):
    """exact | approximate | unknown, from the model's birth block (the engine gate uses the same unknown test)."""
    b = r.get("birth") or {}
    src, rel = str(b.get("time_source") or ""), str(b.get("time_reliability") or "")
    if UNKNOWN_TIME.search(src) or UNKNOWN_TIME.search(rel):
        return "unknown"
    return "exact" if re.search(r"\bexact\b", rel, re.I) and not re.search(r"\b(?:not|approx\w*)\b", rel, re.I) else "approximate"


ADULT_TYPES = ("intimacy", "affairs")
BIRTH_DATE_FORMATS = ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


def _date(x):
    """A date in one of BIRTH_DATE_FORMATS, else None. A numeric day/month date whose two parts are both 12 or less and differ
    (12/05/2008) is ambiguous between day-first and month-first, so it is not read."""
    x = str(x or "").strip()
    m = re.fullmatch(r"(\d{1,2})([/-])(\d{1,2})\2\d{4}", x)
    if m and int(m[1]) <= 12 and int(m[3]) <= 12 and m[1] != m[3] and int(m[1]) != int(m[3]):
        return None
    for f in BIRTH_DATE_FORMATS:
        try:
            return dt.datetime.strptime(x, f).date()
        except ValueError:
            pass
    return None


def adult_errors(r, birth_date=None):
    """The adult gate (owner decision 2026-11-19): built only when the birth date shows 18 or over on the report date. It fails
    closed: an unreadable or ambiguous date counts as not shown, and a report date in the future is refused. `birth_date` is the
    engine's own birth input (create_report); when given, the model's date must be the same day."""
    b, on = _date((r.get("birth") or {}).get("date")), _date(r.get("prepared_on"))
    if not b or not on:
        return ["adult gate: the birth date or the report date cannot be read (a numeric day/month date with both parts 12 or "
                "less is ambiguous), so 18 or over is not shown; no report is built"]
    if birth_date is not None and b != birth_date:
        return ["adult gate: the model's birth date is not the birth input's date; no report is built"]
    if on > dt.date.today():
        return ["adult gate: the report date is in the future; no report is built"]
    if on.year - b.year - ((on.month, on.day) < (b.month, b.day)) < 18:
        return ["adult gate: the birth date does not show 18 or over on the report date; no report is built"]
    return []


AFFAIRISH = re.compile(r"\baffairs?\b|extramarital|infidelit|unfaithful|cheat\w*|outside (?:a |the )?(?:committed relationship|marriage)|ties beyond", re.I)
NODEPTH_TYPES = ("children", "intimacy", "affairs", "jupiter-transit", "rahu-ketu", "varshaphal", "sade-sati", "mangal-dosha", "raj-yoga",
                 "match", "lal-kitab")   # no legacy models: depth is required


def needs_adult(r):
    """Intimacy and affairs, and a kundli with an intimacy section or affairs wording in any section."""
    t = r.get("report_type")
    return t in ADULT_TYPES or (t == "kundli" and any(s["id"] == "intimacy" or any(AFFAIRISH.search(x) for x in _strings(s))
                                                      for s in r.get("sections", [])))


def _agrees(text, need):
    """The Moderate rule of topic-relationships-marriage.md §9 and §10: only when the named factors and the navamsa agree."""
    return (all(w in text for w in need) and bool(re.search(r"navamsa|\bD-?9\b", text, re.I))
            and not re.search(r"disagree|differ|conflict|not agree|only one|one factor|contradict|mixed|unclear", text, re.I))


_NODE_COUNT = re.compile(r"\b(?:\d{1,2}(?:st|nd|rd|th)|fifth|seventh|ninth|trines?)\b", re.I)


def node_claims(strings, strict=False):
    """Clauses that state a node aspect. A clause that reports the dispute or attributes the view ('some writers hold') is
    not a claim; with strict (the rahu-ketu report, where the dispute has its labelled unit) an attributed view that names
    the houses still is."""
    return [c for s in strings for c in _clauses(_fold(s)) if NODE_ASPECT.search(c)
            and not (NODE_META.search(c) and not (strict and _NODE_COUNT.search(c)))]


def node_dispute(s, u):
    """The one place a node aspect may be stated: the labelled dispute unit in rahu-ketu 'axis' (owner decision 13)."""
    return (s["id"] == "axis" and u.get("claim_basis") == "DISPUTED" and u.get("claim_type") != "fact"
            and grades_of(u) <= {"Weak", "Contradictory"})


def transit_errors(r, t, strings):
    """Batch 4 rules (report-specs/<t>.md): the scope sentence; a window or pressure row names the running dasha;
    varshaphal creates no window and shows no Patyayini or exact day; rahu-ketu is never Strong and gives node aspects
    only as a labelled dispute; sade-sati keeps Kantaka and Ashtama Weak with the no-source sentence."""
    errs = [] if TRANSIT_SCOPE[t] in str(r.get("scope", "")) else [
        f"{t} report: the scope must carry the sentence '{TRANSIT_SCOPE[t]}' (report-specs/{t}.md)"]
    errs += [f"timeline row '{x.get('label')}': a {x['kind']} row must name the running dasha in its basis (a transit alone "
             "never gives a window)" for x in r.get("timeline", [])
             if x["kind"] in ("window", "pressure") and not DASHA_BASIS.search(str(x.get("basis", "")))]
    units = [(s, u) for s in r["sections"] for u in s.get("units", [])]
    grades = lambda u: set((u.get("confidence") or {}).values())
    kps = (r.get("summary") or {}).get("key_points", [])
    if t == "varshaphal":
        if any(x["kind"] in ("window", "pressure") for x in r.get("timeline", [])):
            errs.append("varshaphal report: Mudda seasons are chapter rows; no window or pressure rows (the year chart never creates one)")
        if hits := sorted({m.group() for s in strings for m in re.finditer(r"\bpatyayini\b|\bvarsha narayana\b", s, re.I)}):
            errs.append(f"varshaphal report: Mudda only (owner decision 12), no {', '.join(hits)}")
        days = sorted({m.group() for s in strings for m in DAY.finditer(s)}) + [x[k] for x in r.get("timeline", [])
                                                                               for k in ("start", "end") if len(x[k]) > 7]
        if days:
            errs.append(f"varshaphal report: Mudda boundaries to the month, no exact days ({', '.join(days[:4])})")
    if t == "rahu-ketu":
        if any("Strong" in grades(u) for _, u in units) or any(x.get("support") == "Strong" for x in r.get("ranking", [])) \
                or any(k.get("confidence") == "Strong" for k in kps):
            errs.append("rahu-ketu report: library support is thin, so nothing is graded Strong")
        for s, u in units:
            utext = _strings({k: u.get(k) for k in TEXT_KEYS + ("basis",)})
            if node_dispute(s, u) and (hits := [m.group() for x in utext for c in _clauses(x) for m in NODE_SETTLE.finditer(c)
                                                 if not _excused(c[:m.start()], m.group())]):
                errs.append(f"[axis] '{u['theme'][:50]}': the node aspect dispute shows both sides and settles neither "
                            f"({', '.join(hits[:3])}; owner decision 13)")
            elif not node_dispute(s, u) and node_claims(utext, strict=True):
                errs.append(f"[{s['id']}] '{u['theme'][:50]}': node aspects only as a labelled dispute in 'axis' "
                            "(claim_basis DISPUTED, graded Weak or Contradictory; owner decision 13)")
            if s["id"] == "axis" and grades(u) & {"Moderate", "Strong"} and not DASHA_BASIS.search(str(u.get("basis", ""))):
                errs.append(f"[axis] '{u['theme'][:50]}': an axis line is Moderate only when the running dasha agrees "
                            "(name it in basis); otherwise Weak")
        rows = _strings([r.get(k) for k in ("summary", "ranking", "timeline", "watch_list", "practical_summary")])
        if node_claims(rows, strict=True):
            errs.append("rahu-ketu report: node aspects never in the summary, ranking, timeline, watch list or practical lines")
    if t == "sade-sati":
        sec = next((s for s in r["sections"] if s["id"] == "kantaka"), None)
        if sec and KANTAKA_NOTE not in str(sec.get("text", "")):
            errs.append(f"sade-sati 'kantaka' section needs the sentence '{KANTAKA_NOTE}' in its text (owner decision 4)")
        errs += [f"[{s['id']}] '{u['theme'][:50]}': Kantaka and Ashtama Shani are graded Weak on every line (owner decision 4)"
                 for s, u in units if KANTAKA.search(" ".join(_strings({k: u.get(k) for k in TEXT_KEYS + ("basis",)})))
                 and grades(u) - {"Weak"}]
        errs += [f"'{x.get('item', x.get('text', ''))[:40]}': Kantaka and Ashtama Shani are graded Weak (owner decision 4)"
                 for x in r.get("ranking", []) + kps if KANTAKA.search(" ".join(_strings(x)))
                 and (x.get("support") or x.get("confidence")) != "Weak"]
        if not sec and any(KANTAKA.search(x) for x in strings) and "kantaka" not in {d["item"] for d in r.get("dropped", [])}:
            errs.append("sade-sati report: Kantaka or Ashtama named without its 'kantaka' section and the no-source sentence")
    return errs


def yoga_errors(r, t, strings, fact_ids=None):
    """Batch 5 (report-specs/<t>.md). mangal-dosha: the scope sentence; exactly one unit per engine rule, in order, each with
    its base rate and its cancellations; no Strong; no timeline and no dates. raj-yoga: the scope sentence; a window row names
    the running dasha; the base rate in words; no Strong; a dual-lordship line is a labelled dispute showing both readings."""
    errs = [] if YOGA_SCOPE[t] in str(r.get("scope", "")) else [
        f"{t} report: the scope must carry the sentence '{YOGA_SCOPE[t]}' (report-specs/{t}.md)"]
    units = [(s, u) for s in r["sections"] for u in s.get("units", [])]
    grades = lambda u: set((u.get("confidence") or {}).values())
    kps = (r.get("summary") or {}).get("key_points", [])
    if any("Strong" in grades(u) for _, u in units) or any(x.get("support") == "Strong" for x in r.get("ranking", [])) \
            or any(k.get("confidence") == "Strong" for k in kps):
        errs.append(f"{t} report: nothing is graded Strong (a convention or a common configuration, never a verdict)")
    if t == "mangal-dosha":
        if r.get("timeline"):
            errs.append("mangal-dosha report: no timeline rows (the dosha is read from the birth chart, not timed)")
        if hits := sorted({m.group() for s in strings for m in DATEISH.finditer(s)}):
            errs.append(f"mangal-dosha report: no years, months or dates in the text ({', '.join(hits[:4])})")
        sec = next((s for s in r["sections"] if s["id"] == "rules"), None)
        if sec:
            errs += mangal_rule_errors(sec.get("units", []), "mangal-dosha 'rules'", "rules")
    if t == "raj-yoga":
        errs += [f"timeline row '{x.get('label')}': a {x['kind']} row must name the running dasha in its basis (a yoga acts "
                 "only in its planets' periods)" for x in r.get("timeline", [])
                 if x["kind"] in ("window", "pressure") and not DASHA_BASIS.search(str(x.get("basis", "")))]
        sec = next((s for s in r["sections"] if s["id"] == "lines"), None)
        if sec and not BASE_RATE_RX.search(str(sec.get("text", ""))):
            errs.append("raj-yoga 'lines': the section text states the base rate in words ('about 2 in 3 charts') or "
                        "'base rate not checked'")
        for s, u in units:
            dual = s["id"] == "lines" and dual_lords(u, fact_ids)
            refs = " ".join(map(str, u.get("rule_refs", [])))
            if dual and (u.get("claim_basis") != "DISPUTED" or not grades(u) <= {"Weak", "Contradictory"}
                         or not (re.search(r"\bBPHS\b", refs) and re.search(r"\bPDK?\b", refs))):
                errs.append(f"[lines] '{u['theme'][:50]}': a planet that also owns a 6th, 8th or 12th is a labelled dispute showing both "
                            "readings (claim_basis DISPUTED, graded Weak or Contradictory, rule_refs naming BPHS and PD; owner decision 14)")
    return errs


def mangal_rule_errors(us, where, sid):
    """One unit per engine Mangal rule, in order, each with its base rate in words and its cancellations (batch 5; batch 6
    runs it once per person)."""
    errs, txt = [], lambda u: " ".join(str(u.get(k, "")) for k in TEXT_KEYS + ("basis",))
    found = [[n for n, rx in MANGAL_RULES if rx.search(u.get("theme", ""))] for u in us]
    if found != [[n] for n, _ in MANGAL_RULES]:
        errs.append(f"{where}: exactly one unit per engine rule, in this order: classical (BPHS), popular, "
                    "Phaladeepika, HJH2, each named in its theme")
    for u in us:
        if not BASE_RATE_RX.search(txt(u)):
            errs.append(f"[{sid}] '{u['theme'][:50]}': state the base rate in words ('about 88 in 100 random charts') "
                        "or 'base rate not checked'")
        if not CANCEL_RX.search(str(u.get("counter", ""))):
            errs.append(f"[{sid}] '{u['theme'][:50]}': list the cancellations (or 'no cancellation') in the counter line")
    return errs


TIME_RANK = {"exact": 0, "approximate": 1, "unknown": 2}


def match_errors(r, strings):
    """Batch 6 (report-specs/match.md): consent; Person A and Person B; the less certain birth time decides; four kootas in
    order with their exceptions, the role sentence once and the no-total sentence; Mars per person under the four rules and
    the two-chart cancellation with its source or 'not checked'; nothing Strong; no timeline and no dates."""
    errs, b = [], r.get("birth") or {}
    if MATCH_CONSENT not in str(r.get("consent", "")):
        errs.append(f"match report: no report without consent: 'consent' must carry the sentence '{MATCH_CONSENT}' (owner decision 10)")
    ps = b.get("persons") or []
    if tuple(p.get("label") for p in ps) != PERSONS:
        errs.append("match report: birth.persons holds exactly two people, labelled 'Person A' and 'Person B' in that order (owner decision 10)")
    if r.get("prepared_for") != " and ".join(PERSONS):
        errs.append("match report: prepared_for is 'Person A and Person B' (neutral names, owner decision 10)")
    one = [time_class({"birth": p}) for p in ps]
    if one and TIME_RANK[time_class(r)] < max(TIME_RANK[x] for x in one):
        errs.append("match report: birth.time_reliability is the less certain of the two birth times (it decides what is said for both)")
    if b.get("moon_stable") and not all(p.get("moon_stable") for p, x in zip(ps, one) if x == "unknown"):
        errs.append("match report: birth.moon_stable needs moon_stable on each person whose birth time is unknown")
    units = [(s, u) for s in r["sections"] for u in s.get("units", [])]
    if any(grades_of(u) & {"Strong"} for _, u in units) or any(x.get("support") == "Strong" for x in r.get("ranking", [])) \
            or any(k.get("confidence") == "Strong" for k in (r.get("summary") or {}).get("key_points", [])):
        errs.append("match report: nothing is graded Strong (fit is a set of tendencies, never a verdict)")
    if r.get("timeline"):
        errs.append("match report: no timeline rows (the match is read from the two birth charts, not timed)")
    if hits := sorted({m.group() for s in strings for m in DATEISH.finditer(s)}):
        errs.append(f"match report: no years, months or dates in the text ({', '.join(hits[:4])})")
    if sum(x.count(MATCH_ROLES) for x in strings) > 1:
        errs.append("match report: the classical roles are labelled once (the role sentence appears once)")
    if hits := sorted({m.group().lower() for x in strings for m in ROLE_WORDS.finditer(x.replace(MATCH_ROLES, ""))}):
        errs.append(f"match report: Person A and Person B everywhere; role words only in the one role sentence ({', '.join(hits[:4])})")
    # shortcut: the intimacy name helper (a capitalised word that is not a planet, sign, nakshatra or school) less the match
    # sources' own names; a lower-case or sentence-initial name with no possessive or verb after it still passes
    if names := sorted({w for _, w in _name_hits(strings)} - MATCH_NAME_OK):
        errs.append(f"match report: only Person A and Person B name the two people (owner decision 10): {', '.join(names[:4])}")
    sec = {s["id"]: s for s in r["sections"]}
    if "kootas" in sec:
        k = sec["kootas"]
        errs += [f"match 'kootas': the section text needs the sentence '{x}'" for x in (MATCH_ROLES, MATCH_NOSUM)
                 if x not in str(k.get("text", ""))]
        us = k.get("units", [])
        if [[n for n, rx in KOOTAS if rx.search(u.get("theme", ""))] for u in us] != [[n] for n, _ in KOOTAS]:
            errs.append("match 'kootas': exactly one unit per computed koota, in this order: tara, bhakoot, graha maitri, nadi")
        errs += [f"[kootas] '{u['theme'][:50]}': list its exception conditions (or 'no exception listed') in the counter line"
                 for u in us if not EXCEPT_RX.search(str(u.get("counter", "")))]
    if "mangal" in sec:
        us = sec["mangal"].get("units", [])
        for p in PERSONS:
            errs += mangal_rule_errors([u for u in us if u.get("theme", "").startswith(p)], f"match 'mangal' ({p})", "mangal")
        both = [u for u in us if not u.get("theme", "").startswith(PERSONS)]
        txt = lambda u: " ".join(_strings({k: u.get(k) for k in TEXT_KEYS + ("basis", "rule_refs")}))
        if len(both) != 1 or not re.search(r"\bboth\b", both[0].get("theme", ""), re.I) or not CANCEL_RX.search(txt(both[0])) \
                or not (re.search(r"\bBPHS\b", txt(both[0])) or "not checked" in txt(both[0])):
            errs.append("match 'mangal': one closing unit on both charts shows the 'both have it' cancellation with its source "
                        "(BPHS) or says 'not checked'")
    return errs


def lk_errors(r, strings):
    """Batch 6 (report-specs/lal-kitab.md): the scope sentence; Lal Kitab sections and units only (Parashari stays out);
    no timeline; an unknown birth time gives no report (every section rests on the houses); the rin section names pitri rin
    with its note, never above Weak."""
    errs = [] if LK_SCOPE in str(r.get("scope", "")) else [
        f"lal-kitab report: the scope must carry the sentence '{LK_SCOPE}' (report-specs/lal-kitab.md)"]
    if bad := [s["id"] for s in r["sections"] if s["id"] not in LK_SECTIONS]:
        errs.append(f"lal-kitab report: sections are {', '.join(LK_SECTIONS)} only (not {', '.join(bad)}); Parashari readings "
                    "have their own reports")
    errs += [f"[{s['id']}] '{u['theme'][:50]}': every unit in this report is a Lal Kitab unit (system lal_kitab); Parashari "
             "and Lal Kitab stay separate" for s in r["sections"] for u in s.get("units", []) if u.get("system") != "lal_kitab"]
    if r.get("timeline"):
        errs.append("lal-kitab report: no timeline rows (no dasha is used; the Lal Kitab timing rules are read in words)")
    if time_class(r) == "unknown":
        errs.append("lal-kitab report: every section rests on the Lal Kitab houses, counted from the lagna, so an unknown "
                    "birth time gives no Lal Kitab report; ask for the time")
    rin = next((s for s in r["sections"] if s["id"] == "lk-rin"), None)
    if rin:
        if RIN_NOTE not in str(rin.get("text", "")):
            errs.append(f"lal-kitab 'lk-rin': the section text needs the sentence '{RIN_NOTE}'")
        if not any(PITRI.search(u.get("theme", "")) for u in rin.get("units", [])):
            errs.append("lal-kitab 'lk-rin': one unit names pitri rin in its theme (Pitra Dosha is read here, owner decision 2)")
        errs += [f"[lk-rin] '{u['theme'][:50]}': a debt signature is graded Weak, Contradictory or Unknown (no debt is named)"
                 for u in rin.get("units", []) if grades_of(u) - {"Weak", "Contradictory", "Unknown"}]
    return errs


def kaal_errors(r):
    """Batch 5 (kundli.md §2): a kundli unit that names Kaal Sarp says its modern status plainly, names the strict form and
    the axis, and is graded Weak; the pattern never appears in the summary, ranking, timeline, watch list or practical lines."""
    errs = []
    for s in r["sections"]:
        for u in s.get("units", []):
            text = " ".join(str(u.get(k, "")) for k in TEXT_KEYS + ("basis",))
            if not KAAL.search(text):
                continue
            name = f"[{s['id']}] '{u['theme'][:50]}'"
            if KAAL_NOTE not in text:
                errs.append(f"{name}: a Kaal Sarp unit needs the sentence '{KAAL_NOTE}' (owner decision 9, kundli.md §2)")
            if not (re.search(r"\bstrict\b", text, re.I) and re.search(r"\baxis\b", text, re.I)):
                errs.append(f"{name}: a Kaal Sarp unit names the strict form and the Rahu-Ketu axis houses")
            if grades_of(u) - {"Weak"}:          # a calculated fact too: the pattern's effect is not agreed
                errs.append(f"{name}: Kaal Sarp is graded Weak on every line (no agreed effect)")
    rows = _strings([r.get(k) for k in ("summary", "ranking", "timeline", "watch_list", "practical_summary")])
    if any(KAAL.search(x) for x in rows):
        errs.append("kundli: Kaal Sarp stays in its one foundation unit, never in the summary, ranking, timeline, watch list or practical lines")
    return errs


def grades_of(u):
    return set((u.get("confidence") or {}).values())


def spec_checks(r, fact_ids=None):
    """Errors for a model written to a T10 spec (it carries `depth`); legacy models (no depth) are left alone."""
    t, depth = r.get("report_type"), r.get("depth")
    if t not in SPEC_SECTIONS:
        return ([f"depth is only for spec reports ({', '.join(SPEC_SECTIONS)})"] if depth else []), []
    pre = []
    if not depth and t in NODEPTH_TYPES:       # no legacy models: every gate runs, and the missing depth is an error
        pre, depth = [f"{t} report needs depth: standard (it has no legacy form, so no gate may be skipped)"], "standard"
    if not depth:
        return ([], ["written before the T10 spec (no depth): spec checks skipped"]) if t != "kundli" else (
            ["a kundli report needs depth (standard or full)"], [])
    if depth not in SPEC_SECTIONS[t]:
        return [f"{t} has no depth '{depth}' (only {', '.join(SPEC_SECTIONS[t])})"], []
    errs = pre + [f"spec report needs '{k}' (the frame, report-specs/{t}.md)" for k in ("scope", "confidence_note", "next_step")
                  if not r.get(k)]
    if not (r.get("birth") or {}).get("time_reliability"):
        errs.append("spec report needs birth.time_reliability (exact, approximate or unknown): it decides what may be dated")
    ids = [s["id"] for s in r["sections"]]
    dropped = {d["item"] for d in r.get("dropped", [])}
    if len(ids) != len(set(ids)):
        errs.append("section ids repeat: one section per id (one timing framework: a single 'windows')")
    want = SPEC_SECTIONS[t][depth]
    errs += [f"section '{x}' is missing: write it or list it in dropped with the reason" for x in want
             if x not in ids and x not in dropped]
    unknown = time_class(r) == "unknown"
    if t != "lal-kitab" and (bad := [x for x in ids if x not in want and not (unknown and x == "note")]):
        errs.append(f"section ids {', '.join(bad)} are not in the {t} spec (report-specs/{t}.md: {', '.join(want)})")
    if unknown and (bad := [x for x in UNKNOWN_DROP.get(t, ()) if x in ids]):
        errs.append(f"unknown birth time: report-specs/{t}.md drops {', '.join(bad)} (list it in dropped with the reason)")
    order = [x for x in ids if x in want]
    if order != [x for x in want if x in order]:
        errs.append(f"spec sections out of order: {order}, spec order {want}")
    if not r.get("ranking") and "ranking" not in dropped:
        errs.append("the ranking table is missing: give ranking rows or list 'ranking' in dropped with the reason")
    if any(x["kind"] in ("window", "pressure") for x in r.get("timeline", [])) and "windows" not in ids:
        errs.append("timeline windows need the one 'windows' section that the other sections point to")
    for s in r["sections"]:
        for u in s.get("units", []):
            name = f"[{s['id']}] '{u['theme'][:50]}'"
            text = " ".join(str(u.get(k, "")) for k in TEXT_KEYS)
            if not u.get("claim_type"):
                errs.append(f"{name} has no claim_type: its fact or interpretation label cannot be shown")
            if u.get("claim_type") != "fact" and not any((u.get("confidence") or {}).values()):
                errs.append(f"{name} has no grade word (confidence)")
            if LOOKS.search(text) or any(AGE.search(x) and PARTNER.search(x) for x in re.split(r"(?<=[.!?;])\s+", text)):
                c = u.get("confidence") or {}
                home = "appearance" if t == "self" else "partner"      # the one section where looks may be described
                if s["id"] != home:
                    errs.append(f"{name} describes looks or age outside the '{home}' section")
                elif c.get("manifestation", c.get("event")) not in ("Weak", "Unknown"):
                    errs.append(f"{name} describes looks or age: its form must be graded Weak or Unknown")
            if t == "self" and s["id"] == "appearance" and any(c not in ("Weak", "Unknown") for c in (u.get("confidence") or {}).values()):
                errs.append(f"{name} in 'appearance' must be graded Weak or Unknown on every line")
    if t == "self":
        app = next((s for s in r["sections"] if s["id"] == "appearance"), None)
        if app and SELF_APPEARANCE_CAVEAT not in str(app.get("text", "")):
            errs.append("self 'appearance' section needs its caveat sentence in the section text (report-specs/self.md §1)")
    if needs_adult(r):
        errs += adult_errors(r)
    if t in ("children", "affairs") and r.get("timeline"):
        errs.append(f"{t} report: no timeline rows are given (no windows, no periods, no 'when'; report-specs/{t}.md)")
    if t == "intimacy" and any(x["kind"] != "chapter" for x in r.get("timeline", [])):
        errs.append("intimacy report: the timeline carries chapter rows only (no windows or pressure rows; report-specs/intimacy.md)")
    if t == "intimacy" and r.get("timeline") and "phases" not in ids:
        errs.append("intimacy report: a timeline row is given only when `phases` is asked and written (report-specs/intimacy.md)")
    if t in ("children", "affairs") and (r.get("appendix") or {}).get("periods"):
        errs.append(f"{t} report: no periods table in the appendix (no periods are given; report-specs/{t}.md)")
    if t in ("intimacy", "affairs"):          # grades: never Strong; Moderate only when the named factors and the navamsa agree
        need = ("12th", "Venus") if t == "intimacy" else ("7th", "Venus")
        for s in r["sections"]:
            for u in s.get("units", []):
                g = set((u.get("confidence") or {}).values())
                if "Strong" in g or ("Moderate" in g and not _agrees(u.get("basis", ""), need)):
                    errs.append(f"[{s['id']}] '{u['theme'][:50]}': {t} is graded Weak on one factor and Moderate only when {' and '.join(need)} "
                                "and the navamsa agree (named in basis); never Strong")
        for x in r.get("ranking", []):
            if x.get("support") == "Strong" or (x.get("support") == "Moderate" and not _agrees(x.get("why", ""), need)):
                errs.append(f"ranking row '{x['item'][:40]}': {t} is Moderate only when {' and '.join(need)} and the navamsa agree (named in why); never Strong")
        kps = (r.get("summary") or {}).get("key_points", [])
        if any(k.get("confidence") == "Strong" for k in kps):
            errs.append(f"{t} report: no key point is graded Strong")
        grades = ([c for s in r["sections"] for u in s.get("units", []) for c in (u.get("confidence") or {}).values()]
                  + [x.get("support") for x in r.get("ranking", [])] + [k.get("confidence") for k in kps])
        if "Unknown" in grades and time_class(r) == "exact":
            errs.append(f"{t} report: Unknown is for an approximate or unknown birth time only; grade Weak or Moderate")
    if t != "lal-kitab" and (r.get("remedies") or any(u.get("system") == "lal_kitab" for s in r["sections"] for u in s.get("units", []))):
        errs.append("Lal Kitab stays out of these Parashari reports (remedies section included); it has its own report")
    for s in r["sections"]:
        if s["id"] == "remedies":
            errs += [f"[remedies] '{u['theme'][:50]}' has no 'no efficacy established' line (remedy-safety.md)"
                     for u in s.get("units", []) if "no efficacy" not in " ".join(str(u.get(k, "")) for k in TEXT_KEYS).lower()]
    if t == "kundli" and r.get("ranking"):     # the snapshot: one row per life-area section present
        rows = {x["item"].lower() for x in r["ranking"]}
        errs += [f"snapshot has no row for '{s['title']}' (one row per life area)" for s in r["sections"]
                 if s["id"] not in ("foundation", "windows", "remedies") and s["title"].lower() not in rows]
    for x in r.get("timeline", []):
        if x["kind"] in ("window", "pressure") and not x.get("confidence"):
            errs.append(f"timeline row '{x['label']}' has no grade word (confidence)")
    client = [v for k, v in r.items() if k not in ("appendix", "birth", "engine", "prepared_on", "period")]
    strings = _strings(client)
    if hits := sorted({m.group() for s in strings for m in PERCENT.finditer(s)}):
        errs.append(f"percentages in the report ({', '.join(hits)}): grade words only")
    if t in TRANSIT_TYPES:
        errs += transit_errors(r, t, strings)
    if t != "lal-kitab":         # README §5: Lal Kitab words, sources included; a follow-up may point at the lal-kitab report
        lk = copy.deepcopy({k: v for k, v in r.items() if k not in ("birth", "engine", "prepared_on", "period")})
        (lk.get("next_step") or {}).pop("follow_ups", None)
        if hits := sorted({m.group() for x in _strings(lk) for m in LK_TERMS.finditer(x)}):
            errs.append(f"Lal Kitab stays out of these Parashari reports: no Lal Kitab names, sources, houses, debts or tables "
                        f"({', '.join(hits[:4])}); it has its own report (README §5)")
    rest = copy.deepcopy(client)                 # node aspects: never as a fact, in any field of any type (owner decision 13)
    for x in rest:
        for s in (x if isinstance(x, list) else []):
            if isinstance(s, dict) and t == "rahu-ketu" and "units" in s:
                s["units"] = [u for u in s["units"] if not node_dispute(s, u)]
    if claims := node_claims(_strings(rest), strict=t == "rahu-ketu"):
        errs.append(f"{t} report: node aspects only as one side of the labelled dispute in the rahu-ketu 'axis' unit, never as "
                    f"a fact ('{claims[0].strip()[:60]}'; owner decision 13)")
    if t in YOGA_TYPES:
        errs += yoga_errors(r, t, strings, fact_ids)
    if t == "kundli":
        errs += kaal_errors(r)
    if t == "match":
        errs += match_errors(r, strings)
    if t == "lal-kitab":
        errs += lk_errors(r, strings)
    nontl = _strings([v for k, v in r.items() if k not in ("appendix", "birth", "engine", "prepared_on", "period", "timeline")])
    if t == "intimacy" and (hits := sorted({m.group() for s in nontl for m in DATEISH.finditer(s)})):
        errs.append(f"intimacy report: no years, months or dates in the text ({', '.join(hits[:4])}): no dated windows (chapter rows keep their own dates)")
    if t in ("children", "affairs") and (hits := sorted({m.group() for s in strings for m in DATEISH.finditer(s)})):
        errs.append(f"{t} report: no years, months or dates anywhere ({', '.join(hits[:4])}): no windows or periods are given")
    if hits := sorted({m.group().lower() for s in _strings(r) for m in ORGANS.finditer(s)}):
        errs.append(f"organ words in the report ({', '.join(hits)}): body parts are not read in this practice")
    # looks wording in every client string outside the one section that may carry it (self: 'appearance'; kundli and
    # relationship: 'partner'); a ranking row about looks must be Weak or Unknown in self
    home = "appearance" if t == "self" else "partner"
    outside = [s for s in r["sections"] if s["id"] != home]
    loose = [{k: s.get(k) for k in ("title", "intro", "text")} for s in outside]
    rows = [x for x in r.get("ranking", []) if not (t == "self" and x.get("support") in ("Weak", "Unknown"))]
    loose_strings = _strings([loose, rows] + [r.get(k) for k in ("title", "subtitle", "scope", "summary", "confidence_note",
                                                                 "practical_summary", "watch_list", "timeline", "uncertainty")])   # `dropped` names what is withheld
    unit_strings = _strings([[{k: u.get(k) for k in TEXT_KEYS} for u in s.get("units", [])] for s in outside]) if t == "self" else []
    for x in loose_strings:
        for sent in re.split(r"(?<=[.!?;])\s+", x):
            if LOOKS_TOPIC.search(sent) or (AGE.search(sent) and PARTNER.search(sent)):
                errs.append(f"looks or age wording outside the '{home}' section: '{sent[:70]}'")
    for x in loose_strings + unit_strings if t == "self" else []:
        if SELF_LOOKS.search(x) or LOOKS_TOPIC.search(x):
            errs.append(f"looks wording outside the 'appearance' section: '{x[:70]}'")
    forbid_text = _strings(_no_ids({k: v for k, v in r.items() if k not in ("birth", "engine", "prepared_on", "period")}))
    if bad := sorted({m.group().lower() for x in forbid_text for m in _FORBID.finditer(x)}
                     | {w for x in forbid_text for w in medical_words.words_in(x)}):      # list, Devanagari, typos, homoglyphs
        errs += [FORBID_MSG, f"words found: {', '.join(bad[:8])}"]
    method = _strings((r.get("appendix") or {}).get("method")) if t in NODEPTH_TYPES else []   # the appendix method is printed
    hits = gate_hits(t, strings + method)
    if t == "self":
        hits += gate_hits("self_outside", loose_strings + unit_strings)
    if t == "kundli":       # the same wording is refused in a kundli section as in the report of its own type
        for sec in r["sections"]:
            for g in KUNDLI_GATES.get(sec["id"], ()):
                hits += gate_hits(g, _strings(sec))
            if sec["id"] == "self":
                hits += gate_hits("self_outside", _strings(sec))
            if sec["id"] == "self" and any(SELF_LOOKS.search(x) for x in _strings(sec)):
                errs.append("kundli 'self' describes looks: looks belong in the 'partner' section for another person only")
        for sec in r["sections"]:      # a unit that names Kaal Sarp or Mangal dosha gets that type's wording gates
            for u in sec.get("units", []):
                us = _strings(u)
                if any(KAAL.search(x) for x in us):
                    hits += gate_hits("kaal_sarp", us)
                if any(MANGAL_NAME.search(x) for x in us):
                    hits += gate_hits("mangal-dosha", us)
        rows = _strings([r.get(k) for k in ("summary", "timeline", "watch_list", "ranking", "practical_summary")])
        for g in ("family", "challenges", "spirituality", "children_forms", "intimacy_forms", "affairs_forms"):
            hits += gate_hits(g, rows)
    if t == "family":       # a section about one relative: a harm word is refused there, dated or not
        for sec in r["sections"]:
            if sec["id"] in ("mother", "father", "siblings"):
                hits += gate_hits("family_sec", _strings(sec))
    if t in ("family", "kundli"):
        # a dated row or line that names a relative is refused only when it also carries a harm word (or is a pressure row)
        dated = ([(f"{x['label']} {x.get('basis', '')}", True, x["kind"] == "pressure") for x in r.get("timeline", [])]
                 + [(" ".join(_strings(x)), bool(DATEISH.search(" ".join(_strings(x)))), False) for x in r.get("watch_list", [])]
                 + [(" ".join(_strings(x)), True, False) for x in r.get("ranking", []) if x.get("window")]
                 + [(x, bool(DATEISH.search(x)), False) for x in _strings(r.get("practical_summary", []))]
                 + [(" ".join(_strings(x)), bool(x.get("window")), False) for x in (r.get("summary") or {}).get("key_points", [])])
        for x, is_dated, hard in dated:
            if is_dated and PARSIB.search(x) and (hard or gate_hits("family_sec", [x])):
                errs.append(f"{t}: a dated row or line names a parent or sibling with a harm word ('{x[:60]}'): "
                            "neutral dated forecasts are fine, anything about their health, danger, loss or death is not")
    for what in sorted({w for w, _ in hits}):
        words = sorted({h for w, h in hits if w == what})
        errs.append(f"{t} report: {what} are not allowed ({', '.join(words[:4])}; report-specs/{t}.md caveats)"
                    + (_ALLOWHINT if what == _ALLOWWHAT else ""))
    for s in strings:
        for sent in re.split(r"(?<=[.!?;])\s+", s):
            if AFFAIR.search(sent) and OTHER.search(sent) and not OWN.search(sent):
                errs.append(f"fidelity is read from the person's own chart only, never about another person: '{sent[:70]}'")
    tc = time_class(r)
    if tc != "exact":
        days = sorted({m.group() for s in strings for m in DAY.finditer(s)})
        days += [x["start"] for x in r.get("timeline", []) if len(x["start"]) > 7] + [x["end"] for x in r.get("timeline", []) if len(x["end"]) > 7]
        if days:
            errs.append(f"birth time is {tc}: no exact days ({', '.join(days[:4])}); months at most")
    if tc == "approximate":
        for s in r["sections"]:
            errs += [f"[{s['id']}] '{u['theme'][:50]}' rests on a time-dependent factor but has no sensitivity "
                     "(get_birth_time_sensitivity)" for u in s.get("units", [])
                     if TIME_DEP.search(u.get("basis", "")) and not u.get("sensitivity")]
    if tc == "unknown":
        errs += unknown_time_errors(r)
    srcs = (r.get("appendix") or {}).get("sources") or []
    if not srcs:
        errs.append("appendix.sources is empty: name the books (id, author, title, page)")
    cat = _catalog()
    for x in srcs:
        book = (re.match(r"[A-Z][A-Z0-9]+\b", x) or [""])[0]
        if not book or re.search(r"\.md\b|\bskill\b|\breferences/", x):
            errs.append(f"source '{x[:60]}' is not a book: start with the catalog id (e.g. 'BPHS ...')")
        elif cat is not None and book not in cat:
            errs.append(f"source '{x[:60]}': '{book}' is not a catalog book")
    return errs, []


def ledger(r):
    """Evidence ledger (frame item 9): unit themes by Confirmed / Inferred / Hypothesis, from each unit's claim_type."""
    out = {"Confirmed": [], "Inferred": [], "Hypothesis": []}
    for s in r["sections"]:
        for u in s.get("units", []):
            if u.get("claim_type"):
                out[LEDGER[u["claim_type"]]].append(u["theme"])
    return out


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


def event_index(facts):
    """Stable ids for the engine events a key point can cite (#46) → the dates that anchor them.
    DSH.<MD> / DSH.<MD>-<AD> (start and end), ING.<planet>.<date>, CON.<transit>.<natal>.<aspect>.<date>."""
    ev = {}
    for md in facts.get("vimshottari", []):
        ev[f"DSH.{md['lord']}"] = [_d(md["start"]), _d(md["end"])]
        for ad in md.get("sub", []):
            ev[f"DSH.{md['lord']}-{ad['lord']}"] = [_d(ad["start"]), _d(ad["end"])]
    for x in facts.get("ingresses", []):
        ev[f"ING.{x['planet']}.{x['date'][:10]}"] = [_d(x["date"])]
    for x in facts.get("slow_contacts", []):
        ev[f"CON.{x['transit']}.{x['natal']}.{x.get('aspect', 'contact')}.{x['date'][:10]}"] = [_d(x["date"])]
    return ev


def _key_point_refs(r, facts, tol):
    """Key points that cite engine events are checked exactly: each event_ref must exist and fall inside the key point's
    window (± tol). Returns (errors, windows already settled, so proximity is not used for them)."""
    ev, errs, settled = event_index(facts), [], set()
    for k in r["summary"].get("key_points", []):
        refs = k.get("event_refs") or []
        if not refs:
            continue
        unknown = [x for x in refs if x not in ev]
        if unknown:
            errs.append(f"key point cites unknown engine event(s): {', '.join(unknown)}")
        if not k.get("window"):
            errs.append(f"key point cites engine events ({', '.join(refs)}) but has no window")
            continue
        # Only the key point's own `window` is settled by its refs (council RC-02): other dates in its text are still
        # grounded by proximity. A ref may fall in any of the window's ranges (RC-03); one message per ref.
        ctx = f"{k.get('text', '')} {k.get('window', '')}"
        own = [(lab, s, e, ctx) for lab, s, e, _ in
               _windows({"timeline": [], "summary": {"headline": "", "key_points": [{"text": "", "window": k["window"]}]},
                         "sections": []})]
        settled |= set(own)
        off = [x for x in refs if x in ev and not any(s - tol <= a <= e + tol for _, s, e, _ in own for a in ev[x])]
        if off:
            errs.append(f"window '{k['window']}' does not contain the engine event(s) it cites: {', '.join(off)}")
    return errs, settled


def grounding(r, facts):
    """Every window must lie near a dasha/AD boundary, ingress or exact contact of a planet its own text names (calc.json).
    A key point with event_refs is checked exactly against those events instead (#46)."""
    first = _d(facts["meta"]["transit_date"])
    last = max([_d(x["date"]) for x in facts.get("ingresses", []) + facts.get("slow_contacts", [])], default=first)
    if facts["meta"].get("months"):         # calc.json does not store `months`; its last event bounds the horizon otherwise
        last = max(last, first + dt.timedelta(days=30.44 * facts["meta"]["months"]))
    tol = dt.timedelta(days=TOLERANCE_DAYS)
    errs, warns, seen = [], [], set()
    ref_errs, seen = _key_point_refs(r, facts, tol)
    errs += ref_errs
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
        return [medical_words.norm(x)]   # NFKC, no zero-width or other format characters: every gate reads clean text
    if isinstance(x, dict):
        return [s for v in x.values() for s in _strings(v)]
    if isinstance(x, list):
        return [s for v in x for s in _strings(v)]
    return []


def month_name(s):
    """'2026-05' -> 'May 2026'; anything else (a day, a word) is left as written."""
    m = re.fullmatch(r"(\d{4})-(0[1-9]|1[0-2])", str(s))
    return f"{calendar.month_name[int(m.group(2))]} {m.group(1)}" if m else s


def used_marks(r):
    """Which claim types, grades, birth-time states and bar kinds the report really uses: the legend lists only those."""
    units = [u for s in r["sections"] for u in s.get("units", [])]
    kp, tl = r["summary"]["key_points"], r.get("timeline", [])
    grades = {k.get("confidence") for k in kp} | {x.get("support") for x in r.get("ranking", [])} | {t.get("confidence") for t in tl}
    grades |= {v for u in units for v in (u.get("confidence") or {}).values()}
    return dict(claim={u.get("claim_type") for u in units}, grade=grades, sens={sens_state(x) for x in units + kp + tl} - {None},
                line={t["kind"] for t in tl})


def html_of(r):
    try:
        import jinja2
    except ImportError:
        raise RuntimeError("render needs jinja2 (pip install jinja2); the JSON itself was valid")   # not sys.exit: callers are servers (council R3 M4)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ASSETS), autoescape=True)
    env.globals.update(TEMPLATE_GLOBALS)
    env.filters["mon"] = month_name
    bases = [dict(theme=u["theme"], basis=u["basis"]) for s in r["sections"] for u in s.get("units", []) if u.get("basis")]
    style = r.get("chart_style", "north")
    chart = None if r["report_type"] == "match" else chart_svg.chart((r.get("appendix") or {}).get("positions", []), style)   # P7-1; None without a lagna row; two people: no single chart
    calc = (r.get("engine") or {}).get("calculation", "")
    extra = {}
    extra["remedy_cards"], extra["remedy_sources"] = lk_remedies.cards_html(r)
    moving = [(u["theme"], sens_state(u)) for s in r["sections"] for u in s.get("units", []) if sens_state(u) in ("may_shift", "depends")]
    moving += [(t["label"], sens_state(t)) for t in r.get("timeline", []) if sens_state(t) in ("may_shift", "depends")]
    caption = f"{style.capitalize()} Indian rasi chart (numbers are signs, 1 = Aries; degrees in the table below)" + (f"; {calc}" if calc else "")
    return env.get_template("template.html.j2").render(
        r=r, css=open(os.path.join(ASSETS, "report.css")).read(), type_name=TYPE_NAMES[r["report_type"]],
        default_how_to_read=HOW_TO_READ_NOTIME if r['report_type'] in ('children', 'affairs') else HOW_TO_READ, tl=timeline(r.get("timeline", [])), bases=bases,
        appendix=bool(bases or r.get("appendix") or extra.get("remedy_sources")), section_titles={s["id"]: s["title"] for s in r["sections"]},
        answers_line=r.get("answers") or ANSWERS[r["report_type"]], moving=moving, sens=sens_state, show_evidence=True, used=used_marks(r),
        claim_labels=CLAIM_LABELS, system_labels=SYSTEM_LABELS, basis_labels=BASIS_LABELS,
        chart=chart, chart_caption=caption, spec=bool(r.get("depth")), ledger=ledger(r), partner_caveat=PARTNER_CAVEAT,
        **extra)


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
    extra = [spec_checks(r, fact_ids), citations(r)]
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


def cli_refusals(r):
    """The script cannot recompute the birth day, so it does not trust birth.moon_stable on an unknown time."""
    if time_class(r) == "unknown" and (r.get("birth") or {}).get("moon_stable"):
        return ["birth.moon_stable can only be verified by create_report (the engine recomputes the birth day); "
                "remove it here or render through create_report"]
    return []


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
    errs += cli_refusals(r)
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
        assert re.search(r'class="basis">\s*<span class="chip ev-interpretation">Interpretation</span>\s*<span class="chip ba-COMMENTARY">Commentary</span>\s*<span class="chip sys">Parashari</span>', page), "unit chips"
        assert "Prediction (interpretive)" in page and "Key to the labels" in page and ANSWERS["career"] in page, "legend, answers line"
        assert set(ANSWERS) == set(TYPE_NAMES) and set(LEGEND["claim"]) == set(CLAIM_LABELS) and set(LEGEND["sens"]) == set(SENS_LABELS)
        assert set(CLAIM_LABELS) == set(schema["$defs"]["unit"]["properties"]["claim_type"]["enum"])
        assert set(BASIS_LABELS) == set(schema["$defs"]["unit"]["properties"]["claim_basis"]["enum"])
        assert set(SYSTEM_LABELS) == set(schema["$defs"]["unit"]["properties"]["system"]["enum"])
    print(f"selftest ok ({len(warns)} advisory warnings on the example)")


if __name__ == "__main__":
    main()
