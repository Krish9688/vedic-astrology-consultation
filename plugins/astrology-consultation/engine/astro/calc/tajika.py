"""Tajika (Tajaka) annual chart core, as taught in PVR ch. 27-28 and 31 (Narasimha Rao, "Vedic Astrology: An Integrated
Approach"; page-cited source map, not page-checked): the solar return (varsha pravesh) at the birthplace, day or night
year, muntha, harsha bala, the five year-lord candidates with their Tajika aspect on the annual lagna, sahams and Mudda
dasha. Calculation and rule lookup only.

PVR p377: Tajika has no reference in Parasara or Jaimini; its oldest respected source, Tajaka Neelakanthi, is not in
the project library. Not computed: pancha vargeeya bala (the source gives no value for a neutral sign), so the year
lord is named only when the selection rule settles it without that bala; Patyayini and Varsha Narayana dashas; the
sahams that need house cusps (the cusp system is not stated).
"""
from __future__ import annotations

from . import engine as E
from .strength import EXALT, SIGN_LORD

NOT_COMPUTED = ("pancha vargeeya bala (no value for a neutral sign in the source), so the year lord is named only when "
                "the aspect tiers settle it; Patyayini and Varsha Narayana dashas; Karyasiddhi and the sahams that need "
                "house cusps (Mrityu, Paradesa, Artha, Santapa, Apamrityu, Labha: the cusp system is not stated)")
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
SOURCES = {"return": "PVR p379-380: the moment the Sun returns to its natal sidereal longitude, for the birthplace",
           "muntha": "PVR p386: the Nth sign from the natal lagna (inclusive) in the Nth year",
           "harsha_bala": "PVR p387-388: four sources of 5 units",
           "year_lord": "PVR p391-393: candidates with a benefic Tajika aspect on the annual lagna, then the highest "
                        "pancha vargeeya bala; else a malefic aspect; else a very strong candidate; else candidate 1",
           "sahams": "PVR p394-395 (Table 74): A - B + C by day, reversed at night unless the same for both; add 30° "
                     "when C is not on the zodiacal arc from the subtracted to the added point",
           "mudda": "PVR p411-412 (Table 76): Vimshottari compressed to 360 solar days (days = years x 3; a solar "
                    "day = the Sun moving 1°); first lord = natal Moon-nakshatra lord's number + completed years, "
                    "mod 9; balance from the natal Moon's nakshatra; PVR ranks it below Patyayini and Varsha Narayana. "
                    "PVR's own Example 122 dates fit a clock day instead (about 2 days earlier in mid-year): the "
                    "definition and the example disagree; the definition is used"}


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
    lord, reason = None, "pancha vargeeya bala decides between several candidates; not computed (see note)"
    for tier in ("benefic", "malefic"):
        short = sorted({r["planet"] for r in rows if r["aspect_on_lagna"] and tier in r["aspect_on_lagna"]})
        if len(short) == 1:
            lord, reason = short[0], f"the only candidate with a {tier} Tajika aspect on the annual lagna"
        if short:
            break
    pts = {p: P[p]["lon"] for p in PLANETS} | {"Lg": lg, "LgLord": P[SIGN_LORD[asc_sign]]["lon"], "CnMid": 105.0}
    sah = {}
    for name, spec in SAHAMS.items():
        if name == "Samartha" and SIGN_LORD[asc_sign] == "Ma":   # Ju - Ma + Lg when Mars owns the lagna
            spec = ("Ju", "Ma", "Lg", False)
        sah[name] = _saham(spec, pts, night, sah)
    return {"year": completed + 1, "jd": jd, "positions": P, "asc": lg, "night": night, "muntha": muntha,
            "harsha_bala": harsha, "candidates": rows, "year_lord": lord, "year_lord_reason": reason, "sahams": sah,
            "mudda": mudda(natal["Mo"], completed, jd, natal["Su"])}
