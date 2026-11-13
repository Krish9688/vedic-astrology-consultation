# Architecture

How the whole project is built: the parts, how data flows between them, what each edition contains and where the
version lives. Counts were made on 2026-11-12 (task T8.2) by listing the folders; they change when files are added.


## 1. The parts

| Part | What it is | Workspace folder |
|---|---|---|
| Engine | Python package `astro`. Calculates charts, dashas, transits, strength, panchang, matching. Facts only. | `astro/` |
| Skill | Instructions for the AI: method, topics, tone, safety, reports. Plus standard-library helper scripts. | `astrology-prediction/` |
| Knowledge | Book catalog, page text, source maps (rules with pages), full-text index, knowledge graph. | `knowledge/`, `text/`, `sourcemaps/`, `index/`, `graphify-out/` |
| Plugin | Claude marketplace plugin: MCP launcher, two extra skills, commands, one agent. | `plugin/`, `public-root/` |
| Tools | Exporters, privacy and link checks, version and package checks, graph builders, accuracy scorer. | `tools/` |
| Tests | pytest suite with synthetic or published fixtures. | `tests/` |
| Docs | Project documentation (this folder). | `docs/` |

## 2. Three separations

These never mix. Each has one job and hands plain data to the next.

| Separation | Who does it | Does | Never does |
|---|---|---|---|
| Calculation | `astro/` (engine) and the skill script `chart_facts.py` (derived facts: houses, lords, aspects) | numbers and facts | interpret |
| Retrieval | skill scripts `kg.py` (graph) and `search.py` (full-text index) | return a rule or a page with book, page and tier | decide a prediction |
| Interpretation | `SKILL.md` and `references/*.md`, read by the AI | judge, weigh, answer in life terms | invent positions, dates or verses |

## 3. Data flow: a consultation

```
birth input (date, time, UTC offset, place)
  → astro.service  (one service layer; CLI, REST and MCP all call it)
  → astro/calc/*   (Swiss Ephemeris via pyswisseph; Lahiri default)
  → engine facts (JSON)  + chart_facts.py derived facts
  → astro/routing.py picks the reference files for the question (analyze_question / prepare_consultation)
  → AI reads SKILL.md + listed references (skill://<path> over MCP)
  → retrieval when a rule needs a source: kg.py / search.py
  → answer in chat (life first)   or   report model JSON → render_report.py → HTML / PDF
```

Routing: `astro/routing.py` is the one list of which files a question loads. `ALWAYS` = `SKILL.md`,
`consultation-reasoning`, `inputs`, `question-trees`, `synthesis-method`, `communication`, `qc`; plus one
`topic-<name>.md` per matched topic; plus `timing.md` when the question asks "when". `SKILL.md` must agree
with it (tested by `tests/test_routing_manifest.py`).

## 4. Data flow: books into knowledge

```
book file (PDF/EPUB, read only)
  → knowledge/catalog.json        register: id, title, tier, system, SHA-256   (tools/kg/add_book.py register)
  → text/<ID>.jsonl                page text: text layer, Apple Vision OCR, or Docling   (add_book.py text)
  → sourcemaps/<ID>_partN.md       one bullet per rule, cited to a page   (written by an AI from sourcemaps/BRIEF.md)
  → knowledge/extraction.json      rules, concepts, disputes   (tools/kg/extract.py; also reads contradiction-register.md)
  → graphify-out/graph.json        knowledge graph   (tools/kg/build_graph.py)
  → index/library.sqlite           full-text index, one row per page   (tools/build_index.py)
  → kg.py / search.py at answer time
```

`add_book.py rebuild` runs the index, extraction, graph and `validation/graph_checks.py`. Steps: [ADD-A-BOOK.md](ADD-A-BOOK.md).


## 5. The engine (`astro/`)

