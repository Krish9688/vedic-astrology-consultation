# Cream and green visual system

Contents: tokens; semantics; figure selection; figure contract; typography/layout; validation. This is **DESIGN** guidance for requested reports, not a chart calculator or mandatory renderer. Text-only consultation remains fully usable.

## Palette and hierarchy

Warm surfaces dominate. Green shades carry titles, tints separate information gently, and tones reduce competition. These example colors form a related family around botanical `#3F6B52`; tint/shade/tone mixtures are simple sRGB design mixes, not perceptually equal steps.

| Role | Color | Use |
|---|---|---|
| Warm paper / ivory | `#F7F3E8` / `#FFFDF7` | Main canvas / chart and reading surfaces; white print variant |
| Base botanical | `#3F6B52` | Analytical lines and emphasis |
| Mint / pistachio / eucalyptus tints | `#ECF0EE` / `#CFDAD4` / `#A9BCB1` | Base mixed with 90%/75%/55% white; note backgrounds, bands and large secondary fills |
| Forest / pine shades | `#2F503E` / `#203629` | Base mixed with 25%/50% black; headings, main boundaries, occasional concise inverted takeaway |
| Moss / sage tones | `#5C7768` / `#6E7E75` | Base mixed with 40%/65% gray `#888888`; secondary diagram lines / decorative borders |
| Body / muted ink | `#26342C` / `#58685A` | Body text / captions on approved light surfaces |
| Parchment | `#E9E0CE` | Appendix bands or quiet alternate surface |
| Clay | `#8B5039` | Explicitly labeled moderating evidence |
| Antique bronze | `#9A783E` | Restrained decorative rule; not normal small text on cream |

Calculated intended pairs: body/cream 11.76:1, forest/cream 8.10:1, muted ink/cream 5.35:1, clay/cream 5.73:1, body/mint 11.34:1, body/pistachio 9.09:1, ivory/pine 12.74:1. Moss/cream is 4.41:1: suitable for essential lines at the 3:1 target, **not** ordinary small text at 4.5:1. Bronze/cream is 3.69:1 and stays decorative. Check every new adjacent pair; do not round a near miss up. See DESIGN sources in [source-index.md](source-index.md).

## Semantic rules

- **Supports:** botanical solid rule plus the label. “Support” always refers to the stated proposition, not universal goodness.
- **Moderates/alternative:** clay dashed rule plus label. Do not use ominous warning styling for routine uncertainty.
- **Unknown/unverified:** outlined neutral symbol plus explicit words, never zero strength or negative coloring.
- **Confidence:** event, timing and manifestation in equal-size text fields with reasons. No filled meters, star scores, percentages or larger marks implying measured probability.
- **Time:** distinguish supplied astronomical/period spans, observed events and interpretive windows with labels and line patterns. Use hatched/outlined forecast spans and explicit uncertainty at their edges; do not make approximate dates look exact.
- **Planets:** names or clear abbreviations with a legend. Green is the document identity, not an invented planetary correspondence or new astrology rule.
- **Decoration:** a single pale motif family at a cover edge or major divider. No scale, measured labels or claim that its dots are actual stars. Keep it outside reading areas.

Do not use neon, rainbow planet palettes, gradients, simulated metal effects or large dark interior pages. A warm report need not decorate every page. Distinctive identity can come from open-sided notes, a consistent rule/spacing system and careful typography rather than rectangles around every paragraph.

## Select figures for a job

