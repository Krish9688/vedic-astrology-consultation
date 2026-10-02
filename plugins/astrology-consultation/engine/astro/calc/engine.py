"""Local Vedic chart calculation on the Swiss Ephemeris (pyswisseph). Calculation only — it never interprets.

Conventions (recorded in every result's ``meta``): Lahiri ayanamsa; mean nodes (true optional); whole-sign houses
from the sidereal ascendant for the rasi chart, Sripati bhava cusps as a separate table; Parashari vargas
(``VARGA_METHODS``); Vimshottari with 365.256363-day years (365.25 / 360 optional).
Ephemeris: the Swiss Ephemeris files (sepl_18/semo_18) when found, otherwise the built-in Moshier fallback —
``ephemeris_info()`` says which, and differences are ≈1″ for planets, ≈3″ for the Moon, 0 for mean nodes, ≈1′ for
true nodes (benchmark in docs/CALCULATION-ENGINES.md).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os

import swisseph as swe

SIGNS = "Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius Capricorn Aquarius Pisces".split()
NAKS = ("Ashwini Bharani Krittika Rohini Mrigashira Ardra Punarvasu Pushya Ashlesha Magha PurvaPhalguni UttaraPhalguni "
        "Hasta Chitra Swati Vishakha Anuradha Jyeshtha Mula PurvaAshadha UttaraAshadha Shravana Dhanishtha Shatabhisha "
        "PurvaBhadrapada UttaraBhadrapada Revati").split()
DASA = [("Ke", 7), ("Ve", 20), ("Su", 6), ("Mo", 10), ("Ma", 7), ("Ra", 18), ("Ju", 16), ("Sa", 19), ("Me", 17)]
PL = [("Su", swe.SUN), ("Mo", swe.MOON), ("Ma", swe.MARS), ("Me", swe.MERCURY), ("Ju", swe.JUPITER),
      ("Ve", swe.VENUS), ("Sa", swe.SATURN)]
YEAR = {"sidereal": 365.256363, "365.25": 365.25, "360": 360.0}
VARGAS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
EPS = 1e-9  # in units of a division (≈1e-8°): absorbs float error at exact boundaries
ENGINE_VERSION = "3.5.0"

# Parashari varga rules as implemented (BPHS ch. 6–7). Other engines' variants are recorded in compare.py notes.
VARGA_METHODS = {
    "D1": "rasi", "D2": "Parashari hora: odd signs 0–15° Leo, 15–30° Cancer; even signs reversed",
    "D3": "drekkana: 1st, 5th, 9th from the sign by 10° thirds",
    "D4": "chaturthamsha: 1st, 4th, 7th, 10th from the sign by 7°30′",
    "D7": "saptamsha: odd signs from the sign, even signs from the 7th, 4°17′ parts",
    "D9": "navamsha: movable from the sign, fixed from the 9th, dual from the 5th (continuous from Aries)",
    "D10": "dashamsha: odd signs from the sign, even signs from the 9th, 3° parts",
    "D12": "dwadashamsha: from the sign, 2°30′ parts",
    "D16": "shodashamsha: movable from Aries, fixed from Leo, dual from Sagittarius",
    "D20": "vimshamsha: movable from Aries, fixed from Sagittarius, dual from Leo",
    "D24": "chaturvimshamsha: odd signs from Leo, even signs from Cancer, 1°15′ parts",
    "D27": "bhamsha: fire from Aries, earth from Cancer, air from Libra, water from Capricorn (continuous)",
    "D30": "trimshamsha (Parashari): odd 5/5/8/7/5° → Ar/Aq/Sg/Ge/Li; even 5/7/8/5/5° → Ta/Vi/Pi/Cp/Sc",
    "D40": "khavedamsha: odd signs from Aries, even signs from Libra, 45′ parts",
    "D45": "akshavedamsha: movable from Aries, fixed from Leo, dual from Sagittarius, 40′ parts",
    "D60": "shashtyamsha: from the sign, 30′ parts",
}


def _find_ephe():
    """ASTRO_EPHE_PATH, then <project>/ephe, then ~/.local/share/astrology-consultation/ephe; None → Moshier."""
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (os.environ.get("ASTRO_EPHE_PATH"), os.path.join(here, "..", "..", "ephe"),
              os.path.expanduser("~/.local/share/astrology-consultation/ephe")):
        if d and os.path.exists(os.path.join(d, "sepl_18.se1")) and os.path.exists(os.path.join(d, "semo_18.se1")):
            return os.path.abspath(d)
    return None


EPHE_DIR = _find_ephe()
swe.set_ephe_path(EPHE_DIR)          # None → Moshier fallback
swe.set_sid_mode(swe.SIDM_LAHIRI)


def ephemeris_info(jd=2451545.0):
    """Which ephemeris actually served `jd` (outside the files' 1800–2399 range Swiss Ephemeris drops to Moshier)."""
    flag = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[1]
    if EPHE_DIR and flag & swe.FLG_SWIEPH:
        files = {}
        for f in ("sepl_18.se1", "semo_18.se1"):
            with open(os.path.join(EPHE_DIR, f), "rb") as fh:
                files[f] = hashlib.sha256(fh.read()).hexdigest()[:16]
        return {"ephemeris": "Swiss Ephemeris data files", "ephemeris_files": files, "ephemeris_range": "1800–2399 CE"}
    why = "outside the data files' 1800–2399 range" if EPHE_DIR else "no .se1 files"
    return {"ephemeris": f"Moshier analytical fallback ({why})", "ephemeris_files": {},
            "ephemeris_range": "≈3000 BCE–3000 CE"}


def jd_of(t):
    return swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60 + t.second / 3600 + t.microsecond / 3.6e9)