| File | Job |
|---|---|
| `service.py` | The one service layer. Holds `VERSION`. Every front end calls it. |
| `cli.py`, `rest.py`, `mcp_server.py` | Front ends: command line, local REST API, MCP server. |
| `routing.py` | Which reference files a question loads (see section 3). |
| `config.py` | Settings and privacy modes (`config.toml`), including the skill folder. |
| `places.py` | Offline birthplace → coordinates and time zone (GeoNames, downloaded once). |
| `identity.py` | Report identity gate: does a report's printed birth data belong to this person? |
| `predictions.py` | Private prediction log (local SQLite; never over MCP or REST; never committed). |
| `calc/` (14 modules) | `engine` (positions, vargas, dashas; holds `ENGINE_VERSION`), `strength`, `jaimini`, `transit`, `tajika`, `chara`, `panchang`, `match`, `activation`, `applicability`, `sensitivity`, `compare`, `adapters`, `schema`. |

MCP: `astro/mcp_server.py` defines 28 tools (for example `prepare_consultation`, `calculate_birth_chart`, `get_dasha`,
`create_report`, `prepare_consultation_report`, `create_consultation_report`), one resource `skill://{path}` (read-only
skill files) and one prompt. The plugin starts it through `plugin/.mcp.json` → `plugin/scripts/astro mcp`; the server key there
is `astrology`.

`tools/calc/` (`local_chart`, `adapters`, `compare`, `schema`, `yoga_baserates`) is a compatibility layer: its own header
says the engine now lives in `astro/calc/engine.py`. `tests/test_regressions.py` and `tools/bench_db.py` mention it.
The old text of this file named `tools/calc/` as the calculation layer; that is out of date.

## 6. The skill (`astrology-prediction/`)

| Part | Content (counted 2026-11-12) |
|---|---|
| `SKILL.md` | Entry point: workflow, tools, rules, topic table. Heading carries the skill version (`v3.8`). |
| `references/` | 25 files (the old text said 22): method (`synthesis-method`, `consultation-reasoning`, `question-trees`, `timing`, `inputs`), voice and checks (`communication`, `qc`, `evidence-card`, `examples`), topics (4 `topic-*` files), systems (`vedic-natal`, `vargas`, `jaimini`, `lal-kitab-method`, `yoga-definitions`, `remedy-safety`), reports (`reports`, `consultation-report`, `report-audit`, `visuals`), sources (`source-index`, `contradiction-register`). |
| `scripts/` | 12 standard-library scripts: `chart_facts`, `chart_svg`, `consultation`, `kg`, `search`, `paths`, `vocab`, `life_lint`, `render_report`, `lal_kitab`, `lk_remedies`, `varshaphal`. |
| `assets/report/` | Jinja2 templates, CSS, report and consultation-model schemas, a synthetic example. |
| `tests/` | Test cases, requests, fixtures (`chart_A`, `chart_B`). `tests/results/` is never exported. |
| `data/lal-kitab/` | Private Lal Kitab knowledge base and Varshaphal table. Never public. |

A focused question loads about seven files, not the whole skill. Books are never loaded whole; retrieval returns
single rules or pages.

## 7. Two editions

One workspace feeds two git repositories. Allowlists decide what is copied; nothing is copied by default.

| | Private edition | Public edition |
|---|---|---|
| Repository | `astrology-consultation` | `vedic-astrology-consultation` |
| Built by | `tools/export_repo.py --archive` | `tools/export_public.py --repo <path>` |
| What decides | `ALLOW` + `ARCHIVE` lists in `export_repo.py` | `MAP` + `DOCS` lists in `export_public.py`, then `tools/public_edition.py` |
| Gate | `tools/archive-manifest.txt` (path + SHA-256 of every exported file) | `tools/public-manifest.txt` (same idea) plus KEEP-OUT, privacy, links, Gitleaks, Ruff, versions, plugin validate, package check, install smoke test (no test suite; product only, 2026-11-13) |
| Book-derived material | Catalog, extraction and graph (gzip), chapters, curation | Catalog metadata only (no file names, no hashes, no KB) |
| Lal Kitab | Code, rules, remedies, knowledge base, Varshaphal table | Code, rules, remedies (public since 3.7.0). No knowledge base, no table, no book text. |

