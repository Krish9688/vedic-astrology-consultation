#!/usr/bin/env python3
"""Turn a node-link graph into the compact data the single-file viewer (tools/kg/viewer.html) draws, and write the page.
Standard library only. Two views: the project map (project_graph.py) and the knowledge graph (graphify-out/graph.json).

The knowledge view keeps every rule, concept, book, person, dispute and position. Page nodes and page-to-concept mentions
(about half of the edges) are folded into the rule and concept details, because a browser cannot usefully draw them.
usage: python3 tools/kg/graph_view.py knowledge [GRAPH.json] [OUT.html]
"""
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "viewer.html")
SWITCH_PROJECT = [{"label": "Project map", "href": "project.html", "here": True}, {"label": "Knowledge graph", "href": "graph.html"}]
SWITCH_KNOWLEDGE = [{"label": "Project map", "href": "project.html"}, {"label": "Knowledge graph", "href": "graph.html", "here": True}]
GROUP_NOTE = "shortcut: at most 400 tiles are drawn per folder, the rest stay in search and the outline"


def generator_sha():
    h = hashlib.sha256()
    for name in ("project_graph.py", "graph_view.py", "viewer.html"):
        with open(os.path.join(HERE, name), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:12]


class View:
    def __init__(self):
        self.groups = [["All", -1]]
        self.index = {}

    def group(self, key, label, parent=0):
        if key not in self.index:
            self.index[key] = len(self.groups)
            self.groups.append([label, parent, key])
        return self.index[key]


def pack(view, title, subtitle, kinds, rels, nodes, edges, note, switch, meta, legend):
    pos = {n[0]: i for i, n in enumerate(nodes)}
    rel_ix = {r["id"]: i for i, r in enumerate(rels)}
    flat = []
    for s, t, r in sorted(set(edges)):
        if s in pos and t in pos and r in rel_ix:
            flat += [pos[s], pos[t], rel_ix[r]]
    return {"title": title, "subtitle": subtitle, "kinds": kinds, "rels": rels, "groups": view.groups, "nodes": nodes, "edges": flat,
            "note": note, "switch": switch or [], "meta": meta, "legend": legend}


# ---------- project map ----------
# slot = colour in the viewer (six hues, validated for colour-blind separation); -1 = neutral
PROJECT_KINDS = [{"id": "module", "label": "Engine module", "slot": 0}, {"id": "script", "label": "Script or tool", "slot": 1}, {"id": "test", "label": "Test", "slot": 2},
                 {"id": "doc", "label": "Document", "slot": 3}, {"id": "config", "label": "Config and data", "slot": 4},
                 {"id": "interface", "label": "Interface", "slot": 5}, {"id": "package", "label": "External package", "slot": -1}]
PROJECT_LEGEND = [{"dash": "", "label": "read from code"}, {"dash": "6 4", "label": "test of"}, {"dash": "2 4", "label": "matched by name"}]
KNOWLEDGE_LEGEND = [{"dash": "", "label": "stated in a source"}, {"dash": "6 4", "label": "disputed"}, {"dash": "2 4", "label": "similar wording"}]
PROJECT_RELS = [{"id": "IMPORTS", "label": "imports", "inverse": "imported by"}, {"id": "TESTS", "label": "tests", "inverse": "tested by", "dash": "6 4"},
                {"id": "USES", "label": "uses file", "inverse": "used by", "dash": "2 4"}, {"id": "EXPOSES", "label": "exposes", "inverse": "exposed by"},
                {"id": "DEPENDS_ON", "label": "needs package", "inverse": "needed by"},
                {"id": "DECLARES", "label": "declares", "inverse": "declared in"},
                {"id": "LINKS_TO", "label": "links to", "inverse": "linked from"},
                {"id": "REFERENCES", "label": "mentions", "inverse": "mentioned in", "dash": "2 4"}]


def project_view(g, switch=None):
    v = View()
    by_id = {n["id"]: n for n in g["nodes"]}
    parent = {e["target"]: e["source"] for e in g["links"] if e["relation"] == "CONTAINS"}

    def group_of(nid):
        if nid is None or nid not in by_id:
            return 0
        n = by_id[nid]
        return v.group(nid, n["label"], group_of(parent.get(nid)))

    nodes = []
    for n in g["nodes"]:
        t = n["node_type"]
        if t in ("Area", "Folder"):
            group_of(n["id"])
            continue
        a = n["attributes"]
        if t == "Package":
            gid = v.group("area:external", "External packages")
            nodes.append([n["id"], n["label"], "package", gid, "", {}])
        elif t == "Interface" and "channel" in a:
            nodes.append([n["id"], n["label"], "interface", group_of(parent.get(n["id"])), a.get("channel", ""),
                          {"path": n["source_file"] + (":" + n["source_location"][1:] if n["source_location"] else "")}])
        else:
            d = {"path": n["source_file"]}
            for k in ("lines", "role", "summary"):
                if a.get(k):
                    d[k] = a[k]
            if a.get("defs"):
                d["defines"] = a["defs"]
            kind = "config" if a["kind"] in ("config", "data") else a["kind"]
            nodes.append([n["id"], n["label"], kind, group_of(parent.get(n["id"])), a.get("summary", ""), d])
    edges = [(e["source"], e["target"], e["relation"]) for e in g["links"] if e["relation"] != "CONTAINS"]
    meta = g["graph"]
    return pack(v, "Project map", f"{meta['edition'].capitalize()} edition, release {meta['release']}", PROJECT_KINDS, PROJECT_RELS, nodes, edges,
                "Every file in this edition, its imports, tests, document links and external packages, plus the engine's "
                "interfaces. Solid lines are read from the code. Dotted lines are matched by name.", switch, meta, PROJECT_LEGEND)


