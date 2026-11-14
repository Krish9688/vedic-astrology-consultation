# Education report spec (`education`)

How the person learns, which fields the chart leans to and the periods that favour study. Inside the shared frame
([README.md](README.md)). Method: [topic-travel-education-health-life.md](../topic-travel-education-health-life.md) §2.

**Order (standard):** `windows` → `learning` → `fields` → `next`

Inputs: `birth`. Model: `report_type: "education"`, `depth: "standard"`, the frame fields. The `ranking` table ranks the
fields or the windows by support (`item`, `support`, `why`, `window`, `caution`).

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | three to five named windows for study (start, deepen, sit exams, finish), each with dates, a one-line basis and the event it activates; admission, exam results and completion are separate windows | network → `get_topic_network` (topic `education`); activation → `get_activation`; MD/AD → `get_dasha`; Jupiter and Saturn on the 4th, 5th, 9th or their lords → `get_transits` |
| `learning` | learning style and aptitude: the 5th and its lord, Mercury (analysis) and Jupiter (knowledge), the 4th for schooling, the 2nd for speech and early learning, the 3rd for skills; strengths and blind spots, each tied to a placement | houses 2 to 5 and 9, lords, occupants, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`); the Saraswati combination only as a cited rule checked by hand from the printed placements (the engine's yoga list has no such yoga) |
| `fields` | fields of study as aptitudes (analysis, languages, care, building, law, teaching), ranked by support; D24 is always dropped here (listed in `dropped`) | the 5th, 9th, Mercury, Jupiter → `calculate_birth_chart` |
| `next` | the next two to three years by window name: what to start, what to finish, who helps | `get_activation`, `get_transits`, `get_dasha` |

Situation check: ask in `next_step` (current stage, the course or exam in view, whether already enrolled). Sensitivity of
every unit and window: `get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Houses: 4 foundational schooling, 5 intelligence and learning, 9 higher study, 2 speech and early learning, 3 skills; karakas Mercury and Jupiter | topic-travel-education-health-life.md §2 (the skill's own summary) |
| The 5th a Mercury sign or with Mercury, or the 5th lord well placed: sharp intellect | PD XVI.15 |
| Saraswati yoga (Venus, Jupiter, Mercury in kendra, kona or the 2nd, with a strong Jupiter): learning and expression | PD VI.26-27 |
| Benefics in the 4th with its lord well placed: higher education, its kind by dignity | HPA p50-52 |
| D24 is a learning varga but is not in the sensitivity grid, so it is always Untested; this report drops it and never uses it to confirm an event or raise a grade | vargas.md (D24 row; stability rules, l.70) |
| Admission, exam results and degree completion are distinct events with their own windows | topic-travel-education-health-life.md §2 |
| A running dasha of the network gives the event; transits only confirm | timing.md §0 (the skill's own ladder) |
| No score, admission or degree guarantee | the skill's own rule (topic-travel-education-health-life.md §2; vargas.md) |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. Fields are translated into present-day study areas, never
a guaranteed course, college or result. The activation preset runs on the 4th with the 5th and 9th lords added (its own
note says the topic file names houses 4, 5 and 9).

## 4. Caveats

- Aptitude, not outcome: no marks, rank, admission or pass or fail claim; no scholarship or test score.
- Fields are ranked by support, not predicted.
- Study abroad belongs to the relocation report; mention it only as a pointer.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | units on the 4th, 5th or 9th carry `sensitivity`; windows in months |
| unknown time | `windows` and `next` become at most labelled monthly markers of slow planets to time-independent natal planets; drop `learning` and `fields` (house-based); drop the ranking if no field has support without houses |
| any time | D24 always (untested, vargas.md); the Saraswati combination when its placements cannot be shown from the chart table |
