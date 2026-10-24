# Conditional-dasha applicability (BPHS ch. 46, roadmap P4-4a): synthetic positions only, no birth data except the
# synthetic service chart S1 from test_service.py.
import datetime as dt

import pytest

from astro import service as S
from astro.calc import applicability as AP

S1 = dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12)

# Base: Aries lagna 25° (Moon's hora, D9 Scorpio, D12 Capricorn); Mars (lagna lord) in Gemini, Venus (7th lord) in
# Leo, Saturn (10th lord) in Pisces, Rahu in Taurus (12th from Mars), Sun in Virgo, Moon 40° ahead (Shukla), day birth.
BASE = dict(Asc=25.0, Su=160.0, Mo=200.0, Ma=70.0, Me=170.0, Ju=250.0, Ve=130.0, Sa=340.0, Ra=40.0, Ke=220.0, day=True)


def verdict(dasha, reading=None, **kw):
    rows = AP.rows(BASE | kw)
    return next(r["holds"] for r in rows if r["dasha"] == dasha and (reading is None or r["reading"].startswith(reading)))


def test_base_chart_meets_no_default_condition():
    assert [r["dasha"] for r in AP.rows(BASE) if r["default"] and r["holds"]] == []


def test_every_row_cites_a_not_page_checked_locator():
    rows = AP.rows(BASE)
    assert len({r["dasha"] for r in rows}) == 9
    for r in rows:
        assert r["source"].startswith("BPHS ch. 46 sl. ") and "not page-checked" in r["source"] and r["inputs"]


# --- Ashtottari ------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("ra, holds", [
    (160.0, True),    # Virgo: 4th from Mars in Gemini (kendra)
    (190.0, True),    # Libra: 5th (trikona)
    (75.0, True),     # Gemini: with Mars, the 1st from it (convention: a kendra), not the lagna
    (40.0, False),    # Taurus: 12th from Mars
    (10.0, False),    # Aries: 11th from Mars, and the lagna itself
])
def test_ashtottari_rahu_condition(ra, holds):
    assert verdict("Ashtottari", "Rahu", Ra=ra) is holds


def test_ashtottari_rahu_in_lagna_fails_even_in_a_kendra_from_the_lagna_lord():
    assert verdict("Ashtottari", "Rahu", Ma=100.0, Ra=10.0) is False      # Mars in Cancer, Rahu in Aries = its 10th


def test_ashtottari_sign_cusp_boundary():
    assert verdict("Ashtottari", "Rahu", Ra=150.0) is True                 # 0° Virgo
    assert verdict("Ashtottari", "Rahu", Ra=149.9999) is False             # 29°59' Leo: 3rd from Mars


@pytest.mark.parametrize("day, elong, pak", [(True, 200.0, True), (False, 20.0, True), (True, 20.0, False),
                                              (False, 200.0, False), (False, 179.999, True), (False, 180.0, False)])
def test_ashtottari_paksha_clause(day, elong, pak):
    kw = dict(day=day, Mo=(160.0 + elong) % 360, Ra=160.0)                 # Rahu condition met
    assert verdict("Ashtottari", "paksha", **kw) is pak
    assert verdict("Ashtottari", "with", **kw) is pak                      # Rahu holds, so the clause decides
    assert verdict("Ashtottari", "Rahu", **kw) is True                     # the reading without the clause


def test_ashtottari_with_clause_needs_the_rahu_condition_too():
    assert verdict("Ashtottari", "paksha", day=True, Mo=0.0) is True and verdict("Ashtottari", "with", day=True, Mo=0.0) is False


# --- hora, navamsha, dwadashamsha conditions -------------------------------------------------------------------------
@pytest.mark.parametrize("asc, mo, holds", [
    (20.0, 70.0, True),     # Moon's hora (Aries 15-30), Krishna
    (20.0, 200.0, False),   # Moon's hora, Shukla
    (10.0, 200.0, True),    # Sun's hora (Aries 0-15), Shukla
    (10.0, 70.0, False),    # Sun's hora, Krishna
    (15.0, 70.0, True),     # boundary: exactly 15° is the second (Moon) hora
    (14.9999, 70.0, False),
])
def test_shodashottari(asc, mo, holds):
    assert verdict("Shodashottari", Asc=asc, Mo=mo) is holds


@pytest.mark.parametrize("asc, holds", [(5.0, True), (2.0, False), (10 / 3, True), (10 / 3 - 1e-6, False),
                                         (181.0, True), (190.0, False)])   # Aries 2nd navamsha Taurus; Libra 1st Libra, 4th Capricorn
def test_dwadashottari(asc, holds):
    assert verdict("Dwadashottari", Asc=asc) is holds


@pytest.mark.parametrize("asc, holds", [(91.0, True), (90.0, True), (92.4999, True), (92.5, False), (125.0, False)])
def test_panchottari(asc, holds):
    assert verdict("Panchottari", Asc=asc) is holds


