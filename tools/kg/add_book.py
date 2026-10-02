# Add a new book to the astrology knowledge system, or rebuild everything. Local only; the book is never modified.
#
#   .venv/bin/python tools/kg/add_book.py register "<file>.pdf" --id RATH --title "..." --author "..." \
#          --system Parashari --tier modern --language English [--translator ".."] [--edition ".."] [--year 2003]
#   .venv/bin/python tools/kg/add_book.py text RATH [--ocr en-US|hi-IN]   extract per-page text (OCR if scanned)
#   .venv/bin/python tools/kg/add_book.py chapters RATH                   detect chapters (PDF outline, else headings)
#   .venv/bin/python tools/kg/add_book.py rebuild                          index → graph → checks → retrieval test
#
# Between `chapters` and `rebuild`, write the source map (sourcemaps/<ID>.md) — see docs/ADD-A-BOOK.md.
import argparse, datetime, hashlib, json, os, re, statistics, subprocess, sys

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAT_PATH = os.path.join(WS, "knowledge", "catalog.json")
PY = os.path.join(WS, ".venv", "bin", "python")            # PyMuPDF
PYG = os.path.join(WS, ".venv-graphify", "bin", "python")  # Graphify


def load_cat():
    return json.load(open(CAT_PATH, encoding="utf-8"))


def save_cat(cat):
    cat["updated"] = datetime.date.today().isoformat()
    tmp = CAT_PATH + ".new"
    json.dump(cat, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, CAT_PATH)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def book(cat, sid):
    for b in cat["books"]:
        if b["id"] == sid:
            return b
    sys.exit(f"{sid} is not in the catalog; run `register` first")


def cmd_register(a):
    import pymupdf
    cat = load_cat()
    path = os.path.join(cat["library_root"], os.path.basename(a.file))
    if not os.path.exists(path):
        sys.exit(f"Put the PDF in {cat['library_root']} first (it is read, never changed): {path}")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,11}", a.id):
        sys.exit("--id must be 2–12 capitals/digits, e.g. BPHS1")
    h = sha256(path)
    for b in cat["books"]:
        if b["id"] == a.id:
            sys.exit(f"id {a.id} already used by {b['title']}")
        if b["sha256"] == h:
            b.setdefault("duplicates", [])
            if os.path.basename(path) not in b["duplicates"] and os.path.basename(path) != b["file"]:
                b["duplicates"].append(os.path.basename(path))
                save_cat(cat)
            sys.exit(f"Byte-identical to {b['id']} ({b['file']}); recorded as a duplicate, not added.")
    d = pymupdf.open(path)
    same_title = [b["id"] for b in cat["books"] if a.title.lower()[:20] in b["title"].lower()]
    if same_title:
        print(f"NOTE: title resembles {same_title}: if this is another edition, keep both and describe the edition.")
    cat["books"].append(dict(id=a.id, title=a.title, author=a.author, translator=a.translator or "", edition=a.edition or "",
                             year=a.year or "", language=a.language, system=a.system, tier=a.tier,
                             text_file=f"{a.id}.jsonl", text_layer="pending", page_convention="PDF p", pages=d.page_count,
                             file=os.path.basename(path), sha256=h, added=datetime.date.today().isoformat()))
    save_cat(cat)
    print(f"registered {a.id}: {d.page_count} pages, sha256 {h[:16]}…  next: text {a.id}")


