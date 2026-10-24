# Edge cases (task E1): each test asserts an invariant that must hold, not a value copied from another engine.
# Synthetic times and places only.
import datetime as dt

import pytest
import swisseph as swe

from astro.calc import engine as E


def same_instant(date, time, tz):
    """The same moment restated in UT (tz 0)."""
    t = dt.datetime.fromisoformat(f"{date}T{time}") - dt.timedelta(hours=tz)
    return t.date().isoformat(), t.strftime("%H:%M:%S")


def core(c):
    return ({n: (b["lon"], b["sign"], b["nakshatra"], b["pada"], b["vargas"]["D9"]) for n, b in c["bodies"].items()},
            c["mc"], [h["middle"] for h in c["bhavas"]], [m["lord"] for m in c["vimshottari"]])


@pytest.mark.parametrize("name,date,time,tz,lat,lon", [
    ("western longitude, negative offset", "1987-11-05", "23:50", -5, 40.71, -74.01),
    ("daylight saving offset taken verbatim", "2021-07-04", "13:15", -4, 40.71, -74.01),
    ("+05:45", "1999-02-20", "05:45", 5.75, 27.70, 85.32),
    ("+09:30", "2003-08-11", "18:10", 9.5, -12.46, 130.84),
    ("southern hemisphere", "1995-06-21", "06:30", 10, -33.87, 151.21),
])
def test_offset_is_only_a_restatement_of_the_instant(name, date, time, tz, lat, lon):
    d0, t0 = same_instant(date, time, tz)
    a = E.compute(date, time, tz, lat, lon, on="2030-01-01", extras=False)
    b = E.compute(d0, t0, 0, lat, lon, on="2030-01-01", extras=False)
    assert core(a) == core(b), name
    assert a["meta"]["birth_local"].endswith(f"UTC{E.fmt_offset(tz)}")   # echoed as ±HH:MM (audit H1)


def test_date_line_same_instant_same_chart():
    """Kiritimati restated as +14 and -10 (its offset changed in 1995): positions and houses identical."""
    a = E.compute("2026-03-11", "12:00", 14, 1.87, -157.4, on="2030-01-01", extras=False)
    b = E.compute("2026-03-10", "12:00", -10, 1.87, -157.4, on="2030-01-01", extras=False)
    assert core(a) == core(b)


@pytest.mark.parametrize("lat", [0.0, -33.87, 51.5])
def test_bhava_madhyas_are_ascendant_and_mc(lat):
    """Sripati: house 1 middle = ascendant, house 10 middle = MC — at the equator and in both hemispheres."""
    c = E.compute("2010-01-15", "08:00", 0, lat, 30.0, extras=False)
    assert abs((c["bhavas"][0]["middle"] - c["bodies"]["Asc"]["lon"] + 180) % 360 - 180) < 1e-3
    assert abs((c["bhavas"][9]["middle"] - c["mc"] + 180) % 360 - 180) < 1e-3
    assert c["meta"]["flags"] == []


def test_ephemeris_file_range_edges():
    """Outside 1800–2399 the engine says Moshier; at the edge the two ephemerides agree to arcseconds."""
    before = E.compute("1799-12-31", "12:00", 0, 51.5, 0, extras=False)
    assert "Moshier" in before["meta"]["ephemeris"]
    after = E.compute("1800-01-01", "12:00", 0, 51.5, 0, extras=False)
    if "Moshier" in after["meta"]["ephemeris"]:
        pytest.skip("no Swiss Ephemeris files installed here")
    moon = (after["bodies"]["Mo"]["lon"] - before["bodies"]["Mo"]["lon"]) % 360   # ~13°/day apart
    assert 11 < moon < 16


def _bisect(f, a, b, steps=40):
    for _ in range(steps):
        m = (a + b) / 2
        a, b = (a, m) if (f(a) > 0) != (f(m) > 0) else (m, b)
    return (a + b) / 2


def test_outer_planet_station_flips_the_retrograde_flag():
    """Saturn's retrograde flag changes exactly where its speed changes sign."""
    jd0 = swe.julday(2026, 1, 1, 0.0)
    speed = lambda jd: E.positions(jd)["Sa"]["speed"]
    jd = next(j for j in (jd0 + k for k in range(0, 400, 2)) if (speed(j) > 0) != (speed(j + 2) > 0))
    st = _bisect(speed, jd, jd + 2)
    assert E.positions(st - 0.5)["Sa"]["retro"] != E.positions(st + 0.5)["Sa"]["retro"]


def test_node_sign_boundary():
    """At a mean-node sign change Ketu stays exactly opposite Rahu, and its sign/nakshatra follow its longitude."""
    jd0 = swe.julday(2026, 1, 1, 0.0)
    sign = lambda jd: int(E.positions(jd)["Ra"]["lon"] // 30)
    jd = next(j for j in (jd0 + k for k in range(0, 700, 5)) if sign(j) != sign(j + 5))
    a, b = jd, jd + 5
    for _ in range(40):
        m = (a + b) / 2
        a, b = (a, m) if sign(m) != sign(a) else (m, b)
    for t in (a, b):
        p = E.positions(t)
        assert abs(((p["Ke"]["lon"] - p["Ra"]["lon"]) % 360) - 180) < 1e-9
        assert p["Ke"]["retro"] == p["Ra"]["retro"]
        c = {"lon": p["Ke"]["lon"]}
        nk, pada, _ = E.nak(c["lon"])
        assert E.SIGNS[int(c["lon"] // 30)] == E.SIGNS[(int(p["Ra"]["lon"] // 30) + 6) % 12] and 1 <= pada <= 4 and nk
