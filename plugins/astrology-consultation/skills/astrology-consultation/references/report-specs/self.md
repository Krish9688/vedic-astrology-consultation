# Self report spec (`self`)

Who the person is: core, temperament, broad appearance and the direction of growth. A natal description with no
event timing. Inside the shared frame ([README.md](README.md)). Method: [vedic-natal.md](../vedic-natal.md) §2 to §5,
question-trees.md tree 11 for appearance and constitution.

**Order (standard):** `core` → `temperament` → `appearance` → `growth`

Inputs: `birth`. Model: `report_type: "self"`, `depth: "standard"`, the frame fields. The `ranking` table ranks the
traits or strengths the chart supports (`item`, `support`, `why`, `caution`); there is no window, so `window` is left out.
The timeline carries only `chapter` rows (the running major period); a `window` or `pressure` row is not used.

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `core` | the lagna sign and its lord, the lagna lord's house and condition, the Sun, planets in or aspecting the lagna, one sentence on the main pattern | lagna, lord, occupants, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`); strength → `get_shadbala` (the number is a fact in the appendix, the reading a grade word) |
| `temperament` | how the person feels and responds: the Moon's sign, nakshatra and strength, Mercury for mind, Mars for drive; the lagna lord as the point of agency | Moon, Mercury, Mars, nakshatra → `calculate_birth_chart`; strength → `get_shadbala` |
| `appearance` | broad frame, stature class and bearing only, as the tradition's description; always graded Weak and always with the caveat below (see 2) | rising sign class and the candidate planets, ranked by dignity → `calculate_birth_chart`; the rising navamsa → `get_divisional_chart` (9) only when the lagna class is not `high` or `very high`; stability → `get_birth_time_sensitivity` |
| `growth` | where the person grows: the 5th, 9th and 10th lords, the dispositor of the lagna lord, one strength to use and one habit to watch; the running major period as a chapter | houses, lords → `calculate_birth_chart`; MD/AD → `get_dasha`; sensitivity → `get_birth_time_sensitivity` |

Situation check: ask in `next_step` what fits and what does not (calibration, consultation-reasoning.md §8), and which
area to look at next.

### The appearance section

Look and age wording is refused in every other section and report type outside the relationship `partner` section.
Here it is allowed in `appearance` only. The section's `text` must contain this sentence exactly, every unit in it is
graded Weak or Unknown, and it names at most one or two texts in passing:

> This is the tradition's description, untested and graded Weak: family and region decide more, and it is not a measurement.

Steps (question-trees.md tree 11): the stature class of the rising sign (LOL p133); the planet the person resembles,
chosen from the rising-navamsa lord, the lagna occupant, the lagna lord and the strongest planet, and why; modifiers
from planets in or aspecting the lagna; a synthesis in a short portrait. Where the sign's own verse and the class
differ (Cancer, Sagittarius), say the texts differ (CR-X19) and let the planet decide. Never state a height from the
sign alone. With an unstable time, give the Moon-sign sketch as the fallback and say so.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| The 1st house: body, build, appearance, vitality, agency, direction; the lagna lord links the person to the house it occupies | vedic-natal.md §2 (the skill's own summary); BPHS ch. 12 sl. 1-4 (PDF p138-139) |
| Settle the lagna, its lord, its dispositor and the Moon's strength first: a weak lagna or lagna lord stops even a fine yoga from delivering | LOL p367 |
| Stature class of the rising sign: Aries, Taurus, Aquarius, Pisces short; Gemini, Cancer, Sagittarius, Capricorn middling; Leo to Scorpio long | LOL p133 |
| The sign's own verses differ for some signs | PD IX.4, IX.7, IX.9 (p129-131); PDK p105-106; CR-X19 |
| The planet the person resembles: the lord of the rising navamsa or the strongest planet; other statements take a strong planet in the lagna or add the lagna lord | BJ p88-89; HJH1 p159; JP2 XI.15; LOL p140-141 |
| A benefic in or aspecting the lagna adds to looks, a malefic takes from them (after dignity and lordship are checked) | BPHS ch. 12 sl. 3-4 (PDF p139) |
| The rising-sign sketch is also read from the Moon's sign | PD IX.13; PDK p107 |
| Planet-in-house sketches are one input each, to be weighed with lordship, dignity and aspects | PDK p105-106; BEHARI2A p6-9 (Weak, one modern author) |
| The Moon in a sign, its star and its strength colour temperament and emotional response | vedic-natal.md §7 (nakshatras); consultation-reasoning.md |
| Where steps disagree, say "mixed" and give the stronger factor first | SAR1 p158 |
| Complexion only if asked, in `appearance` only: neutral, once, never ranked or valued | question-trees.md tree 11 (BJ p88-89; HJH1 p159) |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes. Rising sign from the birth time; the rising navamsa changes about every thirteen
minutes, so it is used only on a stable time. Say which candidate planet was chosen and why. No dasha or transit step for
appearance.

## 4. Caveats

- Appearance is the lowest-confidence part: Weak, with the caveat sentence above, in the `appearance` section only.
- Tendencies, never measurements: no height in numbers, no weight (refused in `appearance` too), no age claim ("you look older"), no named body part,
  no scars or marks, and hair and eye colour are never given.
- Never name or predict caste, community, religion or ethnicity; the chart is not read for orientation or gender
  identity; never use it to pick or reject a real person.
- Constitution is symbolism only: nothing medical, no diagnosis, no organ.
- No fixed-age claim ("at 32 you will change"): periods are named by months and years, not by the person's age.
- The Moon-sign reading of temperament is a tendency; the person's account of themselves decides what fits.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5). Remedies are not part of this type.

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | the rising navamsa and the rising-sign sketch when the lagna class is `high` or `very high` (give the Moon-sign sketch); every unit on the lagna, its lord or a house carries `sensitivity` |
| unknown time | drop `core`, `appearance` and `growth` (lagna, house and dasha based) and the ranking; `temperament` stays only from the Moon's sign and star when `birth.moon_stable` is true (`create_report` checks it), otherwise it too is dropped; no timeline row beyond labelled monthly markers; the model keeps one house-free note section (the schema needs at least one section) that says what was dropped and why |
| any time | height, weight, complexion and any appearance claim outside `appearance`; a trait claimed from one text alone is graded Weak |
