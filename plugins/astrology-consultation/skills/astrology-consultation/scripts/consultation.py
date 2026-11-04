#!/usr/bin/env python3
"""Consultation report (owner specification, 2026-11-01): intake -> engine pack -> interpretation model -> checked
HTML, PDF and DOCX.

usage: python3 consultation.py --selftest
The engine (astro.service.consultation_pack / create_consultation_report) computes every number; this module only
validates the intake, arranges the engine output into a pack (tables, charts, ids), checks the interpretation model
written by the consultant against that pack, and renders. Nothing here computes a position (no ephemeris).

Division of labour, so that no number is ever typed by the writer:
- pack  (engine): positions, houses, nakshatras, dignity, vargas, Vimshottari periods, yogas and dosha checks, Shadbala,
                  Ashtakavarga, transits, Lal Kitab placements and annual chart, verification record.
- model (writer): readings, eight life-area chapters, answers to every intake question, timeline, remedies. Every
                  statement carries fact ids (F.*, LK.*, SB.*, AV.*, GO.*, DOSHA.*) and/or engine event ids
                  (DSH.*, ING.*, CON.*) that must exist in the pack; every window must contain the events it cites.
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets", "report")
sys.path.insert(0, HERE)

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
         "Aquarius", "Pisces"]
SIGN_LORD = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]
ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
NAME = dict(Su="Sun", Mo="Moon", Ma="Mars", Me="Mercury", Ju="Jupiter", Ve="Venus", Sa="Saturn", Ra="Rahu", Ke="Ketu",
            Asc="Ascendant")
CHAPTERS = [("love", "Love, relationships and marriage"), ("career", "Career and work"),
            ("wealth", "Wealth and finance"), ("foreign", "Foreign travel and settlement"),
            ("education", "Education and skills"), ("family", "Family and children"),
            ("health", "Health tendencies (general wellness only)"), ("spirituality", "Spirituality and life purpose")]
CHAPTER_IDS = [c for c, _ in CHAPTERS]
# question category -> the chapter that also shows its answer (general and lal_kitab are answered in section 6 only)
CATEGORY_CHAPTER = {"love": "love", "marriage": "love", "relationship": "love", "career": "career",
                    "business": "career", "wealth": "wealth", "finance": "wealth", "foreign": "foreign",
                    "travel": "foreign", "relocation": "foreign", "education": "education", "family": "family",
                    "children": "family", "health": "health", "spirituality": "spirituality", "purpose": "spirituality",
                    "lal_kitab": None, "general": None}
CATEGORY_LABEL = {"love": "Love", "marriage": "Marriage", "relationship": "Relationships", "career": "Career",
                  "business": "Business", "wealth": "Wealth", "finance": "Finance", "foreign": "Foreign travel",
                  "travel": "Travel", "relocation": "Relocation", "education": "Education", "family": "Family",
                  "children": "Children", "health": "Health", "spirituality": "Spirituality", "purpose": "Life purpose",
                  "lal_kitab": "Lal Kitab", "general": "General"}
PRIORITIES = ("high", "medium", "low")
RELIABILITY = ("exact", "approximate", "unknown")
CONSULT_TYPES = ("one-time", "annual", "follow-up")
LANGUAGES = ("English",)          # the report text is English; other languages are refused with a clear message
GRADES = ("Strong", "Moderate", "Weak", "Contradictory", "Unknown")
NOT_PROVIDED = "Not provided"
PLACEHOLDER = re.compile(r"\[(?:CONFIRM|TODO|TBD|FILL|PLACEHOLDER|INSERT|XXX)[^\]]*\]|\bundefined\b|\bTBD\b|\bTODO\b"
                         r"|lorem ipsum|\{\{|\}\}|\bNaN\b|^None$|^null$|\?\?\?", re.I)
YM = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
TOLERANCE_DAYS = 45
INDIA_IST_FROM = dt.date(1945, 10, 15)     # tzdb Asia/Kolkata: IST +05:30 without war time from this date


# ------------------------------------------------------------------------------------------------ intake --------
def _str(x):
    return isinstance(x, str) and x.strip() != ""


def _date(s):
    try:
        return dt.date.fromisoformat(str(s))
    except ValueError:
        return None


def _walk(x, path="$"):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _walk(v, f"{path}[{i}]")
    elif isinstance(x, str):
        yield path, x


def in_india(b):
    place = f"{b.get('place', '')} {b.get('country', '')}".lower()
    if "india" in place:
        return True
    lat, lon = b.get("lat"), b.get("lon")
    return isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and 6 <= lat <= 36 and 68 <= lon <= 97.5 \
        and not re.search(r"nepal|bangladesh|sri lanka|pakistan|bhutan|myanmar|china|kathmandu|dhaka|colombo|lahore|karachi", place)


def validate_intake(intake):
    """Clear, field-named errors for a missing or invalid intake (spec test 5: never a broken report)."""
    errs = []
    if not isinstance(intake, dict):
        return ["intake must be a JSON object"]
    for path, s in _walk(intake):
        if PLACEHOLDER.search(s.strip()):
            errs.append(f"{path}: '{s[:40]}' looks like a placeholder; give the value or leave the field out "
                        f"(it is then printed as '{NOT_PROVIDED}')")
    c, b = intake.get("client") or {}, intake.get("birth") or {}
    k, q, consent = intake.get("consultation") or {}, intake.get("questions"), intake.get("consent") or {}
    if not _str(c.get("full_name")):
        errs.append("client.full_name: the client's name is required")
    if not _str(c.get("gender")):
        errs.append("client.gender: required (write 'prefer not to say' if the client does not give it)")
    lang = c.get("language") or "English"
    if lang not in LANGUAGES:
        errs.append(f"client.language: '{lang}' reports are not available yet; the report is written in English "
                    "(set language to English, or ask for a consultation in another language instead)")
    report_date = _date(k.get("report_date"))
    if report_date is None:
        errs.append("consultation.report_date: give the report date as YYYY-MM-DD")
    bd = _date(b.get("date"))
    if bd is None:
        errs.append(f"birth.date: '{b.get('date')}' is not a valid date (YYYY-MM-DD)")
    elif report_date and bd > report_date:
        errs.append(f"birth.date {bd} is after the report date {report_date}")
    rel = b.get("time_reliability")
    if rel not in RELIABILITY:
        errs.append(f"birth.time_reliability: one of {', '.join(RELIABILITY)}")
    t = b.get("time")
    if rel == "unknown":
        if t not in (None, ""):
            errs.append("birth.time: leave it out when the time is unknown (no placeholder time is printed)")
    elif not (isinstance(t, str) and re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d(:[0-5]\d)?", t)):
        errs.append(f"birth.time: '{t}' is not a 24-hour clock time (HH:MM); if the time is unknown, set "
                    "time_reliability to unknown")
    if rel == "approximate":
        u = b.get("time_uncertainty_min")
        if not (isinstance(u, int) and 1 <= u <= 720):
            errs.append("birth.time_uncertainty_min: an approximate time needs its uncertainty in minutes (1-720)")
    if not _str(b.get("place")):
        errs.append("birth.place: the place of birth is required")
    has = [x for x in ("lat", "lon") if isinstance(b.get(x), (int, float)) and not isinstance(b.get(x), bool)]
    if len(has) == 1:
        errs.append("birth.lat/lon: give both coordinates or neither (the place is then looked up)")
    if b.get("tz") in (None, "") and not _str(b.get("zone")):
        errs.append("birth.tz or birth.zone: give the UTC offset at birth (+HH:MM, India +05:30) or an IANA zone")
    if bd and in_india(b) and bd >= INDIA_IST_FROM and b.get("tz") not in (None, "") \
            and str(b.get("tz")).replace(" ", "") not in ("+05:30", "+0530", "5.5", "+5.5"):
        errs.append(f"birth.tz: an Indian birth on {bd} uses IST +05:30 (got {b.get('tz')}); local mean time is never used")
    if k.get("type") not in CONSULT_TYPES:
        errs.append(f"consultation.type: one of {', '.join(CONSULT_TYPES)}")
    w = k.get("window") or {}
    if w and not (YM.match(str(w.get("from", ""))) and YM.match(str(w.get("to", ""))) and w["from"] <= w["to"]):
        errs.append("consultation.window: from/to as YYYY-MM, from not after to")
    if k.get("chart_style") not in (None, "north", "south"):
        errs.append("consultation.chart_style: north or south")
    if not isinstance(q, list) or not q:
        errs.append("questions: at least one client question is required (the client's own words, with a category "
                    "and a priority)")
    else:
        seen = set()
        for i, x in enumerate(q):
            p = f"questions[{i}]"
            if not isinstance(x, dict):
                errs.append(f"{p}: must be an object with id, text, category, priority")
                continue
            if not re.fullmatch(r"Q\d{1,2}", str(x.get("id", ""))) or x["id"] in seen:
                errs.append(f"{p}.id: Q1, Q2, ... and unique (got {x.get('id')!r})")
            seen.add(x.get("id"))
            if not (_str(x.get("text")) and len(x["text"].strip()) >= 8):
                errs.append(f"{p}.text: the question is empty or too short to answer")
            if x.get("category") not in CATEGORY_CHAPTER:
                errs.append(f"{p}.category: one of {', '.join(CATEGORY_CHAPTER)} (got {x.get('category')!r})")
            if x.get("priority") not in PRIORITIES:
                errs.append(f"{p}.priority: one of {', '.join(PRIORITIES)}")
    if consent.get("store_and_process") is not True:
        errs.append("consent.store_and_process: the client's consent to process the birth data is required")
    for f in ("print_birth_data", "print_full_name", "remedies_requested"):
        if f in consent and not isinstance(consent[f], bool):
            errs.append(f"consent.{f}: true or false")
    return errs


def birth_input(intake):
    """The engine's birth input (BirthInput fields) from a validated intake. An unknown time is computed at 12:00 as a
    placeholder that is never printed; every time-dependent result is withheld or measured over the whole day."""
    b = intake["birth"]
    rel = b["time_reliability"]
    src = b.get("time_source") or {"exact": "stated exact", "approximate": "approximate"}.get(rel, "")
    if rel == "unknown":
        src = "unknown; 12:00 used only as a placeholder, never printed"
    elif rel == "approximate":
        src = f"approximate (±{b['time_uncertainty_min']} min){'; ' + b['time_source'] if b.get('time_source') else ''}"
    out = {"date": b["date"], "time": b.get("time") or "12:00", "lat": b.get("lat"), "lon": b.get("lon"),
           "time_source": src[:120], "calendar": b.get("calendar", "gregorian")}
    for f in ("tz", "zone", "fold"):
        if b.get(f) not in (None, ""):
            out[f] = b[f]
    return out


def sample_times(intake):
    """Clock times at which the chart is recomputed to measure what the uncertain birth time can change."""
    b = intake["birth"]
    rel = b["time_reliability"]
    if rel == "unknown":
        return ["00:00:00", "03:00:00", "06:00:00", "09:00:00", "12:00:00", "15:00:00", "18:00:00", "21:00:00", "23:59:00"]
    if rel == "approximate":
        base = dt.datetime.fromisoformat(f"{b['date']}T{b['time'] if len(b['time']) > 5 else b['time'] + ':00'}")
        u = b["time_uncertainty_min"]
        return [(base + dt.timedelta(minutes=m)).isoformat() for m in (-u, -u // 2, 0, u // 2, u)]
    return []


# ------------------------------------------------------------------------------------------------ pack ----------
def dms(x):
    d = int(x)
    m = int(round((x - d) * 60 * 60))
    m, s = divmod(m, 60)
    if m >= 60:
        d, m = d + 1, m - 60
    return f"{d}°{m:02d}′{s:02d}″"


def _n(v):
    return "—" if v in (None, "", [], "none") else v


def _yoga_names(text):
    names = {}
    for m in re.finditer(r"^- \[([A-Za-z0-9.\-]+)\] (.+?): (HOLDS|does not hold)", text or "", re.M):
        names[m.group(1)] = m.group(2)
    return names


def _house_of(sign_idx, asc_idx):
    return (sign_idx - asc_idx) % 12 + 1


def _ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _rows_for(bodies, key):
    """Chart rows (body, sign, retro) for D1 or a varga, with the Ascendant row the chart drawing needs."""
    rows = []
    for b in ["Asc"] + ORDER:
        if b not in bodies:
            continue
        v = bodies[b]
        sign = v["sign"] if key == "D1" else v["vargas"][key]
        rows.append({"body": "Ascendant" if b == "Asc" else NAME[b], "sign": sign, "retro": bool(v.get("retro"))})
    return rows


def spread(samples):
    """What an uncertain birth time can change: for each quantity, the set of values over the sample charts."""
    out = {}

    def put(k, v):
        out.setdefault(k, set()).add(json.dumps(v, sort_keys=True, default=str))
    for c in samples:
        for b, v in c["bodies"].items():
            put(f"{b}.sign", v["sign"])
            put(f"{b}.nakshatra", v["nakshatra"])
            put(f"{b}.pada", v["pada"])
            put(f"{b}.lon", round(v["lon"], 2))
            for d, s in v["vargas"].items():
                put(f"{b}.{d}", s)
        for md in c["vimshottari"]:
            put(f"DSH.{md['lord']}.start", md["start"][:10])
    varying = {k for k, v in out.items() if len(v) > 1 and not k.endswith(".lon")}
    values = {k: sorted(json.loads(x) for x in v) for k, v in out.items() if len(v) > 1}
    shift = 0
    if len(samples) > 1:
        def starts(c):
            return {md["lord"]: dt.date.fromisoformat(md["start"][:10]) for md in c["vimshottari"]}
        s0 = [starts(c) for c in samples]
        common = set.intersection(*[set(s) for s in s0])
        shift = max((max(s[k] for s in s0) - min(s[k] for s in s0)).days for k in common) if common else None
    return varying, shift, values


def _current(vim, on):
    for md in vim:
        if md["start"][:10] <= on < md["end"][:10]:
            for ad in md.get("sub", []):
                if ad["start"][:10] <= on < ad["end"][:10]:
                    return md, ad
            return md, None
    return None, None


def lk_block(lk_mod, houses):
    """Structured Lal Kitab placements and states, from lal_kitab.py's own tables (the text block is kept too)."""
    L = lk_mod
    occ = {h: [p for p in ORDER if houses.get(p) == h] for h in range(1, 13)}
    rows, ids, disputes = [], {}, []
    for p in ORDER:
        h = houses[p]
        opp = (h + 5) % 12 + 1
        pakka = h in L.LK_PAKKA[p]
        pakka_note = L.LK_PAKKA_DISPUTED.get((p, h), "") if pakka else (
            "pakka ghar in LK1952 only (p72)" if (p, h) in L.LK_PAKKA_LK1952_ONLY else "")
        if pakka_note:
            disputes.append({"topic": f"{NAME[p]} in house {h}: pakka ghar", "shrimali": "pakka ghar" if pakka else "not pakka ghar",
                             "lk1952": "house 12 belongs to Rahu only (p72)" if (p, h) == ("Ju", 12) else "pakka ghar (p72)",
                             "used": "both shown; no edition chosen"})
        if p in L.LK_EXALT:
            dign = "exalted" if h in L.LK_EXALT[p] else "debilitated" if h in L.LK_DEBIL[p] else "—"
            if (p, h) == ("Ma", 8):
                dign = "exalted (Shrimali only)"
                disputes.append({"topic": "Mars in house 8", "shrimali": "exalted", "lk1952": "no planet is exalted in 8 (p72)",
                                 "used": "both readings shown; neither used alone"})
        else:
            (te, td), (ce, cd) = L.LK_NODE_TABLE[p], L.LK_NODE_CHAPTER[p]
            t = "exalted" if h in te else "debilitated" if h in td else "—"
            ch = "exalted" if h in ce else "debilitated" if h in cd else "—"
            dign = t if t == ch else f"tables: {t}; chapters: {ch}"
            if t != ch:
                disputes.append({"topic": f"{NAME[p]} in house {h}: dignity", "shrimali": f"table set: {t}",
                                 "lk1952": f"chapter set: {ch}", "used": "both readings shown; not used as evidence"})
        # sleeping: each edition's own test, never merged (CR-L27)
        rules = [(e, s) for e, s in L.LK_SLEEP.get(h, []) if all(not occ[x] for x in e)]
        if h in L.LK_SLEEP_REPLACES_GENERIC:
            shr = "asleep" if rules else "awake"
        else:
            shr = "asleep" if not occ[opp] else "awake"
        if h == 11:
            k52 = "awake" if occ[1] and occ[3] else "not fully awake"
        elif h in L.LK_ASPECT and h not in L.LK_ASPECT_NONE:
            tg = L.LK_ASPECT[h]
            n_occ = sum(1 for x in tg if occ[x])
            k52 = "awake" if n_occ == len(tg) else "asleep" if not n_occ else "split (no rule for two targets)"
        elif h in (1, 9):
            k52 = "asleep" if not occ[2] else "awake"
        else:
            k52 = "no test in this edition"
        if (shr == "asleep") != (k52 in ("asleep", "not fully awake")) and k52 != "no test in this edition":
            disputes.append({"topic": f"{NAME[p]} in house {h}: sleeping or awake", "shrimali": shr, "lk1952": k52,
                             "used": "both verdicts shown; neither used alone"})
        mates = [q for q in occ[h] if q != p]
        enemies = [NAME[q] for q in mates if q in L.LK_ENEMY[p]]
        friends = [NAME[q] for q in mates if q in L.LK_FRIEND[p]]
        sinful = p in L.LK_SINFUL and h in L.LK_SINFUL[p]
        dharmi = (p in ("Ra", "Ke") and (h == 4 or "Mo" in mates)) or (p == "Sa" and (h == 11 or "Ju" in mates))
        rows.append({"planet": NAME[p], "house": h, "pakka_ghar": "yes" if pakka else "no",
                     "pakka_note": pakka_note, "dignity": dign, "sleeping_shrimali": shr, "sleeping_lk1952": k52,
                     "with_friends": ", ".join(friends) or "—", "with_enemies": ", ".join(enemies) or "—",
                     "state": "dharmi" if dharmi else "sinful placement" if sinful else "—"})
        ids |= {f"LK.{p}.house": h, f"LK.{p}.pakka_ghar": pakka, f"LK.{p}.dignity": dign,
                f"LK.{p}.sleeping.shrimali": shr, f"LK.{p}.sleeping.lk1952": k52,
                f"LK.{p}.state": "dharmi" if dharmi else "sinful" if sinful else "none"}
    masnui = []
    for h in range(1, 13):
        for (a, b), what, note in L.LK_ARTIFICIAL:
            if a in occ[h] and b in occ[h]:
                same = next((x for x in masnui if x["house"] == h and x["pair"] == f"{NAME[a]} + {NAME[b]}"), None)
                if same:              # the book gives two readings for one pair: one row, both readings
                    same["acts_as"] += f"; also {what}"
                    same["note"] = "the book lists both readings for this pair"
                    continue
                masnui.append({"house": h, "pair": f"{NAME[a]} + {NAME[b]}", "acts_as": what,
                               "note": note.strip(" ()") or "—"})
                ids[f"LK.masnui.H{h}.{a}{b}"] = what
                if note:
                    disputes.append({"topic": f"Artificial planet from {NAME[a]} + {NAME[b]}", "shrimali": f"acts as {what}",
                                     "lk1952": note.strip(" ()"), "used": "listed with the note"})
    rin = []
    for ed, table in (("Lal Kitab 1952 (p146–150)", L.RIN_LK1952), ("Shrimali knowledge base B12 (p164–174)", L.RIN_KB)):
        for debt, hurt, hs, foes, note in table:
            got = [q for q in ORDER if q in foes and q != hurt and houses.get(q) in hs]
            if got and (note != "ALL" or len(got) == len(foes)):
                rin.append({"edition": ed, "debt": debt, "planet": NAME[hurt], "houses": ", ".join(map(str, hs)),
                            "occupants": " + ".join(NAME[q] for q in got)})
                key = "lk1952" if ed.startswith("Lal Kitab 1952") else "kb"
                ids[f"LK.rin.{key}.{re.sub(r'[^a-z0-9]+', '_', debt.lower()).strip('_')}"] = True
    e52 = {r["debt"].split(",")[0] for r in rin if r["edition"].startswith("Lal Kitab 1952")}
    ekb = {r["debt"].split(",")[0] for r in rin if not r["edition"].startswith("Lal Kitab 1952")}
    syn = {"swa": "zaati", "zaati": "swa", "stree": "stri", "stri": "stree", "bandhu": "rishtedari", "rishtedari": "bandhu",
           "sister": "ladki-bahan", "ladki-bahan": "sister", "nirdayi": "zalimana", "zalimana": "nirdayi",
           "ajanma": "anjanme", "anjanme": "ajanma", "kudrati": "dargahi", "dargahi": "kudrati"}
    for d in sorted(e52 ^ ekb):
        if syn.get(d) not in (e52 if d in ekb else ekb):
            disputes.append({"topic": f"Debt (rin) signature '{d}'", "shrimali": "present" if d in ekb else "absent",
                             "lk1952": "present" if d in e52 else "absent", "used": "both shown; no debt is declared from one edition"})
    blind = sorted({"+".join(NAME[x] for x in sorted((p, q), key=ORDER.index)) for p in occ[10] for q in occ[10]
                    if p != q and (q in L.LK_ENEMY[p] or p in L.LK_ENEMY[q])})
    if blind:
        ids["LK.chart.blind"] = blind
    return {"houses": {NAME[p]: houses[p] for p in ORDER}, "occupants": {h: [NAME[p] for p in occ[h]] for h in occ},
            "empty_houses": [h for h in range(1, 13) if not occ[h]], "rows": rows, "masnui": masnui, "rin": rin,
            "blind": blind, "disputes": disputes, "ids": ids,
            "awakeners": {h: L.LK_AWAKENER[h] for h in range(1, 13) if not occ[h]}}


