"""B-T4: the never-recommend regex covers every item of remedy-safety.md §2 and runs over all client text; Parashari and
Lal Kitab claims cannot mix silently (render_report.checks)."""
import copy
import json
import os
import re
import sys

from astro import config

SKILL = config.load().skill_dir
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import lk_remedies  # noqa: E402
import render_report as rr  # noqa: E402

FIX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "lk_never_probes.json"), encoding="utf-8"))


def table_items():
    """The ';'-separated items of the two '⛔ Never recommend' rows of remedy-safety.md."""
    rows = [ln for ln in open(os.path.join(SKILL, "references", "remedy-safety.md"), encoding="utf-8")
            if ln.startswith("|") and "⛔ **Never recommend" in ln]
    assert len(rows) == 2
    return [i.strip() for ln in rows for i in ln.split("|")[2].split(";") if i.strip()]


def test_one_probe_per_table_item_in_table_order():
    items = table_items()
    assert len(items) == len(FIX["probes"]), "remedy-safety.md ⛔ items changed: add or remove a probe"
    for item, p in zip(items, FIX["probes"]):
        assert item.lower().startswith(p["item"].lower()), (item, p["item"])


def test_every_probe_is_caught_and_benign_text_is_not():
    for p in FIX["probes"]:
        assert lk_remedies.NEVER.search(p["probe"]), p["probe"]
    for t in FIX["extra"]:
        assert lk_remedies.NEVER.search(t), t
    for t in FIX["benign"]:
        assert not lk_remedies.NEVER.search(t), t


def _example():
    return copy.deepcopy(json.load(open(os.path.join(rr.ASSETS, "example-synthetic.json"), encoding="utf-8")))


def test_never_runs_over_all_client_text_not_only_remedy_cards():
    for place in ("meaning", "watch", "manifestation"):
        r = _example()
        r["sections"][0]["units"][0][place] = "Offer milk to a serpent on Saturdays."
        assert any("never-recommend" in e for e in rr.checks(r)[0]), place
    r = _example()
    r["practical_summary"] = ["Keep a piece of ivory at home"]
    assert any("never-recommend" in e for e in rr.checks(r)[0])
    assert not any("never-recommend" in e for e in rr.checks(_example())[0])


def _unit(**kw):
    r = _example()
    r["sections"][0]["units"][0].update(kw)
    return r


def errs(r):
    return rr.checks(r)[0]


def test_lal_kitab_unit_needs_edition_and_lk_section():
    lk = dict(system="lal_kitab", claim_type="rule", claim_basis="TEXT", rule_refs=["LK1952 p59"])
    assert any("edition" in e for e in errs(_unit(**lk)))
    assert any("lk-" in e for e in errs(_unit(edition="lk1952", **lk)))
    r = _unit(edition="lk1952", **lk)
    r["sections"][0]["id"] = "lk-career"
    assert not any(k in e for e in errs(r) for k in ("edition", "lk-", "cites"))


def test_rule_refs_need_system_and_text_needs_rule():
    assert any("system" in e for e in errs(_unit(system=None, rule_refs=["BPHS ch. 7"], claim_type="rule", claim_basis="TEXT")))
    assert any("claim_basis TEXT" in e for e in errs(_unit(claim_type="interpretation", claim_basis="TEXT")))


def test_a_unit_cites_only_its_own_traditions_books():
    base = dict(claim_type="rule", claim_basis="TEXT")
    assert any("Lal Kitab" in e for e in errs(_unit(system="parashari", rule_refs=["LK1952 p59"], **base)))
    assert any("Lal Kitab" in e for e in errs(_unit(system="jaimini", rule_refs=["KB B7 p51"], **base)))
    r = _unit(system="lal_kitab", edition="shrimali", rule_refs=["BPHS ch. 7"], **base)
    r["sections"][0]["id"] = "lk-x"
    assert any("Parashari" in e for e in errs(r))
    assert not any("cites" in e for e in errs(_unit(system="parashari", rule_refs=["BPHS ch. 7"], **base)))


def test_edition_values_match_the_schema_and_the_example_passes():
    enum = rr.json.load(open(os.path.join(rr.ASSETS, "report.schema.json"), encoding="utf-8"))["$defs"]["unit"]["properties"]["edition"]["enum"]
    assert enum == ["shrimali", "lk1952", "both"]
    r = _example()
    assert rr.validate(r, json.load(open(os.path.join(rr.ASSETS, "report.schema.json")))) == [] and errs(r) == []
    assert re.search(r"edition", open(os.path.join(SKILL, "references", "synthesis-method.md"), encoding="utf-8").read())


def test_family_by_name_with_or_without_page():
    base = dict(claim_type="rule", claim_basis="TEXT")
    for ref in ("LK1952", "Shrimali p.12", "Lal Kitab p.12", "LKS", "LKS p.12", "LK1952 p.12"):
        for system in ("parashari", "jaimini"):
            assert any("Lal Kitab" in e for e in errs(_unit(system=system, rule_refs=[ref], **base))), (system, ref)
    r = _unit(system="lal_kitab", edition="both", rule_refs=["Jataka Parijata ch. 4"], **base)
    r["sections"][0]["id"] = "lk-x"
    assert any("Parashari" in e for e in errs(r))


def test_edition_must_match_the_reference():
    base = dict(system="lal_kitab", claim_type="rule", claim_basis="TEXT")
    def run(ed, ref):
        r = _unit(edition=ed, rule_refs=[ref], **base)
        r["sections"][0]["id"] = "lk-x"
        return [e for e in errs(r) if "reference" in e]
    assert run("lk1952", "Shrimali p.12") and run("lk1952", "LKS p.12") and run("shrimali", "LK1952 p.54")
    assert not run("lk1952", "LK1952 p.54") and not run("shrimali", "LKS p.12")
    assert not run("both", "LK1952 p.54") and not run("both", "Shrimali p.12")


def test_combined_only_in_comparison_section():
    u = dict(system="combined", claim_type="interpretation", rule_refs=["LKS p.12"])
    assert any("comparison" in e for e in errs(_unit(**u)))
    r = _unit(**u)
    r["sections"][0]["id"] = "closing-comparison"
    assert not any(k in e for e in errs(r) for k in ("comparison", "cites", "edition"))
