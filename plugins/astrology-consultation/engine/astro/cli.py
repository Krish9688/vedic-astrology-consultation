"""`astro` — command-line front end over astro.service. Birth data is read from a JSON file (not typed on the command
line, so it stays out of shell history):  {"date": "1992-03-14", "time": "09:40", "tz": 0, "lat": 51.5, "lon": -0.12}

  astro chart input.json [--md] [--out DIR]       astro sensitivity input.json [--md]
  astro dasha input.json [--on DATE] [--year 360] astro compare input.json [--vedastro-dir DIR | --live]
  astro varga input.json --d 9                    astro consult "Will my career change?" input.json
  astro transits input.json [--months 24]         astro report model.json [--name NAME]
  astro strength input.json                       astro sources "rule" | astro search "words"
  astro jaimini input.json                        astro predict add|list|evaluate|score ...
  astro doctor | astro setup | astro add-book PDF | astro mcp [--http] | astro serve
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys

from . import config, predictions, service as S

# Swiss Ephemeris 1800–2399 CE files, pinned to the versions benchmarked for v3.5 (docs/CALCULATION-ENGINES.md)
EPHE_SHA256 = {"sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
               "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7"}


def _birth(path):
    with open(path) as f:
        return S.BirthInput(**json.load(f))


def _opts(a):
    return S.Options(on=a.on, months=getattr(a, "months", 24), year=getattr(a, "year", "sidereal"))


def _print(obj, md_key=None, md=False):
    if md and md_key and isinstance(obj, dict) and md_key in obj:
        print(obj[md_key])
    elif isinstance(obj, str):
        print(obj)
    else:
        print(json.dumps(obj, indent=1, ensure_ascii=False, default=str))


def doctor():
    """Health check. PASS = working; WARN = works but should be fixed; FAIL = core broken (exit 1);
    OPTIONAL = an optional component is not installed."""
    s = config.load()
    rows = []
    add = lambda level, name, detail="": rows.append((level, name, detail))
    add("PASS" if sys.version_info >= (3, 11) else "FAIL", "Python ≥ 3.11", sys.version.split()[0])
    add("PASS" if shutil.which("uv") else "WARN", "uv", "found" if shutil.which("uv") else "needed only for install.sh")
    venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    add("PASS" if venv else "WARN", "isolated environment", sys.prefix if venv else "not a virtual environment")
    try:
        from .calc import engine
        c = engine.compute("1992-03-14", "09:40", 0, 51.5, -0.12, on="2026-01-01", extras=False)
        add("PASS" if c["bodies"]["Asc"]["sign"] == "Taurus" else "FAIL", "calculation engine",
            f"test chart computed ({c['meta']['engine']})")
        if engine.EPHE_DIR:
            bad = [f for f, sha in EPHE_SHA256.items()
                   if hashlib.sha256(open(os.path.join(engine.EPHE_DIR, f), "rb").read()).hexdigest() != sha]
            add("FAIL" if bad else "PASS", "Swiss Ephemeris files and checksums",
                f"checksum mismatch: {', '.join(bad)} — re-run `astro setup --ephemeris`" if bad else engine.EPHE_DIR)
        else:
            add("WARN", "Swiss Ephemeris files", "absent: Moshier fallback (≈1–3″); `astro setup --ephemeris`")
    except Exception as e:  # noqa: BLE001
        add("FAIL", "calculation engine", f"{type(e).__name__}: {e}")
    for mods, name in ((("mcp",), "MCP server"), (("fastapi", "uvicorn"), "REST API"), (("jinja2",), "report HTML"),
                       (("weasyprint",), "report PDF (needs Pango)")):
        try:
            for m in mods:
                __import__(m)
            add("PASS", name)
        except Exception:  # noqa: BLE001
            add("OPTIONAL", name, f"pip install {' '.join(mods)}")
    has = lambda *p: bool(s.knowledge_dir) and os.path.exists(os.path.join(s.knowledge_dir, *p))
    add("PASS" if s.skill_dir else "WARN", "skill folder", s.skill_dir or "not found — `astro setup --skill-dir`")
    add("PASS" if has("index", "library.sqlite") else "OPTIONAL", "book index (your own books)",
        "" if has("index", "library.sqlite") else "`astro add-book`")
    add("PASS" if has("graphify-out", "graph.json") else "OPTIONAL", "knowledge graph")
    graphify = os.path.exists(os.path.join(config.PROJECT, ".venv-graphify"))
    add("PASS" if graphify else "OPTIONAL", "Graphify (only to rebuild the graph)")
    books = s.books_dir and os.path.isdir(s.books_dir)
    add("PASS" if books else "OPTIONAL", "books folder",
        f"{sum(f.lower().endswith('.pdf') for f in os.listdir(s.books_dir))} PDFs" if books else "not configured")
    add("PASS", f"privacy mode: {s.mode}", "external calculation allowed" if s.external_allowed else "fully local")
    if s.allow_remote and not s.api_token:
        add("WARN", "remote access", "allow_remote is set but no api_token — servers will refuse to listen remotely")
    for path, want, name in ((config.CONFIG_PATH, 0o600, "config file permissions"),
                             (s.data_dir, 0o700, "data folder permissions"),
                             (os.path.join(s.data_dir, "predictions.sqlite"), 0o600, "prediction log permissions")):
        if os.path.exists(path):
            mode = os.stat(path).st_mode & 0o777
            add("PASS" if mode & ~want == 0 else "WARN", name, f"{oct(mode)} (want {oct(want)} or stricter)")
    vedastro = os.path.exists(s.vedastro_server) and shutil.which("node")
    add("PASS" if vedastro else "OPTIONAL", "VedAstro cross-check", "used only in hybrid mode")
    for level, name, detail in rows:
        print(f"{level:<8} {name}" + (f" — {detail}" if detail else ""))
    return 1 if any(r[0] == "FAIL" for r in rows) else 0


def setup(a):
    s = config.load()
    if a.mode:
        s.mode = a.mode
    for k in ("skill_dir", "knowledge_dir", "books_dir", "reports_dir"):
        v = getattr(a, k)
        if v:
            setattr(s, k, os.path.abspath(os.path.expanduser(v)))
    path = config.write(s)
    print(f"settings → {path} (mode {s.mode})")
    if a.ephemeris:
        d = os.path.expanduser("~/.local/share/astrology-consultation/ephe")
        os.makedirs(s.data_dir, mode=0o700, exist_ok=True)
        os.chmod(s.data_dir, 0o700)                       # private: also holds the prediction log
        os.makedirs(d, exist_ok=True)
        base = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/"
        for f, sha in EPHE_SHA256.items():
            path = os.path.join(d, f)
            subprocess.run(["curl", "-fsSL", "-o", path, base + f], check=True)
            if hashlib.sha256(open(path, "rb").read()).hexdigest() != sha:
                os.remove(path)
                raise SystemExit(f"{f}: checksum mismatch — file removed; the engine keeps using its built-in fallback")
        print(f"Swiss Ephemeris files → {d} (source: github.com/aloistr/swisseph, official)")
    print("MCP client config examples: docs/CLIENT-INTEGRATIONS.md")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="astro", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("chart", "positions", "dasha", "transits", "strength", "jaimini", "sensitivity", "compare", "varga"):
        p = sub.add_parser(name)
        p.add_argument("input")
        p.add_argument("--on", type=dt.date.fromisoformat)
        p.add_argument("--months", type=int, default=24)
        p.add_argument("--year", default="sidereal", choices=["sidereal", "365.25", "360"])
        p.add_argument("--md", action="store_true")
        if name == "chart":
            p.add_argument("--out")
        if name == "varga":
            p.add_argument("--d", type=int, required=True)
        if name == "compare":
            p.add_argument("--vedastro-dir")
            p.add_argument("--live", action="store_true")
    p = sub.add_parser("consult")
    p.add_argument("question")
    p.add_argument("input")
    p.add_argument("--on", type=dt.date.fromisoformat)
    p = sub.add_parser("report")
    p.add_argument("model")
    p.add_argument("--name", default="report")
    sub.add_parser("sources").add_argument("rule")
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--src")
    p = sub.add_parser("predict")
    p.add_argument("action", choices=["add", "list", "evaluate", "score"])
    p.add_argument("--chart-id")
    p.add_argument("--category")
    p.add_argument("--text")
    p.add_argument("--window", nargs=2, metavar=("YYYY-MM", "YYYY-MM"))
    p.add_argument("--confidence", default="Moderate")
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--consent", action="store_true", help="the person agreed to having this prediction logged")
    p.add_argument("--id", type=int)
    p.add_argument("--outcome")
    p.add_argument("--evaluation")
    sub.add_parser("doctor")
    p = sub.add_parser("setup")
    p.add_argument("--mode", choices=["private", "hybrid", "research"])
    for k in ("skill-dir", "knowledge-dir", "books-dir", "reports-dir"):
        p.add_argument("--" + k)
    p.add_argument("--ephemeris", action="store_true", help="download the Swiss Ephemeris data files (≈1.8 MB)")
    p = sub.add_parser("add-book")
    p.add_argument("pdf")
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p = sub.add_parser("mcp")
    p.add_argument("--http", action="store_true")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p = sub.add_parser("serve")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8766)
    a = ap.parse_args(argv)

    if a.cmd == "doctor":
        return doctor()
    if a.cmd == "setup":
        return setup(a)
    if a.cmd == "mcp":
        from .mcp_server import main as run
        return run(http=a.http, host=a.host, port=a.port)
    if a.cmd == "serve":
        from .rest import main as run
        return run(host=a.host, port=a.port)
    if a.cmd == "consult":
        return _print(S.consultation_context(a.question, _birth(a.input), S.Options(on=a.on)))
    if a.cmd == "report":
        with open(a.model) as f:
            return _print(S.create_report(json.load(f), a.name))
    if a.cmd == "sources":
        return _print(S.rule_sources(a.rule))
    if a.cmd == "search":
        return _print(S.search_sources(a.query, a.src))
    if a.cmd == "add-book":
        tool = os.path.join(config.PROJECT, "tools", "kg", "add_book.py")
        if not os.path.exists(tool):
            raise FileNotFoundError("adding books needs the full repository (book ingestion, index and graph tools): "
                                    "clone it and run `astro add-book` from there — see docs/ADD-A-BOOK.md")
        return subprocess.call([sys.executable, tool, "register", a.pdf, "--id", a.id, "--title", a.title,
                                "--author", a.author, "--language", "English", "--system", "Parashari",
                                "--tier", "modern"])
    if a.cmd == "predict":
        if a.action == "add":
            pid = predictions.add(a.chart_id, a.category, a.text, *(a.window or (None, None)),
                                  confidence=a.confidence, synthetic=a.synthetic, consent=a.consent,
                                  skill_version=S.VERSION)
            return print(f"recorded prediction {pid}")
        if a.action == "evaluate":
            return predictions.evaluate(a.id, a.outcome, a.evaluation)
        return _print(predictions.rows() if a.action == "list" else predictions.scorecard())
    b = _birth(a.input)
    o = _opts(a)
    if a.cmd == "chart":
        c = S.calculate_chart(b, o)
        if a.out:
            from .calc import engine
            engine.write_outputs(c, a.out)
            return print(f"wrote {a.out}/calc.json, chart.json, calc.md")
        if a.md:
            from .calc import engine
            return print(engine.render_md(c))
        return _print(c)
    fn = {"positions": lambda: S.planet_positions(b), "dasha": lambda: S.dasha(b, o),
          "transits": lambda: S.transits(b, o), "strength": lambda: {"shadbala": S.shadbala(b),
                                                                     "ashtakavarga": S.ashtakavarga(b)},
          "jaimini": lambda: S.jaimini_factors(b), "sensitivity": lambda: S.birth_time_sensitivity(b, o),
          "varga": lambda: S.divisional_chart(b, a.d),
          "compare": lambda: S.compare_engines(b, a.vedastro_dir, a.live)}[a.cmd]
    return _print(fn(), md_key="table_markdown", md=a.md)


def entry():
    """Console-script entry: refusals and bad input print one line instead of a traceback."""
    try:
        return main() or 0
    except (ValueError, PermissionError, FileNotFoundError) as e:
        print(f"astro: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(entry())
