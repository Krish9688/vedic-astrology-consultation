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
import vocab  # noqa: E402  (the project's term list: houses, vargas, dasha names and their spellings)
from life_lint import BUDGET, FACT, lint, report_text  # noqa: E402

TYPE_NAMES = {"kundli": "Kundli report", "complete-life": "Complete life report", "career": "Career report", "relationship": "Relationship report",
              "marriage": "Marriage report", "dasha": "Dasha report", "12-month": "Twelve-month forecast",
              "relocation": "Relocation and foreign travel report", "compact": "Consultation summary",
              "outlook": "Personal outlook", "wealth": "Wealth report", "education": "Education report",
              "reputation": "Reputation report", "spirituality": "Spirituality report", "self": "Self report",
              "family": "Family report", "challenges": "Challenges report"}
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
# Body section ids per type and depth, in order. A section may be left out only with a `dropped` entry and its reason.
SPEC_SECTIONS = {
    "kundli": {"standard": ["foundation", "windows", "self", "strengths", "current"],
               "full": ["foundation", "windows", "self", "career", "relationship", "partner", "intimacy", "wealth",
                        "health", "family", "friends", "education", "home", "travel", "inner", "challenges", "remedies"]},
    "relationship": {"standard": ["windows", "relate", "partner"]},
    "career": {"standard": ["windows", "pattern", "chapter", "next", "money", "choices"]},
    "wealth": {"standard": ["windows", "pattern", "retention", "sudden", "choices"]},
    "education": {"standard": ["windows", "learning", "fields", "next"]},
    "reputation": {"standard": ["windows", "standing", "image", "setbacks", "choices"]},
    "spirituality": {"standard": ["windows", "path", "practice", "inner"]},
    "self": {"standard": ["core", "temperament", "appearance", "growth"]},
    "family": {"standard": ["windows", "home", "mother", "father", "siblings"]},
    "challenges": {"standard": ["windows", "pressure", "disputes", "response"]},
}
LEDGER = {"fact": "Confirmed", "rule": "Inferred", "interpretation": "Inferred", "prediction": "Hypothesis",
          "speculation": "Hypothesis"}
PARTNER_CAVEAT = ("This is an archetype derived from the chart. It is not a description of a real person. Appearance "
                  "and age, where given, are the lowest-confidence parts and are graded Weak.")
# copied exactly from astro/service.py (the skill runs without the engine); tests/test_report_specs.py keeps them equal
UNKNOWN_TIME = re.compile(r"^\s*(unknown|not known|n/?a|none|no (birth )?time)\s*($|[;,(:.-])"
                          r"|\b(birth )?time\s+(is\s+)?(unknown|not known)\b|\bno birth time\b", re.I)
SELF_APPEARANCE_CAVEAT = ("This is the tradition's description, untested and graded Weak: family and region decide "
                          "more, and it is not a measurement.")
HEALTH_CAVEAT = ("This describes tendencies and stress periods. It is not medical advice or a diagnosis; see a "
                 "clinician for any symptom.")
PERCENT = re.compile(r"\d\s?%|\bper ?cent\b|\bpercentage\b", re.I)
ORGANS = re.compile(r"\b(?:liver|kidneys?|lungs?|stomach|intestin\w*|bowels?|colon|bladder|uterus|womb|ovar\w*|testic\w*|"
                    r"prostate|thyroid|pancrea\w*|spleen|gall ?bladder|genital\w*)\b", re.I)
