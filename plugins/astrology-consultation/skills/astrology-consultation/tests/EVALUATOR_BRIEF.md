# Evaluator brief (give to a fresh agent)

You are simulating Claude answering real users with ONE astrology skill. Follow that skill's `SKILL.md` exactly as
written (load the references it routes you to, run its scripts if it has any). Do not use anything else you know about
this project.

Rules:
- Do NOT open `tests/test-cases.md`, `tests/results/` (other than writing your own outputs) or anything under
  `_skill_workspace/sourcemaps` or `docs`. Those would bias the test.
- Do NOT call any MCP server or the internet. All calculated data you may use is in the fixture files named in each
  request. "Today" is 2026-09-24. If the skill would normally calculate something that is not in the fixtures, behave as
  the skill instructs for missing data.
- Treat each request as a separate conversation with a different user. Write the exact reply you would send that user.
- Save each reply to the output folder you are given as `Txx.md`, with this structure:
  1. `## Reply` — exactly what the user would see.
  2. `## Method trace` — 5–15 lines: which skill files you loaded, which scripts you ran (with arguments), and any
     judgement calls. This part is for the reviewer, not the user.
- Be efficient: load the skill's core files once and reuse them across your requests.
