# Build the Graphify knowledge graph from knowledge/extraction.json (made by extract.py).
# Uses Graphify's own library for validation, graph assembly, community detection, the report and exports.
# Local only: no LLM backend, no network. Graphify's fuzzy entity dedup is OFF on purpose: rules that sound
# alike must not be merged (possible duplicates are listed in validation/duplicates.md instead).
# usage: .venv-graphify/bin/python tools/kg/build_graph.py [--wiki] [--obsidian]
import json, os, shutil, sys

os.environ.setdefault("GRAPHIFY_QUERY_LOG_DISABLE", "1")
from graphify.validate import validate_extraction
from graphify.build import build
from graphify.cluster import cluster, score_all, label_communities_by_hub
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json, to_html

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(WS, "graphify-out")


def main():
    ext = json.load(open(os.path.join(WS, "knowledge", "extraction.json"), encoding="utf-8"))
    errors = validate_extraction(ext)
    if errors:
        sys.exit("Extraction failed Graphify schema validation:\n" + "\n".join(errors[:30]))
    G = build([ext], directed=True, dedup=False)
    communities = cluster(G)
    labels = label_communities_by_hub(G, communities)
    cohesion = score_all(G, communities)
    gods = god_nodes(G)
    surprises = surprising_connections(G, communities)
    questions = suggest_questions(G, communities, labels)
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "graph.json.new")
    to_json(G, communities, tmp, force=True, community_labels=labels)
    os.replace(tmp, os.path.join(OUT, "graph.json"))  # atomic: readers never see a half-written graph
    report = generate(G, communities, cohesion, labels, gods, surprises,
                      {"warning": "built from knowledge/extraction.json by tools/kg (deterministic, no LLM)"},
                      {"input": 0, "output": 0}, WS, suggested_questions=questions)
    open(os.path.join(OUT, "GRAPH_REPORT.md"), "w", encoding="utf-8").write(report)
    try:
        to_html(G, communities, os.path.join(OUT, "graph.html"), community_labels=labels, node_limit=5000)
    except ValueError as e:
        print("graph.html skipped:", e)
    if "--wiki" in sys.argv:
        from graphify.wiki import to_wiki
        shutil.rmtree(os.path.join(OUT, "wiki"), ignore_errors=True)
        to_wiki(G, communities, os.path.join(OUT, "wiki"), community_labels=labels, cohesion=cohesion, god_nodes_data=gods)
    if "--obsidian" in sys.argv:
        from graphify.export import to_obsidian
        to_obsidian(G, communities, os.path.join(OUT, "obsidian"), community_labels=labels, cohesion=cohesion)
    print(f"graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities → {OUT}")


if __name__ == "__main__":
    main()
