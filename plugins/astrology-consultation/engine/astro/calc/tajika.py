"""Tajika (Tajaka) annual chart core, as taught in PVR ch. 27-28 and 31 (Narasimha Rao, "Vedic Astrology: An Integrated
Approach"; page-cited source map, not page-checked): the solar return (varsha pravesh) at the birthplace, day or night
year, muntha, harsha bala, pancha vargeeya bala, the five year-lord candidates with their Tajika aspect on the annual
lagna, sahams, and the Mudda and Patyayini dashas (timing tools inside an annual chart that never stand alone).
Calculation and rule lookup only.

PVR p377: Tajika has no reference in Parasara or Jaimini; its oldest respected source, Tajaka Neelakanthi, is not in
the project library. Pancha vargeeya bala: PVR states no Sun-Mercury relation, so the owner's default (Sun and Mercury
enemies, Kesava's blocs) decides the year lord and the 'friends' variant is printed beside it. Not computed: Varsha
Narayana dasha; the sahams that need house cusps (the cusp system is not stated).
"""
from __future__ import annotations

from . import engine as E
from .strength import EXALT, SIGN_LORD

NOT_COMPUTED = ("Varsha Narayana dasha; Karyasiddhi and the sahams "
                "that need house cusps (Mrityu, Paradesa, Artha, Santapa, Apamrityu, Labha: the cusp system is not "
                "stated)")
SIDEREAL_YEAR = 365.256363
PLANETS = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")
MASCULINE, FEMININE = {"Su", "Ma", "Ju"}, {"Mo", "Me", "Ve", "Sa"}
HARSHA_HOUSE = {"Su": 9, "Mo": 3, "Ma": 6, "Me": 1, "Ju": 11, "Ve": 5, "Sa": 12}               # PVR p387-388
TRIRASI = [("Su", "Ju"), ("Ve", "Mo"), ("Sa", "Me"), ("Ve", "Ma"), ("Ju", "Su"), ("Mo", "Ve"), ("Me", "Sa"),
           ("Ma", "Ve"), ("Sa", "Sa"), ("Ma", "Ma"), ("Ju", "Ju"), ("Mo", "Mo")]               # Table 73: (day, night)
ASPECT = {5: "trine (strong benefic)", 9: "trine (strong benefic)", 3: "sextile (weak benefic)",
          11: "sextile (weak benefic)", 4: "square (weak malefic)", 10: "square (weak malefic)",
          1: "conjunction (strong malefic)", 7: "opposition (strong malefic)", 2: "semi-sextile (neutral)",
          12: "semi-sextile (neutral)"}                                                     # PVR p387
# Table 74 (PVR p394-395): name -> (A, B, C, same by day and night); saham = A - B + C by day, B - A + C by night.
SAHAMS = {"Punya": ("Mo", "Su", "Lg", False), "Vidya": ("Su", "Mo", "Lg", False), "Yasas": ("Ju", "Punya", "Lg", False),
          "Mitra": ("Ju", "Punya", "Ve", False), "Mahatmya": ("Punya", "Ma", "Lg", False),
          "Asha": ("Sa", "Ma", "Lg", False), "Samartha": ("Ma", "LgLord", "Lg", False),
          "Bhratri": ("Ju", "Sa", "Lg", True), "Gaurava": ("Ju", "Mo", "Su", False), "Pitri": ("Sa", "Su", "Lg", False),
          "Rajya": ("Sa", "Su", "Lg", False), "Matri": ("Mo", "Ve", "Lg", False), "Putra": ("Ju", "Mo", "Lg", False),
          "Jeeva": ("Sa", "Ju", "Lg", False), "Karma": ("Ma", "Me", "Lg", False), "Roga": ("Lg", "Mo", "Lg", False),
          "Kali": ("Ju", "Ma", "Lg", False), "Sastra": ("Ju", "Sa", "Me", False), "Bandhu": ("Me", "Mo", "Lg", False),
          "Paradara": ("Ve", "Su", "Lg", False), "Vanik": ("Mo", "Me", "Lg", False), "Vivaha": ("Ve", "Sa", "Lg", False),
          "Sraddha": ("Ve", "Ma", "Lg", False), "Preeti": ("Sastra", "Punya", "Lg", False),
          "Jadya": ("Ma", "Sa", "Me", False), "Vyapara": ("Ma", "Sa", "Lg", True), "Satru": ("Ma", "Sa", "Lg", False),
          "Jalapatana": ("CnMid", "Sa", "Lg", False), "Bandhana": ("Punya", "Sa", "Lg", False)}
