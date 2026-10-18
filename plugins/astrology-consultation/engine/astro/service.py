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

VERSION = "3.6.3"
SOURCE_URL = "https://github.com/Krish9688/vedic-astrology-consultation"
SOURCE_NOTICE = ("This service is free software under the GNU Affero General Public License v3 or later, with NO "
                 "WARRANTY. The Corresponding Source of the version running here is available at the 'source' URL. "
                 "If you run a modified version for other people over a network, set source_url in the config to "
                 "your modified source (AGPL-3.0 section 13).")
THIRD_PARTY = "Swiss Ephemeris © Astrodienst AG (AGPL-3.0); pyswisseph"
REMOTE = False   # set by the HTTP servers when they listen beyond localhost
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
TOPICS = {  # question → the skill's topic reference (SKILL.md routing table); word starts, so "remove" ≠ "move"
    "relationships-marriage": r"\bmarr(?:y|ie|ia)|\bwed|\bspouse|\bwife|\bhusband|(?<!business )\bpartner|"
                              r"\brelationship|\blove\b|\bromance|\bdating|\bgirlfriend|\bboyfriend|\bmy ex\b|\bbreak ?up",
    "career-money": r"\bcareer|\bjob|\bwork|\bbusiness|\bpromotion|\bincome|\bmoney|\bfinanc|\bwealth|\bdebt|"
                    r"\bsalary|\bboss|\bcompany|\binvest",
    "home-family-children": r"\bhome|\bhouse\b|\bproperty|\bflat\b|\bapartment|\bmother|\bfather|\bparent|\bsibling|"
                            r"\bbrother|\bsister|\bchild|\bkids?\b|\bbab(?:y|ies)|\bpregnan|\bconceiv|\bson\b|"
                            r"\bdaughter|\bfamil|\bfriend",
    "travel-education-health-life": r"\babroad|\bforeign|\btravel|\brelocat|\bmov(?:e|ing)\b|\bstud(?:y|ies)|"
                                    r"\beducation|\bdegree|\buniversity|\bcollege|\bexam|\bschool|\bhealth|"
                                    r"\billness|\bill\b|\bsick|\bdisease|\bsurgery|\bwellbeing|\bspiritual|"
                                    r"\byear ahead|\bnext year|\b12 months",
}


class BirthInput(BaseModel):
    date: dt.date
    time: str = Field(pattern=r"^\d{1,2}:\d{2}(:\d{2})?$")
    tz: float = Field(ge=-14, le=14, description="UTC offset in hours at the birth moment (include daylight saving)")
    lat: float = Field(ge=-89.9, le=89.9, description="the ascendant is undefined at the poles")
    lon: float = Field(ge=-180, le=180)
    label: Optional[str] = Field(default=None, max_length=64)
    time_source: Optional[str] = Field(default=None, max_length=120)

    @field_validator("date")
    @classmethod
    def _range(cls, v):
        if not 2 <= v.year <= 2999:
            raise ValueError("dates must lie between the years 2 and 2999 (Moshier outside 1800-2399)")
        return v

    @field_validator("time")
    @classmethod
    def _clock(cls, v):
        h, m, *s = (int(x) for x in v.split(":"))
        if not (0 <= h < 24 and 0 <= m < 60 and all(0 <= x < 60 for x in s)):
            raise ValueError("time must be a valid 24-hour clock time")
        return f"{h:02d}:{m:02d}:{(s or [0])[0]:02d}"   # zero-padded: the engine parses ISO times (P1-5)


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


def source_offer(s=None) -> dict:
    """AGPL-3.0 section 13: where network users get the Corresponding Source."""
    s = s or config.load()
    return {"license": "AGPL-3.0-or-later", "source": s.source_url or f"{SOURCE_URL}/tree/v{VERSION}",
            "source_notice": SOURCE_NOTICE, "third_party": THIRD_PARTY}


def engine_info() -> dict:
    s = config.load()
    return {"service": "astrology-consultation", "version": VERSION, "engine": engine.ENGINE_VERSION,
            **source_offer(s),
            **engine.ephemeris_info(), "ayanamsa": "Lahiri (default)", "privacy_mode": s.mode,
            "knowledge_available": bool(s.knowledge_dir), "skill_available": bool(s.skill_dir),
            "vargas": engine.VARGA_METHODS, "shadbala_conventions": strength.SHADBALA_CONVENTIONS,
            "jaimini_conventions": jaimini.CONVENTIONS}


def calculate_chart(b: BirthInput, o: Options = DEFAULTS, full: bool = True) -> dict:
    a, kw = _args(b, o)
    c = compute_full(*a, **kw) if full else engine.compute(*a, **kw)
    c["meta"] |= {k: v for k, v in (("time_source", b.time_source), ("label", b.label)) if v}   # P1-5: never dropped
    return c


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


