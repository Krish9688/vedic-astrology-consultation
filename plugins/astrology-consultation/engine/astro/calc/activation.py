"""Dasha activation table, topic significator networks and the retrospective calibration check (roadmap P4-6;
PRED-X1, X5, X6; timing.md §0 steps 3-7). Calculation and rule lookup only: no verdicts, no grading of outcomes.

Lordships, houses, dignities and vargas come from the skill's chart_facts.facts_json ids (one implementation); this
module only arranges them by dasha segment. A network is frozen by a sha256 over its canonical JSON: a network whose
content no longer matches its hash, or that was built for another chart, is refused.

Date rule: segments are half-open, start <= date < end (local dates at the birth UTC offset), so a contact dated
exactly on a boundary belongs to the segment that starts that day. A Jupiter/Saturn sign stay belongs to every
segment it overlaps (stay.from < segment.end and stay.to > segment.start).
"""
from __future__ import annotations

import copy
import hashlib
import json

from .engine import SIGNS
from .strength import SIGN_LORD

NOT_CHECKED = "source map, not page-checked"
RAMAN = "HJH2 {p} (Raman's significators (a)-(g), the same list for every house; timing.md §1; " + NOT_CHECKED + ")"
SKILL_ONLY = "skill method file only, no book locator"
# topic -> house the (a)-(g) list runs on, the HJH2 page of that house's version, karakas and extras.
# Each extra: (role, rule, source, variant-or-None); rule names a fact lookup (see _pick).
PRESETS = {
    "marriage": {"house": 7, "page": "p20-21 (pr 13-14)",
                 "karaka": [("Ve", "HJH2 p20-21 (karaka Venus); " + NOT_CHECKED, None)],
                 "extras": [
                     ("dispositor of the 7th lord", ("disp", 7), "HJH2 p25-26 (pr 18-19); " + NOT_CHECKED, None),
                     ("navamsa dispositor of the 7th lord", ("d9lord", 7), "HJH2 p25-26 (pr 18-19); " + NOT_CHECKED, None),
                     ("Moon", ("planet", "Mo"), "HJH2 p25-26 (pr 18-19); " + NOT_CHECKED, None),
                     ("2nd lord", ("lord", 2), "HJH2 p25-26 (pr 18-19); " + NOT_CHECKED, None),
                     ("navamsa dispositor of the 2nd lord", ("d9lord", 2), "HJH2 p25-26 (pr 18-19); " + NOT_CHECKED, None),
                     ("9th lord", ("lord", 9), "HJH2 p25-26 (pr 18-19); " + NOT_CHECKED,
                      "conditional in the source ('if the earlier dasas are fruitless'); ranking differs at HJH2 p31 "
                      "(contradiction-register CR-V11)"),
                     ("10th lord", ("lord", 10), "HJH2 p25-26 (pr 18-19); " + NOT_CHECKED,
                      "conditional in the source ('if the earlier dasas are fruitless'); ranking differs at HJH2 p31 "
                      "(contradiction-register CR-V11)")]},
    "career": {"house": 10, "page": "p258",
               "karaka": [("Su", "HJH2 Charts 118, 155, 201 ('karaka Sun'), p260; " + NOT_CHECKED, None),
                          ("Ju", "HJH2 p430 (Bhavartha Ratnakara table: Jupiter karaka of the 10th); " + NOT_CHECKED,
                           "a second karaka reading (contradiction-register CR-V09); kept beside the Sun, not merged")],
               "extras": [
                   ("lagna lord", ("lord", 1), "question-trees.md §5 (" + SKILL_ONLY + ")", None),
                   ("navamsa dispositor of the 10th lord", ("d9lord", 10),
                    "PD V.1-8; HJH2 p253, p267 (topic-career-money.md §3); " + NOT_CHECKED, None)]},
    "finance": {"house": 11, "page": "p375",
                "karaka": [("Ju", "HJH2 p392-393 (pr 385-386): Jupiter (Dhanakaraka) as karaka of gains; "
                            + NOT_CHECKED, None)],
                "extras": [
                    ("2nd lord", ("lord", 2), "HJH2 p393 (pr 386): the 11th 'necessarily comprises the 2nd'; "
                     + NOT_CHECKED, None),
                    ("planet in the 2nd", ("occupants", 2), "HJH2 p393 (pr 386); " + NOT_CHECKED, None),
                    ("planet aspecting the 2nd", ("aspecting", 2), "HJH2 p393 (pr 386); " + NOT_CHECKED, None)]},
    "relocation": {"house": 9, "page": "p196, p225 (pr 218)", "karaka": [],
                   "extras": [
                       ("12th lord", ("lord", 12), "HJH2 p225 (pr 218), p464-465; " + NOT_CHECKED,
                        "the source says 'the 12th house'; read here as its lord and occupants"),
                       ("planet in the 12th", ("occupants", 12), "HJH2 p225 (pr 218); " + NOT_CHECKED,
                        "the source says 'the 12th house'; read here as its lord and occupants"),
                       ("4th lord (a residence change touches the 4th)", ("lord", 4),
                        "HJH2 p225 via topic-travel-education-health-life.md §1; " + NOT_CHECKED, None),
                       ("Rahu", ("planet", "Ra"), "question-trees.md §7 (" + SKILL_ONLY + ")", None)]},
    "education": {"house": 4, "page": "p20-21 (pr 13-14) applied to the 4th",
                  "karaka": [("Me", "topic-travel-education-health-life.md §2 (" + SKILL_ONLY + ")", None),
                             ("Ju", "topic-travel-education-health-life.md §2 (" + SKILL_ONLY + ")", None)],
                  "extras": [
                      ("5th lord", ("lord", 5), "PD XVI.15 via topic-travel-education-health-life.md §2; "
                       + NOT_CHECKED, "the topic file names houses 4, 5 and 9; the (a)-(g) list runs on the 4th"),
                      ("9th lord (higher study)", ("lord", 9), "topic-travel-education-health-life.md §2 ("
                       + SKILL_ONLY + ")", "the topic file names houses 4, 5 and 9; the (a)-(g) list runs on the 4th")]},
    "children": {"house": 5, "page": "p20-21 (pr 13-14) applied to the 5th",
                 "karaka": [("Ju", "PM2 p84 (XIX.83); topic-home-family-children.md §1; " + NOT_CHECKED, None)],
                 "extras": [
                     ("lagna lord", ("lord", 1), "PM2 p84 (XIX.83); " + NOT_CHECKED, None),
                     ("navamsa dispositor of the 5th lord", ("d9lord", 5), "PM2 p84 (XIX.83); " + NOT_CHECKED, None),
                     ("navamsa dispositor of Jupiter", ("d9lord_of", "Ju"), "PM2 p84 (XIX.83); " + NOT_CHECKED, None),
                     ("7th lord", ("lord", 7), "PM2 p84 (XIX.83); " + NOT_CHECKED, None)]},
}
THEME_ONLY = {"children": "Theme network only (topic-home-family-children.md output rule): it describes the subject, "
                          "it is never laid over dates, so activation and retrospective refuse it."}
