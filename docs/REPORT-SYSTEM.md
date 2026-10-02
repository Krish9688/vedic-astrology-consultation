# Report system

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
| `report_type` | compact · career · relationship · marriage · dasha · 12-month · relocation · complete-life |
| `summary` | headline + at most seven key points, each with a confidence word, optional window and the section that argues it |
| `sections[]` | `units[]` of the life-first unit (theme, meaning, manifestation, timing, nuance, counter, watch, confidence per event/timing/form, basis) or free `text` |
| `timeline[]` | start, end, label, kind (chapter · window · pressure · watch), basis |
| `watch_list[]` | when, observable sign, what it would mean |
| `uncertainty` | birth time (calculated sensitivity), engine differences, contradictions, not assessed |
| `practical_summary[]` | short actionable lines |
| `appendix` | positions, periods, method, sources — the only place for chart detail and page references |

Each unit's `basis` (its chart relationships) is moved by the renderer into an appendix table "Why each
conclusion", so technical traceability is kept without chart facts in the client text.

## 3. Visual design

Cream and green, from `references/visuals.md`: warm paper and ivory surfaces; botanical, forest and pine greens for
structure; sage and eucalyptus tints; clay only for counter-evidence and pressure periods; bronze as a single cover
rule. Serif headings (Iowan Old Style → Palatino → Georgia), sans body (Avenir Next → Helvetica Neue → Arial). No
meters, stars or percentages; confidence is written in words; timeline kinds differ by fill *and* border style so
colour is never the only carrier. A4, page numbers and running title, cover without numbering.

Rendering pitfalls found and fixed: Jinja2 auto-escaping broke the embedded stylesheet (quotes became entities) — the
CSS is marked safe; WeasyPrint ignores CSS variables inside `font` shorthands and margin boxes — fonts and page
colours are spelled out.

## 4. Using it

```bash
python3 scripts/render_report.py report.json --out OUTDIR        # validate, check, render HTML (+ PDF)
python3 scripts/render_report.py report.json --check-only        # validate and check only
python3 scripts/render_report.py --selftest                      # uses assets/report/example-synthetic.json
```
In Claude Code on the development Mac: `_skill_workspace/.venv-report/bin/python` has Jinja2 and WeasyPrint.
Personal reports are saved where the person asks; never inside the skill or the repository.

## 5. Tests

The self-test validates the synthetic example, checks that a bad model is rejected (unknown type, missing title,
unsupported year) and that timeline geometry stays inside the page. CI renders the example to PDF with WeasyPrint on
Linux. The v3.4 blind benchmark compares full reports (R01 career, R02 twelve-month) against v3.3.