def lon_of(jd, body, flags):
    x, _ = swe.calc_ut(jd, body, flags)
    return x[0] % 360, x[3]


def positions(jd, node="mean"):
    f = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    out = {}
    for n, b in PL:
        lon, spd = lon_of(jd, b, f)
        out[n] = {"lon": lon, "speed": spd, "retro": spd < 0}
    lon, spd = lon_of(jd, swe.MEAN_NODE if node == "mean" else swe.TRUE_NODE, f)
    out["Ra"] = {"lon": lon, "speed": spd, "retro": spd < 0}   # mean node: always; true node: usually
    out["Ke"] = {"lon": (lon + 180) % 360, "speed": spd, "retro": True}
    return out


def declination(jd, body):
    x, _ = swe.calc_ut(jd, body, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
    return x[1]


def asc(jd, lat, lon):
    _, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    return ascmc[0] % 360


def angles(jd, lat, lon):
    """Sidereal ascendant and midheaven."""
    _, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    return ascmc[0] % 360, ascmc[1] % 360


def bhavas(jd, lat, lon):
    """Sripati bhavas: madhyas (house middles) at the Porphyry cusps — house 1 middle = ascendant, house 10 middle =
    midheaven — and sandhis (boundaries) halfway between consecutive madhyas. Sidereal."""
    cusps, _ = swe.houses_ex(jd, lat, lon, b"O", swe.FLG_SIDEREAL)
    mid = [c % 360 for c in cusps[:12]]
    sandhi = [(mid[i] + ((mid[(i + 1) % 12] - mid[i]) % 360) / 2) % 360 for i in range(12)]
    start = [sandhi[(i - 1) % 12] for i in range(12)]
    return [{"house": i + 1, "start": round(start[i], 4), "middle": round(mid[i], 4), "end": round(sandhi[i], 4)}
            for i in range(12)]


def varga(L, n):
    """Parashari varga sign index (0 = Aries) for sidereal longitude L (rules in VARGA_METHODS)."""
    s, d = int(L // 30), L % 30
    odd = s % 2 == 0                      # Aries (index 0) is an odd sign
    mov, fix = s % 3 == 0, s % 3 == 1     # movable / fixed / dual by index
    part = lambda size: int(d / size + EPS)   # EPS: exact boundaries (e.g. 0° Taurus) must not fall back a division
    if n == 1:
        return s
    if n == 2:
        return (4 if d < 15 else 3) if odd else (3 if d < 15 else 4)       # Leo / Cancer
    if n == 3:
        return (s + 4 * part(10)) % 12
    if n == 4:
        return (s + 3 * part(7.5)) % 12
    if n == 7:
        return ((s if odd else s + 6) + part(30 / 7)) % 12
    if n == 9:
        return ((s if mov else s + 8 if fix else s + 4) + part(30 / 9)) % 12
    if n == 10:
        return ((s if odd else s + 8) + part(3)) % 12
    if n == 12:
        return (s + part(2.5)) % 12
    if n == 16:
        return ((0 if mov else 4 if fix else 8) + part(30 / 16)) % 12
    if n == 20:
        return ((0 if mov else 8 if fix else 4) + part(1.5)) % 12
    if n == 24:
        return ((4 if odd else 3) + part(1.25)) % 12
    if n == 27:
        return ((0, 3, 6, 9)[s % 4] + part(30 / 27)) % 12
    if n == 30:
        spans = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)] if odd else [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]
        return next(sg for lim, sg in spans if d < lim)
    if n == 40:
        return ((0 if odd else 6) + part(0.75)) % 12
    if n == 45:
        return ((0 if mov else 4 if fix else 8) + part(30 / 45)) % 12
    if n == 60:
        return (s + part(0.5)) % 12
    raise ValueError(n)


