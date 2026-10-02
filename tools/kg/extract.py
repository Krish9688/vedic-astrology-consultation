# Deterministic, local extraction of the astrology library into Graphify's extraction schema.
# No LLM, no network. Reads: knowledge/catalog.json, text/*.jsonl, sourcemaps/*.md, the Lal Kitab KB v2.2
# and the skill's contradiction register. Writes: knowledge/extraction.json + validation/*.md reports.
# usage: .venv-graphify/bin/python tools/kg/extract.py
import datetime, hashlib, json, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astrology-prediction", "scripts"))  # the one vocab copy ships with the skill
import vocab

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAT = json.load(open(os.path.join(WS, "knowledge", "catalog.json"), encoding="utf-8"))
BOOKS = {b["id"]: b for b in CAT["books"]}
SRC_IDS = "|".join(sorted(list(BOOKS) + ["KB"], key=len, reverse=True))
VAL = os.path.join(WS, "validation")
KB_PATH = os.path.join(WS, "astrology-prediction", "data", "lal-kitab", "LalKitab_Shrimali_Knowledge_Base_v2.2.md")
CR_PATH = os.path.join(WS, "astrology-prediction", "references", "contradiction-register.md")
CURATION = os.path.join(WS, "knowledge", "curation", "xb_curation.json")   # manual review of the automatic disputes
SYSTEM = {"PD": "Parashari", "BJ": "Parashari", "HJH2": "Parashari", "HPA": "Parashari", "LOL": "Parashari",
          "PM2": "Prashna/Parashari", "LKS": "Lal Kitab", "LK1952": "Lal Kitab",
          "BPHS": "Parashari", "KNRT": "Parashari", "CRUX": "Parashari + Jaimini (SJC)", "PVR": "Parashari",
          "JSR": "Jaimini", "HJH1": "Parashari", "JP2": "Parashari", "SAR1": "Parashari", "NAKS": "Parashari (nakshatra)",
          "DEVA2": "Nadi"}

nodes, edges = {}, []


def mdate(path):
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def node(nid, label, ntype, source_file, loc="", ft="document", **attrs):
    if nid not in nodes:
        nodes[nid] = {"id": nid, "label": vocab_label(label), "file_type": ft, "source_file": source_file,
                      "source_location": loc, "node_type": ntype,
                      "attributes": {k: v for k, v in attrs.items() if v not in (None, "", [], {})}}
    return nid


def vocab_label(s):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= 110 else s[:107] + "…"


def edge(s, t, rel, conf="EXTRACTED", source_file="", **attrs):
    e = {"source": s, "target": t, "relation": rel, "confidence": conf, "source_file": source_file}
    e.update({k: v for k, v in attrs.items() if v not in (None, "")})
    edges.append(e)


# ---------- citations ----------
_CIT = re.compile(rf"\b({SRC_IDS})\b|\bp\.?\s?(\d{{1,4}})((?:\s*[-–]\s*\d{{1,4}})?)((?:\s*,\s*(?!p)\d{{1,4}}(?![\d.]))*)"
                  r"(?:\s*\((?:pr\.?|ed\.?)\s?([^)]{1,20})\))?")


def citations(text, default_src):
    """[(src, pdf_page, printed_or_None)] in order of appearance. KB pages are LKS pages."""
    out = []
    for seg in re.split(r"[—;|]", text):  # a source id only governs pages in its own clause
        out += _citations_segment(seg, default_src)
    return out


def _citations_segment(text, default_src):
    out, cur = [], default_src
    for m in _CIT.finditer(text):
        if m.group(1):
            cur = m.group(1)
            continue
        if not cur:
            continue
        src = "LKS" if cur == "KB" else cur
        first = int(m.group(2))
        pages = [first]
        if m.group(3):
            last = int(re.sub(r"\D", "", m.group(3)))
            if first < last <= first + 8:
                pages = list(range(first, last + 1))
        if m.group(4):
            pages += [int(x) for x in re.findall(r"\d+", m.group(4))]
        for i, p in enumerate(pages):
            out.append((src, p, m.group(5).strip() if (m.group(5) and i == 0) else None))
    return out


_VERSE = re.compile(r"\b([IVXL]{1,6})\s?[.:]\s?(\d{1,3}(?:\s?[-–]\s?\d{1,3})?)\b|\b(?:st(?:anza)?|sl(?:oka)?)\.?\s?(\d{1,3})\b")


def verses(text):
    v = []
    for m in _VERSE.finditer(text):
        v.append(f"{m.group(1)}.{m.group(2)}" if m.group(1) else f"st.{m.group(3)}")
    return sorted(set(v))


# ---------- books, authors, pages ----------
def page_id(src, p):
    return f"page:{src}:{p}"


WORDS = None


