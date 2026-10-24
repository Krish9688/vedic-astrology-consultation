# Lal Kitab rules, code and remedies are public since 3.7 (owner decision 2026-10-25, reversing council option B2).
# What stays private is the book-derived material: the knowledge base, its audit and the Varshaphal table
# (data/lal-kitab/), book and page text, source maps, the extraction, the graph and the index. In the private workspace
# these tests check the markers, the KEEP-OUT list and a real export; in the public repository (no
# tools/public_edition.py, no data/lal-kitab/) they check the shipped skill folder itself.
import hashlib
import json
import os
import re
import sys

import pytest

from astro import config

ROOT = os.path.join(os.path.dirname(__file__), "..")
SKILL = config.load().skill_dir
PRIVATE = os.path.exists(os.path.join(SKILL, "data", "lal-kitab"))
# The same content signatures as tools/public_edition.py KEEP_OUT_CONTENT (that tool stays in the private workspace).
KEEP_OUT = [r"KB Part 0\.2 Validation Register|\bkb-register\b|lk-planet-in-hous[e]|\bB8-\{", r"RECOMMENDED_house_[1],|lk1952_house_[1],",
            r"(?m)^#{2,4} B\d+\. ", r"_skill_[w]orkspace|Documents/Astrology Book[s]"]   # [x] classes: this file never matches itself