@pytest.mark.parametrize("asc, holds", [(1.0, True), (5.0, False), (10 / 3 - 1e-6, True), (10 / 3, False),
                                         (135.0, True), (125.0, False)])  # Leo (fixed): vargottama in its 5th navamsha
def test_shatabdika(asc, holds):
    assert verdict("Shatabdika", Asc=asc) is holds


# --- lord and Sun conditions -----------------------------------------------------------------------------------------
@pytest.mark.parametrize("sa, holds", [(280.0, True), (310.0, False), (270.0, True), (269.9999, False)])
def test_chaturashiti_sama(sa, holds):
    assert verdict("Chaturashiti-sama", Sa=sa) is holds


@pytest.mark.parametrize("ma, ve, eng, skt", [
    (10.0, 130.0, True, True),     # lagna lord in the lagna
    (190.0, 130.0, True, True),    # lagna lord in the 7th
    (70.0, 5.0, False, True),      # 7th lord Venus in the lagna: the Sanskrit reading only
    (70.0, 130.0, False, False),
    (180.0, 130.0, True, True),    # 0° Libra
    (179.9999, 130.0, False, False),
])
def test_dwisaptati_sama_both_readings(ma, ve, eng, skt):
    assert verdict("Dwisaptati-sama", "English", Ma=ma, Ve=ve) is eng
    assert verdict("Dwisaptati-sama", "with", Ma=ma, Ve=ve) is skt


@pytest.mark.parametrize("su, holds", [(15.0, True), (45.0, False), (0.0, True), (359.9999, False)])
def test_shashtihayani(su, holds):
    assert verdict("Shashtihayani", Su=su) is holds


@pytest.mark.parametrize("day, asc, holds", [(True, 10.0, True), (False, 20.0, True), (True, 20.0, False),
                                              (False, 10.0, False), (True, 14.9999, True), (True, 15.0, False)])
def test_shattrimsha_sama(day, asc, holds):
    assert verdict("Shattrimsha-sama", day=day, Asc=asc) is holds


# --- report: default, overlap, birth-time flips ----------------------------------------------------------------------
def fake_state(base, asc_per_min=0.25):
    t0 = dt.datetime(2000, 1, 1)
    return lambda ut, lat, lon, node="mean": base | {"Asc": base["Asc"] + (ut - t0).total_seconds() / 60 * asc_per_min,
                                                     "polar_fallback": False}


def test_report_states_default_and_flags_overlap(monkeypatch):
    # Cancer 1°: Panchottari (D12 Cancer) and Shatabdika (D9 Cancer) both hold; lagna moves 0.25°/min.
    monkeypatch.setattr(AP, "state", fake_state(BASE | {"Asc": 91.0}))
    r = AP.report(dt.datetime(2000, 1, 1), 0, 0)
    assert r["default"] == "Vimshottari default (BPHS 46.2-5)" and "not page-checked" in r["default_source"]
    assert {"Panchottari", "Shatabdika"} <= set(r["applies"]) and r["overlap"]
    assert "BPHS gives no rule for choosing" in r["overlap_note"]


def test_report_no_overlap_note_when_one_or_none_applies(monkeypatch):
    monkeypatch.setattr(AP, "state", fake_state(BASE))
    r = AP.report(dt.datetime(2000, 1, 1), 0, 0)
    assert r["applies"] == [] and not r["overlap"] and r["overlap_note"] is None


def test_report_flags_birth_time_flips(monkeypatch):
    # Aries 14.9°, Shukla, day: Sun's hora now, Moon's hora half a minute later (15.025°) -> flips at +0.5 min.
    monkeypatch.setattr(AP, "state", fake_state(BASE | {"Asc": 14.9}))
    r = AP.report(dt.datetime(2000, 1, 1), 0, 0)
    row = next(x for x in r["rows"] if x["dasha"] == "Shodashottari")
    assert row["birth_time_sensitive"] and row["flips_at_min"] == {"earlier": None, "later": 0.5}
    assert "Shodashottari" in r["birth_time_sensitive"]
    steady = next(x for x in r["rows"] if x["dasha"] == "Chaturashiti-sama")
    assert not steady["birth_time_sensitive"] and steady["flips_at_min"] == {"earlier": None, "later": None}


def test_report_reading_dependent(monkeypatch):
    monkeypatch.setattr(AP, "state", fake_state(BASE | {"Ve": 5.0}))      # 7th lord in the lagna
    assert "Dwisaptati-sama" in AP.report(dt.datetime(2000, 1, 1), 0, 0)["reading_dependent"]


def test_service_on_synthetic_chart():
    r = S.dasha_applicability(S.BirthInput(**S1))
    assert r["default"] == "Vimshottari default (BPHS 46.2-5)" and len(r["rows"]) == 12 and r["window_min"] == 15
    assert r["meta"]["engine"].startswith("astro ")
    day = next(x for x in r["rows"] if x["dasha"] == "Shattrimsha-sama")["inputs"]["birth"]
    assert day == "day"                                                    # 09:40 UT in London in March
