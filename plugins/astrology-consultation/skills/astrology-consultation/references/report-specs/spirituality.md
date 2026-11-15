# Spirituality report spec (`spirituality`)

The person's inner path, what supports practice and the periods that turn them inward. Inside the shared frame
([README.md](README.md)). Method: [topic-travel-education-health-life.md](../topic-travel-education-health-life.md) §4.
This is a report on tendencies and timing of inner life. It never ranks a person spiritually, never reads past lives
or curses, and never certifies a level of attainment.

**Order (standard):** `windows` → `path` → `practice` → `inner`

Inputs: `birth`. Model: `report_type: "spirituality"`, `depth: "standard"`, the frame fields. The `ranking` table ranks the
supports for practice (study, devotion, service, solitude, inquiry) by support (`item`, `support`, `why`, `window`,
`caution`), never the person.

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | two to four named windows that turn the person inward or open study, retreat or a teacher, and one for restlessness or loss of footing; each with dates, a one-line basis and what it activates | network → `get_topic_network` with a `planets` list (see the network below); activation → `get_activation` with that network; MD/AD → `get_dasha`; Jupiter and Saturn on the 5th, 9th, 12th, their lords or Ketu → `get_transits` |
| `path` | what the chart leans to: devotion, study, service, solitude or inquiry; the 9th (teachers, dharma), 5th (practice, mantra), 12th (retreat), 8th (inquiry), Jupiter and Ketu; a chart where renunciation is the dominant theme is read in that key | houses 5, 8, 9, 12, lords, occupants, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`); karakamsa as a labelled Jaimini note → `get_jaimini_factors` |
| `practice` | what fits as a regular practice (a steady daily one, study, service, silence), tied to the placements above; no remedy, gem or ritual | from `path`; D20 only as a labelled conditional reading → `get_divisional_chart` (20) |
| `inner` | what the running and next major periods ask of the inner life (a chapter, not a verdict) and the early sign to notice | MD/AD → `get_dasha`; the period lords' roles → `get_activation`; sensitivity → `get_birth_time_sensitivity` |

### The custom network (`windows`, `inner`)

There is no spirituality preset in the engine (presets exist only for marriage, career, finance, relocation and
education). Build the network with `get_topic_network` and a `planets` list: the lords of the 12th, 9th and 5th (read
from the chart facts, `F.H12.lord`, `F.H9.lord`, `F.H5.lord`) with Jupiter, Ketu and Saturn, duplicates removed. Freeze it
before looking at dates, then pass the unchanged result to `get_activation`.

Why these: the reference names the 5th, 9th, 12th and 8th with Jupiter and Ketu (topic-travel-education-health-life.md §4).
The 8th is a house of inquiry and is read in `path` but is not added to the network (its lord would pull in loss and
disruption windows that have nothing to do with practice). Saturn is not named in that reference; it is added as the
skill's own inference, as for the 12th-house retreat note in topic-relationships-marriage.md §9, and it is labelled
that way. The engine flags every entry of a custom network as unsourced; the report says so in `appendix.method` and
grades any window that rests on the network alone no higher than Moderate.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Houses: 5th practice and mantra, 9th teachers and dharma, 12th retreat and liberation, 8th inquiry; Jupiter and Ketu | topic-travel-education-health-life.md §4 (the skill's own summary) |
| Renunciation yogas colour the whole chart when dominant: read other combinations in that key | LOL p418; BJ XV |
| A strong 4th lord gives moral development in place of outward show (chart tenor) | LOL p418 |
| The 12th house: expenditure, separation, retreat, liberation | HJH2 p418 |
| Karakamsa (the Atmakaraka's navamsa sign used as a lagna) gives a Jaimini reading of the inner bent; state the karaka scheme (seven or eight) and that the reading is Unknown if the karaka changes between them | BPHS ch. 33; jaimini.md §1 |
| D20 is for spiritual practice; it is not in the sensitivity grid, so it is always Untested: a labelled conditional reading at most, never a confirmation | vargas.md (D20 row and the Untested rule) |
| A running dasha gives the event; a transit only confirms | timing.md §0 (the skill's own ladder) |
| No spiritual rank, no past lives, no curses | topic-travel-education-health-life.md §4 |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. Karakamsa is Jaimini: the unit carries `system: "jaimini"`
and names the scheme. The custom network is the skill's own and is called that. Ketu is read as a theme of letting go
and detachment, never as a fate.

## 4. Caveats

- Never rank or grade the person spiritually: no "enlightened", "old soul", "advanced soul" or "spiritual level". The
  report may say that no rank or level is given.
- No past lives, no karma carried from before birth, no curse. Those claims are not in this library as testable rules.
- A window turns the person inward or tests their footing; it is not a spiritual event and nothing is awarded in it.
- No practice is prescribed as a cure and no gem, ritual or costly rite is advised; remedies are outside this type.
- Religion, sect and belief are never assumed or asked: the report names a kind of practice, not a faith.
- Parashari with a labelled Jaimini note only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | karakamsa when the D9 lagna class is `high` or `very high` (karakamsa is the Atmakaraka's navamsa sign); D20 is not in the sensitivity grid, so it has no lagna class and is always Untested: a labelled conditional reading, never a confirmation; units on the 5th, 9th or 12th carry `sensitivity`; windows in months |
| unknown time | `windows` becomes at most labelled monthly markers of slow planets to time-independent natal planets; drop `path`, `practice` and `inner` (house, lord, varga and dasha based) and the ranking; the model keeps one house-free note section (the schema needs at least one section) that says what was dropped and why |
| any time | D20 as a confirmation; karakamsa when the karaka scheme changes the Atmakaraka |
