# astrology-consultation (Claude plugin)

Vedic astrology consultations that reason like a careful practitioner — answering the actual question, weighing the
few factors that matter, timing them, and saying how sure they are — backed by a private calculation engine that runs
on your own computer.

## What the plugin installs

| Component | Where it runs | Notes |
|---|---|---|
| Skill `astrology-consultation` | Claude Code, Cowork, claude.ai chat | the consultation and report method |
| Local MCP server `astrology` (16 tools) | Claude Code; Cowork sessions on your computer | started by `scripts/astro`; not available in web chat |
| Commands `/astrology-consultation:setup`, `/astrology-consultation:doctor` | Claude Code, Cowork | first-time setup and health check |

The engine's Python environment is created on first use in the plugin's data folder (`~/.claude/plugins/data/…`),
kept across plugin updates and removed when you uninstall. Swiss Ephemeris files go to
`~/.local/share/astrology-consultation/ephe` (checksum-verified). Settings: `~/.config/astrology-consultation/config.toml`.

## First run

1. `/astrology-consultation:setup` — builds the local engine (needs Python 3.11+ or `uv`, and internet once),
   downloads the ephemeris files, runs the health check.
2. `/reload-plugins` (or start a new session) so the astrology tools connect.
3. Ask: "Calculate my chart" (give date, time, UTC offset and coordinates), "Give me a career consultation",
   "Create my 12-month report", "Explain my current dasha".

Privacy: **private mode** by default — calculation is local and nothing is sent anywhere. An optional VedAstro
cross-check exists only in hybrid mode (`astro setup --mode hybrid`), and it is never needed.

Full guide, updates, uninstalling and troubleshooting:
[docs/MARKETPLACE.md](https://github.com/Krish9688/vedic-astrology-consultation/blob/main/docs/MARKETPLACE.md).
