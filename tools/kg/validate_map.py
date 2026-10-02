# Validate a staged source map before it enters the knowledge system.
# usage: .venv-graphify/bin/python tools/kg/validate_map.py sourcemaps/staging/BPHS_part1.md --pages 1-120
# Checks: completion log, tags, citations, page ranges, and a spot-check that each sampled rule's distinctive words
# appear on the page(s) it cites. Writes validation/sourcemaps/<name>.md; exit 1 if it fails the thresholds.
import json, os, random, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import extract as X

STOP = set("""which their there these those where would could should about after before other under while being
their shall will with from into when then than that this have has were been also only such very more most some
native planet planets house houses lord lords sign signs result results effect effects good evil strong weak""".split())


def words(t):
    return {w for w in re.findall(r"[a-z]{5,}", t.lower()) if w not in STOP}


def main():
    path = sys.argv[1]
    rng = next((a for a in sys.argv if re.fullmatch(r"\d+-\d+", a)), None)
    name = os.path.basename(path)[:-3]
    src = name.split("_part")[0]
    book = X.BOOKS.get(src) or sys.exit(f"unknown source id {src}")
    lo, hi = map(int, rng.split("-")) if rng else (1, book["pages"])
    lines = open(path, encoding="utf-8").read().splitlines()
    log = open(path[:-3] + ".log", encoding="utf-8").read() if os.path.exists(path[:-3] + ".log") else ""
    text = {}
    for l in open(os.path.join(X.WS, "text", book["text_file"]), encoding="utf-8"):
        r = json.loads(l)
        text[r["page"]] = r["text"]
    bl = [(n, t, h) for n, t, h in X.bullets(lines) if not h.get(2, "").startswith("1.") and len(t) >= 25]
    tagged = [b for b in bl if re.match(r"\[[^\]]+\]", b[1])]
    cited, out_of_range, foreign = [], [], []
    for n, t, h in bl:
        c = X.citations(t, src) or X.citations(h.get(max(h)) or "", src) if h else X.citations(t, src)
        if c:
            cited.append((n, t, c))
        for s2, p, _ in c:
            if s2 == src and not (lo - 15 <= p <= hi + 15):
                out_of_range.append(f"line {n}: {s2} p{p}")
            if s2 not in X.BOOKS:
                foreign.append(f"line {n}: {s2}")
    random.seed(7)
    sample = random.sample(cited, min(25, len(cited)))
    ok, bad = 0, []
    for n, t, c in sample:
        pages = {p for s2, p, _ in c if s2 == src}
        pt = " ".join(text.get(q, "") for p in pages for q in (p - 1, p, p + 1))
        body = re.sub(rf"—\s*(?:(?:{X.SRC_IDS})\s*)?pp?\.?\s?\d.*$", "", t)  # drop only the trailing citation
        hit = words(body) & words(pt)
        if len(hit) >= 2 or not pages:
            ok += 1
        else:
            bad.append(f"line {n} (p{sorted(pages)}): {body[:110]} — shared words {sorted(hit)}")
    flags = sum("❓" in t for _, t, _ in bl)
    res = {
        "complete": "COMPLETE" in log,
        "bullets": len(bl),
        "tagged %": round(100 * len(tagged) / max(1, len(bl))),
        "cited %": round(100 * len(cited) / max(1, len(bl))),
        "spot-check %": round(100 * ok / max(1, len(sample))),
        "❓ flagged": flags,
        "out of range": len(out_of_range),
    }
    passed = res["complete"] and res["tagged %"] >= 85 and res["cited %"] >= 85 and res["spot-check %"] >= 80
    os.makedirs(os.path.join(X.WS, "validation", "sourcemaps"), exist_ok=True)
    rep = [f"# Validation of {name} ({'PASS' if passed else 'FAIL'})", "", *(f"- {k}: {v}" for k, v in res.items()), "",
           "## Spot-check failures (rule words not found on the cited page ±1)", *(f"- {b}" for b in bad), "",
           "## Citations outside the part's page range", *(f"- {x}" for x in out_of_range[:50]), "",
           "## Unknown source ids", *(f"- {x}" for x in foreign[:30])]
    open(os.path.join(X.WS, "validation", "sourcemaps", name + ".md"), "w").write("\n".join(rep) + "\n")
    print(("PASS " if passed else "FAIL ") + name, res)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