Never in either repository: the books, `text/`, `index/`, `read/`, `private/`, `backups/`, `ephe/`, `vendor/`, `trash/`,
virtual environments.

Edition markers (applied by `tools/public_edition.py`, used by `export_public.py`):

| Marker | Effect |
|---|---|
| Markdown `<!-- private-edition -->` … `<!-- /private-edition -->` | Block removed from the public edition. |
| Markdown `<!-- public-edition` … `public-edition -->` | Block shown only in the public edition. |
| Python `# <private-edition>` … `# </private-edition>` | Block removed from the public edition; the rest must still compile. |

Marker lines stand alone, never inside a table. A malformed or leftover marker fails the export. The accuracy pack
(`docs/ACCURACY-RUBRIC.md`, `docs/accuracy/*`, `tools/accuracy_*.py`) is not edited; its public copies are redacted
by the exporter and listed with both hashes in `docs/accuracy/FREEZE-PUBLIC.md`.

## 8. Path map

| Workspace | Private repository | Public repository |
|---|---|---|
| `astrology-prediction/` | `skill/astrology-consultation/` | `plugins/astrology-consultation/skills/astrology-consultation/` |
| `astro/` | `astro/` | `plugins/astrology-consultation/engine/astro/` |
| `plugin/` | `plugin/` | `plugins/astrology-consultation/` (selected files) |
| `plugin/engine-pyproject.toml` | `plugin/engine-pyproject.toml` | `plugins/astrology-consultation/engine/pyproject.toml` |
| `public-root/` | `public-root/` | repository root |
| `repo-root/` (incl. `.claude/`, `.github/`) | repository root | not exported |
| `repo-root/CHANGELOG.md` | `CHANGELOG.md` | `CHANGELOG.md` |
| `docs/*.md` | `docs/` (all) | `docs/` (only names in `DOCS`) |
| `tests/` | `tests/` | `tests/` (`*.py`, fixtures, reference charts, LK goldens) |
| `tools/` | `tools/` | `tools/` (selected checks, `calc/`, `kg/`, accuracy) |
| `knowledge/catalog.json` | `knowledge/catalog.json` | `knowledge/catalog.json` (reduced) |
| `graphify-out/graph.json`, `knowledge/extraction.json` | `knowledge/graph/graph.json.gz`, `knowledge/extraction.json.gz` | not exported |


## 9. Where versions live

`tools/check_versions.py` requires these to match (run it inside a clone; in the workspace it stops with a missing-file error):

| File | Field |
|---|---|
| `plugin/.claude-plugin/plugin.json` | `"version"` |
| `plugin/engine-pyproject.toml` | `version =` |
| `repo-root/pyproject.toml` (private repository root) | `version =` (private check only) |
| `astro/service.py` | `VERSION =` |
| `astro/calc/engine.py` | `ENGINE_VERSION =` |
| `astrology-prediction/SKILL.md` | heading `…, vX.Y` (major.minor only) |

Not checked by any tool (update by hand): `repo-root/README.md` ("Current version"), `repo-root/CHANGELOG.md`,
`docs/CHANGELOG-v3.0-v3.3.md`, [VERSION-HISTORY.md](VERSION-HISTORY.md), the release notes in `releases/notes/vX.Y.md`
(`tools/release_skill.py` refuses to build without them).

## 10. Environments

One Python environment per job: `.venv` (engine, tests), `.venv-graphify` (graph), `.venv-report` (reports),
`.venv-docling` (Docling), `.venv-pyjhora` (cross-check). The skill scripts use only the standard library (plus Jinja2
for reports), so they also run in Claude Chat. The engine, index and graph run only on the owner's Mac.

More detail: [REPOSITORY-EDITIONS.md](REPOSITORY-EDITIONS.md), [KNOWLEDGE-SYSTEM.md](KNOWLEDGE-SYSTEM.md),
[CONSULTATION-REASONING.md](CONSULTATION-REASONING.md), [CALCULATION-ENGINES.md](CALCULATION-ENGINES.md),
[PRIVACY.md](PRIVACY.md); tests: `TESTING.md` (development repository).
