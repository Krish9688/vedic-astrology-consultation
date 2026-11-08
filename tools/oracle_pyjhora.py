#!/usr/bin/env python3
"""PyJHora differential oracle (roadmap P6-1). Dev only: not shipped, not run in CI, never imported by astro/ or the
skill. PyJHora (AGPL) runs in its own venv in a subprocess on synthetic charts only; this file holds no PyJHora code,
only calls to its public functions inside WORKER. PyJHora is a second opinion, never a golden.

usage: python3 tools/oracle_pyjhora.py setup [--venv DIR]      create the venv, pip-install PyJHora (pinned)
       python -m tools.oracle_pyjhora run [--venv DIR] [--out tests/fixtures/oracle/pyjhora-edge.json]
       (run needs the project venv: astro + pydantic; results feed astro.calc.compare verdicts)
Pinned PyJHora settings (its defaults differ): LAHIRI (default TRUE_PUSHYA), MEAN_SIDEREAL_YEAR (default
TRUE_SIDEREAL_YEAR), apparent positions (default FLG_TRUEPOS), mean nodes (default true), sunrise with refraction
(default without), and the engine's own ephemeris files (PyJHora ships none, so it would fall back to Moshier).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PYJHORA = "PyJHora==4.8.7"
# PyJHora's wheel declares no dependencies; these are its requirements.txt pins that its calc path imports.
# timezonefinder 6.5.2 has no cp313 wheel (h3 build fails); 6.6.3 is used — only for place lookup, never called here.
DEPS = ["pyswisseph==2.10.3.2", "numpy==2.1.1", "pytz==2024.1", "geocoder==1.38.1", "geopy==2.4.1",
        "Requests==2.32.3", "reverse_geocode==1.6.6", "setuptools==69.5.1", "python-dateutil", "timezonefinder==6.6.3"]
DEFAULT_VENV = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "astro-oracle",
                            "pyjhora-4.8.7")
OUT = os.path.join(ROOT, "tests", "fixtures", "oracle", "pyjhora-edge.json")
EDGE = os.path.join(ROOT, "tests", "reference_charts", "edge_suite.json")
BODY = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]          # PyJHora planet ids 0..8
VARGAS = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
# PyJHora chart_method that reproduces engine.varga (found on a 0.05° grid, 0 differences; re-checked every run).
VARGA_METHOD = {d: 1 for d in VARGAS} | {2: 2}
# Variants recorded as conventions (PyJHora method numbers and its own labels; engine.VARGA_METHODS has ours).
VARIANTS = {2: {1: "Parasara hora with parivritti and even reversal (PVR)", 3: "Raman method",
                4: "Parivritti dwaya", 6: "Somanatha"},
            24: {2: "Parasara with even-sign reversal", 3: "even-sign double reversal (PyJHora function default)"},
            30: {2: "Parivritti cyclic", 3: "Shastyamsa-like", 4: "Parivritti even reverse", 5: "Somanatha"}}
TOL = {"position_arcmin": "compare.POS_TOL_ARCMIN (1′), ascendant compare.ASC_TOL_ARCMIN (3′)",
       "dasha_days": "compare.DASHA_TOL_DAYS (3 days) on local-date Vimshottari MD/AD and Yogini MD boundaries; a "
                     "tolerance, not a measured gap: the exact gap is in 'timing'",
       "timing_seconds": "matched (same unrounded Moon and year length): 1 s; as shipped (Moon rounded to 0.0001°, "
                         "QA-F3, and the engine's 365.256363-day year): within SHIPPED_BOUND_S",
       "ayanamsa_deg": 1e-6, "sunrise_minutes": 1, "panchang": "exact element numbers at the birth moment",
       "varga": "exact sign"}

# Synthetic charts beyond the edge suite (no real person). S1/S2 are the test charts in tests/test_behaviour_static.py.
EXTRA = [
    {"id": "S1", "date": "1992-03-14", "time": "09:40:00", "tz": 0, "lat": 51.5, "lon": -0.12, "check": "test chart S1"},
    {"id": "S2", "date": "1990-05-17", "time": "06:30:00", "tz": 5.5, "lat": 19.07, "lon": 72.88, "check": "test chart S2"},
    {"id": "ayan-1900", "date": "1900-01-01", "time": "12:00:00", "tz": 0, "lat": 51.5, "lon": -0.12, "check": "ayanamsa table"},
    {"id": "ayan-1956", "date": "1956-03-21", "time": "12:00:00", "tz": 0, "lat": 51.5, "lon": -0.12, "check": "ayanamsa table (Lahiri epoch year)"},
    {"id": "ayan-2000", "date": "2000-01-01", "time": "12:00:00", "tz": 0, "lat": 51.5, "lon": -0.12, "check": "ayanamsa table (J2000)"},
    {"id": "ayan-2050", "date": "2050-01-01", "time": "12:00:00", "tz": 0, "lat": 51.5, "lon": -0.12, "check": "ayanamsa table"},
    {"id": "dst-gap-after", "date": "2021-03-14", "time": "03:30:00", "tz": -4, "lat": 40.71, "lon": -74.01, "check": "first hour after a US spring-forward gap (offset -04:00 given)"},
    {"id": "cal-1582", "date": "1582-10-15", "time": "12:00:00", "tz": 1, "lat": 41.9, "lon": 12.5, "check": "first Gregorian day"},
    {"id": "cal-1500", "date": "1500-03-01", "time": "12:00:00", "tz": 1, "lat": 41.9, "lon": 12.5, "check": "pre-1582 date (proleptic Gregorian on both sides)"},
    {"id": "south-west", "date": "2015-08-10", "time": "18:20:00", "tz": -3, "lat": -34.6, "lon": -58.38, "check": "southern and western hemisphere"},
]

WORKER = r'''
import json, sys, importlib.metadata as md
inp, out, ephe = sys.argv[1], sys.argv[2], sys.argv[3]
import swisseph as swe
from jhora import const, utils
from jhora.panchanga import drik
from jhora.horoscope.chart import charts
from jhora.horoscope.dhasa.graha import vimsottari, yogini
if ephe != "-":
    swe.set_ephe_path(ephe)
drik.set_ayanamsa_mode("LAHIRI")
const.dhasa_year_duration_default = const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR
const.set_planet_positions_true(False)
const.RISE_SET_USE_REFRACTION = True
const.set_node_mode(False)
drik.set_planet_list(set_rahu_ketu_as_true_nodes=False)
drik.refresh_planet_flags()
req = json.load(open(inp))
res = {"version": md.version("PyJHora"), "pyswisseph": md.version("pyswisseph"), "swe_version": swe.version,
       "planet_flags": drik.PLANET_FLAGS, "ayanamsa_mode": const._DEFAULT_AYANAMSA_MODE,
       "year_days": drik.dhasa_year_duration(), "charts": [], "grid": {}}
G = req["grid"]
pp = [[k, (int(L // 30), L % 30)] for k, L in enumerate(G)]
for d, ms in req["methods"].items():
    for m in ms:
        r = charts.divisional_positions_from_rasi_positions(pp, int(d), chart_method=m)
        res["grid"][f"{d}:{m}"] = [x[1][0] for x in r]
def run(c, part, f):
    try:
        c[part] = f()
    except Exception as e:
        c.setdefault("errors", {})[part] = f"{type(e).__name__}: {e}"
for ch in req["charts"]:
    y, mo, d = map(int, ch["date"].split("-")); h, mi, s = map(int, ch["time"].split(":"))
    place = drik.Place("synthetic", ch["lat"], ch["lon"], ch["tz"])
    jd = utils.julian_day_number(drik.Date(y, mo, d), (h, mi, s))
    c = {"id": ch["id"], "jd_utc": jd - ch["tz"] / 24}
    run(c, "ayanamsa", lambda: swe.get_ayanamsa_ut(jd - ch["tz"] / 24))
    def rasi():
        r = charts.rasi_chart(jd, place)
        c["_rasi"] = r
        return {("Asc" if p == "L" else str(p)): sg * 30 + lo for p, (sg, lo) in r}
    run(c, "lon", rasi)
    run(c, "retro", lambda: list(drik.planets_in_retrograde(jd, place)))
    if "_rasi" in c:
        r = c.pop("_rasi")
        run(c, "vargas", lambda: {str(dv): {("Asc" if p == "L" else str(p)): v[0] for p, v in
            charts.divisional_positions_from_rasi_positions(r, dv, chart_method=req["methods_used"][str(dv)])}
            for dv in req["vargas"]})
    run(c, "vim1", lambda: vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, dhasa_level_index=1)[1])
    run(c, "vim2", lambda: vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, dhasa_level_index=2)[1])
    run(c, "yogini", lambda: yogini.get_dhasa_bhukthi(drik.Date(y, mo, d), (h, mi, s), place, dhasa_level_index=1,
                                                       round_duration=False))
    run(c, "tithi", lambda: drik.tithi(jd, place)[0])
    run(c, "nakshatra", lambda: drik.nakshatra(jd, place)[0])
    run(c, "yoga", lambda: drik.yogam(jd, place)[0])
    run(c, "karana", lambda: drik.karana(jd, place)[0])
    run(c, "vaara", lambda: drik.vaara(jd, place))
    run(c, "sunrise", lambda: drik.sunrise(utils.julian_day_number(drik.Date(y, mo, d), (12, 0, 0)), place)[0])
    res["charts"].append(c)
json.dump(res, open(out, "w"))
'''


def venv_python(venv):
    return os.path.join(venv, "bin", "python")


def setup(venv):
    if os.path.abspath(venv).startswith(ROOT + os.sep):
        sys.exit("refusing to create the PyJHora venv inside the repository")
    if not os.path.exists(venv_python(venv)):
        subprocess.run([sys.executable, "-m", "venv", venv], check=True)
    pip = [venv_python(venv), "-m", "pip", "install", "-q", "--only-binary=:all:"]
    subprocess.run(pip + [PYJHORA] + DEPS, check=True)
    print(f"PyJHora venv ready: {venv}")


def run_pyjhora(venv, charts, ephe):
    grid = [i * 0.05 + 0.0123 for i in range(7200)]          # off exact boundaries, 0.05° steps
    methods = {str(d): sorted({VARGA_METHOD[d], *VARIANTS.get(d, {})}) for d in VARGAS}
    req = {"charts": charts, "grid": grid, "methods": methods, "vargas": VARGAS,
           "methods_used": {str(d): m for d, m in VARGA_METHOD.items()}}
    with tempfile.TemporaryDirectory() as tmp:               # empty cwd: PyJHora puts cwd and ~ on sys.path
        inp, out = os.path.join(tmp, "in.json"), os.path.join(tmp, "out.json")
        json.dump(req, open(inp, "w"))
        p = subprocess.run([venv_python(venv), "-I", "-c", WORKER, inp, out, ephe or "-"], cwd=tmp,
                           capture_output=True, text=True, timeout=3600)
        if p.returncode:
            sys.exit(f"PyJHora worker failed:\n{p.stderr[-3000:]}")
        return json.load(open(out)), grid


# ---------- comparison (project venv) ----------

def _date(t):
    """PyJHora (Y, M, D, fractional hour), local → date; hour 24 rolls over."""
    y, m, d, h = t
    return (dt.datetime(int(y), int(m), int(d)) + dt.timedelta(hours=h)).date()


def _periods(vim1, vim2, ylen):
    from astro.calc.schema import Period
    md_starts = [(BODY[r[0][0]], _date(r[1]), r[2]) for r in vim1]
    ads = {}
    for r in vim2:
        ads.setdefault(BODY[r[0][0]], []).append((BODY[r[0][1]], _date(r[1])))
    out = []
    for i, (lord, start, yrs) in enumerate(md_starts):
        end = md_starts[i + 1][1] if i + 1 < len(md_starts) else start + dt.timedelta(days=yrs * ylen)
        sub = ads.get(lord, [])
        subp = [Period(lord=a, start=s, end=sub[j + 1][1] if j + 1 < len(sub) else end) for j, (a, s) in enumerate(sub)]
        out.append(Period(lord=lord, start=start, end=end, sub=subp))
    return out


def facts_pyjhora(ch, c, ylen, version, ephemeris):
    """Normalised PyJHora output → ChartFacts (adapters' conventions: nothing corrected)."""
    from astro.calc.adapters import _body
    from astro.calc.schema import Birth, ChartFacts, Provenance
    from astro.calc.schema import SIGNS as S
    retro = set(c.get("retro", []))
    bodies = {}
    for k, lon in c["lon"].items():
        name = "Asc" if k == "Asc" else BODY[int(k)]
        vg = {f"D{d}": S[v[k]] for d, v in c.get("vargas", {}).items()}
        bodies[name] = _body(lon, None if name == "Asc" else int(k) in retro, {"D1": S[int(lon // 30)], **vg})
    prov = Provenance(engine="PyJHora", engine_version=version, network="local", ayanamsa="Lahiri",
                      ayanamsa_deg=c.get("ayanamsa"), nodes="mean", dasha_year_days=ylen, ephemeris=ephemeris,
                      settings={"positions": "apparent (FLG_TRUEPOS off)", "varga_methods": json.dumps(VARGA_METHOD)})
    birth = Birth(date=ch["date"], time=ch["time"], utc_offset_hours=ch["tz"], lat=ch["lat"], lon=ch["lon"])
    vim = _periods(c["vim1"], c["vim2"], ylen) if "vim1" in c and "vim2" in c else []
    return ChartFacts(birth=birth, provenance=prov, bodies=bodies, vimshottari=vim)


def _row(kind, key, a, b, verdict, delta=None, note=""):
    from astro.calc.schema import Agreement
    return Agreement(kind=kind, key=key, a=None if a is None else str(a), b=None if b is None else str(b),
                     delta=delta, verdict=verdict, note=note)


def _boundary_ok(rows, A, B):
    """compare() marks a sign/nakshatra/pada split 'unresolved'; when the two longitudes are within the position
    tolerance the split only says the body sits on the boundary (edge-suite charts are 30 s from one)."""
    from astro.calc import compare as C
    from astro.calc import engine as E
    for r in rows:
        if r.kind in ("sign", "nakshatra", "pada") and r.verdict == "unresolved":
            am = C._arcmin(A.bodies[r.key].lon, B.bodies[r.key].lon)
            if am <= (C.ASC_TOL_ARCMIN if r.key == "Asc" else C.POS_TOL_ARCMIN):
                r.verdict, r.note = "within tolerance", f"{am:.2f}′ apart across a {r.kind} boundary"
        if r.kind == "varga" and r.verdict == "unresolved":
            # a boundary effect only if our own rule, applied to PyJHora's longitude, gives PyJHora's sign
            k, d = r.key.split(":")
            am = C._arcmin(A.bodies[k].lon, B.bodies[k].lon)
            if am <= (C.ASC_TOL_ARCMIN if k == "Asc" else C.POS_TOL_ARCMIN) and \
                    E.SIGNS[E.varga(B.bodies[k].lon, int(d[1:]))] == r.b:
                r.verdict, r.note = "within tolerance", f"{am:.2f}′ apart across a {d} boundary"
    return rows


def compare_chart(ch, c, ylen, version, ephemeris):
    from astro.calc import compare as C
    from astro.calc import engine as E
    from astro.calc import panchang as P
    from astro.calc.adapters import from_local
    rows = []
    calc = E.compute(ch["date"], ch["time"], ch["tz"], ch["lat"], ch["lon"], on="2026-01-01", extras=False)
    if "lon" not in c:
        return [_row("chart", "all", "computed", "error", "not comparable",
                     note=f"PyJHora raised {c['errors'].get('lon', '?')}; local engine flags: "
                          f"{'; '.join(calc['meta']['flags']) or 'none'}")]
    A, B = from_local(calc), facts_pyjhora(ch, c, ylen, version, ephemeris)
    rows += _boundary_ok(C.compare(A, B), A, B)
    for part, err in c.get("errors", {}).items():
        rows.append(_row(part, "all", "computed", "error", "not comparable", note=f"PyJHora raised {err}"))
    ut = dt.datetime.fromisoformat(f"{ch['date']}T{ch['time']}") - dt.timedelta(hours=ch["tz"])
    jd = E.jd_of(ut)
    E._sid()
    if "ayanamsa" in c:
        d = E.swe.get_ayanamsa_ut(jd) - c["ayanamsa"]
        rows.append(_row("ayanamsa", "Lahiri", f"{c['ayanamsa'] + d:.6f}", f"{c['ayanamsa']:.6f}",
                         "match" if abs(d) <= TOL["ayanamsa_deg"] else "unresolved", f"{d * 3600:+.3f}″"))
    for k in ("Ma", "Me", "Ju", "Ve", "Sa"):
        ra, rb = A.bodies[k].retro, B.bodies[k].retro
        if ra is not None and rb is not None:
            spd = calc["bodies"][k]["speed"]
            v = "match" if ra == rb else "within tolerance" if abs(spd) < 1 / 3600 else "unresolved"
            rows.append(_row("retro", k, ra, rb, v, f"speed {spd:+.5f}°/d",
                             "" if ra == rb else "station: |speed| < 1″/day, PyJHora counts that as stationary"))
    # Yogini mahadashas
    if "yogini" in c:
        mine = E.yogini(calc["bodies"]["Mo"]["lon"], ut, E.YEAR["sidereal"])[:8]
        lid = {1: "Mo", 0: "Su", 4: "Ju", 2: "Ma", 3: "Me", 6: "Sa", 5: "Ve", 7: "Ra"}
        for a, b in zip(mine, c["yogini"]):
            la, lb = a["lord"], lid[b[0][0]]
            sa, sb = (a["start"] + dt.timedelta(hours=ch["tz"])).date(), _date(b[1])
            days = (sa - sb).days
            v = "unresolved" if la != lb else "match" if days == 0 else "within tolerance" if abs(days) <= C.DASHA_TOL_DAYS else "unresolved"
            rows.append(_row("yogini", f"{a['yogini']} start", f"{la} {sa}", f"{lb} {sb}", v, f"{days:+d} d"))
    # Panchang at the birth moment, vara of the Hindu day, sunrise of the civil date
    el = {"tithi": P._index("tithi", jd) + 1, "nakshatra": E.nak(P._moon(jd))[2] + 1,
          "yoga": P._index("yoga", jd) + 1, "karana": P._index("karana", jd) + 1}
    for k, va in el.items():
        if k in c:
            rows.append(_row("panchang", k, va, c[k], "match" if va == c[k] else "unresolved"))
    if "sunrise" in c or "vaara" in c:
        try:
            day = P.day(dt.date.fromisoformat(ch["date"]), ch["lat"], ch["lon"], ch["tz"])
        except Exception as e:      # noqa: BLE001 — recorded, not hidden
            rows.append(_row("panchang", "sunrise", "error", c.get("sunrise"), "not comparable",
                             note=f"local panchang raised {type(e).__name__}: {e}"))
            day = None
        if day and "sunrise" in c and not day["polar_fallback"]:
            hh, mm = map(int, day["sunrise"][11:].split(":"))
            dmin = hh * 60 + mm - c["sunrise"] * 60
            rows.append(_row("panchang", "sunrise", day["sunrise"][11:], f"{c['sunrise']:.4f} h",
                             "match" if abs(dmin) <= TOL["sunrise_minutes"] else "unresolved", f"{dmin:+.1f} min",
                             "local is rounded to the minute"))
        if day and "vaara" in c:
            before = ut < _sunrise_ut(day, ch["tz"])
            vara = P.day(dt.date.fromisoformat(ch["date"]) - dt.timedelta(days=1), ch["lat"], ch["lon"],
                         ch["tz"])["vara"] if before else day["vara"]
            vb = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][c["vaara"]]
            rows.append(_row("panchang", "vara", vara, vb, "match" if vara == vb else "unresolved",
                             note="Hindu day from sunrise" if before else ""))
    return rows


def _sunrise_ut(day, tz):
    return dt.datetime.fromisoformat(day["sunrise"]) - dt.timedelta(hours=tz)


def varga_rule_rows(grid, res):
    from astro.calc import engine as E
    rows = []
    for d in VARGAS:
        n = sum(E.varga(L, d) != s for L, s in zip(grid, res["grid"][f"{d}:{VARGA_METHOD[d]}"]))
        rows.append(_row("varga rule", f"D{d} method {VARGA_METHOD[d]}", "engine.varga", "PyJHora",
                         "match" if n == 0 else "unresolved", f"{n}/{len(grid)} grid points"))
        for m, label in VARIANTS.get(d, {}).items():
            n = sum(E.varga(L, d) != s for L, s in zip(grid, res["grid"][f"{d}:{m}"]))
            rows.append(_row("varga rule", f"D{d} method {m}", "engine.varga", "PyJHora", "methodology",
                             f"{n}/{len(grid)} grid points",
                             f"PyJHora variant '{label}'; local follows {E.VARGA_METHODS[f'D{d}']}"))
    return rows


AGREE, EXPLAINED = ("match", "within tolerance"), ("methodology", "configuration", "implementation", "not comparable")
LID = {0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 4: "Ju", 5: "Ve", 6: "Sa", 7: "Ra"}   # PyJHora yogini lords
# Largest boundary shift the shipped engine may show: Moon rounding (±0.00005° of a 13°20' nakshatra, times the
# longest opening period, 20 years) plus the year-length difference (1e-6 day a year over 150 years).
SHIPPED_BOUND_S = (0.00005 / (40 / 3) * 20 * 365.256364 + 150e-6) * 86400


def timing(ch, c, ylen):
    """Exact-second dasha boundaries (UT) against PyJHora's, the engine fed (a) the same unrounded Moon and the tool's
    year: tests the algorithm; (b) its reported Moon (rounded to 0.0001°, QA-F3) and its own year: the shipped output."""
    from astro.calc import engine as E
    ut = dt.datetime.fromisoformat(f"{ch['date']}T{ch['time']}") - dt.timedelta(hours=ch["tz"])
    raw = E.positions(E.jd_of(ut), "mean")["Mo"]["lon"]
    u = lambda t: dt.datetime(int(t[0]), int(t[1]), int(t[2])) + dt.timedelta(hours=t[3] - ch["tz"])  # noqa: E731
    tool = {"vimshottari MD": [(BODY[r[0][0]], u(r[1])) for r in c["vim1"]],
            "vimshottari AD": [(BODY[r[0][0]] + "-" + BODY[r[0][1]], u(r[1])) for r in c["vim2"]],
            "yogini MD": [(LID[r[0][0]], u(r[1])) for r in c["yogini"]]}
    rows, gaps = [], {}
    for mode, moon, year in (("matched", raw, ylen), ("as shipped", round(raw, 4) % 360, E.YEAR["sidereal"])):
        v = E.vimshottari(moon, ut, year, levels=2)
        mine = {"vimshottari MD": [(m["lord"], m["start"]) for m in v],
                "vimshottari AD": [(m["lord"] + "-" + a["lord"], a["start"]) for m in v for a in m["sub"]],
                "yogini MD": [(r["lord"], r["start"]) for r in E.yogini(moon, ut, year, span_years=150)]}
        for kind, tl in tool.items():
            ml = mine[kind]
            k = next((i for i, x in enumerate(ml) if x[0] == tl[0][0] and abs((x[1] - tl[0][1]).days) < 5), None)
            pairs = list(zip(ml[k:], tl)) if k is not None else []
            if not pairs or any(a[0] != b[0] for a, b in pairs):
                rows.append(_row("timing", f"{mode} {kind}", "lords", "lords", "unresolved", note="lord sequence differs"))
                continue
            gap = max(abs((a[1] - b[1]).total_seconds()) for a, b in pairs)
            gaps[f"{mode} {kind}"] = round(gap, 3)
            if mode == "matched":
                v_ = "match" if gap <= 1 else "unresolved"
                note = "" if gap <= 1 else "algorithm differs: same Moon and year length, gap over 1 s"
            else:
                v_ = "match" if gap <= 1 else "configuration" if gap <= SHIPPED_BOUND_S else "unresolved"
                note = "" if gap <= 1 else (f"engine rounds the Moon to 0.0001° before the balance (QA-F3) and uses "
                                            f"a 365.256363-day year; bound {SHIPPED_BOUND_S:.0f} s; dates are shown "
                                            "as local days")
            rows.append(_row("timing", f"{mode} {kind}", f"{len(pairs)} boundaries", "PyJHora", v_, f"max {gap:.3f} s", note))
    bounds = {"moon_unrounded": raw, "year_days": ylen, "ut": ut.isoformat(),
              **{kind: [[lord, t.isoformat(timespec="milliseconds")] for lord, t in tl] for kind, tl in tool.items()}}
    return rows, gaps, bounds


def run(venv, out):
    from astro.calc import engine as E
    edge = json.load(open(EDGE))["charts"]
    charts = [{k: c[k] for k in ("id", "date", "time", "tz", "lat", "lon")} | {"source": "edge_suite"} for c in edge]
    charts += [dict(c, source="oracle extra") for c in EXTRA]
    res, grid = run_pyjhora(venv, [{k: c[k] for k in ("id", "date", "time", "tz", "lat", "lon")} for c in charts],
                            E.EPHE_DIR)
    local_eph = E.ephemeris_info()["ephemeris"]
    tool_eph = local_eph if E.EPHE_DIR else "Moshier (no .se1 files)"
    ylen = res["year_days"]
    per_chart, all_rows, boundaries = [], [], {}
    for ch, c in zip(charts, res["charts"]):
        rows = compare_chart(ch, c, ylen, res["version"], tool_eph)
        gaps = {}
        if "vim1" in c and "vim2" in c and "yogini" in c:
            trows, gaps, boundaries[ch["id"]] = timing(ch, c, ylen)
            rows += trows
        all_rows += rows
        counts = {}
        for r in rows:
            counts.setdefault(r.kind, {}).setdefault(r.verdict, 0)
            counts[r.kind][r.verdict] += 1
        per_chart.append({"id": ch["id"], "source": ch["source"], "counts": counts, "timing_max_s": gaps,
                          "differences": [r.model_dump(exclude_none=True) for r in rows if r.verdict not in AGREE]})
    rule_rows = varga_rule_rows(grid, res)
    summary = {}
    for r in all_rows + rule_rows:
        summary.setdefault(r.kind, {}).setdefault(r.verdict, 0)
        summary[r.kind][r.verdict] += 1
    unresolved = sum(1 for r in all_rows + rule_rows if r.verdict == "unresolved")
    today = dt.date.today().isoformat()
    doc = {
        "provenance": {
            "run_id": f"pyjhora-{res['version']}-{today}", "tool": "PyJHora", "tool_version": res["version"],
            "tool_license": "AGPL-3.0 (dev oracle only; never a golden, never imported)",
            "tool_runtime": {"pyswisseph": res["pyswisseph"], "swisseph": res["swe_version"],
                             "python": "venv outside the repository", "deviations": "timezonefinder 6.6.3 for 6.5.2 "
                             "(no cp313 wheel; place lookup only, unused)"},
            "local_engine": f"astro {E.ENGINE_VERSION}", "date": today, "harness": "tools/oracle_pyjhora.py",
            "ephemeris": {"local": local_eph, "tool": tool_eph},
            "settings": {"ayanamsa": f"LAHIRI (PyJHora default TRUE_PUSHYA); mode read back: {res['ayanamsa_mode']}",
                         "dasha_year": f"MEAN_SIDEREAL_YEAR = {ylen} d (local {E.YEAR['sidereal']} d; PyJHora "
                                       "default TRUE_SIDEREAL_YEAR)",
                         "positions": f"apparent, FLG_TRUEPOS off (PyJHora default on); flags {res['planet_flags']}",
                         "nodes": "mean (PyJHora default true)", "sunrise": "disc centre with refraction "
                         "(PyJHora default without)", "vargas": {f"D{d}": m for d, m in VARGA_METHOD.items()},
                         "vimshottari_antardasha": "antardhasa_option 1 (from the MD lord, forward)",
                         "panchang": "elements at the birth moment; vara of the Hindu day (sunrise to sunrise)"},
            "charts": [c["id"] for c in charts], "chart_sources": {"edge_suite": "tests/reference_charts/edge_suite.json",
                                                                   "oracle extra": "EXTRA in tools/oracle_pyjhora.py"},
            "verdicts": {"agree": sum(1 for r in all_rows + rule_rows if r.verdict in AGREE),
                         "explained": sum(1 for r in all_rows + rule_rows if r.verdict in EXPLAINED),
                         "unresolved": unresolved},
        },
        "verdict_classes": {"agree": list(AGREE), "explained": list(EXPLAINED), "unresolved": ["unresolved"]},
        "tolerances": TOL, "summary": summary, "varga_rules": [r.model_dump(exclude_none=True) for r in rule_rows],
        "charts": per_chart,
        "boundaries": boundaries,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {out}: {doc['provenance']['verdicts']}")
    return doc


# ---------- yoga shortcuts (P4-1): where PyJHora's yoga functions and the skill's named definitions part ----------
# Synthetic sign charts: sign index of the lagna and [sign, degree] per planet. Each isolates one rule difference.
YOGA_OUT = os.path.join(ROOT, "tests", "fixtures", "oracle", "pyjhora-yoga.json")
YOGA_CHARTS = {
    "gk_self_conjunction": {"asc": 0, "planets": {"Su": [4, 10], "Mo": [0, 10], "Ma": [0, 20], "Me": [4, 20], "Ju": [3, 5],
                                                 "Ve": [2, 10], "Sa": [6, 10], "Ra": [5, 10], "Ke": [11, 10]}},
    "gk_with_venus": {"asc": 0, "planets": {"Su": [4, 10], "Mo": [0, 10], "Ma": [0, 20], "Me": [4, 20], "Ju": [3, 5],
                                           "Ve": [3, 20], "Sa": [6, 10], "Ra": [5, 10], "Ke": [11, 10]}},
    "kem_rahu_only": {"asc": 0, "planets": {"Su": [1, 10], "Me": [1, 20], "Ke": [1, 15], "Ve": [2, 10], "Ma": [4, 10],
                                           "Mo": [6, 10], "Ra": [7, 15], "Ju": [8, 10], "Sa": [10, 10]}},
    "kem_no_node": {"asc": 0, "planets": {"Su": [1, 10], "Me": [1, 20], "Ke": [2, 15], "Ve": [2, 10], "Ma": [4, 10],
                                         "Mo": [6, 10], "Ra": [8, 15], "Ju": [8, 10], "Sa": [10, 10]}},
}
YOGA_WORKER = r'''
import json, sys, importlib.metadata as md
from jhora.horoscope.chart import yoga
C = json.load(open(sys.argv[1])); ID = {"Su": 0, "Mo": 1, "Ma": 2, "Me": 3, "Ju": 4, "Ve": 5, "Sa": 6, "Ra": 7, "Ke": 8}
out = {"version": md.version("PyJHora"), "charts": {}}
for k, c in C.items():
    h = [[] for _ in range(12)]; h[c["asc"]].append("L")
    for p, (s, d) in c["planets"].items():
        h[s].append(str(ID[p]))
    ch = ["/".join(x) for x in h]
    out["charts"][k] = {"chart_1d": ch, "gaja_kesari": yoga.gaja_kesari_yoga(ch), "kemadruma": yoga.kemadruma_yoga(ch)}
json.dump(out, open(sys.argv[2], "w"))
'''
# PyJHora function -> the skill definitions it is compared with, and the documented cause when they part
YOGA_PAIRS = {"gaja_kesari": (("GK-BPHS36",), "PyJHora's benefic list includes Jupiter itself, so 'a benefic joins "
                              "Jupiter' always holds (VED-F4); GK-BPHS36 needs another benefic"),
              "kemadruma": (("KEM-BARE", "KEM-BPHS"), "PyJHora counts the nodes in the 2nd/12th from the Moon (KEM-BARE "
                            "does not) and allows the Moon in a kendra from the lagna (KEM-BPHS counts it, LOL p322)")}


def skill_yogas(c):
    sys.path.insert(0, os.path.join(ROOT, "skill", "astrology-consultation", "scripts"))
    import chart_facts as cf
    ch = {"asc": {"sign": cf.SIGNS[c["asc"]], "deg": 5},
          "planets": {p: {"sign": cf.SIGNS[s], "deg": d} for p, (s, d) in c["planets"].items()}}
    return {row[0]: row[2] for row in cf.candidates(cf.derive(ch))}


def yoga_run(venv, out=YOGA_OUT):
    with tempfile.TemporaryDirectory() as tmp:
        inp, res_path = os.path.join(tmp, "in.json"), os.path.join(tmp, "out.json")
        json.dump(YOGA_CHARTS, open(inp, "w"))
        p = subprocess.run([venv_python(venv), "-I", "-c", YOGA_WORKER, inp, res_path], cwd=tmp, capture_output=True,
                           text=True, timeout=600)
        if p.returncode:
            sys.exit(f"PyJHora worker failed:\n{p.stderr[-3000:]}")
        res = json.load(open(res_path))
    rows = []
    for cid, c in YOGA_CHARTS.items():
        mine = skill_yogas(c)
        for fn, (ids, cause) in YOGA_PAIRS.items():
            for i in ids:
                a, b = mine[i], res["charts"][cid][fn]
                rows.append({"chart": cid, "kind": "yoga", "key": f"{i} vs PyJHora {fn}", "a": a, "b": b,
                             "verdict": "match" if a == b else "methodology", "note": "" if a == b else cause})
    today = dt.date.today().isoformat()
    doc = {"provenance": {"run_id": f"pyjhora-yoga-{res['version']}-{today}", "tool": "PyJHora",
                          "tool_version": res["version"], "local_engine": "skill chart_facts.candidates", "date": today,
                          "harness": "tools/oracle_pyjhora.py yoga", "ephemeris": {"local": "none (sign charts)",
                                                                                   "tool": "none (sign charts)"},
                          "settings": {"input": "chart_1d sign charts; PyJHora yoga.gaja_kesari_yoga, kemadruma_yoga"},
                          "charts": list(YOGA_CHARTS),
                          "verdicts": {"agree": sum(r["verdict"] == "match" for r in rows),
                                       "explained": sum(r["verdict"] == "methodology" for r in rows), "unresolved": 0}},
           "charts": YOGA_CHARTS, "tool_output": res["charts"], "rows": rows}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {out}: {doc['provenance']['verdicts']}")
    return doc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["setup", "run", "yoga"])
    ap.add_argument("--venv", default=DEFAULT_VENV)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    if a.cmd == "yoga":
        yoga_run(a.venv)
    else:
        setup(a.venv) if a.cmd == "setup" else run(a.venv, a.out)
