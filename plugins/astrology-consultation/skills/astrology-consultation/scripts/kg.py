# Query the local astrology knowledge graph (built with Graphify from the user's books). Read-only, stdlib only.
# Every answer carries its provenance: source book, page (PDF + printed), verse, tier, system, extraction note.
#
#   python3 kg.py sources "karaka in its own house"          best first call: graph rules + disputes + full-text pages
#   python3 kg.py find "Jupiter aspecting the 7th lord"      rules that apply to ALL recognised entities
#   python3 kg.py find "Venus in the 7th" --system "Lal Kitab" --tier classical -n 5
#   python3 kg.py contradictions "Rahu exaltation"           recorded disputes, both positions with pages
#   python3 kg.py pages "Jupiter 7th house"                  pages in every book mentioning all of them
#                                                            (synonyms incl. Hindi: Guru = बृहस्पति = Jupiter)
#   python3 kg.py rule rule:PD:1a2b3c4d5e                    one rule in full, with its links
#   python3 kg.py terms "Guru in 7th, navamsa"               show how a query is understood
#
# The graph is built on the user's Mac (tools/kg); elsewhere this exits cleanly and the skill answers without it.
import argparse, json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vocab

from paths import knowledge_file
GRAPH = knowledge_file("ASTRO_KG", os.path.join("graphify-out", "graph.json"))
TIER_ORDER = {"classical": 0, "traditional": 1, "modern": 2, "synthesis": 3, "experimental": 4}


def load():
    if not os.path.exists(GRAPH):
        sys.exit(f"Knowledge graph not found at {GRAPH}. It exists only on the machine where it was built; "
                 "set ASTRO_KG or answer without graph retrieval and say so.")
    g = json.load(open(GRAPH, encoding="utf-8"))
    N = {n["id"]: n for n in g["nodes"]}
    out, inc = defaultdict(list), defaultdict(list)
    for e in g.get("links") or g.get("edges"):
        out[e["source"]].append(e)
        inc[e["target"]].append(e)
    return N, out, inc


def parse(q):
    ents = set(vocab.find_entities(q))
    houses = vocab.house_refs(q)
    topics = {e for e in ents if e.startswith("topic:")}
    return ents - topics, houses, topics


def attrs(n):
    return n.get("attributes") or {}


def cite(n):
    a = attrs(n)
    parts = [", ".join(a.get("pages", [])[:4]) or "no page"]
    if a.get("verses"):
        parts.append("verse " + ", ".join(a["verses"][:3]))
    return " · ".join(parts)


def rule_matches(rid, ents, houses, out):
    links = {}
    for e in out[rid]:
        if e["relation"] == "APPLIES_TO":
            links[e["target"]] = e.get("role", "")
    if not ents <= set(links):
        return False
    for h, role in houses:
        r = links.get(f"house:{h}")
        if r is None or (role == "lord" and "lord" not in r) or (role == "house" and "house" not in r):
            return False
    return True


def focus(text, ents, houses):
    """Smallest character window holding one mention of every query term (smaller = more on-topic)."""
    hs = vocab.house_spans(text)
    occ = [vocab.entity_spans(text, e) for e in ents]
    occ += [[p for n, r, p in hs if n == h and (role == r or role == "house")] for h, role in houses]
    occ = [o[:20] for o in occ if o]
    if len(occ) < 2:
        return 0
    best = 10 ** 6
    for p in occ[0]:
        near = [min(o, key=lambda q: abs(q - p)) for o in occ[1:]]
        best = min(best, max(near + [p]) - min(near + [p]))
    return best


def supports(rid, out, N):
    """Pages in other books that a source map says agree with this rule."""
    return sorted({N[e["target"]]["label"] for e in out[rid] if e["relation"] == "SUPPORTED_BY"})


def disputes(rid, out, N):
    return sorted({N[e["target"]]["label"].split(":")[0] for e in out[rid] if e["relation"] == "DISCUSSED_IN"})