def nak(L):
    i = int(L / (40 / 3) + EPS) % 27
    return NAKS[i], int(L / (10 / 3) + EPS) % 4 + 1, i


def vimshottari(moon, birth_ut, ylen, levels=3):
    """Nested periods. Balance at birth = unelapsed fraction of the Moon's nakshatra × the lord's years."""
    q = moon / (40 / 3) + EPS          # same arithmetic as nak(), so index and balance never disagree at a boundary
    lord_i = int(q) % 27 % 9
    frac_left = 1 - (q - int(q))
    start = birth_ut - dt.timedelta(days=DASA[lord_i][1] * (1 - frac_left) * ylen)

    def sub(k0, begin, total_years, depth):
        rows, t = [], begin
        for j in range(9):
            lord, yrs = DASA[(k0 + j) % 9]
            span = total_years * yrs / 120
            end = t + dt.timedelta(days=span * ylen)
            row = {"lord": lord, "start": t, "end": end}
            if depth > 1:
                row["sub"] = sub((k0 + j) % 9, t, span, depth - 1)
            rows.append(row)
            t = end
        return rows

    mds, t = [], start
    for j in range(9):
        lord, yrs = DASA[(lord_i + j) % 9]
        end = t + dt.timedelta(days=yrs * ylen)
        mds.append({"lord": lord, "start": t, "end": end, "sub": sub((lord_i + j) % 9, t, yrs, levels - 1)})
        t = end
    return mds


