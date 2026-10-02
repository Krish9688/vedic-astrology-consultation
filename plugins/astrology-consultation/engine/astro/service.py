"""The stable, vendor-neutral service layer. The CLI, the MCP server and the REST API all call these functions and
nothing else, so every client gets the same validated inputs, privacy rules and outputs.

Responsibilities stay separate: calculation (astro.calc), knowledge (the skill's local search scripts), reasoning
(the AI client following the skill's method — this layer supplies facts, sensitivity classes and the method text;
it does not pretend to reason), reports (render a Structured Report Model).
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import sys
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from . import config
from .calc import compute_full, engine, jaimini, sensitivity, strength

VERSION = "3.5.0"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
TOPICS = {  # question → the skill's topic reference (SKILL.md routing table)
    "relationships-marriage": r"marri|spouse|wife|husband|partner|relationship|love|romance|dating|girlfriend|boyfriend",
    "career-money": r"career|job|work|business|promotion|income|money|financ|wealth|debt|salary",
    "home-family-children": r"home|house|property|mother|father|parent|sibling|brother|sister|child|famil|friend",
    "travel-education-health-life": r"abroad|foreign|travel|relocat|move|study|education|degree|health|wellbeing|"
                                    r"spiritual|year ahead|next year|12 months",
}


class BirthInput(BaseModel):
    date: dt.date
    time: str = Field(pattern=r"^\d{1,2}:\d{2}(:\d{2})?$")
    tz: float = Field(ge=-14, le=14, description="UTC offset in hours at the birth moment (include daylight saving)")
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    label: Optional[str] = Field(default=None, max_length=64)
    time_source: Optional[str] = Field(default=None, max_length=120)

    @field_validator("time")
    @classmethod
    def _clock(cls, v):
        h, m, *s = (int(x) for x in v.split(":"))
        if not (0 <= h < 24 and 0 <= m < 60 and all(0 <= x < 60 for x in s)):
            raise ValueError("time must be a valid 24-hour clock time")
        return v if s else v + ":00"


class Options(BaseModel):
    on: Optional[dt.date] = None        # reference date for transits / running periods (default today)
    months: int = Field(default=24, ge=1, le=120)
    node: str = Field(default="mean", pattern="^(mean|true)$")
    year: str = Field(default="sidereal", pattern="^(sidereal|365.25|360)$")

    model_config = {"frozen": True}


DEFAULTS = Options()


def _args(b: BirthInput, o: Options):
    return (b.date.isoformat(), b.time, b.tz, b.lat, b.lon), dict(
        node=o.node, year=o.year, on=(o.on or dt.date.today()).isoformat(), months=o.months)


def engine_info() -> dict:
    s = config.load()
    return {"service": "astrology-consultation", "version": VERSION, "engine": engine.ENGINE_VERSION,
            **engine.ephemeris_info(), "ayanamsa": "Lahiri (default)", "privacy_mode": s.mode,
            "external_calculation_allowed": s.external_allowed,
            "knowledge_available": bool(s.knowledge_dir), "skill_available": bool(s.skill_dir),
            "vargas": engine.VARGA_METHODS, "shadbala_conventions": strength.SHADBALA_CONVENTIONS,
            "jaimini_conventions": jaimini.CONVENTIONS}


def calculate_chart(b: BirthInput, o: Options = DEFAULTS, full: bool = True) -> dict:
    a, kw = _args(b, o)
    return compute_full(*a, **kw) if full else engine.compute(*a, **kw)


def planet_positions(b: BirthInput) -> dict:
    c = engine.compute(*_args(b, Options())[0], extras=False)
    return {"meta": c["meta"], "bodies": {k: {x: v[x] for x in ("sign", "deg", "lon", "nakshatra", "pada", "retro")}
                                          for k, v in c["bodies"].items()}}


def divisional_chart(b: BirthInput, division: int) -> dict:
    if division not in engine.VARGAS:
        raise ValueError(f"supported divisions: {engine.VARGAS}")
    c = engine.compute(*_args(b, Options())[0], extras=False)
    return {"division": f"D{division}", "method": engine.VARGA_METHODS[f"D{division}"],
            "signs": {k: v["vargas"][f"D{division}"] for k, v in c["bodies"].items()}}


def dasha(b: BirthInput, o: Options = DEFAULTS) -> dict:
    a, kw = _args(b, o)
    c = engine.compute(*a, **kw, extras=False)
    on = kw["on"]
    running = next(([md["lord"], ad["lord"], pd["lord"]] for md in c["vimshottari"] for ad in md["sub"]
                    for pd in ad["sub"] if pd["start"] <= on < pd["end"]), None)
    return {"system": "Vimshottari", "year_days": engine.YEAR[o.year], "running_on": on, "running": running,
            "periods": c["vimshottari"]}


def transits(b: BirthInput, o: Options = DEFAULTS) -> dict:
    a, kw = _args(b, o)
    c = engine.compute(*a, **kw)
    return {k: c[k] for k in ("transits", "ingresses", "slow_contacts")} | {"on": kw["on"]}


def shadbala(b: BirthInput) -> dict:
    c = engine.compute(*_args(b, Options())[0], extras=False)
    ut = dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz)
    return strength.shadbala(c, ut, b.lat, b.lon, b.tz)


def ashtakavarga(b: BirthInput) -> dict:
    return strength.ashtakavarga(engine.compute(*_args(b, Options())[0], extras=False))


def jaimini_factors(b: BirthInput) -> dict:
    return jaimini.jaimini(engine.compute(*_args(b, Options())[0], extras=False))


def birth_time_sensitivity(b: BirthInput, o: Options = DEFAULTS) -> dict:
    a, kw = _args(b, o)
    g = sensitivity.grid(*a, on=kw["on"], year=o.year)
    return g | {"table_markdown": sensitivity.render(g)}


def compare_engines(b: BirthInput, vedastro_dir: Optional[str] = None, live: bool = False) -> dict:
    """Local vs VedAstro. `vedastro_dir`: previously fetched raw results inside the data folder (no network).
    `live`: call VedAstro now — only in hybrid/research mode; sends date, time, offset and coordinates."""
    from .calc.adapters import from_local
    from .calc.compare import load_vedastro_dir, summary, table, validate
    s = config.load()
    A = from_local(calculate_chart(b))
    if live:
        if not s.external_allowed:
            raise PermissionError("live VedAstro comparison needs privacy mode 'hybrid' (astro setup)")
        vedastro_dir = os.path.join(s.data_dir, "vedastro", dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
        off = f"{'+' if b.tz >= 0 else '-'}{int(abs(b.tz)):02d}:{int(round(abs(b.tz) % 1 * 60)):02d}"
        subprocess.run([sys.executable, "-m", "astro.vedastro_batch", "--date", b.date.strftime("%d/%m/%Y"), "--time", b.time[:5],
                        "--tz", off, "--lat", str(b.lat), "--lon", str(b.lon), "--out", vedastro_dir], check=True)
    if not vedastro_dir:
        return {"engines": ["local"], "note": "no second engine supplied"}
    vedastro_dir = _inside(vedastro_dir, s.data_dir)
    V = validate(A, load_vedastro_dir(vedastro_dir, birth=A.birth))
    return {"engines": ["local", V.cross_check_engine], "summary": summary(V.agreements),
            "unresolved": [x.model_dump() for x in V.disagreements()], "table_markdown": table(V.agreements)}


def _run_skill_script(name, *args):
    s = config.load()
    if not s.skill_dir:
        raise FileNotFoundError("skill folder not found (astro setup)")
    env = dict(os.environ)
    if s.knowledge_dir:
        env.setdefault("ASTRO_KG", os.path.join(s.knowledge_dir, "graphify-out", "graph.json"))
        env.setdefault("ASTRO_LIBRARY_DB", os.path.join(s.knowledge_dir, "index", "library.sqlite"))
    r = subprocess.run([sys.executable, os.path.join(s.skill_dir, "scripts", name), *args], capture_output=True,
                       text=True, env=env, timeout=120)
    return (r.stdout or r.stderr).strip()


def search_sources(query: str, sources: Optional[str] = None) -> str:
    """Full-text search of the user's own local library (page-cited). Needs a configured knowledge folder."""
    if not config.load().knowledge_dir:
        return "No local library configured — add your own books with `astro add-book` (see docs/ADD-A-BOOK.md)."
    return _run_skill_script("search.py", query[:300], *(["--src", sources] if sources else []))