def english_words():
    global WORDS
    if WORDS is None:
        try:
            WORDS = {w.strip().lower() for w in open("/usr/share/dict/words", encoding="utf-8", errors="ignore")}
        except OSError:
            WORDS = set()
        for _, _, label in vocab.all_entities():
            WORDS.update(label.lower().split())
    return WORDS


def ocr_score(text, lang):
    """Share of tokens that look like real words (English) or Devanagari letters (Hindi). 0–1."""
    if lang.startswith("Hindi"):
        letters = [c for c in text if c.isalpha()]
        if len(letters) < 50:
            return None
        return round(sum("ऀ" <= c <= "ॿ" for c in letters) / len(letters), 3)
    toks = [t.lower() for t in re.findall(r"[A-Za-z]{3,}", text)]
    if len(toks) < 30:
        return None
    W = english_words()
    if not W:
        return None
    return round(sum(t in W or t.rstrip("s") in W for t in toks) / len(toks), 3)


PRINTED_LK = re.compile(r"पेज नंबर\s*(\d+)")
page_texts = {}  # (src, page) -> text, for dedup
page_quality = []


def add_books_and_pages():
    for b in CAT["books"]:
        src = b["id"]
        bid = node(f"book:{src}", b["title"], "Book", b["file"], ft="document", source_id=src, author=b["author"],
                   translator=b.get("translator"), edition=b["edition"], year=b.get("year"), language=b["language"],
                   system=b["system"], tier=b["tier"], sha256=b["sha256"], page_convention=b["page_convention"],
                   pages=b["pages"], text_layer=b["text_layer"])
        for role, who in (("WRITTEN_BY", b["author"]), ("TRANSLATED_BY", b.get("translator"))):
            if who:
                aid = node("person:" + re.sub(r"[^a-z0-9]+", "-", who.lower()).strip("-")[:60], who, "Person",
                           b["file"], ft="concept")
                edge(bid, aid, role, source_file=b["file"])
        for dup in b.get("duplicates", []):
            did = node(f"file:{hashlib.sha1(dup.encode()).hexdigest()[:10]}", dup, "DuplicateFile", dup,
                       sha256=b["sha256"], note="byte-identical copy (same SHA-256); not indexed separately")
            edge(did, bid, "DUPLICATE_OF", source_file=dup)
        path = os.path.join(WS, "text", b["text_file"])
        chp = os.path.join(WS, "knowledge", "chapters", f"{src}.json")
        marks = sorted((c["page"], c["title"]) for c in json.load(open(chp, encoding="utf-8"))) if os.path.exists(chp) else []
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            p, text = r["page"], r["text"]
            m = PRINTED_LK.search(text) if src == "LK1952" else None
            q = ocr_score(text, b["language"])
            words = len(text.split())
            flags = []
            if q is not None and q < (0.85 if b["language"].startswith("Hindi") else 0.6):
                flags.append("low-ocr-quality")
            if words < 15:
                flags.append("near-empty")
            pid = node(page_id(src, p), f"{src} p{p}" + (f" (pr {m.group(1)})" if m else ""), "Page", b["file"],
                       f"p{p}", book=src, chapter=next((t for q, t in reversed(marks) if q <= p), None), pdf_page=p, printed_page=m.group(1) if m else None, words=words,
                       ocr_score=q, flags=flags)
            edge(pid, bid, "PART_OF", source_file=b["file"])
            page_texts[(src, p)] = text
            page_quality.append((src, p, q, words, flags))
            for eid, n in vocab.find_entities(text).items():
                edge(pid, eid, "MENTIONS", "INFERRED", b["file"], weight=n, method="vocab-match")
            for h, _ in vocab.house_refs(text):
                edge(pid, f"house:{h}", "MENTIONS", "INFERRED", b["file"], method="house-pattern")


def add_entities():
    for eid, typ, label in vocab.all_entities():
        node(eid, label, typ, "astrology-prediction/scripts/vocab.py", ft="concept")


# ---------- rules ----------
problems = defaultdict(list)
rules = {}  # id -> (src, text)


def tier_for(tag, src):
    t = (tag or "").upper()
    if "READER NOTE" in t:
        return "synthesis"
    if "CLASSICAL" in t or t.startswith("SUTRA"):
        return "classical"
    if "TRANSLATOR" in t:
        return "traditional"
    if "SAMUDRIK" in t:
        return "traditional"
    if t.startswith("LK"):
        return "classical" if src == "LK1952" else "modern"
    if "AUTHOR" in t or "MIXED" in t or "VED" in t:
        return "modern"
    return BOOKS[src]["tier"] if src in BOOKS else "modern"