def ingresses(t0, months, node):
    """Sign changes of Jupiter, Saturn and the nodes between t0 and t0+months (bisection to ~1 hour)."""
    out = []
    end = t0 + dt.timedelta(days=30.44 * months)
    for n in ("Ju", "Sa", "Ra"):
        def sign(t, n=n):
            return int(positions(jd_of(t), node)[n]["lon"] // 30)
        t, s = t0, sign(t0)
        while t < end:
            t2 = t + dt.timedelta(days=2)   # short step: a sign re-entered near a station is not skipped
            s2 = sign(t2)
            if s2 != s:
                a, bb = t, t2
                while (bb - a) > dt.timedelta(hours=1):
                    m = a + (bb - a) / 2
                    (a, bb) = (a, m) if sign(m) != s else (m, bb)
                out.append({"planet": n, "date": bb.date().isoformat(), "from": SIGNS[s], "to": SIGNS[s2]})
                s = s2
            t = t2
    return sorted(out, key=lambda r: r["date"])


def sensitivity(ut, lat, lon, moon_lon, window_min=180):
    """Minutes of birth-time change (earlier / later) before each birth-time-sensitive factor changes."""
    def asc_at(m):
        return asc(jd_of(ut + dt.timedelta(minutes=m)), lat, lon)
    base = asc_at(0)
    factors = {"ascendant sign (D1)": lambda L: int(L // 30), "D9 lagna": lambda L: varga(L, 9),
               "D10 lagna": lambda L: varga(L, 10), "D12 lagna": lambda L: varga(L, 12)}
    out = {}
    for name, f in factors.items():
        b = f(base)
        out[name] = {d: next((m for m in range(1, window_min + 1) if f(asc_at(sign * m)) != b), None)
                     for d, sign in (("earlier", -1), ("later", 1))}
    m1 = positions(jd_of(ut + dt.timedelta(hours=1)))["Mo"]["lon"]
    moon_step = ((m1 - moon_lon) % 360) / 60   # the Moon's actual motion, degrees per minute
    L0 = moon_lon % (10 / 3)
    out["Moon pada (dasha balance, D9 Moon)"] = {"earlier": round(L0 / moon_step), "later": round((10 / 3 - L0) / moon_step)}
    out["Moon nakshatra (dasha lord)"] = {"earlier": round((moon_lon % (40 / 3)) / moon_step),
                                          "later": round((40 / 3 - moon_lon % (40 / 3)) / moon_step)}
    return out


CONTACT_ANGLES = {"Ju": (0, 180), "Sa": (0, 180), "Ra": (0,), "Ke": (0,)}   # nodes: the axis already covers 180°


def contacts(t0, months, natal, node="mean"):
    """Exact conjunctions (and, for Jupiter and Saturn, oppositions) of transiting slow planets with natal points,
    including retrograde repeats, by bisection."""
    end = t0 + dt.timedelta(days=30.44 * months)
    out = []
    for tp, angles in CONTACT_ANGLES.items():
        for npn, nl0 in natal.items():
            for ang in angles:
                nl = (nl0 + ang) % 360

                def diff(t, tp=tp, nl=nl):
                    return (positions(jd_of(t), node)[tp]["lon"] - nl + 180) % 360 - 180
                t, d = t0, diff(t0)
                while t < end:
                    t2 = t + dt.timedelta(days=2)   # short step: a contact repeated near a station is not skipped
                    d2 = diff(t2)
                    if (d < 0) != (d2 < 0) and abs(d - d2) < 90:
                        a, b = t, t2
                        while (b - a) > dt.timedelta(hours=6):
                            m = a + (b - a) / 2
                            (a, b) = (a, m) if (diff(m) < 0) != (d < 0) else (m, b)
                        out.append({"date": b.date().isoformat(), "transit": tp, "natal": npn,
                                    "aspect": "opposition" if ang else "conjunction",
                                    "direction": "direct" if d < d2 else "retrograde"})
                    t, d = t2, d2
    return sorted(out, key=lambda r: r["date"])


def compute(date, time, tz, lat, lon, node="mean", year="sidereal", on=None, months=36, extras=True):
    """Everything for one chart as a JSON-ready dict (the calc.json format). ``tz`` = UTC offset in hours."""
    on = on or dt.date.today().isoformat()
    local = dt.datetime.fromisoformat(f"{date}T{time}")
    ut = local - dt.timedelta(hours=tz)
    jd = jd_of(ut)
    P = positions(jd, node)
    A, MC = angles(jd, lat, lon)
    P = {"Asc": {"lon": A, "speed": None, "retro": False}, **P}
    bodies = {}
    for n, p in P.items():
        L = p["lon"]
        nk, pada, _ = nak(L)
        bodies[n] = {"sign": SIGNS[int(L // 30)], "deg": round(L % 30, 4), "lon": round(L, 4), "retro": p["retro"],
                     "speed": None if p["speed"] is None else round(p["speed"], 5),
                     "nakshatra": nk, "pada": pada, "vargas": {f"D{v}": SIGNS[varga(L, v)] for v in VARGAS}}
    ylen = YEAR[year]
    fmt = lambda t: (t + dt.timedelta(hours=tz)).strftime("%Y-%m-%d")
    ser = lambda rows: [{"lord": r["lord"], "start": fmt(r["start"]), "end": fmt(r["end"]),
                         **({"sub": ser(r["sub"])} if "sub" in r else {})} for r in rows]
    dasha = vimshottari(P["Mo"]["lon"], ut, ylen, levels=3)
    t_on = dt.datetime.fromisoformat(on + "T12:00") - dt.timedelta(hours=tz)
    T = positions(jd_of(t_on), node)
    asc_i, moon_i = int(A // 30), int(P["Mo"]["lon"] // 30)
    transits = {n: {"sign": SIGNS[int(p["lon"] // 30)], "deg": round(p["lon"] % 30, 2), "retro": p["retro"],
                    "house_from_lagna": (int(p["lon"] // 30) - asc_i) % 12 + 1,
                    "house_from_moon": (int(p["lon"] // 30) - moon_i) % 12 + 1} for n, p in T.items()}
    meta = {"engine": f"astro {ENGINE_VERSION} on Swiss Ephemeris {swe.version} (pyswisseph, local)",
            **ephemeris_info(jd), "ayanamsa": f"Lahiri {swe.get_ayanamsa_ut(jd):.4f}°", "nodes": node,
            "dasha_year_days": ylen, "houses": "whole sign from the sidereal ascendant; Sripati bhavas in 'bhavas'",
            "birth_local": f"{date} {time} UTC{tz:+}", "lat": lat, "lon": lon, "transit_date": on,
            "transit_time": "12:00 local (birth UTC offset)", "vargas": "Parashari rules, engine.VARGA_METHODS",
            "computed_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    out = {"meta": meta, "bodies": bodies, "mc": round(MC, 4), "bhavas": bhavas(jd, lat, lon),
           "vimshottari": ser(dasha), "transits": transits}
    if extras:
        out["ingresses"] = ingresses(t_on, months, node)
        out["birth_time_sensitivity_minutes"] = sensitivity(ut, lat, lon, P["Mo"]["lon"])
        out["slow_contacts"] = contacts(t_on, months, {n: p["lon"] for n, p in P.items() if n not in ("Ra", "Ke")}, node)
    return out


def render_md(c):
    m = c["meta"]
    L = [f"# Local calculation ({m['engine']})", "", *(f"- {k}: {v}" for k, v in m.items()), "",
         "| Body | Sign | Deg | R | Nakshatra-pada | " + " | ".join(f"D{v}" for v in VARGAS[1:]) + " |",
         "|" + "---|" * (5 + len(VARGAS) - 1)]
    for n, b in c["bodies"].items():
        L.append(f"| {n} | {b['sign']} | {b['deg']:.2f} | {'R' if b['retro'] and n not in ('Ra', 'Ke') else ''} | "
                 f"{b['nakshatra']}-{b['pada']} | " + " | ".join(b["vargas"][f"D{v}"][:3] for v in VARGAS[1:]) + " |")
    on = m["transit_date"]
    birth = m["birth_local"][:10]
    L += ["", "## Vimshottari (MD / AD; PD shown inside the running AD)", ""]
    for md in c["vimshottari"]:
        L.append(f"- **{md['lord']}** {md['start']} → {md['end']}")
        for ad in md["sub"]:
            if ad["end"] >= birth:
                cur = ad["start"] <= on < ad["end"]
                L.append(f"  - {md['lord']}–{ad['lord']} {ad['start']} → {ad['end']}" + (" ← now" if cur else ""))
                if cur:
                    L += [f"    - PD {p['lord']} {p['start']} → {p['end']}" for p in ad["sub"]]
    L += ["", f"## Transits on {on} (houses from lagna / from Moon)", "",
          *(f"- {n}: {t['sign']} {t['deg']}°{' R' if t['retro'] and n not in ('Ra', 'Ke') else ''} — "
            f"H{t['house_from_lagna']} / H{t['house_from_moon']} from Moon" for n, t in c["transits"].items())]
    if "ingresses" in c:
        L += ["", "## Slow-planet sign changes", "",
              *(f"- {r['date']}: {r['planet']} {r['from']} → {r['to']}" for r in c["ingresses"]),
              "", "## Exact contacts of Jupiter, Saturn, Rahu, Ketu with natal points (conjunctions; Ju/Sa oppositions)", "",
              *(f"- {r['date']}: {r['transit']} {'opposite' if r.get('aspect') == 'opposition' else 'over'} natal {r['natal']} ({r['direction']})"
                for r in c["slow_contacts"]),
              "", "## Birth-time sensitivity (minutes earlier / later before each factor changes; — = not within 3 h)", "",
              *(f"- {k}: {v['earlier'] or '—'} earlier / {v['later'] or '—'} later"
                for k, v in c["birth_time_sensitivity_minutes"].items())]
    if "shadbala" in c:
        sb, comp = c["shadbala"], ("sthana", "dig", "kala", "cheshta", "naisargika", "drik")
        L += ["", "## Shadbala (local; virupas, BPHS/Raman — conventions in calc.json)", "",
              "| Planet | " + " | ".join(comp) + " | total (rupas) | required | ratio |", "|---" * (len(comp) + 4) + "|",
              *(f"| {p} | " + " | ".join(f"{v['virupas'][k]:.1f}" for k in comp)
                + f" | {v['total_rupas']:.2f} | {v['required_rupas']} | {v['ratio']:.2f} |" for p, v in sb["planets"].items()),
              "", "Time lords: " + ", ".join(f"{k} {v}" for k, v in sb["time_lords"].items())
              + f"; planetary war: {sb['planetary_war'] or 'none'}"]
    if "ashtakavarga" in c:
        a = c["ashtakavarga"]
        L += ["", "## Ashtakavarga (local; bindus by sign, Aries → Pisces)", "",
              "| | " + " | ".join(s[:3] for s in a["signs"]) + " | total |", "|---" * 14 + "|",
              *(f"| {p} | " + " | ".join(map(str, row)) + f" | {a['totals'][p]} |" for p, row in a["bav"].items()),
              "| **SAV** | " + " | ".join(map(str, a["sav"])) + f" | {a['sav_total']} |",
              "", "SAV by house (1 → 12): " + ", ".join(map(str, a["sav_by_house"]))]
    if "jaimini" in c:
        j = c["jaimini"]
        L += ["", "## Jaimini factors (local)", "",
              "- Chara karakas (7): " + ", ".join(f"{k} {v}" for k, v in j["chara_karakas"]["scheme7"].items()),
              "- Chara karakas (8, Rahu included): " + ", ".join(f"{k} {v}" for k, v in j["chara_karakas"]["scheme8"].items()),
              f"- Karakas within 1′ of each other: {j['chara_karakas']['within_1_arcmin'] or 'none'}",
              f"- Arudha lagna {j['arudha_lagna']}; upapada {j['upapada']}; karakamsa {j['karakamsa']}",
              "- Arudha padas: " + ", ".join(f"{k} {v}" for k, v in j["arudha"].items())]
    if "sensitivity_grid" in c:
        from .sensitivity import render
        L += ["", "## Birth-time sensitivity grid", "", render(c["sensitivity_grid"])]
    return "\n".join(L) + "\n"


def chart_facts_input(c):
    """The input format of the skill's scripts/chart_facts.py."""
    m = c["meta"]
    return {"_note": f"Calculated locally: {m['engine']}, {m['ayanamsa']}, {m['nodes']} nodes; birth {m['birth_local']}",
            "asc": {"sign": c["bodies"]["Asc"]["sign"], "deg": c["bodies"]["Asc"]["deg"]},
            "planets": {n: {"sign": b["sign"], "deg": b["deg"]} for n, b in c["bodies"].items() if n != "Asc"}}


def write_outputs(c, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "calc.json"), "w") as f:
        json.dump(c, f, indent=1, ensure_ascii=False)
    with open(os.path.join(out_dir, "chart.json"), "w") as f:
        json.dump(chart_facts_input(c), f, indent=1)
    with open(os.path.join(out_dir, "calc.md"), "w") as f:
        f.write(render_md(c))
