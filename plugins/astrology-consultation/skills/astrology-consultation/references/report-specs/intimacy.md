# Intimacy report spec (`intimacy`)

Closeness and comfort as a natal description: how warmth, affection and desire show, what steadies them, and what can
hold them back. For an adult, about their own life, in plain respectful words; nothing explicit. Inside the shared frame
([README.md](README.md)). Method: [topic-relationships-marriage.md](../topic-relationships-marriage.md) §9. Owner
decision 2026-11-19.

**Order (standard):** `comfort` → `venus` → `bond` → `phases` → `steadiers`

Inputs: `birth`. Model: `report_type: "intimacy"`, `depth: "standard"`, the frame fields. The report is built **only
when the birth date shows 18 or over on the report date** (`prepared_on`); no separate statement is needed and an
unreadable date counts as not shown: `spec_checks` refuses the model (`adult_errors`), so nothing renders. `phases` is
read only when the person asked; otherwise it is listed in `dropped` with the reason "not asked". The timeline carries
`chapter` rows only (the running major period); `window` and `pressure` rows are refused. The `ranking` table ranks the
themes by support (`item`, `support`, `why`, `caution`); there is no window.

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `comfort` | the 12th house and its lord: occupants, aspects, the lord's sign, house and dignity; supported or strained, and why ("desire strong, opportunity limited" is a valid reading) | 12th, lord, occupants → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`) |
| `venus` | Venus as karaka: dignity, combustion, companions, its navamsa sign; the Venus and Mars pairing as warmth and drive, steadied by Jupiter | Venus, companions → `calculate_birth_chart`; navamsa → `get_divisional_chart` (9) only when the lagna class is not `high` or `very high` |
| `bond` | the 7th lord and Venus as fondness inside a partnership (the quality of the bond itself is the relationship report); the lagna lord as the person's own side | 7th lord, lagna lord → `calculate_birth_chart` |
| `phases` | only if asked: how the theme changes with the running periods, by chapter, never as a dated window | MD/AD → `get_dasha`; the model gives `chapter` rows only |
| `steadiers` | what steadies it (Jupiter's aspect on the 12th, its lord or Venus; a strong lagna lord) and the best two reasons if comfort is limited (circumstance, privacy and rest, restraint by choice, the relationship itself), each with its support | aspects → `prepare_consultation`; sensitivity → `get_birth_time_sensitivity` |

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Bed comforts are read from the 12th house, with Venus as karaka and the 7th for union with the partner | HJH2 p418; JP2 XV.73; PVR p80-81 |
| Supported: the 12th and Venus both well disposed; the 12th lord with benefics, own or exalted; strained: an afflicted 12th lord, or one in the 6th or 8th or in a debilitation or enemy navamsa | HJH2 p422-423; JP2 XV.79-81 |
| Venus in the 12th: comfort, and what comes with it depends on Venus's companion | PD VIII.19; BHRIGU p185; LOL p175-176 |
| The Venus and Mars relation carries attraction and needs Jupiter's steadying | HJH2 p64 |
| Rahu in the 12th (wanting that is hard to satisfy) rests on one modern author: Weak alone | LOL p379 |
| Restraint by choice (modern and list support only): Weak | BEHARI2A p157-158; UKAL V p121 |
| Counter-factors: Jupiter's aspect; a strong lagna lord; the full result comes only when the whole chart agrees | HJH2 p423 |
| The navamsa of the 12th lord and of Venus confirms or qualifies the reading | BPHS ch. 23 sl. 5-6 |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes. The reading is a natal description first. Grade: **Moderate** when the 12th with
its lord and Venus agree in rasi and navamsa (the unit's `basis` names the 12th, Venus and the navamsa: checked);
**Weak** on one factor or when they disagree; never Strong, never certain. The classical moral labels are not repeated.

## 4. Caveats

- `depth` is required (no legacy form). The adult gate compares the birth date with the engine's birth input in `create_report`, refuses a report date later than today, and does not read an ambiguous numeric day/month date (both parts 12 or less). Grades: Unknown only on an approximate or unknown birth time. A timeline chapter row is allowed only when `phases` is asked and written. No year or month name in the text. A capitalised given name as subject or possessor is refused (write text in sentence case).

- Scope states: "This report is for an adult and is about your own life. It is tasteful and tendency-level: nothing
  explicit, nothing about the body or reproduction, no reading of orientation or gender, and nothing about any other
  person."
- The adult gate is by birth date only (see above). Under 18: no report.
- Nothing explicit, and nothing on sexual health, potency or fertility (the shared medical list refuses those words in
  every string). The chart is not read for orientation or gender identity. No moral labels or verdicts on character or
  fidelity. Nothing about a named or implied third person's desires or conduct; a partner's conduct is not in the chart.
- The type gate (`_INTIMACY_FORMS`, `_INTIMACY_EXTRA`) also refuses sexual and explicit words, orientation words, moral
  labels, a third person's desires, certainty words and window wording; a negated caveat is allowed ("Nothing here is
  explicit"). It is a word list, a backstop: a missing synonym gets through.
- Added T11.32: more explicit words (carnal, making out, touched all over, under the sheets, physical pleasure, kissing,
  cuddling ...); an orientation rule that refuses any attraction, interest or preference aimed at a gender or sex ("attracted to
  men and women", "into men", "not interested in men"), hard: refused even when negated, so a scope sentence must not name it;
  more moral labels (improper, dirty, tease, loose streak, filthy ...); certainty words (assured, certain as a predicate or "certain
  to", unavoidable, sure thing, written in your chart, a matter of time); and a deny-by-default third-person rule: "your <anyone>"
  followed within four words by a desire or conduct word is refused unless <anyone> is on the closed list of the person's own traits
  (`_OWN_NOUN`: chart, warmth, heart-side words, planets, ordinal houses ...). "Your coworker wants you" is refused;
  "Your warmth needs time" passes. Known limits: a noun missing from the own-trait list is over-blocked; "heart" is refused by the
  shared medical list.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | the navamsa reading when its lagna class is `high` or `very high`; every unit on the 12th, 7th, lagna lord or D9 carries `sensitivity` |
| unknown time | drop all house-based sections and the ranking (the Moon-based note only when `birth.moon_stable` is true); the model keeps one house-free note section that says what was dropped and why |
| under 18, or no readable birth date | the whole report: it is not built |
| not asked | `phases` |
| any time | any dated window or pressure row; anything explicit; anything on the body, health or reproduction |