def system_for(tag, src):
    t = (tag or "").upper()
    if src in ("LKS", "LK1952") and ("VED" in t or "MIXED" in t):
        return "Vedic rule inside a Lal Kitab source"
    if "SAMUDRIK" in t:
        return "Samudrik (body signs)"
    if "JAIMINI" in t or t.startswith("SUTRA"):
        return "Jaimini"
    return SYSTEM.get(src, "")


def link_heading(rid, heading, source_file):
    """Planets/houses/topics named in the rule's own sub-heading (e.g. '3.9 Saturn in the houses')."""
    for eid in vocab.find_entities(heading):
        if eid.split(":")[0] in ("planet", "topic", "yoga", "varga", "nakshatra"):
            edge(rid, eid, "APPLIES_TO", "INFERRED", source_file, method="section-heading")
    for h, role in vocab.house_refs(heading):
        edge(rid, f"house:{h}", "APPLIES_TO", "INFERRED", source_file, method="section-heading", role=role)


def link_rule(rid, text, source_file, cites, default_src):
    for src, p, pr in cites:
        if src not in BOOKS:
            problems["unknown source id in citation"].append(f"{rid}: {src} p{p}")
            continue
        if not 1 <= p <= BOOKS[src]["pages"]:
            problems["page outside the book's range"].append(f"{rid}: {src} p{p} (book has {BOOKS[src]['pages']})")
            continue
        edge(rid, page_id(src, p), "RULE_FROM", source_file=source_file, printed_page=pr)
    if not cites:
        problems["rule without a page citation"].append(f"{rid} [{source_file}]: {text[:90]}")
    for eid in vocab.find_entities(text):
        edge(rid, eid, "APPLIES_TO", "INFERRED", source_file, method="vocab-match")
    for h, role in vocab.house_refs(text):
        edge(rid, f"house:{h}", "APPLIES_TO", "INFERRED", source_file, method="house-pattern", role=role)


def add_rule(src, text, source_file, section, kind, tag, extracted, default_src, extra=None, heading=None):
    clean = re.sub(r"\*\*|`", "", text).strip()
    rid = f"rule:{src}:{hashlib.sha1(clean.encode()).hexdigest()[:10]}"
    if rid in nodes:
        problems["exact duplicate rule text (kept once)"].append(f"{rid} [{source_file}]: {clean[:90]}")
        return rid
    cites = citations(clean, default_src)
    citation_level = "rule"
    if not cites and heading:
        cites, citation_level = citations(heading, default_src), "section heading"
    first = next(((s, p, pr) for s, p, pr in cites if s in BOOKS), None)
    loc = f"p{first[1]}" + (f" (pr {first[2]})" if first and first[2] else "") if first else ""
    flags = [f for f, rx in (("image-checked", r"image[- ]checked"), ("unverified-reading", "❓"),
                             ("deterministic-statement", r"DETERMINISTIC"), ("new-vs-kb", r"\[NEW\]")) if re.search(rx, clean)]
    body = re.sub(r"^\[[^\]]*\]\s*", "", clean) or clean  # a bullet that is only a bracketed note keeps it
    a = dict(source=src, book=BOOKS.get(first[0] if first else src, {}).get("title"), author=BOOKS.get(src, {}).get("author"),
             edition=BOOKS.get(src, {}).get("edition"), language=BOOKS.get(src, {}).get("language"),
             section=section, kind=kind, tag=tag, tier=tier_for(tag, src), system=system_for(tag, src),
             verses=verses(clean), pages=sorted({f"{s} p{p}" for s, p, _ in cites}), text=body,
             extracted_from=os.path.relpath(source_file, WS), extraction_date=extracted,
             extraction_method="page-cited paraphrase written by an AI reader of the full book (source map), parsed deterministically",
             confidence="EXTRACTED" if cites else "AMBIGUOUS", flags=flags, citation_level=citation_level if cites else None,
             do_not_forecast=True if kind == "harmful-statement" or "deterministic-statement" in flags else None)
    if extra:
        a.update(extra)
    a["heading"] = heading
    a["evidence_role"] = evidence_role(a)
    node(rid, f"[{src}] {body}", "Rule", BOOKS.get(src, {}).get("file", source_file), loc, **a)
    rules[rid] = (src, body)
    link_rule(rid, clean, BOOKS.get(src, {}).get("file", source_file), cites, default_src)
    if heading:
        link_heading(rid, heading, BOOKS.get(src, {}).get("file", source_file))
    return rid


