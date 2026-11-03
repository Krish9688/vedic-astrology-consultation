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


# ---- R1 consultation report (owner spec 2026-11-01): intake, model and verification stay in private/regression ----
R1_FILES = [os.path.join(PRIVATE, f"R1-{k}.json") for k in ("intake", "model", "verification")]


@pytest.mark.skipif(not all(os.path.exists(f) for f in R1_FILES), reason=REASON)
def test_r1_consultation_report_is_complete(tmp_path):
    import importlib.util
    import json
    import re
    from astro import service as S
    if importlib.util.find_spec("jinja2") is None:
        pytest.skip("jinja2 not installed")
    intake, model, ver = (json.load(open(f, encoding="utf-8")) for f in R1_FILES)
    r = S.create_consultation_report(intake, model, None, S.DEFAULTS, ver, out_dir=str(tmp_path))
    assert r["ok"], [e[:120] for e in r.get("errors", [])]
    html = open(r["html"], encoding="utf-8").read()
    text = re.sub(r"<[^>]+>", " ", html)
    for s in ("1. Client intake", "3. Personalized kundli (Vedic)", "4. Lal Kitab view", "6. Answers to your questions",
              "9. Appendix"):
        assert s in text
    assert len(intake["questions"]) == 10 and all(f'id="{q["id"]}"' in html for q in intake["questions"])
    assert ver["failures"] == 0 and r.get("pdf_problems", []) == []
    assert "Lahiri" in text and not re.search(r"Raman (?:ayanamsa|2[23]\.\d)", text) and "UTC+05:30" in text.replace("UTC +05:30", "UTC+05:30")
