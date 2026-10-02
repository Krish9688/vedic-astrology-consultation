# Known reference values and the independent-engine cross-check on the synthetic chart S1
# (14 Mar 1992, 09:40 UT, 51.5N 0.12W — not a real person). VedAstro fixtures were fetched once with synthetic
# data only; no personal birth data is used anywhere in this test suite.
import json
import os

import pytest
import swisseph as swe
from pydantic import ValidationError

from astro.calc import engine as lc
from astro.calc.adapters import from_local, from_vedastro
from astro.calc.compare import compare, validate
from astro.calc.schema import ChartFacts, ValidatedChartFacts

FX = os.path.join(os.path.dirname(__file__), "fixtures")


def load(*p):
    with open(os.path.join(FX, *p)) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def s1():
    a = from_local(load("local", "S1", "calc.json"))
    b = from_vedastro(load("vedastro", "S1_planet_data.json"), load("vedastro", "S1_ascendant.json"),
                      load("vedastro", "S1_dasa_range.json"), load("vedastro", "S1_shadbala.json"))
    return a, b


def test_lahiri_ayanamsa_j2000():
    # Lahiri (Chitrapaksha) ayanamsa on 2000-01-01 12:00 UT is 23°51′ (Indian Astronomical Ephemeris)
    ay = swe.get_ayanamsa_ut(swe.julday(2000, 1, 1, 12))
    assert abs(ay - (23 + 51 / 60)) < 1 / 60


def test_tropical_sun_j2000():
    # apparent tropical Sun at J2000.0 ≈ 280.37°
    x, _ = swe.calc_ut(swe.julday(2000, 1, 1, 12), swe.SUN)
    assert abs(x[0] - 280.37) < 0.02


def test_engines_agree_on_positions(s1):
    a, b = s1
    for ag in compare(a, b):
        if ag.kind == "position":
            assert ag.verdict in ("match", "within tolerance"), ag
        assert ag.kind not in ("sign", "nakshatra", "pada"), ag


def test_only_documented_methodology_differences(s1):
    a, b = s1
    bad = [x for x in compare(a, b) if x.verdict == "unresolved"]
    assert bad == [], bad
    vargas = {x.key.split(":")[1] for x in compare(a, b) if x.kind == "varga" and x.verdict != "match"}
    assert vargas <= {"D2", "D7", "D30"}                  # D9, D10, D12, D60 … agree exactly


def test_dasha_lords_agree_and_year_convention_is_flagged(s1):
    a, b = s1
    ag = compare(a, b)
    assert any(x.kind == "configuration" and x.key == "dasha year" for x in ag)
    assert not [x for x in ag if x.key.startswith("sub-period order")]
    assert [p.lord for p in b.vimshottari] == ["Ju", "Sa", "Me", "Ke", "Ve"]
    assert [p.lord for p in a.vimshottari][:5] == ["Ju", "Sa", "Me", "Ke", "Ve"]


def test_validated_facts_roundtrip(s1):
    v = validate(*s1)
    again = ValidatedChartFacts.model_validate_json(v.model_dump_json())
    assert again.cross_check_engine.startswith("vedastro")
    assert again.provenance.network == "local"


def test_schema_rejects_inconsistent_facts(s1):
    a, _ = s1
    d = json.loads(a.model_dump_json())
    d["bodies"]["Mo"]["sign"] = "Leo"                     # Moon is in Cancer
    with pytest.raises(ValidationError):
        ChartFacts(**d)
    d = json.loads(a.model_dump_json())
    d["bodies"]["Ke"]["lon"] = (d["bodies"]["Ra"]["lon"] + 170) % 360
    with pytest.raises(ValidationError):
        ChartFacts(**d)


def test_shadbala_never_compared_as_equal(s1):
    a, b = s1
    a.shadbala_rupas = {"Su": 7.0}
    assert all(x.verdict == "methodology" for x in compare(a, b) if x.kind == "shadbala")
    assert "Ra" not in b.shadbala_rupas                  # VedAstro's node values are copies, dropped


def test_boundary_sensitivity_s1():
    # S1 has the Sun 0°19′ into Pisces and the Moon 0°24′ into Cancer: a few minutes' birth-time error
    # would not move them, but the local engine must report the sign the longitude gives.
    b = load("local", "S1", "calc.json")["bodies"]
    assert b["Su"]["sign"] == "Pisces" and b["Mo"]["sign"] == "Cancer"
    assert lc.varga(b["Mo"]["lon"], 9) == 3               # Moon vargottama (Cancer in D1 and D9)


def test_birth_time_sensitivity_is_exact():
    import datetime as dt
    ut = dt.datetime(1992, 3, 14, 9, 40)
    moon = lc.positions(lc.jd_of(ut))["Mo"]["lon"]
    s = lc.sensitivity(ut, 51.5, -0.12, moon)
    later = s["ascendant sign (D1)"]["later"]
    assert later == 14
    sign = lambda m: int(lc.asc(lc.jd_of(ut + dt.timedelta(minutes=m)), 51.5, -0.12) // 30)
    assert sign(later - 1) == sign(0) != sign(later)


def test_slow_contacts_are_exact():
    import datetime as dt
    natal = {"Me": 347.0746, "Ju": 134.0869}
    found = lc.contacts(dt.datetime(2026, 9, 27, 12), 24, natal)
    assert {(c["transit"], c["natal"]) for c in found} >= {("Sa", "Me"), ("Ju", "Ju")}   # both retro + direct passes
    for c in found:
        t = dt.datetime.fromisoformat(c["date"] + "T12:00")
        target = natal[c["natal"]] + (180 if c["aspect"] == "opposition" else 0)
        d = (lc.positions(lc.jd_of(t))[c["transit"]]["lon"] - target + 180) % 360 - 180
        assert abs(d) < 0.25, c        # within a day's motion of exact
    assert all(c["aspect"] == "conjunction" for c in found if c["transit"] in ("Ra", "Ke"))
