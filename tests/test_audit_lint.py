# life_lint --mode audit (council 6, P3-4): advisory flags for fear, sales, certainty and money language in a
# third-party report. Paraphrased, invented sentences only — never text copied from a real report.
import os
import sys

import pytest

from astro import config


def audit(text):
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import life_lint
    return {cat for cat, _, _ in life_lint.audit(text)}


@pytest.mark.parametrize("text,cat", [
    ("This year a hidden romance of your partner may come to light.", "fear"),
    ("Expect a long illness that doctors struggle to identify.", "fear"),
    ("Someone may have cast black magic on your family.", "fear"),
    ("Book your personalised puja today with the coupon inside.", "sales"),
    ("Talk to our expert astrologers for an energised stone.", "sales"),
    ("These predictions are 100% accurate and scientifically proven.", "certainty"),
    ("March is the right month to invest in the share market.", "money"),
    ("Wear a blue sapphire ring on your middle finger.", "costly-remedy"),
])
def test_audit_flags(text, cat):
    assert cat in audit(text)


@pytest.mark.parametrize("text", ["Career steadies after mid-year; keep up with your studies.",
                                  "Spend time with your parents and help people in need.",
                                  "A good time to plan, not to rush decisions."])
def test_audit_leaves_plain_advice_alone(text):
    assert audit(text) == set()


def test_audit_is_a_mode_of_the_cli(tmp_path, capsys):
    import subprocess
    f = tmp_path / "r.txt"
    f.write_text("Book your puja now.\n")
    out = subprocess.run([sys.executable, os.path.join(config.load().skill_dir, "scripts", "life_lint.py"), str(f),
                          "--mode", "audit"], capture_output=True, text=True).stdout
    assert "AUDIT sales" in out


# P4-3 (council 6): a report unit may say which system it comes from and what kind of claim it is
def test_report_units_carry_claim_types():
    import json
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import render_report as R
    schema = json.load(open(os.path.join(config.load().skill_dir, "assets", "report", "report.schema.json")))
    unit = {"$ref": "#/$defs/unit"}
    ok = {"theme": "t", "meaning": "m", "system": "parashari", "claim_type": "prediction", "rule_refs": ["BPHS 24.1"]}
    assert R.validate(ok, unit, schema) == []
    assert R.validate(ok | {"claim_type": "certainty"}, unit, schema)
    assert R.validate(ok | {"system": "numerology"}, unit, schema)
    assert R.validate(ok | {"rule_refs": "BPHS"}, unit, schema)
