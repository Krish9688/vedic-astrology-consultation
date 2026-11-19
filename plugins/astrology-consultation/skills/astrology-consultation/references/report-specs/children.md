# Children report spec (`children`)

The person's bond with children, their parenting style, and the other ways the care for the next generation shows
(adoption, step-children, students, creative work). Themes only: no window, no "when", no number, no verdict. Inside the
shared frame ([README.md](README.md)). Method: [topic-home-family-children.md](../topic-home-family-children.md) §1 (the
children output rule). Owner decision 2026-11-19.

**Order (standard):** `theme` → `parenting` → `alternatives`

Inputs: `birth`. Model: `report_type: "children"`, `depth: "standard"`, the frame fields. There is no `windows`
section and the model carries no `timeline` rows (the template then prints no timeline). The `ranking` table ranks the
themes the chart supports (`item`, `support`, `why`, `caution`); `window` is left out. Follow-ups point to the family
or relationship report, never to a timing question.

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `theme` | the person's bond with children as a theme: warmth, ease, strictness, distance, responsibility; the 5th house and its lord, Jupiter as karaka, the 5th from the Moon; supportive and strained influences named as qualities of the bond, never as outcomes | 5th, its lord, occupants, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`); theme network → `get_topic_network` (topic `children`: a theme network only; `get_activation` is not run for it); D7 → `get_divisional_chart` (7) only as a labelled conditional reading on a robust time |
| `parenting` | the style of care: how the person teaches, guides, plays and sets limits; the lagna lord, the 5th lord, Jupiter, Saturn and Mars by their roles; the 4th for the home climate the person offers | houses, lords, dignity → `calculate_birth_chart`; sensitivity → `get_birth_time_sensitivity` |
| `alternatives` | the other ways the same theme shows: adoption, step-children, students, mentoring, creative work (the 5th also rules students and creative "offspring"), and care for younger relatives | 5th, 9th, 11th and their lords → `calculate_birth_chart`; D7 as above |

Situation check: ask in `next_step` what fits and what does not, and which area to look at next (never "do you want a
date").

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| The 5th house, its lord and Jupiter are read for the theme; lagna and 5th lords related and Jupiter well placed is the supportive pattern | PD XII.1; HPA p52 |
| Sources conflict on some placements (a benefic owning the 5th; Jupiter in the 5th): say so and grade Weak | PD XII.3; LOL p421; HJH2 p65 |
| Adoption, step-children, students and creative "offspring" are legitimate expressions of the 5th | topic-home-family-children.md §1 |
| D7 is a conditional reading only, on a robust time | vargas.md (D7 row) |
| The method notes on timing, counts and obstruction are for judging the theme, not for forecasting births: they are never applied to the person | topic-home-family-children.md §1 (output rule) |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes. The 5th is taken from the lagna, and again from the Moon as a second view. D7 is
conditional: used only when `time_reliability` is exact and the D7 lagna class from `get_birth_time_sensitivity` is not
`high` or `very high`; otherwise it is dropped and listed. Parashari only.

## 4. Caveats

- `depth` is required (no legacy form), so no gate can be skipped. The gates also read `appendix.method`; no `appendix.periods` table is given. Contractions are folded first ("you'll" reads as "you will"). Twins, little ones, lineage, cradle and similar euphemisms are read as children words; planet periods, seasons and ages are timing words. A relative's baby question is a normal question and is not covered by this report.

- Scope states: "This report reads your bond with children, your parenting style and other ways the care shows. It gives
  no timing, no count and no forecast about having children." (The test keeps this sentence in the fixture.)
- Never a window, a period, a year or any "when" for having, conceiving or raising a child; never an age of parenthood;
  never a number of children; never "delay", "limited progeny", "childless" or a softened form (late, slow, after
  effort, obstructed, denied). The checker refuses years and month names anywhere, any timeline row, and the wording
  forms in `render_report.TYPE_GATES["children"]` (`_CHILDREN_FORMS`, `_CHILDREN_EXTRA`). A forecast about the person
  ("You will not have children") is refused even when negated.
- No fertility, pregnancy, conception or birth-health wording (owner rule 2026-11-15): these words are on the shared
  medical list (`medical_words.REPORT_WORDS`), refused in every string of every report. A "when" question about
  children gets the plain refusal at intake, and routing no longer marks it as a timing question.
- A tendency is not a verdict: the choice stays with the person. No child's character, health or fate is read.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5). Remedies are not part of this type.
- Allow-list (T11.32, owner 2026-11-19): a clause about the person's child or children may only describe. The describing verbs
  are a closed list (`_AL_BASE` in `render_report.py`: bond, connect, guide, teach, mentor, nurture, encourage, support, enjoy,
  share, play, learn, listen, understand, inspire, care, spend, adopt, foster, raise as a style, and similar). Refused in such a
  clause: arrival, giving, having and becoming verbs (come, arrive, bring, give, bless, welcome, have, get, be with child);
  passive existence words (shown, indicated, seen, expected); a modal unless a listed verb follows it; will and other future
  forms; counts; ages and decades; pregnancy and newborn phrasings; closed, quiet or empty family metaphors (empty arms, a quiet
  nursery, the line ends, a family that grows). Child words include baby, newborn, son, daughter, boy, girl, little ones,
  nursery, brood, cradle, stork, lineage, parenthood, motherhood. Error: "wording about children that is not a bond, a parenting
  style or an alternative (only describing those is allowed)". A scope sentence that says what is not given is exempt ("No
  timing, count or forecast about children is given"). In the kundli family section the same rule reads child clauses only; a
  neutral dated line about a relative's baby in the family.md shape is allowed there. Known limit of the allow-list: it is word
  lists and two adjacency checks (the word after and before a child word), not a parser; a verb in neither list with no -s, -ed
  or -ing ending passes, and ordinary clauses with "have", "one" or "after" beside a child word are over-blocked.
- Known limit: the gates are word forms, a backstop; the over-blocks (an ordinary sentence with "have" and "children",
  or "later" beside "children") are accepted, and a missing phrasing gets through.

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | D7 when its lagna class is `high` or `very high` (list in `dropped`); every unit on the 5th, its lord or a house carries `sensitivity` |
| unknown time | drop `theme`, `parenting`, `alternatives` (house and lord based) and the ranking; the model keeps one house-free note section that says what was dropped and why; no timeline row |
| any time | any window, period, year, count or timing for children; any statement about conceiving, pregnancy or birth |
