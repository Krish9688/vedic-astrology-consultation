"""P5-1 acceptance: every register, test and doc reference resolves (research findings, catalogue proposals,
contradiction-register rows, Lal Kitab KB cross-rows). Skips where research/ is absent (CI sparse checkout, public)."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "research", "ledger", "findings.json")),
                                reason="research ledgers not in this checkout")
sys.path.insert(0, os.path.join(ROOT, "tools"))


def test_every_reference_resolves():
    import ref_check
    assert ref_check.problems() == []


def test_a_dangling_reference_is_caught():
    import ref_check
    finding, row = "VED-F" + "9999", "CR-V" + "999"   # split so this file does not cite them itself
    stray = os.path.join(ROOT, "docs", "_ref_check_probe.md")
    try:
        with open(stray, "w") as f:
            f.write(f"Cites {finding} and {row}, neither of which exists.\n")
        bad = ref_check.problems()
        assert any(finding in b for b in bad) and any(row in b for b in bad)
    finally:
        os.remove(stray)