# ---------- knowledge graph ----------
KNOWLEDGE_KINDS = [{"id": "rule", "label": "Rule", "slot": 0}, {"id": "concept", "label": "Concept", "slot": 1}, {"id": "book", "label": "Book", "slot": 2},
                   {"id": "dispute", "label": "Dispute", "slot": 3}, {"id": "position", "label": "Position", "slot": 4}, {"id": "person", "label": "Person", "slot": 5}]
KNOWLEDGE_RELS = [{"id": "APPLIES_TO", "label": "applies to", "inverse": "rules about this"},
                  {"id": "CITES", "label": "cites", "inverse": "cited by"},
                  {"id": "HAS_POSITION", "label": "has position", "inverse": "position of"},
                  {"id": "CONTRADICTS", "label": "contradicts", "inverse": "contradicted by", "dash": "6 4"},
                  {"id": "DISCUSSED_IN", "label": "discussed in", "inverse": "discusses"},
                  {"id": "SIMILAR_TO", "label": "similar to", "inverse": "similar to", "dash": "2 4"},
                  {"id": "REFERS_TO", "label": "refers to", "inverse": "referred to by"},
                  {"id": "WRITTEN_BY", "label": "written by", "inverse": "author of"},
                  {"id": "TRANSLATED_BY", "label": "translated by", "inverse": "translator of"}]
CONCEPT_TITLES = {"planet": "Planets", "house": "Houses", "sign": "Signs", "nakshatra": "Nakshatras", "yoga": "Yogas", "topic": "Topics",
                  "technique": "Techniques", "varga": "Divisional charts", "lk": "Lal Kitab terms", "dasha": "Dasha systems"}
SUMMARY_TYPES = {"Page", "DuplicateFile"}


