# Gochara (Phaladeepika XXVI) and the personal outlook: deterministic tables and output-quality checks.
# Synthetic birth data only.
import datetime as dt

import pytest

from astro import service as S
from astro.calc import transit as TR

B = dict(date="1990-05-17", time="06:30", zone="Asia/Kolkata", lat=19.07, lon=72.88)


def test_good_houses_and_vedha_tables_follow_pd_xxvi():
    assert TR.GOOD["Ju"] == {2, 5, 7, 9, 11} and TR.GOOD["Ra"] == TR.GOOD["Su"] and 11 in TR.GOOD["Sa"]
    assert TR.VEDHA["Ma"] == TR.VEDHA["Sa"] and TR.VEDHA["Me"][10] == 8 and TR.VEDHA["Ve"][11] == 3
    assert all(set(v) <= TR.GOOD[p] for p, v in TR.VEDHA.items())       # vedha applies only to good houses


def test_vedha_and_exemptions(monkeypatch):
    def fake(signs):   # planet -> sign index; everything else far away
        return lambda jd, node="mean": {p: {"lon": signs.get(p, 6) * 30 + 15, "speed": 1, "retro": False}
                                        for p in TR.BODIES}
    moon = 0                                                       # natal Moon in Aries
    monkeypatch.setattr(TR.E, "positions", fake({"Ju": 4, "Ve": 3, "Su": 8, "Sa": 8, "Mo": 8, "Me": 8, "Ma": 8,
                                                 "Ra": 8, "Ke": 8}))
    rows = {r["planet"]: r for r in TR.gochara(0, moon, 0)}
    assert rows["Ju"]["house_from_moon"] == 5 and rows["Ju"]["vedha_by"] == ["Ve"]   # Ju good in 5, obstructed from 4
    assert rows["Ju"]["pd_reading"].startswith("favourable house, obstructed by vedha from Ve")
    monkeypatch.setattr(TR.E, "positions", fake({"Su": 10, "Sa": 4}))                # Sun 11th, Saturn in the 5th
    rows = {r["planet"]: r for r in TR.gochara(0, moon, 0)}
    assert rows["Su"]["house_from_moon"] == 11 and rows["Su"]["vedha_by"] == []      # no vedha from Saturn to the Sun


def test_condition_and_sade_sati():
    assert TR._condition("Sa", 6) == "own or exalted sign" and TR._condition("Ju", 9) == "debilitated"
    assert TR._condition("Ju", 2) == "enemy's sign" and TR._condition("Ra", 0) is None
    assert TR.sade_sati(11, 0).startswith("first") and TR.sade_sati(0, 0).startswith("peak")
    assert TR.sade_sati(1, 0).startswith("last") and TR.sade_sati(3, 0) is None


def test_gochara_output_names_frames_and_sources():
    g = S.gochara(S.BirthInput(**B), S.Options(on=dt.date(2026, 1, 15)))
    assert {r["planet"] for r in g["rows"]} == set(TR.BODIES) and g["meta"]["zone"] == "Asia/Kolkata"
    assert all(1 <= r["house_from_moon"] <= 12 and 1 <= r["house_from_lagna"] <= 12 for r in g["rows"])
    assert "PD XXVI" in g["sources"]["gochara"] and "CR-V07" in g["sources"]["vedha"]


def test_transit_rows_carry_the_bindus_of_the_transited_sign():
    """P4-5(d): each planet's own BAV and the SAV for the sign it transits, equal to ashtakavarga(); nodes have none."""
    from astro.calc import strength
    b = S.BirthInput(**B)
    av = strength.ashtakavarga(S._compute(b, S.Options(on=dt.date(2026, 1, 15)), extras=False))
    g = S.gochara(b, S.Options(on=dt.date(2026, 1, 15)))
    for r in g["rows"]:
        i = TR.E.SIGNS.index(r["sign"])
        if r["planet"] in ("Ra", "Ke"):
            assert "bav" not in r
        else:
            assert (r["bav"], r["sav"]) == (av["bav"][r["planet"]][i], av["sav"][i]), r
    assert "quality only" in g["sources"]["bindus"]
    o = S.outlook(b, "month", "2026-01-15")
    ju = next(f for f in o["factors"] if f["kind"] == "gochara" and f["planet"] == "Ju")
    assert f"own {ju['bav']}, SAV {ju['sav']}" in ju["fact"] and "quality only" in ju["source"]


@pytest.mark.parametrize("period", ["day", "week", "month", "year"])
def test_outlook_is_dated_sourced_and_chart_specific(period):
    a = S.outlook(S.BirthInput(**B), period, "2026-01-15")
    b = S.outlook(S.BirthInput(**(B | {"date": "1975-11-02", "time": "21:10"})), period, "2026-01-15")
    assert a["from"] == "2026-01-15" and a["factors"] and all(f["source"] and f["when"] and f["id"] for f in a["factors"])
    assert any(f["kind"] == "dasha" for f in a["factors"]) and any(f["kind"] == "gochara" for f in a["factors"])
    facts = lambda o: {f["fact"] for f in o["factors"] if f["kind"] in ("dasha", "gochara", "moon")}
    assert facts(a) != facts(b)                                    # two charts, same period: different factors
    if period in ("day", "week"):
        assert any(f["kind"] == "moon" for f in a["factors"])
    with pytest.raises(ValueError):
        S.outlook(S.BirthInput(**B), "fortnight", "2026-01-15")