BODY = re.compile(r"\b(?:heart|brain|spine|spinal|bones?|blood|eyes?|skin|teeth|throat|nerves?|joints?)\b", re.I)  # health section
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
# family: dated wording about a parent or sibling is refused anywhere (only home and property may be dated)
PARSIB = re.compile(r"\b(?:mothers?|fathers?|parents?|mom|mum|dad|brothers?|sisters?|siblings?|grand\w+)\b", re.I)
DATEISH = re.compile(r"\b(?:19|20)\d{2}\b|\b(?:January|February|March|April|June|July|August|September|October|November|December|"
                     r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\b|\bMay \d")
KUNDLI_GATES = {"family": "family", "challenges": "challenges", "inner": "spirituality", "self": "self"}   # full kundli section id -> gate set
AGE = re.compile(r"\b(?:older|younger)\b", re.I)            # an age claim only in a sentence about a partner
PARTNER = re.compile(r"\b(?:partner|spouse|husband|wife)\b", re.I)
AFFAIR = re.compile(r"\b(?:affairs?|cheat\w*|unfaithful\w*|infidelit\w*|fidelity|extramarital)\b", re.I)
OWN = re.compile(r"\byour own (?:chart|tendenc\w*)\b", re.I)     # the caveat itself ("your own tendencies, never ...")
OTHER = re.compile(r"\b(?:partner|spouse|husband|wife|boyfriend|girlfriend|he|she|his|her|they|them|their)\b", re.I)


# type gates (batch 1): refused wording per report type, run on the client text of a spec report. A negated clause is
# excused (the spec caveats: "This is not investment advice"), as life_lint does for its certainty probes.
_S = r"[^.!?;]*"
_NEG_WORDS = {"not", "cannot", "can't", "won't", "don't", "never", "no", "nor", "neither", "none", "nothing", "without"}
_NEG_VERB = re.compile(r"\b(?:never|not|no)\s+(?:be\s+)?(?:predict\w*|read|said|stated|given|made|claimed|promised|shown|implied|inferred)\b", re.I)
# emphatic idioms never excuse a match ("Without doubt you will win" is a claim, not a caveat)
_EMPH = re.compile(r"\b(?:no|without(?: a)?) (?:doubt|question|worry)\b|\bnot a worry\b|\bno cause for (?:alarm|worry)\b|\bnothing to fear\b|\bwithout fail\b", re.I)
# a referral ("ask a doctor", "see a lawyer") excuses its own clause
_DEFER = re.compile(r"\b(?:ask|see|consult|speak to|talk to)\s+(?:a|your|the)\s+(?:doctor|clinician|physician|lawyer|solicitor|attorney|"
                    r"(?:medical|legal) professional|professional)\b", re.I)
_CLAUSE = re.compile(r"[;:—–]|[.!?]\s+(?=[A-Z])|,\s+(?:so|but|yet|and so)\b")   # a match never spans a break
_NUMW = (r"(?:(?:twenty|thirty|forty|fifty|sixty|seventy)(?:[-\s](?:one|two|three|four|five|six|seven|eight|nine))?|"
         r"eighteen|nineteen)")
_BUY = r"(?:now|stocks?|shares|gold|property|land|tickets?|crypto\w*|futures|options)"
_PAR = (r"mothers?|fathers?|parents?|grand\w*|brothers?|sisters?|siblings?|relatives?|family|mom|mum|dad|maternal|paternal|"
        r"stepmother|stepfather|mother-in-law|father-in-law")
_HARM = (r"ill|illness\w*|sick\w*|diseas\w*|death|deaths|dies|die|dying|dead|deceased|pass\w* away|passing|"
         r"passes(?!\s+(?:on|down|by|through))|leaves? this world|lifespans?|life spans?|longevity|"
         r"(?:long|short)(?:-| )?(?:life|lives|lived)|live (?:long|short)|health|ailment\w*|cancer|surger\w*|operation|hospital\w*|"
         r"bereave\w*|mourn\w*|griev\w*|grief|funeral|widow\w*|fatal\w*|accidents?|frail\w*|bedridden|well-?being|"
         r"bod(?:y|ily)|unwell|recover\w*|years left|bury|buried|crisis|decline[sd]?|surviv\w+|numbered|much longer|fad(?:es|ed|ing)|time on earth|old age|taken from|final (?:years|days|illness)|"
         r"last (?:days|years|breath)|nursing|care home|heart (?:may |could |will |might )?(?:weak\w*|attack|trouble|problem\w*|"
         r"condition|failure)|weak(?:en|ens|ened|ening)|misfortune|danger|harm")
# shortcut: the subject test is regex only. A relative word counts as the subject of a forecast when it is followed (same
# clause, no "you"/"your" in between) by a modal or a change/ending verb, or when its possessed state noun (days,
# strength, life, years ...) is. "Your father's advice may help you" passes (advice is not a state noun) and a modal
# followed by a helping verb passes ("may help"). Upgrade to a parser if over- or under-blocking shows up.
_REL = r"(?:mothers?|fathers?|parents?|dad|mom|mum|brothers?|sisters?|siblings?|grand\w+|relatives?)"
_MODAL = r"(?:will|may|might|could|would|shall|is likely to|is set to|is going to|is due to|has (?:only )?(?:a few |\w+ )?(?:years?|months?) left|faces?)"
_HELP = r"(?:help|support|guide|advise|encourage|back|assist|listen|teach|show|give|offer|share|inspire|cheer|welcome|understand|love|like|want|enjoy|be (?:proud|glad|happy|pleased))"
_CHG = r"(?:fad(?:e|es|ed|ing)|declin\w*|weaken\w*|leav(?:e|es|ing)|goes|go|pass(?:es|ed|ing)?|worsen\w*|end(?:s|ing)?|numbered|surviv\w+|longer)"
_STATE = r"(?:days|strength|life|lives|years|time|health|energy|condition|situation|fortunes?|journey|presence|stay|stamina|vitality|body|age)"
_NOYOU = r"(?:(?!\byou\b|\byour\b)[^.!?;])*?"
_LEGAL = r"court(?! of public opinion)|judge|case|lawsuit|legal|justice|trial|tribunal|ruling|claim|petition|oppos\w+|bench|opponents?|rivals?|enem\w*|foes?|adversar\w*|other side|opposing party"
_OUTCOME = (r"win|wins|won|winning|lose|loses|lost|losing|favou?r\w*|your side|sides? with|resolv\w*|crush\w*|defeat\w*|beat|beats|"
            r"prevail\w*|triumph\w*|humbl\w*|victor\w*|verdict|judg(?:e)?ment|ruling|award\w*|upheld|uphold\w*|granted|allowed|dismissed|rejected|silenc\w*|in your pocket|everything you asked for|pay|pays|paid|settle\w*")
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
             (re.compile(r"\b(?:hair|skin\w*|teeth|nose|lips|neck|chest|shoulders?|legs?|knees?|forehead|scars?|moles?|birthmarks?|"
                         r"spine|bones?|throat|joints?|limbs|eye colou?r|eyes? (?:are|is|of)\b)", re.I),
              "body-part claims"),
             (re.compile(r"\b(?:weight(?!\s+of)|overweight|underweight|obese|obesity|fat|diet|plump|heavy-?set|bulky|kilos?|kgs?|pounds)\b", re.I),
              "weight claims")],
    "family": [(re.compile(rf"\b{_REL}\b(?:\s+(?:\w+ly|also|then|soon|still|not|never|yet|now))*\s+"
                           rf"(?:{_MODAL}\b(?!\s+(?:not\s+)?{_HELP}\b)|{_CHG}\b)", re.I),
                "a forecast about a parent or sibling"),
               (re.compile(rf"\b{_REL}(?:['’]s|s['’])\s+(?:(?!\byou\b|\byour\b)\w+\s+)?{_STATE}\b{_NOYOU}\b(?:{_MODAL}|{_CHG})\b", re.I),
                "a forecast about a parent or sibling"),
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
    for rx, what in TYPE_GATES.get(t, []):
        for s in strings:
            for c in _clauses(s):
                if _DEFER.search(c):
                    continue
                out += [(what, m.group().lower()) for m in rx.finditer(c) if not _excused(c[:m.start()], m.group())]
    return out


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


def spec_checks(r):
    """Errors for a model written to a T10 spec (it carries `depth`); legacy models (no depth) are left alone."""
    t, depth = r.get("report_type"), r.get("depth")
    if t not in SPEC_SECTIONS:
        return ([f"depth is only for spec reports ({', '.join(SPEC_SECTIONS)})"] if depth else []), []
    if not depth:
        return ([], ["written before the T10 spec (no depth): spec checks skipped"]) if t != "kundli" else (
            ["a kundli report needs depth (standard or full)"], [])
    if depth not in SPEC_SECTIONS[t]:
        return [f"{t} has no depth '{depth}' (only {', '.join(SPEC_SECTIONS[t])})"], []
    errs = [f"spec report needs '{k}' (the frame, report-specs/{t}.md)" for k in ("scope", "confidence_note", "next_step")
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
            if s["id"] == "health" and (m := BODY.search(text)):
                errs.append(f"{name} names a body part ('{m.group()}'): health is lifestyle and stress periods only")
    if t == "self":
        app = next((s for s in r["sections"] if s["id"] == "appearance"), None)
        if app and SELF_APPEARANCE_CAVEAT not in str(app.get("text", "")):
            errs.append("self 'appearance' section needs its caveat sentence in the section text (report-specs/self.md §1)")
    if r.get("remedies") or any(u.get("system") == "lal_kitab" for s in r["sections"] for u in s.get("units", [])):
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
    if hits := sorted({m.group().lower() for s in _strings(r) for m in ORGANS.finditer(s)}):
        errs.append(f"organ words in the report ({', '.join(hits)}): health is lifestyle and stress periods only")
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
    hits = gate_hits(t, strings)
    if t == "kundli":       # the same wording is refused in a kundli section as in the report of its own type
        for sec in r["sections"]:
            if g := KUNDLI_GATES.get(sec["id"]):
                hits += gate_hits(g, _strings(sec))
            if sec["id"] == "self" and any(SELF_LOOKS.search(x) for x in _strings(sec)):
                errs.append("kundli 'self' describes looks: looks belong in the 'partner' section for another person only")
        rows = _strings([r.get(k) for k in ("summary", "timeline", "watch_list", "ranking", "practical_summary")])
        for g in ("family", "challenges", "spirituality"):
            hits += gate_hits(g, rows)
    if t == "family":       # only home and property may carry dates: never a parent or sibling
        for sec in r["sections"]:
            if sec["id"] in ("mother", "father", "siblings") and (
                    any(u.get("timing") for u in sec.get("units", [])) or any(DATEISH.search(x) for x in _strings(sec))):
                errs.append(f"family '{sec['id']}' carries a date or timing: only home and property may be dated")
    if t in ("family", "kundli"):
        dated = ([(f"{x['label']} {x.get('basis', '')}", True) for x in r.get("timeline", [])]
                 + [(" ".join(_strings(x)), bool(DATEISH.search(" ".join(_strings(x))))) for x in r.get("watch_list", [])]
                 + [(" ".join(_strings(x)), True) for x in r.get("ranking", []) if x.get("window")]
                 + [(x, bool(DATEISH.search(x))) for x in _strings(r.get("practical_summary", []))]
                 + [(" ".join(_strings(x)), bool(x.get("window"))) for x in (r.get("summary") or {}).get("key_points", [])])
        for x, is_dated in dated:
            if is_dated and PARSIB.search(x):
                errs.append(f"{t}: a dated row or line names a parent or sibling ('{x[:60]}'): only home and property may be dated")
    for what in sorted({w for w, _ in hits}):
        words = sorted({h for w, h in hits if w == what})
        hint = (" -- phrase it from the person's side, for example 'Your father may help you with the move.'"
                if what == "a forecast about a parent or sibling" else "")
        errs.append(f"{t} report: {what} are not allowed ({', '.join(words[:4])}; report-specs/{t}.md caveats){hint}")
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
        return [x]
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
    chart = chart_svg.chart((r.get("appendix") or {}).get("positions", []), style)   # P7-1; None without a lagna row
    calc = (r.get("engine") or {}).get("calculation", "")
    extra = {}
    extra["remedy_cards"], extra["remedy_sources"] = lk_remedies.cards_html(r)
    moving = [(u["theme"], sens_state(u)) for s in r["sections"] for u in s.get("units", []) if sens_state(u) in ("may_shift", "depends")]
    moving += [(t["label"], sens_state(t)) for t in r.get("timeline", []) if sens_state(t) in ("may_shift", "depends")]
    caption = f"{style.capitalize()} Indian rasi chart (numbers are signs, 1 = Aries; degrees in the table below)" + (f"; {calc}" if calc else "")
    return env.get_template("template.html.j2").render(
        r=r, css=open(os.path.join(ASSETS, "report.css")).read(), type_name=TYPE_NAMES[r["report_type"]],
        default_how_to_read=HOW_TO_READ, tl=timeline(r.get("timeline", [])), bases=bases,
        appendix=bool(bases or r.get("appendix") or extra.get("remedy_sources")), section_titles={s["id"]: s["title"] for s in r["sections"]},
        answers_line=r.get("answers") or ANSWERS[r["report_type"]], moving=moving, sens=sens_state, show_evidence=True, used=used_marks(r),
        claim_labels=CLAIM_LABELS, system_labels=SYSTEM_LABELS, basis_labels=BASIS_LABELS,
        chart=chart, chart_caption=caption, spec=bool(r.get("depth")), ledger=ledger(r), partner_caveat=PARTNER_CAVEAT, health_caveat=HEALTH_CAVEAT,
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
    extra = [spec_checks(r), citations(r)]
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
