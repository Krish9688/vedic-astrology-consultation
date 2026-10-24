"""P7-2: the periodic outlook report: chart-specific drafts, texture-only months, the anti-generic lint, the window
and the two-page limit; and the engine's texture layer (chandrashtama, tara) against raw pyswisseph."""
import copy
import datetime as dt
import json
import os
import sys

import pytest
import swisseph as swe

from astro import config
from astro import service as S
from astro.calc.transit import TARAS

SKILL = config.load().skill_dir
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import render_report as rr  # noqa: E402

SCHEMA = json.load(open(os.path.join(SKILL, "assets", "report", "report.schema.json"), encoding="utf-8"))
from test_transit import B  # noqa: E402  (the synthetic chart of the transit tests)
B2 = B | {"time": "18:30"}       # same day, Moon still in Capricorn, another nakshatra and lagna
MONTH, QUARTER = S.outlook(S.BirthInput(**B), "month", "2026-01-15"), S.outlook(S.BirthInput(**B), "quarter", "2026-01-15")


def draft(o=MONTH):
    return rr.outlook_draft(o)


def errors(r, o=MONTH):
    return rr.validate(r, SCHEMA) + rr.checks(r)[0] + rr.outlook_checks(r, o)[0]


@pytest.mark.parametrize("o", [MONTH, QUARTER], ids=["month", "quarter"])
def test_draft_is_valid_and_passes_its_own_checks(o):
    assert errors(draft(o), o) == []


def test_same_moon_sign_charts_give_different_monthly_drafts():
    c1, c2 = (S.calculate_chart(S.BirthInput(**b)) for b in (B, B2))
    assert int(c1["bodies"]["Mo"]["lon"] // 30) == int(c2["bodies"]["Mo"]["lon"] // 30)
    other = S.outlook(S.BirthInput(**B2), "month", "2026-01-15")
    assert rr.report_text(draft()) != rr.report_text(draft(other))
    assert errors(draft(other), other) == []


def test_a_month_without_event_level_factors_shows_only_texture():
    assert not [f for f in MONTH["factors"] if f["layer"] == "event"]       # the fixture month is quiet
    d = draft()
    assert rr.NO_EVENT.search(rr.report_text(d))
    assert all(u.get("claim_type") != "prediction" for s in d["sections"] for u in s["units"])
    silent = copy.deepcopy(d)
    silent["sections"][1]["units"][0].update(theme="This month", meaning="A lively month.")
    assert any("no event-level timing" in e for e in errors(silent))
    claim = copy.deepcopy(d)
    claim["sections"][2]["units"][0].update(claim_type="prediction", confidence={"event": "Strong"})
    assert any("texture-only window" in e for e in errors(claim))


def test_quarter_with_natal_stations_lists_them_as_events():
    ev = [f for f in QUARTER["factors"] if f["layer"] == "event"]
    assert ev and {f["kind"] for f in ev} <= {"contact", "station_natal", "sade_sati", "ingress"}
    assert not rr.NO_EVENT.search(rr.report_text(draft(QUARTER)))


@pytest.mark.parametrize("sentence,flagged", [
    ("Mars enters Capricorn, bringing energy and drive.", True),
    ("Venus brings romance this month.", True),
    ("Mars enters Capricorn, the 1st from your Moon.", False),
    ("Saturn makes an exact square to your natal Sun.", False),
    ("A good month for planning.", False)])
def test_transit_sentences_need_a_chart_anchor(sentence, flagged):
    d = draft()
    d["sections"][2]["units"][0]["meaning"] = sentence
    assert any("generic transit sentence" in e for e in errors(d)) == flagged


@pytest.mark.parametrize("to,ok", [("2026-01-22", False), ("2026-02-14", True), ("2026-04-17", True), ("2026-06-01", False)])
def test_window_is_monthly_to_quarterly(to, ok):
    d = draft()
    d["period"]["to"] = to
    assert (not any("window must be" in e for e in errors(d))) == ok


def test_factor_refs_are_required_and_must_exist():
    d = draft()
    d["sections"][0]["units"][0]["factor_refs"] = ["F999"]
    del d["sections"][2]["units"][0]["factor_refs"]
    e = errors(d)
    assert any("F999" in x for x in e) and any("names no outlook factor" in x for x in e)


def test_word_limit():
    d = draft()
    d["sections"][2]["units"][0]["nuance"] = "word " * rr.OUTLOOK_WORDS
    assert any("two pages" in e for e in errors(d))


def test_quarter_pdf_fits_two_pages():
    pytest.importorskip("jinja2")
    weasy = pytest.importorskip("weasyprint")
    assert len(weasy.HTML(string=rr.html_of(draft(QUARTER)), base_url=rr.ASSETS).render().pages) <= 2


def test_texture_layer_matches_raw_swisseph():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    moon = lambda t: swe.calc_ut(swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60 - 5.5), swe.MOON,
                                 swe.FLG_SIDEREAL | swe.FLG_SWIEPH)[0][0]
    c = S.calculate_chart(S.BirthInput(**B))
    natal_sign, birth_star = int(c["bodies"]["Mo"]["lon"] // 30), int(c["bodies"]["Mo"]["lon"] // (360 / 27))
    spans = [f for f in MONTH["factors"] if f["kind"] == "chandrashtama" and "continues" not in f["fact"]]
    assert spans                                                                   # the fixture month has one
    for f in spans:                                                                # 2-hour sampling: first in, first out
        a, b = (dt.datetime.strptime(x, "%Y-%m-%d %H:%M") for x in f["when"].split(" to "))
        assert int(moon(a) // 30) == (natal_sign + 7) % 12 != int(moon(a - dt.timedelta(hours=2)) // 30)
        assert int(moon(b) // 30) != (natal_sign + 7) % 12 == int(moon(b - dt.timedelta(hours=2)) // 30)
    tara = next(f for f in MONTH["factors"] if f["kind"] == "tara")["days"]
    for day, name in tara.items():
        t = dt.datetime.fromisoformat(day) + dt.timedelta(hours=12)
        assert name == TARAS[(int(moon(t) // (360 / 27)) - birth_star) % 27 % 9]


def test_a_chandrashtama_spell_open_at_the_window_end_is_kept():
    o = S.outlook(S.BirthInput(**B), "month", "2026-01-05")       # ends 2026-02-04, inside the spell from 02-03
    last = [f for f in o["factors"] if f["kind"] == "chandrashtama"][-1]
    assert "continues past the period" in last["fact"] and last["when"].endswith("2026-02-04 00:00")
