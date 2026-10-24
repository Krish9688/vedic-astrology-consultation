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


# ---- dasha timing to the second (P6-1 follow-up; P4-4 Yogini criterion) -----------------------------------------------
# The stored run keeps PyJHora's exact boundaries and the unrounded Moon it was compared with, so the engine's dasha
# arithmetic is re-checked here without PyJHora or ephemeris files: same Moon and year length -> within 1 s.
import datetime as dt  # noqa: E402

import pytest  # noqa: E402

from astro.calc import engine as E  # noqa: E402

BOUNDS = DOC["boundaries"]
SHIPPED_BOUND_S = (0.00005 / (40 / 3) * 20 * 365.256364 + 150e-6) * 86400


def _ours(b, moon, year):
    ut = dt.datetime.fromisoformat(b["ut"])
    v = E.vimshottari(moon, ut, year, levels=2)
    return {"vimshottari MD": [(m["lord"], m["start"]) for m in v],
            "vimshottari AD": [(m["lord"] + "-" + a["lord"], a["start"]) for m in v for a in m["sub"]],
            "yogini MD": [(r["lord"], r["start"]) for r in E.yogini(moon, ut, year, span_years=150)]}


def _gaps(b, moon, year):
    out = {}
    for kind, mine in _ours(b, moon, year).items():
        tool = [(lord, dt.datetime.fromisoformat(t)) for lord, t in b[kind]]
        k = next(i for i, x in enumerate(mine) if x[0] == tool[0][0] and abs((x[1] - tool[0][1]).days) < 5)
        pairs = list(zip(mine[k:], tool))
        assert [a[0] for a, _ in pairs] == [t[0] for t in tool], kind        # same lords, same order
        out[kind] = max(abs((a[1] - b_[1]).total_seconds()) for a, b_ in pairs)
    return out


def test_every_comparable_chart_has_timing_rows():
    comparable = [c["id"] for c in DOC["charts"] if c["counts"].get("chart", {}).get("not comparable") is None]
    assert sorted(BOUNDS) == sorted(comparable) and len(BOUNDS) >= 30
    for c in DOC["charts"]:
        if c["id"] in BOUNDS:
            assert set(c["timing_max_s"]) == {f"{m} {k}" for m in ("matched", "as shipped")
                                              for k in ("vimshottari MD", "vimshottari AD", "yogini MD")}
            assert all(v <= 1 for k, v in c["timing_max_s"].items() if k.startswith("matched")), c["id"]


@pytest.mark.parametrize("cid", sorted(BOUNDS))
def test_dasha_arithmetic_matches_pyjhora_within_one_second(cid):
    b = BOUNDS[cid]
    gaps = _gaps(b, b["moon_unrounded"], b["year_days"])
    assert max(gaps.values()) <= 1.0, gaps                       # Vimshottari MD/AD and Yogini MD


@pytest.mark.parametrize("cid", sorted(BOUNDS))
def test_shipped_moon_rounding_stays_within_its_bound(cid):
    """The engine rounds the Moon once to 0.0001° (QA-F3) and uses 365.256363-day years: boundaries move, but never
    beyond the analytic bound (about 40 minutes), far below the dasha shift of one minute of birth-time error."""
    b = BOUNDS[cid]
    gaps = _gaps(b, round(b["moon_unrounded"], 4) % 360, E.YEAR["sidereal"])
    assert max(gaps.values()) <= SHIPPED_BOUND_S, gaps


def test_rounded_moon_keeps_nakshatra_and_dasha_lord_together():
    """QA-F3 seam: 26.666664° is Bharani (Venus) unrounded but rounds to 26.6667° = Krittika (Sun); the engine feeds the
    rounded value to both, so the printed nakshatra and the first dasha lord never disagree."""
    ut = dt.datetime(2000, 1, 1)
    for raw in (26.666664, 26.666667, 13.333329, 359.99996):
        L = round(raw, 4) % 360
        _, _, i = E.nak(L)
        assert E.vimshottari(L, ut, E.YEAR["sidereal"], levels=1)[0]["lord"] == E.DASA[i % 9][0], raw


# ---- yoga shortcuts (P4-1): where PyJHora's yoga functions part from the skill's named definitions --------------------
YOGA = json.load(open(os.path.join(ROOT, "tests", "fixtures", "oracle", "pyjhora-yoga.json"), encoding="utf-8"))


def _skill_yogas(c):
    from astro import config
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import chart_facts as cf
    ch = {"asc": {"sign": cf.SIGNS[c["asc"]], "deg": 5},
          "planets": {p: {"sign": cf.SIGNS[s], "deg": d} for p, (s, d) in c["planets"].items()}}
    return {row[0]: row[2] for row in cf.candidates(cf.derive(ch))}


def test_yoga_record_and_the_skill_still_agree():
    assert check_package.provenance_errors(YOGA["provenance"]) == [] and YOGA["provenance"]["verdicts"]["unresolved"] == 0
    for r in YOGA["rows"]:
        assert _skill_yogas(YOGA["charts"][r["chart"]])[r["key"].split()[0]] == r["a"], r   # the stored side is current
        assert r["verdict"] == "match" if r["a"] == r["b"] else r["verdict"] == "methodology" and r["note"], r


def test_pyjhora_gajakesari_self_conjunction_shortcut():
    """VED-F4: PyJHora counts Jupiter as the benefic joining Jupiter, so its Gajakesari holds with no other benefic;
    GK-BPHS36 does not. With Venus beside Jupiter both agree."""
    row = lambda c, k: next(r for r in YOGA["rows"] if r["chart"] == c and r["key"].startswith(k))   # noqa: E731
    assert (row("gk_self_conjunction", "GK-BPHS36")["a"], row("gk_self_conjunction", "GK-BPHS36")["b"]) == (False, True)
    assert row("gk_with_venus", "GK-BPHS36")["a"] is row("gk_with_venus", "GK-BPHS36")["b"] is True
    assert (row("kem_rahu_only", "KEM-BARE")["a"], row("kem_rahu_only", "KEM-BARE")["b"]) == (True, False)   # nodes
    assert row("kem_no_node", "KEM-BARE")["a"] is row("kem_no_node", "KEM-BARE")["b"] is True
