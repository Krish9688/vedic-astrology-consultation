"""Shadbala and Ashtakavarga, computed locally (no external service).

Shadbala follows BPHS ch. 27 as worked out in B. V. Raman, *Graha and Bhava Balas*. Where authorities or engines
differ, the choice is named in ``SHADBALA_CONVENTIONS`` and travels with every result, so a comparison can say
"methodology difference" instead of guessing. Units: virupas (60 virupas = 1 rupa); totals also in rupas.
Ashtakavarga uses the BPHS benefic-point (bindu) tables; reductions (shodhana) are not applied.
"""
from __future__ import annotations

import datetime as dt

import swisseph as swe

from . import engine as E

SEVEN = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")
SIGN_LORD = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]
EXALT = {"Su": 10, "Mo": 33, "Ma": 298, "Me": 165, "Ju": 95, "Ve": 357, "Sa": 200}          # deep exaltation, sidereal°
MOOLATRIKONA = {"Su": (4, 0, 20), "Mo": (1, 3, 30), "Ma": (0, 0, 12), "Me": (5, 15, 20), "Ju": (8, 0, 10),
                "Ve": (6, 0, 15), "Sa": (10, 0, 20)}                                         # sign index, from°, to°
NATURAL = {  # BPHS natural relationships: friends, enemies (the rest neutral)
    "Su": ({"Mo", "Ma", "Ju"}, {"Ve", "Sa"}), "Mo": ({"Su", "Me"}, set()),
    "Ma": ({"Su", "Mo", "Ju"}, {"Me"}), "Me": ({"Su", "Ve"}, {"Mo"}),
    "Ju": ({"Su", "Mo", "Ma"}, {"Me", "Ve"}), "Ve": ({"Me", "Sa"}, {"Su", "Mo"}),
    "Sa": ({"Me", "Ve"}, {"Su", "Mo", "Ma"})}
NAISARGIKA = {"Su": 60, "Mo": 51.43, "Ve": 42.86, "Ju": 34.29, "Me": 25.71, "Ma": 17.14, "Sa": 8.57}
REQUIRED_RUPAS = {"Su": 6.5, "Mo": 6, "Ma": 5, "Me": 7, "Ju": 6.5, "Ve": 5.5, "Sa": 5}   # BPHS p299 (ch. 27): 390, 360, 300, 420, 390, 330, 300 virupas
SAPTAVARGA = (1, 2, 3, 7, 9, 12, 30)
VARGA_POINTS = {"moolatrikona": 45, "own": 30, "great friend": 20, "friend": 15, "neutral": 10, "enemy": 4,
                "great enemy": 2}
HORA_CYCLE = ["Su", "Ve", "Me", "Mo", "Sa", "Ju", "Ma"]          # Chaldean order of planetary hours
WEEKDAY_LORD = ["Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Su"]        # Python weekday() 0 = Monday
KALI_EPOCH_JD = 588465.5                                          # Kali Yuga epoch, midnight 17/18 Feb 3102 BCE

SHADBALA_CONVENTIONS = {
    "saptavargaja": "D1, D2 (Parashari hora), D3, D7, D9, D12, D30; points 45/30/20/15/10/4/2 (BPHS, Raman); "
                    "moolatrikona counted in D1 only; compound relationship from D1 positions",
    "kendradi": "whole-sign houses from the ascendant",
    "dig": "arc from the powerless point / 3, using the sidereal ascendant and midheaven (not bhava madhyas)",
    "natonnata": "local apparent solar time (UT + longitude/15 + equation of time)",
    "paksha": "benefics elongation/3, malefics 60 − that; Moon doubled; Mercury benefic unless in the sign of "
              "Sun, Mars or Saturn",
    "tribhaga": "day and night each split into three equal parts from actual sunrise/sunset (Sun's disc centre, with "
                "refraction); in polar day/night 06:00 and 18:00 local apparent time (flag polar_sunrise_fallback)",
    "abda_masa": "Raman's Ahargana from the Kali Yuga epoch (JD 588465.5); year lord (q×3+1) mod 7, month lord "
                 "(q×2+1) mod 7, counted from Sunday",
    "vara_hora": "Hindu day from sunrise; equal 60-minute horas from sunrise in Chaldean order",
    "ayana": "(24° ± declination) × 1.25 with true declination; Sun doubled",
    "cheshta": "Sun = ayana bala, Moon = paksha bala (Raman); others cheshta kendra = sighrochcha − mean of madhya "
               "and spashta, the mean taken circularly (a plain average breaks when the two straddle 0° Aries — "
               "PyJHora and VedAstro both show this on test chart S2); modern mean elements (J2000)",
    "yuddha": "Mars, Mercury, Jupiter, Venus, Saturn within 1°: Venus always wins (BPHS ch. 79 sl. 9), otherwise the "
              "northern (higher latitude) planet; transfer = difference of sthana+dig+kala. Variant: LOL — higher "
              "latitude wins with no Venus exception",
    "drik": "Raman's drishti curve with his special-aspect additions (Mars +15, Jupiter +30, Saturn +45, capped at "
            "60); benefic minus malefic, divided by 4 — reproduces Raman's published example to ±0.02",
}