def evidence_role(a):
    """How a rule may be used in a reading (answers "is this used directly or only as support?")."""
    if a.get("do_not_forecast"):
        return "doctrine only — never a forecast"
    if a.get("tier") == "synthesis":
        return "supporting inference (not the author's statement)"
    return {"topic-rule": "direct rule", "timing-rule": "direct rule (timing)", "yoga": "direct rule (yoga)",
            "lk-planet-in-house": "direct rule (Lal Kitab)", "kb-register": "direct rule (Lal Kitab KB)",
            "kb-section": "direct rule (Lal Kitab KB)", "method": "method principle (how to weigh/judge)",
            "worked-example": "illustration (worked case, hindsight)", "contradiction-note": "dispute note",
            "limits": "scope note", "page-notes": "context note", "notes": "context note"}.get(a.get("kind"), "context note")


KIND = {"2": "method", "3": "topic-rule", "4": "timing-rule", "5": "yoga", "6": "worked-example",
        "7": "contradiction-note", "8": "harmful-statement", "9": "limits"}


def bullets(lines):
    """Yield (start_line, text, headings) for each top-level '- ' bullet with its continuation lines."""
    heads, cur, start = {}, None, 0
    for i, ln in enumerate(lines + ["# END"]):
        # "**Saturn H1 (p665–669)**" or "**Jupiter H7** — p341–345 …" act as sub-headings
        bold = re.fullmatch(r"\*\*([^*]{3,120})\*\*(\s*[—:–-].*)?\s*", ln)
        if ln.startswith("#") or bold:
            if cur:
                yield start, " ".join(cur), dict(heads)
                cur = None
            lvl = 5 if bold else len(ln) - len(ln.lstrip("#"))
            heads = {k: v for k, v in heads.items() if k < lvl}
            heads[lvl] = (bold.group(1) + (bold.group(2) or "")).strip() if bold else ln.lstrip("#").strip()
        elif ln.startswith("- "):
            if cur:
                yield start, " ".join(cur), dict(heads)
            cur, start = [ln[2:].strip()], i + 1
        elif cur is not None and (ln.startswith((" ", "\t")) or (ln.strip() and ln.lstrip().startswith("—"))):
            cur.append(ln.strip().lstrip("- ").strip())
        elif cur is not None and ln.strip() and not ln.startswith(("|", ">")):
            yield start, " ".join(cur), dict(heads)
            cur = None


def add_sourcemaps():
    d = os.path.join(WS, "sourcemaps")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md") or f.startswith("BRIEF"):
            continue
        src = f[:-3].split("_part")[0].split("_")[0] if not f.startswith("LK1952") else "LK1952"
        path = os.path.join(d, f)
        lines = open(path, encoding="utf-8").read().splitlines()
        for ln_no, text, heads in bullets(lines):
            sec = heads.get(2, "")
            if sec.startswith("1.") or len(text) < 25:
                continue  # header metadata is carried by the Book node
            m = re.match(r"(\d+)\.", sec)
            kind = KIND.get(m.group(1), "notes") if m else ("page-notes" if sec.lower().startswith("appendix") else "notes")
            tag = re.match(r"\[([^\]]+)\]", text)
            section = " › ".join(v for k, v in sorted(heads.items()) if k >= 2)
            deepest = heads[max(heads)] if heads and max(heads) >= 3 else None
            add_rule(src, text, path, section, kind, tag.group(1) if tag else None, mdate(path), src,
                     {"map_line": f"{f}:{ln_no}"}, heading=deepest)


# ---------- Lal Kitab KB ----------
def table_rows(lines, prefix):
    for ln in lines:
        if ln.startswith("| " + prefix):
            yield [c.strip() for c in ln.strip().strip("|").split("|")]


def add_kb():
    lines = open(KB_PATH, encoding="utf-8").read().splitlines()
    date = "2026-09-21"
    for row in table_rows(lines, "R"):
        if len(row) >= 5 and re.fullmatch(r"R\d+", row[0]):
            pages = ", ".join("p" + x.strip() for x in re.split(r",\s*", row[3]) if re.match(r"\d", x.strip()))
            add_rule("LKS", f"[{row[2]}] KB {row[0]}: {row[1]} — {pages} — status {row[4]}", KB_PATH,
                           "KB Part 0.2 Validation Register", "kb-register", row[2], date, "LKS",
                           {"kb_id": row[0], "validation_status": row[4], "derived_via": "KB v2.2"})
    # A5 contradictions X1..X23
    for row in table_rows(lines, "X"):
        if len(row) >= 7 and re.fullmatch(r"X\d+", row[0]):
            add_contradiction(f"KB-{row[0]}", row[1], row[2], row[3], row[4], row[5], KB_PATH, "LKS", date)
    # B8 planet-in-house entries and general bullets of Part B
    planet = None
    for ln_no, text, heads in bullets(lines):
        h3, h4 = heads.get(3, ""), heads.get(4, "")
        if not h3.startswith("B"):
            continue
        pm = re.match(r"(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b", h4)
        planet = pm.group(1) if (h3.startswith("B8") and pm) else None
        hm = re.match(r"\*\*H(\d{1,2})\*\*\s*\[p(\d+)\]", text)
        if planet and hm:
            body = text[hm.end():].lstrip(" :(").strip()
            add_rule("LKS", f"[LK] {planet} in house {hm.group(1)} (Lal Kitab, Shrimali): {body} — p{hm.group(2)}", KB_PATH,
                     f"KB {h3} › {h4}", "lk-planet-in-house", "LK", date, "LKS",
                     {"kb_id": f"B8-{planet}-H{hm.group(1)}", "derived_via": "KB v2.2", "lk_planet": planet,
                      "lk_house": int(hm.group(1)), "format": "result | adverse conditions | remedies"})
        else:
            sec_pages = re.findall(r"p(\d+)", h3 + " " + h4)[:1]
            add_rule("LKS", text + ("" if re.search(r"\bp\d", text) or not sec_pages else f" — p{sec_pages[0]}"),
                     KB_PATH, f"KB {h3}" + (f" › {h4}" if h4 else ""), "kb-section", "LK", date, "LKS",
                     {"derived_via": "KB v2.2", "citation_level": "section" if not re.search(r"\bp\d", text) else "rule"})


