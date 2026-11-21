# Couples match report spec (`match`)

Two charts compared under what the engine computes: four kootas with their exception conditions, the Prasna Marga
ch. XXI sign and star counts, Mars in each chart under the four Mangal rules, and how the two charts fit, as
tendencies. Inside the shared frame ([README.md](README.md)), with a two-person model. It never gives a verdict to
marry or not, never adds the kootas up and never uses fear framing (owner decisions 3 and 10, 2026-11-20).

**Order (standard):** `kootas` → `counts` → `mangal` → `fit`

Model: `report_type: "match"`, `depth: "standard"`, the frame fields, and:

- `consent` (required): the requester confirms that both people agreed. It carries the sentence "The person who asked
  for this report confirmed that both people agreed to have their charts compared." No report without it: ask before
  any calculation, and a "no" or no answer stops the report (owner decision 10).
- Neutral names: `prepared_for` is "Person A and Person B"; `birth.persons` holds exactly two entries, `label`
  "Person A" then "Person B", each with its own `date`, `time`, `place`, `time_reliability` (and `moon_stable` on an
  unknown time). The outer `birth.time_reliability` is the less certain of the two; it decides what may be said for
  both. Names, initials and relationship words (bride, groom, husband, wife, boy, girl) do not appear anywhere else.
- The koota tables keep the classical roles, labelled once: the `kootas` section text carries the sentence "The koota
  tables keep the tradition's roles: Person A is read in the bride's place and Person B in the groom's." The requester
  says which person takes which role; the engine's girl and boy inputs follow it.
- No timeline rows and no dates: the match is read from the two birth charts and is not timed. Nothing is graded
  Strong. `ranking` is optional (rows per koota or per fit theme); give it or list it in `dropped`.

Template layout (decided 2026-11-20, T11.36, the smallest change): the shared template, with one cover line per person
and the consent line; no rasi chart is drawn (two charts would mix); positions, if given, sit in one appendix table
with a person column.

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `kootas` | exactly four units, in this order: tara, bhakoot, graha maitri, nadi. Each gives the points with that koota's own maximum (a calculated fact), the inputs (stars, Moon signs, sign lords, nadis) and, in the `counter` line, the exception conditions beside it with whether each holds (never applied), or "no exception listed". The section text carries the role sentence and the sentence "The four kootas are not added up: there is no total out of 36, and vashya, yoni, gana and varna are not computed." | `get_compatibility` (`kootas`: `tara`, `bhakoot`, `graha_maitri`, `nadi`, each with `points`, `max`, `exception_conditions`, `exceptions_not_evaluated`, `variants`; `not_computed`) |
| `counts` | the Prasna Marga sign and star counts both ways, the sign lords' relation and the sign yoni, each reading with its verse and the authorities that disagree; said plainly as rule lookups, not a verdict. The grave wording some verses attach to a count is not repeated (below) | `get_compatibility` (`sign_count`, `star_count`, `sign_count_readings`, `star_readings`, `sign_lords`, `sign_yoni`, `fixed_four`, `note`) |
| `mangal` | Mars in each chart under the four engine rules, in the mangal-dosha unit shape: four units for Person A (themes "Person A: classical rule (BPHS)", "Person A: popular rule", "Person A: Phaladeepika rule", "Person A: HJH2 rule"), then four for Person B, each with its base rate in words and its cancellations in the `counter` line; then one closing unit on both charts (theme naming "both") that shows the "both have it" cancellation as a cancellation with its source, or says "not checked" for a rule whose source gives none | `prepare_consultation` on each chart (`F.yoga.KUJA-BPHS80`, `KUJA-POPULAR`, `KUJA-PD11_3`, `KUJA-HJH2`); Mars's house from the lagna, Moon and Venus → `calculate_birth_chart` |
| `fit` | how the two charts fit, as tendencies: Venus, Mars and Jupiter links between the charts, Sun-Moon harmony, one person's Moon sign as the other's lagna, each tied to a factor and graded; where the charts pull apart, said as a tendency to work with | Venus, Mars, Jupiter, Sun, Moon signs and the lagna of each chart → `calculate_birth_chart` |

