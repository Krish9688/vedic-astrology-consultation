# How to add a new astrology book

All commands run from `~/Documents/Astrology Books/_skill_workspace`. Everything stays on your Mac except
step 4, which uses Claude to read the book (see the privacy note there).

**1. Put the PDF in the library folder** (`Astrology Books/`). It is only ever read.

**2. Register it** — records metadata and the SHA-256 fingerprint, and refuses exact duplicates:
```bash
.venv/bin/python tools/kg/add_book.py register "Brihat Parashara Hora Vol 1.pdf" --id BPHS1 \
  --title "Brihat Parashara Hora Shastra, Vol. 1" --author "Parashara" --translator "R. Santhanam" \
  --edition "Ranjan 1984" --year 1984 --language "English translation" --system Parashari --tier classical
```
Tiers: `classical` (the verse/root text), `traditional` (a commentary), `modern` (a practitioner's book),
`experimental`. If a different edition of a book you already have is added, give it its own id — editions are kept
side by side, never merged.

**3. Extract text and chapters**:
```bash
.venv/bin/python tools/kg/add_book.py text BPHS1          # uses the PDF's text; OCRs locally if it is a scan
.venv/bin/python tools/kg/add_book.py text LK1942 --ocr hi-IN   # force Hindi OCR
.venv/bin/python tools/kg/add_book.py chapters BPHS1
```
Open a few pages to check: `python3 astrology-prediction/scripts/search.py --page BPHS1:40` (after step 5), or read
`text/BPHS1.jsonl`.

**4. Write the source map** (the rules). In Claude Code, ask:
> Read `_skill_workspace/sourcemaps/BRIEF.md` and follow it for source id BPHS1, text file `text/BPHS1.jsonl`,
> PDF `<file name>`. Work through the book in chunks, one chapter range per agent, one agent at a time.

This produces `sourcemaps/BPHS1.md` (or `_part1/_part2`), with one bullet per rule, each tagged
`[CLASSICAL-VERSE] / [TRANSLATOR-NOTE] / [AUTHOR] / [LK] / [Reader note]` and ending in `— BPHS1 p<PDF> (pr <printed>)`.
Use `BRIEF_LK1952.md` for Lal Kitab texts. *Privacy:* this step sends the book's text, a page range at a time, to the
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

Add a line to `docs/CHANGELOG.md` describing what changed.

## Optional: layout-aware extraction with Docling (v3.4)

For an English book with image tables, multi-column pages or broken OCR lines, add `--docling` to the text step:
`.venv/bin/python tools/kg/add_book.py text <ID> --docling`. It runs the usual extraction first, then Docling in its
own environment (`.venv-docling`), and keeps for each page whichever text is more complete (catalogue records
`… + Docling (per-page fallback)`). Not recommended for Hindi books (Docling drops pages there). First use downloads
Docling's models from Hugging Face; no book content leaves the machine.