def rule_sources(rule: str) -> str:
    """Which books support or dispute a rule (knowledge graph), with pages and tiers."""
    if not config.load().knowledge_dir:
        return "No knowledge graph configured — retrieval is unavailable; reason from the skill's references."
    return _run_skill_script("kg.py", "sources", rule[:300])


def skill_file(rel: str) -> str:
    """Read one file of the skill (SKILL.md, references/*.md, assets/report/*) — nothing outside the skill folder."""
    s = config.load()
    path = _inside(os.path.join(s.skill_dir, rel), s.skill_dir)
    if not re.search(r"\.(md|json|css|j2)$", path):
        raise PermissionError("only skill documents can be read")
    return open(path, encoding="utf-8").read()


def analyze_question(question: str) -> dict:
    q = question.lower()
    topics = [t for t, rx in TOPICS.items() if re.search(rx, q)]
    timing = bool(re.search(r"\bwhen\b|next \d+|this year|next year|soon|month|period|dasha|timing", q))
    return {"question": question, "topics": topics or ["open activation — see question-trees.md §8"],
            "timing_question": timing, "load": ["SKILL.md", "references/consultation-reasoning.md",
                                                "references/question-trees.md", "references/communication.md"]
            + [f"references/topic-{t}.md" for t in topics] + (["references/timing.md"] if timing else [])}


