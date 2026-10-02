# Version history

The complete lineage of the skill, reconstructed on 2026-09-27 from the preserved packages, their manifests, backup
archives, release and implementation reports, test logs and file timestamps. **This project was not under git before
2026-10-01**: every package up to v3.4 predates the repository (v3.4's source is its first commit, three minutes after
its package was built; v3.5 was developed in it), and no historical commits were manufactured. Packages are
preserved unchanged in `releases/previous/` (machine-readable records in `releases/manifests/v*.json`, with SHA-256
computed from the files themselves).

**How dates were established** — strongest evidence first: a date written in the version's own release/implementation
report; the package archive's timestamp; backup-folder timestamps; test-log timestamps. Where a version was built on
one day and released the next, both are given. No date below is a guess; where evidence is weaker it says so.

## At a glance

| Version | Skill name | Date | Status | Package | SHA-256 (first 16) | Main change |
|---|---|---|---|---|---|---|
| v1.1 | vedic-prediction-synthesis | 2026-09-06 | superseded (predecessor) | `vedic-prediction-synthesis-v1.1.zip` | b136a628a034f623 | first standalone interpretation skill |
| v2.0 | vedic-prediction-synthesis | 2026-09-07 | superseded | `vedic-prediction-synthesis-v2.0.zip` | 66cacaf00c42107c | fact-checking, prediction review, report and visual system |
| v2.1 | vedic-prediction-synthesis | 2026-09-08 | superseded | `vedic-prediction-synthesis-v2.1.zip` | 37bed6a4d18276e1 | past/present/future report delivery |
| v2.2 (Lal Kitab edition) | vedic-prediction-synthesis | 2026-09-21 | superseded (kept beside v3) | `vedic-prediction-synthesis-lal-kitab-v2.2.skill` | 20b4b0c03ea31c60 | separate Lal Kitab branch with a validated knowledge base |
| v3.0 | astrology-consultation | built 2026-09-24 (work began 09-23) | archived | `astrology-consultation-v3.skill` | d1703b513621cb11 | new skill: synthesis method, timing engine, local book search |
| v3.1 | astrology-consultation | 2026-09-25 | archived | `astrology-consultation-v3.1.skill` | 0c0810b6d20c2b38 | Graphify knowledge graph with provenance |
| v3.2 | astrology-consultation | 2026-09-25 | archived | `astrology-consultation-v3.2.skill` | 89fb35dc962c0ffc | consultation-reasoning layer |
| v3.3 | astrology-consultation | built and installed 2026-09-27 00:07 (work 09-25/26) | archived | `astrology-consultation-v3.3.skill` | 265ba20d051fa1cc | all 18 books source-mapped; local calculation engine |
| v3.4 | astrology-consultation | 2026-10-01 (development from 2026-09-27) | previous stable | `astrology-consultation-v3.4.skill` | 2e038b2d92d29a0f | life-first writing, three output modes, report system, normalized calculation layer |
| v3.5 | astrology-consultation | 2026-10-03 | **current stable** | `astrology-consultation-v3.5.skill` | 01a33c976195b20f | local strength/Jaimini/sensitivity engine, full ephemeris, MCP/REST/CLI service, curated disputes |
| 3.5.0 (public plugin) | astrology-consultation | 2026-10-03 | **current public release** | `astrology-consultation-3.5.0.skill` | a2f8a42fe3b6d794 | v3.5 as a Claude marketplace plugin; portable library lookup; no Lal Kitab knowledge base |

Also preserved: the first v3.2 build (installed 10:44, replaced at 10:58 after page-checking citations to the newly
added books) as `releases/previous/astrology-consultation-v3.2-first-build-2026-09-25_1044.tgz`, and a 2026-09-21
re-zip of v2.1 whose contents are identical to v2.1 (`…-v2.1-repack-2026-09-21.skill`).

---

## v1.1 — `vedic-prediction-synthesis` (2026-09-06)

- **Date evidence:** final audit dated 6 September 2026 (revision 1.1); archive timestamp 2026-09-06 19:02; the package
  manifest's archive hash matches the preserved file.
- **Status:** superseded predecessor. Built in a separate project folder with a different AI environment (the package
  carries `agents/openai.yaml`); never installed globally, by the user's instruction to keep all data in the project.
- **Objective:** a standalone Parashari interpretation skill that accepts chart facts and period tables — no
  calculation engine, no personal dataset, no inherited skills.
