#!/usr/bin/env python3
"""Build the accuracy reference set (docs/ACCURACY-RUBRIC.md, frozen 2026-11-07) into docs/accuracy/A1.json..A10.json
and docs/accuracy/different-school.json.

G1 values come from pyswisseph called here directly; this script never imports `astro` (rubric §3 G1). G2 values are
hand-entered from page-checked library books (book, edition, PDF and printed page in each case). G3 values are copied
from stored fixtures of independent engines (PyJHora runs, zoneinfo, USNO); the run never re-runs them. G4 values come
from the documented school's source. Charts are named by id (tools/accuracy_charts.py), never inline birth data.

usage: python tools/accuracy_build_cases.py              build the case files (offline)
       python tools/accuracy_build_cases.py --pyjhora    first re-run PyJHora for the ashtakavarga fixture
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zoneinfo

import swisseph as swe

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import accuracy_charts as AC  # noqa: E402

ROOT = AC.ROOT
OUT = os.path.join(ROOT, "docs", "accuracy")
FIX = os.path.join(OUT, "fixtures")
EPHE = os.path.join(ROOT, "ephe")
EPHE_SHA = {"sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
            "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7"}
RUBRIC_SHA = "0ee28d62bb73da4dfd7458bf0a728c00f5708eca018d714a63c5a585df9f0893"
BUILDER = "tools/accuracy_build_cases.py"
SIGNS = "Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius Capricorn Aquarius Pisces".split()
SIGN2 = "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi".split()
NAKS = ("Ashwini Bharani Krittika Rohini Mrigashira Ardra Punarvasu Pushya Ashlesha Magha PurvaPhalguni "
        "UttaraPhalguni Hasta Chitra Swati Vishakha Anuradha Jyeshtha Mula PurvaAshadha UttaraAshadha Shravana "
        "Dhanishtha Shatabhisha PurvaBhadrapada UttaraBhadrapada Revati").split()
BODIES = [("Su", swe.SUN), ("Mo", swe.MOON), ("Ma", swe.MARS), ("Me", swe.MERCURY), ("Ju", swe.JUPITER),
          ("Ve", swe.VENUS), ("Sa", swe.SATURN)]
SEVEN = [b for b, _ in BODIES]
NINE = SEVEN + ["Ra", "Ke"]
MODES = {"lahiri": swe.SIDM_LAHIRI, "true_chitra": swe.SIDM_TRUE_CITRA, "kp": swe.SIDM_KRISHNAMURTI,
         "raman": swe.SIDM_RAMAN}
WEEKDAY_LORD = ["Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Su"]          # Python weekday() order
CHALDEAN = ["Su", "Ve", "Me", "Mo", "Sa", "Ju", "Ma"]
F = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
VARGAS = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
XC_IDS = [f"C{i}" for i in range(1, 10)]
G1_CHARTS = XC_IDS + ["S1", "S2"]

SETTINGS = {
    "ephemeris": "Swiss Ephemeris 2.10.03 files sepl_18.se1/semo_18.se1 (SHA-256 pinned, docs/CALCULATION-ENGINES.md)",
    "ayanamsa": "Lahiri (SIDM_LAHIRI)", "ayanamsa_value": "true (mean + nutation) in positions; mean also reported",
    "positions": "apparent geocentric sidereal: FLG_SIDEREAL|FLG_SWIEPH|FLG_SPEED, FLG_TRUEPOS off",
    "nodes": "mean (Ketu = Rahu + 180)", "time": "civil time minus the UTC offset taken as UT (swe.julday)",
    "houses": "whole sign; Asc/MC from houses_ex 'W' sidereal", "year_length": "365.256363 d (sidereal)",
    "sunrise": "centre of the disc, standard refraction (rise_trans BIT_DISC_CENTER, pressure/temperature 0 = default)",
    "varga_method": "Parashari (astro VARGA_METHODS; PyJHora method 1, D2 method 2)",
}


# ---------------------------------------------------------------------------------------------------------- helpers
def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def check_ephemeris():
    for f, want in EPHE_SHA.items():
        if sha(os.path.join(EPHE, f)) != want:
            sys.exit(f"ephemeris file {f} missing or changed: no build")
    swe.set_ephe_path(EPHE)


def ut_of(cid):
    c = AC.chart(cid)
    return dt.datetime.fromisoformat(f"{c['date']}T{c['time']}") - dt.timedelta(hours=c["tz"])


def jd_of(t):
    return swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60 + t.second / 3600 + t.microsecond / 3.6e9)


def jd_iso(jd):
    """UT Julian day -> ISO instant to the millisecond (JD 2451545.0 = 2000-01-01T12:00 UT)."""
    return (dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=jd - 2451545.0)).isoformat(timespec="milliseconds")


def bodies(jd, node="mean", mode=swe.SIDM_LAHIRI):
    swe.set_sid_mode(mode)
    out = {}
    for n, b in BODIES + [("Ra", swe.MEAN_NODE if node == "mean" else swe.TRUE_NODE)]:
        x, _ = swe.calc_ut(jd, b, F)
        out[n] = (x[0] % 360, x[3])
    out["Ke"] = ((out["Ra"][0] + 180) % 360, out["Ra"][1])
    return out


def angles(jd, lat, lon):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _, am = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    return am[0] % 360, am[1] % 360


def porphyry(jd, lat, lon):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    cusps, _ = swe.houses_ex(jd, lat, lon, b"O", swe.FLG_SIDEREAL)
    return [c % 360 for c in cusps[:12]]


def margin(lon, step):
    """Arc-seconds from lon to the nearest multiple of `step` degrees."""
    r = lon % step
    return round(min(r, step - r) * 3600, 3)


VARGA_EDGES = {30: ([0, 5, 10, 18, 25, 30], [0, 5, 12, 20, 25, 30])}


def varga_margin(lon, n):
    d, odd = lon % 30, int(lon // 30) % 2 == 0
    edges = (VARGA_EDGES[30][0] if odd else VARGA_EDGES[30][1]) if n == 30 else [k * 30 / n for k in range(n + 1)]
    return round(min(abs(d - e) for e in edges) * 3600, 3)


def snp(lon):
    return int(lon // 30) % 12, int(lon // (40 / 3)) % 27, int(lon // (10 / 3)) % 4 + 1


def atoms_snp(pts, tol_arcsec):
    """Sign, nakshatra, pada atoms of {point: lon} with boundary margins (arc-seconds of D1 longitude)."""
    out = []
    for p, L in pts.items():
        s, n, q = snp(L)
        out += [{"key": f"{p}.sign", "value": s, "boundary_margin": margin(L, 30)},
                {"key": f"{p}.nak", "value": n, "boundary_margin": margin(L, 40 / 3)},
                {"key": f"{p}.pada", "value": q, "boundary_margin": margin(L, 10 / 3)}]
    return out


def g1_source(call):
    return {"reference_script": BUILDER, "swe_call": call, "pyswisseph": swe.version, "astro_imported": False}


# ------------------------------------------------------------------------------------------------------ sun, panchang
def rise(jd, lat, lon, kind):
    flag, tret = swe.rise_trans(jd, swe.SUN, kind | swe.BIT_DISC_CENTER, (lon, lat, 0), 0, 0, swe.FLG_SWIEPH)
    return None if flag == -2 else tret[0]


def sun_events(jd, lat, lon):
    """(r1, s, r2): the last sunrise at or before jd, the next sunset, the next sunrise; None if circumpolar."""
    t, last = jd - 2, None
    for _ in range(6):
        r = rise(t, lat, lon, swe.CALC_RISE)
        if r is None or r > jd:
            break
        last, t = r, r + 0.01
    if last is None:
        return None
    s = rise(last, lat, lon, swe.CALC_SET)
    r2 = rise(s, lat, lon, swe.CALC_RISE) if s else None
    return (last, s, r2) if s and r2 else None


def _elong(jd):
    return (swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0] - swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]) % 360


def _sum(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return (swe.calc_ut(jd, swe.SUN, F)[0][0] + swe.calc_ut(jd, swe.MOON, F)[0][0]) % 360


def _moon(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.calc_ut(jd, swe.MOON, F)[0][0] % 360


PANCHANG = {"tithi": (_elong, 12.0), "karana": (_elong, 6.0), "yoga": (_sum, 40 / 3), "nakshatra": (_moon, 40 / 3)}


def element(kind, jd):
    f, step = PANCHANG[kind]
    return int(f(jd) // step) % round(360 / step) + 1


def element_edge(kind, jd, direction):
    """UT JD of the start (direction -1) or end (+1) of the element running at jd, by bisection on calc_ut."""
    f, step = PANCHANG[kind]
    v0 = f(jd)
    k = int(v0 // step)
    target = (k + (direction > 0)) * step
    lo, hi = (jd, jd + 2.0) if direction > 0 else (jd - 2.0, jd)
    ahead = lambda t: (f(t) - target + 180) % 360 - 180 >= 0          # noqa: E731  past the edge
    for _ in range(60):
        mid = (lo + hi) / 2
        if ahead(mid):
            hi = mid
        else:
            lo = mid
    return hi


def vara(jd, lat, lon, tz):
    ev = sun_events(jd, lat, lon)
    if ev is None:
        return None, None
    y, m, d, _ = swe.revjul(ev[0] + tz / 24)
    return WEEKDAY_LORD[dt.date(y, m, d).weekday()], round(min(jd - ev[0], ev[2] - jd) * 86400, 1)


# ------------------------------------------------------------------------------------------------------------ cases
CASES = {f"A{i}": [] for i in range(1, 11)}
INFO = []
COUNTER = {}


def add(area, grade, sub_item, quantity, inp, expected, unit, tolerance, comparison, source, settings=None,
        status="scored", notes="", boundary_threshold=None, into=None):
    key = (area, grade, into is not None)
    COUNTER[key] = COUNTER.get(key, 0) + 1
    cid = f"{area}-{grade}-{'I' if into is not None else ''}{COUNTER[key]:03d}"
    rec = {"id": cid, "area": area, "sub_item": sub_item, "grade": grade, "source": source,
           "settings": SETTINGS | (settings or {}), "input": inp, "quantity": quantity, "expected": expected,
           "unit": unit, "tolerance": tolerance, "comparison": comparison, "boundary_threshold": boundary_threshold,
           "status_before_run": status, "notes": notes}
    (INFO if into is not None else CASES[area]).append(rec)
    return rec


def chart_inp(cid, **kw):
    return {"chart": cid, "chart_file": AC.chart(cid)["source"], **kw}


# ----------------------------------------------------------------------------------------------------------- A1, A2
def build_a1_a2():
    xc = {c["id"]: c for c in json.load(open(AC.XC, encoding="utf-8"))["charts"]}
    for cid in G1_CHARTS:
        c = AC.chart(cid)
        jd = jd_of(ut_of(cid))
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        mean, true = swe.get_ayanamsa_ut(jd), swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)[1]
        add("A1", "G1", "ayanamsa (mean, true), Lahiri", "ayanamsa", chart_inp(cid),
            [{"key": "mean", "value": mean}, {"key": "true", "value": true}], "arcsec", 0.1, "abs_diff",
            g1_source("get_ayanamsa_ut, get_ayanamsa_ex_ut(FLG_SWIEPH)"))
        P = bodies(jd)
        add("A1", "G1", "sidereal longitude Su..Sa, Ra/Ke (mean)", "longitude", chart_inp(cid),
            [{"key": b, "value": P[b][0]} for b in NINE], "arcsec", 0.5, "circular_diff",
            g1_source("calc_ut(FLG_SIDEREAL|FLG_SWIEPH|FLG_SPEED), MEAN_NODE"),
            notes="engine rounds longitudes once to 0.0001 deg (max 0.18 arcsec)")
        motion = []
        for b in NINE:
            spd = P[b][1]
            # retrograde margin: seconds without a change of the speed's sign (station), capped at one day
            mg = 86400
            for s in (60, 600, 3600, 86400):
                if any((bodies(jd + k * s / 86400)[b][1] < 0) != (spd < 0) for k in (-1, 1)):
                    mg = {60: 0, 600: 60, 3600: 600, 86400: 3600}[s]
                    break
            motion += [{"key": f"{b}.speed", "value": spd},
                       {"key": f"{b}.retro", "value": spd < 0, "comparison": "exact", "tolerance": 0,
                        "boundary_margin": mg, "boundary_threshold": 60}]
        add("A1", "G1", "speed and retrograde flag", "motion", chart_inp(cid), motion, "deg/day", 1e-4, "abs_diff",
            g1_source("calc_ut speed (FLG_SPEED)"),
            notes="retro atoms: exact, scored only if no station within 60 s (rubric 6.1); margin in seconds")
        A, MC = angles(jd, c["lat"], c["lon"])
        add("A1", "G1", "Asc, MC", "angles", chart_inp(cid),
            [{"key": "Asc", "value": A}, {"key": "MC", "value": MC}], "arcsec", 1.0, "circular_diff",
            g1_source("houses_ex(b'W', FLG_SIDEREAL) ascmc[0], ascmc[1]"))
        pts = {"Asc": A} | {b: P[b][0] for b in NINE}
        add("A2", "G1", "sign, nakshatra, pada of Asc and nine bodies", "sign_nak_pada", chart_inp(cid),
            atoms_snp(pts, 0.5), "index", 0, "exact",
            g1_source("calc_ut, houses_ex; fixed divisions 30 deg, 13 deg 20', 3 deg 20'"),
            boundary_threshold=2.0,
            notes="sign/nakshatra 0-based index from 0 deg sidereal Aries, pada 1-4; atoms within 2 x 1 arcsec "
                  "(Asc tolerance; bodies 0.5) of an edge are boundary")
    for cid in ["C1", "C2", "C3", "C4", "C5"]:
        jd = jd_of(ut_of(cid))
        P = bodies(jd, node="true")
        add("A1", "G1", "true node Ra/Ke", "longitude", chart_inp(cid, node="true"),
            [{"key": b, "value": P[b][0]} for b in ("Ra", "Ke")], "arcsec", 0.5, "circular_diff",
            g1_source("calc_ut(TRUE_NODE, FLG_SIDEREAL|FLG_SWIEPH|FLG_SPEED)"), settings={"nodes": "true"})
    for cid in ["S1", "S2", "C1", "C2", "C3"]:
        c = AC.chart(cid)
        cusps = porphyry(jd_of(ut_of(cid)), c["lat"], c["lon"])
        add("A1", "G1", "Porphyry points (Sripati madhyas)", "bhava_middles", chart_inp(cid),
            [{"key": f"H{i + 1}", "value": v} for i, v in enumerate(cusps)], "arcsec", 1.0, "circular_diff",
            g1_source("houses_ex(b'O', FLG_SIDEREAL) cusps"))
    for cid in ["S1", "S2"]:
        c = AC.chart(cid)
        m = porphyry(jd_of(ut_of(cid)), c["lat"], c["lon"])
        sandhi = [(m[i] + ((m[(i + 1) % 12] - m[i]) % 360) / 2) % 360 for i in range(12)]
        add("A1", "G4", "Sripati bhava sandhis", "bhava_sandhis", chart_inp(cid),
            [{"key": f"H{i + 1}.end", "value": v} for i, v in enumerate(sandhi)], "arcsec", 1.0, "circular_diff",
            {"school": "Sripati: madhya = Porphyry cusp, sandhi = midpoint of consecutive madhyas",
             "documented": "astro/calc/engine.py:200-209; docs/CALCULATION-ENGINES.md:44-45",
             "value_source": "the school's rule applied to swe houses_ex 'O' cusps (G1 astronomy, rule of the school)"},
            notes="alternatives: Porphyry cusps as bhava starts; other cusp systems (sources not located): not scored")
    # ayanamsa modes at four epochs
    for mode in MODES:
        at = []
        for cid in ("ayan-1900", "ayan-1956", "ayan-2000", "ayan-2050"):
            jd = jd_of(ut_of(cid))
            swe.set_sid_mode(MODES[mode])
            at += [{"key": f"{cid}.mean", "value": swe.get_ayanamsa_ut(jd)},
                   {"key": f"{cid}.true", "value": swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)[1]}]
        add("A1", "G1", f"ayanamsa {mode} at four epochs", "ayanamsa_epochs", {"charts": ["ayan-1900", "ayan-1956",
            "ayan-2000", "ayan-2050"], "chart_file": "oracle_pyjhora.py EXTRA", "ayanamsa": mode}, at, "arcsec", 0.1,
            "abs_diff", g1_source(f"set_sid_mode({mode}); get_ayanamsa_ut, get_ayanamsa_ex_ut"),
            settings={"ayanamsa": mode})
    # G3: PyJHora columns of the 2026-11 cross-check (stored; never re-run)
    xprov = json.load(open(AC.XC, encoding="utf-8"))["provenance"]["pyjhora"]
    src3 = {"engine": "PyJHora", "version": xprov["version"], "run": "tests/reference_charts/crosscheck_2026_11.json "
            "(generated 2026-11-01)", "settings_read_back": xprov["settings"]}
    for cid in XC_IDS:
        pj = xc[cid]["reference"]["pyjhora"]
        add("A1", "G3", "ayanamsa (mean)", "ayanamsa", chart_inp(cid),
            [{"key": "mean", "value": pj["ayanamsa_deg_mean"]}], "arcsec", 0.1, "abs_diff", src3,
            notes="stored to 1e-6 deg (0.0036 arcsec)")
        add("A1", "G3", "sidereal longitude Su..Sa, Ra/Ke (mean)", "longitude", chart_inp(cid),
            [{"key": b, "value": pj["bodies"][b]["lon"]} for b in NINE], "arcsec", 1.0, "circular_diff", src3)
        add("A1", "G3", "Asc", "angles", chart_inp(cid), [{"key": "Asc", "value": pj["bodies"]["Asc"]["lon"]}],
            "arcsec", 10.0, "circular_diff", src3)
        pts = {p: pj["bodies"][p]["lon"] for p in ["Asc"] + NINE}
        exp = []
        for p, L in pts.items():
            b = pj["bodies"][p]
            exp += [{"key": f"{p}.sign", "value": SIGNS.index(b["sign"]), "boundary_margin": margin(L, 30)},
                    {"key": f"{p}.nak", "value": NAKS.index(b["nakshatra"]), "boundary_margin": margin(L, 40 / 3)},
                    {"key": f"{p}.pada", "value": b["pada"], "boundary_margin": margin(L, 10 / 3)}]
        add("A2", "G3", "sign, nakshatra, pada (PyJHora)", "sign_nak_pada", chart_inp(cid), exp, "index", 0, "exact",
            src3, boundary_threshold=20.0,
            notes="boundary threshold 2 x 10 arcsec (G3 Asc tolerance; bodies 1 arcsec), margin from PyJHora's lon")
        exp = []
        for p, L in pts.items():
            for n in VARGAS:
                exp.append({"key": f"{p}.D{n}", "value": SIGNS.index(pj["bodies"][p]["vargas"][f"D{n}"]),
                            "boundary_margin": varga_margin(L, n)})
        add("A2", "G4", "D2..D60 signs of Asc and nine bodies", "vargas", chart_inp(cid), exp, "sign index", 0, "exact",
            {"school": "Parashari vargas as documented (VARGA_METHODS)", "documented": "astro/calc/engine.py:37-53; "
             "docs/CALCULATION-ENGINES.md:46-68", "value_source": src3 | {"varga_method": "PyJHora chart_method 1 "
             "('Traditional Parasara'), D2 method 2 ('Traditional Parasara, only Le and Cn')"}},
            boundary_threshold=20.0,
            notes="every D2..D60 varga has several PyJHora methods (jhora/horoscope/chart/charts.py), so the varga "
                  "sign is school-dependent: G4. Alternatives: tests/fixtures/oracle/pyjhora-edge.json varga_rules "
                  "(different-school table)")
    # informational: the alternative varga schools, as measured on the stored 7200-point grid
    od = json.load(open(AC.OR, encoding="utf-8"))
    for r in od["varga_rules"]:
        if r["verdict"] == "methodology":
            add("A2", "G4", f"varga school {r['key']}", "stored_note", {"grid": "pyjhora-edge.json varga_rules"},
                [{"key": r["key"], "value": r["delta"]}], "grid points differing", None, "none",
                {"engine": "PyJHora", "version": od["provenance"]["tool_version"], "run": od["provenance"]["run_id"]},
                status="different school", notes=r["note"], into=True)


# ---------------------------------------------------------------------------------------------------------- A3, A4
def build_a3_a4():
    od = json.load(open(AC.OR, encoding="utf-8"))
    prov = od["provenance"]
    src = {"engine": "PyJHora", "version": prov["tool_version"], "run": prov["run_id"],
           "fixture": "tests/fixtures/oracle/pyjhora-edge.json boundaries", "settings_read_back": prov["settings"]}
    for cid, b in sorted(od["boundaries"].items()):
        inp = chart_inp(cid, year_days=b["year_days"], moon="engine positions() unrounded")
        st = {"year_length": f"{b['year_days']} d (PyJHora MEAN_SIDEREAL_YEAR), passed to the engine's dasha function"}
        add("A3", "G3", "MD start instants (internal, unrounded Moon)", "vimshottari_md", inp,
            [{"key": lord, "value": t} for lord, t in b["vimshottari MD"]], "s", 1.0, "instant_diff", src, st)
        add("A3", "G3", "AD start instants (internal, unrounded Moon)", "vimshottari_ad", inp,
            [{"key": lord, "value": t} for lord, t in b["vimshottari AD"]], "s", 1.0, "instant_diff", src, st)
        add("A4", "G3", "Yogini MD sequence and start instants", "yogini_md", inp,
            [{"key": f"{i}:{lord}", "value": t} for i, (lord, t) in enumerate(b["yogini MD"])], "s", 1.0,
            "instant_diff", src, st, notes="key n:lord = n-th period from the first PyJHora row; lords must match")
    hpa = {"book": "B. V. Raman, Hindu Predictive Astrology (library PDF '[library copy]"
           "'), reproducing N. C. Lahiri's Indian Ephemeris balance table",
           "pdf_page": "34 (worked example), 147 and 149 (Tables II-III)", "printed_page": "286 (Table III example)",
           "example": "Moon Taurus 25 deg 10': balance of Mars dasha 6 y 0 m 14 d",
           "checker": "T2.2b against the OCR text layer (text/HPA_ocr.jsonl p34, p147, p149), 2026-11-07; value "
                      "first entered in tests/test_dasha_reference.py by an earlier node"}
    add("A3", "G2", "first lord and balance (Lahiri table)", "vimshottari_balance",
        {"moon_lon_deg": 55 + 10 / 60, "note": "Moon at Taurus 25 deg 10' as printed"},
        [{"key": "lord", "value": "Ma", "comparison": "exact", "tolerance": 0},
         {"key": "balance_table_days", "value": (6 + 0 / 12 + 14 / 360) * 365.25}],
        "day", 1.0, "abs_diff", hpa, notes="table days: years of 12 x 30-day months, x 365.25 (tests/"
        "test_dasha_reference.py YMD_DAYS); rubric 6.1: +-1 day table rounding")
    pvr50 = {"book": "P. V. R. Narasimha Rao, Vedic Astrology: An Integrated Approach (library PDF, edition with the "
             "'Looking Back' preface)", "pdf_page": 223, "printed_page": 211, "example": "Example 50",
             "checker": "T2.2b against the text layer (text/PVR.jsonl p223), 2026-11-07; independent check pending T2.2c"}
    add("A3", "G2", "first lord and balance (PVR Example 50)", "vimshottari_balance",
        {"moon_lon_deg": 300 + 2 + 23 / 60, "note": "Moon at Aquarius 2 deg 23' as printed"},
        [{"key": "lord", "value": "Ma", "comparison": "exact", "tolerance": 0},
         {"key": "balance_years", "value": 2.24875}], "year", 0.000005, "abs_diff", pvr50,
        notes="PVR prints fraction 257/800 = 0.32125 and 7 x 0.32125 = 2.24875 years; his dated MD ends use savana "
              "years (p223), a year-length setting not used here, so only the balance in years is scored")
    for name, test in (("dasha_crux34", "test_published_chart_signs_and_balance"),
                       ("dasha_knrao", "test_published_dasha_boundaries")):
        add("A3", "G2", f"private published-chart fixture {name}", "private_test",
            {"test": f"tests/test_dasha_reference.py::{test}", "fixture": f"[private folder]/{name}.json"},
            [], None, None, "private", {"book": "copyrighted book chart, private fixture (not read by T2.2b)"},
            status="private", notes="rubric Q5: scored only in the owner's private run; values never printed")


# ---------------------------------------------------------------------------------------------------------------- A5
BPHS = "Brihat Parasara Hora Sastra, tr. R. Santhanam (library PDF '[library copy]')"


def build_a5():
    ex = {"La": "Aq", "Me": "Aq", "Ju": "Aq", "Ve": "Aq", "Ma": "Ta", "Ra": "Ge", "Mo": "Ge", "Su": "Cp", "Ke": "Le",
          "Sa": "Sc"}
    school = {"school": "Chara dasha, BPHS ch. 46 sl. 155-167 (Santhanam), bphs_santhanam (decision D-3)",
              "documented": "astro/calc/chara.py:1-30; astro/service.py:486-494",
              "value_source": BPHS + ", example chart PDF p546 (printed 555), table PDF p547 (printed 556); page-"
                              "checked by the owner 2026-10-24 (tests/test_chara.py)"}
    alts = "alternatives: Rath's Jaimini Chara (JSR), PVR Narayana dasha, K. N. Rao's Chara (not built)"
    printed = dict(Aq=8, Pi=1, Ar=1, Ta=9, Ge=8, Cn=1, Le=7, Vi=7, Li=4, Sc=6, Sg=2, Cp=5)
    inp = {"signs": ex, "chart": "BPHS ch. 46 example chart (published, signs only)"}
    add("A5", "G4", "sign years (BPHS example, ten signs)", "chara_years", inp,
        [{"key": s, "value": v} for s, v in printed.items() if s not in ("Cp", "Sc")], "years", 0, "exact", school,
        notes=alts + "; Cp and Sc are separate misprint rows")
    add("A5", "G4", "sign years: Capricorn", "chara_years", inp, [{"key": "Cp", "value": 2}], "years", 0, "exact",
        school | {"printed": 5, "evidence": "Yogardha PDF p551 prints 4 1/2 = (2 + 7) / 2; Kendradi PDF p553 prints 2"},
        status="misprint", notes="printed 5, corrected 2 (same book's other pages); excluded")
    add("A5", "G4", "sign years: Scorpio", "chara_years", inp, [{"key": "Sc", "value": 9}], "years", 0, "exact",
        school | {"printed": 6, "evidence": "sl. 158-166: Mars and Ketu tie, the larger count (Ketu) gives 9; owner "
                  "decision 2026-10-24 follows the rule and records the print"},
        status="misprint", notes="printed 6, rule value 9; excluded")
    add("A5", "G4", "dasha order and direction (sl. 167)", "chara_sequence", inp,
        [{"key": str(i), "value": s} for i, s in enumerate("Aq Pi Ar Ta Ge Cn Le Vi Li Sc Sg Cp".split())],
        "sign", 0, "exact", school | {"value_source": BPHS + ", PDF p547 (printed 556): Libra, 9th from the Aquarius "
                                      "lagna, in an odd pada: forward from the lagna"}, notes=alts)
    for sign, order in (("Aq", "Aq Cn Sg Ta Li Pi Le Cp Ge Sc Ar Vi"), ("Pi", "Pi Sg Vi Ge Sc Le Ta Aq Cn Ar Cp Li"),
                        ("Ar", "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi")):
        add("A5", "G4", f"antardasha order ch. 51 ({sign})", "chara_antardashas", {"sign": sign},
            [{"key": str(i), "value": s} for i, s in enumerate(order.split())], "sign", 0, "exact",
            {"school": "BPHS ch. 51 sl. 7-12 (owner default 2026-10-24)", "documented": "astro/service.py:488-491",
             "value_source": BPHS + ", worked lists PDF p614-615 (Santhanam's Aquarius list omits Leo: misprint, "
                                    "recorded in tests/test_chara.py)"},
            notes="alternative: BPHS ch. 50 sl. 90-96 (start from the lord's sign; no order given)")
    home = {"La": "Sg", "Su": "Ar", "Mo": "Ta", "Ma": "Sc", "Ke": "Sc", "Me": "Ge", "Ju": "Cp", "Ve": "Li", "Sa": "Aq",
            "Ra": "Aq"}
    add("A5", "G4", "lord at home gives 12 years", "chara_years",
        {"signs": home, "chart": "synthetic sign chart (tests/test_chara.py)"},
        [{"key": "Li", "value": 12}, {"key": "Sc", "value": 12}, {"key": "Aq", "value": 12}], "years", 0, "exact",
        {"school": "a single lord in its own sign gives 12 (Rath's rule, labelled); both Sc/Aq co-lords at home "
                   "give 12 (BPHS sl. 158)", "documented": "astro/calc/chara.py:20-21",
         "value_source": "JSR p276 (rule statement); BPHS sl. 158 (rule statement)"},
        notes="BPHS silent on a single lord at home (chara.py:20); other schools' rule: not located")
    add("A5", "G4", "Chara dates from birth", "none", {"note": "dates are a labelled convention"}, [], None, None,
        "none", {"school": "sidereal years from birth", "documented": "astro/service.py:487"},
        status="convention without source", notes="BPHS states neither start nor year length")
    for name, pos, table in (
            ("JSR p285 Sri Rama (Rath, Jaimini Chara)", "La=Cn Mo=Cn Ju=Cn Su=Ar Ve=Pi Me=Ta Ke=Ge Ma=Cp Ra=Sg Sa=Li",
             "Ar 10 Ta 11 Ge 11 Cn 12 Le 5 Vi 4 Li 6 Sc 3 Sg 8 Cp 4 Aq 5 Pi 9"),
            ("JSR p286 Einstein (Rath, Jaimini Chara)", "La=Ge Me=Pi Ve=Pi Su=Pi Sa=Pi Ju=Aq Ra=Cp Ma=Cp Ke=Cn Mo=Sc",
             "Ar 10 Ta 11 Ge 8 Cn 7 Le 5 Vi 5 Li 6 Sc 3 Sg 2 Cp 10 Aq 11 Pi 1"),
            ("PVR Example 66, p247-249 (Narayana dasha)", "La=Aq Su=Cn Sa=Ta Mo=Ta Me=Le Ma=Le Ve=Le Ju=Sc Ra=Pi Ke=Vi",
             "Le 1 Cp 8 Ge 2 Sc 9 Ar 4 Vi 1 Aq 9 Cn 3 Sg 11 Ta 3 Li 10 Pi 4"),
            ("CRUX p72-74 Nehru (Narayana dasha; printed Le 10 read as 9, tests/test_chara.py)",
             "La=Cn Mo=Cn Ra=Ge Sa=Le Ju=Sg Ke=Sg Su=Sc Ve=Li Me=Li Ma=Vi",
             "Cn 12 Ge 4 Ta 5 Ar 5 Pi 3 Aq 8 Cp 5 Sg 12 Sc 1 Li 12 Vi 11 Le 9")):
        t = table.split()
        add("A5", "G4", f"sign years, other school: {name}", "chara_years",
            {"signs": dict(kv.split("=") for kv in pos.split()), "chart": name + " (published, signs only)"},
            [{"key": s, "value": int(v)} for s, v in zip(t[::2], t[1::2])], "years", 0, "exact",
            {"school": name.split("(")[1].rstrip(")"), "value_source": name + " (positions and table as entered in "
             "tests/test_chara.py)"}, status="different school", into=True)


# ---------------------------------------------------------------------------------------------------------------- A6
def build_a6():
    xc = {c["id"]: c for c in json.load(open(AC.XC, encoding="utf-8"))["charts"]}
    for cid in G1_CHARTS:
        c = AC.chart(cid)
        jd = jd_of(ut_of(cid))
        r1, s, r2 = sun_events(jd, c["lat"], c["lon"])
        add("A6", "G1", "sunrise, sunset, next sunrise around the birth moment", "sun_events", chart_inp(cid),
            [{"key": "sunrise", "value": jd_iso(r1)}, {"key": "sunset", "value": jd_iso(s)},
             {"key": "next_sunrise", "value": jd_iso(r2)}], "s", 1.0, "instant_diff",
            g1_source("rise_trans(SUN, CALC_RISE/CALC_SET | BIT_DISC_CENTER)"))
        lord, vm = vara(jd, c["lat"], c["lon"], c["tz"])
        exp = []
        for kind in ("tithi", "nakshatra", "yoga", "karana"):
            a, b = element_edge(kind, jd, -1), element_edge(kind, jd, 1)
            exp.append({"key": kind, "value": element(kind, jd), "boundary_margin": round(min(jd - a, b - jd) * 86400, 1)})
        exp.append({"key": "vara", "value": lord, "boundary_margin": vm})
        add("A6", "G1", "tithi, nakshatra, yoga, karana, vara at birth", "panchang_birth", chart_inp(cid), exp, "number",
            0, "exact", g1_source("calc_ut; tithi 12 deg, karana 6 deg of elongation, yoga 13 deg 20' of Sun+Moon, "
            "nakshatra 13 deg 20'; vara = weekday of the local civil date of the sunrise before birth"),
            boundary_threshold=10.0, notes="numbers 1-based (karana 1 = Kimstughna); vara as weekday lord; margin = "
            "seconds to the element's nearest change (vara: to sunrise); threshold 2 x 5 s")
        exp = []
        for kind in ("tithi", "nakshatra", "yoga", "karana"):
            a, b = element_edge(kind, r1, -1), element_edge(kind, r1, 1)
            exp.append({"key": kind, "value": element(kind, r1), "boundary_margin": round(min(r1 - a, b - r1) * 86400, 1)})
        add("A6", "G1", "tithi, nakshatra, yoga, karana at the sunrise that began the Hindu day", "panchang_sunrise",
            chart_inp(cid), exp, "number", 0, "exact", g1_source("rise_trans, calc_ut"), boundary_threshold=10.0)
        add("A6", "G1", "end instants of the elements running at birth", "element_changes", chart_inp(cid),
            [{"key": k, "value": jd_iso(element_edge(k, jd, 1))} for k in ("tithi", "nakshatra", "yoga", "karana")],
            "s", 5.0, "instant_diff", g1_source("bisection on calc_ut"))
        hour = int((jd - r1) * 24)
        hora = CHALDEAN[(CHALDEAN.index(lord) + hour) % 7]
        mins = ((jd - r1) * 24 - hour) * 60
        add("A6", "G4", "hora lord at birth", "hora", chart_inp(cid),
            [{"key": "hora", "value": hora, "boundary_margin": round(min(mins, 60 - mins) * 60, 1)}], "lord", 0,
            "exact", {"school": "equal 60-minute horas from sunrise in Chaldean order (owner Q11, 2026-11-07)",
                      "documented": "astro/calc/strength.py:55", "value_source": "the school's rule on the G1 sunrise "
                      "(rise_trans) and weekday"}, boundary_threshold=10.0,
            notes="alternative: day and night each divided into 12 (Light on Life PDF p211), different-school row")
        is_day = r1 <= jd < s
        part = (s - r1) / 12 if is_day else (r2 - s) / 12
        k = int((jd - (r1 if is_day else s)) / part) + (0 if is_day else 12)
        add("A6", "G4", "hora lord at birth, day/12 and night/12", "hora", chart_inp(cid),
            [{"key": "hora", "value": CHALDEAN[(CHALDEAN.index(lord) + k) % 7]}], "lord", 0, "exact",
            {"school": "unequal horas: day and night each in 12 parts", "value_source": "Light on Life (Defouw, "
             "Svoboda), PDF p211, rule applied to the G1 sunrise and sunset"}, status="different school", into=True)
    xprov = json.load(open(AC.XC, encoding="utf-8"))["provenance"]["pyjhora"]
    src3 = {"engine": "PyJHora", "version": xprov["version"], "run": "tests/reference_charts/crosscheck_2026_11.json",
            "settings_read_back": xprov["settings"]}
    for cid in XC_IDS:
        c = AC.chart(cid)
        jd = jd_of(ut_of(cid))
        ev = sun_events(jd, c["lat"], c["lon"])
        for which, at in (("birth", jd), ("sunrise", ev[0])):
            pj = xc[cid]["reference"]["pyjhora"][f"panchang_{which}"]
            exp = [{"key": k, "value": pj[k], "boundary_margin": round(min(at - element_edge(k, at, -1),
                    element_edge(k, at, 1) - at) * 86400, 1)} for k in ("tithi", "nakshatra", "yoga", "karana")]
            if which == "birth":
                _, vm = vara(jd, c["lat"], c["lon"], c["tz"])
                exp.append({"key": "vara", "value": WEEKDAY_LORD[["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                            "Saturday", "Sunday"].index(pj["vara"])], "boundary_margin": vm})
            add("A6", "G3", f"panchang at {which} (PyJHora)", f"panchang_{which}", chart_inp(cid), exp, "number", 0,
                "exact", src3, boundary_threshold=120.0,
                notes="threshold 2 x 60 s (G3 change-instant tolerance); margins from the G1 change instants")
    usno = {"engine": "US Naval Observatory, Phases of the Moon 2024 (aa.usno.navy.mil, public domain), as stored in "
            "tests/test_panchang.py", "precision": "minute"}
    for ev, kind, ut in (("new Moon", "tithi", "2024-01-11T11:57"), ("full Moon", "tithi", "2024-04-23T23:49"),
                         ("first quarter", "karana", "2024-07-13T22:49"), ("new Moon", "tithi", "2024-10-02T18:49")):
        add("A6", "G3", f"lunar phase instant = {kind} change (USNO {ev})", "element_end_after",
            {"event": f"USNO {ev}", "kind": kind, "search_from_days_before": 0.3},
            [{"key": kind, "value": ut + ":00.000"}], "s", 60.0, "instant_diff", usno,
            notes="USNO rounds to the minute; tolerance 1 min (rubric 6.1 G3)")


# ---------------------------------------------------------------------------------------------------------------- A7
PVR = "P. V. R. Narasimha Rao, Vedic Astrology: An Integrated Approach (library PDF, edition with the 'Looking Back' preface)"


def pvr(pdf, printed, example, own=False):
    return {"book": PVR, "pdf_page": pdf, "printed_page": printed, "example": example,
            "checker": ("T2.2b against the rendered page/text layer, 2026-11-07; value entered by T2.2b: independent "
                        "check pending T2.2c") if own else
                       ("T2.2b against the rendered page/text layer, 2026-11-07; value first entered by an earlier node "
                        "in tests/test_tajika*.py")}


def sun_sid(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.calc_ut(jd, swe.SUN, F)[0][0] % 360


def solar_return(birth_jd, natal, completed):
    approx = birth_jd + completed * 365.256363
    lo, hi = approx - 3, approx + 3
    f = lambda j: (sun_sid(j) - natal + 180) % 360 - 180           # noqa: E731
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return hi


def lon_of(text):
    """'10 Cp 49' -> degrees."""
    d, s, m = text.split()
    return SIGN2.index(s) * 30 + int(d) + int(m) / 60


def build_a7():
    for cid in XC_IDS:
        bj = jd_of(ut_of(cid))
        natal = sun_sid(bj)
        for n in (10, 30):
            add("A7", "G1", f"varsha pravesh instant, {n} completed years", "varsha_pravesh", chart_inp(cid, completed=n),
                [{"key": "return", "value": jd_iso(solar_return(bj, natal, n))}], "s", 1.0, "instant_diff",
                g1_source("bisection on calc_ut sidereal Sun to the natal sidereal Sun (unrounded)"))
    add("A7", "G2", "varsha pravesh instant (Ex 118, 34th year)", "tajika_return", chart_inp("PVR-Ex118", year=34),
        [{"key": "local", "value": "2000-03-08T04:41:21"}], "s", 60.0, "local_diff",
        pvr(379, 367, "Example 118"))
    add("A7", "G2", "varsha pravesh instant (Exercise 47, 27th year)", "tajika_return", chart_inp("PVR-Ex118", year=27),
        [{"key": "local", "value": "1993-03-08T09:36:18"}], "s", 60.0, "local_diff",
        pvr(385, 373, "Exercise 47 answer (exact method)"))
    add("A7", "G2", "varsha pravesh instant (Ex 122, 22nd year)", "tajika_return", chart_inp("PVR-Ex122", year=22),
        [{"key": "local", "value": "1993-06-01T13:30:04"}], "s", 60.0, "local_diff",
        pvr(408, 396, "Example 122", own=True))
    add("A7", "G2", "annual lagna sign, day/night, muntha (Ex 118)", "tajika_frame", chart_inp("PVR-Ex118", year=34),
        [{"key": "lagna_sign", "value": "Capricorn"}, {"key": "day_or_night", "value": "night"},
         {"key": "muntha", "value": "Taurus"}], "category", 0, "exact", pvr("380, 393", "368, 381", "Chart 66, Example 120"))
    add("A7", "G2", "annual positions (Ex 118, Chart 66)", "tajika_positions", chart_inp("PVR-Ex118", year=34),
        [{"key": k, "value": lon_of(v)} for k, v in (("Asc", "10 Cp 49"), ("Su", "23 Aq 50"), ("Mo", "15 Pi 13"),
                                                     ("Ma", "24 Pi 58"), ("Me", "11 Aq 27"), ("Ju", "10 Ar 10"),
                                                     ("Ve", "29 Cp 20"), ("Sa", "19 Ar 09"))],
        "arcmin", 2.0, "circular_diff", pvr(380, 368, "Chart 66 table", own=True),
        notes="Moon and Mars were in tests/test_tajika.py; the other six read by T2.2b from the chart table")
    add("A7", "G2", "harsha bala (Ex 119 on Ex 118)", "tajika_harsha", chart_inp("PVR-Ex118", year=34),
        [{"key": p, "value": v} for p, v in dict(Su=0, Mo=15, Ma=0, Me=10, Ju=5, Ve=10, Sa=5).items()], "units", 0,
        "exact", pvr(388, 376, "Example 119"))
    add("A7", "G2", "year-lord candidates and year lord (Ex 120)", "tajika_year_lord", chart_inp("PVR-Ex118", year=34),
        [{"key": f"candidate{i + 1}", "value": p} for i, p in enumerate(["Ju", "Su", "Ve", "Sa", "Ma"])] +
        [{"key": "year_lord", "value": "Ma"}], "planet", 0, "exact", pvr(393, 381, "Example 120"))
    add("A7", "G2", "pancha vargeeya bala of Mars (Ex 120)", "tajika_pvb", chart_inp("PVR-Ex118", year=34),
        [{"key": "Ma", "value": 13.7}], "units", 0.05, "abs_diff", pvr(393, 381, "Example 120"),
        notes="printed 13.7; tolerance half the last printed digit")
    add("A7", "G2", "sahams Samartha and Vanik (Ex 121)", "tajika_sahams", chart_inp("PVR-Ex118", year=34),
        [{"key": "Samartha", "value": lon_of("5 Pi 02")}, {"key": "Vanik", "value": lon_of("7 Sg 04")}], "arcmin", 2.0,
        "circular_diff", pvr(396, 384, "Example 121"),
        notes="Samartha (night reversal + 30 deg) and Vanik; Artha (2 Sc 30) needs the 2nd house cusp, which the "
              "engine does not compute (tajika.NOT_COMPUTED): out of scope, not a case")
    add("A7", "G2", "annual positions (Ex 122, Chart 67)", "tajika_positions", chart_inp("PVR-Ex122", year=22),
        [{"key": k, "value": lon_of(v)} for k, v in (("Asc", "7 Vi 13"), ("Su", "17 Ta 04"), ("Mo", "4 Li 48"),
                                                     ("Ma", "23 Cn 53"), ("Me", "4 Ge 47"), ("Ju", "10 Vi 59"),
                                                     ("Ve", "1 Ar 37"), ("Sa", "6 Aq 29"))],
        "arcmin", 2.0, "circular_diff", pvr(409, 397, "Chart 67 table", own=True))
    add("A7", "G2", "vivaha saham (Ex 122)", "tajika_sahams", chart_inp("PVR-Ex122", year=22),
        [{"key": "Vivaha", "value": 240 + 2 + 22 / 60}], "arcmin", 2.0, "circular_diff", pvr(409, 397, "Example 122"))
    add("A7", "G2", "Mudda dasha: first two lords (Ex 122)", "tajika_mudda_lords", chart_inp("PVR-Ex122", year=22),
        [{"key": "0", "value": "Ra"}, {"key": "1", "value": "Ju"}], "planet", 0, "exact",
        pvr(412, 400, "Example 122 (Mudda dasa)"))
    add("A7", "G2", "Mudda dasha: end of Rahu (Ex 122)", "tajika_mudda_end", chart_inp("PVR-Ex122", year=22),
        [{"key": "Ra.end", "value": "1993-07-14"}], "day", 0, "date_exact", pvr(412, 400, "Example 122") | {
            "corrected": "1993-07-16", "evidence": "same page defines a Mudda day as the Sun moving exactly 1 deg; "
            "42.66 such days from 1 Jun 1993 end on 16 Jul (the print adds 42.66 civil days)"},
        status="misprint", notes="recorded in astro/calc/tajika.py SOURCES['mudda']; excluded")
    add("A7", "G2", "Patyayini dasha order (Ex 122, Table 75)", "tajika_patyayini_order", chart_inp("PVR-Ex122", year=22),
        [{"key": str(i), "value": p} for i, p in enumerate(["Ve", "Me", "Mo", "Sa", "Lg", "Ju", "Su", "Ma"])],
        "planet", 0, "exact", pvr(411, 399, "Example 122, Table 75"))
    add("A7", "G2", "Patyayini Mercury dasha dates (Ex 122)", "tajika_patyayini_me", chart_inp("PVR-Ex122", year=22),
        [{"key": "Me.start", "value": "1993-06-26"}, {"key": "Me.end", "value": "1993-08-13"}], "day", 1, "date_diff",
        pvr(410, 398, "Example 122"), notes="PVR prints dates only; +-1 day (rubric 6.1, book rounding)")
    add("A7", "G2", "year lord (Ex 122)", "tajika_year_lord", chart_inp("PVR-Ex122", year=22),
        [{"key": "year_lord", "value": "Me"}], "planet", 0, "exact", pvr(411, 399, "Example 122 ('varsheswara')"))


# ---------------------------------------------------------------------------------------------------------------- A8
def build_a8():
    def bphs(pdf, printed, what):
        return {"book": BPHS, "pdf_page": pdf, "printed_page": printed, "example": what,
                "checker": "T2.2b against the rendered page/text layer, 2026-11-07; value first entered in tests/"
                           "test_strength.py or test_regressions.py by an earlier node"}
    add("A8", "G2", "uchcha bala (Sun 12 deg 15' Pisces)", "uchcha_bala",
        chart_inp("S1", override={"Su": 342.25}), [{"key": "Su", "value": 50.75}], "virupa", 0.02, "abs_diff",
        bphs("276-277", "264-265", "Sun Pisces 12 deg 15' -> (342 deg 15' - 190 deg) / 3 = 50.75 virupas"),
        notes="the Sun's longitude is set to the printed value on chart S1 (as tests/test_strength.py does)")
    add("A8", "G2", "naisargika bala", "naisargika", chart_inp("S1"),
        [{"key": p, "value": v * 60} for p, v in dict(Su=1.0, Mo=0.857, Ma=0.286, Me=0.429, Ju=0.571, Ve=0.714,
                                                      Sa=0.143).items()], "virupa", 0.03, "abs_diff",
        bphs(288, 276, "Naisargika bala table in rupas (3 decimals)"),
        notes="printed in rupas to 0.001: tolerance half the last digit = 0.03 virupa; checker: T2.2b own read")
    add("A8", "G2", "required rupas (Shadbala pinda)", "required_rupas", chart_inp("S1"),
        [{"key": p, "value": v} for p, v in dict(Su=390, Mo=360, Ma=300, Me=420, Ju=390, Ve=330, Sa=300).items()],
        "virupa", 0.5, "abs_diff", bphs(299, "287", "ch. 27 sl. 32-33"))
    add("A8", "G2", "abda, masa, dina lords (BPHS worked example)", "time_lords_date", {"date": "1984-06-01",
        "note": "the book gives a date only; the engine is run at local noon, Ujjain (IST)"},
        [{"key": "year", "value": "Ju"}, {"key": "month", "value": "Ve"}, {"key": "weekday", "value": "Ve"}], "lord", 0,
        "exact", bphs("283-284", "271-272", "1 Jun 1984: Ahargana 65295, year Jupiter, month Venus, Friday"))
    r = json.load(open(AC.RAMAN, encoding="utf-8"))
    add("A8", "G3", "drik bala (Raman's published example)", "drik_bala", chart_inp("raman-1918", ayanamsa="raman"),
        [{"key": p, "value": v} for p, v in r["expected"]["drik_virupas"].items()], "virupa", 0.5, "abs_diff",
        {"engine": "B. V. Raman, Graha and Bhava Balas, quoted in the PyJHora source (jhora/horoscope/chart/"
         "strength.py)", "version": "PyJHora 4.8.7 source", "run": "tests/reference_charts/raman_1918.json",
         "grade_note": "rubric Q6: G3 until the book page is checked (book not in the library)"},
        settings={"ayanamsa": "Raman (SIDM_RAMAN), as the book"})
    add("A8", "G4", "planetary war winner: Venus always wins", "war_winner",
        {"latitudes": {"Ma": 1.0, "Ve": -3.0, "Sa": 0.5, "Ju": 2.0}, "note": "synthetic ecliptic latitudes"},
        [{"key": "Ve-Ma", "value": "Ve"}, {"key": "Sa-Ve", "value": "Ve"}, {"key": "Ma-Sa", "value": "Ma"},
         {"key": "Sa-Ju", "value": "Ju"}], "planet", 0, "exact",
        {"school": "BPHS ch. 79 sl. 9: Venus always wins; otherwise the northern planet",
         "documented": "astro/calc/strength.py:58-60 (SHADBALA_CONVENTIONS yuddha)",
         "value_source": BPHS + ", ch. 79 sl. 9 (rule statement)"},
        notes="alternative: Light on Life, higher latitude wins with no Venus exception (not scored)")


# ---------------------------------------------------------------------------------------------------------------- A9
CHART6 = {"Asc": "Vi", "Su": "Ge", "Mo": "Pi", "Ma": "Ge", "Me": "Ge", "Ju": "Le", "Ve": "Ar", "Sa": "Le"}
PVR_EX19 = {"Su": "5 3 5 3 4 4 2 3 5 4 5 5", "Mo": "3 2 5 3 6 3 4 5 5 5 3 5", "Ma": "4 3 4 3 4 3 2 5 1 3 3 4",
            "Me": "7 4 7 4 4 3 4 4 4 3 6 4", "Ju": "4 3 5 6 3 7 4 3 5 6 5 5", "Ve": "8 7 4 3 3 2 4 6 4 4 4 3",
            "Sa": "3 3 4 3 2 3 2 3 4 5 3 4"}
PVR_EX20 = "34 25 34 25 26 25 22 29 28 30 29 30"


def chart_signs(cid):
    c = AC.chart(cid)
    jd = jd_of(ut_of(cid))
    P = bodies(jd)
    return {"Asc": int(angles(jd, c["lat"], c["lon"])[0] // 30)} | {b: int(P[b][0] // 30) for b in SEVEN}


PYJ_BAV = os.path.join(FIX, "pyjhora-bav.json")
BAV_WORKER = r'''
import json, sys, importlib.metadata as md
from jhora.horoscope.chart import ashtakavarga
req = json.load(open(sys.argv[1]))
out = {}
for cid, signs in req.items():
    h2p = [[] for _ in range(12)]
    for i, p in enumerate(["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]):
        h2p[signs[p]].append(str(i))
    h2p[signs["Asc"]].append("L")
    h2p[0] += ["7", "8"]          # nodes: PyJHora looks up planet 7 before replacing it by the lagna; no effect on BAV
    bav, sav, _ = ashtakavarga.get_ashtaka_varga(["/".join(x) for x in h2p])
    out[cid] = {"bav": {p: list(map(int, bav[i])) for i, p in enumerate(["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"])},
                "sav": list(map(int, sav))}
json.dump({"version": md.version("PyJHora"), "charts": out}, open(sys.argv[2], "w"), indent=1, sort_keys=True)
'''


def run_pyjhora_bav():
    py = os.path.join(ROOT, ".venv-pyjhora", "bin", "python")
    req = {cid: chart_signs(cid) for cid in G1_CHARTS} | {"PVR-Chart6": {k: SIGN2.index(v) for k, v in CHART6.items()}}
    with tempfile.TemporaryDirectory() as tmp:
        for name, body in (("w.py", BAV_WORKER), ("in.json", json.dumps(req))):
            open(os.path.join(tmp, name), "w").write(body)
        subprocess.run([py, "-I", os.path.join(tmp, "w.py"), os.path.join(tmp, "in.json"), os.path.join(tmp, "o.json")],
                       cwd=tmp, check=True)
        res = json.load(open(os.path.join(tmp, "o.json")))
    os.makedirs(FIX, exist_ok=True)
    doc = {"provenance": {"tool": "PyJHora", "tool_version": res["version"], "license": "AGPL-3.0 (out of process, "
           "numbers stored only)", "run_id": f"pyjhora-{res['version']}-bav-{dt.date.today().isoformat()}",
           "call": "jhora.horoscope.chart.ashtakavarga.get_ashtaka_varga(house_to_planet_list)",
           "input": "sign placements of Su..Sa and Asc: G1 (swe direct, Lahiri, apparent) for C1..C9, S1, S2; PVR "
                    "Chart 6 printed signs", "harness": BUILDER + " --pyjhora"},
           "signs": req, "charts": res["charts"]}
    json.dump(doc, open(PYJ_BAV, "w"), indent=1, sort_keys=True)


def build_a9():
    note = ("BAV tables are not school-dependent here: PVR Tables 18-25 (PDF p158-162), PyJHora's const.ashtaka_varga_"
            "dict and BPHS ch. 66 (Santhanam, PDF p837-845, dot lists; e.g. Venus from Mars dotted in 1, 2, 5, 7, 8, 10) "
            "give the same benefic houses, so G2/G3 (rubric 3 step 1)")
    inp6 = {"signs": CHART6, "chart": "PVR Chart 6 (published; sign placements read from the chart table, PDF p119)"}
    for p in SEVEN:
        add("A9", "G2", f"BAV of {p} (PVR Chart 6)", "bav", inp6,
            [{"key": f"{p}.{SIGN2[i]}", "value": int(v)} for i, v in enumerate(PVR_EX19[p].split())], "bindu", 0,
            "exact", pvr(175, 163, "Exercise 19 answer; chart: Chart 6 (PDF p119, printed 107)", own=True), notes=note)
    add("A9", "G2", "SAV (PVR Chart 6)", "bav", inp6,
        [{"key": f"SAV.{SIGN2[i]}", "value": int(v)} for i, v in enumerate(PVR_EX20.split())], "bindu", 0, "exact",
        pvr(175, 163, "Exercise 20 answer; chart: Chart 6", own=True), notes=note)
    pj = json.load(open(PYJ_BAV, encoding="utf-8"))
    src3 = {"engine": "PyJHora", "version": pj["provenance"]["tool_version"], "run": pj["provenance"]["run_id"],
            "fixture": "docs/accuracy/fixtures/pyjhora-bav.json", "settings": "PyJHora const.ashtaka_varga_dict; sign "
            "placements from G1 (swe direct, Lahiri, apparent)"}
    for cid in G1_CHARTS:
        r = pj["charts"][cid]
        add("A9", "G3", "BAV of Su..Sa and SAV (PyJHora)", "bav", chart_inp(cid),
            [{"key": f"{p}.{SIGN2[i]}", "value": v} for p in SEVEN for i, v in enumerate(r["bav"][p])] +
            [{"key": f"SAV.{SIGN2[i]}", "value": v} for i, v in enumerate(r["sav"])], "bindu", 0, "exact",
            src3 | {"signs_used": pj["signs"][cid]}, notes=note)


# --------------------------------------------------------------------------------------------------------------- A10
def build_a10():
    E = "edge_suite.json"
    pairs = [("moon-sign", "Mo", "sign"), ("moon-nak", "Mo", "nak"), ("moon-pada", "Mo", "pada"),
             ("asc-sign", "Asc", "sign"), ("d9-lagna", "Asc", "pada"), ("dasha-edge", "Mo", "nak")]
    for stem, pt, kind in pairs:
        for side in ("before", "after"):
            cid = f"{stem}-{side}"
            c = AC.chart(cid)
            jd = jd_of(ut_of(cid))
            L = angles(jd, c["lat"], c["lon"])[0] if pt == "Asc" else bodies(jd)[pt][0]
            want = {f"{pt}.nak", f"{pt}.pada"} if kind == "pada" else {f"{pt}.{kind}"}
            at = [a for a in atoms_snp({pt: L}, 0.5) if a["key"] in want]
            add("A10", "G1", f"{pt} {kind} 30 s {side} an edge", "sign_nak_pada", chart_inp(cid), at, "index", 0,
                "exact", g1_source("calc_ut / houses_ex; fixed divisions"), boundary_threshold=2.0,
                notes=f"edge chart from {E}; the side comes from swe directly, not the engine's golden block"
                      + ("; Asc pada with nakshatra = the navamsa division (D9 lagna edge)" if stem == "d9-lagna" else ""))
    for cid in ("polar-day", "polar-night"):
        c = AC.chart(cid)
        jd = jd_of(ut_of(cid))
        add("A10", "G1", "polar day/night flag", "polar_flag", chart_inp(cid),
            [{"key": "polar", "value": sun_events(jd, c["lat"], c["lon"]) is None}], "flag", 0, "exact",
            g1_source("rise_trans returns -2 (circumpolar)"))
    add("A10", "G4", "polar sunrise fallback 06:00/18:00 local apparent time", "none", {"charts": ["polar-day",
        "polar-night"]}, [], None, None, "none", {"school": "06:00/18:00 local apparent time",
        "documented": "astro/calc/panchang.py:31; astro/calc/strength.py:119-122"},
        status="convention without source", notes="no published school; only the flag is scored")
    for cid in ("midnight-before", "midnight-after", "pre-sunrise"):
        c = AC.chart(cid)
        lord, vm = vara(jd_of(ut_of(cid)), c["lat"], c["lon"], c["tz"])
        add("A10", "G1", "vara of the Hindu day near midnight/sunrise", "vara", chart_inp(cid),
            [{"key": "vara", "value": lord, "boundary_margin": vm}], "lord", 0, "exact",
            g1_source("rise_trans; weekday of the local civil date of the sunrise before birth"), boundary_threshold=2.0)
    for cid in ("leap-2024", "leap-2000", "south-west", "cal-1582", "cal-1500"):
        P = bodies(jd_of(ut_of(cid)))
        note = "1500 lies outside sepl_18/semo_18 (1800-2399): Swiss Ephemeris falls back to Moshier on both sides" \
            if cid == "cal-1500" else ""
        add("A10", "G1", "longitudes on a leap day / far-past date / south-west", "longitude", chart_inp(cid),
            [{"key": b, "value": P[b][0]} for b in NINE], "arcsec", 0.5, "circular_diff",
            g1_source("calc_ut(FLG_SIDEREAL|FLG_SWIEPH|FLG_SPEED)"), notes=note)
    for cid in ("me-station-before", "me-station-after"):
        jd = jd_of(ut_of(cid))
        spd = bodies(jd)["Me"][1]
        add("A10", "G1", "Mercury retrograde flag a day either side of a station", "motion", chart_inp(cid),
            [{"key": "Me.retro", "value": spd < 0, "comparison": "exact", "tolerance": 0}], "flag", 0, "exact",
            g1_source("calc_ut speed sign"))
    tzsrc = {"engine": "IANA tz database through Python zoneinfo", "tzdb": tzdb_version(),
             "call": "datetime.replace(tzinfo=ZoneInfo(zone), fold).utcoffset(); gap/fold by round trip"}
    for zone, local, fold in (("Asia/Kolkata", "1943-06-01T06:30", None), ("Asia/Kolkata", "1942-09-01T08:00", None),
                              ("Europe/London", "1969-01-15T12:00", None), ("America/New_York", "2021-07-04T13:15", None),
                              ("America/New_York", "1975-10-26T01:30", None),
                              ("Asia/Kathmandu", "1980-06-01T12:00", None), ("Asia/Kathmandu", "1990-06-01T12:00", None),
                              ("Australia/Adelaide", "1965-02-01T14:00", None), ("Pacific/Auckland", "1950-12-31T23:30", None),
                              ("America/Sao_Paulo", "2020-03-21T09:00", None), ("America/New_York", "2021-03-14T02:30", None),
                              ("America/New_York", "2021-11-07T01:30", None), ("America/New_York", "2021-11-07T01:30", 0),
                              ("America/New_York", "2021-11-07T01:30", 1)):
        add("A10", "G3", "UTC offset from the tz database (gap refused, fold required)", "tz_offset",
            {"zone": zone, "local": local, "fold": fold}, [{"key": "offset", "value": tz_expect(zone, local, fold)}],
            "hours", 0, "exact", tzsrc, notes="synthetic clock times (tests/test_timezones.py and the C1..C9 places)")


def tzdb_version():
    for root in zoneinfo.TZPATH:
        try:
            with open(os.path.join(root, "tzdata.zi"), encoding="utf-8") as f:
                return f.readline().split()[-1]
        except (OSError, IndexError):
            continue
    try:
        import tzdata
        return tzdata.IANA_VERSION
    except (ImportError, AttributeError):
        return "unknown"


def tz_expect(zone, local, fold):
    z = zoneinfo.ZoneInfo(zone)
    t = dt.datetime.fromisoformat(local)
    a, b = t.replace(tzinfo=z, fold=0), t.replace(tzinfo=z, fold=1)
    exists = any(x.astimezone(dt.timezone.utc).astimezone(z).replace(tzinfo=None) == t for x in (a, b))
    if not exists:
        return "gap"
    if a.utcoffset() != b.utcoffset() and fold is None:
        return "fold required"
    return (b if fold == 1 else a).utcoffset().total_seconds() / 3600


# -------------------------------------------------------------------------------------------------------------- main
def write():
    os.makedirs(OUT, exist_ok=True)
    meta = {"rubric": "docs/ACCURACY-RUBRIC.md", "rubric_sha256": RUBRIC_SHA, "built_by": BUILDER,
            "builder_sha256": sha(os.path.abspath(__file__)), "pyswisseph": swe.version,
            "ephemeris_sha256": EPHE_SHA}
    for area, cases in CASES.items():
        assert len({c["id"] for c in cases}) == len(cases)
        for g in ("G1", "G2", "G3", "G4"):
            assert sum(c["grade"] == g for c in cases) <= 60, (area, g)       # rubric §8: cap 60 per grade and area
        json.dump(meta | {"area": area, "cases": sorted(cases, key=lambda c: c["id"])},
                  open(os.path.join(OUT, f"{area}.json"), "w", encoding="utf-8"), indent=1, sort_keys=True,
                  ensure_ascii=False, allow_nan=False)
        open(os.path.join(OUT, f"{area}.json"), "a").write("\n")
    json.dump(meta | {"area": "informational", "cases": sorted(INFO, key=lambda c: c["id"])},
              open(os.path.join(OUT, "different-school.json"), "w", encoding="utf-8"), indent=1, sort_keys=True,
              ensure_ascii=False, allow_nan=False)
    open(os.path.join(OUT, "different-school.json"), "a").write("\n")


def main(argv):
    check_ephemeris()
    if "--pyjhora" in argv:
        run_pyjhora_bav()
    build_a1_a2()
    build_a3_a4()
    build_a5()
    build_a6()
    build_a7()
    build_a8()
    build_a9()
    build_a10()
    write()
    for area, cases in CASES.items():
        grades = {g: sum(c["grade"] == g and c["status_before_run"] == "scored" for c in cases) for g in ("G1", "G2", "G3", "G4")}
        print(area, grades, "other:", sum(c["status_before_run"] != "scored" for c in cases))
    print("different school:", len(INFO))


if __name__ == "__main__":
    main(sys.argv[1:])
