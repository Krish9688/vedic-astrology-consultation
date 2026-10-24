"""Compatibility facts from two charts: the Moon-sign and birth-star counts of Prasna Marga ch. XXI, each with the
verse that reads it. Rule lookup only: no verdict (the author assigns no unit scores, PM2 p107), and the verses
disagree with each other, so every matching reading is listed with its authority.

`kootas` adds four rule-fixed Ashtakoota items (tara, bhakoot, graha maitri, nadi) from Muhurtacintamani ch. 6 and
its commentary, per research/KB/R3-ashtakoota.md: each item's points with its maximum and source, exception
conditions beside it (never applied), and no sum (owner decision 2026-10-23, P8-2N1).

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
                "agreement (tables not in the source maps); the 36-point Ashtakoota sum and vashya, yoni, gana, varna (see "
                "kootas.not_computed); "
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
           "note": NOTE, "not_computed": NOT_COMPUTED, "kootas": kootas(girl, boy)}
    if "asc" in girl and "asc" in boy:
        four = lambda c: {int(c["asc"] // 30), E.varga(c["asc"], 9), int(c["moon"] // 30), E.varga(c["moon"], 9)}
        out["fixed_four"] = {"holds": four(girl) <= FIXED_FOUR and four(boy) <= FIXED_FOUR,
                             "rule": "XXI.11: both partners' lagna, lagna navamsa, Moon and Moon navamsa in Virgo, "
                                     "Scorpio, Taurus or Leo: no issue"}
    return out


# --- Ashtakoota: the four rule-fixed kootas (R3 §3.3, 3.5, 3.7, 3.8, §4, §10.4). Facts, never summed. ---------------
_SCAN = "kb-source-researcher's reading of the scan; not page-checked"
_MC = "Muhurtacintamani ch. 6 (Sanskrit mula, archive.org muhurt-chintamani)"
_MCJ = "MCJ = Muhurtacintamani with Piyushadhara and Joshi's Pitambara, 2nd ed. 1979"
KOOTA_VARIANT = "MC-Piyushadhara-Joshi1979"
NADI = {n: "adi" for n in (0, 5, 6, 11, 12, 17, 18, 23, 24)} | {n: "madhya" for n in (1, 4, 7, 10, 13, 16, 19, 22, 25)}
KOOTA_NOT_COMPUTED = {
    "vashya": "sources conflict: four-group MCJ p332, five-group 1905/1939 prints, onlinejyotish, the sign-list "
              "method of Raman 1948 p88 (R3 §3.2, §10.4)",
    "yoni": "14x14 point tables conflict: MCJ p335 vs the 1905 print p106 vs NAKS p529-530 (R3 §3.4, §10.4)",
    "gana": "point tables conflict: MCJ p340 vs the 1905/1933/1939 prints (one cell) vs onlinejyotish (transposed) "
            "(R3 §3.6, §10.4)",
    "varna": "sign schemes conflict (MC 6.22 vs Raman 1948 p90 vs nakshatra basis in PM2 XXI.27) and equal varna "
             "is 1 or 1/2 (R3 §3.1)",
}
KOOTA_NOTE = ("Traditional points of one school for four of the eight items, each with its own maximum; they are not "
              "added up, carry no threshold, and are not evidence about a relationship (R3 calculation note). "
              "Exception conditions are listed beside the points and never change them; the sources disagree on them.")


def _maitri(a, b):
    """Daivajnamanohara rule (MCJ p337) over the engine's natural table: reproduces the MCJ p338 chakra (R3 §3.5)."""
    if a == b:
        return 5
    rel = sorted((_relation(a, b), _relation(b, a)))
    return {("friend", "friend"): 5, ("friend", "neutral"): 4, ("neutral", "neutral"): 3, ("enemy", "friend"): 1,
            ("enemy", "neutral"): 0.5, ("enemy", "enemy"): 0}[tuple(rel)]


