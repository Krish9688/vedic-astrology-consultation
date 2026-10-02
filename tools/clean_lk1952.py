# Strip the typesetter watermark/header lines from the LK1952 Hindi OCR; keep page order and the "पेज नंबर" line.
import json, re
SRC, OUT = "text/LK1952_ocr.jsonl", "text/LK1952_clean.jsonl"
noise = re.compile(r"blogspot|टाईप सेटिंग|जोशी कृत")
def clean(t):
    keep = [l for l in t.splitlines() if not noise.search(l) and l.count("1952") < 2]
    return "\n".join(keep)
rows = sorted((json.loads(l) for l in open(SRC)), key=lambda r: r["page"])
assert [r["page"] for r in rows] == list(range(1, len(rows) + 1)), "missing pages"
with open(OUT, "w") as o:
    for r in rows:
        r["text"] = clean(r["text"]); o.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(rows), "pages ->", OUT)
