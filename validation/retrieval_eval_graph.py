# Graph-only retrieval evaluation (KB-F12 / C7-10). Runs offline on knowledge/graph/graph.json.gz; no full-text index.
# Gold rule ids are the agent's own relevance judgement from reading rule texts (not owner-reviewed, not derived from
# the register or source maps the graph was built from), so this is less circular than validation/retrieval_eval.py,
# not free of bias: unjudged relevant rules count as misses, and the same judge wrote queries and gold.
# Cases: validation/retrieval_eval_cases.json (frozen by sha256 before tuning; split tune/heldout by sha256(query)).
# usage: python3 validation/retrieval_eval_graph.py [--cases]      prints recall@10 / MRR per split
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "validation", "retrieval_eval_cases.json")
GRAPH = os.path.join(ROOT, "knowledge", "graph", "graph.json.gz")
K = 10


def digest(cases):
    return hashlib.sha256(json.dumps(cases, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def split_of(query):
    return "tune" if int(hashlib.sha256(query.encode()).hexdigest()[:8], 16) % 2 == 0 else "heldout"


def load_cases():
    return json.load(open(CASES, encoding="utf-8"))


def load_kg():
    for d in ("skill/astrology-consultation/scripts", "astrology-prediction/scripts"):
        if os.path.isdir(os.path.join(ROOT, d)):
            sys.path.insert(0, os.path.join(ROOT, d))
            break
    import kg
    kg.GRAPH = GRAPH
    return kg


def evaluate(kg=None, graph=None):
    """{split: {"n", "recall@10", "mrr", "misses": [case ids with recall 0]}} for the current kg/vocab code."""
    kg = kg or load_kg()
    N, out, inc = graph or kg.load()
    res = {}
    for c in load_cases()["cases"]:
        gold = set(c["gold"])
        ranked = [h[-1] for h in kg.search_rules(N, out, inc, c["query"])[2]]
        top = set(ranked[:K])
        rr = next((1 / (i + 1) for i, r in enumerate(ranked) if r in gold), 0.0)
        s = res.setdefault(c["split"], {"n": 0, "recall@10": 0.0, "mrr": 0.0, "misses": []})
        s["n"] += 1
        s["recall@10"] += len(gold & top) / len(gold)
        s["mrr"] += rr
        if not gold & top:
            s["misses"].append(c["id"])
    for s in res.values():
        s["recall@10"] = round(s["recall@10"] / s["n"], 4)
        s["mrr"] = round(s["mrr"] / s["n"], 4)
    return res


if __name__ == "__main__":
    r = evaluate()
    for k in ("tune", "heldout"):
        print(k, json.dumps(r[k]))
