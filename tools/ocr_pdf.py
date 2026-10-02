# OCR an image-only PDF with tools/ocr (macOS Vision, fully local). Resumable, parallel.
# usage: ocr_pdf.py PDF SRC_ID OUT.jsonl [lang] [first_page] [last_page]
import pymupdf, json, subprocess, sys, tempfile, os
from concurrent.futures import ThreadPoolExecutor
pdf, sid, out = sys.argv[1:4]
lang = sys.argv[4] if len(sys.argv) > 4 else "en-US"
d = pymupdf.open(pdf)
first = int(sys.argv[5]) if len(sys.argv) > 5 else 1
last = int(sys.argv[6]) if len(sys.argv) > 6 else d.page_count
ocr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr")
done = {json.loads(l)["page"] for l in open(out)} if os.path.exists(out) else set()
tmp = tempfile.mkdtemp()

def run(pno):
    page = pymupdf.open(pdf)[pno - 1]
    zoom = min(2400 / page.rect.width, 4.0)  # ~2400 px wide is plenty for Vision
    p = os.path.join(tmp, f"{pno}.png")
    page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(p)
    txt = subprocess.run([ocr, p, lang], capture_output=True, text=True).stdout
    os.remove(p)
    return pno, txt

todo = [p for p in range(first, last + 1) if p not in done]
with open(out, "a") as o, ThreadPoolExecutor(4) as ex:
    for pno, txt in ex.map(run, todo):
        o.write(json.dumps({"src": sid, "page": pno, "text": txt, "ocr": f"apple-vision:{lang}"}, ensure_ascii=False) + "\n"); o.flush()