- **Design:** validated inputs → D1 topic promise → strength/contradiction → stable varga → MD/AD activation → transit
  window → alternatives and confidence. Confidence means convergence within astrology, never probability; event,
  timing and manifestation assessed separately; repeated facts are not independent confirmations.
- **Testing:** six independent forward-use readings by a separate evaluator; the evaluator found that D9/D10 mapping
  rules were missing and that nominal vargas did not establish birth-time stability; both fixed; six retest readings;
  package and arithmetic checks.
- **Known limitations:** no scripts, no retrieval, no Lal Kitab. **Superseded by** v2.0.

## v2.0 (2026-09-07)

- **Date evidence:** implementation report and project state ("Current release: v2.0, 7 September 2026"); archive
  2026-09-07 15:20.
- **Why:** the user supplied reference reports for review; the review found failure modes to prevent (copied personal
  narrative, invented probability meters, rule-count voting, rescue explanations for missed predictions).
- **Changes:** input validation that challenges wrong interpretive labels and quarantines dependent conclusions;
  explicit dignity checks and yoga conditions; one authoritative period table; prediction review (a miss stays a miss);
  natural consultation language (the prediction fields became an internal checklist); `report.md` and `visuals.md`
  (the cream-and-green visual system still used today); a per-report continuity record.
- **Testing:** 16 independent behaviour responses; a rendered 9-page synthetic PDF; release checks.
- **Installed:** ChatGPT desktop app via a `~/.agents/skills` link (2026-09-07). **Superseded by** v2.1.

## v2.1 (2026-09-08)

- **Date evidence:** implementation report dated 8 September 2026; archive 2026-09-08 09:11.
- **Why:** readings covering several life periods felt like disconnected chapters.
- **Changes:** `report-interpretation.md` — connected past/present/future explanation without manufacturing memories
  or forcing a life story; updates to nine files; five unchanged byte for byte.
- **Testing:** 12 independent test cases in three request sets. **Superseded by** v2.2 (Lal Kitab edition).
  (The `~/.agents` link still serves this version to the ChatGPT app — verified 2026-09-27.)

## v2.2, Lal Kitab edition (2026-09-21)

- **Date evidence:** package notes "v2.2, 21 Sep 2026"; archive 2026-09-21 05:42; knowledge-base audit v2.2 dated
  21 September 2026.
- **Why:** the user wanted Lal Kitab readings, which use a different house system and rules that must not be mixed with
  Parashari lordship.
- **Changes:** a separate Lal Kitab branch; the Shrimali knowledge base v2.2, a 120-row Varshaphal table and the
  validation audit (108 planet-in-house entries checked line by line, every table row compared cell by cell with the
  page images); `consultation-voice.md`.
- **Testing:** the knowledge-base audit; later (2026-09-24) an 8-case comparison against v3: v2.2 4 Pass / 4 Partial.
- **Known limitations:** no scripts, retrieval or calculation; weaker timing. **Superseded by** v3.0 (built beside it;
  v2.2 left unchanged).

## v3.0 — `astrology-consultation` (built 2026-09-24)

- **Date evidence:** package built 2026-09-24 12:16; test log 12:15; changelog "2026-09-23/24"; the project inventory
  that started the work is dated 2026-09-23.
- **Why:** v2.2 could not look anything up in the books, did arithmetic by hand, and its timing technique was thin.
- **Changes:** a new skill beside v2.2 — `synthesis-method.md` (a 16-step practitioner sequence, weighting rules, the
  five evidence grades), four topic frameworks, `timing.md` (significators, dasha intensity, transit triggers, windows),
  a contradiction register, remedy-safety classification, `chart_facts.py` and `varshaphal.py` (deterministic helpers
  with self-tests), and local full-text search of eight books with page citations (Apple Vision OCR for scans).
- **Testing:** 16 cases (T01–T16): 15 Pass, 1 Partial (T01: the 5th house not examined for a relationship question), 0
  Fail; on the same 8 cases v3 scored 7 Pass / 1 Partial against v2.2's 4 / 4.
- **Installed:** Claude Code. **Superseded by** v3.1.

## v3.1 (2026-09-25)

- **Date evidence:** package 2026-09-25 03:55; install backup `installed-before-2026-09-25_035530` (v3 archived).
- **Why:** full-text search found a gold page for only 9 of 17 test questions; the skill could not ask "which books
  support or dispute this rule".