def sky(start, end, tz: float = 0.0, node: str = "mean") -> dict:
    """Retrograde stations and sign changes between two dates — no birth data (council 6, P2-1)."""
    a, b = dt.date.fromisoformat(str(start)), dt.date.fromisoformat(str(end))
    if not (a < b and (b - a).days <= 3 * 366 and -14 <= tz <= 14 and node in ("mean", "true")):
        raise ValueError("need start < end, at most 3 years apart, UTC offset -14..14, node mean or true")
    t0 = dt.datetime.combine(a, dt.time()) - dt.timedelta(hours=tz)
    t1 = dt.datetime.combine(b, dt.time(23, 59)) - dt.timedelta(hours=tz)
    return engine.sky(t0, t1, node, tz) | {"meta": {"from": a.isoformat(), "to": b.isoformat(), "utc_offset": tz,
        "nodes": node, "zodiac": "sidereal Lahiri", "engine": f"astro {engine.ENGINE_VERSION}",
        "note": "sky facts only: the same for everyone; they say nothing about a person without a chart"}}


def birth_time_sensitivity(b: BirthInput, o: Options = DEFAULTS, span_min: int = 15) -> dict:
    a, kw = _args(b, o)
    g = sensitivity.grid(*a, on=kw["on"], year=o.year, span_min=span_min)
    return g | {"table_markdown": sensitivity.render(g)}


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
    if r.returncode != 0:   # pass the script's own one-line message, never a traceback or a local path
        msg = r.stderr.strip()
        if not msg or "Traceback" in msg:
            msg = f"{name} failed (exit {r.returncode}); run it locally to see why"
        raise ValueError(re.sub(r"(?:~|/)[^\s'\"]*/[^\s'\"]*", "<path>", msg))
    return r.stdout.strip()


def _library_gate():
    """Excerpts of the user's own books are for the user: not served to other people over a network unless the owner
    explicitly opts in (share_library_remotely = true)."""
    if REMOTE and not config.load().share_library_remotely:
        raise PermissionError("library lookup is not served to remote clients (set share_library_remotely = true "
                              "only if you are entitled to share these excerpts)")


def search_sources(query: str, sources: Optional[str] = None) -> str:
    """Full-text search of the user's own local library (page-cited). Needs a configured knowledge folder."""
    _library_gate()
    if not config.load().knowledge_dir:
        return "No local library configured — add your own books with `astro add-book` (see docs/ADD-A-BOOK.md)."
    return _run_skill_script("search.py", *(["--src", sources] if sources else []), "--", query[:300])


def rule_sources(rule: str) -> str:
    """Which books support or dispute a rule (knowledge graph), with pages and tiers."""
    _library_gate()
    if not config.load().knowledge_dir:
        return "No knowledge graph configured — retrieval is unavailable; reason from the skill's references."
    return _run_skill_script("kg.py", "sources", "--", rule[:300])


def skill_file(rel: str) -> str:
    """Read one file of the skill (SKILL.md, references/*.md, assets/report/*) — nothing outside the skill folder."""
    s = config.load()
    path = _inside(os.path.join(s.skill_dir, rel), s.skill_dir)
    if "/data/lal-kitab/" in path.replace(os.sep, "/").lower():   # book-derived KB: same rule as library excerpts (H-10); lower(): case-insensitive disks
        _library_gate()
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
             "sensitivity_classes": c["sensitivity_grid"]["classes"],
             "transit_sign_aspects": c["transit_sign_aspects"], "transit_aspects_note": c["meta"]["transit_aspects"]}
    return {"analysis": analyze_question(question), "facts": facts, "derived_facts": _derived_facts(c),
            "instructions": "Follow the loaded skill files: answer life-first (communication.md §1a), grade "
                            "evidence, keep systems separate, never invent positions or dates beyond these facts, "
                            "and treat 'high'/'very high' sensitivity factors as uncertain."}


def _derived_facts(c):
    """The skill's chart_facts.py output (houses, lordships, graha drishti, combustion, D9/D10, dispositors, PD XV tests,
    Lal Kitab flags) — one implementation, owned by the skill with its conventions named — so clients without a shell
    get the same derived facts."""
    path = os.path.join(config.load().skill_dir, "scripts", "chart_facts.py")
    if not os.path.exists(path):
        return "unavailable: the skill's scripts/chart_facts.py was not found"
    spec = importlib.util.spec_from_file_location("chart_facts", path)
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    return cf.facts(engine.chart_facts_input(c))


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
    try:
        html, pdf = rr.render(model, s.reports_dir, name)
    except Exception as e:   # e.g. jinja2 or the PDF libraries missing: tell the client why (not a generic tool error)
        return {"ok": False, "errors": [f"report could not be rendered: {type(e).__name__}: {e}"]}
    for f in (html, pdf):
        if f:
            os.chmod(f, 0o600)      # the files hold birth details too, not only the folder (council R4)
    return {"ok": True, "warnings": warns, "html": html, "pdf": pdf}


def _inside(path, root):
    """Resolve `path` and refuse anything outside `root` (no traversal, no symlink escapes)."""
    if not root:
        raise FileNotFoundError("folder not configured (astro setup)")
    rp, rr = os.path.realpath(path), os.path.realpath(root)
    if os.path.commonpath([rp, rr]) != rr:
        raise PermissionError("path outside the allowed folder")
    return rp
