# Challenges report spec (`challenges`)

Where the chart shows pressure, how disputes tend to show up and how to respond. It names pressure periods and
tendencies, never an outcome. Inside the shared frame ([README.md](README.md)). Method:
[vedic-natal.md](../vedic-natal.md) §2 and [timing.md](../timing.md) §2; the setback rules of
[topic-career-money.md](../topic-career-money.md) §4.

**Order (standard):** `windows` → `pressure` → `disputes` → `response`

Inputs: `birth`. Model: `report_type: "challenges"`, `depth: "standard"`, the frame fields. The `ranking` table ranks the
areas where pressure is more or less likely (work, money, home, relationships, plans) by support (`item`, `support`,
`why`, `window`, `caution`), never the person.

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | two to four named pressure windows and one easing window, each with dates, a one-line basis, the kind of strain and the counter-factor; a window is a period of strain, never a named event | network (below) → `get_topic_network`; activation → `get_activation`; MD/AD and the bhukti relation to the dasha lord → `get_dasha`; Saturn and Jupiter over the lagna, Moon, the 6th, 8th, 12th or their lords → `get_transits` |
| `pressure` | where strain gathers: lords of the 6th, 8th and 12th and their houses, Saturn and Mars by condition, a lagna lord in a dusthana, the viparita form where present; each with the counter-factor | lords, placements, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`) |
| `disputes` | how disagreement tends to show (open or quiet, early or slow, with whom in general terms: work, family, neighbours, money); the 6th, 3rd, 4th (property) and 7th (open opponents) in general terms; no outcome | houses, lords → `calculate_birth_chart`; periods → `get_dasha`, `get_activation` |
| `response` | how to handle each window: slow down, document, ask for advice, pick the moment; no new computation | from the sections above |

Situation check: ask in `next_step` what is happening now (area, since when) and whether anything is pending; do not
ask for details of a case. Sensitivity of every unit and window: `get_birth_time_sensitivity`.

### The custom network (`windows`)

There is no challenges preset in the engine. Build the network with `get_topic_network` and a `planets` list: the lords
of the 6th, 8th and 12th (read from the chart facts) with Mars and Saturn, duplicates removed. Freeze it before looking
at dates, then pass the unchanged result to `get_activation`. Why: the 6th is competition, debt and disputes, the 8th
disruption and the 12th loss and separation (vedic-natal.md §2); the dasha of a natural malefic keeps a flavour of
struggle even when it is functionally good (LOL p346). The engine flags every entry of a custom network as unsourced;
the report says so in `appendix.method`, and a window that rests on the network alone is graded no higher than Moderate.
The library has no direct rule that puts Mars in a disputes network. BPHS p337 (page re-read) lists Mars as the significator of the 6th; the sloka (34) itself is not yet re-read, so check the BPHS bhava-karaka list for the 6th before citing it.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| The 6th: work and service, competition, debt, disputes; the 8th: disruption, hidden matters; the 12th: expenditure, loss, separation | vedic-natal.md §2 (the skill's own summary) |
| A natural malefic's dasha keeps a flavour of struggle even when it is functionally good | LOL p346 |
| Dasha-bhukti lords in 6/8 or 2/12 from each other hinder; in 3 and 11 or kendras they favour rise | HJH2 p260, p364; HPA p76; HJH2 p473 |
| Saturn in the 10th (rise then fall); raja yoga in the 12th or 6th, or 12th from the Moon | HJH2 p362; HJH2 p357-366 |
| Saturn-Venus mutual periods break raja yogas | HJH2 p364 (CR-X12 notes a milder modern view: expect reorganisation, not a verdict) |
| The 4th lord with an enemy planet: property disputes | PD XVI.14 |
| Loans and disputes from the 6th, fines and expense from the 12th, sudden loss from the 8th | topic-career-money.md §5 (outflow and debt) |
| Viparita raja yoga: a rise after a setback is a possibility only. The definitions differ (two of the 6th, 8th, 12th lords each in another dusthana; one such lord in another; joined in a dusthana); name the one used | LOL p327; HJH2 p296, p353; CRUX p30-32; CR-V29, CR-X21 |
| Saturn is not an afflicter when it rules the matter | HJH2 p33, p40, p216 |
| Sade sati is a broad lens, needs dasha confluence and is milder the second time; never a verdict by itself | LOL p363-364; HPA p130 |
| A running dasha gives the event; a transit only confirms | timing.md §0 (the skill's own ladder) |
| A transit never produces a major event without natal promise and dasha activation | HJH2 p119-122; HPA p134 |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. The 6th, 8th and 12th are taken from the lagna; the Moon
view is added only when the writer names it. The viparita definition used is named in the unit.

## 4. Caveats

- Pressure and tendencies only, never an outcome. The report states: "This is not legal advice." No legal outcome is
  given: no win or lose, no verdict, no court ruling, no settlement promise, no court or hearing date.
- A pressure period is a time to be careful, not a forecast of loss; every window carries a counter-factor and an
  early sign to notice.
- Never name a person as an opponent, a cause or at fault; never read a third party's chart or conduct.
- No health, accident or death claim and no organ words; strain is described in life terms (time, money, relationships,
  plans).
- No remedy, gem or ritual: remedies are outside this type.
- A rise after a setback (viparita) is a possibility, never promised.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | units on the 6th, 8th or 12th, the lagna lord or a lord relation carry `sensitivity`; windows in months; the viparita reading when its lagna class is `high` or `very high` |
| unknown time | `windows` becomes at most labelled monthly markers of slow planets to time-independent natal planets; drop `pressure`, `disputes` and `response` (house, lord and dasha based) and the ranking; the model keeps one house-free note section (the schema needs at least one section) that says what was dropped and why |
| any time | any legal-outcome wording; a pressure claim from a transit alone |