- **Changes:** Graphify knowledge graph — 4,378 page-cited rules, 3,459 pages, 76 recorded disputes with both
  positions, 171 vocabulary entities (English/Sanskrit/Hindi); `kg.py`, `vocab.py`, `jaimini.md`; an add-a-book
  pipeline and a release script with backups; integrity checks that verify every book's hash on each rebuild.
- **Testing:** 22 cases, 22/22 Pass (T01 now passes); gold-page recall full-text 0.40 → graph 0.73 → combined 0.77
  (16/17 questions).
- **Known limitation found later:** answers still walked through the chart placement by placement. **Superseded by**
  v3.2.

## v3.2 (2026-09-25)

- **Date evidence:** first build and install 10:44, final package 10:58 the same day (backups
  `installed-before-2026-09-25_104439` and `_105850`); the ten new books were added to the folder between 08:56 and
  10:04, and the final build page-checked BPHS/Jaimini citations in `jaimini.md`, `vargas.md` and `source-index.md`.
- **Why:** a blind comparison showed good rules but answers that read like chart recitals.
- **Changes:** `consultation-reasoning.md` (private workbench vs client answer; question classes; promise vs
  activation; scenario ranking; what-controls-what for contradictions; confidence from evidence quality),
  `question-trees.md` (ten decision trees), research into how senior practitioners reason (96 rated sources).
- **Testing:** blind benchmark against v3.1 — v3.2 won 11/13 (619–564). Four weaknesses were found and fixed
  (unexplained narrow windows, over-graded promise, loose precision, dropped counter-evidence); re-test 6/6 (297–248).
- **Superseded by** v3.3.

## v3.3 (built and installed 2026-09-27; previous stable)

- **Date evidence:** knowledge work and tests 2026-09-25/26 (source-map logs, benchmark rounds 3–5); round 6 and the
  build/install on 2026-09-27 at 00:07 (`release_skill.py` output; backup `installed-before-2026-09-27_000748`).
  Earlier notes gave "2026-09-26"; the package itself was built on the 27th.
