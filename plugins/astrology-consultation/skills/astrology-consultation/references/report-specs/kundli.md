# Kundli report spec (`kundli`)

The birth chart explained: who the person is, where the strengths lie, the yogas and the period now. Two depths:
**standard** (a few pages) and **full**, which follows the owner's 21-section master template. The complete-life report
stays the story report; the kundli is the chart-by-life-area report. Shared frame, confidence scheme, birth-time rules,
QC checks and tone: [README.md](README.md).

**Order (standard):** `foundation` → `windows` → `self` → `strengths` → `current`

**Order (full):** `foundation` → `windows` → `self` → `career` → `relationship` → `partner` → `intimacy` → `wealth` →
`family` → `friends` → `education` → `home` → `travel` → `inner` → `challenges` → `remedies`

Inputs: `birth` (date, time, place, `time_reliability`). Model: `report_type: "kundli"`, `depth`, the frame fields,
`ranking` as the snapshot by life area (master section 2).

## 1. How the 21-section master maps to the model

| Master | Model |
|---|---|
| 1 Read this first | `scope`, `confidence_note`, how-to-read and legend |
| 2 Snapshot | `ranking`: one row per life-area section present, `item` = the section title (checked) (`item`, `support`, `why`, `window` best window, `caution`), printed under the short version |
| 3 Chart foundation (calculated facts) | section `foundation` (fact units) + appendix positions, rasi chart, periods |
| 4-17 life areas | sections `self` … `challenges` (full depth) |
| 18 Master timeline | section `windows` (named once, first in the body) + `timeline` (drawn after the sections) |
| 19 Remedies and actions | `practical_summary` (practical actions first); section `remedies` only if remedies were asked for, via remedy-safety.md, otherwise dropped. Full depth counts as that request (and the request for `intimacy`); the model records it as `remedies_requested: true`. Every `remedies` unit says "no efficacy established" (checked) |
| 20 Evidence ledger | rendered from the units' `claim_type` |
| 21 Open questions | `next_step` |

## 2. Sections and computed fields

Every number comes from the tool named; the writer interprets it. "F.*" ids are the derived facts of
`prepare_consultation` (`derived_fact_ids`, from `chart_facts.py`).

| Section | Content (owner template) | Computed fields → engine tool |
|---|---|---|
| `foundation` | the planet table in words: lagna, Moon sign and nakshatra, the strongest and weakest planets; in full depth also one yoga unit (the yogas the engine names, each with what it does in life); one Kaal Sarp unit when the engine reports the strict pattern (§2a) | positions, nakshatra, houses → `calculate_birth_chart`; strength → `get_shadbala` (total, required, ratio); `get_ashtakavarga` (SAV by house); yogas → `prepare_consultation` (F.yoga.*) |
| `windows` | three to five named windows, each with dates, a one-line basis and what it activates | Vimshottari MD/AD → `get_dasha`; ingresses and slow contacts → `get_transits`; Yogini as a second view → `get_yogini_dasha` (optional) |
| `self` | core self (T18a, T9): identity, mind, the soul lesson, recurring patterns | lagna and lord, Sun, Moon → `calculate_birth_chart`; Atmakaraka → `get_jaimini_factors` |
| `strengths` (standard) | strengths and yogas, each with what it does in life | yogas, dosha checks → `prepare_consultation` (F.yoga.*); Shadbala ratio → `get_shadbala` |
| `current` (standard) | the running period in life terms; what is changing | MD/AD/PD → `get_dasha`; Sade sati phase → `get_outlook` or `get_gochara` |
| `career` | T1 in short; points to the career report | 10th house, lord, 10th from Moon → `calculate_birth_chart`; D10 → `get_divisional_chart` (10); Amatyakaraka → `get_jaimini_factors` |
| `relationship` | T2 in short | 7th house, lord, Venus → `calculate_birth_chart`; D9 → `get_divisional_chart` (9) |
| `partner` | partner as tendencies (T3, trimmed): nature, background, how you meet; appearance and age graded Weak | Darakaraka, Upapada → `get_jaimini_factors`; 7th lord, D9 7th → as above |
| `intimacy` | T18b, tendency-level only | Mars, Venus, 8th house → `calculate_birth_chart` |
| `wealth` | T4: income model, saving pattern, risk | 2nd, 11th, 5th, 9th, 8th → `calculate_birth_chart`; SAV for those houses → `get_ashtakavarga` |
| `family` | T6 | 4th, 3rd, 2nd, Sun, Moon → `calculate_birth_chart` |
| `friends` | T7 (+ hobbies, T13) | 11th, 3rd, 5th → `calculate_birth_chart` |
| `education` | T8 | 4th, 5th, 9th, Mercury, Jupiter → `calculate_birth_chart`; D24 → `get_divisional_chart` (24) |
| `home` | T10 | 4th, lord, Mars, Saturn → `calculate_birth_chart`; D4 → `get_divisional_chart` (4) |
| `travel` | T11 + T18c (unconventional and foreign openings, ranked by type) | 3rd, 9th, 12th, Rahu-Ketu axis → `calculate_birth_chart`; slow transits → `get_transits` |
| `inner` | T12 + T14: inner life and public image | 9th, 12th, Ketu, 10th → `calculate_birth_chart`; D20 → `get_divisional_chart` (20) |
| `challenges` | T15 + T18e: top challenges and opportunities, each with its window by name | 6th, 8th, 12th, weak planets → `calculate_birth_chart`, `get_shadbala` |
| `remedies` | T17, only on request; Parashari only (no Lal Kitab, see README §5) | none computed; remedy-safety.md and the books |

