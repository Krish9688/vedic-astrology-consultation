# The publication guard: folder location never matters, public rules stay strict, archive rules stay personal-safe
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import privacy_check as P  # noqa: E402


def make(root, rel, text="synthetic"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def test_scanned_folder_location_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_PRIVACY_TERMS", str(tmp_path / "none.txt"))
    root = tmp_path / "private" / "text" / "export"          # parent path full of blocked folder names
    make(root, "README.md")
    assert P.check(P.files([str(root)]))[0] == []


def test_public_and_archive_rules(tmp_path, monkeypatch):
    terms = make(tmp_path, "terms.txt", "Synthetic Person\n")
    monkeypatch.setenv("ASTRO_PRIVACY_TERMS", str(terms))
    root = tmp_path / "repo"
    make(root, "sourcemaps/BPHS_part1.md")
    make(root, "private/chart.md")
    make(root, "text/BPHS.jsonl")
    with zipfile.ZipFile(make(root, "releases/old.skill"), "w") as z:
        z.writestr("SKILL.md", "path /Users/someone/x — kept in history")
    with zipfile.ZipFile(make(root, "releases/bad.skill"), "w") as z:
        z.writestr("notes.md", "chart of synthetic person")
    bad = lambda archive: sorted(x.split(":")[0].split("!")[0] for x in P.check(P.files([str(root)]), archive)[0])
    assert bad(False) == ["private/chart.md", "releases/bad.skill", "releases/old.skill", "sourcemaps/BPHS_part1.md",
                          "text/BPHS.jsonl"]
    assert bad(True) == ["private/chart.md", "releases/bad.skill", "text/BPHS.jsonl"]   # personal term inside a package


def test_gz_and_csv_are_scanned(tmp_path, monkeypatch):
    """G-7: compressed graph files and CSV tables get the same personal-term checks as text."""
    import gzip
    terms = make(tmp_path, "terms.txt", "Synthetic Person\n")
    monkeypatch.setenv("ASTRO_PRIVACY_TERMS", str(terms))
    root = tmp_path / "repo"
    (root / "knowledge").mkdir(parents=True)
    with gzip.open(root / "knowledge" / "graph.json.gz", "wt") as g:
        g.write('{"note": "synthetic person"}')
    make(root, "data/table.csv", "a,Synthetic Person\n")
    found = P.check(P.files([str(root)]), archive=True)[0]
    assert any("graph.json.gz" in f for f in found) and any("table.csv" in f for f in found)



def test_archived_test_results_only_in_the_archive_folder(tmp_path, monkeypatch):
    """T1(a): grading history is archived under archive/skill-test-results/, never inside the skill package."""
    monkeypatch.setenv("ASTRO_PRIVACY_TERMS", str(tmp_path / "none.txt"))
    make(tmp_path / "a", "archive/skill-test-results/v3.4/T01.md")
    assert P.check(P.files([str(tmp_path / "a")]), archive=True)[0] == []
    make(tmp_path / "b", "skill/astrology-consultation/tests/results/T01.md")
    assert P.check(P.files([str(tmp_path / "b")]), archive=True)[0]          # anywhere else still blocked