- **Why:** ten new books (BPHS, K. N. Rao, Sanjay Rath's *Crux* and Jaimini course, P. V. R. Narasimha Rao, Raman
  Vol. 1, Jataka Parijata Vol. 2, Saravali, Komilla Sutton's *Nakshatras*, Deva Keralam) were searchable but unmapped;
  the only calculation path was a cloud API.
- **Knowledge changes:** 25 validated source-map parts (+6,066 rules → 10,444); disputes 76 → 217 (16 curated,
  125 automatic "uncurated" with both positions); evidence roles on every rule; automatic system filters so Lal
  Kitab, Jaimini and Nadi questions stay inside their system.
- **Calculation:** a local Swiss Ephemeris engine; the discovery that VedAstro counts dasha years as 360 days (about
  four months early at age 21) and that Shadbala differs between engines.
- **Reasoning changes (from testing):** at most one concentrated timing window; recount before claiming a pattern
  repeats from the Moon; slow-planet stays from the calculated sign-change list; absence claims name what was checked;
  no internal vocabulary.
- **A regression and its fix:** the final benchmark (v3.3 662 vs v3.2 645, 8 wins, 3 losses, 2 ties) showed v3.3
  appending "technical basis" blocks with page citations to ordinary answers; citation restraint scored 50/65 against
  v3.2's 59/65. Technical detail and citations were made opt-in; the affected questions were re-graded blind and
  v3.3 won 4/5 with citation restraint 25/25 vs 20/25.
- **Live test on the user's own chart:** v3.3 on freshly calculated data beat the earlier v3.1 answer 4/4 (184–136).
- **Other tests:** 27/27 graph checks with all 18 book hashes unchanged; retrieval 16/17; regression 8/8.
- **Known limitations:** 125 automatic disputes await curation; Claude Chat/Cowork cannot reach the local search,
  graph or engine; the local engine uses the Moshier fallback ephemeris; `kg.py`/`search.py` defaults contain an
  absolute home path (fixed in v3.4); answers still open many sentences with a planet or house.

## v3.5 (2026-10-03; current stable)

- **Why:** Shadbala and Ashtakavarga came only from a cloud engine whose numbers disagreed with others; birth-time
  margins were estimated by eye; the calculation could only be used inside Claude Code; 125 automatic cross-book
  disputes were uncurated.
- **Changes:** local Shadbala (BPHS/Raman), Ashtakavarga, Jaimini factors and Sripati bhavas; a birth-time sensitivity
  grid with robust/moderate/high/very-high classes, used by the skill; full Swiss Ephemeris files with a before/after
  benchmark; seven comparison verdicts; the vendor-neutral `astro` service (MCP, REST, CLI, privacy modes, install.sh);
  a consent-gated prediction log; contradiction register section F; renderer timeline/compact fixes; a SAFETY check that
  blocks fertility and death statements.
- **Date evidence:** round 9 benchmark, regression and fixes on 2026-10-02 (unpublished candidate rc1 built 17:33);
  final validation, rebuild and install 2026-10-03 03:18 (`release_skill.py`; backup
  `installed-before-2026-10-03_031853`); source committed three minutes later as `4dd3a54` (skill files identical,
  verified) — v3.5 is the first version developed inside the repository.
- **Faults found and fixed:** the Sun's required Shadbala (5 → 6.5 rupas, BPHS p299); a parenthood age and child window in
  a complete-life answer; "just reaches" for a 0.99 Shadbala ratio; one-page summaries rendering at 5–7 pages; two
  register rows misdescribing *Light on Life* (p89, p291); planetary war without BPHS's Venus rule; the arudha variant
  unnamed.
- **Testing:** round 9 on a new synthetic chart (8 report types + 4 consultations) vs v3.4 7/12, 764–757 (parity);
  vs v3.3 3/4, 233–227; relationship/marriage re-tests after fixes 128–137 then 141–139 (parity); 85 automated tests
  incl. 22 edge-case reference charts; offline run; clean install; children-safety prompts; private-chart tests
  (main session, not blind). Final validation also fixed a polar-latitude crash, the data-folder permissions and
  added Jupiter/Saturn oppositions. 85 automated tests at the release commit. Promotion rule: new capability, no
  regression in reasoning.
- **Known limitations:** private-chart tests ran in the main session, not blind (subagent answerers were blocked);
  no Chara/Yogini/Narayana dasha; no time-zone database.
- **Distribution (3.5.0, same day):** published as a Claude plugin marketplace in a new public repository
  (`Krish9688/vedic-astrology-consultation`) under the split licence; the plugin's skill is the v3.5 skill plus a
  portable library lookup (`paths.py`) and without the Lal Kitab knowledge base (package
  `astrology-consultation-3.5.0.skill`). See CHANGELOG [3.5.0] and docs/MARKETPLACE.md.

## v3.4 (2026-10-01; previous stable)

- **Why:** answers still lead with chart facts ("Your Mars is…") rather than with what they mean for the person;
  there was no professional report format; calculation engines were compared by hand; the project had no repository,
  no secret scanning and no CI.
- **Changes so far:** three output modes (consultation, deep consultation, professional report); the life-first unit
  (theme → meaning → likely form → timing → nuance → counter-factor → what to watch); `life_lint.py`; a Structured
  Report Model rendered by Jinja2 and WeasyPrint in the cream-and-green system; research into professional report
  practice; a normalized `ChartFacts` schema with engine adapters and an astrology-aware comparator; property-based
  calculation tests (which found and fixed an exact-boundary bug); an opt-in Docling ingestion step; a benchmark
  database; privacy/secret checks, pre-commit and CI.
- **Date evidence:** development and blind round 7 on 2026-09-27; round 8, regression and the build/install on
  2026-10-01 03:28 (`release_skill.py`; backup `installed-before-2026-10-01_032857`).
- **Faults found by the blind round and fixed:** a "matched JHora" claim for a chart JHora was never run on; the
  current period not named when asked about; report sources citing the skill's own files; "again" for a transit
  contact with no earlier pass; relationship and marriage windows merged; Lal Kitab asides that changed nothing.
- **Testing:** round 7 (28 questions, 25 categories + deep consultation + 2 reports) 22/28, 1543–1424; round 8 after
  fixes 3/4, 224–217; regression 8/8; calculation tests 22/22. Promotion rule met: better overall, no category
  regressed beyond a point.
- **Known limitations:** 125 automatic disputes uncurated; long reports can repeat themselves; Chat/Cowork lack local
  search, graph and engine; one benchmark item (R01) was contaminated by the bundled example and is reported apart.
