# P5-2: the prediction log needs a hit criterion, freezes it, migrates old databases and never calls a wide window with a
# high baseline strong evidence; qc and the audit lint flag 'scientifically proven' and accuracy percentages.
import os
import re
import sqlite3
import sys

import pytest

from astro import cli, config, predictions as P

SKILL = config.load().skill_dir   # private skill/ or the public plugin layout
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import life_lint  # noqa: E402


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "p.sqlite")


def add(db, **kw):
    kw = {"hit_criterion": "new employer within the window", "synthetic": True} | kw
    return P.add("S1", "career", "a change of role", "2027-01", "2027-09", db=db, **kw)


def test_add_rejects_a_record_without_a_criterion(db):
    for bad in (None, "", "   "):
        with pytest.raises(ValueError, match="hit_criterion"):
            P.add("S1", "career", "x", synthetic=True, db=db, hit_criterion=bad)
    with pytest.raises(ValueError):
        add(db, claim_basis="TESTED")                 # earned from evaluated rows, not declared
    with pytest.raises(ValueError):
        add(db, claim_basis="GUESS")
    with pytest.raises(ValueError):
        add(db, baseline=1.5)
    assert P.rows(db) == []


def test_defaults_consent_and_permissions_kept(db):
    with pytest.raises(PermissionError):
        P.add("person-a", "career", "x", db=db, hit_criterion="h")
    r = P.rows(db)
    assert r == []
    add(db)
    row = P.rows(db)[0]
    assert (row["baseline_note"], row["baseline"], row["claim_basis"]) == ("unknown", None, "SPECULATIVE")
    assert os.stat(db).st_mode & 0o777 == 0o600


def test_criterion_window_and_baseline_cannot_change(db):
    pid = add(db, baseline=0.2)
    c = sqlite3.connect(db)
    for col, val in (("hit_criterion", "anything"), ("window_end", "2030-12"), ("baseline", 0.9),
                     ("window_start", "2020-01"), ("prediction", "rewritten")):
        with pytest.raises(sqlite3.DatabaseError, match="cannot change"):
            c.execute(f"UPDATE predictions SET {col}=? WHERE id=?", (val, pid))
    c.close()
    P.evaluate(pid, "changed role", "hit", db=db)                      # outcome / evaluation still settable
    row = P.rows(db)[0]
    assert row["evaluation"] == "hit" and row["hit_criterion"] == "new employer within the window"
    assert row["baseline"] == 0.2 and row["window_end"] == "2027-09"


def test_legacy_database_is_migrated_and_legacy_rows_are_not_scored(db):
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE predictions (id INTEGER PRIMARY KEY, made_on TEXT NOT NULL, chart_id TEXT NOT NULL, "
              "skill_version TEXT, engine_version TEXT, category TEXT NOT NULL, prediction TEXT NOT NULL, "
              "window_start TEXT, window_end TEXT, confidence TEXT, techniques TEXT, supporting TEXT, opposing TEXT, "
              "outcome TEXT, outcome_date TEXT, evaluation TEXT, synthetic INTEGER NOT NULL DEFAULT 0, "
              "consent INTEGER NOT NULL DEFAULT 0)")
    c.execute("INSERT INTO predictions (made_on, chart_id, category, prediction, confidence, evaluation, consent) "
              "VALUES ('2025-01-01','K1','career','old','Moderate','hit',1)")
    c.commit()
    c.close()
    row = P.rows(db)[0]
    assert row["hit_criterion"] == P.LEGACY and row["baseline_note"] == "unknown"
    sc = P.scorecard(db)
    assert sc == {"legacy (excluded: no hit criterion recorded)": {"evaluated": 1}}
    pid = add(db, synthetic=False, consent=True, baseline=0.5)          # new records work on the migrated table
    P.evaluate(pid, "yes", "hit", db=db)
    sc = P.scorecard(db)
    assert sc["career / Moderate"]["scored"] == 1 and sc["career / Moderate"]["hit"] == 1


