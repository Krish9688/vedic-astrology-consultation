# Report design spec (T2.3b, 2026-11-07)

> **What:** the visual design of client reports. **Read it when:** you change a report's look.
> **Last checked:** not checked.
> **Related:** REPORT-SYSTEM.md.

Our own design for client reports. It extends `references/visuals.md` (palette, figure contract) and
`references/reports.md` (content, unit model); it does not replace them. Applies to the structured report
(`render_report.py`: HTML, PDF) and the consultation report (`consultation.py`: HTML, PDF, DOCX). Implemented in
`assets/report/` (template.html.j2, consultation.html.j2, legend.html.j2, report.css, consultation.css).

## 0. Provenance and what we do not take

Written from our own files, our own gap list and public design standards (WCAG 2.2 AA, ICD 203 style confidence words,
W3C complex-image guidance). No competitor's report was copied. We must NOT take from any competitor: their wording or
blurbs, product or report names, logos, icons, illustrations, ornament, colour theme or any near match to it, card layouts
or promotional tags, numeric scores or percentages, lucky colours or numbers, "most accurate" claims, credit-pack or upsell
language. The only idea carried over is generic: a report may begin with the question it answers. Our identity stays cream and green.

## 1. What this report answers (one line per type, printed on the cover)

The line is the reader's own question, shown under the title as "This report answers". A model may override it with
`answers`. Strings live in `render_report.ANSWERS`.

| Type | Line |
|---|---|
| compact | What did the chart say to the questions I asked, and what should I watch next? |
| outlook | What is the running period asking of me in the coming weeks, and is any event actually timed? |
| career | What kind of work suits me, which chapter am I in, and when are the next windows for a move or step up? |
| relationship | How do I relate to others, and when is a relationship most likely to form or deepen? |
| marriage | Is marriage supported, when is the main commitment window, and what themes shape married life? |
| dasha | What is the running major period like in life terms, and which turning points follow? |
| 12-month | What is the theme of the coming year, and which stretches bring opportunity or pressure? |
| relocation | Does the chart point to living or working far from home, in what form, and when? |
| complete-life | What is the core pattern of this chart, and how does it show across life areas now and ahead? |
| consultation report | The questions you asked (section 6), and what the chart says about the life areas behind them. |

Each line is a question, has no number, no promise and no superlative.

## 2. Section order

Frame (every structured report), with the type body from `reports.md` section 2 in the middle:

1. Cover: type kicker, title, subtitle, "This report answers", prepared for/on, birth-time source and reliability,
   method line, one-sentence limits.
2. The short version: headline, at most seven key points (grade word, optional birth-time chip, window, link).
3. How to read, then the **legend** (section 10), then contents when there are more than three sections.
4. Main windows (types with more than one window: career, 12-month, dasha, complete-life; section id `windows`).
5. Body sections by life area, each a run of life units (section 6).
6. Timeline: bars, then the table (with a Birth time column when any row carries a state).
7. What to watch for.
8. What is uncertain: birth time, **what moves with the birth time** (units and windows that are not stable),
   contradictions, calculation differences, not assessed.
9. In practice. 10. Technical appendix (basis table, chart, positions, periods, method, sources).

Type bodies (frame stays): **compact** questions answered, current chapter, watch; no full legend, one-line key.
**outlook** running period, event-level factors or the plain statement that none is timed, texture last; two pages,
one-line key. **career** pattern, chapter, next 2-3 years, money, decisions. **relationship** answer and main window,
how you relate, who draws you, window ladder, watch. **marriage** promise grade and commitment window, partner themes,
window ladder, married life. **dasha** current major period, sub-periods as chapters, next major period, turning
points. **12-month** theme, seasons, life areas, pressure and opportunity. **relocation** distance in the chart, kind,
when, help and cost. **complete-life** core pattern, strengths, central tension, life areas, current chapter, change,
windows, long term. **Consultation report** keeps its nine numbered sections; the legend follows "How to read" on the
short-version page.

## 3. Layout grid

