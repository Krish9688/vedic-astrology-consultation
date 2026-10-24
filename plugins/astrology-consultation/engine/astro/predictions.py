"""Private prediction log: dated forecasts recorded BEFORE the outcome, evaluated later — the only honest way to learn
which techniques discriminate. Local SQLite in the data folder; never exposed over MCP/REST; never committed.

Rules: nothing is recorded automatically. A real person's prediction needs `consent=True` (the person agreed to
having it logged); synthetic records are marked `synthetic=True`. chart_id is an opaque label, never birth data.
An evaluated miss stays a miss: the hit criterion, window and baseline are fixed when the record is made (a DB trigger
refuses any later change; evaluate() sets only outcome and evaluation). Every record states its hit criterion; rows
from before that rule are marked LEGACY and never count as scored evidence. The scorecard compares observed hits with
the hits chance alone would give (per-record baselines, where known) and makes no significance claim.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sqlite3

from . import config

SCHEMA = """CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY, made_on TEXT NOT NULL, chart_id TEXT NOT NULL, skill_version TEXT, engine_version TEXT,
  category TEXT NOT NULL, prediction TEXT NOT NULL, window_start TEXT, window_end TEXT, confidence TEXT,
  techniques TEXT, supporting TEXT, opposing TEXT, outcome TEXT, outcome_date TEXT,
  evaluation TEXT CHECK (evaluation IN ('hit','miss','partial','not evaluable') OR evaluation IS NULL),
  synthetic INTEGER NOT NULL DEFAULT 0, consent INTEGER NOT NULL DEFAULT 0,
  hit_criterion TEXT NOT NULL DEFAULT 'legacy: not recorded', baseline_note TEXT NOT NULL DEFAULT 'unknown',
  baseline REAL CHECK (baseline IS NULL OR (baseline >= 0 AND baseline <= 1)),
  claim_basis TEXT NOT NULL DEFAULT 'SPECULATIVE')"""
LEGACY = "legacy: not recorded"
MIGRATE = (("hit_criterion", "TEXT NOT NULL DEFAULT 'legacy: not recorded'"),
           ("baseline_note", "TEXT NOT NULL DEFAULT 'unknown'"), ("baseline", "REAL"),
           ("claim_basis", "TEXT NOT NULL DEFAULT 'SPECULATIVE'"))
FROZEN = "hit_criterion, baseline_note, baseline, window_start, window_end, prediction, category, claim_basis"
BASIS = ("TEXT", "COMMENTARY", "DISPUTED", "COMPUTED", "SPECULATIVE")   # TESTED is earned from evaluated log rows
GRADES = ("Strong", "Moderate", "Weak", "Contradictory", "Unknown")
YM = re.compile(r"^\d{4}-\d{2}$")


def _db(path=None):
    path = path or os.path.join(config.load().data_dir, "predictions.sqlite")
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    c = sqlite3.connect(path)
    c.execute(SCHEMA)
    have = {r[1] for r in c.execute("PRAGMA table_info(predictions)")}
    for col, decl in MIGRATE:                 # databases made before P5-2: old rows keep the LEGACY criterion
        if col not in have:
            c.execute(f"ALTER TABLE predictions ADD COLUMN {col} {decl}")
    c.execute(f"CREATE TRIGGER IF NOT EXISTS predictions_frozen BEFORE UPDATE OF {FROZEN} ON predictions "
              "BEGIN SELECT RAISE(ABORT, 'a recorded prediction cannot change its criterion, window or baseline'); END")
    os.chmod(path, 0o600)                     # private: forecasts about real people
    return c


def add(chart_id, category, prediction, window_start=None, window_end=None, confidence="Moderate", techniques="",
        supporting="", opposing="", skill_version="", engine_version="", synthetic=False, consent=False, db=None, hit_criterion=None, baseline_note="unknown", baseline=None,
        claim_basis="SPECULATIVE"):
    """hit_criterion (what counts as a hit, written before the outcome) is required. baseline is the chance of a hit
    with no astrology (0..1) when known; otherwise leave it None and say why in baseline_note."""
    if not synthetic and not consent:
        raise PermissionError("recording a real person's prediction needs their explicit consent (consent=True)")
    if confidence not in GRADES:
        raise ValueError(f"confidence must be one of {GRADES}")
    for w in (window_start, window_end):
        if w and not YM.match(w):
            raise ValueError("windows are YYYY-MM")
    if not chart_id:
        raise ValueError("chart_id is required (an opaque label such as K1)")
    if re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}", chart_id):
        raise ValueError("chart_id must be an opaque label, not birth data")
    if not (hit_criterion or "").strip():
        raise ValueError("hit_criterion is required: state what would count as a hit before the outcome is known")
    if claim_basis not in BASIS:
        raise ValueError(f"claim_basis must be one of {BASIS} (TESTED comes from evaluated records, not from a label)")
    if baseline is not None and not 0 <= baseline <= 1:
        raise ValueError("baseline is a probability between 0 and 1")
    c = _db(db)
    cur = c.execute("INSERT INTO predictions (made_on, chart_id, skill_version, engine_version, category, prediction, "
                    "window_start, window_end, confidence, techniques, supporting, opposing, synthetic, consent, "
                    "hit_criterion, baseline_note, baseline, claim_basis) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (dt.date.today().isoformat(), chart_id, skill_version, engine_version, category, prediction,
                     window_start, window_end, confidence, techniques, supporting, opposing, int(synthetic),
                     int(consent), hit_criterion.strip(), baseline_note or "unknown", baseline, claim_basis))
    c.commit()
    return cur.lastrowid


def purge(older_than_days, delete=False, db=None):
    """Prediction rows made more than `older_than_days` ago: counted, and deleted only when delete=True."""
    cutoff = (dt.date.today() - dt.timedelta(days=older_than_days)).isoformat()
    c = _db(db)
    n = c.execute("SELECT COUNT(*) FROM predictions WHERE made_on < ?", (cutoff,)).fetchone()[0]
    if delete:
        c.execute("DELETE FROM predictions WHERE made_on < ?", (cutoff,))
        c.commit()
        c.execute("VACUUM")                  # deleted text must not linger in free pages
    return n


def evaluate(pid, outcome, evaluation, outcome_date=None, db=None):
    if evaluation not in ("hit", "miss", "partial", "not evaluable"):
        raise ValueError("evaluation: hit | miss | partial | not evaluable")
    c = _db(db)
    row = c.execute("SELECT evaluation FROM predictions WHERE id=?", (pid,)).fetchone()
    if row is None:
        raise ValueError(f"no prediction {pid}")
    if row[0] is not None:
        raise PermissionError("already evaluated — the first evaluation stands (add a note instead of rewriting)")
    c.execute("UPDATE predictions SET outcome=?, outcome_date=?, evaluation=? WHERE id=?",
              (outcome, outcome_date or dt.date.today().isoformat(), evaluation, pid))
    c.commit()


def rows(db=None, synthetic=None):
    c = _db(db)
    q = "SELECT * FROM predictions" + ("" if synthetic is None else f" WHERE synthetic={int(synthetic)}")
    cols = [d[1] for d in c.execute("PRAGMA table_info(predictions)")]
    return [dict(zip(cols, r)) for r in c.execute(q + " ORDER BY id")]


def _months(r):
    a, b = r["window_start"], r["window_end"]
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:]) - int(a[5:]) + 1 if a and b else None


def scorecard(db=None, include_synthetic=False):
    """Per category / confidence: counts, observed hits vs the hits chance alone would give, and an evidence label.
    Synthetic (test) records are left out unless asked for (EVID-F10); LEGACY rows (no recorded criterion) are counted
    apart and never scored. Only 'hit' counts as an observed hit ('partial' does not). expected_hits sums the
    per-record baselines of scored records; records without one are counted in baseline_unknown and the label then
    says the comparison is not possible. No label is ever stronger than 'indicative', and none is a significance test."""
    out, legacy = {}, 0
    for r in rows(db, synthetic=None if include_synthetic else False):
        if not r["evaluation"]:
            continue
        if r["hit_criterion"] == LEGACY:
            legacy += 1
            continue
        v = out.setdefault(f"{r['category']} / {r['confidence']}", {
            "hit": 0, "miss": 0, "partial": 0, "not evaluable": 0, "scored": 0, "expected_hits": 0.0,
            "baseline_known": 0, "baseline_unknown": 0, "wide_windows": 0})
        v[r["evaluation"]] += 1
        if r["evaluation"] == "not evaluable":
            continue
        v["scored"] += 1
        if r["baseline"] is None:
            v["baseline_unknown"] += 1
        else:
            v["baseline_known"] += 1
            v["expected_hits"] = round(v["expected_hits"] + r["baseline"], 4)
        v["wide_windows"] += (_months(r) or 0) > 24
    for v in out.values():
        if v["baseline_unknown"]:
            v["evidence"] = "none: baseline unknown for some records, so hits cannot be compared with chance"
        elif v["scored"] < 30:
            v["evidence"] = (f"insufficient: {v['hit']} hit(s) vs {v['expected_hits']} expected by chance in "
                             f"{v['scored']} record(s); too few to say anything")
        else:
            v["evidence"] = (f"indicative only: {v['hit']} hit(s) vs {v['expected_hits']} expected; "
                             "no significance test, windows and criteria chosen by the forecaster")
    if legacy:
        out["legacy (excluded: no hit criterion recorded)"] = {"evaluated": legacy}
    return out
