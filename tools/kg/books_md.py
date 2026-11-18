# Private Markdown copy of every extracted book, one folder per book, one file per chapter, with page markers.
# Reads knowledge/catalog.json, text/<ID>.jsonl and knowledge/chapters/<ID>.json; writes books-md/ (PRIVATE: the text is
# copyrighted; the folder is never committed or exported). Text is kept as extracted; the build is idempotent.
#
#   python3 tools/kg/books_md.py build [ID ...]     all books with extracted text, or the named ones
#   python3 tools/kg/books_md.py --selftest
import argparse, json, os, re, shutil, tempfile

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JUNK = re.compile(r"^\s*(page|p\.?)\s*\d+\s*$", re.I)    # PDF outlines that list every page are not chapters
FIXED, MAXP = 40, 80                                       # no chapter data / chapter longer than MAXP pages: parts of FIXED


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40] or "section"


def read_pages(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    return sorted(rows, key=lambda r: r["page"])


def segments(chs, nums):
    """([(title, first_page, last_page)], note, sub_headings) covering nums, the sorted page numbers."""
    chs = [c for c in chs if not JUNK.match(c["title"]) and nums[0] <= c["page"] <= nums[-1]]
    tops = []
    if chs:
        lv = min(c["level"] for c in chs)
        for c in sorted((c for c in chs if c["level"] == lv), key=lambda c: c["page"]):
            if not tops or c["page"] > tops[-1]["page"]:
                tops.append(c)
    if len(tops) < 2:
        segs = [(f"Pages {nums[i]}-{nums[min(i + FIXED, len(nums)) - 1]}", nums[i], nums[min(i + FIXED, len(nums)) - 1])
                for i in range(0, len(nums), FIXED)]
        return segs, f"no usable chapter data: split every {FIXED} pages", []
    segs = [("Front matter", nums[0], tops[0]["page"] - 1)] if tops[0]["page"] > nums[0] else []
    for i, c in enumerate(tops):
        end = tops[i + 1]["page"] - 1 if i + 1 < len(tops) else nums[-1]
        inside = [p for p in nums if c["page"] <= p <= end]
        title = " ".join(c["title"].split())
        if len(inside) > MAXP:   # long chapter: parts, so no file is huge
            for k in range(0, len(inside), FIXED):
                part = inside[k:k + FIXED]
                segs.append((f"{title} (part {k // FIXED + 1})", part[0], part[-1]))
        else:
            segs.append((title, c["page"], end))
    subs = [c for c in chs if c["level"] > lv]
    return segs, "chapters from " + (chs[0].get("method") or "chapter data"), subs


def marker(b, r):
    n = r["page"]
    if b["page_convention"].startswith("epub"):
        t = f": {r['title']}" if r.get("title") else ""
        return f"<!-- section {n} -->\n**[section {n}{t}]**"
    m = re.search(r"printed\s*([=≈])\s*PDF\s*[−-]\s*(\d+)", b["page_convention"])
    pr = f" (printed {'~' if m.group(1) == '≈' else ''}{n - int(m.group(2))})" if m and n > int(m.group(2)) else ""
    return f"<!-- p. {n} -->\n**[p. {n}{pr}]**"


def quality(b, rows):
    layer = b.get("text_layer", "")
    if layer.startswith("pdf text +"):
        return "text+OCR"   # text layer, OCR only on pages that had none
    if "ocr" in layer.lower() or any(r.get("ocr") for r in rows):
        return "OCR"
    return "partial" if sum(len(r["text"].strip()) < 50 for r in rows) > 0.15 * len(rows) else "text"


def build_book(b, ws, out):
    tpath = os.path.join(ws, "text", b["text_file"])
    if not os.path.exists(tpath):
        return None
    rows = read_pages(tpath)
    nums = [r["page"] for r in rows]
    cpath = os.path.join(ws, "knowledge", "chapters", b["id"] + ".json")
    chs = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else []
    segs, note, subs = segments(chs, nums)
    d = os.path.join(out, b["id"])
    os.makedirs(d, exist_ok=True)
    width = max(2, len(str(len(segs))))
    unit = "sections" if b["page_convention"].startswith("epub") else "pages"
    written, lines, size = set(), [], 0
    for i, (title, a, z) in enumerate(segs, 1):
        name = f"{i:0{width}d}-{slug(title)}.md"
        body = [r for r in rows if a <= r["page"] <= z]
        if not body:
            continue
        text = f"# {b['title']}: {title}\n\n*{unit.capitalize()} {body[0]['page']}-{body[-1]['page']} ({b['page_convention']})*\n\n"
        text += "\n\n".join(f"{marker(b, r)}\n\n{r['text'].rstrip()}" for r in body) + "\n"
        open(os.path.join(d, name), "w", encoding="utf-8").write(text)
        written.add(name)
        size += len(text.encode("utf-8"))
        lines.append(f"- [{title}]({name}) ({unit} {body[0]['page']}-{body[-1]['page']})")
        lines += [f"  - {' '.join(s['title'].split())} (p. {s['page']})" for s in subs if body[0]["page"] <= s["page"] <= body[-1]["page"]]
    for f in os.listdir(d):   # generated files only: drop chapter files an earlier, different split left behind
        if re.fullmatch(r"\d+-.*\.md", f) and f not in written:
            os.remove(os.path.join(d, f))
    q = quality(b, rows)
    fm = [("id", b["id"]), ("title", b["title"]), ("author", b["author"]), ("translator", b.get("translator", "")),
          ("edition", b.get("edition", "")), ("year", b.get("year", "")), ("language", b["language"]), ("system", b["system"]),
          ("tier", b["tier"]), ("page_convention", b["page_convention"]), ("source_file", b["file"]),
          ("sha256_12", b.get("sha256", "")[:12]), ("text_source", f"text/{b['text_file']} ({b.get('text_layer', '')}; {q})"),
          ("pages", len(rows)), ("chapter_split", note)]
    idx = "---\n" + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fm) + "\n---\n\n"
    idx += f"# {b['title']}\n\nPrivate Markdown copy (copyrighted text, never commit or export). Chapters ({note}):\n\n" + "\n".join(lines) + "\n"
    open(os.path.join(d, "index.md"), "w", encoding="utf-8").write(idx)
    return dict(id=b["id"], files=len(written) + 1, pages=len(rows), bytes=size + len(idx.encode("utf-8")), quality=q, note=note)


