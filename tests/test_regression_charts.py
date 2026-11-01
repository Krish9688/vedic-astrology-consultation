"""Regression: the engine (via astro.service, defaults = Lahiri, mean nodes, 365.256363-day dasha year) against stored
REFERENCE values for the synthetic edge charts C1..C9 (tests/reference_charts/crosscheck_2026_11.json).

The golden values come from two engines that share no code with astro/: an independent pyswisseph reference and PyJHora
4.8.7 (AGPL, run out-of-process by tools/crosscheck, never imported here). Regenerate with
`tools/crosscheck/run.sh --golden tests/reference_charts/crosscheck_2026_11.json`. No PyJHora or Skyfield is needed to
run these tests. Tolerances: longitudes 1', Asc 3', dasha starts 3 days, ayanamsa 1e-5 deg; sign, nakshatra, pada,
16 vargas, dasha lords and panchang exact. Without the Swiss Ephemeris files the engine falls back to Moshier (<= 3"
difference), still inside these tolerances.

Coverage of C1..C9: J2000 Greenwich, pre-midnight and exact midnight (+05:30), US DST day (-04:00), +05:45, +09:30
southern hemisphere, +12:00 year rollover, -03:00 southern hemisphere, wartime India 1942 (+06:30).
The same checks run on local-only charts in tests/test_private_regression.py.
"""
from __future__ import annotations

import datetime as dt
import functools
import json
import os

import pytest

