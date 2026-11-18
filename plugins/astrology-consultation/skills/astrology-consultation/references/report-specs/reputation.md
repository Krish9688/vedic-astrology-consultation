# Reputation report spec (`reputation`)

Standing, recognition and image: how others see the person and what the standing rests on. Inside the shared frame
([README.md](README.md)). Method: [topic-career-money.md](../topic-career-money.md) §4 and §6, and the arudha lines of
[jaimini.md](../jaimini.md) §2. Kept apart from the career report: career answers the type of work and the next step;
this report answers rank, recognition, image and setbacks, and never ranks fields of work.

**Order (standard):** `windows` → `standing` → `image` → `setbacks` → `choices`

Inputs: `birth`. Model: `report_type: "reputation"`, `depth: "standard"`, the frame fields. The `ranking` table ranks the
windows or the sources of standing (expertise, authority, visibility, connections) by support (`item`, `support`,
`why`, `window`, `caution`).

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | three to five named windows for recognition or exposure, and for pressure on standing, each with dates, a one-line basis and what it activates | network → `get_topic_network` (topic `career`, whose 10th-house frame is the one used here); activation → `get_activation`; MD/AD → `get_dasha`; Jupiter and Saturn on the 10th, its lord or the Sun → `get_transits` |
| `standing` | how far and on what the standing rests: the 9th-10th lord link, lagna lord and 10th lord, mahapurusha yoga by the 10th lord, an exalted 10th lord aspecting the 10th; D10 for position in society | 10th, 9th and lagna lords, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`); D10 → `get_divisional_chart` (10) |
| `image` | how the person is seen, from the Arudha Lagna (the image, not the substance); A10 for visible status as modern practice, labelled; a strong AL with a weak lagna is image ahead of resources, and the reverse | arudha padas (AL, A10) → `get_jaimini_factors`; the lagna and its lord → `calculate_birth_chart` |
| `setbacks` | what lowers or unsettles standing: Saturn in the 10th, raja yoga in the 12th or 6th or 12th from the Moon, Saturn-Venus mutual periods; each with its period and the counter-factor | placements → `calculate_birth_chart`; periods → `get_dasha`, `get_activation` |
| `choices` | how to handle visibility, credit and timing in each window; no new computation | from the sections above |

When the same person also gets the career report, name a shared window the same way in both and point to the career report.
Situation check: ask in `next_step` (the role or public setting, whether the person wants more or less visibility).
Sensitivity of every unit and window: `get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Yogas raise the degree of success, not the type of work; judge rank separately from type | HJH2 p288; HJH2 p304-321 |
| Markers of rise: 9th-10th lord link; lagna lord and 10th lord related; mahapurusha yoga by the 10th lord; the 10th lord exalted and aspecting the 10th | HJH2 p304-321 |
| Markers of fall or instability: Saturn in the 10th (rise then fall); raja yoga in the 12th or 6th, or 12th from the Moon | HJH2 p362; HJH2 p357-366 |
| Saturn-Venus mutual periods break raja yogas | HJH2 p364 |
| Dasha-bhukti lords in 3 and 11 or kendras from each other favour rise; 6/8 or 2/12 hinder | HJH2 p260, p364 |
| Authority comes in periods of the planet in the lagna, the planet in the 10th or the strongest planet; it is lost in periods of planets in enemy or debilitation signs | HJH2 p344; BJ p158 |
| The dasamsa gives power and position | BPHS p104 (inherited from career.md) |
| The dasamsa shows achievements in society | PVR p493 (inherited from career.md) |
| Arudha Lagna: count from the lagna to its lord and the same number again; examine it as another birth chart for how the person is seen and what they visibly accumulate (Jaimini method; LOL says Parashara's method gives the same) | LOL p440 |
| Arudha exceptions: a count landing in the house itself takes the 10th from it; landing in the 7th takes the 4th from the original. Some practitioners do not apply this; name the convention used | BPHS ch. 29 sl. 45 (PDF p308) |
| A10 for visible career status | modern practice, not a rule found in this library (label it so; jaimini.md §2) |
| Arudha is image, not substance; never count AL as a Parashari house | LOL p122 (spirit); modern practice (jaimini.md §2) |
| D10 confirms the 10th lord's condition; it never creates an event alone | the skill's own rule (topic-career-money.md §3) |
| A running dasha gives the event; a transit only confirms | timing.md §0 (the skill's own ladder) |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. Jaimini units carry `system: "jaimini"` and say which
arudha convention was used. The 10th is taken from the lagna; the Moon and Sun views are added only when the writer
names them.

## 4. Caveats

- Standing and image only: no forecast of fame, celebrity or public office; no legal, scandal or reputation-damage
  verdicts; a setback is a pressure period, never a named event.
- Jaimini and A10 readings are labelled and graded no higher than Moderate (A10 is modern practice).
- Never accuse or name a person as a rival or a cause.
- The career report owns the type of work and the money; do not restate its fields or income here.
- Parashari with Jaimini arudha only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | D10 and the arudha padas when their lagna class is `high` or `very high`; units on the 10th, 9th or the AL carry `sensitivity`; windows in months |
| unknown time | `windows` becomes at most labelled monthly markers of slow planets to time-independent natal planets; drop `standing`, `image` and `setbacks` (house, lagna, varga and arudha based); drop the ranking if nothing has support without houses |
| any time | A10 if the writer cannot state the convention; a reputation claim from D10 alone |