- A4, margins 22 mm top, 21 mm sides, 24 mm bottom; cover full bleed, no page number. Running title bottom left,
  "n / N" bottom right, 8.5 pt.
- One text column, measure 60-80 characters (about 165 mm). Screen: max 820 px, 16 px gutter.
- Life unit: two-column grid, 33 mm label column, text column the rest, 10 pt gap. Under 560 px it stacks.
- Confidence fields: three equal boxes in a row (event, timing, form); they stack on narrow screens.
- Timeline: label column 38 %, track 62 %, 14 pt track, 18 pt row. Key and table follow the bars; rows and units never
  split across pages; table headers repeat.
- Spacing rhythm 4 / 8 / 12 / 20 / 32 pt (existing values stay until a layout change touches them).
- Section headings start with a 1.5 pt botanical rule; the legend is a row-ruled table, not a card.

## 4. Typography scale

Serif (Iowan Old Style, Palatino Linotype, Palatino, Georgia) for titles and unit themes; sans (Avenir Next,
Helvetica Neue, Helvetica, Arial) for body, labels, tables. No bundled fonts, so the fallback chain is part of the
check. **Minimum size 8 pt** (was 7.5 pt).

| Role | Size / line | Notes |
|---|---|---|
| Cover title | 30 pt serif, 1.2 | compact 20 pt |
| Section heading h2 | 18 pt serif | compact 14 pt |
| Sub heading h3 | 13 pt serif | chapter title 15 pt |
| Headline / answer line | 15 pt / 12 pt serif, 1.4 | |
| Unit theme | 12.5 pt serif semibold | |
| Body | 10.5 pt sans, 1.45 | |
| Tables, captions, small | 9-9.5 pt | |
| Labels (chips, dt, kicker) | 8-8.5 pt uppercase, .04-.14 em spacing | muted ink, never moss |

## 5. Colour tokens (light, print-safe)

The cream and green family is ours (visuals.md); this spec adds no new hue. Tokens live in `report.css :root`. Colour
only supports meaning: every state also has a word and a shape (border, underline style, fill, fade). Measured WCAG
contrast (small text needs 4.5, large text and boundaries 3.0):

| Pair | Ratio | Use |
|---|---|---|
| ink on ivory / paper / mint | 12.8 / 11.8 / 11.3 | body |
| muted on ivory / paper / mint | 5.8 / 5.4 / 5.2 | captions, labels, notes |
| forest on ivory / mint / pistachio | 8.8 / 7.8 / 6.3 | headings, grade words |
| pine on ivory / pistachio | 12.7 / 9.0 | chip text, headings |
| clay on ivory / mint | 6.3 / 5.5 | counter-evidence, Contradictory |
| moss on ivory / paper | 4.8 / 4.4 | lines and boundaries only; small text on paper fails, so labels use muted |
| sage on ivory | 4.2 | decorative borders only (it was used for 7.5 pt refs; now muted) |
| bronze on paper | 3.7 | single cover rule only |
| muted on pistachio / eucalyptus | 4.1 / 3.0 | never used for text |

`tests/test_report_design.py` re-checks the small-text pairs. Grayscale print must stay legible (section 12).

## 6. Evidence labels (one chip per point)

Each life unit shows a row of chips under its theme, with the existing label wording unchanged. The first chip (claim
type) differs by **shape**, not only colour:

| Claim type | Label | Shape |
|---|---|---|
| fact | Calculated fact | solid 1.5 pt border, pistachio fill, square |
| rule | Traditional rule (cited) | solid 1 pt border, mint fill, square |
| interpretation | Interpretation | dashed border, ivory, square |
| prediction | Prediction (interpretive) | dashed border, rounded, italic |
| speculation | Speculative | dotted border, rounded, italic, muted text |

