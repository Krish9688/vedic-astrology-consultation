"""Jaimini factors computed locally: chara karakas (7- and 8-karaka schemes), arudha padas, upapada, karakamsa,
rasi drishti. Conventions follow BPHS ch. 29–32 as used by the skill's references/jaimini.md; the choices that
schools dispute are named in CONVENTIONS. Chara dasha is not calculated (its sign-direction and year rules vary by
school and the reasoning layer does not use it yet).
"""
from __future__ import annotations

SIGN_LORDS = [("Ma",), ("Ve",), ("Me",), ("Mo",), ("Su",), ("Me",), ("Ve",), ("Ma", "Ke"), ("Ju",), ("Sa",),
              ("Sa", "Ra"), ("Ju",)]
ROLES7 = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
ROLES8 = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]
CONVENTIONS = {
    "karakas": "degrees within the sign; 7-scheme Sun–Saturn; 8-scheme adds Rahu counted as 30° minus its degree",
    "arudha": "count from the house to its lord, then as many again; if that lands in the house itself or the 7th "
              "from it, take the 10th from the landing sign (BPHS 29.45, as read by Rath; Santhanam's example instead "
              "takes the 4th house when the lord is in the 7th)",
    "dual_lordship": "Scorpio (Mars/Ketu), Aquarius (Saturn/Rahu): the lord with more planets in its sign; if "
                     "equal, the one farther advanced in its sign",
    "rasi_drishti": "movable signs aspect fixed signs except the adjacent; fixed aspect movable except adjacent; "
                    "dual signs aspect each other",
}


def _lord(sign, sg, deg):
    lords = SIGN_LORDS[sign]
    if len(lords) == 1:
        return lords[0]
    count = {lo: sum(1 for p, s in sg.items() if s == sg[lo] and p != lo) for lo in lords}
    a, b = lords
    if count[a] != count[b]:
        return a if count[a] > count[b] else b
    return a if deg[a] >= deg[b] else b


def karakas(c):
    deg = {p: c["bodies"][p]["lon"] % 30 for p in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")}
    order7 = sorted(deg, key=lambda p: -deg[p])
    deg8 = dict(deg, Ra=30 - c["bodies"]["Ra"]["lon"] % 30)
    order8 = sorted(deg8, key=lambda p: -deg8[p])
    ties = [f"{a}/{b}" for i, a in enumerate(order8) for b in order8[i + 1:] if abs(deg8[a] - deg8[b]) < 1 / 60]
    return {"scheme7": dict(zip(ROLES7, order7)), "scheme8": dict(zip(ROLES8, order8)),
            "degrees": {p: round(v, 4) for p, v in deg8.items()}, "within_1_arcmin": ties}


def arudhas(c):
    sg = {p: int(b["lon"] // 30) for p, b in c["bodies"].items() if p != "Asc"}
    deg = {p: c["bodies"][p]["lon"] % 30 for p in sg}
    lagna = int(c["bodies"]["Asc"]["lon"] // 30)
    out = {}
    for h in range(1, 13):
        house = (lagna + h - 1) % 12
        lord = _lord(house, sg, deg)
        dist = (sg[lord] - house) % 12
        pada = (sg[lord] + dist) % 12
        if pada in (house, (house + 6) % 12):
            pada = (pada + 9) % 12
        out[f"A{h}"] = pada
    return out


def rasi_drishti(sign):
    movable, fixed, dual = (0, 3, 6, 9), (1, 4, 7, 10), (2, 5, 8, 11)
    if sign in movable:
        return [s for s in fixed if s != (sign + 1) % 12]
    if sign in fixed:
        return [s for s in movable if s != (sign - 1) % 12]
    return [s for s in dual if s != sign]


def jaimini(c):
    from .engine import SIGNS, varga
    k = karakas(c)
    a = arudhas(c)
    ak = k["scheme7"]["AK"]
    return {"chara_karakas": k, "arudha": {h: SIGNS[s] for h, s in a.items()}, "arudha_lagna": SIGNS[a["A1"]],
            "upapada": SIGNS[a["A12"]], "karakamsa": SIGNS[varga(c["bodies"][ak]["lon"], 9)],
            "rasi_drishti": {SIGNS[s]: [SIGNS[t] for t in rasi_drishti(s)] for s in range(12)},
            "conventions": CONVENTIONS}
