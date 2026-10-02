# Structural integrity checks on the built graph. Exit code 1 if any hard check fails.
# usage: python3 validation/graph_checks.py
import hashlib, json, os, sys
from collections import Counter, defaultdict

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
g = json.load(open(os.path.join(WS, "graphify-out", "graph.json"), encoding="utf-8"))
cat = json.load(open(os.path.join(WS, "knowledge", "catalog.json"), encoding="utf-8"))
N = {n["id"]: n for n in g["nodes"]}
out = defaultdict(list)
for e in g["links"]:
    out[e["source"]].append(e)
fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(("PASS " if ok else "FAIL ") + msg)


rules = [n for n in N.values() if n.get("node_type") == "Rule"]
a = lambda n: n.get("attributes") or {}
check(all(a(n).get("source") and a(n).get("tier") and a(n).get("extraction_date") for n in rules),
      f"all {len(rules)} rules carry source, tier and extraction date")
cited = [n for n in rules if any(e["relation"] == "RULE_FROM" for e in out[n["id"]])]
check(all(a(n).get("confidence") == "EXTRACTED" for n in cited), "every rule with a page link is marked EXTRACTED")
check(all(a(n).get("confidence") == "AMBIGUOUS" for n in rules if n not in cited), "every rule without a page link is marked AMBIGUOUS")
check(len(cited) / len(rules) > 0.9, f"{len(cited)}/{len(rules)} rules link to at least one source page (>90%)")
cons = [n for n in N.values() if n.get("node_type") == "Contradiction"]
bad = [c["id"] for c in cons if sum(e["relation"] == "HAS_POSITION" for e in out[c["id"]]) != 2]
check(not bad, f"all {len(cons)} disputes keep exactly two positions {bad[:3]}")
agree = [c for c in cons if str(a(c).get("classification", "")).startswith("false_positive")]   # curated: agreements
check(sum(e["relation"] == "CONTRADICTS" for e in g["links"]) == len(cons) - len(agree),
      f"one CONTRADICTS edge per dispute ({len(agree)} curated false positives have none)")
check(not any(e["relation"] in ("SAME_AS", "MERGED") for e in g["links"]), "no automatic merges of rules")
for b in cat["books"]:
    h = hashlib.sha256(open(os.path.join(cat["library_root"], b["file"]), "rb").read()).hexdigest()
    check(h == b["sha256"], f"book file unchanged: {b['id']}")
pages = Counter(a(n).get("book") for n in N.values() if n.get("node_type") == "Page")
check(all(pages[b["id"]] == b["pages"] for b in cat["books"]), "every PDF page of every book has a page node")
tiers = Counter(a(n).get("tier") for n in rules)
check(set(tiers) <= set(cat["tiers"]), f"tiers are from the catalog vocabulary {dict(tiers)}")
print("\n".join(notes + fails))
sys.exit(1 if fails else 0)