def consultation_context(question: str, b: BirthInput, o: Options = DEFAULTS) -> dict:
    """Everything an AI client needs to answer like the skill: the routed method files, the calculated facts with
    provenance, and the birth-time sensitivity classes. The client does the reasoning."""
    c = calculate_chart(b, o)
    on = c["meta"]["transit_date"]
    running = next(([md["lord"], ad["lord"], pd["lord"]] for md in c["vimshottari"] for ad in md["sub"]
                    for pd in ad["sub"] if pd["start"] <= on < pd["end"]), None)
    facts = {"meta": c["meta"], "bodies": {k: {x: v[x] for x in ("sign", "deg", "nakshatra", "pada", "retro")}
                                           for k, v in c["bodies"].items()},
             "d9": {k: v["vargas"]["D9"] for k, v in c["bodies"].items()},
             "d10": {k: v["vargas"]["D10"] for k, v in c["bodies"].items()},
             "running_periods": running, "transits": c["transits"], "slow_contacts": c["slow_contacts"],
             "ingresses": c["ingresses"],
             "shadbala_rupas": {p: v["total_rupas"] for p, v in c["shadbala"]["planets"].items()},
             "sav_by_house": c["ashtakavarga"]["sav_by_house"], "jaimini": {k: c["jaimini"][k] for k in
                                                                             ("arudha_lagna", "upapada", "karakamsa")},
             "sensitivity_classes": c["sensitivity_grid"]["classes"]}
    return {"analysis": analyze_question(question), "facts": facts,
            "instructions": "Follow the loaded skill files: answer life-first (communication.md §1a), grade "
                            "evidence, keep systems separate, never invent positions or dates beyond these facts, "
                            "and treat 'high'/'very high' sensitivity factors as uncertain."}


def create_report(model: dict, name: str = "report") -> dict:
    """Validate and render a Structured Report Model (assets/report/report.schema.json) to HTML (+PDF)."""
    s = config.load()
    if not SAFE_NAME.match(name):
        raise ValueError("report name: letters, digits, dot, dash, underscore; ≤ 64 characters")
    spec = importlib.util.spec_from_file_location("render_report", os.path.join(s.skill_dir, "scripts", "render_report.py"))
    rr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr)
    schema = json.load(open(os.path.join(s.skill_dir, "assets", "report", "report.schema.json")))
    errs = rr.validate(model, schema)
    if not errs:
        e2, warns = rr.checks(model)
        errs += e2
    else:
        warns = []
    if errs:
        return {"ok": False, "errors": errs}
    os.makedirs(s.reports_dir, mode=0o700, exist_ok=True)      # reports hold birth details: owner-only when created
    html, pdf = rr.render(model, s.reports_dir, name)
    return {"ok": True, "warnings": warns, "html": html, "pdf": pdf}


def _inside(path, root):
    """Resolve `path` and refuse anything outside `root` (no traversal, no symlink escapes)."""
    if not root:
        raise FileNotFoundError("folder not configured (astro setup)")
    rp, rr = os.path.realpath(path), os.path.realpath(root)
    if os.path.commonpath([rp, rr]) != rr:
        raise PermissionError(f"path outside the allowed folder: {root}")
    return rp
