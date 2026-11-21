# Raj Yoga report spec (`raj-yoga`)

The kendra-kona combinations the engine names in the birth chart, what the sources dispute about each, and when the
periods of their planets run. Inside the shared frame ([README.md](README.md)). A raja yoga is a combination, never a
promise: it shows a result only where the strength of its planets and the running period agree (HJH2 p288: yogas raise
the degree of success; they do not show the type of work). No promise of fame, wealth, rank or certainty.

**Order (standard):** `windows` → `lines` → `strength`

Inputs: `birth`. Model: `report_type: "raj-yoga"`, `depth: "standard"`, the frame fields. `ranking` rows (`item`,
`support`, `why`, `window`, `caution`) rank the lines by how much agrees; nothing is graded Strong. Required sentence in
`scope`: "A yoga is a combination in the chart, not a promise: it shows a result only where the strength of its
planets and the running period agree."

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | the periods of the lines' planets (major and sub-period) as timeline rows: `window` rows only where the period of a line's planet runs (basis names the running dasha), else `chapter` rows | Vimshottari → `get_dasha` |
| `lines` | one unit per engine line, in this order: yogakaraka (`RAJA-YK-*`), then the kendra-kona lord relations (`RAJA-KK-*`), then lords placed in an angle or a trine (`RAJA-KKP-*`). Each says which lords, which houses they own, how they relate, and where the sources dispute it. The section text states the base rate in words | `prepare_consultation` (`F.yoga.RAJA-YK-*`, `RAJA-KK-*`, `RAJA-KKP-*`: holds and detail); houses and lords → `calculate_birth_chart` |
| `strength` | what weighs a line: the planets' strength (Shadbala ratio), dignity, affliction; the lagna lord; why a common configuration carries little weight alone | `get_shadbala` (total, required, ratio); `calculate_birth_chart` |

Sensitivity for every unit and window: `get_birth_time_sensitivity`.

### The yogakaraka line (added 2026-11-20, T11.35)

`chart_facts.candidates()` prints `RAJA-YK-<planet>` when one planet owns both an angle (4th, 7th or 10th) and a trine
(5th or 9th) from the lagna: Saturn for Taurus and Libra, Mars for Cancer and Leo, Venus for Capricorn and Aquarius (PDK
p191, note to v. 47). It is membership by lordship only; CRUX p27 reads it as an indication, not as the yoga itself.

### Dual lordship (CR-V22, owner decision 14)

When a lord in a line also owns a 6th, 8th or 12th, the engine detail says "DISPUTED". The unit then shows both readings
side by side, never one: BPHS 34.14-15 gives no yoga by the relation alone and the moolatrikona sign decides which lordship
shows (not page-checked); the Phaladeepika translator's note gives yoga even so (PDK p191, v. 45: lords of kendras and
trikonas become yogakarakas by their mere relationship, even with a 6th, 8th or 12th lordship). The unit carries
`claim_basis: DISPUTED`, is graded Weak or Contradictory, and its `rule_refs` name both BPHS and PD. `spec_checks`
refuses a dual-lordship unit without these; it reads the dual lordship from the engine's lordships (`F.<p>.owns`) when
create_report passes the facts, else from the lordships the unit states ("owns the 6th and the 7th", "owns H6,7").

Base rates (engine, 4,000 random charts, the bare condition): some kendra-kona lord relation about 68 in 100 charts (about
2 in 3: the plan's figure is confirmed by the engine), a lord placed in an angle or trine about 61 in 100, a yogakaraka
about 51 in 100. A high rate means the bare condition carries little weight on its own (yoga-definitions.md). Write them
in words, never a percentage sign.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Kendra and kona lords related by exchange, by joining or by mutual opposition make a raja yoga; a lord of a dusthana as well gives none by relation alone (dispute) | BPHS ch. 34 sl. 11-15 (source map BPHS_part3.md, not page-checked) |
| Lords of kendras and trikonas become yogakarakas by mere relationship, even with a 6th, 8th or 12th lordship | PDK p191 (v. 45) |
| One planet owning a kendra and a trikona is the yogakaraka of that lagna; its mere existence indicates a possibility, not the yoga | PDK p191; CRUX p27; HJH1 p20 |
| Dashas of kendra and trikona lords in association are favourable | BPHS p584 |
| Yogas raise the degree of success; they do not show the type of work | HJH2 p288 |
| A yoga acts in the periods of its planets, scaled by their strength | BPHS p504, p299 (kundli.md §3) |

Cite them in `appendix.sources` as "PDK: Mantreswara, tr. G. S. Kapoor, *Phaladeepika*, p191" and in unit `rule_refs`
as "PDK p191".

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. A yoga name is shorthand for its parts, not more evidence
(kundli.md §4). Lines the engine does not print are not invented: the Parashara permutations and Jaimini raja yogas are
not computed here and are not named (not checked).

## 4. Caveats

- No promise of fame, wealth, rank, office or certainty ("will become", "destined", "guaranteed"): `spec_checks` refuses
  them unless a negation excuses the clause ("not a promise of fame").
- No fear framing (batch 4 gate reused); no illness or death words (shared list).
- Nothing is graded Strong: the lines are common (about 2 in 3 charts have a lord relation), so the bare condition is Weak
  or Moderate; a line graded Moderate names the strength and the period that agree.
- A dual-lordship line is a dispute, shown with both readings.
- Parashari only: no Lal Kitab, no remedies section ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | every unit carries `sensitivity` (lords and houses need the lagna); drop `windows` rows whose period boundary shifts by months |
| unknown time | drop `windows`, `lines` and `strength` (the lines count lords and houses); at most labelled monthly markers; one house-free `note` section stays |
| any time | the Parashara permutations and Jaimini raja yogas (not computed) |
