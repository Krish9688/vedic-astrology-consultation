# Run the validation/ scripts from a clean checkout. They hard-code the owner's workspace layout (WS = parent of
# validation/: astrology-prediction/, graphify-out/graph.json, index/library.sqlite, the book PDFs), so each runs in a
# throw-away workspace built from symlinks + the decompressed graph and is skipped, naming the input, if one is missing.
# The public edition has only knowledge/catalog.json, so everything here skips cleanly there.
import gzip
import json
import os
import shutil
import sqlite3
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAL = os.path.join(ROOT, "validation")
GZ = os.path.join(ROOT, "knowledge", "graph", "graph.json.gz")
CAT = os.path.join(ROOT, "knowledge", "catalog.json")
SKILL = os.environ.get("ASTRO_SKILL_DIR", "")
LIBDB = os.environ.get("ASTRO_LIBRARY_DB", "")      # the owner's full-text index (not in the repository)


def need(path, what):
    if not path or not os.path.exists(path):
        pytest.skip(f"missing input: {what} ({path or 'unset'})")


def workspace(tmp_path, script, graph=None, db=None):
    """A WS directory laid out as the script expects; `graph` is a dict (written as graph.json) or None for the real
    compressed graph, `db` a sqlite path copied to index/library.sqlite."""
    need(os.path.join(VAL, script), f"validation/{script}")
    need(os.path.join(SKILL, "scripts", "kg.py"), "skill scripts/kg.py (ASTRO_SKILL_DIR)")
    ws = tmp_path / "ws"
    (ws / "validation" / "sourcemaps").mkdir(parents=True)
    (ws / "graphify-out").mkdir()
    shutil.copy(os.path.join(VAL, script), ws / "validation" / script)
    os.symlink(SKILL, ws / "astrology-prediction")
    os.symlink(os.path.join(ROOT, "knowledge"), ws / "knowledge")
    with open(ws / "graphify-out" / "graph.json", "wb") as f:
        if graph is None:
            with gzip.open(GZ, "rb") as g:
                shutil.copyfileobj(g, f)
        else:
            f.write(json.dumps(graph).encode())
    if db:
        (ws / "index").mkdir()
        shutil.copy(db, ws / "index" / "library.sqlite")
    return ws


def run(ws, script, *args):
    env = {**os.environ, "ASTRO_KG": str(ws / "graphify-out" / "graph.json"), "ASTRO_LIBRARY_DB": str(ws / "index" / "library.sqlite")}
    return subprocess.run([sys.executable, str(ws / "validation" / script), *args], cwd=ws, env=env,
                          capture_output=True, text=True, timeout=600)


def tiny_world(tmp_path, page_text):
    """One synthetic rule citing one page; the page index holds `page_text` for that page."""
    graph = {"nodes": [
        {"id": "rule:T:1", "label": "r", "node_type": "Rule", "attributes": {"source": "T", "text": "Saturn in the seventh house delays marriage considerably"}},
        {"id": "planet:Sa", "label": "Saturn", "node_type": "Entity"},
        {"id": "page:T:5", "label": "T p5", "node_type": "Page", "attributes": {"book": "T", "pdf_page": 5}}],
        "links": [{"source": "rule:T:1", "target": "planet:Sa", "relation": "APPLIES_TO"},
                  {"source": "rule:T:1", "target": "page:T:5", "relation": "RULE_FROM"}]}
    db = tmp_path / "lib.sqlite"
    con = sqlite3.connect(db)
    con.execute("create virtual table pages using fts5(src, page, text)")
    con.execute("insert into pages values ('T', 5, ?)", (page_text,))
    con.commit()
    con.close()
    return graph, str(db)


def test_citation_check_passes_for_real_citation(tmp_path):
    graph, db = tiny_world(tmp_path, "Saturn in the seventh house delays marriage considerably, says the text.")
    ws = workspace(tmp_path, "citation_test.py", graph, db)
    r = run(ws, "citation_test.py", "T")
    assert r.returncode == 0 and "matching words 1/1" in r.stdout, r.stdout + r.stderr


def test_seeded_fake_citation_fails(tmp_path):
    # the rule cites a page whose text has nothing to do with it: the check must report 0 matching pages (0/1)
    graph, db = tiny_world(tmp_path, "Chapter on the lunar nodes and eclipses; nothing else appears here.")
    ws = workspace(tmp_path, "citation_test.py", graph, db)
    r = run(ws, "citation_test.py", "T")
    assert "matching words 0/1" in r.stdout, r.stdout + r.stderr


def test_graph_checks(tmp_path):
    need(GZ, "knowledge/graph/graph.json.gz")
    need(CAT, "knowledge/catalog.json")
    root = json.load(open(CAT, encoding="utf-8")).get("library_root")
    need(root, "library_root in knowledge/catalog.json = the owner's book PDFs (graph_checks hashes every PDF)")
    r = run(workspace(tmp_path, "graph_checks.py"), "graph_checks.py")
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-1000:]


def test_retrieval_eval(tmp_path):
    need(GZ, "knowledge/graph/graph.json.gz")
    need(LIBDB, "full-text index library.sqlite from the owner's book library (set ASTRO_LIBRARY_DB)")
    r = run(workspace(tmp_path, "retrieval_eval.py", db=LIBDB), "retrieval_eval.py")
    assert r.returncode == 0 and "Mean recall" in r.stdout, r.stdout[-2000:] + r.stderr[-1000:]
