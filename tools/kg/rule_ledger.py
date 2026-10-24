# Stable rule ids, typed disputes and the verification ladder (roadmap P5-1). Pure functions, no book text needed:
# tools/kg/extract.py calls them during the owner's local rebuild; tests run them on synthetic inputs.
#
# Rule ids: R-<SRC>-NNNNNN, kept in knowledge/curation/rule_ids.json (the id ledger, rewritten by every rebuild).
#   - unchanged bullet (same content hash)                    -> same id, same rev
#   - edited bullet: same first cited page AND wording >= 90   -> same id, rev + 1 (old graph node ids kept in `nodes`)
#   - anything else                                            -> new id; the vanished id is withdrawn, with a successor
#     when one new rule of that source scores >= 90 anywhere or >= 80 on the same page (listed for review, never carried)
# Graph node ids stay rule:<SRC>:<hash>; `resolve` maps an R-id or any former node id to the current entry.
#
# usage: python3 tools/kg/rule_ledger.py resolve <R-id | rule:SRC:hash> [ledger.json]
#        python3 tools/kg/rule_ledger.py sample [extraction.json(.gz)] [--per 2] [--seed 1]   owner page-check list
import gzip, json, os, random, re, sys
from collections import Counter, defaultdict

CARRY, BORDER = 90, 80
RULE_ID = re.compile(r"^R-([A-Z][A-Z0-9_]{0,11})-(\d{6})$")
LEVELS = ("none", "text-layer", "image-checked", "human-page-checked")
DISPUTE_TYPES = ("contradiction", "edition_variant", "school_difference", "reviewed_non_conflict", "empirical")
ANCHOR_MAX_WORDS = 15


# ---------- wording and similarity ----------
def wording(text, src_ids=r"[A-Z][A-Z0-9]{1,11}"):
    """What two versions of a bullet are compared on: the trailing citation clause, digits and punctuation removed."""
    t = re.sub(rf"\s*—\s*(?:(?:{src_ids})\s*)?pp?\.?\s?\d.*$", "", text)
    return re.sub(r"[\d\W_]+", " ", t).lower().strip()


