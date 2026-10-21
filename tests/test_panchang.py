# Panchang against independent references: US Naval Observatory 2024 lunar phases and sunrise (public-domain data,
# aa.usno.navy.mil), and the definitions (tithi 12°, karana 6°, yoga (Sun+Moon)/13°20', vara from sunrise).
import datetime as dt

import pytest

from astro import service as S
from astro.calc import engine as E, panchang as P

UT = lambda *a: E.jd_of(dt.datetime(*a))


@pytest.mark.parametrize("kind,when", [("tithi", (2024, 1, 11, 11, 57)),     # USNO new Moon (UT)
                                       ("tithi", (2024, 4, 23, 23, 49)),     # USNO full Moon
                                       ("karana", (2024, 7, 13, 22, 49)),    # USNO first quarter: a karana boundary
                                       ("tithi", (2024, 10, 2, 18, 49))])    # USNO new Moon
def test_lunar_phase_instants_are_element_boundaries(kind, when):
    jd = UT(*when)
    assert abs(P._end(kind, jd - 0.3) - jd) * 1440 < 1.0             # USNO rounds to the minute


def test_tithi_numbers_at_the_phases():
    assert P.elements(UT(2024, 4, 23, 23, 0))["tithi"] == {"number": 15, "name": "Purnima", "paksha": "Shukla"}
    assert P.elements(UT(2024, 1, 11, 11, 0))["tithi"]["name"] == "Amavasya"
    assert P.elements(UT(2024, 1, 11, 13, 0))["tithi"]["name"] == "Shukla Pratipada"


def test_karana_sequence_fixed_and_movable():
    nm = UT(2024, 1, 11, 11, 57)
    assert P._name("karana", P._index("karana", nm + 0.1)) == "Kimstughna"      # first half of Pratipada
    assert P._name("karana", P._index("karana", nm + 0.6)) == "Bava"            # second half
    assert P._name("karana", P._index("karana", nm - 0.1)) == "Naga"            # last half of Amavasya
    assert [P._name("karana", i) for i in (57, 58, 59)] == ["Shakuni", "Chatushpada", "Naga"]
    assert sum(P._name("karana", i) == "Vishti" for i in range(60)) == 8


def test_day_sunrise_vara_and_transitions():
    d = S.panchang("2024-03-20", 28.61, 77.21, "+05:30")
    assert d["sunrise"] == "2024-03-20 06:26" and d["vara"] == "Wednesday"      # USNO upper limb 06:25; disc centre +1 min
    last = {c["element"]: c["ends"] for c in d["changes"]}                     # each element's last listed change
    assert all(t >= d["next_sunrise"] for t in last.values()), last
    kinds = {c["element"] for c in d["changes"]}
    assert kinds == {"tithi", "nakshatra", "yoga", "karana"} and d["meta"]["utc_offset"] == "+05:30"
    assert all(c["ends"] > d["sunrise"] for c in d["changes"])
    z = S.panchang("2024-03-20", 28.61, 77.21, zone="Asia/Kolkata")
    assert z["at_sunrise"] == d["at_sunrise"] and z["meta"]["zone"] == "Asia/Kolkata"


def test_polar_and_invalid_inputs():
    assert S.panchang("2024-06-21", 78.2, 15.6, "+02:00")["polar_fallback"] is True     # midnight Sun
    with pytest.raises(ValueError):
        S.panchang("2024-06-21", 95, 0, "+00:00")
    with pytest.raises(ValueError):
        S.panchang("2024-06-21", 28.6, 77.2)