MUDDA_ORDER = ("Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ke", "Ve")                           # Table 76, numbers 1-9
VIM_YEARS = dict(E.DASA)
PATYAYINI_YEAR = 365.2425                                     # PVR p410-411, as mapped (not the sidereal year)
# Pancha vargeeya bala (PVR p388-391; research/CALC/R4). Friendship: Kesava's two Tajika blocs, which reproduce PVR
# Example 118; no neutral relation exists in that scheme.
BLOC = {"Su", "Mo", "Ma", "Ju"}
# PVR Table 72 haddas (p390): per sign, (lord, end degree); a boundary degree belongs to the next hadda.
HADDA = [[(t[:2], float(t[2:])) for t in row.split()] for row in (
    "Ju6 Ve12 Me20 Ma25 Sa30", "Ve8 Me14 Ju22 Sa27 Ma30", "Me6 Ve12 Ju17 Ma24 Sa30", "Ma7 Ve13 Me19 Ju26 Sa30",
    "Ju6 Ve11 Sa18 Me24 Ma30", "Me7 Ve17 Ju21 Ma28 Sa30", "Sa6 Me14 Ju21 Ve28 Ma30", "Ma7 Ve11 Me19 Ju24 Sa30",
    "Ju12 Ve17 Me21 Ma26 Sa30", "Me7 Ju14 Ve22 Sa26 Ma30", "Me7 Ve13 Ju20 Ma25 Sa30", "Ve12 Ju16 Me19 Ma28 Sa30")]
# Owner's page check of PVR p388-393 and p64-65 (2026-10-24, CALC-F411, D-6): no neutral value, own rasi only (an
# exaltation sign is not own), Parashari D-3. The Sun-Mercury relation is not stated: label -> sun_mercury_friends.
PVB_DEFAULT = "Su-Me enemies (default)"
STRONG, VERY_STRONG = 10, 15                            # PVR p391 bands: 10-15 strong, 15-20 very strong
PVB_VARIANTS = {PVB_DEFAULT: False, "Su-Me friends": True}
PVB_UNSETTLED = ("PVR p388-393 states no Sun-Mercury relation (Raman's Varshaphala, the other source, is not in the "
                 "library): the default makes them enemies (Kesava's blocs) and the 'friends' variant is shown beside "
                 "it. Settled by the owner's check (2026-10-24): no neutral value, exaltation not counted as own, "
                 "Parashari drekkana")
