# Architecture

The system separates five responsibilities that are easy to blur in astrology software: **calculating** a chart,
**storing and retrieving** what books say, **researching** practice, **reasoning** about a person's question, and
**presenting** the answer. Each layer has one job and a clear interface to the next.

```
                         ┌──────────────────────┐
                         │   PUBLIC RESEARCH    │  Agent Reach (search, page reader, transcripts)
                         └──────────┬───────────┘  → research/ (methodology only, paraphrased)
                                    ↓
ASTROLOGY BOOKS → text layer / Apple Vision OCR / Docling (opt-in) → page text → source maps (validated)
                → full-text index (SQLite FTS5) + Graphify knowledge graph (rules, disputes, provenance)
                                    │  retrieval only: kg.py, search.py
Birth data → local engine (Swiss Ephemeris) → adapter → ChartFacts ─┐
          └→ VedAstro (cloud, consent)      → adapter → ChartFacts ─┴→ compare → ValidatedChartFacts
                                    ↓
                      question / report request
                                    ↓
              CONSULTATION REASONING (the skill: workbench)
        question class → natal promise → activation → trigger → scenarios
        → contradictions → confidence per claim → what to expose
                                    ↓
                        prediction synthesis (life units)
                 ┌──────────────────┴──────────────────┐
     A. consultation / B. deep consultation      C. Structured Report Model (JSON)
        (chat, life-first prose)                        ↓ render_report.py (checks)
                                                   Jinja2 → HTML/CSS → WeasyPrint → PDF
```

Development around it: Skill Creator (evaluation method), pytest + Hypothesis, Ruff, Ponytail, the SQLite benchmark
database. Release and security: git, GitHub CLI, Gitleaks, pre-commit, GitHub Actions, the privacy check.

## Layers

| Layer | Components | Does | Does not |
|---|---|---|---|
| Calculation | `tools/calc/` (local_chart, schema, adapters, compare); VedAstro MCP | positions, vargas, dashas, transits, sign changes, slow-planet contacts, birth-time sensitivity; cross-engine agreement | interpret |
| Derivation | skill `scripts/chart_facts.py`, `varshaphal.py` | houses, lordships, aspects, dignity, dispositors, D9/D10, PD XV tests, Lal Kitab states and annual chart — deterministic, self-tested | calculate positions |
| Knowledge | books → `text/` → `sourcemaps/` → `knowledge/extraction.json` → `graphify-out/graph.json`; `index/library.sqlite` | store and retrieve rules with book/page/verse/tier/school, disputes with both sides, related rules | decide predictions |
| Research | Agent Reach; `research/` | learn from public practice | receive chart data |
| Reasoning | skill `SKILL.md` + `references/` | the judgement: question-first, promise vs activation, scenarios, contradictions, calibrated confidence, the life-first answer | recite the chart |
| Presentation | `communication.md`, `reports.md`, `scripts/life_lint.py`, `scripts/render_report.py`, `assets/report/` | three output modes; checked reports | invent content |

## Folder layout

```
Astrology Books/                         the owner's library (books; never published)
├── *.pdf                                18 books (authoritative evidence; hashes verified on every rebuild)
├── LalKitab_v2.2_Reference_and_Skill_Bundle/   validated Lal Kitab KB/CSV/audit + the v2.2 skill (unchanged)
├── releases/                            current package, previous/ (all versions), manifests/, release notes
└── _skill_workspace/
    ├── astrology-prediction/            THE SKILL (source; installed as ~/.claude/skills/astrology-consultation)
    │   ├── SKILL.md, references/ (22 files), scripts/ (stdlib), assets/report/, data/lal-kitab/, tests/
    ├── tools/                           calc/, kg/, bench/, OCR, Docling, release, export, privacy, benchmark DB
    ├── tests/                           pytest + Hypothesis; synthetic fixtures (S1 local + VedAstro)
    ├── schemas/                         chart_facts.schema.json
    ├── text/, index/, sourcemaps/, knowledge/, graphify-out/   book-derived (private)
    ├── validation/                      graph checks, retrieval and citation tests, Docling benchmark
    ├── private/                         personal charts and benchmarks (never published)
    ├── research/                        consultation and report research (methodology)
    ├── backups/                         pre-release snapshots with SHA256SUMS
    ├── repo-root/                       README, CHANGELOG, CI and tooling config for the repository
    └── docs/                            this documentation
```

The git repository (`~/Documents/astrology-consultation`) is generated from this workspace by
`tools/export_repo.py` (allowlist + sanitisation) — see [RELEASE-PROCESS.md](RELEASE-PROCESS.md).

## Why the skill is split into many files

A focused question loads SKILL.md (~8 KB), consultation-reasoning, one question tree, one topic file, timing and
communication — roughly 50–60 KB; the books are never loaded wholesale (retrieval returns single rules or pages).
Reports add reports.md and the renderer. Progressive loading keeps answers fast and keeps each rule in one place.

## Environments

One Python environment per responsibility (calculation/tests, knowledge graph, reports, Docling) — see
[TOOLING-INVENTORY.md](TOOLING-INVENTORY.md). The skill's own scripts use only the standard library (plus Jinja2 to
render reports), so they run in Claude Chat/Cowork too; the local engine, index and graph exist only on the owner's Mac.
