"""C7-10 / KB-F12: graph-only retrieval regression guard. The gold set is frozen (sha256) and split by query hash."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "validation"))
ev = pytest.importorskip("retrieval_eval_graph", reason="validation/ is not in this checkout (CI sparse checkout)")

pytestmark = pytest.mark.skipif(not os.path.exists(ev.GRAPH) or not os.path.exists(ev.CASES),
                                reason="knowledge graph not in this edition")


def test_case_file_is_frozen_and_split_is_deterministic():
    d = ev.load_cases()
    assert ev.digest(d["cases"]) == d["cases_sha256"], "gold set edited after the hash was recorded"
    assert all(c["split"] == ev.split_of(c["query"]) for c in d["cases"])
    assert {c["split"] for c in d["cases"]} == {"tune", "heldout"} and d["baseline"]
    assert all(c["gold"] and all(r.strip() for r in c["gold"].values()) for c in d["cases"])


def test_heldout_recall_not_below_baseline():
    d = ev.load_cases()
    res = ev.evaluate()
    assert res["heldout"]["recall@10"] >= d["baseline"]["heldout"]["recall@10"], res["heldout"]
    assert res["tune"]["recall@10"] >= d["baseline"]["tune"]["recall@10"], res["tune"]
