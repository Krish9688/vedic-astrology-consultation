# Install from the Claude plugin marketplace

| | |
|---|---|
| Marketplace | `vedic-astrology` — repository `Krish9688/vedic-astrology-consultation` |
| Plugin | `astrology-consultation` (install id `astrology-consultation@vedic-astrology`) |
| Version | 3.5.0 (plugin = engine = skill) |
| Default privacy mode | **private** — every calculation runs on your computer; nothing is sent anywhere |

Steps marked **tested** were run end to end on a clean, sandboxed Claude Code profile (2026-10-03, synthetic charts
only). Steps marked **documented** follow Anthropic's plugin documentation but were not clicked through here.

## 1. Add the marketplace and install

**Claude desktop app or claude.ai** (documented)
1. Open **Customize → Plugins**.
2. Choose **Add → Add marketplace** and enter `Krish9688/vedic-astrology-consultation`
   (or `https://github.com/Krish9688/vedic-astrology-consultation`).
3. Find **Astrology Consultation (Vedic)** and install it.

**Claude Code desktop, Code tab** (documented): **+ → Plugins → Add plugin**, add the marketplace above, then install.
Manage it later under **+ → Plugins → Manage plugins**.

**Claude Code in a terminal** (tested)
```bash
claude plugin marketplace add Krish9688/vedic-astrology-consultation
```
```bash
claude plugin install astrology-consultation@vedic-astrology
```
Inside a session: `/plugin marketplace add Krish9688/vedic-astrology-consultation`, then
`/plugin install astrology-consultation@vedic-astrology` (choose a scope), then `/reload-plugins`. On Claude Code
v2.1.275+ one command does both: `/plugin install astrology-consultation --marketplace Krish9688/vedic-astrology-consultation`.

## 2. What gets installed

| Component | Works in | Notes |
|---|---|---|
| Skill `astrology-consultation` | Claude Code, Cowork, claude.ai chat | the consultation, timing, safety and report method |
| Local MCP server `astrology` (16 tools: chart, vargas, dashas, transits, Shadbala, Ashtakavarga, Jaimini, birth-time sensitivity, consultation context, reports, source lookup) | Claude Code; Cowork sessions on your own computer | started by the plugin's `scripts/astro`; **not available in web chat**, which cannot run programs on your computer |
| `/astrology-consultation:setup`, `/astrology-consultation:doctor` | Claude Code, Cowork | first-time setup and health check |

Tested: `claude plugin details` lists the three skills and the MCP server; about 250 tokens stay loaded in every
session, the rest loads only when you ask an astrology question.

Nothing personal ships with the plugin: no charts, no birth details, no books, no book-derived text. Tests and the
worked report example use synthetic charts.

## 3. First-time setup (tested)