HASHED = ("chart", "topic", "house", "entries", "planets")
ORD = {1: "lagna", 2: "2nd", 3: "3rd"}


def _ord(h):
    return ORD.get(h, f"{h}th")


def _d9lord(F, p):
    d9 = F.get(f"F.{p}.d9")
    return SIGN_LORD[SIGNS.index(d9)] if d9 else None


def _pick(F, rule):
    kind, x = rule
    if kind == "planet":
        return [x] if f"F.{x}.sign" in F else []
    if kind == "lord":
        return [F[f"F.H{x}.lord"]]
    if kind == "disp":
        return [F[f"F.{F[f'F.H{x}.lord']}.dispositor"]]
    if kind == "d9lord":
        return [q for q in [_d9lord(F, F[f"F.H{x}.lord"])] if q]
    if kind == "d9lord_of":
        return [q for q in [_d9lord(F, x)] if q]
    if kind == "occupants":
        return list(F[f"F.H{x}.occupants"])
    if kind == "aspecting":
        return list(F[f"F.H{x}.aspected_by"])
    raise ValueError(rule)


def digest(net):
    return "sha256:" + hashlib.sha256(json.dumps({k: net[k] for k in HASHED}, sort_keys=True,
                                                 separators=(",", ":")).encode()).hexdigest()


