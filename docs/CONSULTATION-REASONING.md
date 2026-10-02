# Consultation reasoning architecture (skill v3.2, extended in v3.4)

v3.2 adds a reasoning layer on top of the v3.1 knowledge system. Nothing below replaces the calculation inputs, the
books, the Graphify knowledge graph, provenance, the contradiction register, or the Jaimini/Lal Kitab separation.

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
without an explicit precision budget. The research (docs/ASTROLOGER-CONSULTATION-RESEARCH.md) showed that experienced
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
