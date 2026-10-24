# Patyayini dasha and pancha vargeeya bala against PVR Examples 122 and 118 (published textbook charts; locators from
# sourcemaps/PVR_part3.md, not page-checked). Inputs are imported from tests/test_tajika.py, so no new birth record.
import datetime as dt
import importlib.util
import pathlib

import pytest

from astro.calc import engine as E
from astro.calc import tajika as TJ
from tests.test_tajika import EX118, EX122

PROTO = pathlib.Path(__file__).resolve().parents[1] / "research" / "CALC" / "pvb_proto.py"


def annual(b, year):              # the same inputs astro.service.tajika passes to TJ.annual
    bj = E.jd_of(dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz))
    P = E.positions(bj)
    return TJ.annual(bj, {"Su": P["Su"]["lon"], "Mo": P["Mo"]["lon"], "Asc": E.asc(bj, b.lat, b.lon)}, year - 1,
                     b.lat, b.lon), b.tz


def local_date(jd, tz):
    return (dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=jd - 2451545.0, hours=tz)).date().isoformat()


def test_example_122_patyayini_mercury_dasha():
    a, tz = annual(EX122, 22)
    rows = a["patyayini"]
    assert [r["lord"] for r in rows] == ["Ve", "Me", "Mo", "Sa", "Lg", "Ju", "Su", "Ma"]
    me = rows[1]
    # PVR prints dates only: Mercury 26 Jun-13 Aug 1993. Reproduced to the calendar day (tolerance: one day).
    assert (local_date(me["start_jd"], tz), local_date(me["end_jd"], tz)) == ("1993-06-26", "1993-08-13")
    assert sum(r["days"] for r in rows) == pytest.approx(TJ.PATYAYINI_YEAR, abs=0.01)
    assert rows[-1]["end_jd"] == pytest.approx(a["jd"] + TJ.PATYAYINI_YEAR, abs=1e-6)
    for r in rows:                # antardashas start with the lord, keep the order, and fill the dasha exactly
        subs = r["antardashas"]
        assert subs[0]["lord"] == r["lord"] and subs[0]["start_jd"] == r["start_jd"]
        assert subs[-1]["end_jd"] == pytest.approx(r["end_jd"], abs=1e-6)
        assert [s["lord"] for s in subs] == [x["lord"] for x in rows[rows.index(r):] + rows[:rows.index(r)]]
    assert "365.2425" in TJ.SOURCES["patyayini"] and "never standalone" in TJ.SOURCES["patyayini"]


def test_patyayini_second_path_from_raw_degrees():
    """Cumulative form: dasha k ends at year x krisamsa_k / largest krisamsa, straight from the raw longitudes."""
    a, _ = annual(EX122, 22)
    kris = sorted([a["asc"] % 30] + [a["positions"][p]["lon"] % 30 for p in TJ.PLANETS])
    ends = [a["jd"] + 365.2425 * k / kris[-1] for k in kris]
    assert [r["end_jd"] for r in a["patyayini"]] == pytest.approx(ends, abs=1e-6)


def test_patyayini_synthetic_ratios():
    rows = TJ.patyayini({"Lg": 10.0, "Su": 32.0, "Mo": 65.0, "Ma": 95.0, "Me": 128.0, "Ju": 156.0, "Ve": 189.0,
                         "Sa": 219.0}, 0.0, year=290.0)        # krisamsas 10, 2, 5, 5, 8, 6, 9, 9 (synthetic)
    assert [(r["lord"], r["days"]) for r in rows] == [("Su", 58.0), ("Mo", 87.0), ("Ma", 0.0), ("Ju", 29.0),
                                                      ("Me", 58.0), ("Ve", 29.0), ("Sa", 0.0), ("Lg", 29.0)]
    assert [s["days"] for s in rows[1]["antardashas"]] == [26.1, 0.0, 8.7, 17.4, 8.7, 0.0, 8.7, 17.4]


def test_example_118_pvb_mars_and_year_lord():
    a, _ = annual(EX118, 34)
    pvb = a["pancha_vargeeya_bala"]
    mars = pvb["planets"]["Ma"]
    assert len(mars) == 1 and len(mars[0]["variants"]) == 2          # Mars is untouched by the Sun-Mercury question
    assert [mars[0][k] for k in ("kshetra", "uchcha", "hadda", "drekkana", "navamsa")] == pytest.approx(
        [15, 13.67, 15, 10, 1.25], abs=0.01)
    assert mars[0]["pvb"] == 13.73                                    # PVR prints 13.7
    # derived, not published: Jupiter's navamsa is Cancer (its exaltation); owner check of PVR p388-391 (CALC-F411):
    # exaltation is not counted as own, so 9.21 only (9.83 was the dropped exaltation-as-own variant)
    assert [g["pvb"] for g in pvb["planets"]["Ju"]] == [9.21]
    cands = {c["planet"] for c in a["candidates"]}
    assert all(max(cands, key=lambda p: res[p]["pvb"]) == "Ma" for res in pvb["by_variant"].values())
    assert a["year_lord"] == "Ma" and "default" in TJ.SOURCES["pancha_vargeeya_bala"]


SYN = {"Su": 75.0, "Mo": 40.0, "Ma": 210.0, "Me": 125.0, "Ju": 100.0, "Ve": 150.0, "Sa": 200.0}   # research R4, synthetic