SOURCES = {"return": "PVR p379-380: the moment the Sun returns to its natal sidereal longitude, for the birthplace",
           "muntha": "PVR p386: the Nth sign from the natal lagna (inclusive) in the Nth year",
           "harsha_bala": "PVR p387-388: four sources of 5 units",
           "year_lord": "PVR p391-393 (page-checked by the owner 2026-10-24, CALC-F412): candidates strong by pancha "
                        "vargeeya bala (>= 10, p391) with a benefic whole-sign Tajika aspect on the annual lagna, the "
                        "highest PVB winning; else the same with a malefic aspect; else a very strong candidate "
                        "(>= 15); else candidate 1. PVB uses the default convention, and the reason names the planet "
                        "the 'Su-Me friends' variant would choose when it differs",
           "sahams": "PVR p394-395 (Table 74): A - B + C by day, reversed at night unless the same for both; add 30° "
                     "when C is not on the zodiacal arc from the subtracted to the added point",
           "mudda": "PVR p411-412 (Table 76): Vimshottari compressed to 360 solar days (days = years x 3; a solar "
                    "day = the Sun moving 1°); first lord = natal Moon-nakshatra lord's number + completed years, "
                    "mod 9; balance from the natal Moon's nakshatra; PVR ranks it below Patyayini and Varsha Narayana. "
                    "PVR's own Example 122 dates fit a clock day instead (about 2 days earlier in mid-year): the "
                    "definition and the example disagree; the definition is used",
           "patyayini": "PVR p410-411 (Table 75): krisamsa = degrees within the sign of the lagna and the seven "
                        "planets, sorted ascending; patyamsa = each minus the previous; dasha = 365.2425 days x patyamsa "
                        "/ largest krisamsa (year length as mapped, not the sidereal year); antardashas in the same "
                        "order and ratios from the dasha lord. A timing tool inside an annual chart, never standalone. "
                        "Example 122: Mercury 26 Jun-13 Aug 1993",
           "pancha_vargeeya_bala": "PVR p388-391: kshetra 30/15/7.5 (own/friend/enemy), uchcha 20 x distance from deep "
                                   "debilitation / 180, hadda 15/7.5/3.75 (Table 72, p390), Parashari drekkana 10/5/2.5, "
                                   "navamsa 5/2.5/1.25, sum / 4. Friendship: Kesava's two Tajika blocs (Su Mo Ma Ju; Me Ve "
                                   "Sa), via Raman, Varshaphala ch. 3 art. 17-18, second-hand (research/CALC/R4); it "
                                   "reproduces PVR Example 118 Mars 13.7. Variants: " + PVB_UNSETTLED}


def _sun_reaches(target, jd_lo, jd_hi):
    """UT Julian day when the sidereal Sun reaches `target` degrees within [jd_lo, jd_hi] (bisection, ~1e-9 d)."""
    f = lambda j: (E.positions(j)["Su"]["lon"] - target + 180) % 360 - 180
    for _ in range(60):
        mid = (jd_lo + jd_hi) / 2
        jd_lo, jd_hi = (mid, jd_hi) if f(mid) < 0 else (jd_lo, mid)
    return jd_hi


def varsha_pravesh(birth_jd, natal_sun, completed):
    approx = birth_jd + completed * SIDEREAL_YEAR
    return _sun_reaches(natal_sun, approx - 3, approx + 3)


def _house(sign, asc_sign):
    return (sign - asc_sign) % 12 + 1


def _saham(spec, pts, night, out):
    a, b, c, same = spec
    get = lambda k: out[k] if k in out else pts[k]
    x, y = (get(b), get(a)) if night and not same else (get(a), get(b))
    v = (x - y + get(c)) % 360
    if (get(c) - y) % 360 > (x - y) % 360:                       # C not on the arc from y (subtracted) to x
        v = (v + 30) % 360
    return v


def mudda(natal_moon, completed, ret_jd, natal_sun):
    q = natal_moon / (40 / 3) + E.EPS
    lord = E.DASA[int(q) % 27 % 9][0]
    k = (MUDDA_ORDER.index(lord) + 1 + completed) % 9
    first = (k - 1) % 9                                          # 0 = Venus = number 9
    full = VIM_YEARS[MUDDA_ORDER[first]] * 3
    spans = [(MUDDA_ORDER[first], (1 - (q - int(q))) * full)]
    spans += [(MUDDA_ORDER[(first + j) % 9], VIM_YEARS[MUDDA_ORDER[(first + j) % 9]] * 3) for j in range(1, 9)]
    spans.append((MUDDA_ORDER[first], full - spans[0][1]))        # the cycle closes at 360 solar days
    rows, start, deg = [], ret_jd, 0.0
    for p, span in spans:
        deg += span
        end = _sun_reaches((natal_sun + deg) % 360, ret_jd + deg * 0.9 - 3, ret_jd + deg * 1.1 + 3)
        rows.append({"lord": p, "start_jd": start, "end_jd": end, "solar_days": round(span, 3)})
        start = end
    return rows


