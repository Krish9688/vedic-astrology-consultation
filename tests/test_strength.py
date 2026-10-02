# Shadbala, Ashtakavarga, Jaimini and birth-time sensitivity: book reference values plus properties.
import datetime as dt
import json
import os

import pytest
import swisseph as swe
from hypothesis import given, settings
from hypothesis import strategies as st

from astro.calc import engine as E
from astro.calc import jaimini as J
from astro.calc import sensitivity as SENS
from astro.calc import strength as S

REF = os.path.join(os.path.dirname(__file__), "reference_charts")
moment = st.datetimes(min_value=dt.datetime(1900, 1, 1), max_value=dt.datetime(2099, 12, 31))
lat = st.floats(min_value=-55, max_value=60)
lon = st.floats(min_value=-180, max_value=180)


def chart(t, la, lo):
    return E.compute(t.date().isoformat(), t.strftime("%H:%M:%S"), 0, la, lo, on="2000-01-01", extras=False)


def test_drik_bala_matches_raman_published_example():
    ref = json.load(open(os.path.join(REF, "raman_1918.json")))
    b = ref["birth"]
    swe.set_sid_mode(swe.SIDM_RAMAN)
    try:
        c = E.compute(b["date"], b["time"], b["tz"], b["lat"], b["lon"], on="2000-01-01", extras=False)
        ut = dt.datetime.fromisoformat(f"{b['date']}T{b['time']}") - dt.timedelta(hours=b["tz"])
        got = S.shadbala(c, ut, b["lat"], b["lon"], b["tz"])["planets"]
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    for p, want in ref["expected"]["drik_virupas"].items():
        assert abs(got[p]["virupas"]["drik"] - want) <= ref["tolerance"], (p, got[p]["virupas"]["drik"], want)


@given(moment, lat, lon)
@settings(max_examples=25, deadline=None)
def test_ashtakavarga_totals_are_fixed_by_the_tables(t, la, lo):
    av = S.ashtakavarga(chart(t, la, lo))
    assert av["totals"] == S.BAV_TOTALS and av["sav_total"] == 337
    assert all(0 <= x <= 8 for row in av["bav"].values() for x in row)


@given(moment, lat, lon)
@settings(max_examples=20, deadline=None)
def test_shadbala_components_stay_in_range(t, la, lo):
    c = chart(t, la, lo)
    sb = S.shadbala(c, t, la, lo, 0)["planets"]
    for p, v in sb.items():
        d = v["detail"]
        assert 0 <= d["uchcha"] <= 60 and 0 <= v["virupas"]["dig"] <= 60, p
        assert 0 <= v["virupas"]["cheshta"] <= 120, p          # Moon's (paksha, doubled) can reach 120
        assert v["virupas"]["naisargika"] == S.NAISARGIKA[p]
        assert 14 <= d["saptavargaja"] <= 315


@pytest.mark.parametrize("a,b", [(3.3, 356.9), (356.9, 3.3), (10.0, 20.0), (179.0, 181.0)])
def test_circular_mean_never_jumps_to_the_far_side(a, b):
    # the defect found in PyJHora/VedAstro: a plain average of 3.3° and 356.9° gives 180°
    avg = (a + ((b - a + 180) % 360 - 180) / 2) % 360
    assert min(abs(avg - a), 360 - abs(avg - a)) <= 90


@given(moment, lat, lon)
@settings(max_examples=25, deadline=None)
def test_karakas_and_arudhas(t, la, lo):
    c = chart(t, la, lo)
    k = J.karakas(c)
    assert sorted(k["scheme7"].values()) == sorted(["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"])
    assert len(set(k["scheme8"].values())) == 8
    lagna = int(c["bodies"]["Asc"]["lon"] // 30)
    for h, pada in J.arudhas(c).items():
        house = (lagna + int(h[1:]) - 1) % 12
        assert pada not in (house, (house + 6) % 12)          # BPHS 29.45 exception always applied


def test_sensitivity_grid_classes_on_synthetic_s1():
    g = SENS.grid("1992-03-14", "09:40", 0, 51.5, -0.12, on="2026-09-27")
    assert set(g["classes"].values()) <= {"robust", "moderate", "high", "very high"}
    assert g["classes"]["ascendant sign"] == "moderate"        # changes 14 minutes later (Gemini), inside ±15
    assert g["rows"]["ascendant sign"][g["offsets_min"].index(15)] == "Gemini"
    assert g["dasha_boundary_shift_days"][0] == 0


def test_war_winner_bphs():
    from astro.calc.strength import war_winner
    lat = {"Ma": 1.0, "Ve": -3.0, "Sa": 0.5, "Ju": 2.0}
    assert war_winner("Ve", "Ma", lat) == "Ve" and war_winner("Sa", "Ve", lat) == "Ve"   # Venus always wins
    assert war_winner("Ma", "Sa", lat) == "Ma" and war_winner("Sa", "Ju", lat) == "Ju"   # else the northern planet


def test_required_rupas_bphs():
    from astro.calc.strength import REQUIRED_RUPAS
    # BPHS ch. 27 (Santhanam p299): 390, 360, 300, 420, 390, 330, 300 virupas for Sun … Saturn
    assert [REQUIRED_RUPAS[p] * 60 for p in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")] == [390, 360, 300, 420, 390, 330, 300]