Base rates of the four Mangal rules (mangal-dosha.md §1): classical about 15 in 100 random charts, popular about 88 in
100, Phaladeepika about 10 in 100, HJH2 about 78 in 100. Sensitivity of every unit that uses the lagna or a house:
`get_birth_time_sensitivity`, for each person.

`spec_checks` (`match_errors`) refuses: no consent sentence; labels other than Person A and Person B or a `prepared_for`
other than "Person A and Person B"; an outer birth time more certain than either person's; role words outside the one
role sentence, or the sentence twice; a `kootas` section without the role and no-total sentences or without exactly
the four koota units in order, each with its exceptions; a `mangal` section without four rule units per person in order
(base rate, cancellations) and one closing both-charts unit; any Strong grade; timeline rows or dates. The type gate
refuses a total or score, a verdict to marry or not, the grave readings of a count, fear framing and the Mangal gate's
marriage-failure, match-rule and remedy wording.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Basic chart structure matters more than koota points | HJH2 p66; PM2 p107 |
| Venus, Mars and Jupiter links (trine or 3/11), Sun-Moon harmony, one Moon sign as the other's lagna | HJH2 p69-70 |
| Sign and star counts from one Moon to the other, each verse with its reading; the author gives no unit scores | PM2 ch. XXI (the engine's source map, pages p96-107, not page-checked); PM2 p107 |
| Tara, bhakoot, graha maitri and nadi points, maxima and exception conditions; vashya, yoni, gana and varna not computed (the sources conflict), so no total | MC5 ch. 6 (verse numbers as the engine gives them, from another edition of the same text; pages not checked in MC5); topic-relationships-marriage.md (the skill's own rule: never add them up) |
| Mangal rules per chart: classical, popular, Phaladeepika, HJH2 | BPHS p955; LOL p329-331; PD p142 (XI.3); HJH2 p70 (as mangal-dosha.md §2) |
| The classical rule's effect ceases when both people have it | BPHS p955 (ch. 80 sl. 47-49 and the translator's note) |
| A "both have it" cancellation under the popular, Phaladeepika and HJH2 rules | not checked: no source in this library was read for it; say "not checked" |
| The partner and age exceptions of the popular rule | LOL p329-331 names them; not assessed here |
| Consent of both people before any calculation; neutral names | owner decision 10 (2026-11-20) |

Cite them in `appendix.sources` with the catalog id first ("HJH2: B. V. Raman, How to Judge a Horoscope Vol. 2, p66,
p69-70"). Never cite the MCJ edition the engine read as a catalog book: it is not one.

## 3. Conventions

Lahiri, whole-sign houses, mean nodes (the engine defaults). Prasna Marga counts from the bride's Moon to the groom's;
both directions are given. The engine's girl and boy inputs are the classical roles only; the report says Person A and
Person B. The HJH2 rule counts by bhava; here by whole sign (as mangal-dosha.md).

## 4. Caveats

- Fit is a set of tendencies, never a verdict: no "good match", "compatible", "should marry", "reject" or any advice to
  marry or not. Mutual love and the two people's own choice decide; the report says what the charts show.
- Never a total: no sum of points, no "out of 36", no score. Each koota keeps its own maximum.
- No fear framing (`_FEAR`), no medical or death words (the shared `medical_words.py`), no marriage-failure or
  partner-harm wording, no match rule and no remedies (the Mangal gate). Several Prasna Marga verses attach loss,
  quarrel or worse to a count: name the verse and say "a traditional caution", never the wording.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).
- Each chart is computed on its own; the two are never merged. One person's data never appears in the other's lines.

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time (either person) | every unit that uses that person's lagna or houses carries `sensitivity`; drop a Mangal rule whose count changes inside that person's birth-time range |
| unknown time (either person) | the whole report is read at the less certain time: drop `mangal` (all four rules need the lagna) and the lagna and house parts of `fit`; `kootas` and `counts` stay only when each unknown-time person's Moon sign and nakshatra are the same across the whole birth day (`moon_stable` on that person and on `birth`), else drop them with that reason |
| any time | a total or score; the other four kootas (vashya, yoni, gana, varna); a "both have it" cancellation with no source read; any timing |