def preset(F, topic, chart):
    """Raman's (a)-(g) significators for the topic's house plus the topic extras, every entry with its source. `F` is
    chart_facts.facts_json(...)["facts"]; `chart` an opaque chart key bound into the hash."""
    if topic not in PRESETS:
        raise ValueError(f"topic must be one of {', '.join(PRESETS)}")
    P, h, flags = PRESETS[topic], PRESETS[topic]["house"], []
    L, raman = F[f"F.H{h}.lord"], RAMAN.format(p=PRESETS[topic]["page"])
    rows = [(f"(a) {_ord(h)} lord", [L], raman, None),
            (f"(b) aspecting the {_ord(h)}", F[f"F.H{h}.aspected_by"], raman, None),
            (f"(c) in the {_ord(h)}", F[f"F.H{h}.occupants"], raman, None),
            (f"(d) aspecting the {_ord(h)} lord", F[f"F.{L}.aspected_by"], raman, None),
            (f"(e) associated with the {_ord(h)} lord", F[f"F.{L}.with"], raman,
             "association read as the same sign; exchanges are not added")]
    if f"F.M{h}.lord" in F:
        rows.append((f"(f) {_ord(h)} lord from the Moon", [F[f"F.M{h}.lord"]], raman, None))
    else:
        flags.append("Moon missing: (f) (the house lord counted from the Moon) not computed")
    rows += [("(g) karaka", [p], src, var) for p, src, var in P["karaka"]]
    if not P["karaka"]:
        flags.append(f"no karaka for {topic} in the sources read: (g) left empty")
    rows += [(role, _pick(F, rule), src, var) for role, rule, src, var in P["extras"]]
    entries = [{"planet": p, "role": role, "source": src, "page_checked": False, **({"variant": var} if var else {})}
               for role, ps, src, var in rows for p in ps]
    flags += sorted({f"{e['role']}: {e['source']}" for e in entries if SKILL_ONLY in e["source"]})
    net = {"chart": chart, "topic": topic, "house": h, "entries": entries,
           "planets": sorted({e["planet"] for e in entries})}
    return net | {"hash": digest(net), "flags": flags, **({"note": THEME_ONLY[topic]} if topic in THEME_ONLY else {})}


def custom(planets, chart, F):
    bad = [p for p in planets if f"F.{p}.sign" not in F]
    if bad or not planets:
        raise ValueError("custom network: give one or more chart planets (Su Mo Ma Me Ju Ve Sa Ra Ke)")
    entries = [{"planet": p, "role": "caller-supplied", "source": "none (caller-supplied, unsourced)",
                "page_checked": False} for p in dict.fromkeys(planets)]
    net = {"chart": chart, "topic": "custom", "house": None, "entries": entries, "planets": sorted({*planets})}
    return net | {"hash": digest(net), "flags": ["custom network: no source support for any entry"]}


def verify(net, chart):
    """Refuse a network that changed after it was frozen or that belongs to another chart; returns a private copy."""
    if not isinstance(net, dict) or "hash" not in net or any(k not in net for k in HASHED):
        raise ValueError("network: pass the object returned by the network builder (topic_network), unchanged")
    if digest(net) != net["hash"]:
        raise ValueError("network changed after it was frozen (hash differs): build a new network before looking "
                         "at any dates, and do not edit it afterwards")
    if net["chart"] != chart:
        raise ValueError("network was frozen for another chart")
    if net["topic"] in THEME_ONLY:
        raise ValueError(THEME_ONLY[net["topic"]])
    return copy.deepcopy(net)


def roles(F, p, net):
    """Natal roles of one planet from chart_facts ids; Moon-frame values are None when the Moon is missing."""
    moon = F.get("F.Mo.sign")
    return {"house_from_lagna": F[f"F.{p}.house"], "owns_from_lagna": F[f"F.{p}.owns"],
            "house_from_moon": None if moon is None else (SIGNS.index(F[f"F.{p}.sign"]) - SIGNS.index(moon)) % 12 + 1,
            "owns_from_moon": None if moon is None else [h for h in range(1, 13) if F[f"F.M{h}.lord"] == p],
            "sign": F[f"F.{p}.sign"], "d9": F[f"F.{p}.d9"], "d10": F[f"F.{p}.d10"], "dignity": F[f"F.{p}.dignity"],
            "d9_dignity": F[f"F.{p}.d9_dignity"], "retro": F[f"F.{p}.retro"], "combust": F[f"F.{p}.combust"],
            "network_roles": [{"role": e["role"], "source": e["source"], **({"variant": e["variant"]} if "variant" in e else {})}
                              for e in net["entries"] if e["planet"] == p]}


