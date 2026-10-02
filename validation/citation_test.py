# Source-citation test for one book's rules in the graph: can a rule be found again from its own subject matter, and
# does the page it cites exist in the index with matching words?
# usage: python3 validation/citation_test.py BPHS
import os, random, re, sqlite3, sys
WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(WS, "astrology-prediction", "scripts"))
import kg

src = sys.argv[1]
N, out, inc = kg.load()
db = sqlite3.connect(f"file:{os.path.join(WS, 'index', 'library.sqlite')}?mode=ro", uri=True)
rules = [n for n in N.values() if n.get("node_type") == "Rule" and kg.attrs(n).get("source") == src]
random.seed(11)
sample = random.sample(rules, min(20, len(rules)))
found = page_ok = 0
lines = []
for n in sample:
    ents = [e["target"] for e in out[n["id"]] if e["relation"] == "APPLIES_TO" and not e["target"].startswith("topic:")]
    labels = " ".join(N[e]["label"] for e in ents[:3] if not e.startswith("house:"))
    houses = [e.split(":")[1] for e in ents if e.startswith("house:")][:1]
    q = (labels + (f" house {houses[0]}" if houses else "")).strip()
    hit = False
    if q:
        _, _, hits = kg.search_rules(N, out, inc, q, src=src)
        hit = n["id"] in [h[-1] for h in hits]
    pages = [e["target"] for e in out[n["id"]] if e["relation"] == "RULE_FROM"]
    pw = False
    for pid in pages[:2]:
        a = kg.attrs(N[pid])
        row = db.execute("select text from pages where src=? and page=?", (a["book"], a["pdf_page"])).fetchone()
        if row:
            bw = {w for w in re.findall(r"[a-z]{5,}", kg.attrs(n).get("text", "").lower())}
            pw = pw or len(bw & set(re.findall(r"[a-z]{5,}", row[0].lower()))) >= 2
    found += hit
    page_ok += pw
    lines.append(f"- {'✓' if hit else '·'}{'✓' if pw else '·'} {n['id']} q='{q}' pages={[N[p]['label'] for p in pages[:3]]}")
k = len(sample)
print(f"{src}: {len(rules)} rules in graph; retrievable from own entities {found}/{k}; cited page present with matching words {page_ok}/{k}")
open(os.path.join(WS, "validation", "sourcemaps", f"citation_{src}.md"), "w").write(
    f"# Citation test {src}\n\nretrievable {found}/{k}; page match {page_ok}/{k}\n\n" + "\n".join(lines) + "\n")
