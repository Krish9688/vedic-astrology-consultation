#!/usr/bin/env sh
# Standalone install (without Claude's plugin system): a private virtual environment, the `astro` command, settings,
# Swiss Ephemeris files and a health check. Claude users can instead add the marketplace and run
# /astrology-consultation:setup (see README).
#   ./install.sh          engine + MCP server + REST API + HTML reports
#   ./install.sh --all    also PDF reports (WeasyPrint needs Pango: `brew install pango` / apt libpango-1.0-0)
set -eu
cd "$(dirname "$0")"
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
extras="mcp,api"
[ "${1:-}" = "--all" ] && extras="all"
uv venv -q .venv
uv pip install -q --python .venv/bin/python -e "plugins/astrology-consultation/engine[${extras}]" jinja2
.venv/bin/astro setup --skill-dir "$PWD/plugins/astrology-consultation/skills/astrology-consultation" --ephemeris
.venv/bin/astro doctor
cat <<MSG

Installed. Use:  $PWD/.venv/bin/astro --help
MCP clients:     command "$PWD/.venv/bin/astro", args ["mcp"]   (docs/CLIENT-INTEGRATIONS.md)
MSG