def segments(periods, start, end, level):
    """AD (or PD) segments of nested Vimshottari rows overlapping [start, end)."""
    out = []
    for md in periods:
        for ad in md["sub"]:
            for row in (ad["sub"] if level == "pd" else [ad]):
                if row["start"] < end and row["end"] > start:
                    out.append({"md": md["lord"], "ad": ad["lord"], **({"pd": row["lord"]} if level == "pd" else {}),
                                "start": row["start"], "end": row["end"]})
    return out


def table(F, net, periods, start, end, level, contacts, stays, stations, av, episodes=()):
    """One row per segment: its lords' natal roles, and the slow contacts, Ju/Sa sign stays and stations inside it that
    touch a period lord or a network planet. `stays` = engine.transit_sign_aspects rows; `stations` rows carry the
    station planet's sign; `av` = strength.ashtakavarga(c); `episodes` = transit.station_episodes() rows."""
    natal_sign = {k[2:4]: v for k, v in F.items() if k.endswith(".sign") and len(k) == 9}
    moon = F.get("F.Mo.sign")
    rows = []
    for s in segments(periods, start, end, level):
        lords = list(dict.fromkeys(s[k] for k in ("md", "ad", "pd") if k in s))
        watch = {**{p: "network" for p in net["planets"]}, **{p: "period lord" for p in lords}}
        inside = lambda d, s=s: s["start"] <= d < s["end"]
        ss = []
        for st in stays:
            if not (st["from"] < s["end"] and st["to"] > s["start"]):
                continue
            idx = SIGNS.index(st["sign"])
            signs = [(SIGNS.index(F["F.asc.sign"]) + h - 1) % 12 for h in st["houses_from_lagna"]]
            ss.append({**st, "touches": sorted(p for p in watch if natal_sign.get(p) and SIGNS.index(natal_sign[p]) in signs),
                       "topic_house_touched": None if net["house"] is None else {
                           "from_lagna": net["house"] in st["houses_from_lagna"],
                           "from_moon": None if moon is None else net["house"] in st["houses_from_moon"]},
                       "bav": av["bav"][st["planet"]][idx], "sav": av["sav"][idx]})
        rows.append({**s, "lords": {p: roles(F, p, net) for p in lords},
                     "lords_in_network": [p for p in lords if p in net["planets"]],
                     "contacts": [c | {"touches": watch[c["natal"]]} for c in contacts
                                  if inside(c["date"]) and c["natal"] in watch],
                     "ju_sa_sign_stays": ss,
                     "stations": [x | {"natal_in_sign": sorted(p for p in watch if natal_sign.get(p) == x["sign"])}
                                  for x in stations if inside(x["date"])],
                     "station_episodes": [e | {"touches": watch[e["natal"]]} for e in episodes
                                          if e["natal"] in watch and inside(e["stations"][0]["date"])]})
    return rows


def month_bounds(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    nxt = f"{y + (m == 12):04d}-{m % 12 + 1:02d}-01"
    return f"{ym}-01", nxt


def event_row(ev, net, periods, contacts, stations):
    """Period and contact state for one (category, YYYY-MM) event against its frozen network. Consistency rule: an MD
    or AD lord running at any time in the event month is in the network; contacts and stations are shown, not counted."""
    a, b = month_bounds(ev["month"])
    ads = segments(periods, a, b, "ad")
    pds = segments(periods, a, b, "pd")
    lords = sorted({x[k] for x in ads for k in ("md", "ad")} & set(net["planets"]))
    watch = set(net["planets"])
    return {"category": ev["category"], "month": ev["month"], "network_hash": net["hash"],
            "periods": [f"{x['md']}-{x['ad']} {x['start']} to {x['end']}" for x in ads],
            "pratyantar": [f"{x['md']}-{x['ad']}-{x['pd']} {x['start']} to {x['end']}" for x in pds],
            "period_lords_in_network": lords, "consistent": bool(lords),
            "contacts_within_window": [c | {"natal_in_network": c["natal"] in watch} for c in contacts],
            "stations_within_window": stations}