def patyayini(lons, start_jd, year=PATYAYINI_YEAR):
    """lons: {'Lg': lagna, 'Su'..'Sa': sidereal longitude}. Dashas in ascending krisamsa, each with its antardashas."""
    order = sorted(lons, key=lambda k: lons[k] % 30)
    kris = [lons[k] % 30 for k in order]
    share = dict(zip(order, (k - prev for k, prev in zip(kris, [0.0] + kris)), strict=True))
    rows, start = [], start_jd
    for i, lord in enumerate(order):
        days = year * share[lord] / kris[-1]
        subs, s0 = [], start
        for sub in order[i:] + order[:i]:
            d = days * share[sub] / kris[-1]
            subs.append({"lord": sub, "start_jd": s0, "end_jd": s0 + d, "days": round(d, 3)})
            s0 += d
        rows.append({"lord": lord, "krisamsa": round(lons[lord] % 30, 4), "patyamsa": round(share[lord], 4),
                     "start_jd": start, "end_jd": start + days, "days": round(days, 3), "antardashas": subs})
        start += days
    return rows


def pancha_vargeeya_bala(lons, sun_mercury_friends):
    """lons: {'Su'..'Sa': sidereal longitude}. One convention variant -> {planet: five components and pvb (sum / 4)}."""
    def frac(p, lord):
        if lord == p:
            return 1.0
        friends = (p in BLOC) == (lord in BLOC) or (sun_mercury_friends and {p, lord} == {"Su", "Me"})
        return .5 if friends else .25

    def by_sign(p, s, mx):
        return mx * frac(p, SIGN_LORD[s])                   # own rasi only: exaltation is scored by uchcha (PVR p389)

    out = {}
    for p in PLANETS:
        L = lons[p]
        d = (L - EXALT[p] - 180) % 360
        uchcha = 20 * min(d, 360 - d) / 180
        row = {"kshetra": by_sign(p, int(L // 30), 30), "uchcha": round(uchcha, 2),
               "hadda": 15 * frac(p, next(lord for lord, end in HADDA[int(L // 30)] if L % 30 < end)),
               "drekkana": by_sign(p, E.varga(L, 3), 10), "navamsa": by_sign(p, E.varga(L, 9), 5)}
        out[p] = row | {"pvb": round((sum(row.values()) - row["uchcha"] + uchcha) / 4, 2)}
    return out


def pvb_all(lons):
    """Every convention variant, grouped per planet: one entry when all variants agree, else one per distinct value."""
    by_var = {label: pancha_vargeeya_bala(lons, friends) for label, friends in PVB_VARIANTS.items()}
    planets = {}
    for p in PLANETS:
        groups = []
        for label, res in by_var.items():
            g = next((g for g in groups if all(g[k] == v for k, v in res[p].items())), None)
            if g is None:
                groups.append(g := dict(res[p], variants=[]))
            g["variants"].append(label)
        planets[p] = groups
    return {"variants": list(PVB_VARIANTS), "default": PVB_DEFAULT, "unsettled": PVB_UNSETTLED, "planets": planets,
            "by_variant": by_var}


def year_lord(rows, by_variant):
    """PVR p391-393 (owner page check 2026-10-24, CALC-F412): a candidate strong by PVB (>= 10) with a benefic aspect
    on the annual lagna, else one with a malefic aspect; else a very strong candidate (>= 15); else candidate 1. The
    highest PVB wins a shortlist under the default variant; a differing variant is named. Aspects are whole-sign."""
    default = by_variant[PVB_DEFAULT]

    def top(res, short):
        best = [p for p in short if res[p]["pvb"] == max(res[q]["pvb"] for q in short)]
        return best[0] if len(best) == 1 else None                         # a tie decides nothing

    def pick(short, what):
        lord = top(default, short)
        if lord is None:
            return None, f"year lord undetermined: {what} ({', '.join(short)}) tie on pancha vargeeya bala"
        others = [f"{label} variant names {top(res, short) or 'a tie'}" for label, res in by_variant.items()
                  if label != PVB_DEFAULT and top(res, short) != lord]
        return lord, (f"the highest pancha vargeeya bala among {what} ({', '.join(short)}), default convention "
                      f"({PVB_DEFAULT})" + (f"; the {'; the '.join(others)} instead" if others else ""))

    for tier in ("benefic", "malefic"):
        short = sorted({r["planet"] for r in rows if r["aspect_on_lagna"] and tier in r["aspect_on_lagna"]
                        and default[r["planet"]]["pvb"] >= STRONG})
        if short:
            return pick(short, f"the strong (PVB >= {STRONG}) candidates with a {tier} Tajika aspect on the annual lagna")
    short = sorted({r["planet"] for r in rows if default[r["planet"]]["pvb"] >= VERY_STRONG})
    if short:
        return pick(short, f"the very strong (PVB >= {VERY_STRONG}) candidates, none strong with an aspect on the lagna")
    return rows[0]["planet"], (f"candidate 1 ({rows[0].get('as', 'lord of the Sun or Moon sign')}): no strong candidate "
                               f"aspects the annual lagna and none is very strong (PVR p392)")


def annual(birth_jd, natal, completed, lat, lon, node="mean"):
    """natal: {'Su','Mo','Asc'} sidereal longitudes. completed: whole years of age at the return (year N = completed+1)."""
    jd = varsha_pravesh(birth_jd, natal["Su"], completed)
    P = E.positions(jd, node)
    lg = E.asc(jd, lat, lon)
    asc_sign = int(lg // 30)
    sign = {p: int(P[p]["lon"] // 30) for p in PLANETS}
    night = (P["Su"]["lon"] - lg) % 360 < 180                    # the Sun below the horizon (houses 1-6)
    muntha = (int(natal["Asc"] // 30) + completed) % 12
    harsha = {}
    for p in PLANETS:
        h = _house(sign[p], asc_sign)
        harsha[p] = 5 * sum((h == HARSHA_HOUSE[p],
                             sign[p] == int(EXALT[p] // 30) or SIGN_LORD[sign[p]] == p,
                             (p in FEMININE and h in (1, 2, 3, 7, 8, 9)) or (p in MASCULINE and h in (4, 5, 6, 10, 11, 12)),
                             p in (FEMININE if night else MASCULINE)))
    cands = [("lord of the " + ("Moon" if night else "Sun") + "'s sign", SIGN_LORD[sign["Mo" if night else "Su"]]),
             ("natal lagna lord", SIGN_LORD[int(natal["Asc"] // 30)]), ("muntha lord", SIGN_LORD[muntha]),
             ("annual lagna lord", SIGN_LORD[asc_sign]), ("tri-rasi lord", TRIRASI[asc_sign][night])]
    rows = []
    for why, p in cands:
        h = _house(asc_sign, sign[p])                            # the lagna counted from the planet
        rows.append({"planet": p, "as": why, "aspect_on_lagna": ASPECT.get(h), "harsha_bala": harsha[p]})
    pvb = pvb_all({p: P[p]["lon"] for p in PLANETS})
    lord, reason = year_lord(rows, pvb["by_variant"])
    pts = {p: P[p]["lon"] for p in PLANETS} | {"Lg": lg, "LgLord": P[SIGN_LORD[asc_sign]]["lon"], "CnMid": 105.0}
    sah = {}
    for name, spec in SAHAMS.items():
        if name == "Samartha" and SIGN_LORD[asc_sign] == "Ma":   # Ju - Ma + Lg when Mars owns the lagna
            spec = ("Ju", "Ma", "Lg", False)
        sah[name] = _saham(spec, pts, night, sah)
    return {"year": completed + 1, "jd": jd, "positions": P, "asc": lg, "night": night, "muntha": muntha,
            "harsha_bala": harsha, "candidates": rows, "year_lord": lord, "year_lord_reason": reason, "sahams": sah,
            "mudda": mudda(natal["Mo"], completed, jd, natal["Su"]), "pancha_vargeeya_bala": pvb,
            "patyayini": patyayini({"Lg": lg} | {p: P[p]["lon"] for p in PLANETS}, jd)}
