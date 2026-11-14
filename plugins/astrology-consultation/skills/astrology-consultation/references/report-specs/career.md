# Career report spec (`career`)

The working pattern, the current chapter, the next two to three years, money and choices. Owner template T1 inside the
shared frame ([README.md](README.md)). The existing `career` type is kept; this spec aligns it (reports.md §2).

**Order (standard):** `windows` → `pattern` → `chapter` → `next` → `money` → `choices`

Inputs: `birth`. Model: `report_type: "career"`, `depth: "standard"`, the frame fields. "Fields that fit" is the
`ranking` table (rank, field, supporting indicators in `why`, `support`), not a section.

## 1. Sections and computed fields

| Section | Content (owner template T1) | Computed fields → engine tool |
|---|---|---|
| `windows` | three to five named windows, each with dates, a one-line basis and what it activates | network → `get_topic_network` (topic `career`); activation → `get_activation`; MD/AD → `get_dasha`; 10th-lord transit contacts, ingresses → `get_transits` |
| `pattern` | work nature, work style (employee or self-employed, solo or team, pace, authority), strengths and blind spots, each tied to a placement | 10th house sign, occupants, 10th lord, 10th from the Moon and Sun → `calculate_birth_chart`; aspects on the 10th → `prepare_consultation` (derived facts, chart_facts `aspected_by`); D10 → `get_divisional_chart` (10); Amatyakaraka → `get_jaimini_factors`; strength ratio per planet → `get_shadbala` |
| `chapter` | the running period in work terms (free text or units) | MD/AD → `get_dasha` |
| `next` | the next two to three years by window name: growth phase, who helps | `get_activation`, `get_transits` |
| `money` | income source and pattern, retention | 2nd, 11th and lords → `calculate_birth_chart`; SAV of the 10th and 11th → `get_ashtakavarga` |
| `choices` | decisions and choices: what to do in which window | from the sections above; no new computation |

Growth curve: by period and window, with dates, not ages (an age would be new arithmetic on the birth date and adds
nothing the dates do not say). Current situation check: ask in `next_step` (current role, target role, whether
actively looking). Sensitivity: `get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Vocation from the 10th: empty 10th → 10th lord and its navamsa lord, the stronger decides; occupied → the strongest of lord, occupant and navamsa lord | HJH2 p253 |
| Take the 10th from the lagna, the Moon and the Sun; use the strongest | HJH2 p254–255 |
| The 10th settled the profession clearly in only 15 of over 50 charts: give a field of aptitude, not a title | HJH2 p250 |
| Yogas raise the degree of success, not the type of work | HJH2 p288 |
| Power and position from the dasamsa | BPHS p104 |
| The dasamsa shows "achievements in society" | PVR p493 |
| Amatyakaraka (second-highest longitude) controls career | JSR p292, p299 |
| 9th and 10th lords linked: Dharma-Karmadhipati yoga | PVR p146 |
| Required Shadbala and its effect | BPHS p299 |
| Gains from the 11th, by occupant | HJH2 p372 |
| D10 confirms the 10th lord's condition; it never creates a career event alone | the skill's own rule (topic-career-money.md §3) |
| No investment signals; no guaranteed job title | the skill's own rule (owner, remedy-safety.md) |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. Classical occupations are translated into present-day
functions (analysis, care, building, law, teaching), never a guaranteed title.

## 4. Caveats

- Fields are ranked by support, not predicted.
- Money: income pattern and timing only; no buy or sell advice, no figures.
- Health appears only as workload and stress periods, never organs.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | D10 readings when the D10 lagna class is `high` or `very high`; units on the 10th or 11th carry `sensitivity`; windows in months |
| unknown time | `windows`, `chapter`, `next` (dasha-based) become at most labelled monthly markers of slow planets to time-independent natal planets; drop the house-based parts of `pattern` and `money`; drop the ranking if no field has support without houses |
| any time | the template's per-planet "strength ratio" as a second scale (it stays a computed number in the appendix; the text uses grade words) |
