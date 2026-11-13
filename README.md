# Vedic Astrology Consultation

**A Claude plugin and local calculation engine for Vedic astrology readings that cite their evidence and say how sure they are.**

[![CI](https://github.com/Krish9688/vedic-astrology-consultation/actions/workflows/ci.yml/badge.svg)](https://github.com/Krish9688/vedic-astrology-consultation/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Krish9688/vedic-astrology-consultation)](https://github.com/Krish9688/vedic-astrology-consultation/releases)

The engine calculates. The skill interprets. Positions, dashas and transits come from a Swiss Ephemeris engine on your computer, and the reasoning never invents a number. Astrology's predictive validity is not scientifically established. Answers describe what a tradition's methods indicate, and they never claim certainty.

## Quick start

In Claude Code:

```bash
claude plugin marketplace add Krish9688/vedic-astrology-consultation
claude plugin install astrology-consultation@vedic-astrology
```

Then run `/astrology-consultation:setup` in a session and `/reload-plugins`. Setup builds a private Python environment and downloads the ephemeris files. It needs Python 3.11+ or [uv](https://docs.astral.sh/uv/), and internet once.

No Claude? Use the engine alone with any MCP client, REST or the command line:

```bash
git clone https://github.com/Krish9688/vedic-astrology-consultation && cd vedic-astrology-consultation
./install.sh        # needs uv; add --all for PDF reports (WeasyPrint needs Pango)
.venv/bin/astro doctor
```

Platforms: macOS and Linux. On Windows, use WSL 2.

## What it does

| Feature | What you get |
|---|---|
| **Consultation skill** | Short, life-first answers. Each conclusion is graded Strong, Moderate, Weak, Contradictory or Unknown. |
| **Local engine** | Charts, 16 divisional charts, Vimshottari and Yogini dashas, transits, Shadbala, Ashtakavarga, Jaimini factors. |
| **Birth-time check** | The chart is recomputed at plus and minus 0.5 to 15 minutes. You see which factors survive the error. |
| **Separate systems** | Parashari is primary. Jaimini and Lal Kitab are argued separately and compared only at the end. |
| **Reports** | Career, relationship, dasha and 12-month reports as HTML or PDF. |
| **Three interfaces** | MCP (`astro mcp`), REST (`astro serve`, `/api/v1`) and the `astro` command. All call the same functions. |

## Example

This chart is synthetic, not a real person. Birth data goes in a file, so it stays out of shell history.

```bash
printf '{"date": "%s", "time": "%s", "tz": 0, "lat": 51.5, "lon": -0.12}' 1992-03-14 09:40 > s1.json
.venv/bin/astro chart s1.json --md           # positions, vargas, dashas, transits
.venv/bin/astro sensitivity s1.json --md     # minutes of birth-time error each factor tolerates
.venv/bin/astro consult "What changes in my career?" s1.json
```

In Claude, ask:

- "Calculate my chart — born 14 March 1992, 09:40, UTC+0, London (51.5N, 0.12W)"

Claude calls `calculate_birth_chart`, then `prepare_consultation` and `get_dasha` as the question needs. `get_transits` covers timing.

## Project structure

```text
.claude-plugin/              marketplace.json for the "vedic-astrology" marketplace
plugins/astrology-consultation/
  engine/                    the astro package (CLI, MCP, REST) and its pyproject.toml
  skills/                    consultation, report and source-lookup skills
  agents/  commands/         report reviewer; /setup and /doctor commands
  scripts/astro              launcher that builds the engine on first run
docs/                        guides (see below) and the accuracy rubric and score reports
tools/                       book ingestion for `astro add-book`, privacy check, install smoke test (mcp_smoke.py)
schemas/  knowledge/         JSON schemas of the engine's facts; book catalogue (metadata only)
LICENSES/                    full licence texts
```

## Configuration

Settings live in `~/.config/astrology-consultation/config.toml`, written by `astro setup` with owner-only permissions. Keys: `mode`, `skill_dir`, `knowledge_dir`, `books_dir`, `reports_dir`, `data_dir`, `allow_remote`, `api_token`, `source_url`, `share_library_remotely`.

| Variable | Effect |
|---|---|
| `ASTRO_CONFIG` | Use another config file. |
| `ASTRO_EPHE_PATH` | Folder with Swiss Ephemeris files. Without them the engine uses the built-in Moshier ephemeris and says so. |
| `ASTRO_SKILL_DIR`, `ASTRO_KNOWLEDGE_DIR` | Override the skill and knowledge folders. |

Optional install extras: `mcp`, `api`, `report`, `all`. Servers bind to 127.0.0.1. Remote use needs `allow_remote = true` and an `api_token`.

## Documentation

| Page | Covers |
|---|---|
| [MARKETPLACE](docs/MARKETPLACE.md) | Install, update, roll back, uninstall, troubleshooting |
| [CLIENT-INTEGRATIONS](docs/CLIENT-INTEGRATIONS.md) | Claude Desktop, ChatGPT, Cursor, Open WebUI; what was tested |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | How the engine, skill and interfaces fit together |
| [CALCULATION-ENGINES](docs/CALCULATION-ENGINES.md) | Conventions, ayanamsa and cross-checks |
| [PRIVACY](docs/PRIVACY.md) | What stays local and how remote mode works |
| [ACCURACY-RUBRIC](docs/ACCURACY-RUBRIC.md) | How accuracy is scored; reports in `docs/accuracy/` |
| [ADD-A-BOOK](docs/ADD-A-BOOK.md), [COPYRIGHT](docs/COPYRIGHT.md) | Using your own books; what is not distributed |
| [VERSION-HISTORY](docs/VERSION-HISTORY.md), [CHANGELOG](CHANGELOG.md) | Release history |

## Privacy and limits

Calculation is local and nothing is sent to an outside service. This repository holds no personal data and no book text. Ascendant and divisional-chart claims depend on the birth time: a few minutes can change them, so `get_birth_time_sensitivity` reports how stable each one is and the skill treats "high" sensitivity as uncertain (see the sensitivity grid in [CALCULATION-ENGINES](docs/CALCULATION-ENGINES.md)). There is no time-zone lookup from a birth place without the optional gazetteer, so give the UTC offset at birth if you use coordinates.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Use invented charts only. Report security problems as described in [SECURITY.md](SECURITY.md). Before a pull request, run `uvx ruff check .` and `python3 tools/privacy_check.py`.

## License

Three licences, by component. The engine is AGPL-3.0-or-later, because it links the Swiss Ephemeris. Skill scripts, report templates and plugin files are Apache-2.0. Method text and documentation are CC BY 4.0. Book quotations are not relicensed. See [LICENSE](LICENSE) and [LICENSES/](LICENSES/).