def add_contradiction(cid, topic, side_a, side_b, klass, default, path, default_src, date):
    nid = node(f"contradiction:{cid}", f"{cid}: {topic}", "Contradiction", path, cid, ft="rationale", topic=topic,
               classification=klass, working_default=default, extracted_from=os.path.relpath(path, WS),
               extraction_date=date, note="curated register entry; both positions are preserved, none is deleted")
    pos = []
    for side, txt in (("A", side_a), ("B", side_b)):
        pid = node(f"position:{cid}:{side}", f"{cid} position {side}: {txt}", "Position", path, cid, ft="rationale",
                   text=re.sub(r"\*\*", "", txt), side=side, pages=sorted({f"{s} p{p}" for s, p, _ in citations(txt, default_src)}))
        edge(nid, pid, "HAS_POSITION", source_file=path)
        link_rule(pid, txt, path, citations(txt, default_src), default_src)
        for x in re.findall(r"\bX(\d{1,2})\b", txt):
            edge(nid, f"contradiction:KB-X{x}", "REFERS_TO", source_file=path)
        pos.append(pid)
    edge(pos[0], pos[1], "CONTRADICTS", source_file=path, classification=klass)
    for eid in vocab.find_entities(topic):
        edge(nid, eid, "APPLIES_TO", "INFERRED", path, method="vocab-match")


def add_register():
    lines = open(CR_PATH, encoding="utf-8").read().splitlines()
    for row in table_rows(lines, "CR-"):
        if len(row) >= 6:
            add_contradiction(row[0], row[1], row[2], row[3], row[4], row[5], CR_PATH, None, mdate(CR_PATH))
        elif len(row) >= 4:
            add_contradiction(row[0], row[1], row[2], row[3], "", row[4] if len(row) > 4 else "", CR_PATH, None, mdate(CR_PATH))