def search_rules(N, out, inc, query, src=None, tier=None, system=None, text=None):
    """Ranked [(key..., source, rule_id)] for rules applying to every term recognised in the query."""
    ents, houses, topics = parse(query)
    if not system and re.search(r"lal ?kitab", query, re.I):
        system = "Lal Kitab"  # the question names the system: keep the answer inside it
    elif not system and re.search(r"\bnadi\b", query, re.I):
        system = "Nadi"
    elif not system and re.search(r"\bjaimini\b", query, re.I):
        system = "Jaimini"
    ents = ents - {"technique:jaimini"} if system else ents  # a named system filters; it is not a required term
    seeds = ents | {f"house:{h}" for h, _ in houses} or topics
    cand = None
    for s in seeds:
        rs = {e["source"] for e in inc[s] if e["relation"] == "APPLIES_TO" and e["source"].startswith("rule:")}
        cand = rs if cand is None else cand & rs
    hits = []
    for rid in cand or ():
        at = attrs(N[rid])
        if not rule_matches(rid, ents, houses, out):
            continue
        if src and at.get("source") not in src.split(","):
            continue
        if tier and at.get("tier") != tier:
            continue
        if system and system.lower() not in (at.get("system") or "").lower():
            continue
        if text and not all(w.lower() in at.get("text", "").lower() for w in text.split()):
            continue
        topic_hits = sum(1 for e in out[rid] if e["relation"] == "APPLIES_TO" and e["target"] in topics)
        window = focus(at.get("text", ""), ents, houses)
        h_ents, h_houses, _ = parse(at.get("heading") or "")
        in_section = bool(ents or houses) and ents <= h_ents and all(any(n == h for n, _ in h_houses) for h, _ in houses)
        hits.append((0 if in_section else 1, min(window // 40, 5), -topic_hits, window,
                     TIER_ORDER.get(at.get("tier"), 9), at.get("source", ""), rid))
    hits.sort()
    return seeds, topics, hits


def cmd_find(a, N, out, inc):
    ents, houses, topics = parse(a.query)
    if not ents and not houses and not topics:
        sys.exit("No astrological terms recognised; try `terms` to see the vocabulary, or search.py for free text.")
    seeds, topics, hits = search_rules(N, out, inc, a.query, a.src, a.tier, a.system, a.text)
    print(f"# {len(hits)} rules apply to: {', '.join(sorted(seeds))}"
          + (f" (ranked by topic: {', '.join(sorted(topics))})" if topics and (ents or houses) else ""))
    by_src = defaultdict(int)
    shown = 0
    for *_, src, rid in hits:
        if by_src[src] >= a.per_source or shown >= a.n:
            continue
        by_src[src] += 1
        shown += 1
        n = N[rid]
        at = attrs(n)
        d = disputes(rid, out, N)
        flag = " ⚠ do not forecast" if at.get("do_not_forecast") else ""
        print(f"\n[{src}] {at.get('tier')} · {at.get('system')} · {at.get('evidence_role', '')} · {cite(n)}{flag}\n"
              f"  {at.get('text', '')[:a.width]}"
              + (f"\n  disputed in: {', '.join(d)}" if d else "")
              + (f"\n  also supported by: {', '.join(supports(rid, out, N))}" if supports(rid, out, N) else "")
              + f"\n  id: {rid}")
    rest = {s: sum(1 for h in hits if h[-2] == s) for s in {h[-2] for h in hits}}
    print(f"\n# by source: {', '.join(f'{k} {v}' for k, v in sorted(rest.items()))}  (use --src/-n/--per-source for more)")


def find_contradictions(N, out, query):
    """Recorded disputes whose topic or positions cover every recognised term (or, failing that, every word)."""
    ents, houses, topics = parse(query)
    want = ents | topics | {f"house:{h}" for h, _ in houses}
    words = [w[:5] for w in re.findall(r"\w{4,}", query.lower())]  # stems: "exaltation" also matches "exalted"
    lk_only = bool(re.search(r"lal ?kitab", query, re.I))
    found = []
    for cid, n in N.items():
        if n.get("node_type") != "Contradiction":
            continue
        pos = [N[e["target"]] for e in out[cid] if e["relation"] == "HAS_POSITION"]
        if lk_only and not (cid.split(":")[1].startswith(("KB-", "CR-L", "CR-S"))
                            or any(re.match(r"LK", pg) for p in pos for pg in attrs(p).get("pages", []))):
            continue  # a Lal Kitab question gets Lal Kitab disputes only
        topic_links = {e["target"] for e in out[cid] if e["relation"] == "APPLIES_TO"}
        linked = topic_links | {e["target"] for p in pos for e in out[p["id"]] if e["relation"] == "APPLIES_TO"}
        blob = " ".join([n["label"]] + [attrs(p).get("text", "") for p in pos]).lower()
        overlap = sum(w in blob for w in words)
        curated = 0 if not cid.split(":")[1].startswith("XB-") else 1
        if want and want <= linked:
            # specific disputes first: more query words present, fewer unrelated entities, curated before automatic
            found.append((-overlap, 0 if want <= topic_links else 1, curated, len(linked), cid, n, pos))
        elif words and all(w in blob for w in words):
            found.append((-overlap, 2, curated, len(linked), cid, n, pos))
    return [(f[1], f[4], f[5], f[6]) for f in sorted(found, key=lambda x: x[:5])]


def cmd_contradictions(a, N, out, inc):
    found = find_contradictions(N, out, a.query)
    print(f"# {len(found)} recorded disputes")
    for _, cid, n, pos in found[: a.n]:
        at = attrs(n)
        print(f"\n{n['label']}  [{at.get('classification', '')}]  ({at.get('extracted_from')})")
        for p in sorted(pos, key=lambda p: attrs(p).get("side", "")):
            pa = attrs(p)
            print(f"  {pa.get('side')}: {pa.get('text', '')[:a.width]}")
        if at.get("working_default"):
            print(f"  working default: {at['working_default'][:a.width]}")


def cmd_sources(a, N, out, inc):
    """Hybrid answer to "which source supports this?": graph rules + recorded disputes + full-text pages."""
    ents, houses, topics = parse(a.query)
    cited = set()
    if ents or houses or topics:
        _, _, hits = search_rules(N, out, inc, a.query, a.src, a.tier, a.system, a.text)
        print(f"## Rules in the graph ({len(hits)} match; best {min(a.n, len(hits))})")
        for *_, src, rid in hits[: a.n]:
            at = attrs(N[rid])
            cited.update(at.get("pages", []))
            flag = " ⚠ do not forecast" if at.get("do_not_forecast") else ""
            role = at.get("evidence_role", "")
            print(f"- [{src}] {at.get('tier')} · {role} · {cite(N[rid])}{flag}: {at.get('text', '')[:a.width]}")
    found = find_contradictions(N, out, a.query)[:3]
    if found:
        print("\n## Recorded disputes (both sides kept)")
        for _, cid, n, pos in found:
            print(f"- {n['label']}")
            for p in sorted(pos, key=lambda p: attrs(p).get("side", "")):
                print(f"  {attrs(p).get('side')}: {attrs(p).get('text', '')[:a.width]}")
    db = os.environ.get("ASTRO_LIBRARY_DB") or os.path.join(os.path.dirname(GRAPH), "..", "index", "library.sqlite")
    words = [w for w in re.findall(r"[A-Za-z]{3,}", a.query.lower()) if w not in ("the", "and", "for", "with", "from", "its")]
    if os.path.exists(db) and words:
        import sqlite3
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        print("\n## Full-text pages not already cited above")
        shown = 0
        for expr in (" AND ".join(words), " OR ".join(words)):
            for src, page, snip in c.execute("select src, page, snippet(pages, 3, '[', ']', '…', 14) from pages "
                                             "where pages match ? order by rank limit 12", (expr,)):
                if f"{src} p{page}" in cited or shown >= 5:
                    continue
                cited.add(f"{src} p{page}")
                shown += 1
                print(f"- {src} p{page}: {snip}")
    print("\n# verify before citing: python3 search.py --page SRC:N")


def cmd_pages(a, N, out, inc):
    ents, houses, topics = parse(a.query)
    seeds = ents | topics | {f"house:{h}" for h, _ in houses}
    if not seeds:
        sys.exit("No astrological terms recognised.")
    score, cand = defaultdict(int), None
    for s in seeds:
        ps = {}
        for e in inc[s]:
            if e["relation"] == "MENTIONS":
                ps[e["source"]] = e.get("weight", 1)
        cand = set(ps) if cand is None else cand & set(ps)
        for p, w in ps.items():
            score[p] += w
    ranked = sorted(cand or (), key=lambda p: -score[p])
    if a.src:
        ranked = [p for p in ranked if attrs(N[p]).get("book") in a.src.split(",")]
    per = defaultdict(list)
    for p in ranked:
        per[attrs(N[p]).get("book")].append(p)
    print(f"# {len(ranked)} pages mention all of: {', '.join(sorted(seeds))}")
    for book, ps in sorted(per.items(), key=lambda kv: -len(kv[1])):
        top = ", ".join(N[p]["label"].split(" ", 1)[1] + ("⚑" if "low-ocr-quality" in attrs(N[p]).get("flags", []) else "")
                        for p in ps[: a.n])
        print(f"{book}: {len(ps)} pages — top: {top}")
    print("# read a page: python3 search.py --page SRC:N   (⚑ = low OCR quality, check the image)")


def cmd_rule(a, N, out, inc):
    n = N.get(a.query) or sys.exit(f"no node {a.query}")
    print(json.dumps({k: v for k, v in n.items() if k not in ("norm_label",)}, ensure_ascii=False, indent=1))
    for e in out[a.query]:
        print(f"  --{e['relation']}--> {N[e['target']]['label'][:90]}" + (f" ({e['role']})" if e.get("role") else ""))
    for e in inc[a.query]:
        print(f"  <--{e['relation']}-- {N[e['source']]['label'][:90]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["sources", "find", "contradictions", "pages", "rule", "terms"])
    ap.add_argument("query")
    ap.add_argument("--src", help="comma-separated source ids, e.g. PD,BJ")
    ap.add_argument("--tier", choices=list(TIER_ORDER))
    ap.add_argument("--system", help='e.g. Parashari, "Lal Kitab", Prashna')
    ap.add_argument("--text", help="extra words that must appear in the rule text")
    ap.add_argument("-n", type=int, default=12)
    ap.add_argument("--per-source", type=int, default=4)
    ap.add_argument("--width", type=int, default=320)
    a = ap.parse_args()
    if a.cmd == "terms":
        ents, houses, topics = parse(a.query)
        print("entities:", sorted(ents), "\nhouses:", sorted(houses), "\ntopics (ranking only):", sorted(topics))
        return
    N, out, inc = load()
    {"sources": cmd_sources, "find": cmd_find, "contradictions": cmd_contradictions, "pages": cmd_pages, "rule": cmd_rule}[a.cmd](a, N, out, inc)


if __name__ == "__main__":
    main()
