# P5-1 findings registry: tools/findings_check.py on a synthetic research folder, and on the real one (private edition).
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "tools", "findings_check.py")):
    pytest.skip("public edition: no research registry", allow_module_level=True)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import findings_check as FC  # noqa: E402

SRC = {"title": "Synthetic note", "locator": "notes/synthetic.md §1", "accessed": True}


def finding(fid, claim="A synthetic claim.", **kw):
    return {**dict(id=fid, claim=claim, evidence_type="technical", sources=[SRC], source_ids=["S0001"],
                   researcher_verification="verified", audit_verdict="confirmed"), **kw}


def write(tmp_path, merged, role_files=None):
    (tmp_path / "ledger").mkdir()
    (tmp_path / "ledger" / "findings.json").write_text(json.dumps(merged))
    (tmp_path / "ledger" / "sources.json").write_text(json.dumps([{"id": "S0001", "title": "Synthetic note"}]))
    for name, rows in (role_files or {}).items():
        (tmp_path / name.split("/")[0]).mkdir(exist_ok=True)
        (tmp_path / name).write_text(json.dumps(rows))
    return str(tmp_path)


def test_clean_registry_passes(tmp_path):
    a = finding("QA-F1", status="superseded")
    b = finding("QA-F2", "A newer synthetic claim.", status="accepted", supersedes="QA-F1")
    assert FC.problems(write(tmp_path, [a, b], {"QA/QA-R2.ledger.json": [a]})) == []   # a merged copy is fine


def test_each_registry_rule_is_enforced(tmp_path):
    rows = [finding("QA-F1"), finding("QA-F1", "Twice."), finding("QA-F3", source_ids=["S9999"]),
            finding("QA-F4", status="done"), finding("QA-F5", audit_verdict="refuted", status="accepted"),
            finding("QA-F6", supersedes="QA-F99"), finding("QA-F7", audit_verdict="maybe"),
            finding("QA-F8", sources=[dict(SRC, accessed=False)])]
    got = "\n".join(FC.problems(write(tmp_path, rows, {"QA/QA-R2.ledger.json": [finding("QA-F3", "Other claim.")]})))
    for want in ("QA-F1: duplicate id", "unknown source id S9999", "QA-F4: status must be", "refuted finding cannot be accepted",
                 "supersedes -> QA-F99 does not resolve", "QA-F7: audit_verdict", "cannot be 'verified'",
                 "QA-R2.ledger.json: QA-F3: id already used for a different claim"):
        assert want in got, want


def test_real_registry():
    research = os.path.join(ROOT, "research")
    if not os.path.exists(os.path.join(research, "ledger", "findings.json")):
        pytest.skip("no research ledger")
    assert FC.problems(research) == []      # CALC-R4 findings renumbered to CALC-F401..F410 (2026-10-22)
