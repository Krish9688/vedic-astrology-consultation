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

# --- Q7 / F-17 / F-19: ayanamsa set, nested requests, mean/true fields -------------------------------------------------
def test_q7_owner_ayanamsa_set():
    assert list(E.AYANAMSAS) == ["lahiri", "true_chitra", "kp", "raman"]
    for gone in ("lahiri_icrc", "lahiri_1940"):
        with pytest.raises(Exception):
            S.Options(ayanamsa=gone)


def test_f17_nested_conflicting_request_raises():
    b = S.BirthInput(**B, tz="+05:30")
    with E.using("raman"):
        with pytest.raises(ValueError, match="one call, one ayanamsa"):
            S.calculate_chart(b, S.Options(ayanamsa="lahiri"), full=False)
        assert S.calculate_chart(b, S.Options(ayanamsa="raman"), full=False)["meta"]["ayanamsa"].startswith("Raman ")


def test_f19_meta_has_mean_and_true_values():
    c = S.calculate_chart(S.BirthInput(date="2000-01-01", time="12:00", tz="+00:00", lat=51.48, lon=0.0), full=False)
    m = c["meta"]
    assert m["ayanamsa"] == "Lahiri 23.8571°"
    assert m["ayanamsa_deg_mean"] == pytest.approx(23.857092, abs=2e-6)
    assert m["ayanamsa_deg_true"] == pytest.approx(23.853222, abs=2e-6)

# --- F-04: create_report under the requested mode; locks ---------------------------------------------------------------
def test_f04_create_report_recompute_uses_requested_ayanamsa(monkeypatch):
    seen = []
    real = S._compute

    def spy(b, o, *a, **k):
        c = real(b, o, *a, **k)
        seen.append((o.ayanamsa, c["meta"]["ayanamsa"]))
        return c
    monkeypatch.setattr(S, "_compute", spy)
    try:
        S.create_report({}, "audit-f04", S.BirthInput(**B, tz="+05:30"), S.Options(ayanamsa="raman"))
    except Exception:
        pass                                                    # the empty model is refused; the recompute is what we test
    assert seen and all(m.startswith("Raman ") for _, m in seen), seen


def test_f04_every_chart_service_function_is_wrapped():
    import inspect
    unwrapped = [n for n, f in vars(S).items() if inspect.isfunction(f) and not n.startswith("_") and f.__module__ == S.__name__
                 and "b" in inspect.signature(f).parameters and not hasattr(f, "__wrapped__")
                 and n not in {"unknown_time_problems"}]                      # pure check, computes nothing
    assert unwrapped == [], unwrapped


def test_f04_threaded_modes_never_mix():
    jd = 2451545.0
    lahiri = E.positions(jd)["Su"]["lon"]
    with E.using("raman"):
        raman = E.positions(jd)["Su"]["lon"]
    bad, stop = [], threading.Event()

    def flip():
        while not stop.is_set():
            with E.using("raman"):
                E.positions(jd)
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    t = threading.Thread(target=flip)
    t.start()
    try:
        for _ in range(1500):
            v = E.positions(jd)["Su"]["lon"]
            if abs(v - lahiri) > 1e-9:
                bad.append(v)
    finally:
        stop.set()
        t.join()
        sys.setswitchinterval(old)
    assert bad == [] and abs(raman - lahiri) > 1

# --- F-07: adapter --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("mode,label", [("lahiri", "Lahiri"), ("raman", "Raman")])
def test_f07_adapter_offset_and_ayanamsa(mode, label):
    with E.using(mode):
        c = E.compute("2000-01-01", "12:00:00", 5.5, 28.6, 77.2, extras=False)
    f = adapters.from_local(c)
    assert f.birth.utc_offset_hours == 5.5 and f.provenance.ayanamsa.startswith(label)
    E._sid()
    assert f.provenance.ayanamsa_deg == pytest.approx(c["meta"]["ayanamsa_deg_mean"])
    assert swe.get_ayanamsa_name(E._MODE.get()).startswith("Lahiri")
