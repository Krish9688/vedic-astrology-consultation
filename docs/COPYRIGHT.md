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

## 2. Derived material

| Material | Nature | Published? |
|---|---|---|
| `text/*.jsonl`, `index/library.sqlite` | full page text | never |
| `sourcemaps/<book>_part*.md` | detailed page-by-page paraphrase of each book | never (only the method briefs `BRIEF*.md` and `STATUS.md`) |
| `knowledge/extraction.json`, `graphify-out/` | 10,444 paraphrased rules with pages | never |
| Skill `references/*.md` | the project's own synthesis; short paraphrases with page references | yes (in the skill and repository) |
| Skill `data/lal-kitab/` (Shrimali KB v2.2, audit, Varshaphal table) | a detailed derivative of a copyrighted book, validated against it | in the **private** repository and the skill package for the owner's use; `export_repo.py --public` leaves it out. Review with the rights holder before any public release |

Quotations in the skill stay under ~15 words; the rest is paraphrase.

## 3. Using your own copies

Obtain the books legally, put the PDFs in the library folder and run the ingestion pipeline
([ADD-A-BOOK.md](ADD-A-BOOK.md)). `tools/kg/add_book.py relink` matches files by SHA-256 against the catalogue, so an
identical file is recognised whatever its name; a different edition is registered as a new source with its own page
convention. Without the books, the skill still runs: search and graph lookups report that retrieval is unavailable.

## 4. Code licences

The repository has no licence file yet (all rights reserved by default) — the owner decides; analysis and
recommendation in [LICENSING.md](LICENSING.md). Dependencies: Swiss
Ephemeris/pyswisseph and PyMuPDF are AGPL-3.0 (or commercial); Graphify Apache-2.0; Docling, Pydantic, Ruff, Gitleaks,
pre-commit MIT; Jinja2, WeasyPrint BSD-3; Hypothesis MPL-2.0.