# mean tropical longitudes at J2000 and daily motion (Meeus-type mean elements) for cheshta kendra
MEAN = {"Sun": (280.46646, 0.9856474), "Me": (252.25090, 4.0923344), "Ve": (181.97980, 1.6021302),
        "Ma": (355.43300, 0.5240208), "Ju": (34.35152, 0.0830853), "Sa": (50.07744, 0.0334443)}


def war_winner(a, b, lat):
    """Graha yuddha victor (BPHS ch. 79 sl. 9): Venus always wins; otherwise the planet with the higher latitude."""
    if "Ve" in (a, b):
        return "Ve"
    return a if lat[a] > lat[b] else b


def relation(p, q, signs):
    """Compound (panchadha) relationship of p towards q, from natural + temporary friendship."""
    if p == q:
        return "own"
    fr, en = NATURAL[p]
    nat = 1 if q in fr else -1 if q in en else 0
    dist = (signs[q] - signs[p]) % 12 + 1
    tmp = 1 if dist in (2, 3, 4, 10, 11, 12) else -1
    return {2: "great friend", 1: "friend", 0: "neutral", -1: "enemy", -2: "great enemy"}[nat + tmp]


def drishti(aspecting, aspected, planet):
    """Aspect value (virupas) cast by `planet` at longitude `aspecting` on longitude `aspected`: Raman's curve, plus
    his additions for special aspects (Mars +15, Jupiter +30, Saturn +45 in their ranges), capped at 60."""
    d = (aspected - aspecting) % 360
    if d < 30:
        v = 0.0
    elif d < 60:
        v = (d - 30) / 2
    elif d < 90:
        v = d - 60 + 15
    elif d < 120:
        v = (120 - d) / 2 + 30
    elif d < 150:
        v = 150 - d
    elif d < 180:
        v = (d - 150) * 2
    elif d < 300:
        v = (300 - d) / 2
    else:
        v = 0.0
    special = {"Ma": (15, ((90, 120), (210, 240))), "Ju": (30, ((120, 150), (240, 270))),
               "Sa": (45, ((60, 90), (270, 300)))}
    if planet in special:
        add, ranges = special[planet]
        if any(lo <= d < hi for lo, hi in ranges):
            v = min(60.0, v + add)
    return v


def _sun_events(jd, lat, lon):
    """Sunrise before (or at) jd, the following sunset and next sunrise (UT Julian days), and whether the polar
    fallback was used. Where the Sun does not rise or set within a day (polar day/night), sunrise and sunset are taken
    at 06:00 and 18:00 local apparent solar time (equinoctial convention) — recorded in the output."""
    geo = (lon, lat, 0)

    def event(t, kind):
        flag, tret = swe.rise_trans(t, swe.SUN, kind | swe.BIT_DISC_CENTER, geo, 0, 0, swe.FLG_SWIEPH)
        return None if flag == -2 else tret[0]          # -2: circumpolar, no event
    r1 = event(jd - 1, swe.CALC_RISE)
    if r1 is not None and r1 > jd:
        r1 = event(jd - 2, swe.CALC_RISE)
    s = event(r1, swe.CALC_SET) if r1 is not None else None
    r2 = event(s, swe.CALC_RISE) if s is not None else None
    if None in (r1, s, r2) or not (r1 <= jd < r2) or s - r1 > 1 or r2 - s > 1:
        noon = int(jd - 0.5) + 1.0 - lon / 360 - swe.time_equ(jd)   # local apparent noon (UT) of jd's civil day
        noon = noon - 1 if noon - 0.25 > jd else noon + 1 if noon + 0.75 <= jd else noon
        return noon - 0.25, noon + 0.25, noon + 0.75, True
    return r1, s, r2, False


