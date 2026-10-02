# Testing

Five kinds of test, from arithmetic to judgement. Everything that can run without personal data runs in CI; blind
benchmarks use the owner's chart and stay private (only their scores are published).

## 1. Calculation

| Test | What it proves | Where |
|---|---|---|
| Property tests (Hypothesis) | sign/nakshatra/pada follow from longitude at every value incl. exact boundaries; varga identities; Vimshottari structure (order, first lord, 120-year total, contiguous sub-periods); time-zone conversion is only a shift; the ascendant moves forward with time; leap days and midnight; nodes opposite | `tests/test_calc_properties.py` |
| Reference values | Lahiri ayanamsa 23°51′ at J2000; tropical Sun 280.37° at J2000 | `tests/test_reference.py` |
| Independent engine | local vs VedAstro on the synthetic chart S1: positions within tolerance, no sign/nakshatra/pada flips, only documented method differences | `tests/test_reference.py`, fixtures from VedAstro with synthetic data |
| Schema | inconsistent facts are rejected; validated facts round-trip | same |
| Sensitivity and contacts | the reported minutes really flip the ascendant; reported contact dates are exact conjunctions | same |
| Strength and Jaimini (v3.5) | Raman's published 1918 drik bala reproduced (±0.02); Ashtakavarga totals 48/49/39/54/56/52/39 = 337 for any chart; Shadbala component ranges; circular cheshta mean across 0° Aries; BPHS war victor; karaka/arudha properties; S1 sensitivity classes | `tests/test_strength.py`, `tests/reference_charts/` |
| Interfaces and security (v3.5) | service results equal the engine's; input validation; `skill://` traversal and code reads refused; live VedAstro refused in private mode; data-folder confinement; report-name sanitising; consent-gated, owner-only prediction log; REST endpoints, OpenAPI and bearer token; remote binding refused without a token (MCP and REST); MCP stdio round trip with a generic client; CLI; tampered ephemeris download rejected | `tests/test_service.py` |

Result (2026-09-27): **22/22 pass**. First-run finding: exact-boundary floating-point error (fixed; no real chart changed).
Result (2026-10-02, v3.5): **54/54 pass** locally (Swiss Ephemeris files) and in a clean install from the exported
repository (Moshier fallback). Manual: MCP over Streamable HTTP with and without a token; REST under uvicorn (empty
server log); `install.sh` with a sandboxed home folder.

## 2. Knowledge

`validation/graph_checks.py` (27 checks incl. every book's SHA-256), `validation/retrieval_eval.py` (gold-page recall,
16/17 questions), `validation/citation_test.py` (20 sampled rules per book, cited page contains the rule's words:
19–20/20), `tools/kg/validate_map.py` (every source-map part before promotion). Docling benchmark:
`validation/docling/README.md`.

## 3. Skill self-tests and behaviour

`chart_facts.py --selftest`, `varshaphal.py --selftest` (120 rows, worked examples), `vocab.py` (180 entities),
`life_lint.py --selftest`, `render_report.py --selftest`. Behavioural regression cases with criteria fixed before
outputs existed: `skill/…/tests/test-cases.md` (22 cases; v3.3 regression subset 8/8).

## 4. Blind consultation benchmarks

