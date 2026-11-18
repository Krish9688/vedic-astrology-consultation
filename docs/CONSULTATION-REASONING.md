# Consultation reasoning architecture (skill v3.2, extended in v3.4)

> **What:** how the skill turns a chart and a question into an answer: the flow, the roles and the research behind it (Appendix). **Read it when:** you change how answers are reasoned or worded.
> **Last checked:** 2026-11-12 (the Appendix was merged in; the rest not checked).
> **Related:** ROADMAP.md, TESTING.md, KNOWLEDGE-SYSTEM.md.

v3.2 adds a reasoning layer on top of the v3.1 knowledge system. Nothing below replaces the calculation inputs, the
books, the Graphify knowledge graph, provenance, the contradiction register, or the Jaimini/Lal Kitab separation.

> **Editions.** From 3.7.0 the public edition also answers Lal Kitab requests, as a separate system from Parashari and
> with remedies only on request; the knowledge-base and annual-table parts below describe the owner's private build.

## 1. The flow

```
User question
  ↓  understand intent, restate answerably, classify (promise / timing / open activation / description /
  ↓  comparison / explaining the past), fit to age and situation            consultation-reasoning §1
Chart data from a calculation engine (never from books or the graph) → chart_facts.py
  ↓  walk the question's tree: which houses, lords, karakas, vargas, periods matter; P / S / X tiers   question-trees
  ↓  give each factor a ROLE (promise, capacity, quality, form, obstruction, activation, trigger, context)  §2
  ↓  natal PROMISE class (promised / delayed / modified / weak / not supported)                           §3
  ↓  ACTIVATION: MD chapter → AD episode → PD narrowing; kept separate from promise                    §4, timing §0
  ↓  TRIGGER: slow transits inside active periods; base-rate discounts; granularity earned               timing §0
  ↓  retrieve supporting rules and disputes: kg.py sources / search.py --page (Graphify graph + index)
  ↓  SCENARIOS: 2–4 concrete manifestations ranked by specific support                                    §5
  ↓  CONTRADICTIONS: decide what each factor controls; both strands kept                                  §6
  ↓  CONFIDENCE per claim (event / timing / manifestation) from quality, not quantity                     §7
  ↓  (optional) calibration against dated past events                                                     §8
  ↓  separate systems (Jaimini, Lal Kitab, KP) in their own notes; cross-system agreement only at the end §9
  ↓  ANSWER: conclusion → likeliest form → timing → nuance → decisive reasons → early sign → confidence
            (≤ ~4 chart facts; technical basis optional)                               communication §1
```

Graphify's role is unchanged and deliberately limited: source retrieval, page lookup, disputes, provenance,
related rules and cross-book/cross-tradition evidence. It never decides the judgement.

## 2. Components

| Concern | Where | Key rule |
|---|---|---|
| Question classification | consultation-reasoning §1 | Class decides the technique budget; one clarifying question only if the answer depends on it |
| Technique selection | question-trees | Walk only the branches the question needs; the 23-factor checklist is a safety net for full readings |
| Evidence hierarchy | question-trees (P/S/X), consultation-reasoning §2 | Supporting evidence never overturns a primary verdict; roles before meanings |
| Natal promise | consultation-reasoning §3 | Five classes; "not supported" needs ≥ 3 independent afflicted channels incl. the varga arbiter |
| Dasha activation | consultation-reasoning §4, timing §0/§2 | Read the lord whole first; Raman's relevance tiers; scale match |
| Transit confirmation | timing §0/§3 | Transits say when, not which way; loops are one episode; double transit is supporting only |
| Divisional charts | vargas.md, question-trees | Confirm/qualify within their domain; veto only when the whole varga network fails; stable times only |
| Contradictions | consultation-reasoning §6, synthesis-method §5, contradiction-register | Assign control (occurrence / timing / quality / pace / form); report both strands |
| Scenarios | consultation-reasoning §5 | Rank by specific support; say when the chart doesn't separate them |
| Timing synthesis | timing §0 | Precision budget (n × m ÷ 4 days); half-year → quarter → month earned by convergence; never a day |
| Confidence | consultation-reasoning §7, synthesis-method §4 | Promise class caps; independent channels; directness; birth-time stability; source tier; base rates |
| Response generation | communication §1, §6a–7; qc | Conclusion first; exposure budget; early sign; difficult news once with what remains open |
| Source retrieval | SKILL step 6, kg.py, search.py | Cite only what retrieval confirms; mark inference and outside knowledge |
| System separation | consultation-reasoning §9, jaimini.md, lal-kitab-method.md | No mixed aspects or significators across schools |

