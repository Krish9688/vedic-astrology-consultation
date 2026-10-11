# Option B2 (council 2026-10-12): the public edition carries no Lal Kitab-derived content; the private edition keeps
# all of it. In the private workspace these tests check the markers, the private files and a real export; in the public
# repository (no tools/public_edition.py, no scripts/lal_kitab.py) they check the shipped skill folder itself.
import hashlib
import os
import re
import sys

import pytest

from astro import config

ROOT = os.path.join(os.path.dirname(__file__), "..")
SKILL = config.load().skill_dir
PRIVATE = os.path.exists(os.path.join(SKILL, "scripts", "lal_kitab.py"))
# The same patterns as tools/public_edition.py FORBIDDEN_IN_SKILL (that tool stays in the private workspace).
FORBIDDEN = [r"\bLK1952\b|\bLKS\b|Shrimali", r"\bLK_[A-Z]+\b|\bpakka\b|\bdharmi\b|mangal-?bad",
             r"\bKB\b|knowledge base v2|CR-L\d|CR-X1[5-8]\b", r"(?i)varshaphal\.py|varshaphal (?:csv|table)|\bsleeping planet",
             r"data/lal-kitab"]
KB_SHA256 = {   # the private knowledge base must never change (B2 touches only the public edition)
    "LalKitab_Shrimali_Knowledge_Base_v2.2.md": "b9d15b1f9f224ea077deca69fd7716866a7c968a911bb3c54ed26bc0cc0077ca",
    "LalKitab_Validation_Audit_Report_v2.2.md": "ceb251714fc64c6095776869b909ef71fb923e80a69b1d84680c9acbd47c358e",
    "LalKitab_Varshaphal_Table_v2.2.csv": "9cf7ea1e9ea3645d03f6f30764c1a9f606229c74f08055b789ab0eb0dd9b90ac",
}


def _skill_files():
    for d, _, fs in os.walk(SKILL):
        if "__pycache__" in d or os.sep + "results" in d:
            continue
        for f in fs:
            if f != ".DS_Store":
                yield os.path.relpath(os.path.join(d, f), SKILL)


@pytest.mark.skipif(not PRIVATE, reason="public edition")
def test_private_edition_keeps_the_lal_kitab_material():
    kb = os.path.join(SKILL, "data", "lal-kitab")
    for name, sha in KB_SHA256.items():
        assert hashlib.sha256(open(os.path.join(kb, name), "rb").read()).hexdigest() == sha, name
    for f in ("scripts/lal_kitab.py", "scripts/varshaphal.py"):
        assert os.path.exists(os.path.join(SKILL, f)), f
    method = open(os.path.join(SKILL, "references", "lal-kitab-method.md")).read()
    assert "## 3. Reading procedure" in method          # the full private method is still there


@pytest.mark.skipif(not PRIVATE, reason="public edition")
def test_public_view_of_every_skill_file_is_clean():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import public_edition as pe
    for rel in _skill_files():
        try:
            text = open(os.path.join(SKILL, rel), encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        pub = pe.public_text(rel, text)                  # raises on unbalanced markers
        if pub is not None:
            assert not pe.violations(pub, pe.FORBIDDEN_IN_SKILL), (rel, pe.violations(pub, pe.FORBIDDEN_IN_SKILL)[:5])
            if rel.endswith(".py"):
                compile(pub, rel, "exec")
    assert pe.public_text("scripts/lal_kitab.py", "x") is None and pe.public_text("scripts/varshaphal.py", "x") is None


@pytest.mark.skipif(not PRIVATE, reason="public edition")
def test_real_public_export_passes_the_b2_gate(tmp_path):
    # the exporter itself (not only the transform) must leave out every private-edition file and pass the B2 gate
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_public as ex
    files = ex.pairs(str(tmp_path))
    for dst, src in files.items():
        ex.copy(src, dst)
    shipped = {os.path.relpath(d, str(tmp_path)) for d in files}
    skill = f"{ex.PLUG}/skills/astrology-consultation/"
    for rel in ("scripts/lal_kitab.py", "scripts/varshaphal.py"):
        assert skill + rel not in shipped, rel
    assert not [s for s in shipped if "data/lal-kitab" in s or s in ("tools/clean_lk1952.py", "validation/retrieval_eval.py")]
    ex.b2_gate(str(tmp_path))                            # sys.exit on any finding


@pytest.mark.skipif(PRIVATE, reason="private edition")
def test_public_skill_folder_has_no_lal_kitab_material():
    for rel in ("scripts/lal_kitab.py", "scripts/varshaphal.py", "data/lal-kitab"):
        assert not os.path.exists(os.path.join(SKILL, rel)), rel
    for rel in _skill_files():
        try:
            text = open(os.path.join(SKILL, rel), encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        hits = [m.group(0) for rx in FORBIDDEN for m in re.finditer(rx, text)]
        assert not hits, (rel, hits[:5])
    assert "does not provide Lal Kitab analysis" in open(os.path.join(SKILL, "references", "lal-kitab-method.md")).read()
    skill_md = open(os.path.join(SKILL, "SKILL.md")).read()
    assert "Lal Kitab is not part of this edition" in skill_md and "ships the Varshaphal" not in skill_md


def test_vedic_calculation_and_chart_facts_work_in_this_edition():
    # removing the Lal Kitab part must not touch the Parashari facts
    from astro.calc import engine as E
    sys.path.insert(0, os.path.join(SKILL, "scripts"))
    import chart_facts
    out = chart_facts.facts(E.chart_facts_input(E.compute("1992-03-14", "09:40", 0, 51.5, -0.12, extras=False)))
    assert "# Parashari D1" in out and "Dispositor chains" in out and "# Houses:" in out
    assert ("Lal Kitab fixed-Aries chart" in out) == PRIVATE
    assert ("# Lal Kitab: not part of this edition" in out) == (not PRIVATE)
