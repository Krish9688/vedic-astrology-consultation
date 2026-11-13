# Contributing

Thank you for helping. A few rules keep the project trustworthy:

1. **Synthetic data only.** Never add a real person's birth details, chart, reading or report to code, tests, docs,
   issues or pull requests. Test charts must be invented or published book examples.
2. **No book text.** Do not add PDFs, extracted page text, OCR output or long quotations. Cite book and page instead.
3. **Calculation changes need evidence.** Attach the input, our output, a reference value and its source (a published
   chart or an independent engine), and state the convention you used. The maintainers add the matching test to the
   suite in the development repository.
4. **Method changes need a reason.** Say what was wrong in a real answer and how the change fixes it; the project
   evaluates skill changes with blind comparisons.
5. **Safety rules are not negotiable:** no death dates, diagnoses, fertility or childbirth forecasts, legal verdicts or
   investment advice.

Setup: `./install.sh`, then `.venv/bin/python tools/mcp_smoke.py .venv/bin/astro` (the install smoke test). Before a
pull request: `uvx ruff check .`, `python3 tools/privacy_check.py`, `claude plugin validate --strict .` and
`claude plugin validate --strict plugins/astrology-consultation`. The full test suite lives in the development
repository; describe in the pull request how you checked a calculation change.

Licences: contributions to the engine are AGPL-3.0-or-later, to skill scripts and templates Apache-2.0, to method text
and docs CC BY 4.0 (see LICENSE).
