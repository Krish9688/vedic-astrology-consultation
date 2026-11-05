# vedic-astrology-consultation

A Claude plugin (`plugins/astrology-consultation/`: skills, agents, commands) and a local Vedic astrology calculation
engine (`plugins/astrology-consultation/engine/`, package `astro`, Swiss Ephemeris; CLI, REST and MCP).

## Rules that always hold
- Calculation, retrieval and interpretation stay separate. Readings are interpretive, never certainties.
- Synthetic or published charts only. No real person's birth data in code, tests, docs, issues or logs. A new test
  chart must pass `python3 tools/privacy_check.py`; review it with `--records` before adding its fingerprint to
  `tools/birthdata-reviewed.txt`.
- No book text, PDFs or extracted pages. Cite book and page instead.
- UTC offsets are `+HH:MM`; decimal hours only in whole or quarter steps.
- A calculation change needs a test (property test, reference chart or independent-engine comparison).
- The safety rules in [CONTRIBUTING.md](CONTRIBUTING.md) are not negotiable.

## Checks (run before reporting work as done)
- `PYTHONPATH=plugins/astrology-consultation/engine python -m pytest -p no:cacheprovider` (set `HOME` to a temp
  folder so tests never touch your real configuration)
- `uvx ruff check .`
- `python3 tools/privacy_check.py`, `python3 tools/check_links.py`, `python3 tools/check_versions.py`
- `claude plugin validate --strict .` and `claude plugin validate --strict plugins/astrology-consultation`

## Working method
Plan small changes, one commit per fix, and never mix a refactor with a bug fix. Important results get an independent
check: tests, primary sources, or a second reviewer who did not make the change.