Method (since v3.2, aligned with Anthropic Skill Creator's blind comparator in v3.4): the same questions and
calculated data go to fresh agents, one set per version, each following its own skill files; method traces are
stripped; each pair gets random X/Y labels (key kept apart); a separate grader scores 12 dimensions (directness,
synthesis, prioritisation, timing, contradictions, scenarios, confidence, voice, life-first, restraint, accuracy,
usefulness) plus report dimensions and per-question expectations, checking facts against the data files. Results go
into the SQLite benchmark database (`tools/bench_db.py`).

| Round | Comparison | Result |
|---|---|---|
| 1 | v3.1 → v3.2 (13 q) | v3.2 11/13, 619–564 |
| 2 | v3.1 → v3.2 after fixes (6 q) | v3.2 6/6, 297–248 |
| 3 | v3.2 → v3.3 checkpoint (8 q) | parity 384–382 → three fixes |
| live | v3.1 answer → v3.3 on fresh calculation (4 q) | v3.3 4/4, 184–136 |
| 5 | v3.2 → v3.3 final (13 q) | v3.3 8 / 3 / 2 ties, 662–645; citation regression found |
| 6 | v3.2 → v3.3 after fix (5 q) | v3.3 4/5, 240–227 |
| 7 | v3.3 → v3.4-dev (28 q, 25 categories + deep mode + 2 reports) | v3.4 22/28, 1543–1424 |
| 8 | v3.3 → v3.4 after fixes (C04, C15, C23, R02) | v3.4 3/4, 224–217; expectations 31/31 vs 30/31 |
| 9 | v3.4 → v3.5 on a new synthetic chart S2: all 8 report types + 4 consultations | v3.5 7/12, 764–757 (parity); expectations 124 vs 123 of 134 |
| 9 | v3.3 → v3.5 subset (2 reports, 2 consultations) | v3.5 3/4, 233–227 |

## 5. v3.4 benchmark (round 7)

**Round 7 (2026-09-27), v3.3 vs v3.4-dev, 28 questions**: 25 consultation categories (career, finance, education,
relationships, marriage, parents, siblings, property, children, health/wellbeing, relocation, foreign travel,
friendships, spiritual growth, current dasha, unexpected events, next 30 days, next 3 months, next year, retrospective,
weak evidence, contradictions, engine disagreement, birth-time sensitivity, unclear timing), one deep consultation and
two full reports; three charts (the owner's, fictional B, synthetic S1); two blind graders, 14 questions each.

**v3.4 won 22 of 28, 1543 vs 1424** (without R01, see caveat: 1474 vs 1361). Expectations passed: v3.3 203/212,
v3.4 206/212.

| Dimension (28 q) | v3.3 | v3.4 | Δ |
|---|---|---|---|
| life-first | 101 | 129 | +28 |
| restraint (no chart dump, no unasked citations) | 101 | 123 | +22 |
| voice | 114 | 134 | +20 |
| synthesis | 118 | 130 | +12 |
| usefulness | 116 | 127 | +11 |
| prioritisation | 114 | 122 | +8 |
| accuracy | 130 | 137 | +7 |
| confidence | 128 | 131 | +3 |
| timing / contradictions / scenarios | 113 / 116 / 107 | 115 / 118 / 109 | +2 each |
| directness | 139 | 138 | −1 |
| report structure (2 reports) | 7 | 10 | +3 |

Strongest gains: relocation (+10), unexpected events (+11), next year (+10), property (+8), birth-time sensitivity (+8,
v3.4 gave the calculated margin, v3.3 "very roughly ten minutes"), parents (+7), both reports (+6 each).
v3.3 won six questions, each by 1–2 points: relationships (C04, tied on points), health (C10), spiritual growth
(C14), fame (C21), engine disagreement (C23), unclear timing (C25).

Faults found in v3.4 and fixed after the round: a claimed JHora agreement for a chart JHora was never run on (C23);
the current sub-period not named when the question was about it (C15); a report "Sources" block citing the skill's
own files (R02); "again" for a transit contact with no earlier pass in the data, and relationship vs marriage windows
not separated (C04); Lal Kitab asides that did not change the answer. Also: benchmark answerers had to estimate
birth-time margins and transit-contact dates → the engine now outputs both.

**Caveat (R01):** the skill's bundled worked example is a career report on the same synthetic chart the R01 question
used, so v3.4 had an advantage there that v3.3 did not; R01 is included in the table and the 22/28, and excluded from
the alternative total (1474 vs 1361). Rule adopted: benchmark charts must differ from charts used in skill examples.

**Round 8 (2026-10-01), re-test after the fixes** — C04, C15, C23, R02; fresh answerers; engine data now including
birth-time sensitivity and slow-planet contacts for both versions; one blind grader. **v3.4 won 3/4, 224 vs 217**;
expectations v3.4 31/31, v3.3 30/31. C15 and C23 (lost in round 7) were won; C23 used the calculated 14-minute margin
and convention-independent contact dates. C04 tied on points (51–51) and went to v3.3 on judgement; v3.4's answer had
no factual errors (v3.3's mislabelled a sub-sub-period as a sub-period). Remaining v3.4 observations: the 12-month
report is long and its appendix lists page references (by design — appendix only); one loose phrase ("Jupiter rules the
learning side" for a planet that occupies, not rules, the 5th).

**Regression subset (T02, T07, T09, T12, T15, T16, T17, T21): 8/8 Pass** (`tests/results/GRADING.md`).

**Decision: promote v3.4** — better overall in the broad benchmark and the re-test, no category regressed beyond a
point, regression unchanged.


## 5a. v3.5 benchmark (round 9, 2026-10-02)

New synthetic chart **S2** (invented; not used in any skill example; kept private until the round ended), data from the
v3.5 local engine (Shadbala, Ashtakavarga, Jaimini, sensitivity grid included). Answerers ran one at a time; four blind
graders. All eight report types (career, relationship, marriage, dasha, 12-month, relocation, complete life, compact)
plus consultations on birth-time sensitivity, strength, timing across engines and career.

| Set | v3.4 | v3.5 |
|---|---|---|
| Reports R1–R8 | 4 wins, 541 | 4 wins, 552 |
| Consultations C1–C4 | 1 win, 216 | 3 wins, 212 |
| Total | 5 wins, 757 | 7 wins, 764 |

**Reading:** parity at the reasoning level, as expected — v3.4 and v3.5 differ in three engine-guidance files; v3.5's
gains are in calculation and interfaces. Versus v3.3 (subset): v3.5 3/4, 233–227.

**Findings acted on:** a complete-life answer gave a parenthood age and a "window for children" (same safety text in
both versions; the topic file taught child-timing rules) → topic-file output rule, QC check, and a negation-aware SAFETY
check in `life_lint.py` that blocks report rendering (scan of all 24 round-9 answers: only the three real lines
flagged); an answer called a Shadbala ratio of 0.99 "just reaching" the minimum → inputs.md wording; the engine's
required Shadbala for the Sun was 5 rupas instead of BPHS's 6.5 (found by an answerer) → fixed and tested; "one-page"
compact reports rendered at 5–7 pages → compact layout and word guidance; a browser-only cover overlap → fixed.
**Limits:** the private-chart items (P1–P3) were not run — the environment's safety classifier blocked the answerers
from the personal chart folder; the generic expectation "no Sources block" mis-scores reports, whose appendix carries
sources by design; one v3.5 answerer could not re-run two scripts.

**Regression subset (T02, T05, T07, T09, T12, T15, T16, T17, T21) on the final candidate: 9/9 Pass.**
**Final validation phase (2026-10-03).** Relationship/marriage re-tests on S2 (blind, vs the original v3.4
answers): after the ladder/Main-windows/plain-name fixes v3.4 still won both (137–128); diagnosis (preamble before the
answer, Shadbala lowering a grade, overlapping windows) → three rule fixes → v3.5 won both by one point (141–139),
i.e. parity. Edge-case reference suite (22 synthetic charts; PyJHora 20/20 agree); offline run with network denied;
clean install from a fresh clone (doctor 0 WARN/FAIL, 85/85); seven children/parenthood prompts; private-chart
tests in the main session (not blind; see the private evaluation). Automated tests: **85/85**.

**Decision: promote v3.5** — new capability, reasoning at parity with v3.4, ahead of v3.3, regression clean.


Gitleaks over full history → privacy check → Ruff → calculation tests → skill self-tests → report rendering with
WeasyPrint → package check. Synthetic data only; no books, graph or personal data exist in the repository.
