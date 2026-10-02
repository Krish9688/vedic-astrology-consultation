---
description: Set up the local astrology engine (private Python environment, Swiss Ephemeris files, settings) and check it
allowed-tools: Bash
---
Set up this plugin's local astrology engine. Run each command with the Bash tool, one at a time, and report the result
in plain words:

1. `"${CLAUDE_PLUGIN_ROOT}/scripts/astro" setup --ephemeris`
   The first run creates a private Python environment in the plugin's data folder (it needs Python 3.11+ or `uv`, and
   an internet connection once), then downloads the Swiss Ephemeris data files from the official repository and
   verifies their checksums. Settings default to **private mode**: all calculation stays on this computer.
2. `"${CLAUDE_PLUGIN_ROOT}/scripts/astro" doctor`

Explain every FAIL or WARN line and how to fix it; OPTIONAL lines are components the user hasn't added (such as their
own book library) and need no action. Finish by telling the user to run `/reload-plugins` (or start a new session) so
the astrology tools connect, and that they can then ask, for example, "Calculate my chart" or "What does my current
dasha mean?". Do not ask for, store or log anyone's birth details during setup.
