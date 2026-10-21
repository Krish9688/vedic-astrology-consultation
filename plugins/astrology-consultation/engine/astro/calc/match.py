"""Compatibility facts from two charts: the Moon-sign and birth-star counts of Prasna Marga ch. XXI, each with the
verse that reads it. Rule lookup only: no points and no verdict (the author assigns no unit scores, PM2 p107), and
the verses disagree with each other, so every matching reading is listed with its authority.

Source: PM2 (Raman's translation) ch. XXI, p96-107, from the project's page-cited source map (not page-checked).
Not computed, because their tables are not in the source maps: vasya, varna, nakshatra sex, gana, gotra, bird and
animal yoni, vedha, bhuta, rajju, ashtakavarga agreement; nor the 36-point Ashtakoota (no source in the library).
"""
from __future__ import annotations

from . import engine as E
from .strength import NATURAL, SIGN_LORD

SIGN_RULES = [  # (verse, applies(r, girl_sign), reading); r = boy's sign counted from the girl's, 1 = same sign
    ("XXI.4 (Sarvasiddhi)", lambda r, g: 2 <= r <= 6, "reject a boy in the 2nd-6th"),
    ("XXI.4 (Sarvasiddhi)", lambda r, g: r == 1, "the same sign is fine if the nakshatra differs"),
    ("XXI.5", lambda r, g: r in (6, 8) and g % 2 == 0, "odd-sign girl: the 6th or 8th is optional"),
    ("XXI.5", lambda r, g: r in (6, 8) and g % 2 == 1, "even-sign girl: reject the 6th, accept the 8th"),
    ("XXI.6 (Madhavacharya)", lambda r, g: 2 <= r <= 6,
     "2nd loss of money, 3rd sorrow, 4th quarrels, 5th loss of children, 6th disease, danger, separation"),
    ("XXI.7-8 (Brihaspati)", lambda r, g: r in (6, 8),
     "ruin unless both signs share a lord or the lords are friends; vasya without vedha makes 6/8 acceptable"),
    ("XXI.9-10", lambda r, g: r in (2, 5), "incompatible"),
    ("XXI.9-10", lambda r, g: r == 7, "very good even if the lords are enemies"),
    ("XXI.9-10", lambda r, g: r in (6, 8), "separation, quarrel or death; enemy lords or vedha aggravate, "
                                            "the same lord with vasya cancels"),
    ("XXI.9-10", lambda r, g: r in (2, 12), "poverty"),
    ("XXI.14 (Muhurtha Sangraha)", lambda r, g: 7 <= r <= 12, "acceptable"),
    ("XXI.14 (Muhurtha Sangraha)", lambda r, g: r == 6, "ordinary"),
    ("XXI.14 (Muhurtha Sangraha)", lambda r, g: r == 4, "acceptable if the other items agree"),
    ("XXI.16", lambda r, g: r == 7, "mutual 7th: loving"),
]
SAME_STAR_BARRED = {"Jyeshtha", "Mula", "PurvaAshadha", "Pushya", "Ashlesha", "Magha", "Hasta", "Rohini", "Dhanishtha",
                    "Shatabhisha", "Ardra", "Bharani"}                                   # XXI.15
SIGN_YONI = {"bird": {9, 11}, "reptile": {3, 7}, "animal": {0, 1, 4, 9}, "human": {2, 5, 6, 10, 8}}   # XXI.12
FIXED_FOUR = {5, 7, 1, 4}                         # Virgo, Scorpio, Taurus, Leo (XXI.11)
NOT_COMPUTED = ("vasya, varna, nakshatra sex, gana, gotra, bird and animal yoni, vedha, bhuta, rajju, ashtakavarga "
                "agreement (tables not in the source maps); the 36-point Ashtakoota (no source in the library); "
                "Kuja dosha (run chart_facts on each chart: BPHS 80.47-49 cancels it when both have it)")
NOTE = ("PM2 counts from the girl's Moon to the boy's; both directions are given. Rule lookups, not a verdict: the "
        "author asks for at least janma rasi, rasi lord, vasya, mahendra and yoni (XXI.64-69; vasya and the star "
        "yoni are not computed here), Raman holds that the two charts' own structure matters more (PM2 p107, HJH2 "
        "p66), and mutual love permits the marriage even without agreement (XXI.54-55).")


