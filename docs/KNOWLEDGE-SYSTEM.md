# Knowledge system: Graphify knowledge graph over the astrology library (v3.1; 18 books since v3.3)

## 1. The flow

```
Your books (PDFs in Astrology Books/ — never modified; SHA-256 recorded in knowledge/catalog.json)
  ↓  text extraction (PyMuPDF) / local OCR (macOS Vision, en-US + hi-IN)           → text/<ID>.jsonl (one row per PDF page)
  ↓  quality checks: OCR score, near-empty pages, duplicate files/pages             → validation/*.md
  ↓  full-text index (SQLite FTS5, page provenance)                                 → index/library.sqlite
  ↓  source maps: page-cited paraphrased rules, tagged by tier (one per book)       → sourcemaps/<ID>.md
  ↓  deterministic extraction (no LLM): rules, pages, books, entities, disputes      → knowledge/extraction.json
  ↓  Graphify: schema validation → graph build → communities → report → exports      → graphify-out/graph.json, GRAPH_REPORT.md, graph.html
  ↓  retrieval: scripts/kg.py (graph) + scripts/search.py (full text)
Chart data from a calculation engine (supplied chart or VedAstro with consent) → scripts/chart_facts.py (derived facts)
  ↓
Senior-astrologer reasoning (SKILL.md → synthesis-method, topic, timing, vargas, Jaimini, Lal Kitab)
  ↓  cross-check techniques, grade convergence, look up and verify sources, show disputes
Source-backed interpretation in plain language
```

Calculation and interpretation stay separate: nothing in the knowledge layer computes positions, and the graph is
never asked what a planet's position is. The graph only answers "what do the books say, where, and who disagrees".

## 2. Folder layout (additive; nothing existing was moved)

```
Astrology Books/
├── *.pdf                         the library (authoritative; read-only)
├── Lal Kitab Knowledge Base/, LalKitab_v2.2_Reference_and_Skill_Bundle/   untouched
├── astrology-consultation-v3.skill, -v3.1.skill                           packages for the Claude app
└── _skill_workspace/
    ├── astrology-prediction/     THE SKILL (source) — installed to ~/.claude/skills/astrology-consultation
    │   └── scripts/kg.py, vocab.py   graph query + controlled vocabulary (stdlib only)
    ├── knowledge/
    │   ├── catalog.json          one record per book: title, author, translator, edition, year, language,
    │   │                         system, tier, text layer, page convention, page count, SHA-256, duplicates
    │   ├── chapters/<ID>.json    chapter marks (PDF outline or heading heuristic)
    │   └── extraction.json       Graphify-schema extraction (nodes + edges), rebuilt from sources
    ├── graphify-out/             graph.json (the graph), GRAPH_REPORT.md, graph.html (+ optional wiki/, obsidian/)
    ├── text/, index/, sourcemaps/   (from v3)
    ├── tools/kg/                 extract.py, build_graph.py, add_book.py ; tools/release_skill.py
    ├── validation/               graph_checks.py, retrieval_eval.py and generated reports
    ├── vendor/graphify/          the inspected Graphify source (commit 4c73561, v0.9.67)
    ├── .venv-graphify/           Graphify + deps (project-local)
    ├── backups/                  pre-change archives and every previous installed skill
    └── docs/                     this file, ADD-A-BOOK.md, ARCHITECTURE.md, CHANGELOG.md, TOOLING.md, reports
```

The suggested `books/ lal-kitab/ vedic/ …` layout was **not** imposed: moving the PDFs would break every recorded
path and hash for no gain. The catalog gives the same organisation logically (system, tier, language per book).

## 3. Why Graphify is used this way

Graphify (Apache-2.0, v0.9.67, very active) is mainly a code-graph tool. For documents and PDFs its normal path is a
"semantic pass" in which an LLM reads the files — that would send the whole private, copyrighted library to a model
API, and for 3,459 pages it would be slow, costly and non-deterministic. Instead:

- **Extraction is ours and deterministic** (`tools/kg/extract.py`): it turns the already page-cited source maps, the
  audited Lal Kitab KB and the contradiction register into Graphify's documented extraction schema.
- **Graphify does what it is good at**: schema validation (`validate_extraction`), graph assembly (`build`),
  community detection (`cluster`), hub/"god node" and surprise analysis, `GRAPH_REPORT.md`, `graph.html`, optional
  wiki/Obsidian export, and its CLI (`graphify query/explain/path --graph graphify-out/graph.json`).
- **Graphify's fuzzy entity de-duplication is switched off** (`build(..., dedup=False)`), because it merges
  similar-sounding labels — exactly what must not happen to rules. Possible duplicates are listed for review instead.