## 3. What changed from v3.1 (and why)

The v3.1 answers were accurate but mechanical: one paragraph per placement, every route or trait justified by a single
placement, "Venus weak → caution/slowness" by default, a flat refusal to discuss the spouse's appearance, and timing
without an explicit precision budget. The research (the appendix below) showed that experienced
practitioners (a) restate and classify the question, (b) assign roles before meanings, (c) keep promise and
activation apart, (d) rank manifestations, (e) earn precision, and (f) lead with the judgement. v3.2 encodes those
steps. The measured effect is in `private/benchmark/COMPARISON.md` (blind side-by-side grading of the same 13
questions answered by v3.1 and v3.2).

## 4. Measured effect (blind, rubric-based)

Round 1 (13 questions): v3.2 won 11/13, 619 vs 564 — large gains in directness, prioritisation, voice, exposure and
usefulness; small regressions in timing logic, contradiction handling and accuracy, traced to unexplained sub-windows,
over-grading and loose precision. Rules added for each (consultation-reasoning §7; communication §1; qc). Round 2 (the
six affected questions): v3.2 won 6/6, 297 vs 248, with every dimension equal or better, including timing (+3),
contradictions (+2) and accuracy (+4). Details and caveats: `private/benchmark/COMPARISON.md` (private: uses the
user's own chart).

## 5. v3.4: from judgement to a life-first answer

Research into professional practice (`research/reports/SYNTHESIS.md`) and blind benchmarks showed the remaining
weakness was not the judgement but its telling: answers still opened sentences with "Your Mars…" or "The 10th lord…".
v3.4 adds a final translation step and three output modes:

- **Life unit**: theme → what it means → likely form → timing → nuance → counter-factor → what to watch; chart facts
  follow the life consequence in the same sentence or move to a technical section (communication.md §1a).
- **Modes**: A consultation (default), B deep consultation (reasoning shown after the answer, grouped by what each fact
  decides), C professional report (reports.md; Structured Report Model rendered to HTML/PDF).
- **Checks**: `life_lint.py` flags chart-first sentences, workbench words, citations and sub-period lists; qc.md adds
  the "cover-the-chart" test and requires calculated (not estimated) birth-time sensitivity.
- Measured effect: see TESTING.md (v3.4 benchmark).

## Appendix: how senior Vedic astrologers reason in consultations — research synthesis (2026-09-25)

Three research passes (Agent Reach: Exa web search, Jina page reader, YouTube transcripts via yt-dlp; plus the eight
library books), each rating its sources and extracting **reasoning patterns, not wording**.


Tags such as `[R1-P3]`, `[R2-TP1]`, `[R3-RP6]` in the skill point into these reports. Limits: Reddit was blocked
(snippets only, low weight); Hindi live readings could not be transcribed usefully; several books were read through
publisher pages or excerpts only. No personal chart data was sent in any query.

### A1. Who was studied and how they compare

| Practitioner / school | What they are good for | Caution |
|---|---|---|
| K. N. Rao & BVB disciples (Journal of Astrology) | Promise → dasha → transit stages; published hit/miss self-criticism; case studies with outcomes | Double-transit and other success figures have no chance baseline (critiques S9, S10) |
| Hart de Fouw & Robert Svoboda (*Light on Life*, in library) | Confluence, dridha/adridha karma, dispositor logic, "contradictions add up", objective vs subjective split | Case charts are famous lives read in hindsight |
| P. V. R. Narasimha Rao (free textbook) | Probability reasoning (P(A\|B) vs P(B\|A)), rectification method, precision budget from birth-time error, documented failure | Switched dasha variant after a failed call — the move he warns against |
| B. V. Raman (HJH2, HPA in library) | Fixed house–lord–karaka–Moon template; strength limits delay; paired chart comparisons | Some deterministic, gendered doctrine |
| Sanjay Rath / SJC, Visti Larsen | Clear arudha (A7/UL) framework; delay-vs-denial rule; getting vs staying married | Untested; examples chosen after outcomes |
| KP school (Paramarsh, Jagannath Hora) | Explicit significator logic for relationship levels (5-11, 2-7-11, 1-6-10-12) | A different system — never mix its rules into Parashari |
| Ernst Wilhelm, Ryan Kurczak | Dasha-lord "snapshot" across D9/D10; opposite yogas show in different sub-periods | Day-level claims tied to products |
| James Braha | Dominant-factor-first delivery; self-checking predictions; admits method limits | — |
| Sam Geppi, Kapiel Raaj | Live readings: context gathering, refusing one-placement questions | Remedies without checkable logic; after-the-fact reconstructions |
| Lal Kitab live readers | Ranked-year phrasing; "fewest remedies" ethic | Remedy inflation in the genre |
| Nadi (critic's field test vs practitioner's defence) | Shows what *fishing* looks like | No validation found |
| Joni Patry live stream | Anti-pattern: instant verdicts from one placement | — |
| Statistical tests (Narlikar et al.; Skeptical Inquirer 2022) | Single-rule claims show no effect; blind judges near chance | Tests single rules, not full synthesis — but single rules therefore carry little weight |

### A2. Principles shared by the better practitioners (now built into the skill)

1. **Question first.** Restate the question in answerable form; fix the event level (dating ≠ marriage, travel ≠
   settling); gather context and chronology; still scan the whole period for anything serious [R1-P9; R3-CP1].
2. **Promise, then period, then transit** — whether/what kind, which years, which months. A later stage never creates
   what an earlier one lacks [R1-P1].
3. **Promise has classes**: promised, delayed, modified (form/place/cost), weakly supported, not supported; "denied"
   needs several independent afflicted channels and no rescuer [R1-P2].
4. **Primary / secondary / supporting**: house + lord + karaka, the dasha lord's condition and link, the relevant
   varga set direction; dispositor, the right strength measure and period-active yogas set degree; nakshatra, argala,
   fast transits, Ashtakavarga add texture only [R1-P3].
5. **Lordship → event, nature → experience** (de Fouw; Mantreswara) [R1-P3].
6. **One negative factor has several readings** (delay, quality, dynamics, attraction, setting, intention) — keep the
   one another independent factor supports; mind base rates of common placements [R1-P5].
7. **Contradictions add up**, surfacing in different sub-periods or levels; assign what each factor controls
   [R1-P4; LOL p279, p342].
8. **Independent convergence**: count channels, not factors; discount near-always-true conditions (double transit,
   OR-bundles) [R1-P8; R2-TP9].
9. **Precision is earned**: birth-time error sets how many dasha levels are usable (dates shift ≈ n × m ÷ 4 days);
   windows before months; never days [R2-TP1, TP13].
10. **Scenario thinking**: an activation is a class of events; rank concrete manifestations [R3-RP4, RP5; LOL p308–309].
11. **Past events calibrate, not prove**; fix methods before checking; ask discriminating questions, don't fish
    [R1-P10, P11; R3-CP2].
12. **Delivery**: dominant factor first; answer → why → the counter-weight → an early sign to watch → at most one question
    back; machinery hidden unless wanted; difficult news stated once, with what remains open [R3-EP1–EP4].

### A3. School-specific methods (kept in their own notes)

KP significator logic; Jaimini/SJC arudhas (A7, UL, 2nd from UL), Darakaraka, chara/Narayana dasha; Tajika annual
charts; Lal Kitab varshaphal; Nadi rules. Agreement **across** schools is reported as convergence; rules from one
school never satisfy another school's conditions [R1-P13; R2-TP11–TP12].

### A4. Unsupported or overclaimed (the skill treats these as supporting at most, or not at all)

Double transit as a necessary/sufficient trigger; OR-stacked timing rules; switching dasha variants after the event;
denial rulings from famous-person charts; single-affliction rules; "research" without a chance baseline; higher vargas
used both to rectify and to predict; sookshma-level event dates; transit-only sun/moon-sign forecasts; fear-and-remedy
selling; detailed physical-appearance prediction; a method for "who approaches first" (none found).

### A5. Methods worth testing later (logged forecasts, fixed in advance)

The precision-budget rule; Raman's relevance tiers for dasha pairs; the D9/D10 dasha snapshot for open questions;
meeting vs commitment windows; KP 5-7-11 vs 2-7-11 for relationship level (as a separate-system note); "continuation
when MD and AD lords point different ways".

### A6. Where each finding lives in the skill

| Finding | Skill file |
|---|---|
| Workbench vs answer, question classes, roles, promise classes, scenarios, what-controls-what, confidence, calibration | `references/consultation-reasoning.md` |
| Decision trees per question family (relationship levels, marriage, meeting/initiative, spouse and appearance, career, money, travel/relocation, open activation, past periods) | `references/question-trees.md` |
| Timing ladder and precision budget, 30-day questions | `references/timing.md` §0 |
| Relationship levels, meeting vs marriage, ex/new person, appearance as themes and ranges | `references/topic-relationships-marriage.md` §1, §5, §6 |
| Answer order, early sign to watch, difficult news, questions back, anti-patterns | `references/communication.md` §1, §6a, §6b, §7 |
| Checks | `references/qc.md` (consultation-shape items) |