def add_crossbook_disputes():
    """Source-map §7 notes that cite two or more different books become (uncurated) dispute nodes: one position per
    side, each linked to its own pages. Split at the first " vs " when present; never merged or resolved."""
    cur_file = json.load(open(CURATION)) if os.path.exists(CURATION) else {"disputes": []}
    curated = {x["id"]: x for x in cur_file["disputes"]}
    curation_date = cur_file.get("curated", "")
    for rid, (src, body) in list(rules.items()):
        a = nodes[rid]["attributes"]
        if a.get("kind") != "contradiction-note":
            continue
        cites = citations(body, src)
        books = {s for s, _, _ in cites if s in BOOKS}
        if len(books) < 2 or src not in books:
            continue
        if re.search(r"\bagree|\bconsistent with|\bmatches\b|no dispute", body, re.I) and not re.search(
                r"disagree|differ|dispute:|contradict|oppos|\bvs\b|\bbut\b", body, re.I):
            for s2, p, pr in cites:  # an agreement note: the other book's pages SUPPORT this rule
                if s2 != src and 1 <= p <= BOOKS[s2]["pages"]:
                    edge(rid, page_id(s2, p), "SUPPORTED_BY", "INFERRED", nodes[rid]["source_file"],
                         method="agreement noted in a source map", printed_page=pr)
            continue
        cid = "XB-" + rid.split(":")[-1]
        cur = curated.get(cid, {})
        if cur.get("duplicate_of") and f"contradiction:{cur['duplicate_of']}" in nodes:
            edge(rid, f"contradiction:{cur['duplicate_of']}", "DISCUSSED_IN", source_file=nodes[rid]["source_file"],
                 method="curated: same dispute as the register entry")
            continue
        klass = (f"{cur['class']} (curated {curation_date})" + (f" — {cur['note']}" if cur.get("note") else "")
                 if cur else "uncurated (from a source map; review before relying)")
        left, right = (body.split(" vs ", 1) + [""])[:2] if " vs " in body else (body, "")
        nid = node(f"contradiction:{cid}", f"{cid}: {body[:90]}", "Contradiction", nodes[rid]["source_file"], cid,
                   ft="rationale", topic=body[:160], classification=klass,
                   working_default="", extracted_from=a.get("extracted_from"), extraction_date=a.get("extraction_date"),
                   note="automatic cross-book dispute from a source map §7; both sides preserved")
        pos = []
        for side, txt, want in (("A", left, {src}), ("B", right or body, books - {src})):
            pid = node(f"position:{cid}:{side}", f"{cid} position {side}", "Position", nodes[rid]["source_file"], cid,
                       ft="rationale", text=txt.strip(), side=side, pages=sorted({f"{s} p{p}" for s, p, _ in cites if s in want}))
            edge(nid, pid, "HAS_POSITION", source_file=nodes[rid]["source_file"])
            for s2, p, pr in cites:
                if s2 in want and 1 <= p <= BOOKS[s2]["pages"]:
                    edge(pid, page_id(s2, p), "RULE_FROM", source_file=nodes[rid]["source_file"], printed_page=pr)
            for eid in vocab.find_entities(body):
                edge(pid, eid, "APPLIES_TO", "INFERRED", nodes[rid]["source_file"], method="vocab-match")
            pos.append(pid)
        if cur.get("class") != "false_positive":
            edge(pos[0], pos[1], "CONTRADICTS", source_file=nodes[rid]["source_file"],
                 classification=cur.get("class", "uncurated"))
        edge(rid, nid, "DISCUSSED_IN", source_file=nodes[rid]["source_file"], method="same note")


def link_rules_to_contradictions():
    """Rule cites a page that a contradiction position cites and shares a non-topic entity → DISCUSSED_IN."""
    by_page = defaultdict(set)
    ents = defaultdict(set)
    for e in edges:
        if e["relation"] == "RULE_FROM":
            by_page[e["target"]].add(e["source"])
        elif e["relation"] == "APPLIES_TO" and not e["target"].startswith("topic:"):
            ents[e["source"]].add(e["target"])
    seen = set()
    for pid in [n for n in nodes if n.startswith("position:")]:
        cid = "contradiction:" + pid.split(":")[1]
        for page in [e["target"] for e in edges if e["source"] == pid and e["relation"] == "RULE_FROM"]:
            for rid in by_page[page]:
                if rid.startswith("rule:") and ents[rid] & ents[pid] and (rid, cid) not in seen:
                    seen.add((rid, cid))
                    edge(rid, cid, "DISCUSSED_IN", "INFERRED", nodes[rid]["source_file"], method="shared page + entity")


# ---------- duplicates ----------
def near_duplicate_pages(threshold=0.6):
    sh = {}
    for k, t in page_texts.items():
        w = re.findall(r"\w+", t.lower())
        if len(w) >= 40:
            sh[k] = {hash(" ".join(w[i:i + 5])) for i in range(len(w) - 4)}
    inv = defaultdict(list)
    for k, s in sh.items():
        for h in s:
            inv[h].append(k)
    overlap = Counter()
    for ks in inv.values():
        if 1 < len(ks) <= 20:
            for i in range(len(ks)):
                for j in range(i + 1, len(ks)):
                    overlap[(ks[i], ks[j])] += 1
    out = []
    for (a, b), n in overlap.items():
        j = n / len(sh[a] | sh[b])
        if j >= threshold:
            out.append((round(j, 2), a, b))
            edge(page_id(*a), page_id(*b), "NEAR_DUPLICATE_OF", "AMBIGUOUS", BOOKS[a[0]]["file"], jaccard=round(j, 2))
    return sorted(out, reverse=True)


def similar_rules(same_src_cut=90, cross_cut=85):
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        return []
    ids = list(rules)
    # compare wording only: citations and digits removed (tables of house numbers are not duplicates)
    texts = [re.sub(r"[\d\W_]+", " ", re.sub(rf"\s*—\s*(?:(?:{SRC_IDS})\s*)?pp?\.?\s?\d.*$", "", rules[i][1])).lower().strip()
             for i in ids]
    M = process.cdist(texts, texts, scorer=fuzz.token_sort_ratio, score_cutoff=min(same_src_cut, cross_cut), workers=-1)
    out = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            s = M[i][j]
            if not s or len(texts[i].split()) < 6 or len(texts[j].split()) < 6:
                continue
            same = rules[ids[i]][0] == rules[ids[j]][0]
            if s >= (same_src_cut if same else cross_cut):
                out.append((round(float(s)), ids[i], ids[j], same))
                edge(ids[i], ids[j], "SIMILAR_TO", "AMBIGUOUS", "", score=round(float(s)), same_source=same,
                     note="candidate duplicate/parallel — never merged automatically")
    return sorted(out, reverse=True)


