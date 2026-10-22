"""P3-3: grounding, citation and fact_ref validators in render_report."""
import copy
import json
import os
import re
import sys

import pytest

from astro import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = config.load().skill_dir   # private skill/ or the public plugin layout
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import render_report as rr  # noqa: E402
from astro.calc import engine  # noqa: E402

EX = json.load(open(os.path.join(SKILL, "assets", "report", "example-synthetic.json"), encoding="utf-8"))


@pytest.fixture(scope="module")
def facts():   # the example's synthetic chart: 1992-03-14 09:40 UTC+0, London
    return engine.compute("1992-03-14", "09:40", 0, 51.5, -0.12, on=EX.get("prepared_on") or "2026-01-01", months=60)


def model(**unit):
    r = copy.deepcopy(EX)
    r["sections"][0]["units"][0].update(unit)
    return r


def shift(x):
    if isinstance(x, str):
        return re.sub(r"\b20(\d\d)\b", lambda m: str(int(m.group()) + 1), x)
    if isinstance(x, dict):
        return {k: shift(v) for k, v in x.items()}
    return [shift(v) for v in x] if isinstance(x, list) else x


def test_example_passes(facts):
    errs, _ = rr.grounding(EX, facts)
    assert errs == []


def test_shifted_year_fails(facts):
    errs, _ = rr.grounding(shift(EX), facts)
    assert any("does not match its Mercury" in e for e in errs), errs


def test_narrow_ungrounded_window_errors(facts):
    import datetime as dt
    anchors = [dt.date.fromisoformat(x[k][:10]) for md in facts["vimshottari"] for x in [md] + md["sub"] for k in ("start", "end")]
    anchors += [dt.date.fromisoformat(x["date"]) for x in facts["ingresses"] + facts["slow_contacts"]]
    d = dt.date.fromisoformat(facts["meta"]["transit_date"]).replace(day=1)
    tol = dt.timedelta(days=rr.TOLERANCE_DAYS)
    while any(d - tol <= a <= d + dt.timedelta(days=31) + tol for a in anchors):   # month +-tolerance holds no anchor
        d = (d + dt.timedelta(days=32)).replace(day=1)
    assert d < dt.date.fromisoformat(facts["ingresses"][-1]["date"]) + dt.timedelta(days=400), "no gap found in range"
    r = copy.deepcopy(EX)
    r["timeline"] = [{"start": d.strftime("%Y-%m"), "end": d.strftime("%Y-%m"), "label": "gap", "kind": "window", "basis": "x"}]
    assert any("matches no dasha boundary" in e for e in rr.grounding(r, facts)[0])


def test_window_beyond_horizon_and_broad(facts):
    r = copy.deepcopy(EX)
    r["timeline"] = [{"start": "2040-02", "end": "2040-05", "label": "far", "kind": "window", "basis": "x"},
                     {"start": "2026-10", "end": "2034-01", "label": "long", "kind": "chapter", "basis": "x"}]
    errs, warns = rr.grounding(r, facts)
    assert errs == [] and any("unverified" in w for w in warns) and any("broad window" in w for w in warns)


def test_cr_ids():
    assert rr.citations(model(rule_refs=["CR-V01"]), catalog={}, graph={})[0] == []
    errs, _ = rr.citations(model(rule_refs=["CR-V99"]), catalog={}, graph={})
    assert any("CR-V99" in e for e in errs)


def test_book_citations():
    cat = {"BPHS": {"pages": 400}, "LOL": {"pages": 300}}
    ok = rr.citations(model(rule_refs=["BPHS 24.1", "BPHS ch. 34 sl. 11", "LOL p299"]), catalog=cat, graph={})
    assert ok == ([], [])
    for bad in ("LOL p321", "ZZZ 1.2", "see somewhere"):
        assert rr.citations(model(rule_refs=[bad]), catalog=cat, graph={})[0], bad
    assert rr.citations(model(rule_refs=["BPHS 24.1"]), catalog=None, graph={})  # path via real catalog
    real = rr._catalog()
    if real:
        assert "BPHS" in real and rr.citations(model(rule_refs=["BPHS 24.1"]), graph={}) == ([], [])


def test_graph_ids():
    import kg
    gz = os.path.join(ROOT, "knowledge", "graph", "graph.json.gz")
    if os.path.exists(gz) and not os.path.exists(kg.GRAPH):
        kg.GRAPH = gz
    g = rr._graph()
    if g is None:
        pytest.skip("no knowledge graph")
    assert rr.citations(model(rule_refs=["rule:XXX:deadbeef"]), catalog={}, graph=g)[0]
    real = next(i for i in g if i.startswith("rule:"))
    assert rr.citations(model(rule_refs=[real]), catalog={}, graph=g)[0] == []


def test_no_graph_is_unverified(monkeypatch):
    monkeypatch.setattr(rr, "_graph", lambda: None)
    errs, warns = rr.citations(model(rule_refs=["rule:XXX:deadbeef"]), catalog={})
    assert errs == [] and "citations unverified: no knowledge graph" in warns


def test_rule_claim_needs_refs():
    errs, _ = rr.citations(model(claim_type="rule", rule_refs=[]), catalog={}, graph={})
    assert any("no rule_refs" in e for e in errs)


def test_fact_refs():
    ids = {"schema": "derived_facts/1", "facts": {"F.lagna.sign": {}}}
    assert rr.fact_refs(model(fact_refs=["F.lagna.sign"]), ids)[0] == []
    assert rr.fact_refs(model(fact_refs=["F.moon.nakshatra"]), ids)[0]
    schema = json.load(open(os.path.join(SKILL, "assets", "report", "report.schema.json")))
    assert rr.validate(model(fact_refs=["F.lagna.sign"]), schema) == []
    assert rr.validate(model(fact_refs=["lagna"]), schema)
