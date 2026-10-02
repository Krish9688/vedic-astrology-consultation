# Changelog

Every version up to v3.4 predates this git repository as a package (created 2026-10-01; v3.4's source is its first commit, made three minutes after the v3.4 package was built; v3.5 was developed in it); dates come from the evidence listed in
[docs/VERSION-HISTORY.md](docs/VERSION-HISTORY.md). For important changes this log records what existed before, what
problem was observed, what exposed it, what changed, why that solution, and how it was validated.

## [3.5.0] — 2026-10-03 — Claude marketplace plugin and public repository

Same skill method and engine as v3.5; this entry is about distribution.

### Added
- **Claude plugin marketplace** `vedic-astrology` with the plugin `astrology-consultation` (public repository
  `Krish9688/vedic-astrology-consultation`): the consultation skill, `/astrology-consultation:setup` and `:doctor`,
  and the local engine served over MCP by `scripts/astro`, which builds a private Python environment in the plugin's
  data folder on first use. One shared core: the plugin contains the engine source; no second engine.
  *Validated:* `claude plugin validate --strict` (marketplace and plugin); new-user install from GitHub in a sandboxed
  Claude Code profile → setup → doctor (13 PASS, 0 WARN/FAIL) → `claude mcp list` Connected → MCP smoke (16 tools,
  synthetic D9) → report HTML + PDF; update, disable/enable, rollback, uninstall with and without `--keep-data`.
- **Two repositories**: a public distribution repository (allowlist export `tools/export_public.py --check`: privacy
  check, Gitleaks, version consistency, official validator, tests in a fresh environment, package check) and the
  private archive (`tools/export_repo.py --archive`: book-derived analysis, compressed graph, full release history,
  local-only manifest with checksums). docs/MARKETPLACE.md, REPOSITORY-EDITIONS.md, PRIVATE-REPOSITORY-INVENTORY.md.
- Split licence (owner's decision): AGPL-3.0-or-later engine, Apache-2.0 skill scripts and plugin files, CC BY 4.0 text.

### Changed
- Skill scripts find the book library through settings (`paths.py`: environment → config → standard folder → legacy
  folder) instead of a fixed folder; the public edition says when the Lal Kitab knowledge base is absent.
- The engine reads `ASTRO_SKILL_DIR`/`ASTRO_KNOWLEDGE_DIR` and never pins a plugin path in the settings file.

### Fixed
- Report folders are created owner-only (0700); they hold birth details. *Exposed by:* the new-user test (0755).
- The privacy check judged scanned folders by their absolute path (a folder under `/private/tmp` failed every file);
  paths are now relative to the scanned folder (test added).
- The MCP smoke client now passes the environment through (the SDK drops non-default variables).

## [v3.5] — 2026-10-03

### Added
- **Fully local strength and Jaimini calculation**: Shadbala (all six components, BPHS as worked by Raman),
  Ashtakavarga (bhinna and sarva), chara karakas (7 and 8), arudha padas with the BPHS exception, upapada, karakamsa,
  rasi drishti; Sripati bhavas. *Before:* Shadbala and Ashtakavarga came only from VedAstro (cloud, consent needed),
  and engines disagreed by more than a rupa. *Validated:* Raman's published drik bala reproduced (±0.02);
  Ashtakavarga equal to VedAstro cell for cell on two charts; every Shadbala difference with VedAstro and PyJHora
  classified — the comparison exposed three defects in those engines (CALCULATION-ENGINES.md §5).
- **Birth-time sensitivity grid**: the chart recomputed at ±0.5…15 minutes; each factor classed robust / moderate /
  high / very high, and the skill uses the classes. *Exposed by:* answers estimating birth-time margins by eye.
- **Full Swiss Ephemeris files** (pinned SHA-256; Moshier fallback when absent), with a before/after benchmark over
  400 dates: largest planetary difference 2.65″ (Moon); the true node 55.6″.
- **Comparison verdicts** match / within tolerance / methodology / configuration / implementation / unresolved /
  not comparable; 0 unresolved on two synthetic charts and one private chart.
- **Portable service** `astro/`: one vendor-neutral core behind an MCP server (stdio and Streamable HTTP), a REST API
  (`/api/v1`, OpenAPI) and a CLI (`astro chart|dasha|varga|strength|jaimini|sensitivity|compare|consult|report|predict|
  doctor|setup|add-book|mcp|serve`); privacy modes private (default) / hybrid / research; localhost only unless remote
  use is opted into with a token; `install.sh`. *Why:* the same private calculation and method for Claude, ChatGPT
  desktop/Codex, Cursor or a script. *Validated:* tests/test_service.py (MCP round trip with a generic client, REST,
  CLI, security refusals); client matrix in docs/CLIENT-INTEGRATIONS.md claims only what was run.
- **Prediction log** (consent-gated, owner-only, evaluated once) seeded with synthetic records.
- **Contradiction register section F**: the 125 automatic cross-book disputes curated (47 genuine, 38 school, 12 false
  positives, 12 translation, 9 compatible, 6 context, 1 printing error — the last five checked against page images);
  18 that change readings added to
  the register; the graph carries the classes (182 disputes).
- docs/CLIENT-INTEGRATIONS.md, docs/LICENSING.md (recommendation; repository stays private until the owner decides).

### Changed
- Report renderer: timelines zoom to the interpreted window (clipped chapters marked); compact layout for summaries;
  no forced page gaps; browser cover fix. *Exposed by:* page-by-page visual review of round-9 reports.
- Planetary war follows BPHS (Venus always wins); the arudha convention names Rath's and Santhanam's readings.

### Fixed
- Required Shadbala for the Sun was 5 rupas; BPHS gives 6.5 (390 virupas). *Found by:* a benchmark answerer.
- Cheshta bala uses a circular mean (a plain average fails across 0° Aries — present in PyJHora and VedAstro).

### Safety
- A complete-life benchmark answer gave a parenthood age and a "window for children". The children topic file now
  states an output rule, QC checks it, and `life_lint.py` blocks such phrasing (negation-aware); the renderer refuses
  to render a report that trips it.

### Final validation phase (before publication)
- **Fixed:** full-chart calculation crashed for polar-day/polar-night births (no sunrise) — equinoctial 06:00/18:00
  fallback, flagged in the output; ephemeris provenance now reported for the birth date (Moshier outside 1800–2399);
  true-node retrograde state from its speed; transit search step 2 days; `astro setup` created the private data
  folder world-readable (found by the clean-install test) — now 0700; SAFETY lint no longer flags headings or doctor
  referrals.
- **Added:** exact Jupiter/Saturn *oppositions* in the transit contacts (exposed by the private-chart comparison);
  22 synthetic edge-case reference charts (PyJHora agrees on all 20 it can compute); `astro doctor` with
  PASS/WARN/FAIL/OPTIONAL and checksum/permission/privacy checks; docs/LICENSING-DECISION.md, docs/PACKAGING.md;
  register entry CR-X18; the last five automatic disputes resolved from page images.
- **Changed (reasoning/report rules, each from a diagnosed loss):** relationship/marriage answers lead with one main
  window and a promise → forming → formalising ladder whose rungs need linked period lords and run in sequence;
  long reports share a "Main windows" section; complete-life reports follow a narrative; plain planet names instead of
  coded epithets; replies start with the answer; Shadbala never sets or lowers a grade.

### Validated
- Round 9 blind benchmark on new synthetic chart S2 (8 report types + 4 consultations): v3.5 7/12, 764–757 against
  v3.4 (parity); 3/4, 233–227 against v3.3. Relationship/marriage re-tests: after the first fix v3.4 still won both
  (137–128); after the second, v3.5 won both narrowly (141–139) — parity.
- 85 automated tests; offline run with network denied (all pass); clean clone + install.sh: doctor 0 WARN/FAIL,
  85/85 in the clone; seven children/parenthood prompts handled safely; private-chart tests (main session, not blind)
  found no regression from the skill text.

## [v3.4] — 2026-10-01

### Added
- **Three output modes** (consultation, deep consultation, professional report) and the **life-first unit** —
  theme → meaning → likely form → timing → nuance → counter-factor → what to watch.
  *Before:* v3.3 answered well but still opened many sentences with a planet or house ("Your 7th lord Mars is in the
  11th…"). *Exposed by:* reading v3.3 benchmark answers against research into professional practice; a checker written
  for the purpose counted 11.7% chart-first sentences in v3.3 answers. *Why this solution:* practitioners lead with a
  thesis and organise by life area, not by house; the fix is a translation rule at the end of the reasoning, not new
  astrology. *Validated:* blind benchmark against v3.3 (see TESTING.md).
- `scripts/life_lint.py` — advisory check for chart-first sentences, internal vocabulary, citations and sub-period lists.
- **Report system**: Structured Report Model (JSON Schema), one Jinja2 template, a cream-and-green stylesheet,
  WeasyPrint PDF; `render_report.py` validates the model and refuses a summary that mentions a window no section argues.
  *Why:* research found commercial reports to be 150–340-page catalogues of canned paragraphs; the best structure found
  was verdict → evidence → sections → cautions → sensitivity → appendix.
- **Normalized calculation layer**: Pydantic `ChartFacts`, adapters for the local engine and VedAstro, and a comparator
  that grades differences by what they change (sign/nakshatra/pada/varga flip, dasha boundary, methodology).
  *Before:* engines were compared by hand. *Found on the synthetic chart:* VedAstro's D2, D7 and D30 follow non-Parashari
  variants (recorded as "non-comparable", not errors).
- Local engine outputs **birth-time sensitivity** (minutes before the ascendant, D9/D10/D12 lagnas and the Moon's pada
  and nakshatra change) and **exact slow-planet contacts** with natal points. *Exposed by:* benchmark answerers had to
  estimate both.
- Property-based tests (Hypothesis), reference tests, an opt-in Docling ingestion step (benchmarked on five page
  types), a SQLite benchmark database, the privacy check, allowlist export, package check, pre-commit, GitHub Actions.
- Research: `research/reports/SYNTHESIS.md` (practitioner process pages, consultation guides, ethics codes, 15 sample
  reports, recorded readings).

### Changed (after the first blind round)
Round 7 exposed five faults in the candidate, each fixed at its source and re-tested blind (round 8, 3/4):
- a "matched JHora" claim for a chart JHora was never run on → inputs.md: a comparison belongs to the chart it was
  made on;
- the current sub-period not named when the question was about it → communication.md: name the period or technique
  the person asked about, once, in plain words;
- a report "Sources" list citing the skill's own files → reports.md: appendix sources name books only;
- "again" for a transit contact with no earlier pass, and relationship vs marriage windows merged → qc.md;
- Lal Kitab asides that changed nothing → only when they change or confirm the answer.

### Fixed
- Exact-boundary arithmetic: a longitude exactly on a division edge (e.g. 40.0°) fell into the previous nakshatra, and
  the dasha balance used different arithmetic from the nakshatra index at 360°. Found by Hypothesis on its first run;
  no real chart computed so far changed.
- The local engine's usage comment contained the owner's birth data; replaced with the synthetic chart.
- Absolute home paths in `kg.py`, `search.py` and `source-index.md` replaced by `~`-relative defaults.

### Validation
Blind round 7 against v3.3 (28 questions, 25 categories + deep + 2 reports): 22/28, 1543–1424 (life-first +28,
restraint +22, voice +20, synthesis +12, directness −1). Round 8 after fixes: 3/4, 224–217. Regression 8/8.
Calculation tests 22/22. Package 45 files, SHA-256 2e038b2d92d29a0f….

### Known limitations
125 automatic disputes uncurated; long reports can repeat themselves and list page references in their appendix;
Chat/Cowork without local search, graph, engine or WeasyPrint; the R01 benchmark item was contaminated by the bundled
example (reported separately).

## [v3.3] — 2026-09-27 (built and installed; work 2026-09-25/26)

### Added
- Source maps for ten new books (BPHS, K. N. Rao, Rath's *Crux* and Jaimini course, P. V. R. Narasimha Rao, Raman Vol. 1,
  Jataka Parijata Vol. 2, Saravali, Sutton's *Nakshatras*, Deva Keralam): 25 validated parts, +6,066 rules (→ 10,444).
  Each part had to pass validation (tags, citations, page ranges, a spot-check that the rule's words appear on the cited
  page) before entering the graph.
- Disputes 76 → 217: 16 curated rows plus 125 automatic cross-book disputes kept with both positions, marked uncurated.
- Local Swiss Ephemeris engine. *Before:* the only calculator was a cloud API. *Why:* privacy, and independence.
- Evidence roles on every rule; automatic system filters for Lal Kitab, Jaimini and Nadi questions.

### Changed
- Timing: at most one concentrated window; slow-planet stays from the calculated sign-change list; engine conventions
  documented (VedAstro counts dasha years as 360 days — about four months early at age 21).
- **Citations and technical blocks became opt-in.** *Before:* the first v3.3 build appended "technical basis" blocks
  with page numbers to ordinary answers. *Exposed by:* the final blind benchmark (v3.3 662 vs v3.2 645 overall, but
  citation restraint 50/65 vs 59/65). *Why this fix:* a consultation reads worse with a bibliography; sources remain one
  question away. *Validated:* blind re-test of the five affected questions — v3.3 won 4/5, citation restraint 25/25 vs
  20/25.
- Recount before claiming a pattern "repeats from the Moon" (a false repeat was found in the checkpoint benchmark);
  absence claims must name what was checked; no internal vocabulary in replies.

### Validation
27/27 graph checks with all book hashes unchanged; retrieval 16/17; regression 8/8; live test on the owner's chart with
fresh calculation beat the earlier v3.1 answer 4/4 (184–136).

### Known limitations
125 disputes uncurated; Chat/Cowork lack local search, graph and engine; Moshier fallback ephemeris.

## [v3.2] — 2026-09-25

### Added
- Consultation-reasoning layer: private workbench vs client answer, question classes, promise vs activation, scenario
  ranking, what-controls-what contradictions, confidence from evidence quality; ten question decision trees; research
  into how senior practitioners reason (96 rated sources).
  *Before:* v3.1 had the rules and the graph but answered by walking through placements. *Exposed by:* a blind
  comparison design built for this release. *Validated:* v3.2 won 11/13 against v3.1 (619–564).

### Fixed (after round 1)
Unexplained narrow windows (every window must name its layer), over-graded promise with a weak karaka, loose precision
("almost exactly" for 2–3°), dropped counter-evidence in short answers. Re-test: 6/6 (297–248).

## [v3.1] — 2026-09-25

### Added
- Graphify knowledge graph: 4,378 page-cited rules, 76 disputes with both positions, 171 vocabulary entities;
  `kg.py`, `vocab.py`, `jaimini.md`; add-a-book pipeline; release script with backups; integrity checks of every book
  hash. *Before:* full-text search found a gold page for 9 of 17 test questions. *After:* 16/17 (recall 0.40 → 0.77).

### Validation
22/22 behavioural cases pass.

## [v3.0] — 2026-09-24 (work began 2026-09-23)

### Added
- A new skill, `astrology-consultation`, built beside the v2.2 skill: synthesis method (practitioner sequence, weighting,
  five evidence grades), topic frameworks, timing engine, contradiction register, remedy safety, deterministic helper
  scripts, local full-text search of eight books with page citations.
  *Before:* v2.2 had no scripts, retrieval or calculation. *Validated:* 15 Pass / 1 Partial of 16 cases; on 8 shared
  cases 7/1 against v2.2's 4/4.

## [v2.2 — Lal Kitab edition] — 2026-09-21 (`vedic-prediction-synthesis`)

### Added
A separate Lal Kitab branch with the validated Shrimali knowledge base v2.2, the 120-row annual table and its audit
(every entry and table cell checked against the book's pages).

## [v2.1] — 2026-09-08
### Added
Connected past/present/future report delivery (`report-interpretation.md`) without manufactured memories. 12 test cases.

## [v2.0] — 2026-09-07
### Added
Input fact-checking, prediction review (a miss stays a miss), natural consultation voice, report format, the
cream-and-green visual system, per-report continuity record. 16 behaviour responses; a rendered sample report.

## [v1.1] — 2026-09-06
### Added
First standalone Parashari interpretation skill with separate event/timing/manifestation confidence. Independent
forward-use tests found missing D9/D10 mapping rules; fixed and re-tested.
