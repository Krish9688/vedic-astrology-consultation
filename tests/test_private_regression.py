"""Local-only regression charts: every private/regression/*_golden.json (same format as
tests/reference_charts/crosscheck_2026_11.json, built by tools/crosscheck/run.sh --golden) is checked with the same
engine-vs-reference checks as the synthetic charts. This file holds no birth data; the charts never leave private/
(never exported, gitignored). Without that folder (CI, a fresh clone) the tests skip.

Test ids and failure messages show only the chart label (e.g. R1), the quantity and the delta - never the input.
"""
from __future__ import annotations

import glob
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_regression_charts import AREAS, check, load_golden  # noqa: E402

PRIVATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "private", "regression")
FILES = sorted(glob.glob(os.path.join(PRIVATE, "*_golden.json")))
REASON = ("no local-only regression charts (private/regression/*_golden.json): they exist only on the owner's machine "
          "and are never exported")


def _cases():
    out = []
    for f in FILES:
        g = load_golden(f)
        for ch in g["charts"]:
            for area in AREAS:
                out.append(pytest.param(ch, area, g["tolerances"], id=f"{ch['id']}-{area}"))
    return out


CASES = _cases()


@pytest.mark.skipif(not CASES, reason=REASON)
@pytest.mark.parametrize("ch,area,tol", CASES or [pytest.param(None, None, None, id="none")])
def test_private_chart_matches_reference(ch, area, tol):
    bad = check(ch, area, tol)
    assert not bad, f"{ch['id']} {area}: {len(bad)} mismatch(es):\n" + "\n".join(bad)