### 2a. Kaal Sarp (folded into the Kundli, owner decision 9, 2026-11-20)

There is no standalone Kaal Sarp report. When the engine reports the strict pattern (`DOSHA.kala_sarpa` from
`prepare_consultation`: all seven planets from the Sun to Saturn on one side of the Rahu-Ketu axis by longitude), one unit
in `foundation` says so; when it does not occur, nothing is written unless the person asked, and then one fact unit says
the strict pattern does not occur. The unit:

- names the **strict form** only (all seven planets on one side by longitude, nothing looser; the direction types and the
  "near" forms are not computed and not named);
- names the **axis houses**: the houses Rahu and Ketu occupy from the lagna (`calculate_birth_chart`);
- says its **modern status plainly**, in the sentence "Kaal Sarp is a modern combination: no classical text in this
  library names it, its effect is not agreed and no cancellation is known." (LOL p331-332: not mentioned in any
  classical work; the Dravidian treatises disagree on its effect and on its formation). The report never repeats the
  sources' dire effects and reads no effect from the pattern;
- is a fact unit for the pattern and, if interpreted, an interpretation unit graded Weak on every line;
- never appears in the summary, ranking, timeline, watch list or practical lines (the engine shows it "for completeness,
  not used as evidence"), and has no fear framing (the batch 4 wording gate runs on it).

`spec_checks` enforces the sentence, the words "strict" and "axis", the Weak grade, the gate and the rows rule.

Every section's dates refer to a window by its name in `windows`; a section adds only what is specific to its area.
Birth-time sensitivity for every unit and window: `get_birth_time_sensitivity`.

## 3. Method rules and their sources

| Rule | Source |
|---|---|
| Each divisional chart has its own subject: spouse from the navamsa, power and position from the dasamsa | BPHS p104 |
| A planet with its required Shadbala works in the native's favour | BPHS p299 |
| Vimshottari periods total 120 years; the running period sets the chapter | BPHS p504 |
| Dashas of kendra and trikona lords in association are favourable (raja yoga periods) | BPHS p584; PVR p146 ("Dharma-Karmadhipati") |
| The strength of the lagna and its lord is "very important" in any chart | PVR p191 |
| Chara karakas: Atmakaraka the highest longitude, Amatyakaraka the second, Darakaraka the least | JSR p292, p295 |
| Yogas raise the degree of success; they do not show the type of work | HJH2 p288 |
| Ashtakavarga bindus weigh a transit | HPA p134; PVR p343 |
| Kaal Sarp (all seven planets on one side of the nodes) is in no classical work; no agreed effect, formation or cancellation | LOL p331-332 |
| One timing framework; windows named once; snapshot under the short version | the skill's own rule (reports.md §2, owner) |

Cite them in `appendix.sources` as "BPHS: Parasara, tr. R. Santhanam, *Brihat Parasara Hora Sastra*, p104", and in
unit `rule_refs` as "BPHS p104".

## 4. Conventions

Lahiri ayanamsa, whole-sign houses, mean nodes, sidereal year for dashas (the engine defaults; the cover names them).
Houses from the lagna, repeated from the Moon where the spec says so. Yogas only as the engine names them; a yoga name
is shorthand for its parts, not more evidence.

## 5. Caveats

- Partner section: the archetype caveat is printed by the template; looks and age graded Weak.
- Intimacy: tendency-level, tasteful; full depth counts as asking for it; at standard depth drop it unless asked or the chart says something specific.
- Affairs: the person's own tendencies only, never a verdict on a partner.
- Remedies: practical actions first; traditional remedies optional and only on request (full depth is that request); each remedy unit carries "no efficacy established".
- Kaal Sarp: one strict-form unit in `foundation`, its modern status said plainly, no fear framing (§2a).
- No gemstones, lucky numbers or percentages.

## 6. What to drop

| Data | Drop |
|---|---|
| approximate time | sections whose key factor `get_birth_time_sensitivity` classes `high` or `very high` (often `partner`, `career` D10, `education` D24, `inner` D20); D4, D20, D24 are dropped by default unless the class is robust |
| unknown time | the Kaal Sarp unit is dropped (its axis houses need the lagna); `foundation` keeps planets by sign only, and the Moon's sign and nakshatra only when they are the same across the whole birth day (else dropped with that reason); `windows` becomes labelled monthly markers of slow planets to time-independent natal planets; drop `career`, `relationship`, `partner`, `wealth`, `home`, `education`, `inner`, `challenges`, `current` (all house- or dasha-based); keep `self` from planets by sign (the Moon only under the same rule) |
| any time | intimacy and remedies unless asked (full depth counts as asked); any field with no engine tool (below) |

Not calculated, so dropped and named: the partner's height range, build and age gap (no computation exists; the
partner section gives tendencies only); a numeric "life score" or any index; Ashtakoota points (match report).
