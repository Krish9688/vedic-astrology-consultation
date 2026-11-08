# The project map and its single-file viewer, on a small invented tree (no books, no private data).
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "kg"))
import graph_view  # noqa: E402
import project_graph as PG  # noqa: E402


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tree(root):
    write(root, "plugin/.claude-plugin/plugin.json", '{"version": "9.9.9"}')
    write(root, "astro/__init__.py", "")
    write(root, "astro/calc.py", '"""Sums things."""\nimport swisseph\ndef total(): ...\n')
    write(root, "astro/service.py", "from astro.calc import total\nfrom astro import calc\n")
    write(root, "astro/mcp_server.py", 'from astro.service import total\n@tool("x")\ndef chart(): ...\n')
    write(root, "astro/cli.py", 'for name in ("doctor", "sky"):\n    sub.add_parser(name)\nsub.add_parser("serve")\n')
    write(root, "tests/test_calc.py", 'from astro.calc import total\nPATH = "astro/service.py"\n')
    write(root, "docs/GUIDE.md", "# Guide\nSee [other](OTHER.md), `astro/service.py` and [gone](MISSING.md).\n")
    write(root, "docs/OTHER.md", "# Other\n")
    write(root, "astrology-prediction/SKILL.md", "# Skill\n")
    write(root, "repo-root/pyproject.toml", '[project]\nname = "x"\ndependencies = ["pyswisseph>=2"]\n')
    write(root, "private/person/chart.py", "import secret_module\n")     # must never be walked
    write(root, "text/BOOK.jsonl", '{"text": "book"}\n')                # not one of the workspace source folders


def edges(g):
    return {(e["source"], e["target"], e["relation"]) for e in g["links"]}


def test_scan_finds_structure(tmp_path):
    tree(tmp_path)
    g, p = PG.generate(tmp_path, tmp_path / "out", "workspace")
    e = edges(g)
    assert ("file:astro/service.py", "file:astro/calc.py", "IMPORTS") in e
    assert ("file:tests/test_calc.py", "file:astro/calc.py", "TESTS") in e
    assert ("file:tests/test_calc.py", "file:astro/service.py", "USES") in e          # a path in a string is only a name match
    assert ("file:astro/calc.py", "pkg:pyswisseph", "DEPENDS_ON") in e
    assert ("file:repo-root/pyproject.toml", "pkg:pyswisseph", "DECLARES") in e
    assert ("file:docs/GUIDE.md", "file:docs/OTHER.md", "LINKS_TO") in e
    assert ("file:docs/GUIDE.md", "file:astro/service.py", "REFERENCES") in e
    assert ("file:astro/mcp_server.py", "mcp:chart", "EXPOSES") in e
    assert {("file:astro/cli.py", f"cli:{c}", "EXPOSES") for c in ("doctor", "sky", "serve")} <= e
    assert g["graph"]["release"] == "9.9.9"
    assert p.broken == ["docs/GUIDE.md -> MISSING.md"]


def test_private_folders_and_book_text_stay_out(tmp_path):
    tree(tmp_path)
    PG.generate(tmp_path, tmp_path / "out", "workspace")
    written = (tmp_path / "out" / "project.json").read_text(encoding="utf-8") + (tmp_path / "out" / "project.html").read_text(encoding="utf-8")
    assert "secret_module" not in written and "chart.py" not in written and "BOOK.jsonl" not in written


def test_repeat_scan_is_identical_and_check_notices_change(tmp_path):
    tree(tmp_path)
    PG.generate(tmp_path, tmp_path / "out", "workspace")
    first = (tmp_path / "out" / "project.json").read_bytes()
    PG.generate(tmp_path, tmp_path / "out", "workspace")
    assert first == (tmp_path / "out" / "project.json").read_bytes()
    write(tmp_path, "astro/new_module.py", "")
    fresh = PG.dumps(PG.to_node_link(PG.build(str(tmp_path), "workspace", str(tmp_path / "out")), "workspace", "9.9.9"))
    assert fresh.encode() != first


def test_public_layout_maps_to_the_same_areas(tmp_path):
    write(tmp_path, "plugins/astrology-consultation/.claude-plugin/plugin.json", '{"version": "1.0.0"}')
    write(tmp_path, ".git", "gitdir: elsewhere\n")                    # a linked worktree
    write(tmp_path, "docs/project-graph/cache/last_query_stamp", "1")   # left by graphify query commands
    write(tmp_path, "plugins/astrology-consultation/engine/astro/calc.py", "")
    write(tmp_path, "plugins/astrology-consultation/engine/astro/service.py", "from astro import calc\n")
    write(tmp_path, "plugins/astrology-consultation/skills/astrology-consultation/SKILL.md", "# Skill\n")
    g, _ = PG.generate(tmp_path, tmp_path / "docs" / "project-graph")
    assert g["graph"]["edition"] == "public"
    assert not [n["id"] for n in g["nodes"] if n["id"] == "file:.git" or "last_query_stamp" in n["id"]]
    by = {n["id"]: n for n in g["nodes"]}
    assert by["file:plugins/astrology-consultation/engine/astro/calc.py"]["attributes"]["area"] == "Engine"
    assert by["file:plugins/astrology-consultation/skills/astrology-consultation/SKILL.md"]["attributes"]["area"] == "Skill"
    assert ("file:plugins/astrology-consultation/engine/astro/service.py", "file:plugins/astrology-consultation/engine/astro/calc.py", "IMPORTS") in edges(g)


