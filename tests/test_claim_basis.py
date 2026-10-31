"""P3-1: claim_basis taxonomy, rendered labels, temporal status, and the tested/proven lint."""
import copy
import gzip
import json
import os
import sys

import pytest

from astro import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = config.load().skill_dir   # private skill/ or the public plugin layout
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import kg  # noqa: E402
import render_report as rr  # noqa: E402

EX = json.load(open(os.path.join(SKILL, "assets", "report", "example-synthetic.json"), encoding="utf-8"))
SCHEMA = json.load(open(os.path.join(SKILL, "assets", "report", "report.schema.json"), encoding="utf-8"))
GRAPH = os.path.join(ROOT, "knowledge", "graph", "graph.json.gz")
BASES = set(SCHEMA["$defs"]["unit"]["properties"]["claim_basis"]["enum"])


def unit(**kw):
    r = copy.deepcopy(EX)
    r["sections"][0]["units"][0].update(kw)
    return r


def test_role_prefixes_are_unambiguous_and_map_into_the_schema():
    keys = list(kg.ROLE_BASIS)
    assert not [(a, b) for a in keys for b in keys if a != b and a.startswith(b)]
    assert set(kg.ROLE_BASIS.values()) <= BASES - {"COMPUTED", "TESTED"}    # neither ever comes from the graph
    assert set(rr.BASIS_LABELS) == BASES


@pytest.mark.skipif(not os.path.exists(GRAPH), reason="knowledge graph not in this edition")
def test_every_graph_role_maps_to_exactly_one_basis():
    nodes = [n.get("attributes") or {} for n in json.load(gzip.open(GRAPH, "rt", encoding="utf-8"))["nodes"]]
    roles = {(a.get("tier"), a["evidence_role"]) for a in nodes if "evidence_role" in a}
    assert roles
    for tier, role in roles:
        assert sum(role.startswith(k) for k in kg.ROLE_BASIS) == 1, role
        assert kg.claim_basis({"tier": tier, "evidence_role": role}) in BASES


def test_basis_rules():
    cb = kg.claim_basis
    assert cb({"tier": "classical", "evidence_role": "direct rule (timing)"}) == "TEXT"
    assert cb({"tier": "modern", "evidence_role": "illustration (worked case, hindsight)"}) == "COMMENTARY"
    assert cb({"tier": "classical", "evidence_role": "dispute note"}) == "DISPUTED"
    inf = {"tier": "synthesis", "evidence_role": "supporting inference (not the author's statement)"}
    assert cb(inf) == "SPECULATIVE" and cb(dict(inf, inferred_by="B. V. Raman")) == "COMMENTARY"
    assert cb({"tier": "synthesis", "evidence_role": "doctrine only — never a forecast"}) == "SPECULATIVE"
    with pytest.raises(ValueError):
        cb({"evidence_role": "hunch"})


def test_example_renders_labels():
    assert rr.validate(EX, SCHEMA) == [] and rr.checks(EX)[0] == []
    html = rr.html_of(EX)
    assert "Interpretation · Commentary · Parashari" in html and "Prediction (interpretive) · Commentary" in html


def test_past_unit_without_history_status_warns_and_shows_not_confirmed():
    r = unit(temporal_mode="past")
    assert any("no history_status" in w for w in rr.checks(r)[1])
    assert "Past: not confirmed" in rr.html_of(r)
    r = unit(temporal_mode="past", history_status="confirmed")
    assert not any("no history_status" in w for w in rr.checks(r)[1]) and "Past: confirmed" in rr.html_of(r)


def test_text_claims_phrased_as_tested_are_rejected():
    r = unit(meaning="This placement is proven to bring promotion.")
    assert any("phrased as tested or proven" in e for e in rr.checks(r)[0])
    r = unit(claim_basis="SPECULATIVE", meaning="Untested; a guess.")
    assert not any("phrased as tested" in e for e in rr.checks(r)[0])


def test_tested_needs_a_result_and_facts_are_computed():
    assert any("no test_result" in e for e in rr.checks(unit(claim_basis="TESTED"))[0])
    r = unit(claim_basis="TESTED", test_result="7 of 12 hits, log PL-1")
    assert rr.checks(r)[0] == [] and "Tested: 7 of 12 hits, log PL-1" in rr.html_of(r)
    assert any("calculated fact" in e for e in rr.checks(unit(claim_type="fact", claim_basis="TEXT"))[0])


def test_chart_facts_header_says_computed():
    import chart_facts as cf
    out = cf.facts({"asc": {"sign": "Taurus"}, "planets": {"Su": {"sign": "Pisces"}, "Mo": {"sign": "Cancer"}}})
    assert out.splitlines()[0].endswith(cf.COMPUTED) and "COMPUTED" in cf.COMPUTED
