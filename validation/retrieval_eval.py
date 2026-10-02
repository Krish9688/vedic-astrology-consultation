# Does the knowledge graph retrieve the right source pages better than plain full-text search?
# Gold pages come from the contradiction register and source-map headings (written from reading the books),
# not from the graph code. Metric: share of gold pages found in the top-K pages each method returns.
# usage: python3 validation/retrieval_eval.py   → prints a table and writes validation/retrieval_eval.md
import os, re, sqlite3, sys

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(WS, "astrology-prediction", "scripts"))
import kg

K = 15
CASES = [  # (question as a user/astrologer would type it, gold "SRC:page" set)
    ("house, its lord and the karaka all weak destroy the house", {"PD:184"}),
    ("karaka in its own house harms the house (karako bhava nashaya)", {"PD:191", "LOL:291"}),
    ("Kemadruma yoga cancellation", {"BJ:179", "BJ:180", "LOL:321"}),
    ("Venus in the 7th house and marriage", {"HJH2:65"}),
    ("marriage timing when Venus or the 7th lord transits a trine to the lagna lord", {"PD:139"}),
    ("vedha obstruction in transits of Mercury and Venus", {"PD:313", "PD:314", "HPA:133", "HPA:134"}),
    ("combustion makes a planet powerless", {"HPA:16", "HPA:17", "LOL:297", "LOL:298"}),
    ("Mars in the 7th kuja dosha and the spouse", {"HJH2:27", "HJH2:70", "LOL:329", "LOL:330", "LOL:331"}),
    ("Rahu exaltation sign", {"HPA:14", "LOL:89", "LKS:33", "LKS:34"}),
    ("retrograde debilitated planet acts as exalted", {"LOL:300", "LOL:416"}),
    ("bhukti lord in the 6th, 8th or 12th from the dasha lord", {"PD:240", "LOL:356", "LOL:357"}),
    ("transits judged from the Moon or from the lagna", {"LOL:362", "HPA:132"}),
    ("Atmakaraka and karakamsa (Jaimini)", {"HJH2:285"}),
    ("Saturn in the 10th house in Lal Kitab", {"LK1952:699", "LK1952:700", "LK1952:701", "LK1952:702", "LK1952:703"}),
    ("Jupiter in the 7th house in Lal Kitab", {"LK1952:341", "LK1952:342", "LK1952:343", "LK1952:344", "LK1952:345", "LKS:109"}),
    ("sleeping planet wakes up in Lal Kitab", {"LK1952:119", "LKS:44"}),
    ("planet in its pakka ghar cannot be remedied", {"LK1952:59", "LK1952:60", "LKS:42", "LKS:47"}),
]
STOP = set("the a an of in and or to its is as by for from with when all own house planet lal kitab".split())


def fts_pages(db, q):
    words = [w for w in re.findall(r"[A-Za-z]+", q.lower()) if w not in STOP and len(w) > 2]
    out = []
    for expr in (" AND ".join(words), " OR ".join(words)):  # strict first, then relaxed; keep order
        try:
            for src, page in db.execute("select src, page from pages where pages match ? order by rank limit ?", (expr, K)):
                k = f"{src}:{page}"
                if k not in out:
                    out.append(k)
        except sqlite3.OperationalError:
            pass
    return out[:K]


def graph_pages(N, out, inc, q):
    pages = []
    _, _, hits = kg.search_rules(N, out, inc, q)
    ranked = [h[-1] for h in hits]
    # recorded disputes on the same topic point to the pages on both sides
    for _, _, _, pos in reversed(kg.find_contradictions(N, out, q)[:3]):
        ranked[:0] = [p["id"] for p in pos]
    for rid in ranked:
        for e in out[rid]:
            if e["relation"] == "RULE_FROM":
                a = N[e["target"]]["attributes"]
                k = f"{a['book']}:{a['pdf_page']}"
                if k not in pages:
                    pages.append(k)
        if len(pages) >= K:
            break
    return pages[:K]


def hybrid(a, b):
    """Interleave graph and full-text results (graph first), dropping repeats."""
    out = []
    for pair in zip(a + [None] * K, b + [None] * K):
        for p in pair:
            if p and p not in out:
                out.append(p)
    return out[:K]


def main():
    db = sqlite3.connect(f"file:{os.path.join(WS, 'index', 'library.sqlite')}?mode=ro", uri=True)
    N, out, inc = kg.load()
    rows, tot = [], [0] * 6
    for q, gold in CASES:
        f, g = fts_pages(db, q), graph_pages(N, out, inc, q)
        h = hybrid(g, f)
        rf, rg, rh = (len(gold & set(x)) / len(gold) for x in (f, g, h))
        bf, bg, bh = (len({p.split(':')[0] for p in x}) for x in (f, g, h))
        rows.append((q, len(gold), rf, rg, rh, bf, bg, bh))
        tot = [t + v for t, v in zip(tot, (rf, rg, rh, rf > 0, rg > 0, rh > 0))]
    n = len(CASES)
    L = ["# Retrieval evaluation: knowledge graph vs full-text search", "",
         f"Top-{K} pages per method. Recall = share of the case's gold pages retrieved. Books = distinct books in the results.", "",
         "| Question | Gold | FTS | Graph | Hybrid | Books FTS/Graph/Hybrid |", "|---|---|---|---|---|---|"]
    L += [f"| {q} | {g} | {rf:.2f} | {rg:.2f} | {rh:.2f} | {bf}/{bg}/{bh} |" for q, g, rf, rg, rh, bf, bg, bh in rows]
    L += ["", f"**Mean recall:** full-text {tot[0]/n:.2f}, graph {tot[1]/n:.2f}, hybrid {tot[2]/n:.2f}.  "
          f"**Cases with ≥1 gold page:** full-text {tot[3]}/{n}, graph {tot[4]}/{n}, hybrid {tot[5]}/{n}.", ""]
    txt = "\n".join(L)
    open(os.path.join(WS, "validation", "retrieval_eval.md"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