- Its assistant hooks (`graphify install`, `graphify claude install`) were **not** run: they write to CLAUDE.md, add a
  PreToolUse hook and install a code-oriented skill, none of which this project needs.
- The graph is the retrieval layer, not the authority: every answer points back to a book page that `search.py
  --page` can show, and the books stay the source of truth.

## 4. Entity model (node types)

| Type | Count | Id pattern | Key attributes |
|---|---|---|---|
| Book | 8 | `book:PD` | title, author, translator, edition, year, language, system, tier, sha256, page convention |
| Person | 10 | `person:…` | author / translator |
| DuplicateFile | 1 | `file:…` | identical copy of LK1952 (same SHA-256), not indexed |
| Page | 3,459 | `page:PD:184` | pdf_page, printed_page (LK1952), chapter, words, ocr_score, flags |
| Rule | 4,378 | `rule:PD:<hash>` | text (paraphrase), source, book, author, edition, language, section (chapter path), heading, verses, pages, kind, tag, **tier**, system, extraction date and method, confidence, citation level, flags (image-checked, unverified, deterministic), do_not_forecast, map_line |
| Contradiction | 76 | `contradiction:CR-V02`, `contradiction:KB-X3` | topic, classification (T/R/U), working default |
| Position | 152 | `position:CR-V02:A` | one side of a dispute, with its pages |
| Planet, Sign, House, Nakshatra, Yoga, DivisionalChart, Technique, LalKitabConcept, Topic | 171 | `planet:jupiter`, `house:7`, `varga:d9`… | synonyms in `scripts/vocab.py` (English, Sanskrit, Hindi) |

Rule **kinds**: method, topic-rule, timing-rule, yoga, worked-example, contradiction-note, harmful-statement, limits,
page-notes, kb-register, kb-section, lk-planet-in-house. Rules correspond to the brief's Rule / Timing Rule / Lal
Kitab rule / Exception entities; Prediction and Remedy are rule kinds or topics rather than separate node types,
because forcing them apart would mean guessing.