README = """# books-md: the library as Markdown (PRIVATE)

One folder per book, one file per chapter, every page marked. Read the relevant chapter file instead of opening the PDF.

**Privacy rule.** This folder holds copyrighted book text. It lives only in the private workspace (`_skill_workspace/books-md/`).
It is never committed, never exported to `astrology-consultation/` or `vedic-astrology-consultation/`, never pasted into
reports beyond a few words. Regenerate it, do not copy it: `python3 tools/kg/books_md.py build`.

## How to find things
- By book: `<ID>/index.md` (front matter: title, author, edition, page convention, source file; then the chapter list
  with page ranges linking to chapter files). Book ids are in the table below and in `knowledge/catalog.json`.
- By chapter: `<ID>/NN-<chapter-slug>.md`. Books without chapter data are cut every 40 pages (the index says so).
- By page: every page starts with `<!-- p. 123 -->` and a visible `**[p. 123]**` (PDF page; `printed N` is added where the
  catalog records a fixed offset). EPUB books use `<!-- section 3 -->`: spine sections in reading order.
- Search: `grep -n "<!-- p. 123 -->" <ID>/*.md`, `grep -niE "saturn.*seventh" <ID>/*.md`, or search the whole folder
  with your tool's recursive option. The ranked full-text search over the same text is `astrology-prediction/scripts/search.py`.
- Text is exactly as extracted (OCR noise and hyphenated line breaks included); check page quality before quoting.

## Books
| id | title | author | system | tier | language | pages | text | index |
|---|---|---|---|---|---|---|---|---|
"""


def build(ids, ws=WS, out=None):
    out = out or os.path.join(ws, "books-md")
    cat = json.load(open(os.path.join(ws, "knowledge", "catalog.json"), encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    res = [r for b in cat["books"] if not ids or b["id"] in ids for r in [build_book(b, ws, out)] if r]
    q = {r["id"]: r["quality"] for r in res}

    def cell(s):
        return str(s).replace("|", "/")
    # the table lists every book that has a folder (also those built in an earlier run)
    rows = [f"| {b['id']} | {cell(b['title'])} | {cell(b['author'])} | {cell(b['system'])} | {b['tier']} | {cell(b['language'])} | "
            f"{b['pages']} | {q.get(b['id']) or 'see index'} | [{b['id']}/index.md]({b['id']}/index.md) |"
            for b in cat["books"] if os.path.exists(os.path.join(out, b["id"], "index.md"))]
    open(os.path.join(out, "README.md"), "w", encoding="utf-8").write(README + "\n".join(rows) + "\n")
    return res


def selftest():
    w = tempfile.mkdtemp()
    for d in ("knowledge/chapters", "text"):
        os.makedirs(os.path.join(w, d))
    b = dict(id="TST", title="Test Book", author="A. Author", system="Parashari", tier="modern", language="English", pages=3,
             file="t.pdf", sha256="ab" * 32, text_file="TST.jsonl", text_layer="pdf text", page_convention="PDF p; printed = PDF − 1")
    json.dump(dict(books=[b]), open(os.path.join(w, "knowledge/catalog.json"), "w"))
    json.dump([dict(page=1, level=1, title="One"), dict(page=3, level=1, title="Two"), dict(page=2, level=2, title="Sub")],
              open(os.path.join(w, "knowledge/chapters/TST.json"), "w"))
    with open(os.path.join(w, "text/TST.jsonl"), "w") as f:
        for n in (3, 1, 2):
            f.write(json.dumps(dict(src="TST", page=n, text=f"fake page {n} " * 30)) + "\n")
    res = build([], w)
    assert res[0]["pages"] == 3 and res[0]["files"] == 3, res
    c = open(os.path.join(w, "books-md/TST/01-one.md")).read()
    assert "<!-- p. 1 -->" in c and "**[p. 2 (printed 1)]**" in c and "<!-- p. 3 -->" not in c, c
    assert "<!-- p. 3 -->" in open(os.path.join(w, "books-md/TST/02-two.md")).read()
    idx = open(os.path.join(w, "books-md/TST/index.md")).read()
    assert "Sub (p. 2)" in idx and "(01-one.md)" in idx
    assert "TST/index.md" in open(os.path.join(w, "books-md/README.md")).read()
    build([], w)
    assert idx == open(os.path.join(w, "books-md/TST/index.md")).read()   # idempotent
    shutil.rmtree(w)
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    sp = ap.add_subparsers(dest="cmd")
    bp = sp.add_parser("build")
    bp.add_argument("ids", nargs="*")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.cmd == "build":
        tot = 0
        for r in build(a.ids):
            tot += r["bytes"]
            print(f"{r['id']:10} files {r['files']:4} pages {r['pages']:5} {r['bytes'] / 1e6:6.2f} MB  {r['quality']:8} {r['note']}")
        print(f"total {tot / 1e6:.1f} MB")
    else:
        ap.print_help()
