"""Regression tests for the 2026-11-01 audit findings (notes/hermes-audit-2026-11-01, Audit-Report F-xx).
Synthetic charts only."""
import re  # noqa: F401
import sys  # noqa: F401
import threading  # noqa: F401

import pytest  # noqa: F401
import swisseph as swe  # noqa: F401

from astro import service as S  # noqa: F401
from astro.calc import adapters  # noqa: F401
from astro.calc import engine as E  # noqa: F401

B = dict(date="2000-01-01", time="12:00", lat=28.6, lon=77.2)

# --- F-03: offset parser -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("given,hours", [("+0530", 5.5), ("-0300", -3.0), ("UTC+0545", 5.75), ("+05:30", 5.5),
                                         ("+14:00", 14.0), ("-12:00", -12.0)])
def test_f03_compact_and_extreme_offsets(given, hours):
    assert S.utc_offset_hours(given) == pytest.approx(hours)


@pytest.mark.parametrize("bad", ["0530", "530", "+20:00", "-15:00", "+14:30", 15, -14.25])
def test_f03_bare_digits_and_out_of_range_refused(bad):
    with pytest.raises(ValueError):
        S.utc_offset_hours(bad)


@pytest.mark.parametrize("bad", ["0530", "+20:00"])
def test_f03_panchang_refuses_bad_offsets(bad):
    with pytest.raises(ValueError):
        S.panchang("2000-01-01", 28.6, 77.2, bad)


def test_f03_panchang_compact_offset_equals_colon_form():
    a, b = S.panchang("2000-01-01", 28.6, 77.2, "+0530"), S.panchang("2000-01-01", 28.6, 77.2, "+05:30")
    a["meta"].pop("computed_at_utc", None), b["meta"].pop("computed_at_utc", None)
    assert a == b and a["sunrise"][11:13] == "07"            # was 03:34 when '+0530' meant 530 h


def test_f03_panchang_over_rest_is_refused():
    from fastapi.testclient import TestClient
    from astro import rest
    r = TestClient(rest.app).get("/api/v1/panchang", params={"date": "2000-01-01", "lat": 28.6, "lon": 77.2, "tz": "0530"})
    assert r.status_code in (400, 422), r.text

# --- F-06: no LMT, mean times refused, stated non-standard offsets flagged ----------------------------------------------
@pytest.mark.parametrize("date", ["1860-01-01", "1900-06-01"])
def test_f06_tzdb_city_mean_times_refused(date):
    with pytest.raises(ValueError, match="before standard time") as e:
        S.BirthInput(date=date, time="12:00", zone="Asia/Kolkata", lat=19.07, lon=72.88)
    assert "longitude" not in str(e.value) and "local mean time at" not in str(e.value)


def test_f06_stated_nonstandard_offset_used_and_flagged():
    b = S.BirthInput(date="1900-06-01", time="12:00", tz="+04:51", lat=19.07, lon=72.88)
    assert b.tz == pytest.approx(4 + 51 / 60) and b.tz_flags[0].startswith("non-standard offset +04:51")


@pytest.mark.parametrize("tz", ["+05:30", "+05:45", "-10:40", "+12:20", "-03:30"])
def test_f06_standard_offsets_carry_no_flag(tz):
    assert not any(f.startswith("non-standard") for f in S.BirthInput(**B, tz=tz).tz_flags)


def test_f06_no_lmt_offer_in_skill_text():
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in ("plugin/skills/astro-report/SKILL.md", "astrology-prediction/references/inputs.md"):
        p = os.path.join(root, rel)
        if os.path.exists(p):
            t = open(p, encoding="utf-8").read()
            assert "{lmt}" not in t and "it suggests local mean time" not in t and "V-ZONE-LMT" not in t