# --- P4-5(c) vedha intervals and (e) station-near-natal episodes (synthetic) -------------------------------------
def ch(planet, date, to):
    return {"planet": planet, "date": date, "from": "x", "to": to}


S0, S1 = "2026-03-01", "2026-05-01"
# natal Moon in Aries: Ju in Leo (5th, favourable) is obstructed by a planet in the 4th (Cancer) [VEDHA Ju 5: 4]
BASE = {"Su": 6, "Ma": 6, "Me": 6, "Ve": 6, "Ju": 4, "Sa": 6}   # all others in the 7th: unfavourable, no vedha


def test_vedha_interval_starts_and_ends_at_the_obstructors_sign_change():
    ch_ = [ch("Ve", "2026-03-04", "Cancer"), ch("Ve", "2026-04-19", "Leo")]
    out = TR.vedha_intervals(BASE, ch_, 0, S0, S1)
    assert out == [{"planet": "Ju", "house": 5, "by": {"Ve": 4}, "start": "2026-03-04", "end": "2026-04-19"}]


def test_vedha_interval_boundaries_and_open_ends():
    v = TR.vedha_intervals(BASE | {"Ve": 3}, [ch("Ve", "2026-04-10", "Leo")], 0, S0, S1)       # obstructed from the start
    assert [(x["start"], x["end"]) for x in v] == [(S0, "2026-04-10")]
    v = TR.vedha_intervals(BASE | {"Ve": 3}, [], 0, S0, S1)                                    # never freed in the window
    assert [(x["start"], x["end"]) for x in v] == [(S0, S1)]
    v = TR.vedha_intervals(BASE, [ch("Ve", S0, "Cancer")], 0, S0, S1)                          # change on the first day
    assert [(x["start"], x["end"]) for x in v] == [(S0, S1)]


def test_vedha_interval_ends_when_the_transiting_planet_leaves_its_good_house():
    v = TR.vedha_intervals(BASE | {"Ve": 3}, [ch("Ju", "2026-03-20", "Virgo")], 0, S0, S1)      # Jupiter 5th -> 6th
    assert [(x["planet"], x["start"], x["end"]) for x in v] == [("Ju", S0, "2026-03-20")]


def test_exempt_pairs_and_unfavourable_houses_never_obstruct():
    # Sun in the 11th (favourable) with Saturn in the 5th: Sun-Saturn exempt; Mercury 2nd with Moon-side obstructor n/a
    assert TR.vedha_intervals(BASE | {"Su": 10, "Sa": 4, "Ju": 6}, [], 0, S0, S1) == []
    # Jupiter in the 4th (not favourable) with a planet in the 12th: no vedha is looked up
    assert TR.vedha_intervals({"Su": 6, "Ma": 6, "Me": 6, "Ve": 11, "Ju": 3, "Sa": 6}, [], 0, S0, S1) == []
    # Mars in the 11th with Saturn in the 5th (vedha Ma 11:5) is NOT exempt
    out = TR.vedha_intervals(BASE | {"Ma": 10, "Sa": 4, "Ju": 6}, [], 0, S0, S1)
    assert [(x["planet"], x["by"]) for x in out] == [("Ma", {"Sa": 5})]


def test_station_two_degrees_from_a_natal_point_is_one_episode():
    lon = {("Sa", "2026-02-01"): 102.0, ("Sa", "2026-06-20"): 98.5, ("Ju", "2026-03-01"): 200.0}
    st = [{"planet": "Sa", "date": "2026-02-01", "station": "retrograde"},
          {"planet": "Ju", "date": "2026-03-01", "station": "retrograde"},
          {"planet": "Sa", "date": "2026-06-20", "station": "direct"}]
    eps = TR.station_episodes(st, lambda p, d: lon[p, d], {"Su": 100.0})
    assert len(eps) == 1 and eps[0]["planet"] == "Sa" and eps[0]["band"] == "close" and eps[0]["orb"] == 1.5
    assert [s["date"] for s in eps[0]["stations"]] == ["2026-02-01", "2026-06-20"]
    wide = TR.station_episodes(st[:1], lambda p, d: 105.0, {"Su": 100.0})                   # 5 deg: wide band
    assert wide[0]["band"] == "wide" and TR.station_episodes(st[:1], lambda p, d: 108.0, {"Su": 100.0}) == []


def test_outlook_carries_vedha_and_station_factors_with_conventions(monkeypatch):
    b = S.BirthInput(**B)
    o = S.outlook(b, "year", "2026-01-15")
    assert "trigger inside" in o["note"] or "triggers inside" in o["note"]
    assert "Moon vedha omitted" in o["sources"]["vedha_intervals"] and "Convention" in o["sources"]["station_natal"]
    for f in o["factors"]:
        if f["kind"] == "vedha":
            assert "obstructed by vedha from" in f["fact"] and " to " in f["when"] and f["source"]
        if f["kind"] == "station_natal":
            assert f["orb"] <= 7 and "orb a convention" in f["fact"]