**Tiers** (the brief's distinction): classical (verse or root text) · traditional (translator/commentator notes) ·
modern (practitioner teaching) · experimental · synthesis (reader notes, our inference). External knowledge (not in
the library) is never in the graph; the skill labels it separately.

## 5. Relationship model (edge types)

| Relation | From → To | Confidence | Meaning |
|---|---|---|---|
| RULE_FROM | Rule/Position → Page | EXTRACTED | the page the rule was read from (printed page kept) |
| PART_OF | Page → Book | EXTRACTED | |
| WRITTEN_BY / TRANSLATED_BY | Book → Person | EXTRACTED | |
| APPLIES_TO | Rule/Position/Contradiction → entity | INFERRED | vocabulary match in the rule text or its section heading; houses carry `role` = house/lord |
| MENTIONS | Page → entity | INFERRED | the page text mentions it (weight = count; Hindi synonyms included) |
| HAS_POSITION | Contradiction → Position | EXTRACTED | both sides always kept |
| CONTRADICTS | Position A → Position B | EXTRACTED | from the curated registers |
| DISCUSSED_IN | Rule → Contradiction | INFERRED | the rule cites a page one side of the dispute cites and shares an entity |
| REFERS_TO | Contradiction → Contradiction | EXTRACTED | register row points to a KB X-row |
| SIMILAR_TO | Rule → Rule | AMBIGUOUS | wording ≥ 90 (same source) / ≥ 85 (cross-source) — never merged |
| NEAR_DUPLICATE_OF | Page → Page | AMBIGUOUS | 5-word-shingle Jaccard ≥ 0.6 |
| DUPLICATE_OF | DuplicateFile → Book | EXTRACTED | identical SHA-256 |

Not created automatically: MODIFIED_BY, STRENGTHENED_BY, WEAKENED_BY, SUPPORTS, TRIGGERS, TIMED_BY, VALIDATED_BY.
They would require judging meaning, and a wrong "supports" edge is worse than none. They are the right place for
future hand-curated edges (see §10).

## 6. Provenance

Every rule node carries: source id → book title, author, edition, language; PDF page(s) and printed page(s);
chapter/section path from the source map; verse numbers where given (e.g. XV.6); the tag written by the reader
(CLASSICAL-VERSE, TRANSLATOR-NOTE, AUTHOR, LK, VED, MIXED, Reader note); the tier; the extraction date and method;
whether the page came from the rule itself or its section heading; and flags such as image-checked or ❓.
The rule text is a **paraphrase** made while reading the whole book (copyright): quote from the page itself, via
`search.py --page SRC:N`, and keep quotations short.

## 7. Integrity: duplicates, OCR, metadata, linking

Generated on every rebuild (`validation/`):
- `library_integrity.md` — hashes every PDF: changed, missing, unregistered or duplicate files (found: the two
  identical *Lal Kitab 1952* PDFs; the copy is recorded, not deleted).
- `ocr_quality.md` — per-page text quality; 38 low-quality pages listed for image checks.
- `duplicates.md` — duplicate files, near-duplicate pages (7), near-identical rules (3 same-source, 1 cross-source:
  BJ and PD both give "source of wealth from the 10th" — a lineage parallel, *not* independent support).
- `provenance.md` — rules lacking a page (382, mostly "limits" notes and cross-references; marked AMBIGUOUS),
  citations outside a book's page range (2, both reviewed: an external *Jataka Parijata* page and a KB note).
- `entity_linking_review.md` — ambiguous vocabulary (Cancer, Mula/Moolatrikona, hora, rin, bindus…) with samples.
- `graph_checks.py` — hard checks (exit 1 on failure): every rule has source, tier and date; confidence matches
  citation; ≥ 90 % of rules page-linked; each dispute has exactly two positions; no automatic merges; every book
  hash unchanged; every PDF page present.

Lal Kitab edition differences are preserved by construction: LK1952 and Shrimali rules are separate nodes from
separate sources, and their 25+ documented differences are Contradiction nodes with both positions.

## 8. Using it

```bash
cd ~/.claude/skills/astrology-consultation/scripts
python3 kg.py sources "karaka in its own house"          # best first call: rules + disputes + full-text pages
python3 kg.py find "Saturn in the 10th" --system "Lal Kitab" -n 5
python3 kg.py find "Jupiter aspecting the 7th lord" --tier classical
python3 kg.py contradictions "Rahu exaltation"
python3 kg.py pages "Guru 7th house marriage"            # pages in all 8 books, Hindi LK1952 included
python3 kg.py terms "Guru in 7th, navamsa"               # how the query is understood
# Graphify's own tools on the same graph:
_skill_workspace/.venv-graphify/bin/graphify explain "Gajakesari yoga" --graph _skill_workspace/graphify-out/graph.json
open _skill_workspace/graphify-out/graph.html            # visual map of the 167 communities
```

## 9. Update, backup, restore

- **Add a book**: `docs/ADD-A-BOOK.md`. **Rebuild everything**: `.venv/bin/python tools/kg/add_book.py rebuild`
  (index → extraction → graph → checks → retrieval test). **Install**: `python3 tools/release_skill.py --version X`
  (archives the installed copy to `backups/installed-before-<time>/` first, runs self-tests, builds the package).
- **Update Graphify**: `git -C vendor/graphify pull`, read its CHANGELOG, then
  `.venv-graphify/bin/pip install --no-build-isolation --only-binary=:all: --no-binary=graphifyy ./vendor/graphify`
  and rebuild; `graph_checks.py` and `retrieval_eval.py` must still pass.
- **Backups**: `backups/2026-09-25_pre-v3.1/` holds the v3 skill source, installed copy, package and the previous
  index. To restore v3: extract `installed-skill.tgz` into `~/.claude/skills/`. Everything derived (extraction,
  graph, index) can be regenerated from the books + source maps, so the irreplaceable items are the books, the
  source maps, the KB bundle and the skill source — back those up with Time Machine or a copy of the folder.

## 10. Known limitations

- Entity linking is vocabulary-based: good recall for named things, but it cannot tell "Jupiter aspects the 7th"
  from "Jupiter is aspected by the 7th lord"; `find` narrows by co-occurrence and proximity, and the reader verifies.
- Rules are AI-written paraphrases from full reads (spot-checked, page-cited), not the books' words.
- 382 rules have no page of their own (listed); chapter marks for scanned books are heuristic.
- The retrieval test's gold pages come from the same curated registers and maps the graph ingests, so it measures the
  value of that curated layer as much as graph mechanics; it is not a blind test.
- No semantic (meaning-level) relations such as SUPPORTS or MODIFIED_BY — deliberately; add them by hand in a
  small curated file if wanted (future work).
- The graph lives only on this Mac. In Claude Chat/Cowork the skill works without it and says so.

## 11. Docling evaluation (v3.4)

Docling 2.130.0 was benchmarked against the existing extraction on five kinds of page (`validation/docling/README.md`).
It recovers image tables the text layer loses entirely and repairs broken OCR lines in mixed Sanskrit/English books
(real-word share 0.746 → 0.937 once garbled glyph runs are filtered), is neutral on clean text, and loses whole Hindi
pages. It is therefore an **opt-in** step for new English books (`add_book.py text ID --docling`), merged page by page
with the baseline so no page gets worse (`tools/docling_text.py`). The existing library was not re-extracted; see
ROADMAP.md. Graphify remains the retrieval/evidence layer only — it neither calculates nor reasons.