def test_viewer_is_self_contained():
    page = open(graph_view.TEMPLATE, encoding="utf-8").read()
    assert not re.search(r"""(?:src|href)=["']https?:|@import|url\(["']?https?:""", page)
    assert "/*GRAPH_DATA*/null" in page


def test_page_data_cannot_close_its_script_tag(tmp_path):
    g = {"graph": {"edition": "public", "release": "1"}, "links": [],
         "nodes": [{"id": "file:a.md", "label": "</script><b>", "node_type": "Doc", "source_file": "a.md", "source_location": "",
                    "attributes": {"kind": "doc"}}]}
    out = tmp_path / "x.html"
    graph_view.write_html(graph_view.project_view(g), str(out))
    html = out.read_text(encoding="utf-8")
    data = html.split('id="graph-data">')[1].split("</script>")[0]
    assert json.loads(data)["nodes"][0][1] == "</script><b>" and "<" not in data


def test_knowledge_view_withholds_birth_details():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from privacy_check import records
    sample = "[AB] Example chart: born " + "on 1 May 2000 at 10:30"       # invented; split so this file holds no record
    assert records(sample)
    g = {"nodes": [{"id": "book:AB", "label": "B", "node_type": "Book", "attributes": {"source_id": "AB", "system": "Parashari"}},
                   {"id": "rule:AB:1", "label": sample, "node_type": "Rule", "attributes": {"source": "AB", "section": "6. Examples", "tier": "modern"}}],
         "links": []}
    v = graph_view.knowledge_view(g, "1.0", None)
    assert not records(json.dumps(v))
    assert [n[1] for n in v["nodes"] if n[0] == "rule:AB:1"] == ["[AB] Worked example, birth details withheld"]


def test_viewer_data_has_colour_slots_and_line_patterns(tmp_path):
    for kinds, rels in ((graph_view.PROJECT_KINDS, graph_view.PROJECT_RELS), (graph_view.KNOWLEDGE_KINDS, graph_view.KNOWLEDGE_RELS)):
        assert all(-1 <= k["slot"] <= 5 for k in kinds)                       # six hues, -1 = neutral
        coloured = [k["slot"] for k in kinds if k["slot"] >= 0]
        assert len(set(coloured)) == len(coloured)
        assert all(r.get("dash", "") in ("", "6 4", "2 4") for r in rels)      # solid, dashed, dotted
    tree(tmp_path)
    write(tmp_path, "tests/fixtures/sample.json", "{}")                        # kind "data": shares the config colour
    g, _ = PG.generate(tmp_path, tmp_path / "out", "workspace")
    v = graph_view.project_view(g)
    assert {n[2] for n in v["nodes"]} <= {k["id"] for k in v["kinds"]}
    assert any(n[0] == "file:tests/fixtures/sample.json" and n[2] == "config" for n in v["nodes"])


def test_knowledge_view_folds_pages_and_keeps_rules():
    node = lambda i, t, **a: {"id": i, "label": i, "node_type": t, "attributes": a}  # noqa: E731
    g = {"nodes": [node("book:AB", "Book", source_id="AB", system="Parashari", author="A"), node("page:AB:1", "Page", book="AB"),
                   node("page:CD:2", "Page", book="CD"), node("book:CD", "Book", source_id="CD", system="Jaimini", author="B"),
                   node("rule:AB:1", "Rule", source="AB", section="3. Topic › x", tier="classical", pages=["AB p1"]), node("planet:sun", "Planet")],
         "links": [{"source": "page:AB:1", "target": "planet:sun", "relation": "MENTIONS"}, {"source": "page:AB:1", "target": "book:AB", "relation": "PART_OF"},
                   {"source": "rule:AB:1", "target": "page:AB:1", "relation": "RULE_FROM"}, {"source": "rule:AB:1", "target": "page:CD:2", "relation": "RULE_FROM"},
                   {"source": "rule:AB:1", "target": "planet:sun", "relation": "APPLIES_TO"}]}
    v = graph_view.knowledge_view(g, "1.0", None)
    ids = [n[0] for n in v["nodes"]]
    assert "rule:AB:1" in ids and not any(i.startswith("page:") for i in ids)
    sun = next(n for n in v["nodes"] if n[0] == "planet:sun")
    assert sun[5]["mentioned on"] == "1 book pages"
    names = [r["id"] for r in v["rels"]]
    triples = {(ids[v["edges"][i]], ids[v["edges"][i + 1]], names[v["edges"][i + 2]]) for i in range(0, len(v["edges"]), 3)}
    assert ("rule:AB:1", "planet:sun", "APPLIES_TO") in triples
    assert ("rule:AB:1", "book:CD", "CITES") in triples and ("rule:AB:1", "book:AB", "CITES") not in triples
