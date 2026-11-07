# The accuracy scorer (tools/accuracy_score.py) on toy case sets: the rubric §4.3 formula, the minimum-count factor,
# and §4.4 determinism. No real reference values are used here.
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
A = pytest.importorskip("accuracy_score")   # the scorer is private-edition only; the public export ships this test without it


def row(i, area, grade, outcome):
    return {"id": f"{area}-{grade}-{i:03d}", "area": area, "grade": grade, "outcome": outcome}


def test_lost_points_sum_to_k_minus_t():
    rows = [row(i, "A1", "G1", "fail" if i < 2 else "pass") for i in range(7)]
    rows += [row(i, "A1", "G3", "fail" if i == 0 else "pass") for i in range(3)]
    rows += [row(i, "A4", "G2", "fail") for i in range(2)] + [row(9, "A4", "G2", "boundary")]
    rows += [row(i, "A5", "G4", "pass") for i in range(4)] + [row(8, "A5", "G4", "misprint")]
    s = A.aggregate(rows)
    assert s["K"] == 20 + 4 + 5
    assert sum(s["lost"].values()) == pytest.approx(s["K"] - s["T"], abs=1e-12)
    assert set(s["lost"]) == {r["id"] for r in rows if r["outcome"] == "fail"}
    assert s["areas"]["A4"]["score"] == 0 and s["areas"]["A5"]["score"] == 1      # boundary/misprint rows not counted


def test_minimum_count_factor():
    rows = [row(i, "A1", "G1", "pass") for i in range(2)]                        # n = 2: weight 4 x 2/5 = 1.6
    rows += [row(i, "A1", "G3", "pass" if i < 5 else "fail") for i in range(10)]  # n = 10: full weight 2
    s = A.aggregate(rows)
    a = s["areas"]["A1"]
    assert a["grades"]["G1"]["effective_weight"] == pytest.approx(1.6)
    assert a["grades"]["G3"]["effective_weight"] == 2
    assert a["score"] == pytest.approx((1.6 * 1 + 2 * 0.5) / 3.6)
    assert s["T"] == pytest.approx(20 * 2.6 / 3.6)
    assert s["lost"]["A1-G3-005"] == pytest.approx(20 * (2 / 3.6) / 10)
    assert s["per_grade"] == {"G1": 1.0, "G3": 0.5}


def test_comparisons_wrap_and_convert_units():
    assert A.compare("circular_diff", 359.99995, 0.00005, 0.5, "arcsec") == (True, pytest.approx(-0.36))
    assert A.compare("instant_diff", "2000-01-01 00:00:01", "2000-01-01T00:00:00.000", 1, "s") == (True, 1.0)
    assert A.compare("date_diff", "2000-01-03", "2000-01-01", 1, "day") == (False, 2)
    assert A.compare("exact", None, 1, 0, "index") == (False, "missing")


TOY = [
    {"id": "A5-G4-001", "area": "A5", "grade": "G4", "quantity": "chara_years", "unit": "years", "tolerance": 0,
     "comparison": "exact", "status_before_run": "scored", "notes": "", "sub_item": "toy", "source": {},
     "input": {"signs": {"La": "Aq", "Me": "Aq", "Ju": "Aq", "Ve": "Aq", "Ma": "Ta", "Ra": "Ge", "Mo": "Ge",
                         "Su": "Cp", "Ke": "Le", "Sa": "Sc"}},
     "expected": [{"key": "Pi", "value": 1}, {"key": "Ar", "value": 2}]},           # Ar deliberately wrong: one fail
    {"id": "A8-G4-001", "area": "A8", "grade": "G4", "quantity": "war_winner", "unit": "planet", "tolerance": 0,
     "comparison": "exact", "status_before_run": "scored", "notes": "", "sub_item": "toy", "source": {},
     "input": {"latitudes": {"Ma": 1.0, "Ve": -3.0}}, "expected": [{"key": "Ve-Ma", "value": "Ve"}]},
]


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "ephe", "sepl_18.se1")), reason="ephemeris files absent")
def test_two_runs_are_byte_identical_apart_from_run_time(tmp_path):
    (tmp_path / "A5.json").write_text(json.dumps({"cases": [TOY[0]]}))
    (tmp_path / "A8.json").write_text(json.dumps({"cases": [TOY[1]]}))
    outs = []
    for k in (1, 2):
        res = A.run(str(tmp_path), str(tmp_path / f"r{k}"), allow_partial=True)
        outs.append([(tmp_path / f"r{k}.{x}").read_text() for x in ("json", "md")])
    assert res["score"]["K"] == 13 and len(res["score"]["lost"]) == 1
    strip = lambda s: "\n".join(x for x in s.splitlines() if "run_utc" not in x and not x.startswith("Run (UTC)"))  # noqa: E731
    assert strip(outs[0][0]) == strip(outs[1][0]) and strip(outs[0][1]) == strip(outs[1][1])
    with pytest.raises(SystemExit):                                              # rubric Q9: no run below K = 100
        A.run(str(tmp_path), str(tmp_path / "r3"))
