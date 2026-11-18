# Report specs: the shared frame (T10 pilot)

One spec per report type in [`assets/report/registry.json`](../../assets/report/registry.json):
[kundli](kundli.md), [relationship](relationship.md), [career](career.md), [wealth](wealth.md),
[education](education.md), [reputation](reputation.md), [spirituality](spirituality.md), [self](self.md),
[family](family.md), [challenges](challenges.md). Each spec lists the body sections in order,
every computed field with the engine tool that gives it, the conventions, the caveats and what to drop when data is
missing. The frame below is the same for all of them. It comes from the owner's report template (shared frame, tone
guide, QC checklist) and is **DESIGN** (the skill's own rules), not classical doctrine.

Three things stay apart: **calculation** (an engine tool prints every number), **retrieval** (the books, cited by id
and page in `appendix.sources`) and **interpretation** (the writer's judgement, graded). A field whose calculation does
not exist is dropped and named, never estimated.

## 1. The frame and where each item lives in the model

| # | Frame item | Model field | Rendered as |
|---|---|---|---|
| 1 | Scope line | `scope` | top of "The short version" |
| 2 | Confidence note | `confidence_note` (grade words only) | under the scope line |
| 3 | Basis, tagged | each unit's `claim_type` (+ `basis`) | a "Calculated fact" chip for `fact`, "Interpretation" for the rest; chart basis in the appendix table |
| 4 | Core reading | `sections[]` in the spec's order | life units |
| 5 | Timeline | `windows` section + `timeline[]` | one timing framework: the windows section names each window once; the other sections point to it by name |
| 6 | Ranking / verdict table | `ranking[]` (`item`, `support` grade, `why`, `window`, `caution`) | after the timeline (kundli: under the short version, as the snapshot) |
| 7 | Cautions, dated | `watch_list[]` and `timeline` rows of kind `pressure` | "What to watch for" |
| 8 | Actions, dated | `practical_summary[]` | "In practice" |
| 9 | Confirmed / Inferred / Hypothesis | derived from `claim_type`: fact = Confirmed; rule, interpretation = Inferred; prediction, speculation = Hypothesis | "Evidence ledger" |
| 10 | Next step | `next_step.questions[]`, `next_step.follow_ups[]` | "Next step" |

A model that carries `depth` (`standard`, or `full` for the kundli) is checked against its spec by
`render_report.spec_checks`; a model without `depth` is a legacy model and keeps the old checks only. A section the
chart or the data cannot support is listed in `dropped` with its reason (printed under "What is uncertain"); the
same goes for the ranking table (`"item": "ranking"`).

## 2. One confidence scheme

Strong / Moderate / Weak / Contradictory / Unknown, defined as how much of the chart agrees, never a probability
(synthesis-method.md). Every claim carries one: key points (`confidence`), units (`confidence.event`, `.timing`,
`.manifestation`), ranking rows (`support`) and timeline rows of kind `window` or `pressure` (`confidence`). The
template's High/Med/Low and "strength ratio" are not used as a second scale: a Shadbala ratio is a computed fact in
the appendix, and its reading in the text is a grade word.

## 3. Birth time decides what may be dated

| `birth.time_reliability` | What the report may contain |
|---|---|
| exact (the word "exact" in `time_reliability`, e.g. "exact (birth certificate)"; anything else that is not unknown counts as approximate) | everything in the spec; dates as months or periods |
| approximate | months at most, no exact day; every unit whose basis uses a house, lord, lagna, varga or dasha carries `sensitivity` from `get_birth_time_sensitivity`; drop a section whose factor class is `high` or `very high` |
| unknown | labelled monthly transit markers only (one-month `watch` rows whose label says "marker"), no day, no date range, no house, lagna, varga or dasha claim anywhere in the client text; sections that need them are dropped with the reason (timing.md §0, owner decision 2026-11-13) |

Engine gate (owner decision 2026-11-14): `astro/service.py` `create_report` lets every report type run on an unknown
birth time. It refuses time-dependent fact ids, event ids, dated windows and any timeline row that is not a labelled
monthly marker, and it runs `render_report.unknown_time_errors`: no house, lagna, varga or dasha terms (built from `scripts/vocab.py`,
with Sanskrit spellings, hyphenated and spaced forms), no time-dependent fact ids, no event ids. The gate fails closed:
if the check cannot run, nothing is rendered. "Unknown" is the one pattern `UNKNOWN_TIME`, shared by the engine and
the renderer.

On an unknown time the Moon's sign and nakshatra are used only if they are the same across the whole birth day
(inputs.md, unknown-time procedure; the engine measures it with `time_varying_facts`); otherwise they are dropped with
that reason. To use them, set `birth.moon_stable: true`; `create_report` recomputes the day and refuses the flag when
the Moon's sign or nakshatra changes (the `render_report.py` script cannot recompute the day, so it refuses the flag). A marker's natal point must be equally stable (a slow planet's sign is; the Moon's often is not).

The word guard is a backstop, not proof: some wordings still pass it. The skill's rules and the independent
checker are the main safety for unknown-time reports.

## 4. QC checklist: what is automated

`render_report.spec_checks` turns the owner's checklist into errors where text can show it:

| QC item | Check |
|---|---|
| scope line and confidence note at the top; next step | `scope`, `confidence_note`, `next_step` required |
| basis tagged | every unit has `claim_type` |
| ranking table and timeline present | `ranking` (or dropped); a timeline window needs the `windows` section |
| a grade word beside each claim | units (except facts), timeline window and pressure rows |
| no percentages | no `%`, "percent" or "percentage" in client text |
| partner and appearance caveat | looks or age words only in the `partner` section, graded Weak or Unknown; caveat printed there |
| affairs: own tendencies only | a fidelity sentence may not be about another person |
| no exact day when the time is not exact | no `YYYY-MM-DD` or day-month dates; timeline months only |
| books named | `appendix.sources` non-empty, each starting with a catalog book id, none naming the skill's own files |
| missing data dropped | spec sections present or in `dropped`; unknown time: no house, varga or dasha words |

Not automated (the writer checks them): birth data matches what the person gave; every placement was computed, not
recalled; the same dates and periods in every section (`checks` warns on restated windows); tone.

## 5. Lal Kitab stays out

These reports are Parashari (with Jaimini karakas and arudhas). Lal Kitab readings and remedies, LK remedy cards included,
never appear in them, the `remedies` section included; Lal Kitab has its own report. `spec_checks` refuses a
`lal_kitab` unit or a `remedies` card block in a spec report.

## 6. Tone (owner's guide, kept)

Lead with the answer; tie every claim to a named factor; rank and give the reason; plain verbs; state confidence once;
separate Confirmed, Inferred and Hypothesis; warm and direct; tendencies, never illness, death or fixed outcomes; say
what only the person can confirm; intimate topics tasteful and tendency-level. Pattern: factor, meaning, what it looks
like in life, what to do. Specific numbers only when an engine tool computed them (the template's "about 5'4" to 5'7""
has no calculation behind it and is not used).
