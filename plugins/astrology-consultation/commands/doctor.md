---
description: Check the local astrology engine, its data files, optional components and privacy settings
allowed-tools: Bash
---
Run `"${CLAUDE_PLUGIN_ROOT}/scripts/astro" doctor` with the Bash tool and summarise the result: what works (PASS), what
should be fixed (WARN), what is broken (FAIL) and which optional parts are not installed (OPTIONAL). If the place gazetteer row says "not installed", the fix is `astro setup --places` (about 7 MB from GeoNames, CC BY 4.0; ask before running). For each WARN or
FAIL, give the exact fix. If the engine is missing, suggest `/astrology-consultation:setup`.
