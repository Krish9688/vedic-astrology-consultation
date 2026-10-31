# Sample report: Asha (invented)

Asha is an invented person from the /astro-report design spec (D1). Nothing here is a real person's chart or data.

- `asha-birth-invented.json`: the invented birth details (14 March 1991, 06:20, Pune, Asia/Kolkata) and the analysis date.
- `asha-invented.json`: the Structured Report Model (career, Parashari only, birth data not printed).
- `asha-career-20261030-1015.html`: the rendered report (the PDF, 11 pages, is not shipped: the public KEEP-OUT gate bans every .pdf).

How it was made: every position, period and ingress came from the engine (`astro` service functions, Lahiri, mean
nodes, whole-sign houses), and the text was written only from those outputs. `service.create_report` accepted the model
with the birth input (ok, 0 errors) into a scratch reports folder, because the folder guard refuses the skill folder.
The PDF was rendered with `.venv-report` (WeasyPrint) from the same model; `tools/report_qa.py` found no problems.
The test `tests/test_sample_report.py` re-runs the checks; the model is a hand-written draft, not a calculation output.