| Visual | When and why it helps beyond prose | Position/type | Required integration |
|---|---|---|---|
| D1 chart | Full chart report: shows occupancy and concentration spatially | Chart orientation; analytical | Ivory/forest/ink, readable ascendant and key; text positions alongside |
| D9 | Supplied reliable dignity/partnership comparison actually changes the answer | Relevant topic/appendix; analytical | Same grammar; identify method and stable versus nominal facts |
| D10/other topical varga | A work/residence/etc question benefits from comparison with its D1 network | Topic/appendix; analytical | Select only the needed division; no missing data invented |
| North/South format | Choose the reader's familiar convention; do not duplicate by default | Every chart; analytical | North fixes houses; South fixes signs; explicit caption and legend |
| Positions table/degree strip | Table for exact supplied values; strip only for a decisive proximity/boundary | Appendix or claim; analytical | Actual precision, clear scale/source; no reconstructed degrees |
| Planet/house strength bars | Actual comparable numeric data matter to the argument | Technical overview; analytical | Zero baseline, units/normalization/benchmarks, labels; do not cap values at 100 or imply happiness/success |
| BAV/SAV grid | Supplied point distributions inform a transit comparison | Transit appendix; analytical | Values plus tints, table identity/reduction convention, missing cells labeled |
| MD/AD timeline | Multiple supplied periods or boundary changes are hard to compare in prose | Current/future overview; analytical | Nested spans, accurate lengths and containment, timezone/precision, explicit scale breaks |
| Transit/opportunity lanes | Distinguish verified repeated passages from a proposed event window | Timing discussion; mixed analytical/interpretive | Labeled solid data spans and hatched hypothesis spans; anchors/source/crossings |
| Past-present-future timeline | Longitudinal report needs an observation/forecast distinction | Overview; mixed analytical/interpretive | Dated known events, explicit reference date, qualified future; no invented biography |
| House/lord/yoga map | A complex claim has shared supports and counterevidence | After explanation; interpretive reasoning diagram | Few nodes, labeled owns/occupies/aspects/moderates links; same fact not counted twice |
| Theme/activation matrix | Several topics and periods genuinely need comparison | Overview/appendix; interpretive | Supported/mixed/not assessed text, no fabricated numerical intensity or smooth life-success curve |
| Confidence fields | Major claims need several kinds of uncertainty visible | Beside forecast; qualitative assessment | Equal text fields, short reasons; source reliability in a separate note |
| Nakshatra/pada strip | Reader needs a division/boundary explained | Educational note; analytical | Actual supplied longitude and division; never confuse it with a constellation photograph |
| Glyph/rashi key | A novice needs abbreviation help | First chart/glossary; explanatory | Full names available; no glyph-only data |
| Botanical/Jyotisha-inspired geometry | Requested report benefits from atmosphere | Cover/divider; decorative | Sparse pale tone; no implied chart fact, orbit or real star configuration |

Do not add every visual. For a short answer, no figure may be needed. A dominant-planet badge requires a defined supplied measure; Shadbala rank is not synonymous with topical importance. A table often explains exact values better than a graphic.

## Figure contract

Before drawing, identify: input/source and source status; chart/method or scale; data versus interpretation versus decoration; exact claim it helps; caption/legend; text alternative; missing-data behavior. Use one source for graphic and table. If positions conflict, resolve or quarantine before drawing; a polished figure cannot certify a disputed chart.

Keep every sign, house and planet label legible at final viewing size. In North Indian charts, place house/sign labels explicitly and keep multi-planet groups inside their cells. In South Indian charts, preserve fixed sign order and mark the ascendant. Never compute a new physical sky from varga positions. Use vector lines/text where possible; raster figures need adequate final resolution and adjacent data text.

## Typography, page rhythm and navigation

Use a readable serif title and sans body pairing; Georgia and Arial are example installed-font choices, not bundled dependencies. Select available licensed fonts/fallbacks and inspect the actual render. Suggested A4 starting values: 21–23 mm margins, 11.5–12 pt body, 1.35–1.45 line spacing, 24–28 pt titles, 17–19 pt section headings, 10–10.5 pt captions/tables. Prefer comfortable prose lines of roughly 60–80 characters. Never shrink data excessively to force a page count.

Use a 4/8/12/20/32 pt spacing rhythm. One chapter title with a short orientation is usually enough. Put a few decisive points in a callout; keep long explanation in prose. Favor flexible chapter flow over a new page for every short section. Keep short cards and rows together, repeat table headers, and avoid isolated continuation fragments. Convert prose-heavy tables to paragraphs or move wide data to an appropriate appendix.

Generate navigation from the final headings/pages. For DOCX use semantic headings, a refreshed contents field and actual page fields; for PDF use navigable bookmarks/links when available; for HTML use heading anchors and semantic tables. Verify every visible contents reference after final pagination. A contents title without entries is not working navigation.

## Final visual check

Render the actual export. Inspect every page for clipping, overlaps, fragment pages, font fallback, crowded chart labels, header/footer errors and incorrect data. Test a narrow digital view and grayscale/white-paper print behavior as applicable. Body text target 4.5:1, large text 3:1, essential nontext boundaries 3:1; never rely on color alone. Provide text equivalents, meaningful image descriptions, semantic headings and reading order. Selected contrast checks or a visually good PDF do not establish full WCAG/PDF-UA conformance; disclose unsupported accessibility features.

If a renderer or format cannot preserve the intended behavior, correct the layout or deliver a clearly identified accessible text alternative. Do not claim unperformed visual checks. See [qc.md](qc.md) and [reports.md](reports.md).