def withhold_birth_details(nodes, groups):
    """Worked examples can quote a chart's birth details. The page shows that an example exists; graph.json keeps the text."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    from privacy_check import records
    for n in nodes:
        if records(n[1]):
            n[1] = (n[1].split("]")[0] + "] " if n[1].startswith("[") else "") + "Worked example, birth details withheld"
        n[5] = {k: v for k, v in n[5].items() if not (isinstance(v, str) and records(v))}
    for g in groups:
        if records(g[0]):
            g[0] = "Section with birth details withheld"


def knowledge_view(g, release="", switch=None):
    v = View()
    books_root, concepts, disputes, people = [v.group(k, label) for k, label in (("books", "Books"), ("concepts", "Concepts"),
                                                                                 ("disputes", "Disputes"), ("people", "People"))]
    types = {n["id"]: n["node_type"] for n in g["nodes"]}
    page_book = {n["id"]: n["attributes"].get("book") for n in g["nodes"] if n["node_type"] == "Page"}
    book_gid = {}
    nodes, edges = [], []
    mentions, mention_books = Counter(), defaultdict(Counter)
    pages_of = defaultdict(set)
    near_dup = 0
    for e in g["links"]:
        r, s, t = e["relation"], e["source"], e["target"]
        if r == "MENTIONS":
            mentions[t] += 1
            mention_books[t][page_book.get(s)] += 1
        elif r == "NEAR_DUPLICATE_OF":
            near_dup += 1
        elif r in ("RULE_FROM", "SUPPORTED_BY") and t in page_book:
            pages_of[s].add(page_book[t])
    for n in g["nodes"]:
        if n["node_type"] == "Book":
            a = n["attributes"]
            system = v.group("system:" + a.get("system", "Other"), a.get("system", "Other"), books_root)
            book_gid[a["source_id"]] = v.group(n["id"] + ":rules", f"{a['source_id']}: {n['label']}", system)
    for n in g["nodes"]:
        t, a, nid = n["node_type"], n.get("attributes") or {}, n["id"]
        if t in SUMMARY_TYPES:
            continue
        if t == "Rule":
            src = a.get("source")
            section = re.split(r"\s*›\s*", a.get("section") or "General")[0][:80]
            gid = v.group(f"sec:{src}:{section}", section, book_gid.get(src, books_root))
            ver = (a.get("verification") or {})
            d = {k: a[k] for k in ("rule_id", "tier", "system", "evidence_role") if a.get(k)}
            d.update({"pages": ", ".join(a.get("pages", [])[:12])} if a.get("pages") else {})
            if isinstance(ver, dict) and ver.get("level"):
                d["verification"] = ver["level"]
            if a.get("do_not_forecast"):
                d["caution"] = "Doctrine only, never a forecast"
            nodes.append([nid, n["label"], "rule", gid, a.get("tier", ""), d])
        elif t == "Book":
            d = {k: a[k] for k in ("author", "translator", "edition", "year", "language", "system", "tier", "pages") if a.get(k)}
            nodes.append([nid, n["label"], "book", book_gid[a["source_id"]], a.get("author", ""), d])
        elif t == "Person":
            nodes.append([nid, n["label"], "person", people, "", {}])
        elif t == "Contradiction":
            gid = v.group("dispute:" + str(a.get("dispute_type")), str(a.get("dispute_type") or "other").replace("_", " ").capitalize(), disputes)
            d = {k: a[k] for k in ("classification", "working_default", "review_note") if a.get(k)}
            nodes.append([nid, n["label"], "dispute", gid, a.get("dispute_type", ""), d])
        elif t == "Position":
            gid = v.group("dispute:positions", "Positions", disputes)
            nodes.append([nid, n["label"], "position", gid, "", {"pages": ", ".join(a.get("pages", [])[:12])} if a.get("pages") else {}])
        else:
            prefix = nid.split(":")[0]
            gid = v.group("concept:" + prefix, CONCEPT_TITLES.get(prefix, prefix.capitalize()), concepts)
            d = {}
            if mentions[nid]:
                top = ", ".join(f"{b} {c}" for b, c in mention_books[nid].most_common(6) if b)
                d = {"mentioned on": f"{mentions[nid]:,} book pages", "most in": top}
            nodes.append([nid, n["label"], "concept", gid, f"{mentions[nid]:,} page mentions" if mentions[nid] else "", d])
    for e in g["links"]:
        r, s, t = e["relation"], e["source"], e["target"]
        if r in ("RULE_FROM", "SUPPORTED_BY"):
            continue
        edges.append((s, t, r))
    # a rule sits under its own book; only citations of another book become edges
    node_src = {n["id"]: n["attributes"].get("source") for n in g["nodes"] if n["node_type"] == "Rule"}
    book_node = {n["attributes"]["source_id"]: n["id"] for n in g["nodes"] if n["node_type"] == "Book"}
    for s, books in pages_of.items():
        for b in books:
            if b in book_node and node_src.get(s) != b:
                edges.append((s, book_node[b], "CITES"))
    withhold_birth_details(nodes, v.groups)
    counts = Counter(t for t in types.values())
    meta = {"release": release, "nodes": len(g["nodes"]), "links": len(g["links"]), "pages": counts["Page"], "near_duplicate_page_pairs": near_dup}
    note = (f"Every rule, concept, book, person and dispute from the full graph ({meta['nodes']:,} nodes, {meta['links']:,} edges). "
            f"{counts['Page']:,} page nodes and their {sum(mentions.values()):,} concept mentions are folded into the details.")
    return pack(v, "Knowledge graph", f"Book library, release {release}" if release else "Book library", KNOWLEDGE_KINDS, KNOWLEDGE_RELS, nodes, edges,
                note, switch, meta, KNOWLEDGE_LEGEND)


def write_html(view, out):
    with open(TEMPLATE, encoding="utf-8") as f:
        page = f.read()
    data = json.dumps(view, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace("<", "\\u003c")
    if "/*GRAPH_DATA*/null" not in page:
        sys.exit("viewer.html has no /*GRAPH_DATA*/ slot")
    page = page.replace("/*GRAPH_DATA*/null", data).replace("__PAGE_TITLE__", view["title"])
    tmp = out + ".new"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(page)
    os.replace(tmp, out)


def release_of_workspace(ws):
    try:
        return json.load(open(os.path.join(ws, "plugin", ".claude-plugin", "plugin.json"), encoding="utf-8"))["version"]
    except (OSError, KeyError, ValueError):
        return ""


def write_knowledge(graph_json, out, ws):
    with open(graph_json, encoding="utf-8") as f:
        g = json.load(f)
    write_html(knowledge_view(g, release_of_workspace(ws), SWITCH_KNOWLEDGE), out)


if __name__ == "__main__":
    ws = os.path.abspath(os.path.join(HERE, "..", ".."))
    if sys.argv[1:2] != ["knowledge"]:
        sys.exit(__doc__)
    src = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ws, "graphify-out", "graph.json")
    dst = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ws, "graphify-out", "graph.html")
    write_knowledge(src, dst, ws)
    print("wrote", dst, os.path.getsize(dst), "bytes")
