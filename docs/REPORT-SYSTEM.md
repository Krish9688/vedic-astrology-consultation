# Report system

> **What:** the report types and how a report is built and rendered. **Read it when:** you add or change a report.
> **Last checked:** 2026-11-21 (T11.45: sections 2a and 4a added for report batches 4-6; the rest not checked).
> **Related:** REPORT-DESIGN-SPEC.md, CONSULTATION-REASONING.md.

Professional personalised reports (output mode C). The design rests on research into how practitioners and report
producers work — what to copy and what to avoid is in `research/reports/SYNTHESIS.md`.

```
consultation reasoning (workbench, per section)
        ↓
Structured Report Model  (JSON; assets/report/report.schema.json)
        ↓  scripts/render_report.py: schema validation → consistency checks → life-first lint
Jinja2 template (assets/report/template.html.j2) + stylesheet (assets/report/report.css)
        ↓
HTML  ──► WeasyPrint ──► PDF          (without WeasyPrint the HTML prints to PDF from any browser)
```

## 1. Why this shape

- **Separation.** Reasoning decides content; the model records it; the template only lays it out. No PDF coordinates
  are drawn by hand, so a layout change never touches a prediction.
- **One template for every report type.** Types differ in which sections they carry (reports.md §2), not in layout.
- **Checks before rendering.** The renderer refuses a model whose summary mentions a year no section argues, or that
  points at a missing section; it warns when a unit lacks a counter-factor or a sign to watch, when a section carries
  too many chart facts, and when page/verse references leak into client text.
- **Portable.** The skill's scripts use only the standard library plus Jinja2 for rendering, so they work in Claude
  Code and, where Jinja2 exists, in Claude Chat/Cowork sandboxes.

## 2. The model

| Field | Content |
|---|---|
| `report_type` | the `built` ids in the registry (section 2a): compact (consultation summary, 2–4 pages), kundli, career, relationship, marriage, dasha, 12-month, relocation, complete-life and the spec-driven types |
| `summary` | headline + at most seven key points, each with a confidence word, optional window and the section that argues it |
| `sections[]` | `units[]` of the life-first unit (theme, meaning, manifestation, timing, nuance, counter, watch, confidence per event/timing/form, basis) or free `text` |
| `timeline[]` | start, end, label, kind (chapter · window · pressure · watch), basis |
| `watch_list[]` | when, observable sign, what it would mean |
| `uncertainty` | birth time (calculated sensitivity), engine differences, contradictions, not assessed |
| `practical_summary[]` | short actionable lines |
| `appendix` | positions, periods, method, sources — the only place for chart detail and page references |

Each unit's `basis` (its chart relationships) is moved by the renderer into an appendix table "Why each
conclusion", so technical traceability is kept without chart facts in the client text.

## 2a. Report types and the registry (updated 2026-11-21)

`assets/report/registry.json` lists 30 types: 28 `built` and 2 `folded` (counted 2026-11-21; none `planned`). The status
`folded` carries `folded_into`: kaal-sarp is a strict-form unit inside the Kundli (`kundli.md` §2a) and pitra-dosha is
read as pitri rin inside the lal-kitab report. A folded type has no spec of its own and cannot be written; the `/report`
menu says which report holds it. The eight types added in 3.12.0, each with a spec in `references/report-specs/`:
jupiter-transit, rahu-ketu, varshaphal, sade-sati, mangal-dosha, raj-yoga, match and lal-kitab.

- **Match is a two-person model.** `birth.persons` holds exactly two births (written as Person A and Person B; the outer
  birth time is the less certain one) and `consent` holds the fixed consent sentence. The cover prints one line per person
  and no rasi chart is drawn. `render_report.match_errors` checks consent, neutral names, four kootas in order with their
  exceptions, no 36 total, Mars per person under the four rules and the both-charts cancellation. Only the service and the
  MCP `create_report` accept `persons` and `consent`; REST and the CLI take one birth and cannot run a match.
- **Lal Kitab** has its own sections and gate (`lk_errors`): Lal Kitab units only, no timeline, no report on an unknown
  time, a pitri rin unit, rin never above Weak. The `lk-year` section sits inside private-edition markers and drops
  when the annual table is absent, so the public edition has three sections.
- **Kantaka and Ashtama Shani** appear in the sade-sati report as a fixed sentence (`KANTAKA_NOTE`), always graded Weak.
- **Wording gates** are word and clause rules in `render_report.py` and `medical_words.py`. They are a backstop with
  known leaks and over-blocks (CHANGELOG 3.12.0, PENDING L15).

## 3. Visual design

Cream and green, from `references/visuals.md`: warm paper and ivory surfaces; botanical, forest and pine greens for
structure; sage and eucalyptus tints; clay only for counter-evidence and pressure periods; bronze as a single cover
rule. Serif headings (Iowan Old Style → Palatino → Georgia), sans body (Avenir Next → Helvetica Neue → Arial). No
meters, stars or percentages; confidence is written in words; timeline kinds differ by fill *and* border style so
colour is never the only carrier. A4, page numbers and running title, cover without numbering.

Rendering pitfalls found and fixed: Jinja2 auto-escaping broke the embedded stylesheet (quotes became entities) — the
CSS is marked safe; WeasyPrint ignores CSS variables inside `font` shorthands and margin boxes — fonts and page
colours are spelled out.

Changes of 2026-11-14 (T11): the cover prints the birth-time source once; the kundli snapshot column reads "How clear the chart is"; "That it happens" appears only on predictions; raw claim tokens are gone; the key lists only the labels a report uses; months print as words; an empty best window reads "no single window"; the chart caption says the numbers are signs; every remedies unit must carry the no-efficacy line.

Evidence chips, the one legend block, birth-time sensitivity states, the per-type "This report answers" line, the type scale and contrast figures are specified in [`REPORT-DESIGN-SPEC.md`](REPORT-DESIGN-SPEC.md).

## 4. Using it

```bash
python3 scripts/render_report.py report.json --out OUTDIR        # validate, check, render HTML (+ PDF)
python3 scripts/render_report.py report.json --check-only        # validate and check only
python3 scripts/render_report.py --selftest                      # uses assets/report/example-synthetic.json
```
In Claude Code on the development Mac: `_skill_workspace/.venv-report/bin/python` has Jinja2 and WeasyPrint.
Personal reports are saved where the person asks; never inside the skill or the repository.

Unknown birth time: `create_report` refuses house, lagna, varga and dasha claims by a word and fact-id guard
(`render_report.unknown_time_errors`). That guard is a backstop, not proof; the skill's rules and an independent
checker are the main safety.

## 4a. Review pages

Owner review pages for each batch are in `notes/t11/batch*/` (synthetic charts built from invented births; each page
describes the birth it prints, and `tests/test_report_specs.py` has an engine-truth test for the facts it can compare).

## 5. Tests

The self-test validates the synthetic example, checks that a bad model is rejected (unknown type, missing title,
unsupported year) and that timeline geometry stays inside the page. CI renders the example to PDF with WeasyPrint on
Linux. The v3.4 blind benchmark compares full reports (R01 career, R02 twelve-month) against v3.3.
