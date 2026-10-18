# Copyright and the library

The skill reasons from a private library of astrology books. **No book, no extracted page text, no full-text index,
no book-by-book source map and no knowledge graph built from them is published** — whatever the book's status — because
together they would reproduce the books. The repository contains only code, the skill's own reference files (the
project's synthesis, with short page references), synthetic test data and bibliographic metadata.

## 1. The books (audit 2026-09-27)

| ID | Book | Translator / author | Status | In repository |
|---|---|---|---|---|
| BJ | Brihat Jataka (Varahamihira) | N. Chidambaram Iyer, 1905 | likely public domain in the US (published 1905); elsewhere depends on the translator's dates — not verified | metadata only |
| PD | Phaladeepika (Mantreswara) | V. Subrahmanya Sastri, 1950 | unclear (translator's dates not verified) — treated as restricted | metadata only |
| JP2 | Jataka Parijata Vol. 2 | V. Subrahmanya Sastri, 1933 | unclear — treated as restricted | metadata only |
| BPHS | Brihat Parasara Hora Sastra | R. Santhanam | copyrighted translation | metadata only |
| PM2 | Prasna Marga Pt. 2 | B. V. Raman | copyrighted | metadata only |
| HPA, HJH1, HJH2 | Raman's Hindu Predictive Astrology; How to Judge a Horoscope 1–2 | B. V. Raman | copyrighted | metadata only |
| LOL | Light on Life | de Fouw & Svoboda | copyrighted | metadata only |
| LKS | Lal Kitab | Radhakrishna Shrimali (2013) | copyrighted | metadata only |
| LK1952 | Lal Kitab 1952 (Hindi re-typeset) | Roop Chand Joshi; ed. V. Nagpal | copyrighted/unclear | metadata only |
| JSR, CRUX | Jaimini Upadesa Sutra course; Crux of Vedic Astrology | Sanjay Rath | copyrighted | metadata only |
| PVR | Vedic Astrology: An Integrated Approach | P. V. R. Narasimha Rao | copyrighted | metadata only |
| KNRT | Timing Events through Vimshottari Dasha | K. N. Rao | copyrighted | metadata only |
| SAR1 | Saravali Vol. 1 | tr. Kalyan Verma, Manoj Kumar | copyrighted | metadata only |
| NAKS | The Nakshatras | Komilla Sutton | copyrighted | metadata only |
| DEVA2 | Deva Keralam Vol. 2 | R. Santhanam | copyrighted | metadata only |

"Metadata only" = the entry in `knowledge/catalog.json`: title, author, translator, edition, language, system, tier,
page convention, page count, expected file name and SHA-256 fingerprint.

## 1a. Public-domain research (2026-10-03; no change in treatment)

| ID | Publication | United States | India (author's life + 60 years) | Treatment |
|---|---|---|---|---|
| BJ | N. Chidambaram Iyer, 1905 | public domain (published before 1931) | translator's death year not verified | still not redistributed (no need) |
| JP2 | V. Subrahmanya Sastri, Mysore 1933 | not yet: a 1933 foreign publication stays protected until 1 Jan 2029 (95 years) | Sastri's death year not found in public sources checked (his output spans 1915–1950s) | restricted |
| PD | V. Subrahmanya Sastri, 2nd ed. 1950 | protected until 2046 | as above | restricted |

Sources checked: Internet Archive catalogue entries for both Sastri translations and a Sri Jagannatha Jyotish article on
the translator (no dates of birth/death). Scans being online is not evidence of public-domain status. Nothing changes:
no book or book text is published whatever its status.

## 2. Derived material

| Material | Nature | Published? |
|---|---|---|
| `text/*.jsonl`, `index/library.sqlite` | full page text | never |
| `sourcemaps/<book>_part*.md` | detailed page-by-page paraphrase of each book | not public; kept in the owner's **private** archive repository (REPOSITORY-EDITIONS.md) |
| `knowledge/extraction.json`, `graphify-out/` | 10,444 paraphrased rules with pages | not public; gzip-compressed copies in the **private** archive repository |
| Skill `references/*.md` | the project's own synthesis; short paraphrases with page references | yes (in the skill and repository) |
| Skill `data/lal-kitab/` Shrimali KB v2.2 and its audit (`*.md`) | a detailed derivative of a copyrighted book, validated against it | in the **private** repository and the owner's skill package only; the public export leaves them out. Review with the rights holder before any public release |
| The Lal Kitab Varshaphal table (private edition data file) | a house-permutation table reconciled from Shrimali's book and the 1952 edition (pp221–222), page references and audit columns; a provenance check (2026-10-18) found every recommended row printed in one of the two books, except one row whose tie was broken with a secondary web chart (the books-only reading is now shown beside it) | was published in 3.5.0 (repository and `.skill`); **dropped from the public edition from 3.6.0** by the owner's decision (2026-10-07) pending rights confirmation; private edition only. the public edition no longer ships `varshaphal.py` either (from 3.6.1) |
| Lal Kitab rules restated in the PUBLIC skill: built-in tables in `scripts/chart_facts.py` (Lal Kitab house dignities, friendships, house states) and the Lal Kitab rules in `references/` (method, timing ages and cycles, the 1952-edition page-cited rules, the contradiction register's Lal Kitab sections, remedy lists, the Lal Kitab layers of the topic files), plus Lal Kitab output in test fixtures and knowledge-base codes in code comments | short factual rule lists (house numbers, ages) compiled from the Shrimali KB (a derivative of a copyrighted book) and from the 1952 edition, whose rights holders have not been identified; no book text; the public script output carries no KB citations from 3.6.1 | published in 3.5.0 and 3.6.0; **removed from the public edition from 3.6.1** (council option B2, 2026-10-12: tables moved to the private `scripts/lal_kitab.py`, LK prose kept private by edition markers, export gate). Never reviewed for redistribution; the earlier releases remain downloadable — no claim is made here about their status |

Keeping a derivative in the private repository or the owner's private package limits who receives it; it is **not** a
licence and grants no right to copy or redistribute. Redistribution rights for the Lal Kitab material remain
unresolved (open question for the owner and, if needed, the rights holders).

Quotations in the skill stay under ~15 words; the rest is paraphrase.

## 2a. Quotation review (recorded 2026-10-03)

Scope: every file the public plugin ships (`SKILL.md`, `references/*.md`, `assets/report/*.json`). Method: extract
every quoted passage (straight or curly quotes, ≥ 3 characters); a passage counts as a possible book quotation when a
book ID or page reference (`BPHS`, `PD`, `p184`, …) appears within 120 characters.

| Result | Count |
|---|---|
| Quoted passages of 10+ words | 68 — all the project's own example, template or instruction text (no book reference nearby) |
| Book-adjacent quotations | 137: 1 word 44 · 2 words 41 · 3 words 15 · 4 words 11 · 5 words 9 · 6 words 7 · 7 words 8 · 8 words 2 |
| Longest book-adjacent quotation | 8 words (e.g. "in no case is a literal application desirable") |

All quotations are within the "under ~15 words, attributed" rule; the rest of the skill's book material is
paraphrase with page references. Re-run before each public release (the method above, or ask Claude to repeat it).

## 3. Using your own copies

Obtain the books legally, put the PDFs in the library folder and run the ingestion pipeline
([ADD-A-BOOK.md](ADD-A-BOOK.md)). `tools/kg/add_book.py relink` matches files by SHA-256 against the catalogue, so an
identical file is recognised whatever its name; a different edition is registered as a new source with its own page
convention. Without the books, the skill still runs: search and graph lookups report that retrieval is unavailable.

## 4. Code licences

Split licence, decided 2026-10-03 ([LICENSING-DECISION.md](LICENSING-DECISION.md)): AGPL-3.0-or-later for the engine,
service and tools; Apache-2.0 for the skill scripts, templates and plugin files; CC BY 4.0 for the method text and
documentation. Book quotations and paraphrases are not relicensed. Dependencies: Swiss
Ephemeris/pyswisseph and PyMuPDF are AGPL-3.0 (or commercial); Graphify Apache-2.0; Docling, Pydantic, Ruff, Gitleaks,
pre-commit MIT; Jinja2, WeasyPrint BSD-3; Hypothesis MPL-2.0.
