## What and why

<!-- One or two sentences. Reference the issue: Fixes #N -->

## Checklist (see CONTRIBUTING.md)

- [ ] Never paste real birth details (yours or anyone else's): date, time and place of birth are personal data. Use an invented chart or a published example, and say which.
- [ ] Install smoke test passes: `python tools/mcp_smoke.py <path to astro>` (see CONTRIBUTING.md)
- [ ] `ruff check .` passes
- [ ] `python3 tools/privacy_check.py <changed files>` reports 0 findings
- [ ] Calculation changes: evidence attached (input, our output, a reference value and its source)
- [ ] Lahiri remains the default ayanamsa; any other mode stays an explicit, stamped option