def kootas(girl, boy):
    """Tara, bhakoot, graha maitri and nadi for girl (bride) and boy (groom): dicts with a sidereal 'moon' longitude."""
    who = {"girl": girl, "boy": boy}
    s = {k: int(c["moon"] // 30) for k, c in who.items()}
    n = {k: E.nak(c["moon"])[2] for k, c in who.items()}
    pada = {k: E.nak(c["moon"])[1] for k, c in who.items()}
    lord = {k: SIGN_LORD[s[k]] for k in who}
    d9lord = {k: SIGN_LORD[E.varga(c["moon"], 9)] for k, c in who.items()}
    nadi = {k: NADI.get(n[k], "antya") for k in who}

    # Tara (max 3): MC 6.24 count both ways, remainder after /9 of 3, 5 or 7 unfavourable; DM via Piyushadhara: 1 1/2
    # per favourable direction. The two counts sum to 29, so only 3 or 1 1/2 occur (R3 §3.3).
    tc = {"girl_to_boy": _count(n["girl"], n["boy"], 27), "boy_to_girl": _count(n["boy"], n["girl"], 27)}
    fav = {k: c % 9 not in (3, 5, 7) for k, c in tc.items()}
    tara = {"max": 3, "points": 1.5 * sum(fav.values()),
            "inputs": {k: E.NAKS[n[k]] for k in who}, "counts": tc, "remainders": {k: c % 9 for k, c in tc.items()},
            "favourable": fav,
            "rule": "count inclusively from each partner's star to the other's and divide by 9; remainder 3, 5 or 7 "
                    "is unfavourable; 1 1/2 points for each favourable direction",
            "source": f"{_MC} v. 24; {_MCJ} p333 (Daivajnamanohara via Piyushadhara; chakra); {_SCAN}",
            "variants": [{"reading": "Kashyapa (quoted MCJ p332): count from the bride's star only",
                          "girl_to_boy_favourable": fav["girl_to_boy"],
                          "points": "not stated for this reading in R3"}]}
    if n["girl"] == n["boy"]:
        tara["same_star"] = ("Narada forbids the janma (same) star; the author defers it to the same-sign/same-star "
                             "rule (MCJ p333; see nadi.exception_conditions)")

    # Bhakoot (max 7): MC 6.31, MCJ p341 chakra: 0 for 2/12, 5/9, 6/8, else 7. Symmetric.
    d = _count(s["girl"], s["boy"], 12)
    rd = _count(s["boy"], s["girl"], 12)
    bk = {"max": 7, "points": 0 if d in (2, 12, 5, 9, 6, 8) else 7,
          "inputs": {k: E.SIGNS[s[k]] for k in who}, "distance": f"{d}/{rd}",
          "rule": "2/12, 5/9 and 6/8 sign distances get 0; same sign, 1/7, 3/11 and 4/10 get 7",
          "source": f"{_MC} v. 31; {_MCJ} p341 chakra; {_SCAN}",
          "variants": [{"reading": "directional sign count (Raman 1948 pp84-85; PM2 XXI.4-14)",
                        "where": "sign_count and sign_count_readings in this output"}]}
    lords_friends = _relation(lord["girl"], lord["boy"]) == _relation(lord["boy"], lord["girl"]) == "friend"
    if bk["points"] == 0:
        dosha_kind = {2: "2/12", 12: "2/12", 5: "5/9", 9: "5/9", 6: "6/8", 8: "6/8"}[d]
        conds = [
            {"condition": "the Moon-sign lords are the same", "holds": lord["girl"] == lord["boy"],
             "readings": ["MC 6.32 with Piyushadhara (MCJ pp341-348): a remedy, but only with nadi purity",
                          "Raman 1948 p85: cancels the rasi-kuta evil, no nadi condition",
                          "Narada (quoted MCJ p348): rescues 2/12 and 5/9, never 6/8"]},
            {"condition": "the Moon-sign lords are mutual friends (natural table)", "holds": lords_friends,
             "readings": ["MC 6.32 with Piyushadhara (MCJ pp341-348): a remedy, but only with nadi purity",
                          "Raman 1948 p85: cancels, no nadi condition",
                          "Narada (quoted MCJ p348): rescues 2/12 and 5/9, never 6/8"]},
            {"condition": "tara favourable both ways", "holds": all(fav.values()),
             "readings": ["MC 6.32 with Piyushadhara (MCJ pp341-348): a remedy, but only with nadi purity"]},
            {"condition": "nadi purity (different nadis)", "holds": nadi["girl"] != nadi["boy"],
             "readings": ["Piyushadhara (MCJ pp341-348): required by each of the five remedies",
                          "Raman 1948 p85: not required"]},
        ]
        if d == 6:
            conds.append({"condition": "bride in an even sign with the groom 6th from her",
                          "holds": s["girl"] % 2 == 1,
                          "readings": ["Pitambara (MCJ p342): no 6/8 dosha", "PM2 XXI.5: reject the 6th"]})
        if dosha_kind == "2/12":
            conds.append({"condition": "2/12 pair: sign parity", "holds": None,
                          "signs_even": {k: s[k] % 2 == 1 for k in who},
                          "readings": ["Vasishtha (quoted MCJ p343): 2/12 is good from even signs, poverty from "
                                       "odd ones (whose sign is counted from is not settled in R3)"]})
        bk["dosha"] = dosha_kind
        bk["exception_conditions"] = conds
        bk["exceptions_not_evaluated"] = [
            "navamsa lords strong and friendly when the sign lords are enemies (MCJ pp341-348): strength not defined",
            "sign vashya (MCJ pp341-348): vashya not computed",
            "Garga (Jyotirnibandha, quoted MCJ p346): three conditions for 6/8, two for 2/12 and 5/9, not listed in R3"]

    # Graha maitri (max 5): DM rule (MCJ p337) over the natural table = MCJ p338 chakra.
    gm = {"max": 5, "points": _maitri(lord["girl"], lord["boy"]), "inputs": dict(lord),
          "relations": {"girl_lord_sees_boy_lord_as": _relation(lord["girl"], lord["boy"]),
                        "boy_lord_sees_girl_lord_as": _relation(lord["boy"], lord["girl"])},
          "rule": "same lord or mutual friends 5; friend and neutral 4; both neutral 3; friend and enemy 1; neutral "
                  "and enemy 1/2; mutual enemies 0 (natural friendship, astro/calc/strength.py NATURAL)",
          "source": f"{_MC} vv. 27-28; {_MCJ} pp337-338 (rule and chakra); {_SCAN}",
          "variants": [{"reading": "PM2 XXI.19 gives a different friendship list (e.g. the Sun's only friend "
                                   "Jupiter); source map sourcemaps/PM2.md §7, not page-checked",
                        "points": "not computed"}],
          "navamsa_lords": {"inputs": dict(d9lord), "points_by_same_rule": _maitri(d9lord["girl"], d9lord["boy"]),
                            "readings": ["MC 6.33 and Raman 1948 p87: navamsa-lord friendship may substitute for "
                                         "sign-lord friendship", "Raman 1948 p87: temporary friendship is not used"]}}
    if gm["points"] < 5:
        gm["exception_conditions"] = [{"condition": "bhakoot gets 7", "holds": bk["points"] == 7,
                                       "readings": ["MC 6.33: a good bhakoot removes planetary enmity"]}]
    if bk["points"] == 0:
        bk["exception_conditions"].append({"condition": "graha maitri: lords friends", "holds": gm["points"] == 5,
                                           "readings": ["MC 6.33: planetary friendship removes a bad bhakoot"]})

    # Nadi (max 8): MC 6.34 lists; same nadi 0, different 8.
    nd = {"max": 8, "points": 0 if nadi["girl"] == nadi["boy"] else 8,
          "inputs": {k: {"nakshatra": E.NAKS[n[k]], "nadi": nadi[k]} for k in who},
          "rule": "adi, madhya or antya by nakshatra; same nadi 0, different 8",
          "source": f"{_MC} v. 34; agrees with Raman 1948 pp91-92 and the NAKS dosha column (sourcemaps/NAKS_part1.md, "
                    f"not page-checked); {_SCAN}",
          "variants": [{"reading": "pada-based nadi (Raman 1948 p92) and three-, four- and five-column schemes "
                                   "(MCJ pp343-344)", "points": "not computed (unresolved in R3)"}]}
    if nd["points"] == 0:
        if nadi["girl"] == "madhya":
            nd["note"] = "MC 6.34 names the same middle nadi as the worst case"
        nd["exception_conditions"] = [
            {"condition": "same sign, different stars", "holds": s["girl"] == s["boy"] and n["girl"] != n["boy"],
             "readings": ["MC 6.35 (6.37 in MCJ): removes nadi and gana dosha"]},
            {"condition": "same star, different signs", "holds": n["girl"] == n["boy"] and s["girl"] != s["boy"],
             "readings": ["MC 6.35 (6.37 in MCJ): removes nadi and gana dosha"]},
            {"condition": "same star, different padas", "holds": n["girl"] == n["boy"] and pada["girl"] != pada["boy"],
             "readings": ["MC 6.35 (6.37 in MCJ): auspicious",
                          "PM2 XXI.15-16: same star barred for twelve stars; 'fear from poison' (star_readings)"]}]
        nd["exceptions_not_evaluated"] = [
            "exempt-star lists of Narada Samhita and Piyushadhara (via onlinejyotish, secondary; they differ)",
            "Muhurta Ganapati: friendly lords cancel (via onlinejyotish, secondary)",
            "Raman 1948 p93: conditions continue on a page missing from the scan",
            "MCJ p349: regional permission south of the Godavari (reading uncertain)"]

    return {"variant": KOOTA_VARIANT, "roles": "girl = bride, boy = groom (the tradition's roles)",
            "padas": pada, "tara": tara, "bhakoot": bk, "graha_maitri": gm, "nadi": nd,
            "not_computed": KOOTA_NOT_COMPUTED, "note": KOOTA_NOTE,
            "research": "research/KB/R3-ashtakoota.md, ledger KB-F304, F308, F310-F312, F318"}