# ---------- reports ----------
def write_reports(dup_pages, sim):
    os.makedirs(VAL, exist_ok=True)
    today = datetime.date.today().isoformat()
    # library integrity
    root = CAT["library_root"]
    import glob
    hashes = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(root, "*.pdf"))):
        h = hashlib.sha256()
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        hashes[h.hexdigest()].append(os.path.basename(f))
    import unicodedata
    nfc = lambda x: unicodedata.normalize("NFC", x)  # macOS may store accented names decomposed (NFD)
    registered = {nfc(b["file"]): b for b in CAT["books"]}
    dup_files = {nfc(d) for b in CAT["books"] for d in b.get("duplicates", [])}
    L = [f"# Library integrity check ({today})", "", "| File | Status |", "|---|---|"]
    for h, fs in hashes.items():
        for f in fs:
            f = nfc(f)
            b = registered.get(f)
            if b:
                L.append(f"| {f} | {'OK ' + b['id'] if b['sha256'] == h else '**CHANGED since cataloguing — investigate**'} |")
            elif f in dup_files:
                L.append(f"| {f} | byte-identical duplicate of another file (same SHA-256); not indexed |")
            else:
                L.append(f"| {f} | **not in catalog** — run tools/kg/add_book.py |")
    for f, b in registered.items():
        if not os.path.exists(os.path.join(root, b["file"])):
            L.append(f"| {f} | **MISSING from the library folder** |")
    open(os.path.join(VAL, "library_integrity.md"), "w").write("\n".join(L) + "\n")
    # OCR quality
    by = defaultdict(list)
    for src, p, q, w, fl in page_quality:
        by[src].append((p, q, fl))
    L = [f"# OCR / text-layer quality ({today})", "",
         "Score = share of tokens that are dictionary words (English) or share of letters in Devanagari (Hindi).",
         "Flag thresholds: English < 0.60, Hindi < 0.85. A flagged page should be image-checked before its wording is relied on.", "",
         "| Book | Pages | Scored | Median | Flagged low | Near-empty |", "|---|---|---|---|---|---|"]
    for src, rows in by.items():
        qs = sorted(q for _, q, _ in rows if q is not None)
        low = [p for p, _, fl in rows if "low-ocr-quality" in fl]
        L.append(f"| {src} | {len(rows)} | {len(qs)} | {qs[len(qs)//2] if qs else '—'} | {len(low)} | "
                 f"{sum('near-empty' in fl for _, _, fl in rows)} |")
    L += ["", "## Flagged pages", ""]
    for src, rows in by.items():
        low = [p for p, _, fl in rows if "low-ocr-quality" in fl]
        if low:
            L.append(f"- **{src}**: " + ", ".join(map(str, low)))
    open(os.path.join(VAL, "ocr_quality.md"), "w").write("\n".join(L) + "\n")
    # duplicates
    L = [f"# Duplicate detection ({today})", "", "Nothing is merged or deleted automatically; these are review lists.", "",
         "## Byte-identical book files", ""]
    L += [f"- {' = '.join(fs)}" for fs in hashes.values() if len(fs) > 1] or ["- none"]
    L += ["", f"## Near-duplicate pages (5-word shingle Jaccard ≥ 0.6): {len(dup_pages)}", ""]
    L += [f"- {a[0]} p{a[1]} ≈ {b[0]} p{b[1]} (J={j})" for j, a, b in dup_pages[:200]]
    same = [x for x in sim if x[3]]
    cross = [x for x in sim if not x[3]]
    L += ["", f"## Near-identical rules within one source (token-sort ratio ≥ 90): {len(same)}", "",
          "Usually the same doctrine restated in two chapters, or a KB register row and a KB section bullet saying the same thing.", ""]
    L += [f"- {s}: `{a}` ≈ `{b}` — {nodes[a]['attributes']['text'][:80]} || {nodes[b]['attributes']['text'][:80]}" for s, a, b, _ in same[:300]]
    L += ["", f"## Similar rules across different sources (≥ 85): {len(cross)}", "",
          "Parallel statements. Treat as *possible* independent support only after reading both; never merge.", ""]
    L += [f"- {s}: `{a}` ≈ `{b}` — {nodes[a]['attributes']['text'][:80]} || {nodes[b]['attributes']['text'][:80]}" for s, a, b, _ in cross[:300]]
    L += ["", "## Exact duplicate rule texts (kept once)", ""] + [f"- {x}" for x in problems.pop("exact duplicate rule text (kept once)", [])]
    open(os.path.join(VAL, "duplicates.md"), "w").write("\n".join(L) + "\n")
    # provenance
    n_rules = [n for n in nodes.values() if n["node_type"] == "Rule"]
    tiers = Counter(n["attributes"].get("tier") for n in n_rules)
    per = Counter(n["attributes"].get("source") for n in n_rules)
    L = [f"# Provenance check ({today})", "", f"Rules: {len(n_rules)}; with ≥1 valid page citation: "
         f"{sum(1 for n in n_rules if n['attributes'].get('confidence') == 'EXTRACTED')}", "",
         "By source: " + ", ".join(f"{k} {v}" for k, v in sorted(per.items())), "",
         "By tier: " + ", ".join(f"{k} {v}" for k, v in tiers.most_common()), ""]
    for k, v in problems.items():
        L += [f"## {k}: {len(v)}", ""] + [f"- {x}" for x in v[:150]] + [""]
    open(os.path.join(VAL, "provenance.md"), "w").write("\n".join(L) + "\n")
    # entity-linking review: ambiguous vocabulary hits with sample contexts
    amb = {"sign:cancer": r"cancer", "nakshatra:mula": r"m[uo]o?la", "varga:d2": r"hora", "technique:dignity-debilitation": r"\bfall\b",
           "topic:fame-status": r"power|status", "lk:rin-ancestral-debt": r"\brin\b", "technique:arudha": r"\bpada\b",
           "technique:ashtakavarga": r"bindus?", "nakshatra:hasta": r"hasta", "technique:combustion": r"\basta"}
    L = [f"# Entity-linking review ({today})", "",
         "Vocabulary words that can mean something else. Each shows the number of rules linked and three contexts.",
         "If a sense is wrong too often, tighten its pattern in astrology-prediction/scripts/vocab.py and rebuild.", ""]
    for eid, rx in amb.items():
        linked = [e["source"] for e in edges if e["target"] == eid and e["relation"] == "APPLIES_TO" and e["source"].startswith("rule:")]
        L.append(f"## {eid} — {len(linked)} rules")
        for rid in linked[:3]:
            t = nodes[rid]["attributes"]["text"]
            m = re.search(rx, t, re.I)
            if m:
                L.append(f"- …{t[max(0, m.start()-60):m.end()+60]}…")
        L.append("")
    open(os.path.join(VAL, "entity_linking_review.md"), "w").write("\n".join(L) + "\n")