Second chip: basis (Source text, Commentary, Disputed between sources, Calculated, Tested plus the log result,
Speculative), quiet underline. Third: system (Parashari, Jaimini, Lal Kitab, Combined). Fourth, past units only:
"Past: confirmed | not confirmed | contradicted". Last, only when a state is given: the birth-time chip (section 8).
Computed and interpretive claims are told apart at a glance because fact and rule chips are filled and the rest are
open. Key points carry the grade word and, if given, the birth-time chip.

## 7. Confidence

Words only: Strong, Moderate, Weak, Contradictory, Unknown, for event, timing and form as three equal fields with
reasons in the text. Each word has its own underline (Strong thick solid, Moderate thin solid, Weak dashed, Unknown
dotted, Contradictory thick double in clay), so the five stay apart in grayscale. No bars, stars, meters or
percentages. The legend defines each word as "how much of the chart agrees", never a probability.

## 8. Birth-time sensitivity: three states

Optional field `sensitivity` on units, key points and timeline rows (schema: `stable | may_shift | depends`), taken
from the calculation (`get_birth_time_sensitivity`), never guessed. The consultation model's boolean `time_sensitive`
maps to `depends`; under an approximate birth time a window without the flag is drawn `stable`; with an exact time no
marks are drawn (nothing varies); with an unknown time the timeline is withheld as before.

| State | Chip label | Chip shape | Bar edge |
|---|---|---|---|
| stable | Birth time: stable | thin solid border | crisp ends |
| may_shift | Birth time: may shift | thick dotted border | dotted ends |
| depends | Birth time: depends on exact time | thick double border | both ends fade into the page |

The uncertainty section lists every unit and window in `may_shift` or `depends`, so prose and marks agree. Known
limit: the consultation pipeline produces only `stable` and `depends`; `may_shift` needs the minutes from the
sensitivity table and is set by the report writer for now.

## 9. Charts and timelines

- Charts follow `visuals.md` and `chart_svg.py`: North or South, `role=img` with a title, positions table beside it.
- Bars: fill plus border per kind (calculated period: pistachio, no border; interpretive window: eucalyptus with 1.5 pt
  pine border; pressure: clay-tint fill, dashed clay border; watch: ivory, dotted pine border). A dashed end means the
  period continues past the chart. Sensitivity edges (section 8) are applied after the cut markers.
- A timing window shows its basis in the table beside it and its dates as a period, never a day. Confidence of timing
  sits in the unit's "When" field, not on the bar.
- Long chapters are clipped and marked; rows wholly outside the zoomed axis stay in the table.

## 10. The legend (one block)

`legend.html.j2`, printed once after "How to read", as a table so DOCX keeps it: evidence labels (structured report
only), the five confidence words, the three birth-time states, the four bar kinds. The timeline footer repeats the
bar and sensitivity keys in one compact line. Compact and outlook reports use a one-line key. Every label rendered in a
chip is in the legend (`tests/test_report_design.py`).

## 11. Tone rules

No scores, indices, percentages or star ratings. No luck items (lucky colours, numbers, gemstones) unless remedies were
requested, and then only via remedy-safety. No sales, upsell, urgency or exclusivity language; no "most accurate" or
"guaranteed". No fear framing: a difficulty is stated with its size, duration and what remains open. No false
precision: periods not days, windows with a stated basis, birth-time dependence stated where the calculation shows it.
Second person, outcome first, plain words; technical terms translated on first use; a paragraph that could sit
unchanged in another person's report is not finished. Past readings stay "not confirmed" until the person confirms.

## 12. Checks

`render_report.py --selftest`; `tests/test_report_design.py`, `test_claim_basis.py`, `test_outlook_report.py` (two
pages), `test_consultation_report.py`; render HTML, PDF (WeasyPrint) and, for the consultation report, DOCX for
synthetic personas only; read the HTML text; look at each PDF page for clipping, missing labels, the legend and the
fade; convert to gray and confirm every chip and bar kind is still distinct.

## 13. Not decided here

Dark screen theme (rejected for print), icon tiles per life area (decorative, optional later), a browsable report menu
(low priority), DOCX for the structured report (not produced today), minute values on `may_shift` edges.
