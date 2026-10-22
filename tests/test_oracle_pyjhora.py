# P6-1: the stored PyJHora differential-oracle run (tools/oracle_pyjhora.py, dev only) is checked offline. PyJHora is
# never installed or run here; it is an AGPL oracle in its own venv and must never be imported by astro/ or the skill.
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_package  # noqa: E402

RUN = os.path.join(ROOT, "tests", "fixtures", "oracle", "pyjhora-edge.json")
EDGE = os.path.join(ROOT, "tests", "reference_charts", "edge_suite.json")
DOC = json.load(open(RUN, encoding="utf-8"))
AGREE, EXPLAINED = set(DOC["verdict_classes"]["agree"]), set(DOC["verdict_classes"]["explained"])


def _rows():
    return DOC["varga_rules"] + [r for c in DOC["charts"] for r in c["differences"]]


def test_provenance_record_shape_and_pins():
    p = DOC["provenance"]
    assert check_package.provenance_errors(p) == []
    assert p["tool"] == "PyJHora" and p["tool_version"]
    s = json.dumps(p["settings"])
    for pin in ("LAHIRI", "MEAN_SIDEREAL_YEAR", "TRUEPOS off", "mean"):
        assert pin in s, pin
    assert set(p["ephemeris"]) == {"local", "tool"}
    assert [c["id"] for c in DOC["charts"]] == p["charts"]


def test_edge_suite_fully_covered_with_zero_unresolved():
    edge = {c["id"] for c in json.load(open(EDGE, encoding="utf-8"))["charts"]}
    assert edge <= set(DOC["provenance"]["charts"])
    assert DOC["provenance"]["verdicts"]["unresolved"] == 0
    total = {"agree": 0, "explained": 0, "unresolved": 0}
    for counts in DOC["summary"].values():
        for v, n in counts.items():
            total["agree" if v in AGREE else "explained" if v in EXPLAINED else "unresolved"] += n
    assert total == DOC["provenance"]["verdicts"]
    for c in DOC["charts"]:                      # per-chart counts add up to the summary
        for kind, counts in c["counts"].items():
            assert all(n <= DOC["summary"][kind][v] for v, n in counts.items())


def test_every_difference_has_a_cause():
    for r in _rows():
        assert r["verdict"] in AGREE | EXPLAINED, r
        if r["verdict"] not in AGREE:
            assert r.get("note", "").strip(), r      # explained = a stated convention or failure, never a bare flag


def test_varga_variants_recorded_as_conventions():
    keys = {r["key"] for r in DOC["varga_rules"] if r["verdict"] == "methodology"}
    for d in ("D2", "D24", "D30"):
        assert any(k.startswith(d + " ") for k in keys), d
    assert all(r["verdict"] == "match" for r in DOC["varga_rules"]
               if r["key"].split(" method ")[1] == str(DOC["provenance"]["settings"]["vargas"][r["key"].split()[0]]))


JHORA_IMPORT = re.compile(r"^\s*(?:import|from)\s+jhora\b|import_module\(\s*['\"]jhora|__import__\(\s*['\"]jhora", re.M)


def test_no_jhora_import_in_engine_or_skill():
    roots = [os.path.join(ROOT, d) for d in ("astro", "skill", "astrology-prediction", "plugins")]
    roots = [r for r in roots if os.path.isdir(r)]
    assert roots
    hits = []
    for r in roots:
        for dirpath, _, files in os.walk(r):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(dirpath, f)
                    if JHORA_IMPORT.search(open(path, encoding="utf-8", errors="replace").read()):
                        hits.append(os.path.relpath(path, ROOT))
    assert hits == []
    assert JHORA_IMPORT.search("from jhora.panchanga import drik") and JHORA_IMPORT.search("  import jhora")


def test_release_notes_match_claims_need_provenance(tmp_path):
    rid = DOC["provenance"]["run_id"]
    err = check_package.match_claim_errors
    assert err("- engine matched PyJHora on all edge charts")
    assert err("- agrees with VedAstro cell for cell")
    assert not err(f"- engine matched PyJHora on all edge charts (provenance: {rid})")
    assert err(f"- matched JHora on the reference chart (provenance: {rid})")      # a PyJHora run is not JHora
    assert err("- matched PyJHora (provenance: pyjhora-0.0-unknown)")
    assert not err("- faults found: a 'matched JHora' claim for a chart JHora never ran on")   # quoted, reported
    assert not err("- every difference with PyJHora classified")
    # a record with unresolved rows cannot back a 'matched' claim
    bad = dict(DOC["provenance"], run_id="bad-run", verdicts={"agree": 1, "explained": 0, "unresolved": 1})
    (tmp_path / "r.json").write_text(json.dumps({"provenance": bad}))
    assert err("- matched PyJHora (provenance: bad-run)", str(tmp_path))
    assert check_package.notes_errors(str(tmp_path), "Matched PyJHora everywhere.")