def test_scorecard_expected_vs_observed_and_unknown_baselines(db):
    for b, ev in ((0.25, "hit"), (0.25, "miss"), (None, "hit")):
        P.evaluate(add(db, baseline=b), "o", ev, db=db)
    v = P.scorecard(db, include_synthetic=True)["career / Moderate"]
    assert (v["hit"], v["miss"], v["scored"]) == (2, 1, 3)
    assert v["expected_hits"] == 0.5 and v["baseline_known"] == 2 and v["baseline_unknown"] == 1
    assert v["evidence"].startswith("none: baseline unknown")


def test_five_year_window_with_0_6_baseline_is_not_strong_evidence(db):
    pid = P.add("S1", "marriage", "a marriage", "2027-01", "2031-12", db=db, synthetic=True,
                hit_criterion="a legal marriage within the window", baseline=0.6)
    P.evaluate(pid, "married 2029", "hit", db=db)
    v = P.scorecard(db, include_synthetic=True)["marriage / Moderate"]
    assert v["expected_hits"] == 0.6 and v["hit"] == 1 and v["wide_windows"] == 1
    assert v["evidence"].startswith("insufficient") and "strong" not in v["evidence"].lower()
    for i in range(40):                                              # even many such hits never read as strong
        P.evaluate(P.add("S1", "marriage", "m", "2027-01", "2031-12", db=db, synthetic=True,
                         hit_criterion="a legal marriage within the window", baseline=0.6), "y", "hit", db=db)
    v = P.scorecard(db, include_synthetic=True)["marriage / Moderate"]
    assert v["evidence"].startswith("indicative only") and "strong" not in v["evidence"].lower()


def test_cli_add_needs_criterion(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.toml"))
    (tmp_path / "config.toml").write_text(f'data_dir = "{tmp_path / "data"}"\n')
    set_ = ["predict", "add", "--chart-id", "S1", "--category", "c", "--text", "t", "--synthetic"]
    with pytest.raises(ValueError, match="hit_criterion"):
        cli.main(set_)
    cli.main(set_ + ["--hit-criterion", "h", "--baseline", "0.3", "--claim-basis", "TEXT"])
    assert "recorded prediction 1" in capsys.readouterr().out
    assert os.stat(tmp_path / "data" / "predictions.sqlite").st_mode & 0o777 == 0o600


@pytest.mark.parametrize("text", ["These readings are scientifically proven.", "Our method has 87% accuracy.",
                                  "Reported accuracy of 92%.", "A 70% success rate in marriage timing."])
def test_audit_flags_proof_and_accuracy_percentages(text):
    assert "certainty" in {c for c, _, _ in life_lint.audit(text)}


def test_audit_leaves_ordinary_percentages_alone():
    assert life_lint.audit("About 17% of champions had Mars in a key sector in the control group.") == []


def test_qc_and_card_state_the_rules():
    qc = open(os.path.join(SKILL, "references", "qc.md"), encoding="utf-8").read()
    assert "scientifically proven" in qc and "accuracy or success percentage" in qc
    card = open(os.path.join(SKILL, "references", "evidence-card.md"), encoding="utf-8").read()
    rows = [l for l in card.splitlines() if re.search(r"\| (true|false)[^|]*\|$", l)]
    assert len(rows) >= 9
    for l in rows:
        if "| false |" in l.replace("| false", "| false |"):
            assert not re.search(r"\d+(\.\d+)?\s?%|p\s?=|\b0\.\d+", l), l      # unopened source: no figures
    assert "no controlled test located" in card and "refuted" in card
    reg = open(os.path.join(SKILL, "references", "contradiction-register.md"), encoding="utf-8").read()
    for rid in ("CR-E01", "CR-E02"):
        assert re.search(rf"\| {rid} \|.*unverified.*\|", reg)
