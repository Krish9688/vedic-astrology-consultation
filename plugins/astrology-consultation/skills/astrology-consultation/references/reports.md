# Professional reports (mode C), working record and continuity

A report is a consultation written down for someone who will reread it: the same judgement as mode A, organised so
the answer is found in the first page and the evidence last. The structure below comes from research into how
practitioners and report producers work — what to copy and what to avoid is in
`_skill_workspace/research/reports/SYNTHESIS.md`. All structure here is **DESIGN**, not classical doctrine.

## 1. Principles

1. **The short version first.** One-sentence headline and at most seven key points, each with its confidence word
   and window. Someone who reads only page one must leave with the right picture.
2. **By life area and by chapter, never house by house or planet by planet.** Houses and planets are evidence inside
   a section, not section titles.
3. **Every point is a life unit** (communication.md §1a): theme → meaning → likely form → timing → nuance → what
   argues against it → what to watch, with separate confidence for event, timing and form.
4. **One timeline for the whole report** instead of dates repeated in every section; calculated periods, interpretive
   windows and pressure periods drawn differently.
5. **Uncertainty is a section, not a disclaimer**: birth-time sensitivity (calculated, not estimated), engine
   differences, where the chart argues both ways, what was not assessed.
6. **Technical appendix last**: the chart basis of each conclusion, positions, periods, method, sources. Page and verse
   references live only here, and `appendix.sources` names **books** (author, title, page) — never the skill's own
   files, scripts or internal registers.
7. **Proportionate length**: compact 2–4 pages, topic report 6–12, twelve-month forecast 8–15, complete life report
   15–30. A catalogue of techniques is not thoroughness.
8. **Not in a report unless asked**: remedies (then only via remedy-safety.md), numerology, gemstones, lucky numbers,
   exhaustive divisional tables, month-by-month filler, numerical "indices".
9. **Balanced**: neither doom nor a glossy picture that hides a real difficulty; every difficulty with its size,
   duration and what remains open.
10. **Test every paragraph**: could it appear unchanged in someone else's report? Then it is not finished.

## 2. Report types

Sections are defaults — drop what the chart or the request does not support, add what the person asked for.

| Type (`report_type`) | Default sections, in order | Timing depth |
|---|---|---|
| `compact` — consultation summary | the questions asked, answered (one unit each) · current chapter · what to watch. When the person asks for "one page", keep the client text to about 450 words and leave out the timeline and appendix (two to three printed pages; a true single page needs about 250 words) | windows named in units |
| `career` | working pattern · current chapter · next 2–3 years · money · decisions and choices | chapter + one or two windows |
| `relationship` | the answer: the main window and its grade · how you relate · what draws you and to whom · the window ladder (promise → forming → formalising) · what to watch | one main forming window + fallback; formalising only as a later rung |
| `marriage` | the answer: promise grade and the main commitment window · the partner, as themes and ranges · the window ladder (forming kept apart from formalising) · married life themes | one main commitment window + fallback |
| `dasha` | the current major period in life terms · its sub-periods as chapters · the next major period · turning points | all sub-periods of the current major period, graded |
| `12-month` | the year's theme · season by season (not month by month) · by life area · pressure and opportunity periods | slow transits on the dasha backdrop; fast transits only if decisive |
| `relocation` | abroad or distance in the chart · what kind (travel, study, work stint, settling) · when · where it helps and costs | windows for moves |
| `complete-life` | *a story, not a catalogue:* core pattern → main strengths → the central tension → how these show in each life area (each section names which part of the core pattern it expresses) → the current chapter → what is changing → near/mid-term windows → long-term direction. Life areas: career · current chapter · career · money · relationships/marriage · family (parents, siblings, children) · home and property · health and wellbeing themes (non-medical) · travel and foreign links · friends and social life · personal and spiritual development · turning points ahead | chapters for the next 10–15 years; windows only where earned |

