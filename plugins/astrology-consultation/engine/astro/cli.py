"""`astro` — command-line front end over astro.service. Birth data is read from a JSON file (not typed on the command
line, so it stays out of shell history):  {"date": "1992-03-14", "time": "09:40", "tz": 0, "lat": 51.5, "lon": -0.12}

  astro chart input.json [--md] [--out DIR]       astro sensitivity input.json [--md]
  astro dasha input.json [--on DATE] [--year 360]
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
import time
import urllib.request

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
    add("PASS", f"privacy mode: {s.mode}", "fully local calculation")
    if s.allow_remote and not s.api_token:
        add("WARN", "remote access", "allow_remote is set but no api_token — servers will refuse to listen remotely")
    for path, want, name in ((config.CONFIG_PATH, 0o600, "config file permissions"),
                             (s.data_dir, 0o700, "data folder permissions"),
                             (os.path.join(s.data_dir, "predictions.sqlite"), 0o600, "prediction log permissions"),
                             (s.reports_dir, 0o700, "reports folder permissions")):
        if os.path.exists(path):
            mode = os.stat(path).st_mode & 0o777
            add("PASS" if mode & ~want == 0 else "WARN", name, f"{oct(mode)} (want {oct(want)} or stricter)")
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
            path, part = os.path.join(d, f), os.path.join(d, f + ".part")   # verified, then moved: never a truncated file
            try:
                urllib.request.urlretrieve(base + f, part)
                ok = hashlib.sha256(open(part, "rb").read()).hexdigest() == sha
            except OSError as e:
                ok, why = False, f"download failed ({e})"
            else:
                why = "checksum mismatch"
            if not ok:
                if os.path.exists(part):
                    os.remove(part)
                raise SystemExit(f"{f}: {why} — nothing installed; the engine keeps using its built-in fallback")
            os.replace(part, path)
        print(f"Swiss Ephemeris files → {d} (source: github.com/aloistr/swisseph, official)")
    if getattr(a, "places", False):
        from . import places
        print(f"place gazetteer → {places.install(s.data_dir)} ({places.SOURCE})")
    print("MCP client config examples: docs/CLIENT-INTEGRATIONS.md")


def purge(days, delete):
    """Reports (.html/.pdf in reports_dir) and prediction rows older than `days`; lists them unless delete is set."""
    if days < 0:
        raise ValueError("--older-than must be 0 or more days")
    s, cutoff = config.load(), time.time() - days * 86400
    old = sorted(e.path for e in (os.scandir(s.reports_dir) if os.path.isdir(s.reports_dir) else ())
                 if e.is_file() and e.name.endswith((".html", ".pdf")) and e.stat().st_mtime < cutoff)
    for f in old:
        print(("deleted " if delete else "would delete ") + f)
        if delete:
            os.remove(f)
    db = os.path.join(s.data_dir, "predictions.sqlite")
    n = predictions.purge(days, delete, db) if os.path.exists(db) else 0
    print(f"{'deleted' if delete else 'would delete'} {len(old)} report file(s) and {n} prediction row(s)"
          + ("" if delete else "; run again with --yes to delete"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="astro", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=S.SOURCE_NOTICE + f" Source: {S.SOURCE_URL}. Uses {S.THIRD_PARTY}.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("chart", "positions", "dasha", "yogini", "gochara", "outlook", "tajika", "transits", "strength",
                 "jaimini", "sensitivity", "varga"):
        p = sub.add_parser(name)
        p.add_argument("input")
        p.add_argument("--on", type=dt.date.fromisoformat)
        p.add_argument("--months", type=int, default=24)
        p.add_argument("--year", default="sidereal", choices=["sidereal", "365.25", "360"])
        p.add_argument("--md", action="store_true")
        if name == "outlook":
            p.add_argument("--period", choices=["day", "week", "month", "year"], default="month")
        if name == "tajika":
            p.add_argument("--life-year", type=int, help="year of life N (default: the year running on --on)")
        if name == "chart":
            p.add_argument("--out")
        if name == "sensitivity":
            p.add_argument("--span", type=int, default=15, help="minutes either side (15..720)")
        if name == "varga":
            p.add_argument("--d", type=int, required=True)
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
    p = sub.add_parser("sky", help="retrograde stations and sign changes between two dates (no birth data)")
    p.add_argument("start", type=dt.date.fromisoformat)
    p.add_argument("end", type=dt.date.fromisoformat)
    p.add_argument("--tz", default="+00:00", help="UTC offset for the printed dates, e.g. +05:30")
    sub.add_parser("doctor")
    p = sub.add_parser("purge", help="delete reports and prediction-log rows older than N days (dry run without --yes)")
    p.add_argument("--older-than", type=int, required=True, metavar="DAYS")
    p.add_argument("--yes", action="store_true", help="really delete")
    p = sub.add_parser("setup")
    p.add_argument("--mode", choices=["private", "research"])
    for k in ("skill-dir", "knowledge-dir", "books-dir", "reports-dir"):
        p.add_argument("--" + k)
    p.add_argument("--ephemeris", action="store_true", help="download the Swiss Ephemeris data files (≈1.8 MB)")
    p.add_argument("--places", action="store_true", help="download the GeoNames place gazetteer (≈7 MB, CC-BY 4.0) "
                   "for offline birthplace lookup")
    p = sub.add_parser("panchang", help="panchang of a local day (no birth data)")
    p.add_argument("date", type=dt.date.fromisoformat)
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--tz", help="UTC offset, e.g. +05:30")
    p.add_argument("--zone", help="IANA time zone, e.g. Asia/Kolkata")
    p = sub.add_parser("place", help="birthplace → coordinates and IANA time zone (offline)")
    p.add_argument("name")
    p.add_argument("--country", help="two-letter country code, e.g. IN")
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
    if a.cmd == "purge":
        return purge(a.older_than, a.yes)
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
    if a.cmd == "sky":
        return _print(S.sky(a.start, a.end, a.tz))
    if a.cmd == "panchang":
        return _print(S.panchang(a.date, a.lat, a.lon, a.tz, a.zone))
    if a.cmd == "place":
        return _print(S.find_place(a.name, a.country))
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
        return _print(predictions.rows() if a.action == "list" else predictions.scorecard(include_synthetic=a.synthetic))
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
          "yogini": lambda: S.yogini_dasha(b, o), "gochara": lambda: S.gochara(b, o),
          "outlook": lambda: S.outlook(b, getattr(a, "period", "month") or "month", a.on, o),
          "tajika": lambda: S.tajika(b, a.life_year, o),
          "transits": lambda: S.transits(b, o), "strength": lambda: {"shadbala": S.shadbala(b),
                                                                     "ashtakavarga": S.ashtakavarga(b)},
          "jaimini": lambda: S.jaimini_factors(b), "sensitivity": lambda: S.birth_time_sensitivity(b, o, a.span),
          "varga": lambda: S.divisional_chart(b, a.d)}[a.cmd]
    return _print(fn(), md_key="table_markdown", md=a.md)


def entry():
    """Console-script entry: refusals and bad input print one line instead of a traceback."""
    try:
        return main() or 0
    except (ValueError, PermissionError, FileNotFoundError, KeyError) as e:
        print(f"astro: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(entry())
