"""Regression tests for the 2026-11-01 audit findings (notes/hermes-audit-2026-11-01, Audit-Report F-xx).
Synthetic charts only."""
import re
import sys
import threading

import pytest
import swisseph as swe

from astro import service as S
from astro.calc import adapters
from astro.calc import engine as E

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
                 and n not in {"unknown_time_problems", "time_unknown"}]                      # pure check, computes nothing
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


# --- #47: panchang takes ayanamsa and calendar on every interface ------------------------------------------------------
MUMBAI = dict(lat=19.07, lon=72.88, tz="+05:30")


def _pada(p):
    return [x for x in p["changes"] if x["element"] == "nakshatra"], p["at_sunrise"]


def test_i47_panchang_ayanamsa_service_mcp_rest_cli(capsys):
    from fastapi.testclient import TestClient
    from astro import cli, mcp_server as M, rest
    lah = S.panchang("2026-01-15", **MUMBAI)
    ram = S.panchang("2026-01-15", **MUMBAI, ayanamsa="raman")
    assert re.fullmatch(r"Lahiri 24\.2\d{3}°", lah["meta"]["ayanamsa"]) and re.fullmatch(r"Raman 22\.\d{4}°", ram["meta"]["ayanamsa"])
    assert lah["at_sunrise"] != ram["at_sunrise"]                    # nakshatra pada differs (audit probe C-07)
    assert M.get_panchang("2026-01-15", ayanamsa="raman", **MUMBAI)["meta"]["ayanamsa"].startswith("Raman ")
    r = TestClient(rest.app).get("/api/v1/panchang", params=dict(date="2026-01-15", ayanamsa="raman", **MUMBAI))
    assert r.status_code == 200 and r.json()["meta"]["ayanamsa"].startswith("Raman ")
    cli.main(["panchang", "2026-01-15", "--lat", "19.07", "--lon", "72.88", "--tz", "+05:30", "--ayanamsa", "raman"])
    import json
    assert json.loads(capsys.readouterr().out)["meta"]["ayanamsa"].startswith("Raman ")
    assert E.ayanamsa_name().startswith("Lahiri")                 # nothing leaks after the calls


def test_i47_panchang_julian_calendar_is_converted():
    j = S.panchang("2026-01-02", **MUMBAI, calendar="julian")      # Julian 2 Jan 2026 = Gregorian 15 Jan 2026
    g = S.panchang("2026-01-15", **MUMBAI)
    assert j["date"] == "2026-01-15" and j["at_sunrise"] == g["at_sunrise"] and "Julian" in j["meta"]["date_source"]


def test_i47_unknown_ayanamsa_refused():
    with pytest.raises(ValueError):
        S.panchang("2026-01-15", **MUMBAI, ayanamsa="lahiri_icrc")


# --- #48: unknown birth time → compact only, enforced by the engine; time_source reaches it over MCP ---------------------
def _example():
    import json
    import os
    from astro import config
    return json.load(open(os.path.join(config.load().skill_dir, "assets", "report", "example-synthetic.json"),
                          encoding="utf-8"))


UNKNOWN = S.BirthInput(**B, tz="+05:30", time_source="unknown; 12:00 used as a placeholder")


def test_i48_non_compact_report_refused_for_unknown_time():
    m = _example()
    assert m["report_type"] != "compact"
    errs = S.unknown_time_problems(m, UNKNOWN)
    assert any("only a compact report" in e for e in errs)


def test_i48_compact_report_with_time_bound_claims_refused():
    m = {"report_type": "compact", "sections": [{"id": "s", "title": "t", "units": [
        {"fact_refs": ["F.asc.sign", "F.Mo.sign", "F.H10.lord", "F.Ju.house"]}]}],
         "timeline": [{"start": "2027-01"}]}
    errs = S.unknown_time_problems(m, UNKNOWN)
    assert any("F.asc.sign" in e and "F.H10.lord" in e and "F.Ju.house" in e and "F.Mo.sign" not in e for e in errs)
    assert any("no dated windows" in e for e in errs)