**One timing framework per report.** Reports with more than one window (career, 12-month, dasha, complete-life)
open the body with a short **Main windows** section: three to five named windows, each with dates, a one-line basis
and what it activates. Life-area sections then refer to a window by its name ("this is the work-heavy stretch from
the Main windows") and add only what is specific to that area — they do not re-explain the period lords or transits.
Each section must still read on its own: one clause of reminder, not a cross-reference. Give the section the id
`windows`; its units need only theme, meaning and timing (counters and signs to watch go in the life-area sections).
**Use every calculated trigger, or say why not.** Each slow-planet sign change or exact contact in the calculation's
horizon that touches the report's houses or their lords is either used or set aside with a reason in the appendix —
leaving one out silently is an omission (round 9: a career report missed Rahu entering the career house).

Every type ends with timeline (if any timing), what to watch, what is uncertain, practical summary, and the
technical appendix.

## 3. Producing a report

1. Do the workbench for each section as for a consultation (consultation-reasoning.md); retrieve and check sources as
   usual. A report does not relax any evidence rule — it multiplies the places where one can break.
2. Write the **Structured Report Model** (`assets/report/report.schema.json`) as JSON: `summary`, `sections` of life
   `units` (put the chart relationships behind each unit in its `basis` field — the renderer moves them to the
   appendix), `timeline`, `watch_list`, `uncertainty`, `practical_summary`, `appendix`. Use first name or initials
   only; birth data only if the person wants it printed.
3. Check and render: `python3 scripts/render_report.py report.json --out <dir>` validates the model, checks that the
   summary's windows are argued in the body, that units carry a counter-factor and a sign to watch, and runs the
   life-first lint; then it writes HTML and, when WeasyPrint is installed, a PDF (cream and green, visuals.md). Without
   WeasyPrint, deliver the HTML (it prints to PDF from a browser) and say so. `--check-only` validates without
   rendering. A worked synthetic example: `assets/report/example-synthetic.json`.
4. Read the rendered result before delivering it; fix the model, not the HTML.
5. Save reports where the person asks. Personal reports never go into the skill package or the repository.

## 4. Consistency

The summary, each section, the timeline and the watch list must state the same event, window and confidence. If a
key point is Moderate, the section that argues it cannot read as Strong. Counter-evidence sits beside the conclusion
it affects. A later section adds something new (an implication, a cost, a tension) or links back in one line — it
does not re-run the same planets.

## Lightweight per-report working record

For a short reading, ordinary context is enough. For a long report, multi-session draft or requested revision, keep one compact `report-state.md` in the authorized report directory. If saving has not been requested and no destination is established, maintain this structure in working context; ask where to save only if durable storage becomes necessary. This is not global memory or a reusable personal profile. Never put a client's biography into the skill package.

Record evidence, brief rationales and decisions, not private hidden deliberation. Use only fields the report needs:

| Section | Minimal fields |
|---|---|
| Scope/status | Question, reference date/timezone, output mode, requested coverage, drafted/reviewed/pending sections, exact next action |
| Evidence `E01...` | Fact, source/location/version, supplied/verified/derived/assumed/unavailable, convention, reliability, dependency group |
| Periods `P01...` | System/lord/parent, start/end/precision/timezone/year convention, source; authoritative source when alternatives conflict |
| Claims `C01...` | Proposition/horizon, temporal mode (past/current/future), history disclosure status; external circumstance versus conditional internal experience where relevant, supporting/moderating evidence IDs, period IDs, realistic alternative, event/timing/manifestation confidence and reasons, what changes it |
| Themes/life areas | Short conclusion, claim IDs, cross-domain tensions, where already explained; earlier/later claim links and the shared natal relationship/change in activation supporting each temporal bridge |
| Sources/techniques | Identifiable source/edition/passage, tradition/method, limitations; no vague claim of classical validation |
| Revision/outcome log | Original issue date/claim/window, new evidence/date, affected IDs, superseded/stale/current status; observed result and hit/miss/not-evaluable if scoreable |

Keep contradictions and confidence in the claim row instead of separate ledgers that can disagree. The only separate contradiction index needed is a short list of unresolved items. The period table is authoritative for dates; the narrative refers to it. Do not create duplicate Markdown/JSON stores unless actual automation requires a structured format with one declared source of truth.

### Small synthetic state example

```text
Scope: career, fictional supplied packet, reference date 2030-01-15 UTC.
E01: Libra D1 lagna; supplied partial teaching data, not an ephemeris.
E02: Moon in Cancer; owns/occupies 10th; dependency D1-Moon.
P01: supplied Moon/Moon interval; boundaries not supplied.
C01: career responsibility is a supported theme, timing not assessable.
Support E02; limitation incomplete chart, no dates/transits or stable D10.
Alternative: an internal assignment rather than a new employer.
Confidence: theme Moderate; timing Not assessable; exact job change Low.
Sections: focused answer drafted; check final wording against C01.
```

## Revision and outcome handling

On a changed fact, use its evidence ID to find all dependent claims, figures, theme summaries and period justifications. Mark them **stale** before rewriting. Preserve the old claim and its original dates; record the corrected source and why the interpretation changed. A corrected historical date or account can also invalidate a narrative bridge and a future rationale: follow earlier/later claim links, not just the original paragraph. Re-evaluate only affected sections, then scan the whole report for repeated stale facts. A wording edit alone does not require recalculating an unaffected chart.

Distinguish: **known history** (disclosed before analysis), **issued prediction** (saved before outcome), **observed afterward**, **superseded**, and **not evaluable**. A corrected date can invalidate a historical fit without invalidating every natal observation. A specific forecast that misses stays a miss under its original criteria even if the new outlook is favorable. Do not silently widen a window or switch methods to rescue it.

## Final consistency and recovery

After the human-language pass, compare final prose, table/graphic labels, summary and closing with the record. Look for changed duration/lord, a broadened event that retains a narrow event's confidence, missing alternatives, or unsupported new emotional details. Fix the underlying claim, not only a visible sentence.

If interrupted, save completed outputs and a compact handoff: objective/constraints, completed/in-progress/pending phases, evidence and source locations, decisions, tests/failures, unresolved issues, exact next action and remaining delivery criteria. Reload the state plus the original evidence needed for the next section. Do not restart completed work merely because the conversation was compacted. A draft, design specification or failed test is progress, not final delivery.

See [communication.md](communication.md) for prose and sensitive topics, [visuals.md](visuals.md) for optional visuals, and [qc.md](qc.md) for checks.


# Explaining a life trajectory

Original **DESIGN** guidance for temporal explanation. The [timing](timing.md) and [confidence](synthesis-method.md) rules govern inference; [communication](communication.md) governs general voice; [report](reports.md) owns the shared record; [visuals](visuals.md) alone governs appearance. No new astrology formula, calculator or memory service is introduced.

## When this reference helps

Use for a substantial life report or an answer that explicitly connects earlier periods, the current phase and future possibilities. A focused question need not become a life review. Give the requested temporal areas comparable explanatory care; equal care does not require equal word counts or invented detail where evidence is missing.

## The explanation unit

Explain a claim through one connected argument: the relevant chart relationship, why that relationship concerns this life area, what activates it in this interval, a plausible expression and its strongest limit. A technical term earns its place by changing the conclusion. Translate it on first use and then use the shorter familiar wording.

A planet's natural symbolism is not the whole mechanism. Explain its topic-specific house ownership, occupation or relationship before moving into daily-life meaning. A yoga name is a shorthand for those constituents, not additional evidence. Clarify how contradictory factors change the event or its cost rather than listing positive and negative traits in succession.

Lead with the reader's question. Use enough astrology to make the conclusion traceable without requiring the reader to decode a paragraph of abbreviations. Place fuller position/period tables in the existing report appendix. If a metaphor helps, make it brief and explanatory; never let a vivid image smuggle in a physical symptom, personality trait, certainty or unreported memory.

Technical specificity is necessary for traceability but does not defeat confirmation bias. Also ask what would distinguish this claim from another plausible manifestation and what outcome would count against it. Do not add a placement citation to a generic claim and call that validation.

## Past: explain the period without manufacturing a memory

First distinguish two tasks: interpreting disclosed history, or proposing historical hypotheses before history is revealed. Record which facts were known before analysis. A disclosed event can be interpreted; it cannot become a blind hit. Unreported events remain unconfirmed hypotheses, including emotionally plausible ones.

Select the significant intervals for a stated reason: a supplied MD/AD change, repeated activation of an important natal network, a usable topical confirmation or a historical transit overlap. Do not select only years that already contain memorable events. Explain natal promise and condition, the actual MD/AD links, relevant stable varga and period-appropriate transits when available. Today's sky cannot explain an earlier year.

For each interval give the likely theme, a small set of distinguishable possible expressions, the strongest contrary indication and the three confidence dimensions. Missing evidence narrows depth, not the person's possible life. Ask neutrally whether any of the proposed themes occurred; allow “none” and “something different.” Do not lead with a vivid event such as a parental separation or school change and invite the reader to reconstruct a memory around it.

When testing, save the original event classes/windows and confidence before comparing history. Include mismatches and non-events. Events used to choose a birth time or dasha convention are fitting data; reserve other events for a separate check. A symbolic interpretation of a confirmed event does not establish that symbolism caused it.

## Present: give the current phase its own explanation

Fix the actual analysis date/timezone. Derive the current MD/AD from the supplied authoritative calendar; include deeper levels only when available, relevant and stable. Explain the difference between the major-period backdrop, the current subperiod's channel and any verified transit trigger.

Develop external circumstances and possible internal experience separately. External themes may concern responsibilities, agreements, learning, relationships or resources. Internal language remains conditional: the same circumstances might increase motivation, expose a tension between priorities or encourage reassessment. A chart cannot observe thoughts, establish emotional diagnoses or confirm another person's intentions. When no current experience is reported, say so rather than writing as if the person has confirmed your portrait.

Name what is continuing, changing or unresolved, supported by the actual period comparison. If a boundary is approaching, state the calendar transition and how the incoming lord differs; do not declare that distress, illness or uncertainty ends that day. A supplied schedule provides a date, not a promise of relief. Real decisions retain their own evidence and deadlines.

## Future: develop the existing thread conditionally

Explain what the next supplied activation adds, removes or redirects relative to the present. Do not merely replace the planet name in the preceding paragraph. State which natal theme persists, why the next lord connects to it, what evidence opposes the favored event and which alternative remains plausible.

A future interval may continue a theme, bring a possible culmination, redirect it or have no clear connection to what came before. These are interpretive descriptions, not a compulsory four-stage life script. Do not make adversity a prerequisite for success or force every earlier experience to prepare a happy ending.

Distinguish an available opportunity from a predicted result. Broad period support can justify a broad hypothesis; narrower windows need the existing timing requirements. No unsupported offer count, salary, marriage deadline, medical recovery date or precise day is added for reassurance. Keep event, timing and manifestation confidence separate and explain their differences in normal prose.

## Join the periods without forcing a story

Follow a few chart-specific themes across time. For each bridge, identify the earlier claim, current claim and future claim it connects; show the shared natal relationship and the change in activation. A recurrence may express differently because the person's circumstances changed. Repetition is not independent confirmation.

An earlier reported experience may influence today's practical options, but that ordinary connection needs the person's account. Do not infer psychological causation, trauma, karmic punishment or a hidden “lesson” from a temporal sequence. Acknowledge gaps and discontinuities directly. Three unsupported chapters joined by fluent transitions are still unsupported.

Use the existing report-state file. Add temporal mode, history-disclosure status, current external/internal distinction and links to earlier/later claim IDs only where needed. Do not create separate past, present and future databases. On corrected history, recheck the dependent narrative bridge and its future rationale as well as the original past paragraph; preserve unaffected sections.

## Final delivery check

Can the reader tell what the chart suggests, why this period is relevant, what is known versus inferred, how it differs from the adjacent phase and what remains uncertain? Can a skeptical reader identify an alternative and what would count against the claim? Does the present get real analysis rather than one sentence between a biography and a forecast?

Check that every repeated date, fact and confidence agrees with the existing claim/period record after editing. Keep all visual decisions under the existing visuals reference. None of this guidance authorizes importing a reference report's typography, colors, graphics or personal story.
