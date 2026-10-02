# Packaging: private full installation vs public repository

> Updated 2026-10-03: the public side is now its own repository built by `tools/export_public.py` (Claude
> marketplace + plugin), and the private repository is the full archive (`export_repo.py --archive`). See
> [REPOSITORY-EDITIONS.md](REPOSITORY-EDITIONS.md) and [MARKETPLACE.md](MARKETPLACE.md); §2 below describes the
> earlier single-repository export and is kept for history.

Two different things, built by different paths. Nothing moves from the private side to the public side except
through the allowlist export and its checks.

## 1. Private / full local installation (the owner's Mac)

| Contains | Where |
|---|---|
| The skill (source) and the `astro` engine/service | `_skill_workspace/astrology-prediction/`, `_skill_workspace/astro/` |
| Swiss Ephemeris data files (pinned SHA-256) | `_skill_workspace/ephe/` or `~/.local/share/astrology-consultation/ephe/` |
| The books (legally obtained PDFs), extracted text, source maps, full-text index, Graphify knowledge graph | `Astrology Books/`, `_skill_workspace/{text,sourcemaps,index,graphify-out,knowledge}` |
| Lal Kitab knowledge base (book derivative) | `astrology-prediction/data/lal-kitab/` |
| Personal charts, private benchmarks, reports, prediction log | `_skill_workspace/private/`, `~/.local/share/astrology-consultation/` (mode 700/600) |
| Settings | `~/.config/astrology-consultation/config.toml` (mode 600) |

Installed copies: Claude Code `~/.claude/skills/astrology-consultation/` (from `release_skill.py`); the `.skill`
package in `releases/`. The package is checked by `check_package.py`: no books, no book-derived text beyond the
skill's own references, no personal data.

## 2. Public distributable repository

Built only by `tools/export_repo.py` (an **allowlist** — files not listed are never copied). `--public` additionally
removes the Lal Kitab knowledge base. Every export is then checked by `tools/privacy_check.py` (personal terms kept
outside the repository), Gitleaks and the pre-commit hooks; CI repeats the checks.

| Included | Excluded (always) |
|---|---|
| `astro/` engine and service, `tools/` code, tests with **synthetic** fixtures and reference charts | books, extracted page text, source maps, index, knowledge graph |
| the skill: `SKILL.md`, `references/`, `scripts/`, report template | the Lal Kitab KB (`--public`) |
| docs, `install.sh`, `pyproject.toml`, CI | personal charts, private benchmarks, reports, the prediction log, settings |
| `knowledge/catalog.json` (bibliographic metadata + fingerprints only, so users can ingest their own copies) | Swiss Ephemeris binaries (users fetch them with `astro setup --ephemeris`, checksum-verified) |
| | secrets of any kind |

Verified 2026-10-03 (`export_repo.py --public` into a scratch folder): 161 files, 1.7 MB; no PDFs, SQLite files, graph,
source-map parts, private files or ephemeris binaries; the only "lal-kitab" file is the skill's own method note;
privacy check 0 findings; Gitleaks clean.

A public user gets: the calculation engine and service (full), the skill's method and report system (full), Lal
Kitab method notes without the knowledge base, and book search/graph only after ingesting their own books
(`astro add-book`).

## 3. Rules

- The private repository is never made public; the public repository is a separate allowlist export ([LICENSING-DECISION.md](LICENSING-DECISION.md): split licence, decided 2026-10-03).
- Personal data never enters tests, fixtures, docs, CI or packages; benchmark charts used publicly are synthetic.
- A file reaches the public side only by being added to the export allowlist on purpose.