def test_i48_compact_moon_only_report_passes_and_known_time_unaffected():
    ok = {"report_type": "compact", "sections": [{"id": "s", "title": "t", "units": [{"fact_refs": ["F.Mo.sign"]}]}]}
    assert S.unknown_time_problems(ok, UNKNOWN) == []
    assert S.unknown_time_problems(_example(), S.BirthInput(**B, tz="+05:30", time_source="birth certificate")) == []
    assert S.unknown_time_problems({"report_type": "career", "birth": {"time_reliability": "unknown"}})


def test_i48_create_report_refuses_over_mcp_with_time_source(tmp_path, monkeypatch):
    from astro import config, mcp_server as M
    s = config.load()
    s.reports_dir = str(tmp_path / "reports")
    monkeypatch.setattr(config, "load", lambda: s)
    r = M.create_report(_example(), "i48", date="1992-03-14", time="12:00", tz=0, lat=51.5, lon=-0.12,
                        time_source="unknown; 12:00 used as a placeholder")
    assert r["ok"] is False and any("only a compact report" in e for e in r["errors"])
    assert not (tmp_path / "reports").exists() or not any((tmp_path / "reports").iterdir())


def test_i48_time_source_reaches_mcp_chart_tools():
    import inspect
    from astro import mcp_server as M
    tools = [f for n, f in vars(M).items() if n.startswith(("get_", "create_", "prepare_")) and callable(f)
             and "time" in inspect.signature(f).parameters and "date" in inspect.signature(f).parameters]
    assert tools and all("time_source" in inspect.signature(f).parameters for f in tools)


# --- council round 2 (REVIEW-correctness.md RC-01..RC-09) ---------------------------------------------------------------
def test_rc01_time_varying_facts_cover_lagna_yogas_and_lordships():
    v = S.time_varying_facts(S.BirthInput(**B, tz="+05:30"), S.DEFAULTS)
    assert "F.asc.sign" in v and any(k.endswith(".owns") for k in v) and any(k.startswith("F.yoga.") for k in v)
    m = {"report_type": "compact", "sections": [{"id": "s", "title": "t", "units": [{"fact_refs": [sorted(
        k for k in v if k.startswith("F.yoga."))[0]]}]}]}
    assert any("cannot be cited" in e for e in S.unknown_time_problems(m, UNKNOWN, v))


@pytest.mark.parametrize("src,unknown", [("unknown; 12:00 used as a placeholder", True), ("time unknown", True),
                                          ("not known", True), ("noon chart (time unknown)", True), ("N/A", True),
                                          ("no birth time", True), ("birth certificate", False),
                                          ("unknown hospital; time from birth certificate", False)])
def test_rc04_unknown_time_wording(src, unknown):
    assert S.time_unknown({}, S.BirthInput(**B, tz="+05:30", time_source=src)) is unknown


def test_rc04_rc09_event_refs_need_a_window_and_are_refused_with_unknown_time():
    m = {"report_type": "compact", "summary": {"headline": "h", "key_points": [{"text": "t", "confidence": "Low",
                                                                                "event_refs": ["DSH.Sa"]}]}}
    assert any("event_refs" in e for e in S.unknown_time_problems(m, UNKNOWN))


@pytest.mark.parametrize("tz,flagged", [("+05:20", True), ("+04:40", True), ("+07:20", False), ("-10:40", False),
                                        ("+12:20", False), ("+05:30", False)])
def test_rc07_only_historical_20_minute_offsets_are_standard(tz, flagged):
    assert any(f.startswith("non-standard") for f in S.BirthInput(**B, tz=tz).tz_flags) is flagged


def test_rc05_refusal_shows_no_mean_time_number():
    with pytest.raises(ValueError) as e:
        S.BirthInput(date="1860-01-01", time="12:00", zone="Asia/Kolkata", lat=19.07, lon=72.88)
    assert not re.search(r"[+-]\d\d:\d\d", str(e.value).split("(+HH:MM)")[0])


def test_rc08_julian_leap_day_in_panchang():
    p = S.panchang("1700-02-29", 19.07, 72.88, "+05:30", calendar="julian")
    assert p["date"] == "1700-03-11"
