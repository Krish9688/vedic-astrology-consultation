# Licensing decision paper (2026-10-03)

Engineering analysis, not legal advice. **Decided 2026-10-03: option B (split licence)**, applied in the public
repository (`LICENSE`, `LICENSES/`, `plugin.json` `license`, engine `pyproject.toml`). Licences below were read from the installed packages' licence files and metadata on 2026-10-03.

## 1. What the project contains

| Part | Imports / contains | Distributed publicly? |
|---|---|---|
| `astro/` (engine, service, MCP, REST, CLI) | pyswisseph (Swiss Ephemeris) | yes (code) |
| `tools/` ingestion (OCR, text extraction) | PyMuPDF; optional Docling | yes (code) |
| `tools/kg/`, `tools/calc/` wrappers | `astro`; Graphify (in its own environment) | yes (code) |
| Skill package (`SKILL.md`, `references/`, `scripts/`, report template) | standard library, Jinja2, WeasyPrint; **does not import pyswisseph or PyMuPDF** (verified) | yes (`.skill`) |
| Contradiction register, source index | short paraphrases of books with page references | yes — inside the skill |
| Lal Kitab knowledge base | detailed derivative of a copyrighted book | **no** (left out of public exports) |
| Books, extracted text, source maps, index, graph | copyrighted material and derivatives | **never** |
| Private charts, benchmarks, reports | personal data | **never** |

## 2. Third-party licences (verified)

| Component | Licence | Bundled? | Effect |
|---|---|---|---|
| pyswisseph 2.10.3.2 / Swiss Ephemeris | **AGPL-3.0** (or Astrodienst's paid Professional Licence) | dependency of `astro/` | code that links it and is distributed — or served to others over a network — must be AGPL-compatible, unless the professional licence is bought |
| PyMuPDF 1.28 | **AGPL-3.0** or Artifex commercial | dependency of `tools/` ingestion | same as above for the ingestion tools |
| PyJHora 4.8.7 | **AGPL-3.0** per its LICENSE file (its package metadata says MIT — inconsistent; treat as AGPL) | **not bundled**, validation only, separate environment | none, as long as it is never imported or shipped |
| Graphify 0.9.67 | Apache-2.0 (vendored copy also MIT) | used to build the graph; `vendor/` is not exported | keep its NOTICE if ever vendored |
| Docling 2.130, docling-ibm-models | MIT; model weights are downloaded by the user at run time | optional, not bundled | check model cards before bundling any weights |
| pypdfium2 | BSD-3-Clause / Apache-2.0 (+ PDFium licences) | optional | compatible |
| mcp, FastAPI, Pydantic, anyio | MIT | dependencies | compatible with anything |
| uvicorn, httpx, Starlette, Jinja2, WeasyPrint, networkx | BSD | dependencies | compatible |
| Hypothesis | MPL-2.0 | tests only | compatible |

## 3. Options

| Option | Code | Skill text | Pros | Cons |
|---|---|---|---|---|
| **A. Everything AGPL-3.0-or-later** (text CC BY-SA 4.0) | AGPL | CC BY-SA | simplest; clearly compliant with Swiss Ephemeris; network-service case covered | discourages reuse of the skill in plugins and marketplaces even though the skill never touches Swiss Ephemeris |
| **B. Split by what links Swiss Ephemeris** | `astro/` + ingestion tools: AGPL-3.0-or-later; skill scripts and report template: Apache-2.0 | CC BY 4.0 | the engine stays AGPL as required; the skill package — the part people install into Claude/ChatGPT — is freely reusable; matches the architecture (the skill reaches the engine only over MCP/REST/CLI) | two licences to explain; contributors must know which side their code is on |
| **C. Permissive everything + buy the Swiss Ephemeris Professional Licence** | MIT/Apache | CC BY 4.0 | maximum reuse, commercial products possible | cost; PyMuPDF would also need a commercial licence or replacement; obligations pass to anyone redistributing |
| D. Keep "all rights reserved" (status quo) | — | — | full control | others cannot legally use or contribute; incompatible with an open plugin ecosystem |

## 4. Obligations under the recommended option (B)

- **AGPL side** (`astro/`, ingestion tools): publish complete corresponding source for any distributed version; if the
  REST/MCP service is offered to *other people over a network* (remote mode), offer them the source of the running
  version (AGPL §13). Local, single-user use triggers nothing. Keep Swiss Ephemeris's copyright notices.
- **Apache side** (skill scripts, template): keep the licence and NOTICE; state changes. No copyleft.
- **CC BY 4.0** (skill prose): attribution on reuse.
- **Never relicensed:** book quotations and paraphrases stay short and attributed; the Lal Kitab KB and all
  book-derived files stay out of public releases.

## 5. Compatibility checks

- AGPL code may use MIT/BSD/Apache-2.0/MPL-2.0 libraries — all present dependencies are compatible.
- The skill package does not import or bundle AGPL code, so it can carry Apache-2.0/CC BY 4.0.
- Future plugin distribution (Claude skills, ChatGPT/Codex skills, MCP registries): ship the skill under B's permissive
  terms; ship the engine separately as an AGPL MCP server the user runs locally — the architecture already in place.
- Before going public: review the contradiction register and source index for quotation length (both ship inside the
  skill package).

## 6. Recommendation

**Option B**: AGPL-3.0-or-later for `astro/` and the ingestion tools; Apache-2.0 for the skill's scripts and report
template; CC BY 4.0 for the skill's method text and documentation. It is compliant without buying a licence and
friendly to the plugin ecosystem the project is aiming at. (This refines the earlier all-AGPL recommendation in
LICENSING.md, after confirming the skill package never links Swiss Ephemeris.)

**Owner's decision (2026-10-03): B**, with CC BY 4.0 for the method text and documentation. The Lal Kitab knowledge
base and all book-derived files stay out of the public repository; see [REPOSITORY-EDITIONS.md](REPOSITORY-EDITIONS.md).
