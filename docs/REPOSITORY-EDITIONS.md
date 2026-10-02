# Repository editions

The project lives in one local workspace and is published as two GitHub repositories, each built by its own
allowlist exporter. Nothing reaches either repository except through these exporters and their checks.

| | Public distribution | Private development archive |
|---|---|---|
| Repository | [`Krish9688/vedic-astrology-consultation`](https://github.com/Krish9688/vedic-astrology-consultation) (public) | `Krish9688/astrology-consultation` (private; created 2026-10-01, history preserved) |
| Purpose | install and use: Claude marketplace + plugin, engine, MCP/REST/CLI, docs | rebuild everything: all source, research, analysis, release history, environments |
| Built by | `python3 tools/export_public.py --repo <clone> --check` | `python3 tools/export_repo.py --archive --repo <clone>` |
| Layout | marketplace root; plugin at `plugins/astrology-consultation/` (skill, engine source, launcher, commands, MCP config) | workspace layout: `astro/`, `skill/`, `tools/`, `plugin/`, `public-root/`, `sourcemaps/`, `knowledge/`, `releases/`, `legacy/`, `archive/` |
| Licence | split: AGPL-3.0-or-later (engine, service, tools), Apache-2.0 (skill scripts, templates, plugin files), CC BY 4.0 (method text, docs) | same, plus material that is not licensed for redistribution (below) |
| Lal Kitab knowledge base | **excluded** (detailed derivative of a copyrighted book); the Varshaphal table and method notes are included | included (the owner's own derived work) |
| Book-derived analysis (source maps, chapter maps, knowledge graph, extraction) | excluded | included; the graph and extraction gzip-compressed (3.9 MB and 3.4 MB) |
| Release packages (`.skill`) | the current public package is attached to the public release | every historical package, byte-identical |
| Books (PDFs), page text, full-text index | never | never — local only, listed with SHA-256 in `archive/local-only-manifest.json` |
| Personal charts, reports, private benchmarks, prediction log | never | never — the owner's rule; counts only in the manifest |
| Secrets, credentials, tokens, cookies | never | never |
| Virtual environments, caches, downloads | never | never — package lists in `archive/environments/` |
| CI | full: Gitleaks (history), privacy, versions, official plugin validator, lint, tests, launcher + MCP smoke, report render, package check | code only: shallow sparse checkout (no archived analysis on runners); full-history Gitleaks and graph checks run locally before each push |

## Gates before every push

| Gate | Public | Private |
|---|---|---|
| `tools/privacy_check.py` (personal terms from a local untracked list, home paths, e-mails, blocked folders/extensions, > 5 MB) | public rules | `--archive` rules: also allows source/chapter maps, the compressed graph and historical packages — packages are opened and scanned member by member for personal terms |
| Gitleaks | `gitleaks dir` on the export + history in CI | `gitleaks git` on the full history, locally |
| Version consistency (`tools/check_versions.py`) | yes | yes |
| `claude plugin validate --strict` (marketplace and plugin) | yes | plugin |
| Tests in a fresh environment | yes (no ephemeris, offline) | yes |
| Package check (`tools/check_package.py`) | yes | yes |

## How a change flows

1. Edit in the workspace (`_skill_workspace/`), run the tests.
2. Private archive: `export_repo.py --archive` into the clone → pre-commit (Gitleaks, privacy `--archive`, Ruff,
   hygiene) → commit → `gitleaks git` → push.
3. Public: `export_public.py --repo <clone> --check` (all gates) → commit → push → CI → release tag `vX.Y.Z`
   (the marketplace's rollback point).

The two repositories are never merged and the private one is never made public. The public repository can be rebuilt
from the private one (`public-root/`, `plugin/` and the code are all in it).
