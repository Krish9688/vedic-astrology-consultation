# Build the local full-text index of the astrology library (stdlib sqlite3 FTS5 only).
# One row per PDF page; provenance = source id + 1-based PDF page (+ printed page where detectable).
# usage: python3 build_index.py            -> writes ../index/library.sqlite
import json, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = os.path.join(HERE, "..", "text")
DB = os.path.join(HERE, "..", "index", "library.sqlite")

# Sources come from knowledge/catalog.json (the one list of books); tuple = (text file, author, title, tradition, text layer).
_CAT = json.load(open(os.path.join(HERE, "..", "knowledge", "catalog.json"), encoding="utf-8"))
SOURCES = {b["id"]: (b["text_file"], b["author"] + (f" (tr. {b['translator']})" if b.get("translator") else ""),
                     b["title"], f"{b['system']} ({b['tier']})", b["text_layer"]) for b in _CAT["books"]}
PRINTED = re.compile(r"पेज नंबर\s*(\d+)")


def pages(src):
    for line in open(os.path.join(TEXT, SOURCES[src][0]), encoding="utf-8"):
        r = json.loads(line)
        m = PRINTED.search(r["text"])
        yield src, r["page"], (m.group(1) if m else None), r["text"]


def build():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    c = sqlite3.connect(DB)
    c.execute("create table sources(id primary key, file, author, title, tradition, text_layer)")
    c.executemany("insert into sources values(?,?,?,?,?,?)", [(k, *v) for k, v in SOURCES.items()])
    # unicode61 with diacritics removed; Devanagari tokenises on whitespace which is what we want.
    c.execute("create virtual table pages using fts5(src unindexed, page unindexed, printed unindexed, text, tokenize='unicode61 remove_diacritics 2')")
    for s in SOURCES:
        c.executemany("insert into pages values(?,?,?,?)", pages(s))
    c.commit()
    n = c.execute("select src, count(*) from pages group by src").fetchall()
    c.close()
    return n


if __name__ == "__main__":
    counts = dict(build())
    print(counts)
    assert all(counts.get(s, 0) > 100 for s in SOURCES), "a source failed to load"
