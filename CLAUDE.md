# vedic-astrology-consultation

A Claude plugin (`plugins/astrology-consultation/`: skills, agents, commands) and a local Vedic astrology calculation
engine (`plugins/astrology-consultation/engine/`, package `astro`, Swiss Ephemeris; CLI, REST and MCP).

## Rules that always hold
- Calculation, retrieval and interpretation stay separate. Readings are interpretive, never certainties.
- Synthetic or published charts only. No real person's birth data in code, docs, issues or logs. A new example chart
  must pass `python3 tools/privacy_check.py`; review it with `--records` before adding its fingerprint to
  `tools/birthdata-reviewed.txt`.
- No book text, PDFs or extracted pages. Cite book and page instead.
- UTC offsets are `+HH:MM`; decimal hours only in whole or quarter steps.
- A calculation change needs evidence: input, output, a reference value and its source (published chart or
  independent engine). The test suite itself is kept in the development repository.
- The safety rules in [CONTRIBUTING.md](CONTRIBUTING.md) are not negotiable.

## Checks (run before reporting work as done)
- `uvx ruff check .` and `python3 tools/privacy_check.py`
- `claude plugin validate --strict .` and `claude plugin validate --strict plugins/astrology-consultation`
- the install smoke test: `python tools/mcp_smoke.py plugins/astrology-consultation/scripts/astro` (in an environment
  with `mcp` installed; it computes a synthetic chart over MCP). The full test suite is kept in the development
  repository and runs there before every release.

## Working method
Plan small changes, one commit per fix, and never mix a refactor with a bug fix. Important results get an independent
check: tests, primary sources, or a second reviewer who did not make the change.