def merge_parallel(es):
    """One edge per (source, target, relation): Graphify's graph keeps a single edge per pair, so merge first
    (roles become a list, weights add up, the first printed page wins) instead of silently losing attributes."""
    merged = {}
    for e in es:
        k = (e["source"], e["target"], e["relation"])
        if k not in merged:
            merged[k] = dict(e)
            if "role" in e:
                merged[k]["role"] = [e["role"]]
            continue
        m = merged[k]
        if "role" in e and e["role"] not in m.setdefault("role", []):
            m["role"].append(e["role"])
        if "weight" in e:
            m["weight"] = m.get("weight", 0) + e["weight"]
        for f in ("printed_page", "method"):
            if e.get(f) and not m.get(f):
                m[f] = e[f]
    for m in merged.values():
        if isinstance(m.get("role"), list):
            m["role"] = "+".join(sorted(m["role"]))
    return list(merged.values())


def main():
    add_entities()
    add_books_and_pages()
    add_sourcemaps()
    add_kb()
    add_register()
    add_crossbook_disputes()
    link_rules_to_contradictions()
    dup_pages = near_duplicate_pages()
    sim = similar_rules()
    ids = set(nodes)
    dangling = [e for e in edges if e["source"] not in ids or e["target"] not in ids]
    for e in dangling:
        problems["edge to a missing node (dropped)"].append(f"{e['source']} -{e['relation']}-> {e['target']}")
    keep = merge_parallel([e for e in edges if e["source"] in ids and e["target"] in ids])
    write_reports(dup_pages, sim)
    out = {"nodes": list(nodes.values()), "edges": keep, "hyperedges": [], "input_tokens": 0, "output_tokens": 0,
           "meta": {"built": datetime.datetime.now().isoformat(timespec="seconds"), "catalog_version": CAT["version"]}}
    path = os.path.join(WS, "knowledge", "extraction.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    c = Counter(n["node_type"] for n in nodes.values())
    print(f"nodes {len(nodes)} {dict(c)}\nedges {len(keep)} {dict(Counter(e['relation'] for e in keep))}\n"
          f"near-duplicate pages {len(dup_pages)}; similar rules {len(sim)}; dropped edges {len(dangling)}\n→ {path}")


if __name__ == "__main__":
    main()
