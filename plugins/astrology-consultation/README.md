# astrology-consultation (Claude plugin)

Vedic astrology consultations that reason like a careful practitioner — answering the actual question, weighing the
few factors that matter, timing them, and saying how sure they are — backed by a private calculation engine that runs
on your own computer.

## What the plugin installs

| Component | Where it runs | Notes |
|---|---|---|
| Skill `astrology-consultation` | Claude Code; Cowork and claude.ai chat (documented, not yet verified) | the consultation and report method |
| Local MCP server `astrology` (26 tools) | Claude Code; Cowork (expected, not yet verified) | started by `scripts/astro`; not available in web chat |
| Commands `/astrology-consultation:setup`, `/astrology-consultation:doctor` | Claude Code; Cowork (not yet verified) | first-time setup and health check |
| Skill `/astrology-consultation:astro-report` | Claude Code | guided report: HTML and PDF |

The engine's Python environment is created on first use in the plugin's data folder (`~/.claude/plugins/data/…`),
kept across plugin updates and removed when you uninstall. Swiss Ephemeris files go to
`~/.local/share/astrology-consultation/ephe` (checksum-verified). Settings: `~/.config/astrology-consultation/config.toml`.

## First run

1. `/astrology-consultation:setup` (macOS or Linux; on Windows use WSL 2) — builds the local engine (needs Python
   3.11+ or `uv`, and internet once),
   downloads the ephemeris files, optionally (asks first) the GeoNames place list (about 7 MB, CC BY 4.0, no birth data
   sent) so birth places can be looked up, and runs the health check.
2. `/reload-plugins` (or start a new session) so the astrology tools connect.
3. Ask: "Calculate my chart" (give date, time, UTC offset and coordinates), "Give me a career consultation",
   "Create my 12-month report", "Explain my current dasha".

## Reports: `/astrology-consultation:astro-report`

Asks whose chart it is, checks the birth details and time zone with you, then writes one report (career, relationship,
marriage, dasha, twelve-month, relocation, complete life, summary or outlook) as HTML and, when the PDF tool is
installed, PDF. The text after the command is the report type, for example `/astrology-consultation:astro-report career`.
Reports go to the reports folder in your Documents (change it with `astro setup --reports-dir DIR`; the engine refuses a
folder inside a code project, the plugin or the skill folder). They print your birth data only if you say yes.

The questions span many messages, and Claude Code may ask permission for each astrology tool again in a later turn. To
avoid that, choose "always allow" for the astrology tools the first time you are asked (or add them to your allowed tools).

Turn it off: it only runs when you type the command (`disable-model-invocation`). To remove it, disable or uninstall the
plugin in `/plugin`. Delete old reports with `astro purge --older-than DAYS`.

Privacy: calculation is local and nothing is sent anywhere.

Full guide, updates, uninstalling and troubleshooting:
[docs/MARKETPLACE.md](https://github.com/Krish9688/vedic-astrology-consultation/blob/main/docs/MARKETPLACE.md).