def varshaphal_block(vp_mod, houses, dob, on):
    rows_all = vp_mod.load()
    ages = vp_mod.age_years(dob, on)
    n = ages["running"]
    if not 1 <= n <= 120:
        return {"age_year": n, "rows": [], "note": "outside the 1-120 table"}
    natal = {p: houses[p] for p in ORDER}
    out, alt, row = vp_mod.annual(natal, n, rows_all)
    rows, ids = [], {}
    for p in ORDER:
        rows.append({"planet": NAME[p], "natal_house": natal[p], "annual_house": out[p],
                     "lk1952_reading": alt[p] if alt and alt[p] != out[p] else "—",
                     "month_lk1952": vp_mod.lk1952_month(natal, out, p).split(" [")[0],
                     "month_shrimali": vp_mod.shrimali_month(out[p], dob.month).split(" [")[0]})
        ids[f"LK.varsh.{p}.house"] = out[p]
    start = dt.date(dob.year + n - 1, dob.month, min(dob.day, 28 if dob.month == 2 else dob.day))
    end = dt.date(dob.year + n, dob.month, min(dob.day, 28 if dob.month == 2 else dob.day)) - dt.timedelta(days=1)
    note = ""
    if n == 17 or (alt and alt != out):
        note = ("the two editions' tables differ for this year; both readings are shown" if n != 17 else
                "year 17: the recommended row is a reconstruction; the 1952 row is shown as the books-only reading")
    return {"age_year": n, "convention": "running year (LK1952 p243); the completed-years count would give "
            f"{ages['completed']}", "from": start.isoformat(), "to": end.isoformat(), "rows": rows,
            "row_status": row["status"], "note": note, "ids": ids,
            "main_month": f"month {out['Su']} from the birthday (annual Sun in house {out['Su']})"}


KUJA_PLAIN = {"KUJA-BPHS80": "classical rule (BPHS: Mars in 12, 4, 7 or 8 from the lagna)",
              "KUJA-POPULAR": "popular rule (Mars in 1, 2, 4, 7, 8 or 12 from the lagna, Moon or Venus)",
              "KUJA-PD11_3": "Phaladeepika rule (Mars in the 7th)",
              "KUJA-HJH2": "HJH2 rule (Mars in 2, 12, 4, 7 or 8 from the lagna, Moon or Venus)"}
def lk_remedy_dispute(row):
    """CR-L01: do the two editions disagree on whether this Lal Kitab placement can be remedied? Returns the client text
    or "". Shrimali/KB: pakka-ghar planets, and the Sun, Moon or Jupiter in house 6, are not changed by remedies.
    LK1952 (p59-60, p91, p176): own house, exaltation/debilitation or pakka ghar are remediable (doubtful); others are
    fixed, and in house 6 every planet except the Sun, Moon and Jupiter is fixed. A 'sathi' (companion) is not modelled."""
    if not row:
        return ""
    pl, h, pk, dg = row["planet"], row["house"], row["pakka_ghar"] == "yes", str(row.get("dignity", "")).lower()
    if "tables:" in dg:          # Rahu/Ketu: the tables' dignity is the one used as evidence; the chapters' is not
        dg = dg.split("tables:")[1].split(";")[0]
    shr = not (pk or (h == 6 and pl in ("Sun", "Moon", "Jupiter")))
    k52 = (pl in ("Sun", "Moon", "Jupiter")) if h == 6 else (pk or any(w in dg for w in ("exalted", "debilitated", "own")))
    if shr == k52:
        return ""
    if shr:
        return ("The editions disagree: Shrimali's edition allows a remedy here, while the 1952 edition counts this "
                "placement as fixed (beyond remedy). Shown as an optional practice only.")
    return ("The editions disagree: Shrimali's edition says this placement is not changed by remedies, while the 1952 "
            "edition treats it as remediable. Shown as an optional practice only.")


CONTINUOUS = re.compile(r"^SB\.\w+\.ratio$")     # shown to two decimals; its threshold (SB.*.strong) and rank are measured