def _lcs(a, b):
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b):
            cur.append(prev[j] + 1 if ca == cb else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def similarity(a, b):
    """Token-sort ratio 0-100 (2*LCS/(len a + len b) over sorted words): the same number as rapidfuzz's
    fuzz.token_sort_ratio, which extract.py uses for SIMILAR_TO, so carry-forward and SIMILAR_TO agree."""
    a, b = " ".join(sorted(a.split())), " ".join(sorted(b.split()))
    if not a and not b:
        return 100.0
    try:
        from rapidfuzz.fuzz import ratio
        return float(ratio(a, b))
    except ImportError:   # ponytail: pure-Python LCS is O(n*m); fine for the few edited bullets of one rebuild
        return 200.0 * _lcs(a, b) / (len(a) + len(b))


# ---------- id assignment ----------
def load(path):
    if path and os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {"version": 1, "rules": {}}


def save(ledger, path):
    tmp = path + ".new"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def assign(ledger, items, today):
    """items: [{"node", "src", "key", "wording"}] in build order; key = first cited page ("PD p191") or "§ <section>".
    Returns (new ledger, {node: entry with "rule_id"}, review lines). The input ledger is not modified."""
    old = {k: dict(v) for k, v in ledger.get("rules", {}).items()}
    active = {k for k, v in old.items() if v.get("status") == "active"}
    by_node = {old[k]["node"]: k for k in active}
    out, review, todo = {}, [], {}
    for it in items:                                    # 1. unchanged text: same content hash
        rid = by_node.get(it["node"])
        if rid:
            old[rid].update(key=it["key"], wording=it["wording"])
            out[it["node"]] = rid
        else:
            todo[it["node"]] = it
    free = sorted(active - set(out.values()))
    pairs = sorted((-similarity(it["wording"], old[k]["wording"]), k, node) for node, it in todo.items()
                   for k in free if old[k]["src"] == it["src"] and old[k]["key"] == it["key"])
    used = set()                                        # 2. edited text: same page, wording >= 90, one-to-one
    for neg, rid, node in pairs:
        if -neg >= CARRY and rid not in used and node not in out:
            e, it = old[rid], todo[node]
            e.update(node=node, nodes=e["nodes"] + [node], key=it["key"], wording=it["wording"], rev=e["rev"] + 1,
                     revised_on=today)
            out[node] = rid
            used.add(rid)
            review.append(f"carried {rid} rev {e['rev']} (same page, wording {-neg:.0f})")
    top = Counter()
    for k in old:
        m = RULE_ID.match(k)
        top[m.group(1)] = max(top[m.group(1)], int(m.group(2)))
    issued = []
    for node, it in todo.items():                       # 3. everything else: a new id, never reusing a number
        if node in out:
            continue
        top[it["src"]] += 1
        rid = f"R-{it['src']}-{top[it['src']]:06d}"
        old[rid] = dict(src=it["src"], key=it["key"], wording=it["wording"], node=node, nodes=[node], rev=1,
                        status="active", issued_on=today)
        out[node] = rid
        issued.append(rid)
    for rid in [k for k in free if k not in used]:      # 4. vanished ids: withdrawn; a successor is only a pointer
        e = old[rid]
        cand = [(similarity(e["wording"], old[n]["wording"]), n) for n in issued if old[n]["src"] == e["src"]]
        score, succ = max(cand, key=lambda x: x[0], default=(0, None))   # ties: the first issued
        same_page = bool(succ) and old[succ]["key"] == e["key"]
        if not (score >= CARRY or (same_page and score >= BORDER)):
            succ = None
        e.update(status="withdrawn", withdrawn_on=today)
        if succ:
            e["superseded_by"] = succ
            old[succ].setdefault("supersedes", rid)
            review.append(f"REVIEW {rid} withdrawn; successor {succ} (wording {score:.0f}, "
                          f"{'same' if same_page else 'different'} page): not carried forward")
        else:
            review.append(f"withdrawn {rid} (no successor)")
    return {"version": ledger.get("version", 1), "rules": old}, {n: dict(old[r], rule_id=r) for n, r in out.items()}, review


def resolve(ledger, ref):
    """An R-id or any graph node id the rule has had -> (rule id, entry, current one), following withdrawn successors."""
    rules = ledger.get("rules", {})
    rid = ref if ref in rules else next((k for k, v in rules.items() if ref in v.get("nodes", [])), None)
    seen = set()
    cur = rid
    while cur and rules[cur].get("status") == "withdrawn" and rules[cur].get("superseded_by") and cur not in seen:
        seen.add(cur)
        cur = rules[cur]["superseded_by"]
    return (rid, rules.get(rid), cur) if rid else (None, None, None)


# ---------- disputes ----------
def dispute_type(cid, classification="", curated_class=None):
    """Typed dispute from the register id and its free-text class (register: T typo/translation/OCR, R rule
    difference, U undetermined; curation classes in knowledge/curation/xb_curation.json). Anything uncertain stays
    'contradiction': a possible dispute is never hidden."""
    c = str(classification or "").strip()
    if cid.startswith("CR-E"):
        return "empirical"
    if curated_class == "false_positive":
        return "reviewed_non_conflict"
    if curated_class == "school" or cid.startswith("CR-S") or c.startswith("R (school)"):
        return "school_difference"
    if curated_class in ("translation", "ocr") or re.match(r"T(?![/\w])", c):
        return "edition_variant"
    return "contradiction"


# ---------- verification ladder ----------
def anchor_words(anchor):
    return sum(len(str(anchor.get(k) or "").split()) for k in ("prefix", "exact", "suffix"))


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def anchor_found(anchor, page_text):
    """TextQuoteSelector re-located on the page's current text layer (whitespace and case ignored)."""
    a = " ".join(_norm(anchor.get(k)) for k in ("prefix", "exact", "suffix") if anchor.get(k))
    return bool(a) and a in _norm(page_text)


def text_layer_match(rule_text, page_texts):
    words = set(re.findall(r"[a-z]{5,}", rule_text.lower()))
    return any(len(words & set(re.findall(r"[a-z]{5,}", (t or "").lower()))) >= 2 for t in page_texts)


def verification(rule_id, flags, rule_text, page_texts, page_check, extraction_date, today):
    """(record, problem or None). page_texts: the text layers of the rule's cited pages. page_check: the owner's
    record from knowledge/curation/page_checks.json for this rule id, or None."""
    if page_check:
        anchor = page_check.get("anchor") or {}
        if anchor_words(anchor) > ANCHOR_MAX_WORDS:
            return {"level": "none"}, f"{rule_id}: anchor longer than {ANCHOR_MAX_WORDS} words (not used)"
        if anchor and page_texts and not any(anchor_found(anchor, t) for t in page_texts):
            problem = f"{rule_id}: stale anchor (not found on the cited pages; re-check the page)"
        else:
            rec = {k: page_check[k] for k in ("by", "on", "method", "result") if page_check.get(k)}
            return dict(level="human-page-checked", anchor=anchor or None, **rec), None
    else:
        problem = None
    if "image-checked" in flags:
        rec = dict(level="image-checked", by="source-map reader", on=extraction_date,
                   method="page image read while writing the source map (bullet marked image-checked)")
    elif text_layer_match(rule_text, page_texts):
        rec = dict(level="text-layer", by="tools/kg/extract.py", on=today,
                   method="two or more 5+ letter words of the rule found on a cited page's text layer (automatic)")
    else:
        rec = {"level": "none"}
    return rec, problem


def verified(rec):
    return rec.get("level") == "image-checked" or (rec.get("level") == "human-page-checked"
                                                    and rec.get("result", "supported") == "supported")


def verification_table(rules):
    """rules: [(source, record)] -> markdown lines: per-book counts per level and the verified share."""
    by = defaultdict(Counter)
    for src, rec in rules:
        by[src][rec.get("level", "none")] += 1
        by[src]["verified"] += verified(rec)
    L = ["| Book | Rules | " + " | ".join(LEVELS) + " | Verified share |", "|---|---" + "|---" * len(LEVELS) + "|---|"]
    for src in sorted(by):
        c = by[src]
        n = sum(c[lv] for lv in LEVELS)
        L.append(f"| {src} | {n} | " + " | ".join(str(c[lv]) for lv in LEVELS) + f" | {100 * c['verified'] / n:.1f}% |")
    return L


# ---------- graph checks (validation/graph_checks.py) ----------
def graph_problems(nodes, contradicts_edges):
    """Enum and id checks on built graph nodes; contradicts_edges = number of CONTRADICTS edges."""
    a = lambda n: n.get("attributes") or {}
    bad = []
    cons = [n for n in nodes if n.get("node_type") == "Contradiction"]
    bad += [f"{n['id']}: dispute_type {a(n).get('dispute_type')!r} not in {DISPUTE_TYPES}" for n in cons
            if a(n).get("dispute_type") not in DISPUTE_TYPES]
    rnc = [n for n in cons if a(n).get("dispute_type") == "reviewed_non_conflict"]
    bad += [f"{n['id']}: reviewed_non_conflict without a review note" for n in rnc if not a(n).get("review_note")]
    if contradicts_edges != len(cons) - len(rnc):
        bad.append(f"{contradicts_edges} CONTRADICTS edges for {len(cons)} disputes ({len(rnc)} reviewed non-conflicts)")
    seen = Counter()
    for n in nodes:
        if n.get("node_type") != "Rule":
            continue
        r, rid = a(n), a(n).get("rule_id", "")
        m = RULE_ID.match(rid)
        seen[rid] += 1
        if not m or m.group(1) != r.get("source"):
            bad.append(f"{n['id']}: rule_id {rid!r} is not R-{r.get('source')}-NNNNNN")
        if not isinstance(r.get("rev"), int) or r["rev"] < 1:
            bad.append(f"{n['id']}: rev must be an integer >= 1")
        v = r.get("verification") or {}
        if v.get("level") not in LEVELS:
            bad.append(f"{n['id']}: verification level {v.get('level')!r} not in {LEVELS}")
        if anchor_words(v.get("anchor") or {}) > ANCHOR_MAX_WORDS:
            bad.append(f"{n['id']}: anchor longer than {ANCHOR_MAX_WORDS} words")
    bad += [f"rule_id {k} on {c} rules" for k, c in seen.items() if c > 1 and k]
    return bad


# ---------- CLI ----------
def sample(rules, per=2, seed=1):
    """Stratified page-check list: per (source, tag) stratum, `per` rules not yet human-page-checked."""
    strata = defaultdict(list)
    for n in rules:
        a = n.get("attributes") or {}
        if (a.get("verification") or {}).get("level") != "human-page-checked" and a.get("pages"):
            strata[(a.get("source"), (a.get("tag") or "untagged").split()[0])].append(n)
    rnd = random.Random(seed)
    return [(k, n) for k in sorted(strata) for n in rnd.sample(sorted(strata[k], key=lambda n: n["id"]),
                                                              min(per, len(strata[k])))]


def main(argv):
    ws = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if argv[:1] == ["resolve"] and len(argv) >= 2:
        ledger = load(argv[2] if len(argv) > 2 else os.path.join(ws, "knowledge", "curation", "rule_ids.json"))
        rid, e, cur = resolve(ledger, argv[1])
        if not rid:
            sys.exit(f"{argv[1]}: not in the rule id ledger")
        print(f"{argv[1]} -> {rid} ({e['status']}, rev {e['rev']}); current: {cur} node {ledger['rules'][cur]['node']}")
    elif argv[:1] == ["sample"]:
        path = next((x for x in argv[1:] if not x.startswith("--") and not x.isdigit()),
                    os.path.join(ws, "knowledge", "extraction.json"))
        opt = lambda k, d: int(argv[argv.index(k) + 1]) if k in argv else d
        with (gzip.open if path.endswith(".gz") else open)(path, "rt", encoding="utf-8") as f:
            rules = [n for n in json.load(f)["nodes"] if n.get("node_type") == "Rule"]
        for (src, tag), n in sample(rules, opt("--per", 2), opt("--seed", 1)):
            a = n["attributes"]
            print(f"{a.get('rule_id', n['id'])}\t{src}\t{tag}\t{', '.join(a['pages'][:3])}")
    else:
        sys.exit("usage: rule_ledger.py resolve <id> | sample [extraction.json] [--per N] [--seed N]")


if __name__ == "__main__":
    main(sys.argv[1:])