1. Run `/astrology-consultation:setup`. It:
   - builds a private Python environment for the engine in the plugin's data folder — needs **Python 3.11+ or
     [uv](https://docs.astral.sh/uv/)** and internet once;
   - downloads the Swiss Ephemeris files (≈1.8 MB) and checks each against a pinned SHA-256;
   - writes settings in **private** mode and runs the health check.
2. Run `/reload-plugins` (or start a new session) so the astrology tools connect.
3. Optional: `/astrology-consultation:doctor` at any time. Expect PASS for the engine, ephemeris, MCP, REST, reports
   and permissions, and OPTIONAL for books, the knowledge graph and VedAstro.

Then ask, for example: "Calculate my chart — born 14 March 1992, 09:40, UTC+0, London (51.5N, 0.12W)",
"What changes in my career over the next few years?", "Create my 12-month report".
(That birth is the project's synthetic test chart, not a real person.)

## 4. Where things live

| What | Location | Removed on uninstall? |
|---|---|---|
| Plugin files | `~/.claude/plugins/cache/vedic-astrology/astrology-consultation/<version>/` | yes |
| Engine environment | `~/.claude/plugins/data/astrology-consultation-vedic-astrology/venv` (kept across updates) | yes, unless `--keep-data` |
| Ephemeris files | `~/.local/share/astrology-consultation/ephe/` | no (reused on reinstall) |
| Settings | `~/.config/astrology-consultation/config.toml` (mode 600) | no |
| Private data (prediction log, comparisons) | `~/.local/share/astrology-consultation/` (mode 700) | no |
| Reports | `~/Documents/astrology-reports/` (created mode 700) | no — they are yours |

## 5. Privacy modes

- **private** (default): local calculation only; tools that would contact a third party refuse.
- **hybrid** (opt-in: `astro setup --mode hybrid`): also allows the optional VedAstro cross-check, which sends birth
  date, time, UTC offset and coordinates to `api.vedastro.org`. Never required.
- The MCP and REST servers listen on 127.0.0.1 only. Remote access needs both `allow_remote = true` and an
  `api_token` in the settings file; without both the server refuses to start on another address.
- No access logs; birth details are not logged. Predictions are logged only with `--consent` (or `--synthetic`).

## 6. Books and the knowledge graph (optional)

Book search and the page-cited knowledge graph need your own legally obtained books — the plugin ships none. With the
full repository you can ingest them (`astro add-book`, see [ADD-A-BOOK.md](ADD-A-BOOK.md)). Without books the
consultation works and says that source lookup is unavailable.

## 7. Update, disable, roll back, uninstall

| Action | Terminal (tested) | GUI (documented) |
|---|---|---|
| Update | `claude plugin marketplace update vedic-astrology`, then `claude plugin update astrology-consultation@vedic-astrology`, then restart or `/reload-plugins` | Customize → Plugins → **Check for updates** / **Sync automatically**; Code: `/plugin` → Installed → **Update now** |
| Auto-update | off by default for third-party marketplaces; `/plugin` → Marketplaces → **Enable auto-update** | **Sync automatically** |
| Disable / enable | `claude plugin disable astrology-consultation@vedic-astrology` / `claude plugin enable …` | the plugin's toggle |
| Roll back | `claude plugin marketplace remove vedic-astrology`, then `claude plugin marketplace add Krish9688/vedic-astrology-consultation#v3.5.0` (any release tag), then install again | — |
| Uninstall | `claude plugin uninstall astrology-consultation@vedic-astrology` (`--keep-data` keeps the engine environment) | **Remove** |

Tested on a sandboxed profile: update 3.5.0 → newer kept the engine environment (no rebuild; it rebuilds only when the
engine version changes); disable removed the astrology server, enable restored it; reverting the marketplace rolled
3.5.x back to 3.5.0; uninstall with `--keep-data` kept the environment and reinstall reused it; plain uninstall deleted
it. Removing a marketplace uninstalls its plugins.

To remove everything the plugin wrote, after uninstalling:
```bash
rm -r ~/.config/astrology-consultation ~/.local/share/astrology-consultation
```
Reports in `~/Documents/astrology-reports` are left for you to keep or delete.

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| "needs Python 3.11 or newer, or uv" | install [uv](https://docs.astral.sh/uv/) or Python 3.11+, then rerun setup |
| Astrology tools missing after setup | `/reload-plugins` or a new session; `claude mcp list` should show `plugin:astrology-consultation:astrology … ✔ Connected` |
| Tools missing in claude.ai chat | expected: web chat can't run the local engine; the skill still reasons from positions you supply |
| doctor: ephemeris checksum mismatch | rerun `/astrology-consultation:setup` (bad files are deleted, never used) |
| PDF report not produced (HTML only) | WeasyPrint needs system libraries; on macOS `brew install pango` |
| First tool call slow | the engine environment is built on first use; later starts are immediate |
| Download blocked by a proxy | run setup once on an open network; afterwards everything works offline |
| Plugin errors on load | `/plugin` → **Errors** tab; see Anthropic's [plugin troubleshooting](https://code.claude.com/docs/en/plugins/troubleshooting) |

## 9. Other AI clients

The same engine runs as a standalone MCP/REST/CLI service for Claude Desktop config files, ChatGPT desktop/Codex,
Cursor and Open WebUI — one engine for every client. See [CLIENT-INTEGRATIONS.md](CLIENT-INTEGRATIONS.md).
