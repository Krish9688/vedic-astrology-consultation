# Vedic Astrology Consultation

Vedic astrology consultations and reports that reason the way a careful, experienced astrologer does — answering the
question actually asked, weighing the few chart factors that matter, keeping competing indications visible, timing
them, and saying how strongly the chart supports each conclusion. Calculations come from a private Swiss Ephemeris
engine that runs on your own computer.

| | |
|---|---|
| **Version** | 3.6.3 (2026-10-19) — plugin, engine and skill share one version; changes: [CHANGELOG](CHANGELOG.md) |
| **Install** | Claude plugin marketplace (below), or the standalone engine for any MCP client |
| **Platforms** | macOS and Linux. Windows: use WSL 2 (works as Linux; not tested by the project). Native Windows is not supported. |
| **Privacy** | private by default: calculation is local, nothing is sent anywhere |
| **Traditions** | Parashari (primary); Jaimini as a separate, labelled system. Lal Kitab is not part of this edition |
| **Licence** | AGPL-3.0-or-later (engine) · Apache-2.0 (skill scripts, plugin files) · CC BY 4.0 (method text, docs) — [LICENSE](LICENSE) |

> Astrology's predictive validity is not scientifically established. The consultation describes what a tradition's
> documented methods indicate and how strongly its factors agree. It never claims certainty and refuses death,
> diagnosis, fertility, legal and investment verdicts.

## Project status

- **Released:** 3.6.3 (2026-10-19). Changes after it are listed under *Unreleased* in the
  [CHANGELOG](CHANGELOG.md) and ship only with the next release.
- **Maintained by one person**; issues and pull requests are read, but there is no support schedule.
- **Scope is deliberately narrow:** Parashari with an optional Jaimini lens. Other systems (Lal Kitab, KP, Western,
  numerology) are not part of this edition.

## Install in Claude

**Claude desktop app or claude.ai:** **Customize → Plugins → Add → Add marketplace**, enter
`Krish9688/vedic-astrology-consultation`, then install **Astrology Consultation (Vedic)** (from Anthropic's
documentation; not yet verified by this project).

