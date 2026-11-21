# Jupiter transit report spec (`jupiter-transit`)

What Jupiter's movement through the chart opens up, sign by sign, read from the natal Moon and, separately, from the
lagna, and how far the running dasha agrees. A transit alone never gives an event: it confirms a period the dasha
already shows (timing.md §0, §3). Inside the shared frame ([README.md](README.md)).

**Order (standard):** `windows` → `moon` → `lagna` → `fit`

Inputs: `birth`, the period asked about (default: the next two years). Model: `report_type: "jupiter-transit"`,
`depth: "standard"`, the frame fields. The `ranking` table ranks the sign stays by support (`item`, `support`, `why`,
`window`, `caution`). Required sentence in `scope`: "A transit alone never gives an event: it only confirms what the running period already shows."

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | one named stay per sign Jupiter occupies in the period, with its dates (retrograde returns kept as their own stay); each stay is a timeline `chapter` row; a `window` row only where the running dasha agrees (`fit`) and names the dasha in its basis | sign changes → `get_transits` (`ingresses`) or `get_outlook` (period `year`, kind `ingress`); exact contacts with natal points → `get_transits` (`slow_contacts`) |
| `moon` | the classical frame: Jupiter's house from the natal Moon, favourable (2, 5, 7, 9, 11) or not, vedha, condition and the bindus of the transited sign; what that house means in life | `get_gochara` rows (`house_from_moon`, `vedha_by`, `condition`, `bav`, `sav`) on a date inside each stay; `get_ashtakavarga` |
| `lagna` | the lagna frame, shown separately and never added to the Moon frame: the house from the lagna and the houses Jupiter aspects (5th, 7th, 9th) | `get_gochara` (`house_from_lagna`); `get_transits` (`transit_sign_aspects`) |
| `fit` | does the running dasha activate what Jupiter touches: the MD and AD lords, their houses and Jupiter's own role; Jupiter over the dasha or bhukti lords; "no event-level timing is indicated" where nothing agrees | MD/AD → `get_dasha`; `get_outlook` (`dasha`, `contact` factors); network if a topic is asked → `get_topic_network`, `get_activation` |

Situation check: ask in `next_step` which area the question is about and what is happening now. Sensitivity of every
unit: `get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Classical gochara is counted from the natal Moon's sign | PD XXVI.1 (p312); HPA p132 |
| Jupiter's favourable houses from the Moon: 2, 5, 7, 9, 11 | PD XXVI.2 (p312) |
| Vedha cancels a favourable transit; the PD table is used (HPA differs for Mercury and Venus, CR-V07) | PD XXVI.3-8 (p313-314); HPA p133-134 |
| Own or exalted sign does no harm; debility or an enemy's sign voids a good transit | PD XXVI.30-32 |
| Many bindus make even a 6th, 8th or 12th transit good | PD XXVI.41 |
| Some count transits from the lagna; practice is split, so the lagna frame is shown apart | LOL p362 |
| Jupiter's houses improve, scaled by natal strength; in a long bhukti good results start when Jupiter stimulates the dasha and bhukti lords | LOL p364-365 |
| A strong dasha lord transiting a friendly sign promotes the house it transits from the lagna | PD XX.34-35; LOL p359-361 |
| Jupiter acts in the middle of a sign | BJ XXII.6; PD XXVI.25 |
| A transit never produces a major event without natal promise and dasha activation | HJH2 p119-122; HPA p134 |
| Jupiter touches some favourable house on most days, so a favourable house alone is no window | timing.md §3 (PRED-F2, the skill's own check) |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. Moon frame first; the lagna frame beside it, never summed.
Dates of a stay are the engine's sign-change dates; a retrograde return is its own stay. Write the sign Cancer as "the Cancer sign": the shared medical word list (`medical_words.py`) refuses the bare
word, an accepted over-block.

## 4. Caveats

- A favourable Jupiter is a tendency of support, never a promise of marriage, a child, money or a post.
- No sun-sign or Moon-sign text that would fit anyone: tie every line to a house, a natal point or a dasha.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | `lagna` and `fit` units carry `sensitivity`; drop `lagna` when the lagna class is `high` or `very high`; months only |
| unknown time | drop `moon` (houses from the Moon), `lagna` and `fit`; `windows` keeps only labelled monthly markers of Jupiter to time-independent natal planets; the ranking is dropped |
| any time | a stay with no dasha agreement is a `chapter` row only, never a `window` |
