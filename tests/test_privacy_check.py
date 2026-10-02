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