from astro import service as S
from astro.calc import engine as E
from astro.calc import panchang as P

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "reference_charts", "crosscheck_2026_11.json")
COLUMNS = ("independent", "pyjhora")
BODIES = ["Asc", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
AREAS = ("ayanamsa", "positions", "categorical", "dasha", "panchang")
ON = dt.date(2026, 1, 1)   # transit reference date: irrelevant to natal values, fixed for reproducibility


def load_golden(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def am(a, b):
    """signed arc-minute difference a-b on the circle"""
    return ((a - b + 180) % 360 - 180) * 60


def birth_input(inp):
    return S.BirthInput(date=inp["date"], time=inp["time"], tz=inp["utc_offset"], lat=inp["lat"], lon=inp["lon"])


@functools.lru_cache(maxsize=None)
def _engine(key):
    inp = json.loads(key)
    b = birth_input(inp)
    c = S.calculate_chart(b, S.Options(on=ON), full=False)
    # panchang of the Hindu day of birth: the civil date's, or the previous day's when born before sunrise
    local = dt.datetime.fromisoformat(f"{b.date.isoformat()}T{b.time}")
    day = S.panchang(b.date.isoformat(), b.lat, b.lon, tz=inp["utc_offset"])
    if local < dt.datetime.fromisoformat(day["sunrise"]):
        day = S.panchang((b.date - dt.timedelta(days=1)).isoformat(), b.lat, b.lon, tz=inp["utc_offset"])
    with E.using("lahiri"):
        at_birth = P.elements(E.jd_of(local - dt.timedelta(hours=b.tz)))
    return {"chart": c, "day": day, "at_birth": at_birth}


def engine(inp):
    return _engine(json.dumps(inp, sort_keys=True))


def panchang_numbers(el, vara):
    return {"tithi": el["tithi"]["number"], "nakshatra": E.NAKS.index(el["nakshatra"]) + 1,
            "yoga": P.YOGA.index(el["yoga"]) + 1, "karana_name": el["karana"], "vara": vara}


def check(ch, area, tol):
    """Mismatches of one area of one chart, against BOTH reference columns. Messages carry quantities and deltas only
    (never the chart input), so the same function serves the local-only charts."""
    g = engine(ch["input"])
    c = g["chart"]
    bad = []
    for col in COLUMNS:
        R = ch["reference"][col]
        if area == "ayanamsa":
            d = c["meta"]["ayanamsa_deg_mean"] - R["ayanamsa_deg_mean"]
            if abs(d) > tol["ayanamsa_deg"]:
                bad.append(f"{col}: ayanamsa mean off by {d * 3600:+.3f}\"")
            if "ayanamsa_deg_true" in R and abs(c["meta"]["ayanamsa_deg_true"] - R["ayanamsa_deg_true"]) > tol["ayanamsa_deg"]:
                bad.append(f"{col}: ayanamsa true off by {(c['meta']['ayanamsa_deg_true'] - R['ayanamsa_deg_true']) * 3600:+.3f}\"")
        elif area == "positions":
            for b in BODIES:
                lim = tol["asc_arcmin"] if b == "Asc" else tol["moon_arcmin"] if b == "Mo" else tol["longitude_arcmin"]
                d = am(c["bodies"][b]["lon"], R["bodies"][b]["lon"])
                if abs(d) > lim:
                    bad.append(f"{col}: {b} longitude off by {d:+.3f}' (tolerance {lim}')")
        elif area == "categorical":
            for b in BODIES:
                eb, rb = c["bodies"][b], R["bodies"][b]
                for k in ("sign", "nakshatra", "pada"):
                    if eb[k] != rb[k]:
                        bad.append(f"{col}: {b} {k} engine {eb[k]} != reference {rb[k]}")
                for D, v in rb["vargas"].items():
                    if eb["vargas"][D] != v:
                        bad.append(f"{col}: {b} {D} engine {eb['vargas'][D]} != reference {v}")
        elif area == "dasha":
            V, mds = R["vimshottari"], c["vimshottari"]
            if mds[0]["lord"] != V["first_lord"]:
                bad.append(f"{col}: first MD lord engine {mds[0]['lord']} != reference {V['first_lord']}")
            if [m["lord"] for m in mds[:9]] != [m["lord"] for m in V["md_starts"]]:
                bad.append(f"{col}: MD sequence differs")
            for em, rm in zip(mds, V["md_starts"]):
                dd = (dt.date.fromisoformat(em["start"]) - dt.date.fromisoformat(rm["start"][:10])).days
                if abs(dd) > tol["dasha_days"]:
                    bad.append(f"{col}: MD {rm['lord']} start off by {dd:+d} days")
            run = [m for m in mds if m["lord"] == V["running_md"]]
            if not run:
                bad.append(f"{col}: running MD {V['running_md']} missing")
                continue
            subs = run[0]["sub"]
            if [a["lord"] for a in subs] != [a["lord"] for a in V["ad_starts"]]:
                bad.append(f"{col}: AD sequence of the running MD differs")
            for ea, ra in zip(subs, V["ad_starts"]):
                dd = (dt.date.fromisoformat(ea["start"]) - dt.date.fromisoformat(ra["start"][:10])).days
                if abs(dd) > tol["dasha_days"]:
                    bad.append(f"{col}: AD {V['running_md']}/{ra['lord']} start off by {dd:+d} days")
        elif area == "panchang":
            for which, el in (("panchang_birth", g["at_birth"]), ("panchang_sunrise", g["day"]["at_sunrise"])):
                got, ref = panchang_numbers(el, g["day"]["vara"]), R[which]
                for k, v in got.items():
                    if v != ref[k]:
                        bad.append(f"{col}: {which} {k} engine {v} != reference {ref[k]}")
    return bad


def cases(golden):
    return [pytest.param(ch, area, id=f"{ch['id']}-{area}") for ch in golden["charts"] for area in AREAS]


GOLD = load_golden(GOLDEN)


@pytest.mark.parametrize("ch,area", cases(GOLD))
def test_engine_matches_reference(ch, area):
    bad = check(ch, area, GOLD["tolerances"])
    assert not bad, f"{ch['id']} {area}: {len(bad)} mismatch(es):\n" + "\n".join(bad)


def test_golden_covers_the_edge_cases():
    ids = [c["id"] for c in GOLD["charts"]]
    assert ids == [f"C{i}" for i in range(1, 10)]
    offsets = {c["input"]["utc_offset"] for c in GOLD["charts"]}
    assert {"+05:30", "-04:00", "+05:45", "+09:30", "+12:00", "-03:00", "+06:30", "+00:00"} <= offsets
    assert any(c["input"]["lat"] < 0 for c in GOLD["charts"])                       # southern hemisphere
    assert any(c["input"]["time"] == "00:00:00" for c in GOLD["charts"])            # exact midnight
    assert GOLD["provenance"]["pyjhora"]["version"] == "4.8.7"
    assert GOLD["conventions"]["ayanamsa"] == "Lahiri" and GOLD["conventions"]["nodes"] == "mean"


def test_reference_columns_agree_with_each_other():
    """The two reference engines must agree among themselves; otherwise the golden file is not a reference."""
    tol = GOLD["tolerances"]
    for ch in GOLD["charts"]:
        a, b = ch["reference"]["independent"], ch["reference"]["pyjhora"]
        for body in BODIES:
            lim = tol["asc_arcmin"] if body == "Asc" else tol["longitude_arcmin"]
            assert abs(am(a["bodies"][body]["lon"], b["bodies"][body]["lon"])) <= lim, (ch["id"], body)
            assert a["bodies"][body]["vargas"] == b["bodies"][body]["vargas"], (ch["id"], body)
        for which in ("panchang_birth", "panchang_sunrise"):
            for k in ("tithi", "nakshatra", "yoga", "karana", "vara"):
                assert a[which][k] == b[which][k], (ch["id"], which, k)


def test_a_perturbed_golden_value_is_caught():
    """The checks are live: a reference shifted past tolerance, or a changed sign, must be reported."""
    ch = json.loads(json.dumps(GOLD["charts"][0]))
    ch["reference"]["independent"]["bodies"]["Mo"]["lon"] += 2 / 60
    ch["reference"]["pyjhora"]["bodies"]["Su"]["vargas"]["D9"] = "Aries" if \
        ch["reference"]["pyjhora"]["bodies"]["Su"]["vargas"]["D9"] != "Aries" else "Taurus"
    assert any("Mo longitude" in m for m in check(ch, "positions", GOLD["tolerances"]))
    assert any("Su D9" in m for m in check(ch, "categorical", GOLD["tolerances"]))
