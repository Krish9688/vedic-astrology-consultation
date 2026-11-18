# Repository editions

> **What:** what the public and private repositories hold, how each is built and checked, and how a change flows. **Read it when:** you export, push or decide where a file belongs.
> **Last checked:** 2026-11-13 (public contents, CI and gates rows; the older tables not re-checked).
> **Related:** RELEASE-PROCESS.md, COPYRIGHT.md, LICENSING-DECISION.md.

The project lives in one local workspace and is published as two GitHub repositories, each built by its own
allowlist exporter. Nothing reaches either repository except through these exporters and their checks.

| | Public distribution | Private development archive |
|---|---|---|
| Repository | [`Krish9688/vedic-astrology-consultation`](https://github.com/Krish9688/vedic-astrology-consultation) (public) | `Krish9688/astrology-consultation` (private; created 2026-10-01, history preserved) |
| Purpose | the final product only (owner rule 2026-11-13): what a user needs to install and run the Claude marketplace + plugin, engine, MCP/REST/CLI, `astro add-book`, user docs | everything: all source, tests, research, analysis, rough documents, working notes, release history, environments |
| Tests, dev tools, working docs | **excluded** except one install smoke test (`tools/mcp_smoke.py`). Out: `tests/`, the skill's `tests/`, `validation/` (except `graph_checks.py` and `citation_test.py`, which `astro add-book` runs), `tools/calc/`, `tools/check_*.py`, `docs/ROADMAP.md`, `docs/TESTING.md`, the generated code map `docs/project-graph/` | included |
| Accuracy pack | the signed rubric (`docs/ACCURACY-RUBRIC.md`), the score reports (`docs/accuracy/report-*.md`) and `FREEZE-PUBLIC.md` (their hash record, written by the exporter) | also the frozen cases and fixtures, `FREEZE.md`, audit notes, the scorer (`tools/accuracy_*.py`, `tools/oracle_pyjhora.py`) and the chart registry |
| Built by | `python3 tools/export_public.py --repo <clone> --check` | `python3 tools/export_repo.py --archive --repo <clone>` |
| Layout | marketplace root; plugin at `plugins/astrology-consultation/` (skill, engine source, launcher, commands, MCP config) | workspace layout: `astro/`, `skill/`, `tools/`, `plugin/`, `public-root/`, `sourcemaps/`, `knowledge/`, `releases/`, `legacy/`, `archive/` |
| Licence | split: AGPL-3.0-or-later (engine, service, tools), Apache-2.0 (skill scripts, templates, plugin files), CC BY 4.0 (method text, docs) | same, plus material that is not licensed for redistribution (below) |
| Lal Kitab rules, code and remedies (`lal_kitab.py`, `varshaphal.py`, `lk_remedies.py`, method, timing, remedy-safety and contradiction notes, tests and synthetic fixtures) | **included from 3.7.0** (owner decision 2026-10-25, reversing council option B2 of 2026-10-12, which had removed them in 3.6.1). They are the owner's own wording of books still in copyright; their redistribution status is not legally cleared and the owner accepts that risk ([COPYRIGHT.md](COPYRIGHT.md)) | included |
| Lal Kitab knowledge base (Shrimali notes, audit) and Varshaphal table (`data/lal-kitab/`) | **excluded** — the KEEP-OUT list in `tools/public_edition.py`; `varshaphal.py` says the table is not installed | included (the owner's derived material) |
| Book-derived analysis (source maps, chapter maps, knowledge graph, extraction), book and page text, PDFs, full-text index | excluded (KEEP-OUT gate) | included; the graph and extraction gzip-compressed (3.9 MB and 3.4 MB) |
| Release packages (`.skill`) | the current public package is attached to the public release | every historical package, byte-identical |
| Books (PDFs), page text, full-text index | never | never — local only, listed with SHA-256 in `archive/local-only-manifest.json` |
| Personal charts, reports, private benchmarks, prediction log | never | never — the owner's rule; counts only in the manifest |
| Secrets, credentials, tokens, cookies | never | never |
| Swiss Ephemeris binaries | never (users fetch them with `astro setup --ephemeris`, checksum-verified) | never (the owner's `ephe/` folder is a local download) |
| Virtual environments, caches, downloads | never | never — package lists in `archive/environments/` |
| CI | product checks: Gitleaks (history), privacy, official plugin validator, lint, one install smoke test (launcher builds the engine, serves MCP, computes a synthetic chart); no test suite | code only: shallow sparse checkout (no archived analysis on runners); full-history Gitleaks and graph checks run locally before each push |

## Gates before every push

| Gate | Public | Private |
|---|---|---|
| KEEP-OUT gate (`export_public.py`: fails on any KEEP-OUT path, knowledge-base or table signature, leftover edition marker, or a verbatim run of book text) | yes | — |
| `tools/privacy_check.py` (personal terms from a local untracked list, home paths, e-mails, blocked folders/extensions, > 5 MB) | public rules | `--archive` rules: also allows source/chapter maps, the compressed graph and historical packages — packages are opened and scanned member by member for personal terms |
| Gitleaks | `gitleaks dir` on the export + history in CI | `gitleaks git` on the full history, locally |
| Version consistency (`tools/check_versions.py`; on the export, run from the workspace) | yes | yes |
| Link check (`tools/check_links.py`; on the export, run from the workspace) | yes | yes |
| `claude plugin validate --strict` (marketplace and plugin) | yes | plugin |
| Full test suite | privately, before every export (not in the public repository) | yes |
| Install smoke test in a fresh environment (`tools/mcp_smoke.py`, no ephemeris) | yes | — |
| Package check (`tools/check_package.py`; on the export, run from the workspace) | yes | yes |

## How a change flows

1. Edit in the workspace (`_skill_workspace/`), run the full test suite (the public repository has none).
2. Private archive: `export_repo.py --archive` into the clone → pre-commit (Gitleaks, privacy `--archive`, Ruff,
   hygiene) → commit → `gitleaks git` → push.
3. Public: `export_public.py --repo <clone> --check` (all gates) → commit → push → CI → release tag `vX.Y.Z`
   (the marketplace's rollback point).

The two repositories are never merged and the private one is never made public. The public repository can be rebuilt
from the private one (`public-root/`, `plugin/` and the code are all in it).

## What a public user gets

The calculation engine and service (full), the skill's Parashari method and report system (full), the Lal Kitab rules,
code and remedies (from 3.7.0; not the knowledge base or the Varshaphal table), and book search and graph only after
ingesting their own books (`astro add-book`). The `.skill` package is checked by `tools/check_package.py`: no books, no
book-derived text beyond the skill's own references, no personal data.

## Rules

- The private repository is never made public; the public repository is a separate allowlist export
  ([LICENSING-DECISION.md](LICENSING-DECISION.md): split licence, decided 2026-10-03).
- Personal data never enters tests, fixtures, docs, CI or packages; benchmark charts used publicly are synthetic.
- A file reaches the public side only by being added to the export allowlist on purpose. Files not listed are never copied.
- Blocks marked private-edition in the skill and `data/lal-kitab/` never reach the public edition (the Lal Kitab scripts
  and notes do, from 3.7.0). Every export is also checked by `tools/privacy_check.py`, Gitleaks and the pre-commit hooks;
  CI repeats the checks.

