"""Private prediction log: dated forecasts recorded BEFORE the outcome, evaluated later — the only honest way to learn
which techniques discriminate. Local SQLite in the data folder; never exposed over MCP/REST; never committed.

Rules: nothing is recorded automatically. A real person's prediction needs `consent=True` (the person agreed to
having it logged); synthetic records are marked `synthetic=True`. chart_id is an opaque label, never birth data.
An evaluated miss stays a miss: windows are not widened after the fact.
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
  synthetic INTEGER NOT NULL DEFAULT 0, consent INTEGER NOT NULL DEFAULT 0)"""
GRADES = ("Strong", "Moderate", "Weak", "Contradictory", "Unknown")
YM = re.compile(r"^\d{4}-\d{2}$")


def _db(path=None):
    path = path or os.path.join(config.load().data_dir, "predictions.sqlite")
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    c = sqlite3.connect(path)
    c.execute(SCHEMA)
    os.chmod(path, 0o600)                     # private: forecasts about real people
    return c


def add(chart_id, category, prediction, window_start=None, window_end=None, confidence="Moderate", techniques="",
        supporting="", opposing="", skill_version="", engine_version="", synthetic=False, consent=False, db=None):
    if not synthetic and not consent:
        raise PermissionError("recording a real person's prediction needs their explicit consent (consent=True)")
    if confidence not in GRADES:
        raise ValueError(f"confidence must be one of {GRADES}")
    for w in (window_start, window_end):
        if w and not YM.match(w):
            raise ValueError("windows are YYYY-MM")
    if re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}", chart_id):
        raise ValueError("chart_id must be an opaque label, not birth data")
    c = _db(db)
    cur = c.execute("INSERT INTO predictions (made_on, chart_id, skill_version, engine_version, category, prediction, "
                    "window_start, window_end, confidence, techniques, supporting, opposing, synthetic, consent) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (dt.date.today().isoformat(), chart_id, skill_version, engine_version, category, prediction,
                     window_start, window_end, confidence, techniques, supporting, opposing, int(synthetic),
                     int(consent)))
    c.commit()
    return cur.lastrowid


def evaluate(pid, outcome, evaluation, outcome_date=None, db=None):
    if evaluation not in ("hit", "miss", "partial", "not evaluable"):
        raise ValueError("evaluation: hit | miss | partial | not evaluable")
    c = _db(db)
    row = c.execute("SELECT evaluation FROM predictions WHERE id=?", (pid,)).fetchone()
    if row is None:
        raise KeyError(pid)
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


def scorecard(db=None):
    out = {}
    for r in rows(db):
        if r["evaluation"]:
            k = (r["category"], r["confidence"])
            out.setdefault(k, {"hit": 0, "miss": 0, "partial": 0, "not evaluable": 0})[r["evaluation"]] += 1
    return {f"{c} / {g}": v for (c, g), v in out.items()}