KB_SHA256 = {   # the private knowledge base changes only together with its version number (v2.4 since 2026-10-24)
    "LalKitab_Shrimali_Knowledge_Base_v2.2.md": "39f55cca04d507f8a13099132fe38a2827411b3e3842b623491b6e39a1771cca",
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
def test_private_edition_keeps_the_book_derived_material():
    kb = os.path.join(SKILL, "data", "lal-kitab")
    for name, sha in KB_SHA256.items():
        assert hashlib.sha256(open(os.path.join(kb, name), "rb").read()).hexdigest() == sha, name
    method = open(os.path.join(SKILL, "references", "lal-kitab-method.md")).read()
    assert "## 3. Reading procedure" in method


def test_lal_kitab_code_and_notes_are_in_this_edition():
    for f in ("scripts/lal_kitab.py", "scripts/varshaphal.py", "scripts/lk_remedies.py", "references/lal-kitab-method.md",
              "references/remedy-safety.md"):
        assert os.path.exists(os.path.join(SKILL, f)), f
    skill_md = open(os.path.join(SKILL, "SKILL.md")).read()
    assert "Lal Kitab is not part of this edition" not in skill_md and "Lal Kitab Varshaphal and remedies" in skill_md
    assert "does not provide Lal Kitab analysis" not in open(os.path.join(SKILL, "references", "lal-kitab-method.md")).read()


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
            assert not pe.violations(pub, pe.KEEP_OUT_CONTENT), (rel, pe.violations(pub, pe.KEEP_OUT_CONTENT)[:5])
            if rel.endswith(".py"):
                compile(pub, rel, "exec")
        else:
            assert rel.startswith("data/lal-kitab/"), rel          # only the private data folder is left out
    assert pe.public_text("data/lal-kitab/LalKitab_Varshaphal_Table_v2.2.csv", "x") is None
    for f in ("scripts/lal_kitab.py", "scripts/varshaphal.py", "scripts/lk_remedies.py"):
        assert pe.public_text(f, "x = 1\n") == "x = 1\n"       # Lal Kitab code is public


@pytest.mark.skipif(not PRIVATE, reason="public edition")
def test_real_public_export_passes_the_keep_out_gate(tmp_path):
    # the exporter itself (not only the transform) must leave out every KEEP-OUT file, carry the Lal Kitab code and
    # pass the gate
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_public as ex
    files = ex.pairs(str(tmp_path))
    for dst, src in files.items():
        ex.copy(src, dst)
    shipped = {os.path.relpath(d, str(tmp_path)) for d in files}
    skill = f"{ex.PLUG}/skills/astrology-consultation/"
    for rel in ("scripts/lal_kitab.py", "scripts/varshaphal.py", "scripts/lk_remedies.py", "references/lal-kitab-method.md"):
        assert skill + rel in shipped, rel
    assert "tests/test_lal_kitab.py" in shipped and "tests/lk_golden/lk_golden.json" in shipped
    assert not [s for s in shipped if "data/lal-kitab" in s or s in ("tools/clean_lk1952.py", "validation/retrieval_eval.py")]
    kg_pub = open(os.path.join(str(tmp_path), "tools", "kg", "extract.py")).read()   # private KB parser left out
    assert "def add_kb" not in kg_pub and "KB_PATH" not in kg_pub and "def add_kb" in open(os.path.join(ROOT, "tools", "kg", "extract.py")).read()
    compile(kg_pub, "extract.py", "exec")
    add_pub = open(os.path.join(str(tmp_path), "tools", "kg", "add_book.py")).read()   # no call to a private-only script
    assert "retrieval_eval" not in add_pub and "validation/retrieval_eval.py" not in shipped
    ex.catalog(str(tmp_path))                            # the exported catalog: no private KB record or KB codes
    cat = open(os.path.join(str(tmp_path), "knowledge", "catalog.json")).read()
    assert '"id": "KB"' not in cat and "KB R" not in cat and "lal-kitab/" not in cat and "library_root" not in cat
    books = json.loads(cat)["books"]                     # owner's file names and fingerprints stay private (2026-10-21)
    assert books and not [k for b in books for k in b if k in ("file", "sha256", "duplicates")]
    ex.keep_out_gate(str(tmp_path))                      # sys.exit on any finding


@pytest.mark.skipif(not PRIVATE, reason="public edition")
@pytest.mark.parametrize("plant,path", [
    ("age_year,RECOMMENDED_house" "_1,RECOMMENDED_house_2\n1,1,9\n", "plugins/x/notes.csv"),                 # the table under another name
    ("", "plugins/x/skills/y/data/lal-kitab/LalKitab_Shrimali_Knowledge_Base_v2.2.md"),                   # the knowledge base
    ("", "sourcemaps/LK1952_A.md"), ("{}", "text/LKS.jsonl"), ("x", "index/library.sqlite"),
    ("a\n<!-- private-edition -->\nsecret\n", "docs/leaked.md"),                                          # an unclosed marker
    ("### B8. Planet in house\n", "docs/kb-copy.md")])                                                  # a KB section heading
def test_keep_out_gate_fails_on_planted_private_material(tmp_path, plant, path):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_public as ex
    p = tmp_path / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(plant)
    with pytest.raises(SystemExit):
        ex.keep_out_gate(str(tmp_path))


@pytest.mark.skipif(not PRIVATE, reason="public edition")
def test_book_text_gate_catches_a_long_verbatim_passage(tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_public as ex
    if not os.path.exists(os.path.join(ROOT, "text", "LKS.jsonl")):
        pytest.skip("book text not present in this checkout")
    page = next(json.loads(line)["text"] for line in open(os.path.join(ROOT, "text", "LKS.jsonl"), encoding="utf-8")
                if len(json.loads(line)["text"].split()) > 120)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "quote.md").write_text(" ".join(page.split()[20:60]))      # 40 consecutive words of the book
    assert ex.book_text_gate(str(tmp_path))
    (tmp_path / "docs" / "quote.md").write_text(" ".join(page.split()[20:26]))      # a short phrase is fine
    assert not ex.book_text_gate(str(tmp_path))


@pytest.mark.skipif(PRIVATE, reason="private edition")
def test_public_skill_folder_has_no_book_derived_material():
    assert not os.path.exists(os.path.join(SKILL, "data", "lal-kitab"))
    for rel in _skill_files():
        try:
            text = open(os.path.join(SKILL, rel), encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        hits = [m.group(0) for rx in KEEP_OUT for m in re.finditer(rx, text)]
        assert not hits, (rel, hits[:5])
        assert not re.search(r"(?im)^[ \t]*(?:<!--\s*/?\s*(?:private|public)[\s_-]*edition|#\s*</?\s*(?:private|public)[\s_-]*edition>)", text), rel


def test_vedic_calculation_and_chart_facts_work_in_this_edition():
    # removing the Lal Kitab part must not touch the Parashari facts
    from astro.calc import engine as E
    sys.path.insert(0, os.path.join(SKILL, "scripts"))
    import chart_facts
    out = chart_facts.facts(E.chart_facts_input(E.compute("1992-03-14", "09:40", 0, 51.5, -0.12, extras=False)))
    assert "# Parashari D1" in out and "Dispositor chains" in out and "# Houses:" in out
    assert "Lal Kitab fixed-Aries chart" in out and "# Lal Kitab: scripts/lal_kitab.py is missing" not in out


def test_claude_code_config_never_reaches_the_public_export():
    """The research agents, skills, hooks and CLAUDE.md are private-edition tooling: no public MAP entry may match them,
    while the private archive export carries them from repo-root/ (approval checklist items 3-4)."""
    import fnmatch
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    if not os.path.exists(os.path.join(ROOT, "tools", "export_public.py")):
        pytest.skip("exporters stay in the private edition")
    import export_public, export_repo
    for path in (".claude/settings.json", ".claude/agents/vedic-researcher.md", ".claude/skills/verify-rule/SKILL.md",
                 "CLAUDE.md", "research/ledger/findings.json"):
        assert not any(fnmatch.fnmatch(path, g) for g, *_ in export_public.MAP), path
    assert ("repo-root/.claude/**/*", ".") in export_repo.ALLOW


@pytest.mark.skipif(not PRIVATE, reason="public edition")
@pytest.mark.parametrize("name,body", [("docs/X.md", "a\n<!-- private-edition -->\nLK\n<!-- /private-edition -->\nb\n"),
                                       ("tests/t.py", "x = 1\n# <private-edition>\nLK = 2\n# </private-edition>\ny = 3\n")])
def test_markers_in_non_skill_exported_files_are_applied(tmp_path, name, body):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_public as ex
    ex.WS = str(tmp_path)                                # copy() reads rel paths against WS
    try:
        src = tmp_path / name
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text(body)
        dst = tmp_path / "out" / name
        ex.copy(str(src), str(dst))
        assert "LK" not in dst.read_text() and "edition" not in dst.read_text()
        src.write_text(body.split("\n", 1)[0] + "\n<!-- private-edition -->\n# <private-edition>\nLK\n")   # unbalanced
        with pytest.raises((ValueError, SyntaxError)):   # loud either way
            ex.copy(str(src), str(dst))
    finally:
        ex.WS = ROOT
