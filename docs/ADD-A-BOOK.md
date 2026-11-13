# How to add a new astrology book

> **What:** the steps to put a new book into the library, the index and the knowledge graph. **Read it when:** you add or re-ingest a book.
> **Last checked:** 2026-11-12 (only the changelog pointer; the steps were not re-run).
> **Related:** COPYRIGHT.md, KNOWLEDGE-SYSTEM.md, TESTING.md.

All commands run from the `_skill_workspace` folder inside your Astrology Books library folder. Everything stays on your Mac except
step 4, which uses Claude to read the book (see the privacy note there).

**1. Put the PDF or EPUB in the library folder** (the `Astrology Books` folder that holds `_skill_workspace`). It is only ever read. Keep its file name: the catalog, the extraction and the frozen accuracy files cite it, so a registered book is never renamed (if a file must be renamed, run `add_book.py relink`, which re-matches the catalog by SHA-256, and ask the owner first).

EPUBs are read directly, without converting them to PDF: the text comes from the EPUB's own reading order, and each non-empty section counts as one "page", so page numbers in answers and `search.py --page` are "epub section" numbers, not printed pages. `register` records the page convention itself.

**2. Register it** — records metadata and the SHA-256 fingerprint, and refuses exact duplicates (a byte-identical file is only noted as a duplicate of the first):
```bash
.venv/bin/python tools/kg/add_book.py register "Brihat Parashara Hora Vol 1.pdf" --id BPHS1 \
  --title "Brihat Parashara Hora Shastra, Vol. 1" --author "Parashara" --translator "R. Santhanam" \
  --edition "Ranjan 1984" --year 1984 --language "English translation" --system Parashari --tier classical
```
Required options: `--id` (2 to 12 capitals or digits, starting with a capital, never used before), `--title`, `--author`, `--language`, `--system` and `--tier`. Optional: `--translator`, `--edition`, `--year`, `--publisher`. The catalog fields that need the title page (rights, base text, translation tier) start as `unknown`; the owner checks them against the book.
Tiers: `classical` (the verse/root text), `traditional` (a commentary), `modern` (a practitioner's book),
`experimental`. If a different edition of a book you already have is added, give it its own id — editions are kept
side by side, never merged.

**3. Extract text and chapters**:
```bash
.venv/bin/python tools/kg/add_book.py text BPHS1          # uses the PDF's text; OCRs locally if it is a scan
.venv/bin/python tools/kg/add_book.py text LK1942 --ocr hi-IN   # force Hindi OCR
.venv/bin/python tools/kg/add_book.py chapters BPHS1
```
`text` options: `--ocr en-US` or `--ocr hi-IN` forces local OCR (it starts by itself when the text layer is thin; Hindi books default to `hi-IN`), and `--docling` is described at the end. For an EPUB, `text` and `chapters` read the sections and their headings; no OCR runs.

Open a few pages to check: `python3 astrology-prediction/scripts/search.py --page BPHS1:40` (after step 5), or read
`text/BPHS1.jsonl`.

**3b. Make the Markdown copy** (private, local only), so that Claude Code or another agent can read one chapter file instead of opening the book:
```bash
python3 tools/kg/books_md.py build BPHS1
```
It writes `books-md/BPHS1/` (an `index.md` and one file per chapter, every page marked). The folder holds copyrighted text: it is never committed or exported. Run it again after any change to `text/BPHS1.jsonl` or the chapters; if the text changed, also rebuild the search index with `python3 tools/build_index.py` (`add_book.py rebuild` does that too).

**4. Write the source map** (the rules). In Claude Code, ask:
> Read `_skill_workspace/sourcemaps/BRIEF.md` and follow it for source id BPHS1, text file `text/BPHS1.jsonl`,
> PDF `<file name>`. Work through the book in chunks, one chapter range per agent, one agent at a time.

This produces `sourcemaps/BPHS1.md` (or `_part1/_part2`), with one bullet per rule, each tagged
`[CLASSICAL-VERSE] / [TRANSLATOR-NOTE] / [AUTHOR] / [LK] / [Reader note]` and ending in `— BPHS1 p<PDF> (pr <printed>)`.
(The owner's private build uses a separate brief for Lal Kitab texts; it is not shipped.) *Privacy:* this step sends the book's text, a page range at a time, to the
Claude model you are using (Anthropic). It is not uploaded anywhere else, and nothing is published. Skip it if you prefer:
the book will then be in the full-text index and the graph's page layer, just without rule nodes.

**5. Rebuild and check**:
```bash
.venv/bin/python tools/kg/add_book.py rebuild
```
This rebuilds the full-text index, the extraction, the Graphify graph, runs `validation/graph_checks.py` (must pass)
and the retrieval test. Then read the reports in `validation/`:
- `library_integrity.md`: the new book shows "OK";
- `ocr_quality.md`: pages flagged low should be image-checked before their wording is trusted;
- `provenance.md`: rules without pages or with impossible pages;
- `duplicates.md`: near-identical rules or pages (review; nothing is merged);
- `entity_linking_review.md`: if a word is mislinked often, tighten it in `astrology-prediction/scripts/vocab.py`.

**6. Record disagreements.** If the new book contradicts a rule already in the library, add a row to
`astrology-prediction/references/contradiction-register.md` (both positions with pages); it becomes a Contradiction
node on the next rebuild. Add the book to `references/source-index.md` §1.

**7. Install the updated skill**:
```bash
python3 tools/release_skill.py --version 3.2
```
It backs up the installed copy first, runs the self-tests, and writes `Astrology Books/astrology-consultation-v3.2.skill`
for the Claude app (upload it in Settings → Capabilities → Skills).

Add a line to `CHANGELOG.md` (the repository root file) describing what changed.

## Optional: layout-aware extraction with Docling (v3.4)

For an English book with image tables, multi-column pages or broken OCR lines, add `--docling` to the text step:
`.venv/bin/python tools/kg/add_book.py text <ID> --docling`. It runs the usual extraction first, then Docling in its
own environment (`.venv-docling`), and keeps for each page whichever text is more complete (catalogue records
`… + Docling (per-page fallback)`). Not recommended for Hindi books (Docling drops pages there). First use downloads
Docling's models from Hugging Face; no book content leaves the machine.
