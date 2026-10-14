# Known reference values and local-engine exactness checks on the synthetic chart S1
# (14 Mar 1992, 09:40 UT, 51.5N 0.12W — not a real person). No personal birth data is used anywhere in this suite.
import json
import os

import pytest
import swisseph as swe
from pydantic import ValidationError

from astro.calc import engine as lc
from astro.calc.adapters import from_local
from astro.calc.compare import compare, validate
from astro.calc.schema import ChartFacts, ValidatedChartFacts

FX = os.path.join(os.path.dirname(__file__), "fixtures")


def load(*p):
    with open(os.path.join(FX, *p)) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def s1():
    return from_local(load("local", "S1", "calc.json"))


def test_lahiri_ayanamsa_j2000():
    # Lahiri (Chitrapaksha) ayanamsa on 2000-01-01 12:00 UT is 23°51′ (Indian Astronomical Ephemeris)
    ay = swe.get_ayanamsa_ut(swe.julday(2000, 1, 1, 12))
    assert abs(ay - (23 + 51 / 60)) < 1 / 60


def test_tropical_sun_j2000():
    # apparent tropical Sun at J2000.0 ≈ 280.37°
    x, _ = swe.calc_ut(swe.julday(2000, 1, 1, 12), swe.SUN)
    assert abs(x[0] - 280.37) < 0.02


def test_comparator_on_identical_charts(s1):
    """The comparator itself: a chart compared with itself has no difference, and validated facts round-trip."""
    ag = compare(s1, s1)
    assert ag and all(x.verdict in ("match", "within tolerance", "not comparable") for x in ag), \
        [x for x in ag if x.verdict not in ("match", "within tolerance", "not comparable")]
    v = validate(s1, s1)
    again = ValidatedChartFacts.model_validate_json(v.model_dump_json())
    assert again.provenance.network == "local" and again.disagreements() == []


def test_schema_rejects_inconsistent_facts(s1):
    d = json.loads(s1.model_dump_json())
    d["bodies"]["Mo"]["sign"] = "Leo"                     # Moon is in Cancer
    with pytest.raises(ValidationError):
        ChartFacts(**d)
    d = json.loads(s1.model_dump_json())
    d["bodies"]["Ke"]["lon"] = (d["bodies"]["Ra"]["lon"] + 170) % 360
    with pytest.raises(ValidationError):
        ChartFacts(**d)


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


def test_published_json_schema_is_current():
    # AUD-10: schemas/chart_facts.schema.json had drifted from the Pydantic model (diff classes, provenance fields)
    path = os.path.join(os.path.dirname(__file__), "..", "schemas", "chart_facts.schema.json")
    assert json.load(open(path)) == ValidatedChartFacts.model_json_schema()
