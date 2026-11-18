---
description: List the astrology reports you can get, or start one by name (for example /report career). Calculated on this computer; writes HTML and PDF.
argument-hint: "[report name or alias]"
disable-model-invocation: true
allowed-tools: Bash(python3:*) Read AskUserQuestion mcp__plugin_astrology-consultation_astrology__get_engine_info mcp__plugin_astrology-consultation_astrology__find_place mcp__plugin_astrology-consultation_astrology__get_planet_positions mcp__plugin_astrology-consultation_astrology__calculate_birth_chart mcp__plugin_astrology-consultation_astrology__get_birth_time_sensitivity mcp__plugin_astrology-consultation_astrology__get_dasha mcp__plugin_astrology-consultation_astrology__get_transits mcp__plugin_astrology-consultation_astrology__get_outlook mcp__plugin_astrology-consultation_astrology__get_gochara mcp__plugin_astrology-consultation_astrology__get_jaimini_factors mcp__plugin_astrology-consultation_astrology__get_tajika mcp__plugin_astrology-consultation_astrology__prepare_consultation mcp__plugin_astrology-consultation_astrology__create_report mcp__plugin_astrology-consultation_astrology__get_activation mcp__plugin_astrology-consultation_astrology__get_ashtakavarga mcp__plugin_astrology-consultation_astrology__get_divisional_chart mcp__plugin_astrology-consultation_astrology__get_shadbala mcp__plugin_astrology-consultation_astrology__get_topic_network mcp__plugin_astrology-consultation_astrology__get_yogini_dasha
---
# /report

A thin front door to the `astro-report` flow. The one list of reports is the registry; this command adds no report
logic of its own. The text after the command is `$ARGUMENTS`. Use Bash only to run the catalog helper below, never to
write birth data.

Catalog helper (standard library, `python3`), path in every call: `${CLAUDE_PLUGIN_ROOT}/skills/astrology-consultation/scripts/report_catalog.py` (below: `$H`).

1. **No argument.** Run `python3 "$H"`. Show every line it prints, one per report: ready ones are selectable, "coming"
   ones are not built yet. Ask "Which report?" (free text). Treat the answer as the argument.
2. **With an argument.** Run `python3 "$H" resolve "<argument>"` and read the JSON `status`:
   - `built`: continue to step 3 with `entry`.
   - `planned`: say "{name} isn't built yet." and list the `built` reports, then let the person pick one (back to step 2).
     If `built` is empty, say no report is ready yet and stop.
   - `unknown`: say "I don't have a report called '{argument}'." Show the `close` matches, then the full list (step 1).
3. **Hand off.** Read `${CLAUDE_PLUGIN_ROOT}/skills/astro-report/SKILL.md` and follow it from "The conversation",
   with the report type already chosen (`entry.id`; skip its step 1 question). Ask for the missing birth data one
   question at a time, and for a second chart when `entry.charts` is 2. If `entry.depth` lists more than one depth, ask which (one question, standard first), and always set `depth` in the model when the entry lists one. Follow the entry's `spec` file. Compute only with the astrology tools, then write
   and render the HTML and PDF with `create_report`. Keep its validation messages, safety rules, privacy rules and
   delivery text exactly. If the tools are missing: "The astrology engine isn't connected. Run
   /astrology-consultation:setup, then /reload-plugins, and try again."

For the full consultation report, use `/astro-report consultation`.