**Claude Code:**
```bash
claude plugin marketplace add Krish9688/vedic-astrology-consultation
```
```bash
claude plugin install astrology-consultation@vedic-astrology
```
Then, in a session: `/astrology-consultation:setup` (builds the local engine and downloads the ephemeris; needs
Python 3.11+ or [uv](https://docs.astral.sh/uv/) and internet once), then `/reload-plugins`. Ask:

- "Calculate my chart — born 14 March 1992, 09:40, UTC+0, London (51.5N, 0.12W)"
- "What changes in my career over the next few years?"
- "Will I be in a serious relationship in the next two years?"
- "Create my 12-month report"

(That birth is the project's synthetic test chart, not a real person.)

| What you get | Claude Code | Cowork (on your computer) | claude.ai chat |
|---|---|---|---|
| Consultation skill (method, timing, safety, report layout) | yes | expected; not yet verified | documented |
| Local engine: 15 MCP tools (chart, vargas, dashas, transits, Shadbala, Ashtakavarga, Jaimini, birth-time sensitivity, reports) | yes¹ | expected; not yet verified | no — chat can't run programs on your computer; give it positions instead |
| `setup` / `doctor` commands | yes¹ | expected; not yet verified | no |

¹ Tested on macOS with the Claude Code CLI: install from GitHub, the engine steps behind setup/doctor, MCP connected,
tool calls from a test client. A signed-in model turn calling the tools has not been recorded yet.

Updating, disabling, rolling back, uninstalling, where files live and troubleshooting:
**[docs/MARKETPLACE.md](docs/MARKETPLACE.md)**.

## Why it is different

- **Calculation is separate from interpretation.** Positions, dashas and transits come from the local engine; the
  reasoning never invents a position, date or transit.
- **Synthesis, not single placements.** Conclusions need several independent factors to agree and are graded
  Strong / Moderate / Weak / Contradictory / Unknown — separately for *whether*, *when* and *in what form*.
- **Contradictions are kept.** Books and schools disagree; the contradiction register records both sides and the
  answer says what each side would change.
- **Birth-time honesty.** The engine recomputes the chart across ±0.5…15 minutes and says how much error each factor
  tolerates; unstable factors are not leaned on.
- **Systems are not blended.** Jaimini has its own methods; it is argued separately and compared only at the end.
- **Life first.** The person asked about their life; chart facts are the evidence, not the subject.

## Architecture

```
Birth data → local Swiss Ephemeris engine (astro) → validated chart facts
           → question framing → consultation reasoning (promise → activation → trigger → scenarios
             → contradictions → confidence) ⇄ optional source lookup in your own books
           → consultation (chat) or Structured Report Model → Jinja2 → HTML → WeasyPrint → PDF
```

One engine, three interfaces — **MCP** (stdio or Streamable HTTP), **REST** (`/api/v1`, OpenAPI) and the **`astro`
CLI** — all calling the same functions, so a chart computed through Claude, ChatGPT, Cursor or a script is the same
chart. The plugin runs that engine through MCP; nothing is forked per AI client. Details:
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

| Path | Contents |
|---|---|
| `.claude-plugin/marketplace.json` | the `vedic-astrology` marketplace |
| `plugins/astrology-consultation/` | the plugin: `skills/` (consultation skill + `setup`, `doctor` commands), `engine/` (the `astro` package), `scripts/astro` (launcher), `.mcp.json` |
| `tests/` | engine, interface, security and property tests — synthetic charts only |
| `tools/` | checks, MCP smoke test, book-ingestion tools for your own library |
| `docs/` | guides; start with [MARKETPLACE](docs/MARKETPLACE.md) and [CLIENT-INTEGRATIONS](docs/CLIENT-INTEGRATIONS.md) |

## Other AI clients and scripts (no Claude plugin)

```bash
git clone https://github.com/Krish9688/vedic-astrology-consultation && cd vedic-astrology-consultation
./install.sh          # private venv, `astro` command, settings (private mode), ephemeris, health check
```
Then point any MCP client at `.venv/bin/astro mcp`, or run `astro serve` for the REST API
(`http://127.0.0.1:8766/api/v1/docs`). Configuration for Claude Desktop, ChatGPT desktop/Codex, Cursor and Open
WebUI, and which of them were actually tested: [docs/CLIENT-INTEGRATIONS.md](docs/CLIENT-INTEGRATIONS.md).

Birth details go in a file, not on the command line:
```bash
echo '{"date": "1992-03-14", "time": "09:40", "tz": 0, "lat": 51.5, "lon": -0.12}' > s1.json
.venv/bin/astro chart s1.json --md          # positions, vargas, dashas, transits, Shadbala, Ashtakavarga, Jaimini
.venv/bin/astro sensitivity s1.json --md    # minutes of birth-time error each factor tolerates
```

### More engine commands

```bash
.venv/bin/astro dasha s1.json --md                     # Vimshottari periods
.venv/bin/astro transits s1.json --on 2027-01-01 --md  # transits and sign changes from a date
.venv/bin/astro sky 2026-01-01 2026-12-31              # retrograde stations and sign changes, no birth data
.venv/bin/astro sensitivity s1.json --span 120         # look ±2 hours instead of ±15 minutes
```

## Requirements and configuration

- Python 3.11 or newer (or [uv](https://docs.astral.sh/uv/)); runtime dependencies `pyswisseph` and `pydantic`.
  Optional extras: `mcp` (MCP server), `api` (FastAPI + Uvicorn for REST), `report` (Jinja2 + WeasyPrint for PDF).
- Ephemeris: the Swiss Ephemeris files (downloaded by setup, pinned SHA-256) cover 1800–2399; outside that the engine
  falls back to the built-in Moshier ephemeris and says so. Dates are accepted from year 2 to 2999.
- Settings live in `~/.config/astrology-consultation/config.toml` (owner-only permissions), written by `astro setup`:
  `mode`, `skill_dir`, `knowledge_dir`, `books_dir`, `reports_dir`, `data_dir`, `allow_remote`, `api_token`,
  `source_url`, `share_library_remotely`. Unknown keys are reported and ignored. `ASTRO_CONFIG` points to another file.

## Privacy

- All calculation is local; no tool sends birth data anywhere (default **private** mode).
- The MCP and REST servers bind to 127.0.0.1. Remote use needs both `allow_remote = true` and an `api_token`. If you
  let other people use the service over a network and you changed the code, AGPL-3.0 §13 requires you to offer them
  your modified source; set `source_url` in the config, and the service advertises it through `get_engine_info`,
  `/api/v1/version` and the token-free `/api/v1/source`. Library lookup (excerpts of your own books) is not served to
  remote clients unless you set `share_library_remotely = true`.
- No access logs; birth details are not logged. Predictions are logged only with explicit consent.
- This repository contains no personal data: every chart in tests and examples is synthetic.

Details: [docs/PRIVACY.md](docs/PRIVACY.md).

## Books and copyright

No books, book text, index or knowledge graph are distributed here. Book search and the page-cited knowledge graph
work with **your own** legally obtained copies ([docs/ADD-A-BOOK.md](docs/ADD-A-BOOK.md)); without them the
consultation works and says that source lookup is unavailable. This edition contains no Lal Kitab material (rules,
tables, annual chart or remedies); asked about Lal Kitab, the assistant says so. Per-book status:
[docs/COPYRIGHT.md](docs/COPYRIGHT.md).

## Testing

Every push runs: Gitleaks (full history), a privacy and copyright check, version consistency, Anthropic's plugin
validator (`claude plugin validate --strict`) on the marketplace and plugin, Ruff, the test suite (Hypothesis property
tests, reference charts incl. polar and boundary cases, MCP/REST/CLI security tests), a plugin-launcher bootstrap
with an MCP smoke test, skill self-tests, a PDF report render and a package check.

The marketplace flow — add marketplace → install → setup → doctor → MCP connected → synthetic chart → consultation
context → report — was tested from GitHub on a clean, sandboxed Claude Code profile on 2026-10-03 (macOS; the engine,
launcher and MCP also run in Linux CI). Update, disable/enable, rollback and uninstall were tested with a local copy of
the marketplace. What was and wasn't tested for each client: [docs/CLIENT-INTEGRATIONS.md](docs/CLIENT-INTEGRATIONS.md);
method and results: [docs/TESTING.md](docs/TESTING.md).

## Limitations

- Grades describe agreement within the tradition, not probabilities.
- No time-zone database: give the UTC offset at birth, including daylight saving.
- Not yet implemented: Chara/Yogini/Narayana dashas, ishta/kashta phala, bhava bala.
- Native Windows is not supported: the plugin's engine launcher is a POSIX shell script. On Windows, run Claude Code
  inside WSL 2.
- claude.ai chat cannot reach the local engine; ChatGPT on the web would need a public tunnel (not recommended).
- Ascendant- and divisional-chart claims are only as good as the birth time; the engine reports the tolerance.
- First run needs Python 3.11+ or uv and internet once (engine environment and ephemeris download).
- Remote mode has no TLS of its own: put it behind an SSH tunnel or a TLS reverse proxy.
- Adding books (`astro add-book`) needs the full repository, not the plugin.
- The prediction log has only been exercised with synthetic records.

## Version history

The skill has evolved since v1.1 (2026-09-06); v3.5.0 was the first version published here, followed by 3.6.0, 3.6.1, 3.6.2 and 3.6.3 (current). Full history:
[docs/VERSION-HISTORY.md](docs/VERSION-HISTORY.md) · [CHANGELOG.md](CHANGELOG.md).

## Contributing and security

[CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md). Never put real birth details in an issue, test or
pull request: tests use invented charts only, and the privacy check rejects unreviewed birth records.

## License

AGPL-3.0-or-later (engine), Apache-2.0 (skill scripts and plugin files), CC-BY-4.0 (method text and documentation);
book quotations are not relicensed. Full terms: [LICENSE](LICENSE) and [LICENSES/](LICENSES/).