def cmd_text(a):
    import pymupdf
    cat = load_cat()
    b = book(cat, a.id)
    pdf = os.path.join(cat["library_root"], b["file"])
    out = os.path.join(WS, "text", b["text_file"])
    d = pymupdf.open(pdf)
    rows = [{"src": a.id, "page": i + 1, "text": p.get_text()} for i, p in enumerate(d)]
    chars = statistics.median(len(r["text"].strip()) for r in rows)
    if a.ocr or chars < 200:
        lang = a.ocr or ("hi-IN" if b["language"].lower().startswith("hindi") else "en-US")
        print(f"text layer weak (median {chars:.0f} chars/page) → local OCR ({lang}), resumable…")
        tmp = out + ".ocr"
        subprocess.run([PY, os.path.join(WS, "tools", "ocr_pdf.py"), pdf, a.id, tmp, lang], check=True)
        rows = sorted((json.loads(l) for l in open(tmp, encoding="utf-8")), key=lambda r: r["page"])
        os.replace(tmp, out)
        b["text_layer"] = f"Apple Vision OCR {lang}"
    else:
        with open(out, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        b["text_layer"] = "pdf text"
    if a.docling:  # opt-in: layout-aware text, page-by-page fallback to the extraction above (tools/docling_text.py)
        lang = "hi-IN" if b["language"].lower().startswith("hindi") else "en-US"
        dpy = os.path.join(WS, ".venv-docling", "bin", "python")
        subprocess.run([dpy, os.path.join(WS, "tools", "docling_text.py"), pdf, a.id, out, out + ".docling", "--lang", lang],
                       check=True)
        os.replace(out + ".docling", out)
        b["text_layer"] += " + Docling (per-page fallback)"
    save_cat(cat)
    print(f"{len(rows)} pages → {out} ({b['text_layer']}); next: chapters {a.id}")


HEAD = re.compile(r"^\s*(?:CHAPTER|Chapter|ADHYAYA|Adhyaya|अध्याय)\s+([IVXLC\d]+|[०-९]+)\b.*$", re.M)


def cmd_chapters(a):
    import pymupdf
    cat = load_cat()
    b = book(cat, a.id)
    toc = pymupdf.open(os.path.join(cat["library_root"], b["file"])).get_toc()
    junk = sum(bool(re.search(r"\.(jpe?g|png|tiff?)$|_\d{3,}", t, re.I)) for _, t, _ in toc)
    if toc and junk > len(toc) / 2:
        print("PDF outline looks like scan file names — ignored")
        toc = []
    if toc:
        ch = [{"page": p, "level": lvl, "title": t.strip(), "method": "pdf-outline"} for lvl, t, p in toc if p > 0]
    else:
        ch = []
        for line in open(os.path.join(WS, "text", b["text_file"]), encoding="utf-8"):
            r = json.loads(line)
            m = HEAD.search("\n".join(r["text"].splitlines()[:6]))
            # skip front matter (a contents page lists every chapter) and keep marks in page order
            if m and r["page"] > 0.08 * b["pages"] and (not ch or r["page"] > ch[-1]["page"]):
                ch.append({"page": r["page"], "level": 1, "title": " ".join(m.group(0).split())[:100], "method": "heading-regex (heuristic)"})
    os.makedirs(os.path.join(WS, "knowledge", "chapters"), exist_ok=True)
    json.dump(ch, open(os.path.join(WS, "knowledge", "chapters", f"{a.id}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(ch)} chapter marks ({ch[0]['method'] if ch else 'none found — add them by hand if needed'}); "
          f"next: write sourcemaps/{a.id}.md (docs/ADD-A-BOOK.md), then rebuild")


def cmd_relink(a):
    """Re-match catalog entries to files by SHA-256 after renames/moves; report duplicates and unregistered PDFs."""
    cat = load_cat()
    root = cat["library_root"]
    by_hash = {}
    for f in sorted(os.listdir(root)):
        if f.lower().endswith(".pdf"):
            by_hash.setdefault(sha256(os.path.join(root, f)), []).append(f)
    for b in cat["books"]:
        files = by_hash.pop(b["sha256"], [])
        if not files:
            print(f"MISSING {b['id']}: no file with its fingerprint (was {b['file']})")
            continue
        import unicodedata
        if unicodedata.normalize("NFC", b["file"]) not in {unicodedata.normalize("NFC", f) for f in files}:
            print(f"renamed {b['id']}: {b['file']} → {files[0]}")
            b["file"] = files[0]
        b["duplicates"] = [f for f in files
                           if unicodedata.normalize("NFC", f) != unicodedata.normalize("NFC", b["file"])]
        if not b["duplicates"]:
            b.pop("duplicates")
    save_cat(cat)
    for h, files in by_hash.items():
        print(f"NOT REGISTERED: {', '.join(files)}")


def cmd_promote(a):
    """Validate a staged source map; if it passes, move it into production and rebuild + test incrementally."""
    stage = os.path.join(WS, "sourcemaps", "staging", a.name + ".md")
    r = subprocess.run([PYG, "tools/kg/validate_map.py", stage, a.pages], cwd=WS)
    if r.returncode:
        sys.exit(f"{a.name} failed validation — see validation/sourcemaps/{a.name}.md; not promoted")
    os.makedirs(os.path.join(WS, "sourcemaps", "logs"), exist_ok=True)
    os.replace(stage, os.path.join(WS, "sourcemaps", a.name + ".md"))
    if os.path.exists(stage[:-3] + ".log"):
        os.replace(stage[:-3] + ".log", os.path.join(WS, "sourcemaps", "logs", a.name + ".log"))
    run(PYG, "tools/kg/extract.py")
    run(PYG, "tools/kg/build_graph.py")
    run("python3", "validation/graph_checks.py")
    run("python3", "validation/citation_test.py", a.name.split("_part")[0])
    run("python3", "validation/retrieval_eval.py")


def run(*cmd):
    print("→", " ".join(os.path.relpath(c, WS) if os.path.isabs(c) else c for c in cmd))
    subprocess.run(list(cmd), check=True, cwd=WS)


def cmd_rebuild(a):
    run("python3", "tools/build_index.py")
    run(PYG, "tools/kg/extract.py")
    run(PYG, "tools/kg/build_graph.py")
    run("python3", "validation/graph_checks.py")
    run("python3", "validation/retrieval_eval.py")
    print("done. Review validation/*.md (integrity, OCR, duplicates, provenance, entity linking), then "
          "`python3 tools/release_skill.py` to install the updated skill.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("register")
    r.add_argument("file")
    for f in ("id", "title", "author", "language"):
        r.add_argument("--" + f, required=True)
    r.add_argument("--system", required=True, help="Parashari | Jaimini | Lal Kitab | Tajika | KP | Prashna | …")
    r.add_argument("--tier", required=True, choices=["classical", "traditional", "modern", "experimental"])
    for f in ("translator", "edition", "year"):
        r.add_argument("--" + f)
    t = sp.add_parser("text")
    t.add_argument("id")
    t.add_argument("--ocr", help="force OCR with this language, e.g. en-US or hi-IN")
    t.add_argument("--docling", action="store_true",
                   help="layout-aware re-extraction (tables, broken lines) for English books; not recommended for Hindi")
    c = sp.add_parser("chapters")
    c.add_argument("id")
    sp.add_parser("rebuild")
    sp.add_parser("relink", help="re-match catalog to renamed files by SHA-256")
    pr = sp.add_parser("promote", help="validate a staged map and move it into the knowledge system")
    pr.add_argument("name", help="e.g. BPHS_part1")
    pr.add_argument("pages", help="page range of the part, e.g. 1-120")
    a = ap.parse_args()
    {"register": cmd_register, "text": cmd_text, "chapters": cmd_chapters, "rebuild": cmd_rebuild,
     "relink": cmd_relink, "promote": cmd_promote}[a.cmd](a)


if __name__ == "__main__":
    main()
