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
