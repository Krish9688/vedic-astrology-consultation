# Client integrations

One local service (`astro`), three interfaces: **MCP** (stdio or Streamable HTTP), **REST** (`/api/v1`, OpenAPI) and
the **CLI**. Every interface calls the same `astro.service` functions, so a chart computed through Claude, ChatGPT,
Cursor or a script is the same chart. The AI client does the reasoning; the service supplies facts, the skill's method
files (`skill://` resources) and report rendering.

Install first: `./install.sh` (or `uv pip install -e ".[mcp,api]"` then `astro setup && astro doctor`). Below,
`ASTRO` means the absolute path printed by the installer, e.g. `/path/to/repo/.venv/bin/astro`.

## Compatibility matrix (release validation, 2026-10-03; marketplace rows added for 3.5.0)

Statuses: **TESTED** (run end to end here) · **CONFIGURED BUT NOT TESTED** (the client accepted the configuration;
tool calls not run) · **USER ACTION REQUIRED** (needs your sign-in, approval or a change to your own app settings) ·
**DOCUMENTED** (configuration from the client's docs; client not installed here) · **NOT RECOMMENDED** · **UNSUPPORTED**.
All tests used synthetic charts only.

| Client | Skill | MCP | REST | Books / graph | Local engine | Reports | Tested? |
|---|---|---|---|---|---|---|---|
| Generic MCP client (Python SDK 2.2) | via `skill://` resources | stdio + Streamable HTTP | — | yes (local) | yes | `create_report` | **TESTED** — stdio in CI; HTTP with/without bearer token |
| REST client (curl, httpx) | — | — | `/api/v1` | `/consultation` lists files | yes | `/report` | **TESTED** — health, chart, consultation, OpenAPI; empty server log |
| CLI (`astro`) | — | `astro mcp` | `astro serve` | `astro sources/search` | yes | `astro report` | **TESTED** — incl. clean install (install.sh) |
| **Claude Code — marketplace plugin** (recommended) | bundled | stdio, started by the plugin | — | with your own books | yes | yes | **TESTED** (2026-10-03, sandboxed new-user profile, plugin installed from GitHub): marketplace add → install → setup → doctor 13 PASS / 0 WARN / 0 FAIL → `claude mcp list` Connected → MCP smoke through the installed launcher (16 tools, synthetic D9, consultation context) → report HTML + PDF; update, disable/enable, rollback, uninstall. A live model turn calling the tools: **USER ACTION REQUIRED** (the CLI on the test machine was not signed in) — see docs/MARKETPLACE.md |
| Claude desktop app / claude.ai — marketplace plugin | bundled | Cowork on your computer only; not in web chat | — | — | Cowork only | layout only in chat | **DOCUMENTED** (Customize → Plugins → Add → Add marketplace; from Anthropic's docs, not clicked through here) |
| Claude Code — manual MCP setup | installed (`~/.claude/skills`) | stdio | — | yes | yes | yes (renderer) | **USER ACTION REQUIRED** — a project `.mcp.json` was discovered by `claude mcp list` and held at "Pending approval"; approve it, or `claude mcp add`; tool calls not run here |
| Claude Desktop / Cowork | upload the `.skill` | stdio (config file) | — | no (cloud) | via MCP only | layout only | **USER ACTION REQUIRED** — add the server to `claude_desktop_config.json` and restart. Your current config holds `vedastro-local`, which sends birth data to api.vedastro.org |
| ChatGPT desktop (Codex surface) / Codex CLI | `~/.agents/skills` | stdio (`~/.codex/config.toml`) | — | yes | yes | yes | **CONFIGURED BUT NOT TESTED** — the CLI bundled with ChatGPT 26.928 (codex-cli 0.159) accepted the server in an isolated `CODEX_HOME` (`codex mcp list/get`); tool calls need your signed-in app (**USER ACTION REQUIRED**) |
| ChatGPT on the web | — | remote HTTPS only | — | — | — | — | **NOT RECOMMENDED** — would need a public tunnel exposing birth data |
| Cursor | — | stdio | — | yes | yes | — | **DOCUMENTED** (not installed) |
| Open WebUI | — | Streamable HTTP | or REST | yes | yes | — | **DOCUMENTED** (not installed) |

The MCP server's `instructions` are 459 characters, inside the 512 characters Codex reads first.

### ChatGPT: migrating the legacy `vedic-prediction-synthesis` v2.1 to v3.5 (USER ACTION REQUIRED)

Found: `~/.agents/skills/vedic-prediction-synthesis` is a symlink to a Desktop project folder; its SKILL.md is
byte-identical to the archived v2.1 release (`releases/previous/predecessor/vedic-prediction-synthesis-v2.1.zip`).
Nothing else references it (a Codex "trusted project" entry points at the Desktop folder, not at the skill). Two
astrology skills side by side would both trigger, so replace rather than add:

1. **Backup:** `mkdir -p ~/.agents/skills-disabled && mv ~/.agents/skills/vedic-prediction-synthesis ~/.agents/skills-disabled/`
   (moves only the symlink; the Desktop folder and the archived zip stay untouched).
2. **Install:** `unzip astrology-consultation-v3.5.skill -d ~/.agents/skills/` and add the MCP block below to
   `~/.codex/config.toml`.
3. **Test:** in ChatGPT (Codex) start a new thread: "Using astrology-consultation, calculate the synthetic chart
   1992-03-14 09:40 UTC, 51.5N 0.12W and tell me its rising sign" — expect a `calculate_birth_chart` tool call and
   Taurus.
4. **Rollback:** remove `~/.agents/skills/astrology-consultation` and the `[mcp_servers.astrology]` block, then
   `mv ~/.agents/skills-disabled/vedic-prediction-synthesis ~/.agents/skills/`.

## Claude

**Easiest: the marketplace plugin** — see [MARKETPLACE.md](MARKETPLACE.md). Manual setup:

**Claude Code**
```bash
claude mcp add astrology --scope user -- ASTRO mcp
```
The skill itself (`skill/astrology-consultation/`) can also be installed as a Claude skill
(`~/.claude/skills/astrology-consultation`); with both, the skill supplies the method and the MCP server the facts.

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):
```json
{"mcpServers": {"astrology": {"command": "ASTRO", "args": ["mcp"]}}}
```

## ChatGPT and Codex

The ChatGPT desktop app, the Codex CLI and the Codex IDE extension share `~/.codex/config.toml`:
```toml
[mcp_servers.astrology]
command = "ASTRO"
args = ["mcp"]
```
or `codex mcp add astrology -- ASTRO mcp`. The skill folder follows the open Agent Skills format; for Codex, copy or
link it to `~/.agents/skills/astrology-consultation`.

**ChatGPT on the web** only connects to remote HTTPS MCP servers. Reaching a local server would mean exposing it
through a public tunnel (`allow_remote = true`, `api_token`, HTTPS) — birth data would then pass through the tunnel
and OpenAI's servers. That is outside the default `private` mode; prefer the desktop app with stdio.

## Other MCP clients

**Cursor** — `~/.cursor/mcp.json`: `{"mcpServers": {"astrology": {"command": "ASTRO", "args": ["mcp"]}}}`

**Open WebUI** (native MCP, Streamable HTTP): run `ASTRO mcp --http` and add `http://127.0.0.1:8765/mcp` as an MCP
server. If Open WebUI runs in Docker, it cannot reach the host's 127.0.0.1; use the REST API or
[mcpo](https://github.com/open-webui/mcpo) instead of opening the listener to the network.

**Any client with a bearer token** (remote use, opt-in): set `allow_remote = true` and `api_token = "…"` in
`~/.config/astrology-consultation/config.toml` (written with mode 600), then send `Authorization: Bearer <token>`.
Without both settings the server refuses to listen beyond localhost.

## REST

```bash
ASTRO serve            # http://127.0.0.1:8766/api/v1/docs  (OpenAPI: /api/v1/openapi.json)
```
```bash
curl -s -X POST http://127.0.0.1:8766/api/v1/varga -H 'content-type: application/json' \
  -d '{"birth": {"date": "1992-03-14", "time": "09:40", "tz": 0, "lat": 51.5, "lon": -0.12}, "division": 9}'
```

## CLI

Birth details go in a JSON file, not on the command line (keeps them out of shell history):
```bash
ASTRO chart s1.json --md
```
Subcommands: `chart positions varga dasha transits strength jaimini sensitivity compare consult report sources search
predict doctor setup add-book mcp serve` — `ASTRO --help`.

## Privacy and security (all interfaces)

- Default mode `private`: all calculation local; `compare_engines` with `live=true` (sends date, time, offset and
  coordinates to VedAstro) is refused unless the user chose `hybrid`.
- Listeners bind to 127.0.0.1; remote needs `allow_remote` **and** a token.
- `skill://` and report paths are confined to their folders (realpath check); only skill documents are readable.
- No access logs; tool errors return the refusal reason, crashes return a generic message.
- Prediction logging is not exposed over MCP or REST and needs `--synthetic` or `--consent`.
