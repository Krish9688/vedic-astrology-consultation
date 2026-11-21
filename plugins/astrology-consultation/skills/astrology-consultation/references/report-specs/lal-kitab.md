# Lal Kitab report spec (`lal-kitab`)

The Lal Kitab reading of one chart on its own terms: the Lal Kitab chart, its houses, the debt (rin) signatures with
pitri rin, and remedies only when the person asks. Lal Kitab is its own system ([lal-kitab-method.md](../lal-kitab-method.md)):
this report has its own sections and drop list, and no Parashari reading appears in it, as no Lal Kitab reading appears
in the Parashari reports ([README.md](README.md) §5). Pitra Dosha has no report of its own: the Lal Kitab pitri rin is
read here (owner decision 2, 2026-11-20); the Parashari "Pitra dosha" stays "not assessed" (no classical definition).

**Order (standard):** `lk-chart` → `lk-houses` → `lk-rin`

Inputs: `birth`. Model: `report_type: "lal-kitab"`, `depth: "standard"`, the frame fields. Required sentence in `scope`:
"This is a Lal Kitab reading, kept apart from the Parashari reports: its houses, debts and remedies are Lal Kitab's
own." Every unit has `system: "lal_kitab"` and an `edition` (`shrimali`, `lk1952` or `both`), and every section id
starts with `lk-` (REPORT-STANDARD §7). No timeline rows: no dasha is used, and Lal Kitab timing (maturity ages, the
35-year cycle) is said in words. `ranking` is optional (rows per house or per rin signature).

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `lk-chart` | the Lal Kitab chart: each planet's house (house N = Kalpurush sign N, signs dropped), empty houses, the sleeping houses and their awakeners, the clash (takraav) pairs; which edition says what where they differ | the Lal Kitab block of `prepare_consultation` (`chart_facts.py` with `scripts/lal_kitab.py`: house map, sleeping houses, takraav line); the lagna → `calculate_birth_chart` |
| `lk-houses` | the occupied houses read by the house before the planet: pakka ghar, Lal Kitab exaltation and debilitation, friends and enemies in the house, sleeping planets, dharmi or sinful; one unit per house that answers the person's question, each tied to its flags, the editions kept apart | the per-planet flags in the Lal Kitab block of `prepare_consultation` |
| `lk-rin` | the debt (rin) signatures, both editions shown separately, with one unit for pitri rin (Jupiter's houses 2, 5, 9, 12 holding the listed planets); said as traditional family symbolism from the birth chart only. No debt is named: the gate is not evaluated. The section text carries the sentence "A rin (debt) here is traditional family symbolism read from the birth chart only: it names no debt, blames no one and is not a curse." Every rin unit is graded Weak, Contradictory or Unknown | the rin line of the Lal Kitab block of `prepare_consultation` (`lal_kitab.rin_line`: LK1952 p146-150 and KB B12 rows, Mercury in the root, the gate facts) |


Remedies: only when the person asked (`remedies_requested: true`), as remedy cards in `remedies` (planet, Lal Kitab
house, remedy, safety class, safe form for a caution item, source), never inside a section. The shared remedy rule
applies ([remedy-safety.md](../remedy-safety.md)): the gate in §1, the never-recommend and caution lists in §2, no gems
and no costly rituals or payments, and the "no efficacy established" line, which the renderer prints on every card.
Sensitivity of every unit: `get_birth_time_sensitivity` (every Lal Kitab house is counted from the lagna).

`spec_checks` (`lk_errors`) refuses: the scope without its sentence; a section outside this list; a unit that is not a
Lal Kitab unit; timeline rows; an unknown birth time; an `lk-rin` section without its sentence, without a pitri rin unit,
or with a rin unit graded Moderate or Strong. The type gate refuses fear framing and gems or costly rituals; the shared
lists refuse medical and death words and the never-recommend remedies everywhere in the report.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| The chart: each planet keeps its house, signs dropped, house 1 = Aries | KB B2 (Shrimali); lal-kitab-method.md §2 |
| Judge the house before the planet; then pairs and sequence | LK1952 p867-870; lal-kitab-method.md §3 |
| Pakka ghar, exaltation and debilitation, sleeping planets, dharmi and sinful states | KB B7 (Shrimali; pages 40-44 as the KB gives them); LK1952 p117-119 (sleep test), as `lal_kitab.py` prints them |
| Clash (takraav): house N with house N+7, the clash on house 9 helpful; never a "sudden blow" | LK1952 p132-133 |
| Rin signatures from the birth chart only, both editions apart; no debt named (the p150 gate does not say all or any) | LK1952 p144-150; LKS p164-174 (KB B12) |
| Pitri rin: the listed planets in Jupiter's houses 2, 5, 9, 12 | LK1952 p146-150; LKS p164-174 |
| Fixed and changeable results (whether a remedy applies), the editions disagreeing | LK1952 p59-60; KB B7 (page 47 as the KB gives it; CR-L01) |
| Reassure rather than frighten; the author says his calculations may be wrong | LK1952 p1182 |

Cite LK1952 and LKS in `appendix.sources` with the catalog id first ("LK1952: Lal Kitab 1952, p146-150"). KB section
codes are provenance notes for the private knowledge base, not sources: without the knowledge base installed, cite only
the book pages the reference files give (lal-kitab-method.md, top).

## 3. Conventions

Whole-sign houses from the lagna sign (the KB default); a bhava map only when the person supplies one, said so. Both
editions are printed where they differ, and neither is chosen (CR-L01 to CR-L27). Grades: a single rule without
confirmation is Weak; a house whose occupant and helper houses agree is at most Moderate in this report.

## 4. Caveats

- Lal Kitab only: no Parashari rule, dasha, varga or yoga in this report; a Parashari question goes to its own report.
- Family symbolism, never blame: the book often sends a planet's result to a relative; say it as a family theme, never
  as a forecast about a person, and never a relative's illness or death (the shared list refuses those words).
- No fear framing and no curse (`_FEAR`): a rin is not a curse and a clash is a relation, not a blow.
- Remedies only on request, under the shared remedy rule; none in the sections; no gems, no costly rituals.

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | every unit carries `sensitivity`; drop a section whose lagna class is `high` or `very high` (every house would move) |
| unknown time | no Lal Kitab report: every section rests on the houses counted from the lagna; ask for the time |
| any time | a named debt (the gate is not evaluated); house delineations beyond what the reference files state; remedies not asked for |