def chart_ids(c, F, lk_mod=None):
    """Fact ids beyond chart_facts' F.*: Shadbala, Ashtakavarga, transit houses, Jaimini points, dosha checks and the
    Lal Kitab placements. One function, so the birth-time samples are measured with exactly the ids the writer cites."""
    out = {}
    sb = (c.get("shadbala") or {}).get("planets", {})
    for i, (p, v) in enumerate(sorted(sb.items(), key=lambda kv: -kv[1]["ratio"]), 1):
        out |= {f"SB.{p}.ratio": round(v["ratio"], 2), f"SB.{p}.rank": i, f"SB.{p}.strong": v["ratio"] >= 1}
    for i, n in enumerate((c.get("ashtakavarga") or {}).get("sav_by_house") or [], 1):
        out[f"AV.sav.H{i}"] = n
    for p, v in (c.get("transits") or {}).items():
        out |= {f"GO.{p}.from_moon": v.get("house_from_moon"), f"GO.{p}.from_lagna": v.get("house_from_lagna")}
    jf = c.get("jaimini") or {}
    if jf.get("upapada"):
        out |= {"JA.upapada": jf["upapada"], "JA.arudha_lagna": jf.get("arudha_lagna"), "JA.karakamsa": jf.get("karakamsa")}
        out |= {f"JA.{k}": v for k, v in ((jf.get("chara_karakas") or {}).get("scheme8") or {}).items()}
    for y in ("KUJA-BPHS80", "KUJA-POPULAR", "KUJA-PD11_3", "KUJA-HJH2"):
        if f"F.yoga.{y}.holds" in F:
            out[f"DOSHA.kuja.{y}"] = bool(F[f"F.yoga.{y}.holds"])
    if out.get("DOSHA.kuja.KUJA-HJH2") and "HJH2: none in Leo or Aquarius" in str(F.get("F.yoga.KUJA-HJH2.detail", "")):
        out["DOSHA.kuja.KUJA-HJH2"] = False                 # the same source exempts Mars in Leo or Aquarius
        out["DOSHA.kuja.KUJA-HJH2.exempted"] = True
    B = c["bodies"]
    ra = B["Ra"]["lon"]
    out["DOSHA.kala_sarpa"] = len({(B[p]["lon"] - ra) % 360 < 180 for p in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")}) == 1
    out["DOSHA.sade_sati"] = ((c.get("transits") or {}).get("Sa") or {}).get("house_from_moon") in (12, 1, 2)
    if lk_mod is not None and all(f"F.{p}.house" in F for p in ORDER):
        out |= lk_block(lk_mod, {p: F[f"F.{p}.house"] for p in ORDER})["ids"]
    return out


def build_pack(intake, eng, lk_mod=None, vp_mod=None, rr=None):
    """Arrange the engine output into everything the report prints and the ids the writer may cite.
    eng: {"chart": full chart, "derived_text", "derived_ids", "gochara", "samples": [charts], "varying_facts": [...],
          "sensitivity": grid or None, "verification": record or None, "tzdb": str}"""
    c, ids_doc = eng["chart"], eng["derived_ids"]
    F = dict(ids_doc.get("facts", {})) if isinstance(ids_doc, dict) else {}
    m = c["meta"]
    on = m["transit_date"]
    k = intake["consultation"]
    rel = intake["birth"]["time_reliability"]
    unknown = rel == "unknown"
    B = c["bodies"]
    asc = SIGNS.index(B["Asc"]["sign"])
    moon = SIGNS.index(B["Mo"]["sign"])
    varying_q, dasha_shift, spread_values = spread(eng.get("samples") or [])
    vf = set(eng.get("varying_facts") or [])
    sids = eng.get("sample_ids") or []
    measured = set()
    for key in set().union(*sids) if sids else ():
        if len({json.dumps(x.get(key), sort_keys=True, default=str) for x in sids}) > 1 and not CONTINUOUS.match(key):
            measured.add(key)
    vf |= measured
    moon_signs = spread_values.get("Mo.sign") or [B["Mo"]["sign"]]          # more than one: the Moon changes sign that day
    every = "holds at every sampled time of the birth date"
    # ---- planets table ----
    planets = []
    for p in ["Asc"] + ORDER:
        v = B[p]
        row = {"body": NAME[p], "sign": v["sign"], "degree": dms(v["deg"]), "nakshatra": v["nakshatra"],
               "pada": v["pada"], "house": "—" if p == "Asc" else F.get(f"F.{p}.house", "—"),
               "house_from_moon": _house_of(SIGNS.index(v["sign"]), moon),
               "retrograde": "—" if p in ("Asc", "Su", "Mo") else ("yes" if v.get("retro") else "no"),
               "combust": "—" if p in ("Asc", "Su", "Mo", "Ra", "Ke") else ("yes" if F.get(f"F.{p}.combust") else "no"),
               "dignity": "—" if p == "Asc" else (_n(F.get(f"F.{p}.dignity")) if _n(F.get(f"F.{p}.dignity")) != "—"
                                                  else _n(F.get(f"F.{p}.sign_relation"))),
               "relation": "—" if p == "Asc" else _n(F.get(f"F.{p}.sign_relation"))}
        row["varies"] = sorted({f for f in ("sign", "nakshatra", "pada") if f"{p}.{f}" in varying_q}
                               | ({"house", "degree"} if unknown or (rel == "approximate" and "Asc.sign" in varying_q) else set())
                               | ({"degree"} if unknown else set()))
        if p == "Asc" and unknown:
            row["varies"] = ["sign", "degree", "nakshatra", "pada"]
        if "sign" in row["varies"] and p != "Asc":
            row["dignity"] = "varies with the sign"
        planets.append(row)
    # ---- charts ----
    charts = {"D1": _rows_for(B, "D1")}
    for d in ("D9", "D10", "D7", "D4"):
        charts[d] = _rows_for(B, d)
    varga_varies = {d: sorted(NAME[p] for p in ["Asc"] + ORDER if f"{p}.{d}" in varying_q) for d in ("D1", "D9", "D10", "D7", "D4")}
    if unknown:
        varga_varies["D1"] = sorted(set(varga_varies["D1"]) | {"Ascendant"})
    # ---- dasha ----
    vim = c["vimshottari"]
    md, ad = _current(vim, on)
    nxt = vim[vim.index(md) + 1] if md and vim.index(md) + 1 < len(vim) else None
    dasha = {"mahadashas": [{"lord": NAME[x["lord"]], "start": x["start"][:10], "end": x["end"][:10],
                             "id": f"DSH.{x['lord']}"} for x in vim],
             "current_md": md and {"lord": NAME[md["lord"]], "start": md["start"][:10], "end": md["end"][:10], "id": f"DSH.{md['lord']}"},
             "current_ad": ad and {"lord": NAME[ad["lord"]], "start": ad["start"][:10], "end": ad["end"][:10],
                                   "id": f"DSH.{md['lord']}-{ad['lord']}"},
             "antardashas": [{"md": NAME[x["lord"]], "ad": NAME[a["lord"]], "start": a["start"][:10], "end": a["end"][:10],
                              "id": f"DSH.{x['lord']}-{a['lord']}", "current": a is ad}
                             for x in [md, nxt] if x for a in x.get("sub", [])],
             "year_days": m["dasha_year_days"], "shift_days": dasha_shift,
             "stable_running": None}
    if eng.get("samples"):
        runs = {tuple(NAME[x["lord"]] for x in _current(s["vimshottari"], on) if x) for s in eng["samples"]}
        dasha["stable_running"] = len(runs) == 1
        dasha["running_by_sample"] = sorted(" – ".join(r) for r in runs)
    # ---- yogas and dosha checks (only those that hold are shown; the rest are counted) ----
    names = _yoga_names(eng.get("derived_text"))
    yogas, not_holding = [], []
    for key, val in F.items():
        mm = re.fullmatch(r"F\.yoga\.([A-Za-z0-9.\-]+)\.holds", key)
        if not mm or mm.group(1).startswith("KUJA"):
            continue
        y = mm.group(1)
        (yogas if val else not_holding).append(y)
    def plain(t):
        t = re.split(r";\s*(?:DISPUTED|Source|LOL|PD |BJ |BPHS |HJH|any of the seven)", str(t))[0]
        return re.sub(r"\s*\([^)]*(?:p\d|translator|LOL|BJ|PD|BPHS)[^)]*\)", "", t).strip()
    fam = lambda y: re.split(r"-(?:BPHS|LOL|PD|BJ|BARE|LOOSE|HJH)", y)[0]
    yoga_rows = [{"id": y, "name": names.get(y, y), "detail": every if unknown else plain(F.get(f"F.yoga.{y}.detail", "")),
                  "sister_not_holding": [names.get(z, z) for z in not_holding if fam(z) == fam(y) and z != y],
                  "source": F.get(f"F.yoga.{y}.source", ""), "time_dependent": f"F.yoga.{y}.holds" in vf,
                  "disputed": "DISPUTED" in str(F.get(f"F.yoga.{y}.detail", ""))} for y in sorted(yogas)]
    doshas, dosha_ids = [], {}
    kuja = [(y, F.get(f"F.yoga.{y}.holds"), names.get(y, y), F.get(f"F.yoga.{y}.detail", ""))
            for y in ("KUJA-BPHS80", "KUJA-POPULAR", "KUJA-PD11_3", "KUJA-HJH2") if f"F.yoga.{y}.holds" in F]
    kuja = [(y, h and not (y == "KUJA-HJH2" and "HJH2: none in Leo or Aquarius" in det), nm,
             det + ("; exempted by the same source (Mars in Leo or Aquarius)" if y == "KUJA-HJH2" and h and
                    "HJH2: none in Leo or Aquarius" in det else "")) for y, h, nm, det in kuja]
    held = [x for x in kuja if x[1]]
    for y, h, nm, det in kuja:
        dosha_ids[f"DOSHA.kuja.{y}"] = bool(h)
    kuja_varies = any(f"F.yoga.{y}.holds" in vf for y, *_ in kuja)
    kv = lambda y: " (can change within the birth-time range)" if f"F.yoga.{y}.holds" in vf else ""
    if unknown and kuja_varies:
        held = []
        doshas.append({"name": "Mangal (Kuja) — by convention", "status": "not assessed: depends on the birth time",
                       "detail": "the conventions count Mars from the lagna and the Moon, and both change during the birth date", "note": "—", "time_dependent": True})
    elif held:
        doshas.append({"name": "Mangal (Kuja) — by convention", "status": f"holds under {len(held)} of {len(kuja)} conventions"
                       + ("; the count can change within the birth-time range" if kuja_varies else ""),
                       "detail": "; ".join(f"{KUJA_PLAIN.get(y, nm)}: met" + kv(y) for y, _, nm, det in held)
                                 + "".join(f"; {KUJA_PLAIN.get(y, nm)}: not met" + kv(y) + ("; exempted by the same source (Mars in Leo or Aquarius)" if "exempted" in det else "")
                                           for y, h, nm, det in kuja if not h),
                       "note": "Convention membership only; the conventions disagree and several fire in most charts. "
                               "Never a verdict on a marriage.", "time_dependent": kuja_varies})
    ra = B["Ra"]["lon"]
    arc = lambda x: (x - ra) % 360
    sides = {arc(B[p]["lon"]) < 180 for p in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")}
    ks = len(sides) == 1
    dosha_ids["DOSHA.kala_sarpa"] = ks
    if ks:
        doshas.append({"name": "Kala Sarpa pattern", "status": "all seven planets on one side of the Rahu–Ketu axis",
                       "detail": f"Rahu {B['Ra']['sign']} – Ketu {B['Ke']['sign']}",
                       "note": "A modern combination, not classical; no agreed effect and no known cancellation "
                               "(Light on Life p331–333). Shown for completeness, not used as evidence.", "time_dependent": False})
    g = eng.get("gochara") or {}
    sat = (c.get("transits") or {}).get("Sa", {})
    hm = sat.get("house_from_moon")
    PH = {12: "rising phase (Saturn 12th from the Moon)", 1: "peak phase (Saturn over the Moon sign)",
          2: "setting phase (Saturn 2nd from the Moon)"}
    ss = PH.get(hm)
    if len(moon_signs) > 1 and sat.get("sign"):          # the Moon's sign is not fixed: give each possibility
        hms = {ms: _house_of(SIGNS.index(sat["sign"]), SIGNS.index(ms)) for ms in moon_signs}
        if len({bool(PH.get(h)) for h in hms.values()}) > 1:
            ss = "depends on the Moon's sign (" + "; ".join(f"Moon in {ms}: {PH.get(h, 'not active')}" for ms, h in hms.items()) + ")"
        hm = " or ".join(str(h) for h in hms.values())
    dosha_ids["DOSHA.sade_sati"] = bool(ss)
    sade = {"active": bool(ss), "phase": ss, "saturn_sign": sat.get("sign"), "house_from_moon": hm,
            "time_dependent": "Mo.sign" in varying_q}
    sat_ing = [x for x in c.get("ingresses", []) if x["planet"] == "Sa"]
    if ss:
        doshas.append({"name": "Sade Sati (Saturn's 7½-year transit over the Moon)", "status": f"active: {ss}",
                       "detail": f"transit Saturn in {sat.get('sign')}, house {hm} from the natal Moon on {on}",
                       "note": "A broad lens: it matters only when the running period agrees, and it is never a cause on its own.",
                       "time_dependent": "Mo.sign" in varying_q})
    not_assessed_doshas = ["Pitra dosha: the project's classical sources give no definition, so it is not assessed "
                           "(the Lal Kitab 'pitri rin' debt is a different, Lal Kitab-only idea and appears in section 4)."]
    if not held and not (unknown and kuja_varies):
        not_assessed_doshas.append("Mangal (Kuja): no convention holds in this chart.")
    if not ks:
        not_assessed_doshas.append("Kala Sarpa: the planets are not all on one side of the nodes, so the pattern does not occur.")
    if not ss:
        not_assessed_doshas.append(f"Sade Sati: not active on {on} (transit Saturn in house {hm} from the Moon).")
    # ---- strengths and transits ----
    sb = (c.get("shadbala") or {}).get("planets", {})
    shadbala = [{"planet": NAME[p], "rupas": v["total_rupas"], "required": v["required_rupas"], "ratio": v["ratio"],
                 "strong": "yes" if v["ratio"] >= 1 else "no"} for p, v in sb.items()]
    shadbala.sort(key=lambda r: -r["ratio"])
    for i, r in enumerate(shadbala, 1):
        r["rank"] = i
    av = c.get("ashtakavarga") or {}
    sav_house = av.get("sav_by_house") or []
    asc_signs = spread_values.get("Asc.sign") or [B["Asc"]["sign"]]
    gochara_rows = [{"planet": NAME[r["planet"]], "sign": r["sign"], "retro": "yes" if r.get("retro") else "no",
                     "from_moon": " / ".join(str(_house_of(SIGNS.index(r["sign"]), SIGNS.index(ms))) for ms in moon_signs), "from_lagna": r["house_from_lagna"] if len(asc_signs) == 1 or unknown else
                     " / ".join(str(_house_of(SIGNS.index(r["sign"]), SIGNS.index(a))) for a in asc_signs),
                     "condition": r.get("condition", "—"), "reading": r.get("pd_reading", "—") if len(moon_signs) == 1 else "depends on the Moon's sign",
                     "sav": r.get("sav")}
                    for r in g.get("rows", []) if r["planet"] != "Mo"]
    # ---- events the writer may cite ----
    facts_for_events = {"vimshottari": vim, "ingresses": c.get("ingresses", []), "slow_contacts": c.get("slow_contacts", [])}
    ev = rr.event_index(facts_for_events) if rr else {}
    events = []
    for x in c.get("ingresses", []):
        s = SIGNS.index(x["to"])
        events.append({"id": f"ING.{x['planet']}.{x['date'][:10]}", "date": x["date"][:10],
                       "what": f"{NAME[x['planet']]} enters {x['to']}", "house_from_lagna": _house_of(s, asc),
                       "house_from_moon": _house_of(s, moon)})
    for x in c.get("slow_contacts", []):
        events.append({"id": f"CON.{x['transit']}.{x['natal']}.{x.get('aspect', 'contact')}.{x['date'][:10]}",
                       "date": x["date"][:10], "what": f"transit {NAME[x['transit']]} {x.get('aspect', 'contact')} natal {NAME[x['natal']]}"})
    for a in dasha["antardashas"]:
        events.append({"id": a["id"], "date": a["start"], "end": a["end"], "what": f"{a['md']}–{a['ad']} period"})
    for x in dasha["mahadashas"]:
        events.append({"id": x["id"], "date": x["start"], "end": x["end"], "what": f"{x['lord']} major period"})
    # ---- extra fact ids (everything a statement may rest on): the same function measures the time samples ----
    jf = c.get("jaimini") or {}
    extra = chart_ids(c, F, None if unknown else lk_mod)
    extra |= {f"GO.{r['planet']}.sign": r["sign"] for r in g.get("rows", [])}
    # ---- Lal Kitab ----
    lk = vp = None
    if unknown:
        lk_reason = ("Birth time unknown: the Lal Kitab chart is not cast. Lal Kitab places every planet by house, counted "
                     "from the ascendant, and the ascendant needs the birth time. With a birth time this section would "
                     "give the Lal Kitab chart, each planet's house reading (pakka ghar, exalted or debilitated, sleeping "
                     "or awake), the debts (rin), the annual chart (varshphal) for the current year, and remedies with "
                     "both editions compared. A birth certificate, hospital record or family record of the time is "
                     "enough to add it later.")
    elif lk_mod is None:
        lk_reason = "The Lal Kitab module is not installed with this skill."
    else:
        lk_reason = ""
        houses = {p: F[f"F.{p}.house"] for p in ORDER}
        lk = lk_block(lk_mod, houses)
        lk["text"] = [ln for ln in (eng.get("derived_text") or "").split("\n# Lal Kitab", 1)[-1].splitlines()[1:]
                      if ln.strip()] if "# Lal Kitab" in (eng.get("derived_text") or "") else []
        extra |= lk["ids"]
        if vp_mod is not None:
            try:
                vp = varshaphal_block(vp_mod, houses, dt.date.fromisoformat(intake["birth"]["date"]), dt.date.fromisoformat(on))
                extra |= vp.get("ids", {})
                if vp.get("note"):
                    lk["disputes"].append({"topic": f"Varshaphal year {vp['age_year']}", "shrimali": "recommended row",
                                           "lk1952": "1952 row differs", "used": "both readings shown"})
            except (OSError, AssertionError, ValueError) as e:
                vp = {"rows": [], "note": f"annual table not available ({type(e).__name__})"}
    ids = {**F, **extra}
    ids_varying = sorted(x for x in ids if x in vf or x in measured
                         or (unknown and re.match(r"^(LK|SB|AV|DOSHA\.kuja|JA)\.", x))
                         or (unknown and re.match(r"^GO\.\w+\.from_lagna$", x))
                         or (x.startswith("LK.varsh.") and any(k.startswith("LK.") and k.endswith(".house") for k in vf | measured)))
    # ---- methodology ----
    zone = m.get("zone")
    method = {"ayanamsa": f"{m['ayanamsa']} (mean {m['ayanamsa_deg_mean']:.4f}°, true {m['ayanamsa_deg_true']:.4f}°; "
                          "positions use the true value)",
              "houses": ("Houses counted from the Moon's sign (the ascendant needs the birth time); no bhava cusps are given"
                         if unknown else
                         "Whole-sign houses from the sidereal ascendant (Parashari); Sripati bhava cusps are listed in the appendix"),
              "nodes": f"{m['nodes'].capitalize()} nodes (Rahu/Ketu)",
              "dasha": f"Vimshottari from the Moon's nakshatra, year = {m['dasha_year_days']} days (sidereal year)",
              "vargas": "Parashari varga rules (D9 navamsa, D10 dashamsa, D7 saptamsa, D4 chaturthamsa)",
              "time_zone": (f"UTC {m['utc_offset']} — {m.get('utc_offset_source', 'explicit offset')}"
                            + (f"; zone {zone}" if zone else "") + "; civil clock time, never local mean time (LMT)"),
              "time_flags": m.get("utc_offset_flags") or [],
              "ephemeris": f"{m['engine']}; {m['ephemeris']} ({m['ephemeris_range']})",
              "transit_date": f"{on} at {m['transit_time']}",
              "verification": "Independent pyswisseph recompute (no shared code) and PyJHora 4.8.7 (Lahiri set "
                              "explicitly), run out of process. VedAstro is not used: it is not installed locally and "
                              "its library sends birth data to a remote service (the owner's decision).",
              "lal_kitab": "Lal Kitab: houses counted from the lagna, signs dropped (house N = sign N of the natural zodiac); "
                           "Shrimali's edition (2013) and the 1952 edition (Pt. Rupchand Joshi) are "
                           "shown side by side and never merged."}
    return {"schema": "consultation-pack/1", "intake": intake, "time_status": rel,
            "unknown_time": unknown, "report_date": k["report_date"], "on": on,
            "chart_style": k.get("chart_style") or "north", "method": method, "meta": {kk: m[kk] for kk in (
                "engine", "ayanamsa", "utc_offset", "birth_local", "lat", "lon", "nodes", "dasha_year_days") if kk in m},
            "planets": planets, "charts": charts, "varga_varies": varga_varies, "dasha": dasha,
            "yogas": yoga_rows, "yogas_not_holding": len(not_holding), "doshas": doshas,
            "not_assessed_doshas": not_assessed_doshas, "sade_sati": sade,
            "saturn_ingresses": [{"date": x["date"][:10], "to": x["to"]} for x in sat_ing],
            "shadbala": shadbala, "sav_by_house": sav_house, "bav": av.get("bav_by_house") or {},
            "gochara": gochara_rows, "events": sorted(events, key=lambda e: (e["date"], e["id"])),
            "event_ids": sorted(ev), "ids": ids, "varying_ids": ids_varying,
            "lal_kitab": lk, "lal_kitab_reason": lk_reason, "varshaphal": vp,
            "bhavas": c.get("bhavas") or [], "sensitivity": c.get("birth_time_sensitivity_minutes") or {},
            "spread_values": spread_values, "bodies": {b: {x: v[x] for x in ("lon", "sign", "deg", "nakshatra", "pada", "retro", "vargas")}
                                                         for b, v in B.items()},
            "verification": eng.get("verification"),
            "derived_text": eng.get("derived_text") or "",
            "jaimini": {k2: jf.get(k2) for k2 in ("arudha_lagna", "upapada", "karakamsa")} if jf else {},
            "karakas": (jf.get("chara_karakas") or {}).get("scheme8") if jf else {},
            "facts_for_grounding": {"meta": {"transit_date": on, "months": eng.get("months", 60)}, **facts_for_events}}


# ------------------------------------------------------------------------------------------------ writer's brief -
def brief(pack, horizon_years=5):
    """A compact digest for the writer of the interpretation model: the facts, the ids to cite, the events with dates,
    the rules. Everything in it comes from the pack; nothing is to be typed from memory."""
    P, ids = pack, pack["ids"]
    L = []
    W = L.append
    it, b = P["intake"], P["intake"]["birth"]
    W(f"# Writer's brief — consultation report ({P['report_date']})")
    W(f"Birth time: {P['time_status']}" + (f" (±{b.get('time_uncertainty_min')} min)" if P["time_status"] == "approximate" else "")
      + f"; offset UTC{P['meta'].get('utc_offset')}; {P['method']['ayanamsa']}")
    if P["unknown_time"]:
        W("RULES (unknown time): cite NO event ids, NO windows, NO timeline; cite no id in the VARYING list; houses are from the Moon.")
    if P["time_status"] == "approximate":
        W(f"RULES (approximate time): any statement citing a VARYING id, or a DSH.* event (dates move up to "
          f"{P['dasha']['shift_days']} days), must set \"time_sensitive\": true.")
    W("\n## Questions (answer every one, once)")
    for q in it["questions"]:
        W(f"- {q['id']} [{q['category']}, {q['priority']}] {q['text']}")
    W("\n## Positions")
    for r in P["planets"]:
        W(f"- {r['body']}: {r['sign']} {r['degree']}, {r['nakshatra']} {r['pada']}, house {r['house']} (from Moon {r['house_from_moon']}),"
          f" retro {r['retrograde']}, combust {r['combust']}, dignity {r['dignity']}, {r['relation']}" + (f"  VARIES: {r['varies']}" if r['varies'] else ""))
    W("\n## Houses (F.H<n>.*): sign, lord, lord's house, occupants, aspected by")
    for h in range(1, 13):
        W(f"- H{h}: {ids.get(f'F.H{h}.sign')}, lord {ids.get(f'F.H{h}.lord')} in H{ids.get(f'F.H{h}.lord_house')}, "
          f"occupants {ids.get(f'F.H{h}.occupants')}, aspected by {ids.get(f'F.H{h}.aspected_by')}")
    W("\n## Divisional placements (F.<pl>.d9, F.<pl>.d10; D7/D4 in the tables only)")
    for r in P["charts"]["D9"]:
        d10 = next(x["sign"] for x in P["charts"]["D10"] if x["body"] == r["body"])
        W(f"- {r['body']}: D9 {r['sign']}, D10 {d10}")
    W("\n## Yogas that hold (F.yoga.<ID>.holds)")
    for y in P["yogas"]:
        W(f"- {y['id']}: {y['name']}" + (" [DISPUTED]" if y["disputed"] else "") + (" [time-dependent]" if y["time_dependent"] else ""))
    W("\n## Dosha checks (DOSHA.*)")
    for d in P["doshas"]:
        W(f"- {d['name']}: {d['status']}. {d['note']}")
    for x in P["not_assessed_doshas"]:
        W(f"- {x}")
    if not P["unknown_time"]:
        W("\n## Strength (SB.<pl>.rank / .strong / .ratio; AV.sav.H<n>)")
        W("- Shadbala: " + ", ".join(f"{r['planet']} {r['ratio']:.2f}" for r in P["shadbala"]))
        W("- SAV by house: " + ", ".join(f"H{i} {n}" for i, n in enumerate(P["sav_by_house"], 1)))
    W("\n## Transits now (GO.<pl>.from_moon / from_lagna / sign)")
    for r in P["gochara"]:
        W(f"- {r['planet']} in {r['sign']}: {r['from_moon']} from Moon, {r['from_lagna']} from lagna, {r['reading']}")
    W(f"- Sade Sati: {'active, ' + P['sade_sati']['phase'] if P['sade_sati']['active'] else 'not active'}")
    if P.get("jaimini"):
        W(f"- Jaimini: upapada {P['jaimini'].get('upapada')} (JA.upapada), arudha lagna {P['jaimini'].get('arudha_lagna')}, "
          f"karakas {P.get('karakas')}")
    if not P["unknown_time"]:
        d = P["dasha"]
        W("\n## Dasha (event ids DSH.<MD> and DSH.<MD>-<AD>)")
        if d["current_md"]:
            W(f"- NOW: {d['current_md']['lord']} MD {d['current_md']['start']}..{d['current_md']['end']}"
              + (f", {d['current_ad']['lord']} AD {d['current_ad']['start']}..{d['current_ad']['end']} ({d['current_ad']['id']})" if d["current_ad"] else ""))
        for a in d["antardashas"]:
            W(f"- {a['id']}: {a['start']}..{a['end']}")
        nxt = [m for m in d["mahadashas"] if m["start"] > P["on"]][:2]
        for m in nxt:
            W(f"- next MD {m['id']}: {m['start']}..{m['end']}")
        W(f"\n## Transit events within {horizon_years} years (ING.*, CON.*): use the exact id")
        end = (dt.date.fromisoformat(P["on"]) + dt.timedelta(days=365 * horizon_years)).isoformat()
        for e in P["events"]:
            if e["id"].startswith(("ING.", "CON.")) and e["date"] <= end:
                W(f"- {e['id']}: {e['what']}" + (f" (house {e['house_from_lagna']} from lagna, {e['house_from_moon']} from Moon)" if "house_from_lagna" in e else ""))
    lk = P.get("lal_kitab")
    if lk:
        W("\n## Lal Kitab (cite only LK.* ids in Lal Kitab readings)")
        for r in lk["rows"]:
            W(f"- {r['planet']} H{r['house']}: pakka {r['pakka_ghar']}, {r['dignity']}, sleeping Shrimali {r['sleeping_shrimali']} / "
              f"1952 {r['sleeping_lk1952']}, friends {r['with_friends']}, enemies {r['with_enemies']}, {r['state']}")
        W(f"- masnui: {lk['masnui'] or 'none'}; blind: {lk['blind'] or 'none'}")
        W("- rin: " + ("; ".join(f"{x['edition']}: {x['debt']} ({x['planet']}; {x['occupants']} in {x['houses']})" for x in lk["rin"]) or "none"))
        W("- LK ids: " + ", ".join(k for k in ids if k.startswith("LK.") and not k.startswith("LK.varsh")))
        vp = P.get("varshaphal") or {}
        if vp.get("rows"):
            W(f"- Varshaphal age-year {vp['age_year']} ({vp['from']}..{vp['to']}): " +
              ", ".join(f"{r['planet']} {r['natal_house']}->{r['annual_house']}" for r in vp["rows"]) + f"; {vp['main_month']}; ids LK.varsh.<pl>.house")
        W("- Remedies: only the remedies in references/remedy-safety.md or the knowledge base, with safety class; card fields "
          "planet (full name), house (LK house), remedy, safety (low-risk|caution), safe_form (caution), source, instructions, priority, fact_refs (LK.*)")
    if P["varying_ids"]:
        W("\n## VARYING ids (change within the birth-time uncertainty)")
        W(", ".join(x for x in P["varying_ids"] if not x.startswith(("F.yoga",)))[:3000])
    W("\n## Model shape: see assets/report/consultation-model.schema.json (summary, kundli, lal_kitab, chapters x8, answers, timeline, remedies)")
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ model checks --
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
KUNDLI_ITEMS = ("lagna", "moon", "sun", "current_period", "yogas", "strengths", "transits")
LK_ITEMS = ("overview", "debts", "varshaphal")


def ym_label(s):
    y, mo = int(s[:4]), int(s[5:7])
    return f"{MONTHS[mo - 1]} {y}"


def window_label(w):
    a, b = ym_label(w["from"]), ym_label(w["to"])
    return a if a == b else (f"{a[:-5]} – {b}" if a[-4:] == b[-4:] else f"{a} – {b}")


def _ym_dates(w):
    y, mo = int(w["from"][:4]), int(w["from"][5:7])
    s = dt.date(y, mo, 1)
    y, mo = int(w["to"][:4]), int(w["to"][5:7])
    e = dt.date(y + (mo == 12), mo % 12 + 1, 1) - dt.timedelta(days=1)
    return s, e


def _events(pack, rr):
    return rr.event_index(pack["facts_for_grounding"]) if rr else {}


def _planets_of(ev_id):
    return [NAME[x] for x in re.findall(r"\b(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)\b", ev_id.replace("-", " ").replace(".", " "))]


class _Checker:
    def __init__(self, pack, rr):
        self.p, self.errs, self.warns = pack, [], []
        self.ev = _events(pack, rr)
        self.ids = set(pack["ids"])
        self.varying = set(pack["varying_ids"])
        self.unknown = pack["unknown_time"]
        self.approx = pack["time_status"] == "approximate"
        self.shift = (pack.get("dasha") or {}).get("shift_days") or 0

    def dasha_shift(self, x, refs, path):
        """Approximate time: period dates can move by more than the window tolerance, so a statement resting on them
        must say it depends on the exact birth time."""
        if self.approx and self.shift > TOLERANCE_DAYS and any(r.startswith("DSH.") for r in refs) and not x.get("time_sensitive"):
            self.errs.append(f"{path}: rests on dasha dates, which can move by up to {self.shift} days within the stated "
                             "birth-time uncertainty: mark it time_sensitive")

    def item(self, x, path, need_ref=True):
        if not isinstance(x, dict) or not _str(x.get("text")):
            self.errs.append(f"{path}: needs 'text'")
            return
        fr, er = x.get("fact_refs") or [], x.get("event_refs") or []
        if need_ref and not (fr or er):
            self.errs.append(f"{path}: every statement must name the chart factors it rests on (fact_refs or event_refs)")
        bad = [r for r in fr if r not in self.ids]
        if bad:
            self.errs.append(f"{path}: unknown fact id(s) {', '.join(bad[:5])} (only ids from the pack)")
        bad = [r for r in er if r not in self.ev]
        if bad:
            self.errs.append(f"{path}: unknown engine event(s) {', '.join(bad[:5])}")
        false = [r for r in fr if (r.startswith("DOSHA.") or r.endswith(".holds")) and self.p["ids"].get(r) is False]
        if false and not re.search(r"\b(not|no|none|neither|absent|does not|doesn't)\b", x["text"], re.I):
            self.warns.append(f"{path}: cites {', '.join(false)}, which does NOT hold in this chart, in a sentence that "
                              "does not say so: check the claim")
        if self.unknown and er:
            self.errs.append(f"{path}: birth time unknown: no dasha or dated events may be cited (they depend on the time)")
        self.dasha_shift(x, er, path)
        vr = [r for r in fr if r in self.varying]
        if vr and self.unknown:
            self.errs.append(f"{path}: birth time unknown: {', '.join(vr[:4])} change(s) during the birth date and cannot be cited")
        elif vr and self.approx and not x.get("time_sensitive"):
            self.errs.append(f"{path}: {', '.join(vr[:4])} can change within the stated birth-time uncertainty: mark the "
                             "statement time_sensitive (it is then printed with that warning) or rest it on stable factors")

    def window(self, w, path):
        if not isinstance(w, dict) or not _str(w.get("label")) or not (YM.match(str(w.get("from", ""))) and YM.match(str(w.get("to", "")))):
            self.errs.append(f"{path}: a window needs label, from and to (YYYY-MM)")
            return
        if w["from"] > w["to"]:
            self.errs.append(f"{path}: from {w['from']} is after to {w['to']}")
            return
        if self.unknown:
            self.errs.append(f"{path}: birth time unknown: no dated windows")
            return
        refs = w.get("event_refs") or []
        self.dasha_shift(w, refs, path)
        if not refs:
            self.errs.append(f"{path} '{w['label']}': a window must cite the engine events it rests on (event_refs)")
        s, e = _ym_dates(w)
        tol = dt.timedelta(days=TOLERANCE_DAYS)
        for r in refs:
            if r not in self.ev:
                self.errs.append(f"{path} '{w['label']}': unknown engine event {r}")
            elif not any(s - tol <= d <= e + tol for d in self.ev[r]) and not (
                    len(self.ev[r]) == 2 and self.ev[r][0] <= e and self.ev[r][1] >= s):
                self.errs.append(f"{path} '{w['label']}' ({window_label(w)}) does not contain the event {r} "
                                 f"({', '.join(str(d) for d in self.ev[r])})")
        if w.get("kind", "opportunity") not in ("opportunity", "pressure", "watch"):
            self.errs.append(f"{path}: kind is opportunity, pressure or watch")
        for f in ("fact_refs",):
            bad = [r for r in w.get(f) or [] if r not in self.ids]
            if bad:
                self.errs.append(f"{path}: unknown fact id(s) {', '.join(bad)}")


def model_checks(pack, model, rr=None):
    """Consultation-specific checks: every section, every question, every id; (errors, warnings)."""
    C = _Checker(pack, rr)
    E = C.errs
    if not isinstance(model, dict):
        return ["model must be a JSON object"], []
    intake = pack["intake"]
    for path, s in _walk(model):
        if PLACEHOLDER.search(s.strip()):
            E.append(f"{path}: placeholder text '{s[:40]}'")
    sm = model.get("summary") or {}
    if not _str(sm.get("headline")):
        E.append("summary.headline: required")
    kps = sm.get("key_points") or []
    if not 1 <= len(kps) <= 7:
        E.append("summary.key_points: one to seven key points")
    for i, k in enumerate(kps):
        C.item(k, f"summary.key_points[{i}]")
        if k.get("confidence") not in GRADES:
            E.append(f"summary.key_points[{i}].confidence: one of {', '.join(GRADES)}")
        if k.get("window"):
            C.window(k["window"], f"summary.key_points[{i}].window")
    kd = model.get("kundli") or {}
    for f in KUNDLI_ITEMS:
        if pack["unknown_time"] and f in ("lagna", "current_period"):
            if f in kd:
                C.item(kd[f], f"kundli.{f}")
            continue
        if f not in kd:
            E.append(f"kundli.{f}: section 3 needs this reading")
        else:
            C.item(kd[f], f"kundli.{f}")
    if pack["lal_kitab"]:
        lk = model.get("lal_kitab") or {}
        for f in LK_ITEMS:
            if f == "varshaphal" and not (pack.get("varshaphal") or {}).get("rows"):
                continue
            if f not in lk:
                E.append(f"lal_kitab.{f}: section 4 needs this reading")
            else:
                C.item(lk[f], f"lal_kitab.{f}")
                bad = [r for r in lk[f].get("fact_refs", []) if not r.startswith("LK.")]
                if bad:
                    E.append(f"lal_kitab.{f}: a Lal Kitab reading cites only Lal Kitab facts (LK.*), not {', '.join(bad[:3])} "
                             "(the two systems are never merged)")
    ch = model.get("chapters") or {}
    for cid, title in CHAPTERS:
        x = ch.get(cid)
        if not isinstance(x, dict):
            E.append(f"chapters.{cid}: the chapter '{title}' is missing")
            continue
        ind = x.get("indicators") or []
        if not ind:
            E.append(f"chapters.{cid}.indicators: at least one key chart indicator")
        for i, it in enumerate(ind):
            C.item(it, f"chapters.{cid}.indicators[{i}]")
            if any(r.startswith("LK.") for r in it.get("fact_refs", [])):
                E.append(f"chapters.{cid}.indicators[{i}]: Lal Kitab facts belong in section 4, not in a Parashari chapter")
        if "current_period" in x:
            C.item(x["current_period"], f"chapters.{cid}.current_period")
        elif not pack["unknown_time"]:
            E.append(f"chapters.{cid}.current_period: how the running period touches this area")
        ws = x.get("windows") or []
        if not ws and not pack["unknown_time"] and not _str(x.get("no_window_reason")):
            E.append(f"chapters.{cid}.windows: give the favourable windows, or no_window_reason when the chart shows none")
        for i, w in enumerate(ws):
            C.window(w, f"chapters.{cid}.windows[{i}]")
        ca = x.get("cautions") or []
        if not ca:
            E.append(f"chapters.{cid}.cautions: at least one caution or counter-factor")
        for i, it in enumerate(ca):
            C.item(it, f"chapters.{cid}.cautions[{i}]")
    if cid := next((c for c in ch if c not in CHAPTER_IDS), None):
        E.append(f"chapters.{cid}: not a chapter of this report ({', '.join(CHAPTER_IDS)})")
    qs = {q["id"]: q for q in intake["questions"]}
    ans = model.get("answers") or []
    got = [a.get("question_id") for a in ans if isinstance(a, dict)]
    for q in qs:
        if got.count(q) != 1:
            E.append(f"answers: question {q} ('{qs[q]['text'][:50]}') must be answered exactly once (got {got.count(q)})")
    for x in set(got) - set(qs):
        E.append(f"answers: {x} is not a question from the intake")
    for i, a in enumerate(ans):
        p = f"answers[{i}] ({a.get('question_id')})"
        if not (_str(a.get("answer")) and len(a["answer"]) >= 40):
            E.append(f"{p}.answer: a specific answer (not a one-liner)")
        if a.get("confidence") not in GRADES:
            E.append(f"{p}.confidence: one of {', '.join(GRADES)}")
        if not _str(a.get("what_to_do")):
            E.append(f"{p}.what_to_do: what the client can do about it")
        answerable = a.get("answerable", True)
        if not answerable and not _str(a.get("limits")):
            E.append(f"{p}.limits: say why the chart cannot answer it")
        ev = a.get("evidence") or []
        if answerable and not ev:
            E.append(f"{p}.evidence: the chart factors behind the answer")
        for j, it in enumerate(ev):
            C.item(it, f"{p}.evidence[{j}]")
        ws = a.get("windows") or []
        if answerable and not ws and not pack["unknown_time"] and not _str(a.get("no_window_reason")):
            E.append(f"{p}.windows: the best time windows, or no_window_reason")
        for j, w in enumerate(ws):
            C.window(w, f"{p}.windows[{j}]")
    tl = model.get("timeline") or {}
    rd = dt.date.fromisoformat(pack["report_date"])
    if pack["unknown_time"]:
        if tl.get("months_12") or tl.get("years"):
            E.append("timeline: birth time unknown: no dated timeline (dasha dates depend on the birth time)")
    else:
        m12, yrs = tl.get("months_12") or [], tl.get("years") or []
        if not m12:
            E.append("timeline.months_12: the next twelve months at a glance")
        if not yrs:
            E.append("timeline.years: the next three to five years at a glance")
        for i, w in enumerate(m12):
            C.window(w, f"timeline.months_12[{i}]")
            if YM.match(str(w.get("from", ""))) and (_ym_dates(w)[0] > rd + dt.timedelta(days=366) or _ym_dates(w)[1] < rd):
                E.append(f"timeline.months_12[{i}] '{w.get('label')}' lies outside the next twelve months")
        for i, w in enumerate(yrs):
            C.window(w, f"timeline.years[{i}]")
            if YM.match(str(w.get("from", ""))) and (_ym_dates(w)[0] > rd + dt.timedelta(days=366 * 5 + 31) or _ym_dates(w)[1] < rd):
                E.append(f"timeline.years[{i}] '{w.get('label')}' lies outside the next five years")
    rem = model.get("remedies") or {}
    if intake.get("consent", {}).get("remedies_requested"):
        if not rem.get("vedic"):
            E.append("remedies.vedic: the client asked for remedies: give at least one practical Vedic remedy")
        if pack["lal_kitab"] and not rem.get("lal_kitab"):
            E.append("remedies.lal_kitab: the client asked for remedies: give at least one safe Lal Kitab remedy")
        for i, v in enumerate(rem.get("vedic") or []):
            p = f"remedies.vedic[{i}]"
            for f in ("title", "instructions"):
                if not _str(v.get(f)):
                    E.append(f"{p}.{f}: required")
            if v.get("priority") not in PRIORITIES:
                E.append(f"{p}.priority: one of {', '.join(PRIORITIES)}")
            C.item(v.get("why") or {}, f"{p}.why")
        for i, v in enumerate(rem.get("lal_kitab") or []):
            p = f"remedies.lal_kitab[{i}]"
            if not _str(v.get("instructions")):
                E.append(f"{p}.instructions: clear steps")
            if v.get("priority") not in PRIORITIES:
                E.append(f"{p}.priority: one of {', '.join(PRIORITIES)}")
            lkh = (pack.get("lal_kitab") or {}).get("houses", {})
            if lkh and lkh.get(v.get("planet")) != v.get("house"):
                E.append(f"{p}: {v.get('planet')} is in Lal Kitab house {lkh.get(v.get('planet'))}, not {v.get('house')}")
            refs = v.get("fact_refs") or []
            if not refs or any(not r.startswith("LK.") or r not in C.ids for r in refs):
                E.append(f"{p}.fact_refs: the Lal Kitab facts (LK.*) the remedy answers")
    elif rem.get("vedic") or rem.get("lal_kitab"):
        E.append("remedies: the client did not ask for remedies (consent.remedies_requested); leave them out")
    return E, C.warns


# ------------------------------------------------------------------------------------------------ conversion ----
def _unit(x, theme, system="parashari", **kw):
    u = {"theme": theme, "meaning": x["text"], "system": system, "claim_type": kw.pop("claim_type", "interpretation"),
         "fact_refs": [r for r in x.get("fact_refs", []) if r.startswith("F.")]}
    if system == "lal_kitab":
        u["edition"] = "both"
        u["fact_refs"] = []
    u.update({k: v for k, v in kw.items() if v})
    return u


def _timing(w):
    names = sorted({n for r in w.get("event_refs", []) for n in _planets_of(r)}, key=lambda n: list(NAME.values()).index(n))
    return f"{w['label']}: {window_label(w)}" + (f" ({', '.join(names)})" if names else "")


def as_report_model(pack, model):
    """The interpretation as a Structured Report Model, so the existing checks (safety and certainty lint, grounding of
    every dated phrase, the Lal Kitab separation rules, remedy-card safety) run on it unchanged."""
    intake = pack["intake"]
    first = intake["client"]["full_name"].split()[0]
    secs = []
    kd = model.get("kundli") or {}
    secs.append({"id": "kundli", "title": "Personalized Kundli", "units": [
        _unit(kd[f], f.replace("_", " ").capitalize()) for f in KUNDLI_ITEMS if f in kd]})
    lk = model.get("lal_kitab") or {}
    if lk:
        secs.append({"id": "lk-reading", "title": "Lal Kitab view: reading", "units": [
            _unit(lk[f], f.capitalize(), "lal_kitab") for f in LK_ITEMS if f in lk]})
    for cid, title in CHAPTERS:
        x = (model.get("chapters") or {}).get(cid) or {}
        units = [_unit(i, "Indicator") for i in x.get("indicators", [])]
        if x.get("current_period"):
            units.append(_unit(x["current_period"], "Current period"))
        units += [dict(_unit({"text": w.get("text") or w["label"], "fact_refs": w.get("fact_refs", [])}, "Window"),
                       timing=_timing(w)) for w in x.get("windows", [])]
        units += [dict(_unit(i, "Caution"), counter=i["text"]) for i in x.get("cautions", [])]
        secs.append({"id": cid, "title": title, "units": units})
    au = []
    for a in model.get("answers") or []:
        u = {"theme": f"Answer {a.get('question_id')}", "meaning": a.get("answer", ""), "system": "parashari",
             "claim_type": "interpretation", "watch": a.get("what_to_do", ""),
             "fact_refs": [r for e in a.get("evidence", []) for r in e.get("fact_refs", []) if r.startswith("F.")]}
        if a.get("windows"):
            u["timing"] = "; ".join(_timing(w) for w in a["windows"])
        if a.get("limits"):
            u["nuance"] = a["limits"]
        au.append(u)
        for e in a.get("evidence", []):
            if any(r.startswith("LK.") for r in e.get("fact_refs", [])):
                au.append(_unit(e, f"Answer {a.get('question_id')} (Lal Kitab evidence)", "lal_kitab"))
    lk_ans = [u for u in au if u["system"] == "lal_kitab"]
    secs.append({"id": "answers", "title": "Answers to your questions", "units": [u for u in au if u["system"] != "lal_kitab"]})
    if lk_ans:
        secs.append({"id": "lk-answers", "title": "Lal Kitab view: evidence for the answers", "units": lk_ans})
    rem = model.get("remedies") or {}
    if rem.get("vedic"):
        secs.append({"id": "remedies-vedic", "title": "Remedies (Vedic)", "units": [
            dict(_unit(v.get("why") or {"text": ""}, v.get("title", "Remedy")), watch=v.get("instructions", ""))
            for v in rem["vedic"]]})
    tl = model.get("timeline") or {}
    rows = [{"start": w["from"], "end": w["to"], "label": w["label"],
             "kind": {"opportunity": "window", "pressure": "pressure", "watch": "watch"}.get(w.get("kind", "opportunity"), "window"),
             "basis": ", ".join(sorted({n for r in w.get("event_refs", []) for n in _planets_of(r)}))}
            for w in tl.get("months_12", []) + tl.get("years", []) if YM.match(str(w.get("from", ""))) and YM.match(str(w.get("to", "")))]
    sm = model.get("summary") or {}
    kps = [{"text": k.get("text", ""), "confidence": k.get("confidence", "Unknown"),
            **({"window": window_label(k["window"]), "event_refs": k["window"].get("event_refs", [])}
               if isinstance(k.get("window"), dict) and YM.match(str(k["window"].get("from", ""))) and YM.match(str(k["window"].get("to", ""))) else {})}
           for k in sm.get("key_points", [])]
    b = intake["birth"]
    r = {"report_type": "complete-life", "title": "Astrology consultation report", "prepared_for": first,
         "prepared_on": pack["report_date"], "summary": {"headline": sm.get("headline", ""), "key_points": kps},
         "sections": secs, "timeline": rows,
         "birth": {"date": b["date"], "time": b.get("time") or "unknown", "place": b["place"],
                   "time_reliability": b["time_reliability"], "time_source": b.get("time_source") or b["time_reliability"]}}
    if rem.get("lal_kitab"):
        r["remedies_requested"] = True
        r["remedies"] = [{k: v for k, v in c.items() if k in ("planet", "house", "remedy", "safety", "safe_form", "source", "dispute")}
                         for c in rem["lal_kitab"]]
    return r


def all_checks(pack, model, rr, schema):
    """The full gate: consultation checks, then the standard report checks on the converted model. (errors, warnings)"""
    errs, warns = model_checks(pack, model, rr)
    if errs:
        return errs, warns
    r = as_report_model(pack, model)
    facts = pack["facts_for_grounding"]
    fids = {"facts": {k: v for k, v in pack["ids"].items() if k.startswith("F.")}}
    e2, w2 = rr.report_checks(r, schema, facts, fids)
    if pack["unknown_time"]:          # the dated-window rule for unknown times is enforced above, item by item
        e2 = [e for e in e2 if "no dasha period or planet" not in e]
    return errs + e2, warns + [w for w in w2 if "counter-factor" not in w and "nothing to watch" not in w]


# ------------------------------------------------------------------------------------------------ render --------
CONSENT_TEXT = ("The client consented to having their birth details processed for this report. All calculations ran on "
                "this computer; no birth data was sent to any online service. The report files are readable only by "
                "their owner and are not stored in any repository. Birth details are printed only with the client's "
                "permission, and the full name only if the client asked for it.")
UNKNOWN_TEXT = ("No birth time was given, so nothing that depends on it is stated as fact: the ascendant and houses, the "
                "divisional-chart ascendants, the dasha dates, Shadbala, Ashtakavarga and the Lal Kitab chart are left out "
                "or shown as ranges. Houses are counted from the Moon, and only factors that stay the same at every hour "
                "of the birth date are used as evidence. A birth time (a certificate, a hospital record or a family "
                "record) would allow the full report.")
APPROX_TEXT = ("Factors that could change within the stated uncertainty are marked in the tables, and any statement "
               "that rests on one is flagged 'depends on the exact birth time'. Period dates can move by the number of "
               "days given in section 3.")
DASHA_UNKNOWN = ("Vimshottari dates come from the Moon's exact position, which moves about 13° in a day, so with an "
                 "unknown birth time the period dates are not stated.")
TIMELINE_UNKNOWN = ("With an unknown birth time there is no dated timeline: dasha dates and the houses that transits fall "
                    "in both depend on the birth time. The chapters describe tendencies instead. With a birth time, "
                    "the timeline can be added.")
NO_WINDOW_UNKNOWN = "Not dated: the birth time is unknown (see the note on the short version)."
NO_PERIOD_TEXT = "Not stated: the running period depends on the birth time."
GLOSSARY = [
    ("Ayanamsa", "The offset between the tropical and the sidereal zodiac. This report uses Lahiri, India's official standard."),
    ("Lagna (ascendant)", "The sign rising on the eastern horizon at birth; it fixes the twelve houses."),
    ("House (bhava)", "One of twelve areas of life, counted from the lagna (whole-sign houses here)."),
    ("Nakshatra, pada", "One of 27 lunar mansions of 13°20′, each split into four quarters (padas)."),
    ("Rasi (D1)", "The main birth chart of signs and houses."),
    ("Divisional chart (varga)", "A chart derived by dividing each sign: D9 navamsa, D10 dashamsa, D7 saptamsa, D4 chaturthamsa."),
    ("Vimshottari dasha", "A 120-year cycle of planetary periods (major periods and sub-periods) timed from the Moon's nakshatra at birth."),
    ("Mahadasha, antardasha", "A major period and a sub-period within it."),
    ("Gochar", "Transits: where the planets are now, read from the natal Moon and lagna."),
    ("Yoga", "A named combination of planets with a traditional meaning; it shows potential that the periods activate."),
    ("Dosha", "A traditional label for a difficult combination. Several are disputed between sources; none is a verdict."),
    ("Sade Sati", "Saturn's transit through the 12th, 1st and 2nd signs from the natal Moon, about 7½ years."),
    ("Shadbala", "A classical sixfold measure of planetary strength, in rupas; a ratio of 1 or more meets the minimum."),
    ("Ashtakavarga (SAV)", "Points (0-8 per contributor, summed) showing how supported each house is for transits."),
    ("Retrograde (*)", "A planet that appears to move backwards from the Earth."),
    ("Combust", "A planet too close to the Sun to be seen; traditionally weakened."),
    ("Lal Kitab", "A separate 20th-century system with fixed houses (house N = sign N), its own planet states and remedies."),
    ("Pakka ghar", "A planet's permanent house in Lal Kitab."),
    ("Masnui planet", "An artificial planet formed in Lal Kitab by two planets in one house."),
    ("Rin (debt)", "A Lal Kitab pattern said to show an inherited obligation; a signature, never a verdict."),
    ("Varshaphal", "The Lal Kitab annual chart for one year of life."),
    ("Upay", "A Lal Kitab remedy: an optional traditional practice; no efficacy is established."),
]
DISCLAIMER = ("This report is a traditional astrological interpretation based on documented methods (Parashari Jyotish and, "
              "separately, Lal Kitab). It describes tendencies and possible timing within that tradition. It is guidance, "
              "not a prediction of certain events and not a guarantee of any outcome. It does not predict death, illness "
              "or accidents, and it is not a substitute for advice from a doctor, psychologist, lawyer, financial adviser "
              "or other professional. Decisions remain yours. Remedies are optional cultural practices with no "
              "established efficacy. Calculations were made on the client's own computer and checked against independent "
              "software; interpretations rest on the cited chart factors and may differ between astrologers.")
PRIO = {"high": 0, "medium": 1, "low": 2}


def long_date(s):
    d = dt.date.fromisoformat(s[:10])
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def _fmt(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.2f}"
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "none"
    return str(v)


def _ctx(pack, model, rr, lk_rem=None, chart_svg=None):
    from markupsafe import Markup, escape as esc
    intake, m = pack["intake"], model
    cl, b, k = intake["client"], intake["birth"], intake["consultation"]
    consent = {"print_birth_data": True, "print_full_name": True, "remedies_requested": False} | intake.get("consent", {})
    unknown, sv = pack["unknown_time"], pack["spread_values"]
    approx = pack["time_status"] == "approximate"
    asc_alt = " or ".join(x for x in (sv.get("Asc.sign") or []) if x != pack["bodies"]["Asc"]["sign"]) if approx else ""
    cited = {}

    def refs_text(x):
        ids = list(x.get("fact_refs") or []) + list(x.get("event_refs") or [])
        for i in x.get("fact_refs") or []:
            cited[i] = _fmt(pack["ids"].get(i))
        for i in x.get("event_refs") or []:
            e = next((e for e in pack["events"] if e["id"] == i), None)
            cited[i] = (f"{e['what']}, {e['date']}" + (f" to {e['end']}" if e.get("end") else "")) if e else ""
        return ("Rests on: " + ", ".join(ids)) if ids else ""

    def tsmark(x):
        return Markup(" <em class='flag'>(depends on the exact birth time)</em>") if x and x.get("time_sensitive") else ""

    def para(x):
        if not x:
            return ""
        paras = "".join(f"<p>{esc(t)}</p>" for t in x["text"].split("\n\n"))
        return Markup(paras + (f"<span class='refs'>{esc(refs_text(x))}</span>" if refs_text(x) else "")) + tsmark(x)
    first = cl["full_name"].split()[0]
    client = {"first_name": first, "display_name": cl["full_name"] if consent.get("print_full_name") else first,
              "gender": cl.get("gender") or NOT_PROVIDED, "language": cl.get("language") or "English",
              "current_place": ", ".join(x for x in (cl.get("current_city"), cl.get("current_country")) if x) or NOT_PROVIDED}
    for f in ("relationship_status", "occupation", "education"):
        client[f] = cl.get(f) or NOT_PROVIDED
    lat, lon = b.get("lat"), b.get("lon")
    rel = b["time_reliability"]
    birth = {"date_long": long_date(b["date"]), "place": b["place"], "uncertainty": b.get("time_uncertainty_min"),
             "coords": f"{abs(lat):.2f}° {'N' if lat >= 0 else 'S'}, {abs(lon):.2f}° {'E' if lon >= 0 else 'W'}" if lat is not None else "",
             "zone_text": pack["method"]["time_zone"] + (" — Indian Standard Time" if pack["meta"].get("utc_offset") == "+05:30" else ""),
             "zone_plain": (f"UTC{pack['meta'].get('utc_offset')}" + (" — Indian Standard Time (IST)" if pack["meta"].get("utc_offset") == "+05:30" else "")
                            + (f", {b['zone']}" if b.get("zone") else "")
                            + (" — the first occurrence of the repeated hour on the night the clocks went back" if b.get("fold") == 0 else
                               " — the second occurrence of the repeated hour on the night the clocks went back" if b.get("fold") == 1 else "")
                            + "; civil clock time, never local mean time"),
             "midnight": (b.get("time") or "").startswith(("00:00", "0:00")),
             "time_text": {"exact": f"{b.get('time')} (UTC{pack['meta'].get('utc_offset')})",
                           "approximate": f"about {b.get('time')} (±{b.get('time_uncertainty_min')} minutes, UTC{pack['meta'].get('utc_offset')})",
                           "unknown": "unknown"}[rel],
             "reliability_text": {"exact": "Exact" + (f" — {b['time_source']}" if b.get("time_source") else ""),
                                  "approximate": f"Approximate (±{b.get('time_uncertainty_min')} minutes)" + (f" — {b['time_source']}" if b.get("time_source") else ""),
                                  "unknown": "Unknown — time-dependent factors are not used"}[rel]}
    w = k.get("window") or {}
    kk = {"type": k["type"], "focus_text": "; ".join(k.get("focus") or []) or NOT_PROVIDED,
          "window_text": f"{ym_label(w['from'])} to {ym_label(w['to'])}" if w else NOT_PROVIDED}
    qs = []
    for q in intake["questions"]:
        chap = CATEGORY_CHAPTER[q["category"]]
        qs.append(q | {"category_label": CATEGORY_LABEL[q["category"]], "chapter": chap,
                       "chapter_title": dict(CHAPTERS).get(chap, "")})
    style = pack["chart_style"]
    rows = lambda key: pack["charts"][key]
    if unknown:   # Moon chart: the Moon's sign stands in the first house
        moon_sign = next(r["sign"] for r in rows("D1") if r["body"] == "Moon")
        d1 = [{"body": "Ascendant", "sign": moon_sign}] + [r for r in rows("D1") if r["body"] != "Ascendant"]
    else:
        d1 = rows("D1")
    lbl = " — Moon chart: the Moon's sign is house 1" if unknown else ""
    charts = {"D1_north": chart_svg.north(d1, "North Indian chart (D1)" + lbl, "n1", asc=not unknown),
              "D1_south": chart_svg.south(d1, "South Indian chart (D1)" + lbl, "s1", asc=not unknown)}
    for d in ("D9", "D10", "D7", "D4"):
        charts[d] = None if unknown else chart_svg.chart(rows(d), style, f"{d} chart", d.lower())
    if pack["lal_kitab"]:
        lkh = pack["lal_kitab"]["houses"]
        charts["LK"] = chart_svg.north([{"body": "Ascendant", "sign": "Aries"}] +
                                       [{"body": p, "sign": SIGNS[h - 1]} for p, h in lkh.items()], "Lal Kitab chart", "lk", asc=False)
    def show(body_code, field, value):
        vals = sv.get(f"{body_code}.{field}")
        return " / ".join(map(str, vals)) if vals else value
    code = {v: c for c, v in NAME.items()}
    planets = []
    for r in pack["planets"]:
        c = code[r["body"]]
        if unknown and c == "Asc":
            planets.append(r | {"sign_text": "unknown", "degree_text": "unknown", "nak_text": "unknown", "house_text": "—"})
            continue
        lo = sv.get(f"{c}.lon")
        planets.append(r | {"sign_text": show(c, "sign", r["sign"]),
                            "degree_text": (f"{lo[0] % 30:.0f}°–{lo[-1] % 30:.0f}° (range over the day)" if unknown and lo else
                                            f"{lo[0] % 30:.1f}°–{lo[-1] % 30:.1f}° (range over the time window)" if approx and c == "Mo" and lo else
                                            re.sub(r"\d+″$", "", r["degree"]) if approx else
                                            "varies" if unknown and c == "Mo" else r["degree"]),
                            "nak_text": f"{show(c, 'nakshatra', r['nakshatra'])} · {show(c, 'pada', r['pada'])}",
                            "house_text": (" / ".join(str(_house_of(SIGNS.index(r["sign"]), SIGNS.index(ms)))
                                                      for ms in (sv.get("Mo.sign") or [pack["bodies"]["Mo"]["sign"]])) if unknown else
                                           "varies" if "house" in r["varies"] and c != "Asc" else r["house"])})
        if c == "Asc" and "sign" in r["varies"] and lo:
            planets[-1] |= {"degree_text": f"{lo[0] % 30:.0f}° {SIGNS[int(lo[0] // 30)]} – {lo[-1] % 30:.0f}° {SIGNS[int(lo[-1] // 30)]} (range over the time window)"}
    any_varies = any(r["varies"] for r in pack["planets"]) and not (pack["time_status"] == "exact")
    varga_table = []
    for b0 in ["Asc"] + ORDER:
        if unknown and b0 == "Asc":
            continue
        row = {"body": NAME[b0]}
        for d in ("D1", "D9", "D10", "D7", "D4"):
            val = pack["bodies"][b0]["sign"] if d == "D1" else pack["bodies"][b0]["vargas"][d]
            row[d] = show(b0, "sign" if d == "D1" else d, val)
        varga_table.append(row)
    yogas = [y | {"detail_short": re.split(r";\s*(?:DISPUTED|Source)", y["detail"])[0][:170]}
             for y in pack["yogas"] if not (unknown and y["time_dependent"])]
    ev_long = lambda x: x and x | {"start_long": long_date(x["start"]), "end_long": long_date(x["end"])}
    d = pack["dasha"]
    pctx = dict(pack, report_date_long=long_date(pack["report_date"]), on_long=long_date(pack["on"]),
                horizon12_long=long_date((dt.date.fromisoformat(pack["on"]) + dt.timedelta(days=365)).isoformat()),
                dasha=dict(d, current_md=ev_long(d["current_md"]), current_ad=ev_long(d["current_ad"])))

    def wrow(w):
        return w | {"when": window_label(w) + (" (depends on the exact birth time)" if w.get("time_sensitive") else ""),
                    "refs_text": refs_text(w),
                    "kind_text": {"opportunity": "favourable", "pressure": "pressure", "watch": "watch"}[w.get("kind") or "opportunity"]}
    ans_by_q = {a["question_id"]: a for a in m.get("answers", [])}
    answers = []
    for q in qs:
        a = ans_by_q[q["id"]]
        answers.append(a | {"question": q["text"], "category_label": q["category_label"], "priority": q["priority"],
                            "answerable": a.get("answerable", True),
                            "evidence": [e | {"refs_text": refs_text(e)} for e in a.get("evidence", [])],
                            "windows": [wrow(w) for w in a.get("windows", [])]})
    chapters_full = []
    for cid, title in CHAPTERS:
        x = m["chapters"][cid]
        cp = x.get("current_period")
        chapters_full.append({"id": cid, "title": title, "no_window_reason": x.get("no_window_reason"),
                              "indicators": [i | {"refs_text": refs_text(i)} for i in x.get("indicators", [])],
                              "current_period": cp and cp | {"refs_text": refs_text(cp)},
                              "windows": [wrow(w) for w in x.get("windows", [])],
                              "cautions": [i | {"refs_text": refs_text(i)} for i in x.get("cautions", [])],
                              "answers": [{"question_id": a["question_id"], "question": a["question"],
                                           "short": a.get("short") or re.split(r"(?<=[.!?])\s", a["answer"], maxsplit=1)[0]}
                                          for a in answers if dict((q["id"], q["chapter"]) for q in qs)[a["question_id"]] == cid]})
    tl = m.get("timeline") or {}
    m12 = [wrow(w) for w in tl.get("months_12", [])]
    years = [wrow(w) for w in tl.get("years", [])]
    bar = lambda ws: rr.timeline([{"start": w["from"], "end": w["to"], "label": w["label"],
                                   "kind": {"opportunity": "window"}.get(w.get("kind", "opportunity"), w.get("kind"))} for w in ws]) if ws else None
    rem, remedies = m.get("remedies") or {}, []
    for v in rem.get("vedic") or []:
        why = v.get("why") or {}
        remedies.append({"priority": v["priority"], "system": "Vedic", "title": v["title"], "instructions": v["instructions"],
                         "why": why.get("text", ""), "refs_text": refs_text(why), "safety": "Optional practice · no efficacy established",
                         "source": v.get("source") or "Classical shanti practice (prayer, chanting, charity), Phaladeepika XXVI.49",
                         "dispute": ""})
    lkrows = {r["planet"]: r for r in (pack.get("lal_kitab") or {}).get("rows", [])}
    for v in rem.get("lal_kitab") or []:
        safe = v.get("safety") == "caution"
        v = v | {"dispute": lk_remedy_dispute(lkrows.get(v.get("planet"))) or ""}
        remedies.append({"priority": v["priority"], "system": "Lal Kitab",
                         "title": (v.get("safe_form") if safe else v.get("remedy")),
                         "safety": (lk_rem.SAFETY.get(v.get("safety"), "") if lk_rem else "") + " · no efficacy established"
                                   + ("; the editions disagree whether this placement can be remedied" if v.get("dispute") else ""),
                         "source": v.get("source", ""), "dispute": v.get("dispute", ""),
                         "instructions": v["instructions"], "why": f"{v['planet']} in Lal Kitab house {v['house']}",
                         "refs_text": refs_text(v)})
    remedies.sort(key=lambda r: PRIO[r["priority"]])
    raw = []
    for b0 in ["Asc"] + ORDER:
        v = pack["bodies"][b0]
        lo = sv.get(f"{b0}.lon")
        if unknown and (b0 == "Asc"):
            raw.append({"body": NAME[b0], "lon": "unknown", "sign": "unknown", "deg": "—", "nak": "—", "pada": "—", "vargas": "—"})
            continue
        raw.append({"body": NAME[b0], "lon": f"{lo[0]:.2f}°–{lo[-1]:.2f}°" if lo else f"{v['lon']:.4f}°",
                    "sign": show(b0, "sign", v["sign"]), "deg": "range" if lo else f"{v['deg']:.4f}°",
                    "nak": show(b0, "nakshatra", v["nakshatra"]), "pada": show(b0, "pada", v["pada"]),
                    "vargas": "—" if unknown else " ".join(f"{dd}:{s[:3]}" for dd, s in v["vargas"].items())})
    sens = [] if pack["time_status"] == "unknown" else [
        {"factor": f, "before": f"{x['earlier']} min" if isinstance((x or {}).get("earlier"), (int, float)) else "beyond the range checked",
         "after": f"{x['later']} min" if isinstance((x or {}).get("later"), (int, float)) else "beyond the range checked"} for f, x in (pack.get("sensitivity") or {}).items()]
    ver = pack.get("verification")
    if ver and unknown:          # the cross-check ran at the placeholder time: print no time-specific value
        keep = ("Lahiri", "Signs", "Nakshatra", "Divisional", "Vimshottari", "Bhava", "Panchang")
        ver = dict(ver, rows=[r for r in ver["rows"] if r["quantity"].startswith(("Lahiri",)) or
                              (r["quantity"].startswith(keep) and "values" in str(r["engine"]))],
                   about=ver["about"] + " The birth time is unknown, so the check was run at a placeholder time: it shows "
                         "that the engine agrees with the references, not facts about this birth; time-specific values "
                         "are not printed.")
    lk_cards = bool(rem.get("lal_kitab"))
    for e in m.get("summary", {}).get("key_points", []):
        refs_text(e)
        if isinstance(e.get("window"), dict):
            refs_text(e["window"])
    kps = [k2 | ({"window_text": window_label(k2["window"])} if isinstance(k2.get("window"), dict) else {})
           for k2 in m["summary"]["key_points"]]
    vp = pack.get("varshaphal")
    if vp and vp.get("rows"):
        vp = vp | {"from_long": long_date(vp["from"]), "to_long": long_date(vp["to"]),
                   "alt_differs": any(r["lk1952_reading"] != "—" for r in vp["rows"])}
    lkp = pack.get("lal_kitab")
    if lkp:
        lkp = dict(lkp, no_test=[r["planet"] for r in lkp["rows"] if r["sleeping_lk1952"] == "no test in this edition"])
    moon_vals = sv.get("Mo.sign")
    moon_stab = (f"The Moon itself changes sign during the birth date ({' / '.join(moon_vals)}), so even the Moon chart "
                 "is uncertain; the chart shows the Moon's sign at midday." if moon_vals else
                 "The Moon stays in the same sign through the whole birth date, so the Moon chart is reliable.")
    ctx = dict(p=pctx, m=dict(m, summary=dict(m["summary"], key_points=kps), kundli=m.get("kundli") or {},
                              lal_kitab=m.get("lal_kitab") or {}),
               client=client, birth=birth, k=kk, consent=consent, questions=qs, chapters=CHAPTERS,
               chapters_full=chapters_full, answers=answers, charts=charts, planets=planets, any_varies=any_varies,
               varies_note=("Highlighted rows: a value that changes within the birth-time uncertainty is shown as "
                            "'A / B'." if not unknown else "Values that change during the birth date are shown as 'A / B'; "
                            "houses are counted from the Moon."),
               varga_table=varga_table, varga_note=("Divisional-chart ascendants need the birth time; they are not drawn." if unknown else
                                                    "The Ascendant row is the divisional chart's own lagna."),
               lagna_sign="unknown" if unknown else show("Asc", "sign", pack["bodies"]["Asc"]["sign"]), moon_sign=show("Mo", "sign", pack["bodies"]["Mo"]["sign"]),
               sun_sign=show("Su", "sign", pack["bodies"]["Su"]["sign"]), lagna_unknown=("The lagna is not known without a birth "
               "time; the Moon chart stands in for it in this report."), yogas=yogas,
               no_yogas_text="None of the named yoga definitions that are independent of the birth time holds." if unknown else "None of the named yoga definitions holds.",
               lk=lkp, vp=vp, lk_cards=lk_cards, lk_process=lk_rem.PROCESS if lk_rem else "",
               m12=m12, years=years, tl12=bar(tl.get("months_12", [])), tly=bar(tl.get("years", [])),
               remedies=remedies, raw_positions=raw, sensitivity_rows=sens,
               bav_rows=[{"planet": NAME[p], "points": v} for p, v in (pack.get("bav") or {}).items()],
               verification=ver, glossary=GLOSSARY, disclaimer=DISCLAIMER, consent_text=CONSENT_TEXT,
               unknown_text=UNKNOWN_TEXT, approx_text=APPROX_TEXT, dasha_unknown=DASHA_UNKNOWN,
               timeline_unknown=TIMELINE_UNKNOWN, no_window_unknown=NO_WINDOW_UNKNOWN, no_period_text=NO_PERIOD_TEXT,
               moon_stability=moon_stab, para=para, tsmark=tsmark, asc_alt=asc_alt)
    return ctx, cited


def html_of(pack, model, rr, lk_rem=None, chart_svg=None):
    import jinja2
    if chart_svg is None:
        import chart_svg
    if lk_rem is None:
        import lk_remedies as lk_rem
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ASSETS), autoescape=True)
    css = open(os.path.join(ASSETS, "report.css"), encoding="utf-8").read() + "\n" + \
        open(os.path.join(ASSETS, "consultation.css"), encoding="utf-8").read()
    ctx, cited = _ctx(pack, model, rr, lk_rem, chart_svg)
    # the cited-ids table is filled while the context is built, so render once to collect, then render for real
    tpl = env.get_template("consultation.html.j2")
    tpl.render(css=css, cited=[], **ctx)
    return tpl.render(css=css, cited=sorted(cited.items()), **ctx)


def _owner_only(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    return os.fdopen(fd, "wb")


def write_pdf(html, path):
    from weasyprint import HTML
    doc = HTML(string=html, base_url=ASSETS).render()
    with _owner_only(path) as f:
        doc.write_pdf(f, identifier=b"astrology-consultation-report", uncompressed_pdf=False)


def write_docx(pack, model, path, html=None):
    """A Word version of the same content (text and tables; charts as images when PyMuPDF can rasterise the SVG)."""
    import docx
    from docx.shared import Pt, Mm
    d = docx.Document()
    for s in d.sections:
        s.page_height, s.page_width = Mm(297), Mm(210)
        s.left_margin = s.right_margin = Mm(20)
    st = d.styles["Normal"]
    st.font.name, st.font.size = "Calibri", Pt(10)
    import html as H
    from html.parser import HTMLParser

    class P(HTMLParser):
        """Walk the rendered HTML: headings, paragraphs, list items, tables and SVG charts, in order."""
        def __init__(self):
            super().__init__()
            self.stack, self.buf, self.table, self.row, self.cell = [], [], None, None, None
            self.skip = 0
            self.svg = None

        def flush(self, kind):
            t = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            self.buf = []
            if not t:
                return
            if kind in ("h1", "h2", "h3", "h4"):
                d.add_heading(t, level={"h1": 0, "h2": 1, "h3": 2, "h4": 3}[kind])
            elif kind == "li":
                d.add_paragraph(t, style="List Bullet")
            else:
                d.add_paragraph(t)

        def handle_starttag(self, tag, attrs):
            if tag in ("style", "title", "head"):
                self.skip += 1
            if tag == "svg":
                self.svg = [self.get_starttag_text()]
                return
            if self.svg is not None:
                self.svg.append(self.get_starttag_text())
                return
            if tag == "table":
                self.table = []
            elif tag == "tr" and self.table is not None:
                self.row = []
            elif tag in ("td", "th") and self.row is not None:
                self.cell = []
            elif tag in ("p", "li", "h1", "h2", "h3", "h4", "dt", "dd", "div") and self.cell is None:
                self.flush("p")
            elif tag == "br":
                (self.cell if self.cell is not None else self.buf).append(" ")

        def handle_startendtag(self, tag, attrs):
            if self.svg is not None:
                self.svg.append(self.get_starttag_text())      # <rect .../> is complete: no closing tag
            elif tag == "br":
                (self.cell if self.cell is not None else self.buf).append(" ")

        def handle_endtag(self, tag):
            if tag in ("style", "title", "head"):
                self.skip = max(0, self.skip - 1)
            if self.svg is not None:
                self.svg.append(f"</{tag}>")
                if tag == "svg":
                    self.add_svg("".join(self.svg))
                    self.svg = None
                return
            if tag in ("td", "th") and self.cell is not None:
                self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
                self.cell = None
            elif tag == "tr" and self.row is not None:
                self.table.append(self.row)
                self.row = None
            elif tag == "table" and self.table is not None:
                rows = [r for r in self.table if r]
                if rows:
                    n = max(len(r) for r in rows)
                    t = d.add_table(rows=len(rows), cols=n)
                    t.style = "Table Grid"
                    for i, r in enumerate(rows):
                        for j, v in enumerate(r):
                            t.cell(i, j).text = v
                self.table = None
            elif tag in ("p", "li", "h1", "h2", "h3", "h4", "dt", "dd", "div", "figcaption") and self.cell is None:
                self.flush(tag)

        def handle_data(self, data):
            if self.skip:
                return
            if self.svg is not None:
                self.svg.append(H.escape(data))
            elif self.cell is not None:
                self.cell.append(data)
            else:
                self.buf.append(data)

        def add_svg(self, svg):
            try:
                try:
                    import pymupdf as fitz
                except ImportError:
                    import fitz
                import io
                doc = fitz.open(stream=svg.encode("utf-8"), filetype="svg")
                pix = doc[0].get_pixmap(dpi=150)
                d.add_picture(io.BytesIO(pix.tobytes("png")), width=Mm(70))
            except Exception:                                   # no PyMuPDF: the chart's text description instead
                m = re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.S)
                d.add_paragraph(H.unescape(m.group(1)) if m else "(chart)")
    P().feed(html or "")
    core = d.core_properties
    core.title, core.author = "Astrology consultation report", "astrology-consultation"
    when = dt.datetime.fromisoformat(pack["report_date"] + "T00:00:00")
    core.created = core.modified = when
    core.last_modified_by = "astrology-consultation"
    core.revision = 1
    import io
    import zipfile
    buf = io.BytesIO()
    d.save(buf)
    src = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
    out = io.BytesIO()                                   # same input, same bytes: fixed zip entry dates and order
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(src.namelist()):
            zi = zipfile.ZipInfo(n, date_time=(when.year, when.month, when.day, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, src.read(n))
    with _owner_only(path) as g:
        g.write(out.getvalue())


BAD_PAGE_TEXT = re.compile(r"\bundefined\b|(?-i:\bNone\b(?![ \t]+[a-z]))|(?-i:\bNaN\b|\bnan\b)|\{\{|\}\}|\[CONFIRM|Traceback|\bTODO\b|\?\?|\bnull\b", re.I)


def pdf_check(path, expect_min_pages=12):
    """Every page renders text, nothing broken leaks through, the TOC page numbers resolved. Returns problems."""
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    doc = fitz.open(path)
    out = []
    if doc.page_count < expect_min_pages:
        out.append(f"only {doc.page_count} pages")
    for i, pg in enumerate(doc, 1):
        t = pg.get_text()
        if len(t.strip()) < 40:
            out.append(f"page {i}: almost no text ({len(t.strip())} characters)")
        if m := BAD_PAGE_TEXT.search(t):
            out.append(f"page {i}: '{m.group()}' in the page text")
        if i > 1 and not re.search(rf"\b{i}\s*/\s*{doc.page_count}\b", t):
            out.append(f"page {i}: no page number")
    toc = next((pg.get_text() for pg in doc if "Contents" in pg.get_text()[:200]), "")
    if not re.search(r"Methodology and settings\s*\.*\s*\d+", toc) and not re.search(r"Methodology and settings[\s.]*\n\s*\d+", toc):
        out.append("contents page has no page numbers")
    return out


def report(pack, model, out_dir, base, rr, schema, formats=("html", "pdf", "docx")):
    """Check, then write the files. Returns {ok, errors | warnings, html, pdf, docx, pdf_problems}."""
    errs, warns = all_checks(pack, model, rr, schema)
    if errs:
        return {"ok": False, "errors": errs, "warnings": warns}
    html = html_of(pack, model, rr)
    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    res = {"ok": True, "warnings": warns, "html": None, "pdf": None, "docx": None, "pdf_problems": []}
    hp = os.path.join(out_dir, base + ".html")
    with _owner_only(hp) as f:
        f.write(html.encode("utf-8"))
    res["html"] = hp
    if "pdf" in formats:
        try:
            pp = os.path.join(out_dir, base + ".pdf")
            write_pdf(html, pp)
            res["pdf"] = pp
            try:
                res["pdf_problems"] = pdf_check(pp)
            except ImportError:
                res["warnings"].append("PDF not checked page by page (PyMuPDF not installed)")
        except ImportError:
            res["warnings"].append("PDF not written: WeasyPrint is not installed (print the HTML to PDF from a browser)")
        except OSError as e:          # WeasyPrint installed but its system libraries (Pango, GObject) are missing
            res["warnings"].append(f"PDF not written: WeasyPrint cannot load its system libraries ({str(e)[:80]}); "
                                   "install Pango, or print the HTML to PDF from a browser")
    if "docx" in formats:
        try:
            dp = os.path.join(out_dir, base + ".docx")
            write_docx(pack, model, dp, html)
            res["docx"] = dp
        except ImportError:
            res["warnings"].append("DOCX not written: python-docx is not installed")
    if res["pdf_problems"]:
        res["ok"] = False
        res["errors"] = [f"PDF check: {x}" for x in res["pdf_problems"]]
    return res


def selftest():
    bad = validate_intake({"client": {}, "birth": {"date": "2005-13-40", "time_reliability": "exact", "time": "25:00"},
                           "consultation": {"type": "weekly"}, "questions": [], "consent": {}})
    joined = " | ".join(bad)
    for want in ("full_name", "birth.date", "birth.time", "questions", "consent.store_and_process", "consultation.type",
                 "birth.place", "report_date"):
        assert want in joined, (want, bad)
    ok = {"client": {"full_name": "Asha Rao", "gender": "female", "language": "English"},
          "birth": {"date": "1990-01-01", "time": "10:00", "time_reliability": "exact", "place": "Pune, India",
                    "lat": 18.52, "lon": 73.86, "tz": "+05:30"},
          "consultation": {"type": "one-time", "report_date": "2026-11-01"},
          "questions": [{"id": "Q1", "text": "When is a good time to change jobs?", "category": "career", "priority": "high"}],
          "consent": {"store_and_process": True}}
    assert validate_intake(ok) == [], validate_intake(ok)
    assert any("IST" in e for e in validate_intake(json.loads(json.dumps(ok).replace('"+05:30"', '"+05:53"'))))
    assert any("placeholder" in e for e in validate_intake(json.loads(json.dumps(ok).replace("female", "[CONFIRM gender]"))))
    unk = json.loads(json.dumps(ok))
    unk["birth"] |= {"time_reliability": "unknown", "time": None}
    assert validate_intake(unk) == [] and birth_input(unk)["time"] == "12:00" and len(sample_times(unk)) == 9
    assert window_label({"from": "2027-03", "to": "2027-06"}) == "March – June 2027"
    assert window_label({"from": "2026-11", "to": "2027-02"}) == "November 2026 – February 2027"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__.strip())