def _count(a, b, n):
    return (b - a) % n + 1


def _relation(p, q):
    if p == q:
        return "same planet"
    friends, enemies = NATURAL[p]
    return "friend" if q in friends else "enemy" if q in enemies else "neutral"


def facts(girl, boy):
    """girl, boy: dicts with sidereal 'moon' and optional 'asc' longitudes (degrees)."""
    gs, bs = int(girl["moon"] // 30), int(boy["moon"] // 30)
    gn, bn = E.nak(girl["moon"])[2], E.nak(boy["moon"])[2]      # engine.nak: exact boundaries fall forward (EPS)
    r, s = _count(gs, bs, 12), _count(gn, bn, 27)
    rb, sb = _count(bs, gs, 12), _count(bn, gn, 27)
    gl, bl = SIGN_LORD[gs], SIGN_LORD[bs]
    star = []
    if s == 1:
        star.append(("XXI.15", f"same star: permissible except {', '.join(sorted(SAME_STAR_BARRED))}"
                     + (" - this star is one of them" if E.NAKS[gn] in SAME_STAR_BARRED else "")))
        star.append(("XXI.16", "same star: 'fear from poison'"))
    elif r == 1:
        star.append(("XXI.16", "same sign, different star: good"))
    if s in (3, 5, 6, 7):
        star.append(("XXI.21-22 (dina)", "avoid a boy in the 3rd, 6th or 7th star from the girl's; the 5th is worse"))
    if s in (4, 7, 10):
        star.append(("XXI.24", "4th, 7th or 10th star: well-being"))
    if sb == 4:
        star.append(("XXI.25", "girl 4th from the boy: mahendra (wealth)"))
    if sb == 7:
        star.append(("XXI.25", "girl 7th from the boy: upendra (children)"))
    if s > 15:
        star.append(("XXI.26", "more than 15 stars from the girl's to the boy's: streedeergha, very good"))
    pada_of = lambda x: int(x / (10 / 3) + E.EPS) % 108
    pada = _count(pada_of(girl["moon"]), pada_of(boy["moon"]), 108)
    if pada in (88, 108):
        star.append(("XXI.23", f"the boy's Moon pada is the {pada}th from the girl's: evil"))
    yoni = {k: [y for y, signs in SIGN_YONI.items() if x in signs] for k, x in (("girl", gs), ("boy", bs))}
    out = {"girl": {"moon_sign": E.SIGNS[gs], "nakshatra": E.NAKS[gn], "sign_lord": gl},
           "boy": {"moon_sign": E.SIGNS[bs], "nakshatra": E.NAKS[bn], "sign_lord": bl},
           "sign_count": {"girl_to_boy": r, "boy_to_girl": rb}, "star_count": {"girl_to_boy": s, "boy_to_girl": sb},
           "pada_count_girl_to_boy": pada,
           "sign_count_readings": [{"verse": v, "says": t} for v, f, t in SIGN_RULES if f(r, gs)],
           "star_readings": [{"verse": v, "says": t} for v, t in star],
           "sign_lords": {"same": gl == bl, "girl_lord_sees_boy_lord_as": _relation(gl, bl),
                          "boy_lord_sees_girl_lord_as": _relation(bl, gl),
                          "rule": "XXI.17-20: lords friendly or the same is acceptable; friendship by the XXI.20 "
                                  "(Satyacharya) rule, the engine's natural table; XXI.19 gives a different list"},
           "sign_yoni": {**yoni, "rule": "XXI.12-13: same yoni good; human with animal fair; human with reptile or "
                                         "bird reject. The map lists Capricorn under both bird and animal",
                         "ambiguous": any(len(v) > 1 for v in yoni.values())},
           "note": NOTE, "not_computed": NOT_COMPUTED}
    if "asc" in girl and "asc" in boy:
        four = lambda c: {int(c["asc"] // 30), E.varga(c["asc"], 9), int(c["moon"] // 30), E.varga(c["moon"], 9)}
        out["fixed_four"] = {"holds": four(girl) <= FIXED_FOUR and four(boy) <= FIXED_FOUR,
                             "rule": "XXI.11: both partners' lagna, lagna navamsa, Moon and Moon navamsa in Virgo, "
                                     "Scorpio, Taurus or Leo: no issue"}
    return out