def rows_with(*planets, tier="trine (strong benefic)"):
    return [{"planet": p, "aspect_on_lagna": tier} for p in planets]


def test_year_lord_variants_are_the_d6_default_and_friends():
    by_var = TJ.pvb_all(SYN)["by_variant"]
    assert list(by_var) == [TJ.PVB_DEFAULT, "Su-Me friends"] and "exaltation" not in " ".join(by_var)


def pvbs(default, friends=None):
    """Hand-made PVB results for year_lord: {planet: pvb} under the default and the 'friends' variant."""
    return {TJ.PVB_DEFAULT: {p: {"pvb": v} for p, v in default.items()},
            "Su-Me friends": {p: {"pvb": v} for p, v in (friends or default).items()}}


def cands(**aspects):
    """Candidates in PVR's order (the first is candidate 1); value None = no aspect on the annual lagna."""
    return [{"planet": p, "aspect_on_lagna": a} for p, a in aspects.items()]


BEN, MAL = "sextile (weak benefic)", "square (weak malefic)"


def test_year_lord_benefic_winner_must_be_strong():
    """C9-5 / CALC-F412 (owner page check of PVR p391-393): a benefic aspect wins only with PVB >= 10."""
    rows = cands(Ju=None, Ma=BEN, Me=MAL)
    assert TJ.year_lord(rows, pvbs({"Ju": 4, "Ma": 13.73, "Me": 16.28}))[0] == "Ma"     # strong benefic beats malefic
    lord, why = TJ.year_lord(rows, pvbs({"Ju": 4, "Ma": 7.3, "Me": 16.28}))            # Example 122's shape
    assert lord == "Me" and "malefic" in why and "strong" in why


def test_year_lord_strong_means_ten_or_more():
    rows = cands(Ju=None, Ma=BEN)
    assert TJ.year_lord(rows, pvbs({"Ju": 4, "Ma": 10.0}))[0] == "Ma"
    assert TJ.year_lord(rows, pvbs({"Ju": 4, "Ma": 9.99}))[0] == "Ju"                   # falls through to candidate 1


def test_year_lord_malefic_tier_also_needs_strength():
    rows = cands(Ju=None, Sa=MAL, Ve=None)
    assert TJ.year_lord(rows, pvbs({"Ju": 4, "Sa": 9.5, "Ve": 6}))[0] == "Ju"


def test_year_lord_very_strong_fallback_then_candidate_one():
    rows = cands(Ju=None, Ma=BEN, Ve=None)
    lord, why = TJ.year_lord(rows, pvbs({"Ju": 4, "Ma": 8, "Ve": 15.0}))                 # no strong aspecting candidate
    assert lord == "Ve" and "very strong" in why
    lord, why = TJ.year_lord(rows, pvbs({"Ju": 4, "Ma": 8, "Ve": 14.99}))
    assert lord == "Ju" and "candidate 1" in why


def test_year_lord_names_a_disagreeing_variant_and_ties_decide_nothing():
    rows = cands(Su=BEN, Ve=BEN)
    lord, why = TJ.year_lord(rows, pvbs({"Su": 11, "Ve": 12}, {"Su": 13, "Ve": 12}))
    assert lord == "Ve" and "Su-Me friends variant names Su" in why
    lord, why = TJ.year_lord(rows, pvbs({"Su": 12, "Ve": 12}))
    assert lord is None and "tie" in why


def test_example_122_year_lord_is_mercury():
    """PVR p411: Mercury is varsheswara. Mars has the only benefic aspect but PVB 7.30 (ordinary); Mercury squares the
    lagna with PVB 16.28 (very strong)."""
    a, _ = annual(EX122, 22)
    assert a["year_lord"] == "Me" and "malefic" in a["year_lord_reason"]


@pytest.mark.skipif(not PROTO.exists(), reason="research prototype not shipped in this edition")
@pytest.mark.parametrize("chart", ["ex118", "syn"])
def test_pvb_matches_research_prototype(chart):
    spec = importlib.util.spec_from_file_location("pvb_proto", PROTO)
    proto = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proto)
    lons = {p: v["lon"] for p, v in annual(EX118, 34)[0]["positions"].items()} if chart == "ex118" else SYN
    for label, friends in TJ.PVB_VARIANTS.items():
        kw = dict(friendship="naisargika_both_views", neutral=.25) if friends else dict(friendship="kesava_two_bloc")
        want = proto.pvb(lons, exalt_own=False, **kw)
        got = TJ.pvb_all(lons)["by_variant"][label]
        assert {p: got[p] for p in TJ.PLANETS} == {p: want[p] for p in TJ.PLANETS}, label


def test_service_returns_patyayini_dates_and_pvb_variants():
    from astro import service as S
    t = S.tajika(EX122, 22)
    me = next(r for r in t["patyayini_dasha"] if r["lord"] == "Me")
    assert me["start"].startswith("1993-06-26") and me["end"].startswith("1993-08-13")      # PVR Example 122
    pvb = t["pancha_vargeeya_bala"]
    assert "by_variant" not in pvb and len(pvb["variants"]) == 2 and pvb["default"] == TJ.PVB_DEFAULT
    assert "p388" in pvb["unsettled"]
