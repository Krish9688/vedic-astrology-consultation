# Property-based tests (Hypothesis) for the local calculation engine and the normalized schema.
# They complement, not replace, the fixed reference values in test_reference.py.
import datetime as dt

import pytest
import swisseph as swe
from hypothesis import given, settings
from hypothesis import strategies as st

from astro.calc import engine as lc
from astro.calc.schema import NAKS, SIGNS, Body, nak_of, sign_of

lon = st.floats(min_value=0, max_value=360, exclude_max=True, allow_nan=False)
moment = st.datetimes(min_value=dt.datetime(1900, 1, 1), max_value=dt.datetime(2099, 12, 31))
lat = st.floats(min_value=-60, max_value=60)          # beyond ±66° whole-sign ascendants become unstable
geo_lon = st.floats(min_value=-180, max_value=180)
PLANETS = [n for n, _ in lc.DASA]


@given(lon)
def test_sign_nakshatra_pada_follow_from_longitude(L):
    s, (n, p) = sign_of(L), nak_of(L)
    assert SIGNS.index(s) == int(L / 30 + 1e-9) % 12
    i = NAKS.index(n)
    off = (L - i * 40 / 3) % 360
    assert off < 40 / 3 + 1e-6 or off > 360 - 1e-6              # L lies in nakshatra i (circularly)
    assert 1 <= p <= 4
    Body(lon=L, sign=s, deg=L % 30, nakshatra=n, pada=p)       # the schema accepts every consistent body


@given(st.integers(0, 11), st.floats(1e-7, 1e-3))
def test_sign_boundaries_flip_exactly(k, eps):
    edge = k * 30
    assert sign_of(edge + eps) == SIGNS[k]
    assert sign_of(edge - eps) == SIGNS[(k - 1) % 12]


@given(st.integers(0, 107), st.floats(1e-7, 1e-3))
def test_pada_boundaries_flip_exactly(k, eps):
    edge = k * 10 / 3
    n1, p1 = nak_of(edge + eps)
    n0, p0 = nak_of(edge - eps)
    assert (NAKS.index(n1) * 4 + p1 - 1) == k
    assert (NAKS.index(n0) * 4 + p0 - 1) == (k - 1) % 108


@given(st.one_of(lon, st.integers(0, 1079).map(lambda k: k / 3)))   # include exact boundaries
def test_varga_ranges_and_identities(L):
    for n in lc.VARGAS:
        assert 0 <= lc.varga(L, n) <= 11
    assert lc.varga(L, 1) == int(L // 30)
    assert lc.nak(L)[0] == nak_of(L)[0] and lc.nak(L)[1] == nak_of(L)[1]   # engine and schema agree
    # Parashari navamsa and bhamsha run continuously from Aries around the zodiac
    assert lc.varga(L, 9) == int(L / (10 / 3) + 1e-9) % 12
    assert lc.varga(L, 27) == int(L / (30 / 27) + 1e-9) % 12
    assert lc.varga(L, 2) in (3, 4)                            # hora: only Cancer or Leo
    assert (lc.varga(L, 3) - int(L // 30)) % 4 == 0            # drekkana: 1st, 5th or 9th from the sign


@given(lon, st.sampled_from([365.256363, 365.25, 360.0]))
@settings(max_examples=60)
def test_vimshottari_structure(moon, ylen):
    birth = dt.datetime(2000, 1, 1)
    mds = lc.vimshottari(moon, birth, ylen, levels=3)
    lords = [m["lord"] for m in mds]
    start = PLANETS.index(lords[0])
    assert lords == [PLANETS[(start + j) % 9] for j in range(9)]
    assert lords[0] == PLANETS[lc.nak(moon)[2] % 9]           # first lord = the Moon's nakshatra lord
    assert mds[0]["start"] <= birth < mds[0]["end"]
    total = (mds[-1]["end"] - mds[0]["start"]).total_seconds() / 86400
    assert abs(total - 120 * ylen) < 1e-3
    for md in mds:
        subs = md["sub"]
        assert subs[0]["lord"] == md["lord"] and subs[0]["start"] == md["start"]
        assert abs((subs[-1]["end"] - md["end"]).total_seconds()) < 1
        for a, b in zip(subs, subs[1:]):
            assert a["end"] == b["start"]
        for ad in subs:
            assert ad["sub"][0]["start"] == ad["start"] and abs((ad["sub"][-1]["end"] - ad["end"]).total_seconds()) < 1


@given(moment, st.floats(-12, 14))
@settings(max_examples=40, deadline=None)
def test_timezone_conversion_is_only_a_shift(t, tz):
    # a chart given as local time + offset must equal the chart computed directly at the matching UT
    local = t
    ut = local - dt.timedelta(hours=tz)
    p1 = lc.positions(lc.jd_of(ut))
    p2 = lc.positions(swe.julday(ut.year, ut.month, ut.day, ut.hour + ut.minute / 60 + ut.second / 3600 + ut.microsecond / 3.6e9))
    for k in p1:
        assert abs(p1[k]["lon"] - p2[k]["lon"]) < 1e-9


@given(moment, lat, geo_lon)
@settings(max_examples=40, deadline=None)
def test_ascendant_moves_forward_with_birth_time(t, la, lo):
    # four minutes later the ascendant has moved forward by a small positive arc (never backwards, never > 10°)
    a1 = lc.asc(lc.jd_of(t), la, lo)
    a2 = lc.asc(lc.jd_of(t + dt.timedelta(minutes=4)), la, lo)
    step = (a2 - a1) % 360
    assert 0 < step < 10


@pytest.mark.parametrize("day", ["2000-02-29", "2004-02-29", "2024-02-29"])
def test_leap_days_and_midnight(day):
    # 00:30 local at UTC+5:30 is 19:00 UT on the previous calendar day
    local = dt.datetime.fromisoformat(day + "T00:30")
    ut = local - dt.timedelta(hours=5.5)
    assert ut.date() == (local - dt.timedelta(days=1)).date() and ut.hour == 19
    mds = lc.vimshottari(lc.positions(lc.jd_of(ut))["Mo"]["lon"], ut, 365.256363)
    for a, b in zip(mds, mds[1:]):
        assert a["end"] == b["start"]


@given(moment)
@settings(max_examples=30, deadline=None)
def test_nodes_opposite_and_retrograde_flags(t):
    p = lc.positions(lc.jd_of(t))
    assert abs(((p["Ra"]["lon"] - p["Ke"]["lon"]) % 360) - 180) < 1e-9
    assert not p["Su"]["retro"] and not p["Mo"]["retro"]       # the luminaries never retrograde