def shadbala(c, ut, lat, lon, tz):
    """Shadbala for the seven planets from a compute() result `c` and the birth UT (naive datetime)."""
    jd = E.jd_of(ut)
    L = {p: c["bodies"][p]["lon"] for p in SEVEN}
    signs = {p: int(L[p] // 30) for p in SEVEN}
    asc_l, mc_l = c["bodies"]["Asc"]["lon"], c["mc"]
    asc_s = int(asc_l // 30)
    elong = (L["Mo"] - L["Su"]) % 360
    elong_f = elong if elong <= 180 else 360 - elong
    malefic_sign = {signs[x] for x in ("Su", "Ma", "Sa")}
    benefic = {"Ju": True, "Ve": True, "Me": signs["Me"] not in malefic_sign, "Mo": elong <= 180,
               "Su": False, "Ma": False, "Sa": False}
    fold3 = lambda d: (d if d <= 180 else 360 - d) / 3

    # Sthana bala
    uchcha = {p: fold3((L[p] - (EXALT[p] + 180)) % 360) for p in SEVEN}
    sapta, sapta_detail = {}, {}
    for p in SEVEN:
        tot, det = 0.0, {}
        for v in SAPTAVARGA:
            sg = E.varga(L[p], v)
            mt = MOOLATRIKONA[p]
            if v == 1 and sg == mt[0] and mt[1] <= L[p] % 30 < mt[2]:
                kind = "moolatrikona"
            else:
                kind = relation(p, SIGN_LORD[sg], signs)
            det[f"D{v}"] = kind
            tot += VARGA_POINTS[kind]
        sapta[p], sapta_detail[p] = tot, det
    oja = {}
    for p in SEVEN:
        even_rasi, even_nav = signs[p] % 2 == 1, E.varga(L[p], 9) % 2 == 1
        oja[p] = 15 * (even_rasi + even_nav) if p in ("Mo", "Ve") else 15 * ((not even_rasi) + (not even_nav))
    kendra = {p: {0: 60, 3: 60, 6: 60, 9: 60, 1: 30, 4: 30, 7: 30, 10: 30}.get((signs[p] - asc_s) % 12, 15)
              for p in SEVEN}
    gender_third = {"Su": 0, "Ma": 0, "Ju": 0, "Me": 1, "Sa": 1, "Mo": 2, "Ve": 2}
    drekkana = {p: 15 if int((L[p] % 30) // 10) == gender_third[p] else 0 for p in SEVEN}
    sthana = {p: uchcha[p] + sapta[p] + oja[p] + kendra[p] + drekkana[p] for p in SEVEN}

    # Dig bala: distance from the powerless point / 3
    desc, ic = (asc_l + 180) % 360, (mc_l + 180) % 360
    weak = {"Ju": desc, "Me": desc, "Su": ic, "Ma": ic, "Sa": asc_l, "Mo": mc_l, "Ve": mc_l}
    dig = {p: fold3((L[p] - weak[p]) % 360) for p in SEVEN}

    # Kala bala
    lat_hours = (ut.hour + ut.minute / 60 + ut.second / 3600 + lon / 15 + swe.time_equ(jd) * 24) % 24
    day_part = 60 * min(lat_hours, 24 - lat_hours) / 12
    nato = {p: day_part if p in ("Su", "Ju", "Ve") else 60.0 if p == "Me" else 60 - day_part for p in SEVEN}
    paksha = {p: (elong_f / 3 if benefic[p] else 60 - elong_f / 3) for p in SEVEN}
    paksha["Mo"] = 2 * elong_f / 3
    r1, s, r2, polar = _sun_events(jd, lat, lon)
    is_day = r1 <= jd < s
    frac = (jd - r1) / (s - r1) if is_day else (jd - s) / (r2 - s)
    tri_lord = (["Me", "Su", "Sa"] if is_day else ["Mo", "Ve", "Ma"])[min(int(frac * 3), 2)]
    tribhaga = {p: 60.0 if p in ("Ju", tri_lord) else 0.0 for p in SEVEN}
    y, m, d, _ = swe.revjul(r1 + tz / 24)
    vara = WEEKDAY_LORD[dt.date(y, m, d).weekday()]
    hora = HORA_CYCLE[(HORA_CYCLE.index(vara) + int((jd - r1) * 24)) % 7]
    ahargana = int(r1 + tz / 24 + 0.5 - KALI_EPOCH_JD)
    sunday_order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    abda = sunday_order[(((ahargana // 360) * 3 + 1) % 7 - 1) % 7]
    masa = sunday_order[(((ahargana // 30) * 2 + 1) % 7 - 1) % 7]
    amvh = {p: 15 * (p == abda) + 30 * (p == masa) + 45 * (p == vara) + 60 * (p == hora) for p in SEVEN}
    decl = {p: E.declination(jd, b) for p, b in E.PL}
    ayana = {}
    for p in SEVEN:
        dd = abs(decl[p]) if p == "Me" else (-decl[p] if p in ("Mo", "Sa") else decl[p])
        ayana[p] = (24 + dd) * 1.25
    ayana["Su"] *= 2
    kala = {p: nato[p] + paksha[p] + tribhaga[p] + amvh[p] + ayana[p] for p in SEVEN}

    # Cheshta bala
    days = jd - 2451545.0
    mean = {k: (a + b * days) % 360 for k, (a, b) in MEAN.items()}
    trop = {p: swe.calc_ut(jd, b, swe.FLG_SWIEPH)[0][0] for p, b in E.PL}
    cheshta = {"Su": ayana["Su"], "Mo": paksha["Mo"]}
    for p in ("Ma", "Ju", "Sa", "Me", "Ve"):
        madhya, sighra = (mean[p], mean["Sun"]) if p in ("Ma", "Ju", "Sa") else (mean["Sun"], mean[p])
        avg = (madhya + ((trop[p] - madhya + 180) % 360 - 180) / 2) % 360   # circular mean: safe across 0° Aries
        cheshta[p] = fold3((sighra - avg) % 360)

    # Yuddha bala
    yuddha = dict.fromkeys(SEVEN, 0.0)
    war = []
    five = ("Ma", "Me", "Ju", "Ve", "Sa")
    latb = {p: swe.calc_ut(jd, b, swe.FLG_SWIEPH)[0][1] for p, b in E.PL}
    for i, a in enumerate(five):
        for b in five[i + 1:]:
            if abs((L[a] - L[b] + 180) % 360 - 180) < 1:
                win = war_winner(a, b, latb)
                lose = b if win == a else a
                diff = abs((sthana[a] + dig[a] + kala[a]) - (sthana[b] + dig[b] + kala[b]))
                yuddha[win] += diff
                yuddha[lose] -= diff
                war.append({"winner": win, "loser": lose, "transfer": round(diff, 2)})

    # Drik bala
    drik = {p: sum((1 if benefic[q] else -1) * drishti(L[q], L[p], q) for q in SEVEN if q != p) / 4 for p in SEVEN}

    out = {}
    for p in SEVEN:
        comp = {"sthana": sthana[p], "dig": dig[p], "kala": kala[p] + yuddha[p], "cheshta": cheshta[p],
                "naisargika": NAISARGIKA[p], "drik": drik[p]}
        tot = sum(comp.values())
        out[p] = {"virupas": {k: round(v, 2) for k, v in comp.items()}, "total_virupas": round(tot, 2),
                  "total_rupas": round(tot / 60, 2), "required_rupas": REQUIRED_RUPAS[p],
                  "ratio": round(tot / 60 / REQUIRED_RUPAS[p], 2),
                  "detail": {"uchcha": round(uchcha[p], 2), "saptavargaja": sapta[p], "saptavarga": sapta_detail[p],
                             "ojayugma": oja[p], "kendradi": kendra[p], "drekkana": drekkana[p],
                             "natonnata": round(nato[p], 2), "paksha": round(paksha[p], 2), "tribhaga": tribhaga[p],
                             "abda_masa_vara_hora": amvh[p], "ayana": round(ayana[p], 2), "yuddha": round(yuddha[p], 2)}}
    return {"planets": out, "time_lords": {"year": abda, "month": masa, "weekday": vara, "hora": hora,
                                           "tribhaga": tri_lord, "day_birth": is_day,
                                           "polar_sunrise_fallback": polar},
            "planetary_war": war, "conventions": SHADBALA_CONVENTIONS}


# --- Ashtakavarga (BPHS ch. 66): houses, counted from each contributor, where the planet gets a bindu ---------------
BAV_TABLE = {
    "Su": {"Su": [1, 2, 4, 7, 8, 9, 10, 11], "Mo": [3, 6, 10, 11], "Ma": [1, 2, 4, 7, 8, 9, 10, 11],
           "Me": [3, 5, 6, 9, 10, 11, 12], "Ju": [5, 6, 9, 11], "Ve": [6, 7, 12], "Sa": [1, 2, 4, 7, 8, 9, 10, 11],
           "Asc": [3, 4, 6, 10, 11, 12]},
    "Mo": {"Su": [3, 6, 7, 8, 10, 11], "Mo": [1, 3, 6, 7, 10, 11], "Ma": [2, 3, 5, 6, 9, 10, 11],
           "Me": [1, 3, 4, 5, 7, 8, 10, 11], "Ju": [1, 4, 7, 8, 10, 11, 12], "Ve": [3, 4, 5, 7, 9, 10, 11],
           "Sa": [3, 5, 6, 11], "Asc": [3, 6, 10, 11]},
    "Ma": {"Su": [3, 5, 6, 10, 11], "Mo": [3, 6, 11], "Ma": [1, 2, 4, 7, 8, 10, 11], "Me": [3, 5, 6, 11],
           "Ju": [6, 10, 11, 12], "Ve": [6, 8, 11, 12], "Sa": [1, 4, 7, 8, 9, 10, 11], "Asc": [1, 3, 6, 10, 11]},
    "Me": {"Su": [5, 6, 9, 11, 12], "Mo": [2, 4, 6, 8, 10, 11], "Ma": [1, 2, 4, 7, 8, 9, 10, 11],
           "Me": [1, 3, 5, 6, 9, 10, 11, 12], "Ju": [6, 8, 11, 12], "Ve": [1, 2, 3, 4, 5, 8, 9, 11],
           "Sa": [1, 2, 4, 7, 8, 9, 10, 11], "Asc": [1, 2, 4, 6, 8, 10, 11]},
    "Ju": {"Su": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Mo": [2, 5, 7, 9, 11], "Ma": [1, 2, 4, 7, 8, 10, 11],
           "Me": [1, 2, 4, 5, 6, 9, 10, 11], "Ju": [1, 2, 3, 4, 7, 8, 10, 11], "Ve": [2, 5, 6, 9, 10, 11],
           "Sa": [3, 5, 6, 12], "Asc": [1, 2, 4, 5, 6, 7, 9, 10, 11]},
    "Ve": {"Su": [8, 11, 12], "Mo": [1, 2, 3, 4, 5, 8, 9, 11, 12], "Ma": [3, 5, 6, 9, 11, 12],
           "Me": [3, 5, 6, 9, 11], "Ju": [5, 8, 9, 10, 11], "Ve": [1, 2, 3, 4, 5, 8, 9, 10, 11],
           "Sa": [3, 4, 5, 8, 9, 10, 11], "Asc": [1, 2, 3, 4, 5, 8, 9, 11]},
    "Sa": {"Su": [1, 2, 4, 7, 8, 10, 11], "Mo": [3, 6, 11], "Ma": [3, 5, 6, 10, 11, 12],
           "Me": [6, 8, 9, 10, 11, 12], "Ju": [5, 6, 11, 12], "Ve": [6, 11, 12], "Sa": [3, 5, 6, 11],
           "Asc": [1, 3, 4, 6, 10, 11]},
}
BAV_TOTALS = {"Su": 48, "Mo": 49, "Ma": 39, "Me": 54, "Ju": 56, "Ve": 52, "Sa": 39}   # fixed by the tables; SAV 337


def ashtakavarga(c):
    """Bhinnashtakavarga per planet and Sarvashtakavarga, by sign (index 0 = Aries) and by house from the lagna."""
    sg = {p: int(c["bodies"][p]["lon"] // 30) for p in (*SEVEN, "Asc")}
    bav = {}
    for p, rows in BAV_TABLE.items():
        pts = [0] * 12
        for contrib, houses in rows.items():
            for h in houses:
                pts[(sg[contrib] + h - 1) % 12] += 1
        bav[p] = pts
    sav = [sum(bav[p][i] for p in bav) for i in range(12)]
    asc = sg["Asc"]
    by_house = lambda row: [row[(asc + h) % 12] for h in range(12)]
    return {"signs": E.SIGNS, "bav": bav, "sav": sav, "bav_by_house": {p: by_house(r) for p, r in bav.items()},
            "sav_by_house": by_house(sav), "totals": {p: sum(r) for p, r in bav.items()}, "sav_total": sum(sav),
            "conventions": "BPHS bindu tables; no trikona/ekadhipatya reduction; rows indexed by sign from Aries"}
