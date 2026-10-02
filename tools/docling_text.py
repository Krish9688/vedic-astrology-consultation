# Layout-aware page text with Docling, merged page by page with the baseline extraction (text layer / Apple Vision OCR).
# Benchmark (docs/KNOWLEDGE-SYSTEM.md, "Docling evaluation"): Docling recovers image tables and repairs broken English
# lines, but drops whole pages of Hindi OCR — so each page keeps whichever text is more complete.
# Local: Docling fetches its layout/table models from Hugging Face once; no document content leaves the Mac.
# usage: .venv-docling/bin/python tools/docling_text.py PDF SRC_ID BASELINE.jsonl OUT.jsonl [--lang en-US]
import json, re, sys

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import OcrMacOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import TableItem

KEEP_RATIO = 0.6   # Docling page text shorter than 60% of the baseline → keep the baseline page


WORDS = {w.strip().lower() for w in open("/usr/share/dict/words", errors="ignore")}


def junk(t):
    """Garbled glyph runs from Devanagari fonts without a Unicode map (common in scanned translations): few real
    English words and little real Devanagari. Numbered verses ("81. If the 7th lord…") always pass."""
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return True
    if sum("ऀ" <= c <= "ॿ" for c in letters) / len(letters) >= 0.5:
        return False
    toks = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", t)]
    real = sum(w in WORDS or w.rstrip("s") in WORDS for w in toks)
    return not toks or real / len(toks) < 0.5


def main(pdf, sid, base_path, out, lang="en-US"):
    base = {r["page"]: r for r in map(json.loads, open(base_path, encoding="utf-8"))}
    opts = PdfPipelineOptions(do_ocr=True, do_table_structure=True, ocr_options=OcrMacOptions(lang=[lang]))
    doc = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}).convert(pdf).document
    pages = {}
    for item, _ in doc.iterate_items():
        prov = getattr(item, "prov", None)
        if not prov:
            continue
        txt = item.export_to_markdown(doc) if isinstance(item, TableItem) else getattr(item, "text", "")
        if txt and (isinstance(item, TableItem) or not junk(txt)):
            pages.setdefault(prov[0].page_no, []).append(txt)
    used = {"docling": 0, "baseline": 0}
    with open(out, "w", encoding="utf-8") as f:
        for p in sorted(base):
            dl = "\n".join(pages.get(p, []))
            keep = len(dl.strip()) >= KEEP_RATIO * len(base[p]["text"].strip())
            row = {**base[p], "text": dl, "extractor": "docling"} if keep else {**base[p], "extractor": "baseline"}
            used[row["extractor"]] += 1
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{sid}: {used['docling']} pages from Docling, {used['baseline']} kept from the baseline → {out}")


if __name__ == "__main__":
    a = sys.argv[1:]
    lang = a[a.index("--lang") + 1] if "--lang" in a else "en-US"
    main(*a[:4], lang=lang)
