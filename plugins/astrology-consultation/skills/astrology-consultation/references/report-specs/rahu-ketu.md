# Rahu-Ketu transit report spec (`rahu-ketu`)

The nodes' axis through the chart: which pair of houses it occupies and for how long, where it meets natal points and
how far the running dasha agrees. Library support for reading node transits is thin, and the report says so. Inside
the shared frame ([README.md](README.md)).

**Order (standard):** `windows` → `axis` → `contacts` → `fit`

Inputs: `birth`, the period asked about (default: the current axis stay). Model: `report_type: "rahu-ketu"`,
`depth: "standard"`, the frame fields. The `ranking` table ranks the axis themes by support (`item`, `support`, `why`,
`window`, `caution`). Required sentence in `scope`: "Library support for reading the nodes' transit is thin, so these
are tendencies only."

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | the axis stay (Rahu in one sign, Ketu opposite) with its dates as a timeline `chapter` row; a `window` row only where the running dasha agrees (`fit`) and names the dasha in its basis | Rahu sign changes → `get_transits` (`ingresses`, planet `Ra`); `get_outlook` (kind `ingress`) |
| `axis` | the two houses of the axis from the Moon and from the lagna (Rahu's side and Ketu's side), favourable or not from the Moon, and what the pair means in life | `get_gochara` (`house_from_moon`, `house_from_lagna` for `Ra` and `Ke`) |
| `contacts` | exact conjunctions of transit Rahu or Ketu with natal points, each dated to the month | `get_transits` (`slow_contacts`, transit `Ra` or `Ke`) |
| `fit` | does the running dasha involve the nodes, their dispositors or the houses of the axis; "no event-level timing is indicated" where nothing agrees | MD/AD → `get_dasha`; `get_outlook` (`dasha`, `contact` factors) |

Node aspects (owner decision 13, 2026-11-20): the axis and the conjunctions are stated as facts. The view that the
nodes aspect the 5th and 9th from their sign (LOL p87) appears only as one side of a labelled dispute inside `axis`, in a
unit with `claim_basis: "DISPUTED"`, graded Weak or Contradictory, with the other side beside it; never as a fact, never
in the summary, ranking, timeline or watch list. The engine computes no node aspect; count the signs from the engine's
node sign and say so. `spec_checks` enforces this.

Situation check: ask in `next_step` which area feels unsettled now. Sensitivity of every unit:
`get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Classical gochara is from the natal Moon; the nodes' favourable houses are those of the Sun: 3, 6, 10, 11 | PD XXVI.1-2 (p312); HPA p132 |
| PD gives no vedha for the nodes | PD XXVI.3-8 (p313-314) |
| A node gives the results of its house, the planets it joins, its dispositor and its star lord; the strongest dominates | LOL p357; HPA p72 |
| Rahu acts like Saturn, Ketu like Mars (Raman, in delegation) | HJH2 p124 |
| Node dignity is disputed: own and exaltation signs differ between sources | BPHS p573; LOL p89; PVR p46 (CR-X03) |
| Dispute, one side: "some" give the nodes a full aspect on the 5th and 9th; a modern introduction gives the same | LOL p87; SEERS p168 (not a rule source) |
| Dispute, other side: node aspects are school-dependent and omitted by default in this skill | vedic-natal.md (graha drishti), the skill's own rule |
| A transit never produces a major event without natal promise and dasha activation | HJH2 p119-122; HPA p134 |
| Node transit over natal points as a timing rule | not checked: no rule text found in this library (CRUX p424 mentions a Rahu transit over the natal Moon sign in one case study only) |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes (the engine default; true nodes only as an explicit choice), sidereal dasha years.
Contacts are conjunctions only: the axis already covers the opposition. Write the sign Cancer as "the Cancer sign": the shared medical word list (`medical_words.py`) refuses the bare
word, an accepted over-block.

## 4. Caveats

- Thin support: no unit is graded Strong; Moderate needs the dasha to agree (an `axis` unit graded Moderate names the running dasha in its basis; `spec_checks` enforces it).
- No fear framing: no disaster, sudden ruin, curse or "malefic attack" wording; Rahu and Ketu are restlessness and
  release, read as tendencies.
- No Kaal Sarp reading here (it is folded into the kundli, owner decision 9).
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | `axis` units from the lagna carry `sensitivity`; drop the lagna side when its class is `high` or `very high`; months only |
| unknown time | drop `axis` (houses), `fit` and the ranking; `contacts` keeps only labelled monthly markers to time-independent natal planets (the Moon only when `moon_stable`); `windows` becomes those markers |
| any time | the 5th and 9th aspect view only as the labelled dispute; a stay with no dasha agreement is a `chapter` row only |
