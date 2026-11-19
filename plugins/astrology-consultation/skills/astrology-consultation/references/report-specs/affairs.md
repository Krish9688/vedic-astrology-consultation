# Affairs and fidelity report spec (`affairs`)

The person's own tendencies toward ties outside a committed relationship: desire, restlessness, privacy, and what steadies
them. Own chart only. Said as a tendency ("the chart shows a strong pull toward ..., steadied by ..."), never as conduct.
Inside the shared frame ([README.md](README.md)). Method:
[topic-relationships-marriage.md](../topic-relationships-marriage.md) §10, with §8 and §9 limits. Owner decision 2026-11-19.

**Order (standard):** `pulls` → `pressures` → `private` → `steadiers`

Inputs: `birth`. Model: `report_type: "affairs"`, `depth: "standard"`, the frame fields. Same adult gate as intimacy: built
only when the birth date shows 18 or over on the report date (`spec_checks`, `adult_errors`). There is no `windows`
section, no period and no timeline row: the checker refuses any timeline row and any year or month name. The `ranking`
table ranks the tendencies by support (`item`, `support`, `why`, `caution`); no window.

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `pulls` | the 7th house, its lord and Venus: desire in general and ties beyond the marriage; occupants, aspects, the lord's dignity, in rasi and navamsa | 7th, lord, Venus → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`); navamsa → `get_divisional_chart` (9) |
| `pressures` | the named pressures, each with its book and said as present, partly present or absent (absent is a real answer): Saturn or Mars aspecting Venus in the 7th, the 7th lord or Venus with a node under a malefic aspect, Venus with Mars and Mercury afflicted, the 2nd, 7th and 10th lords together in the 10th | aspects and conjunctions → `calculate_birth_chart`, `prepare_consultation` |
| `private` | the 12th house and its lord for the private side, read as in the intimacy report; restlessness against privacy | 12th, lord → `calculate_birth_chart` |
| `steadiers` | the counter-factors with equal weight: the same Mars-Venus pair as a loving, faithful bond when well placed; Jupiter's aspect; a strong lagna lord; the choice stays with the person | aspects → `prepare_consultation`; sensitivity → `get_birth_time_sensitivity` |

Periods are not read here (owner decision: no periods); no dasha tool is in the map.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| The 7th covers the spouse and also desire in general and ties beyond the marriage | LOL p167 |
| Saturn or Mars aspecting Venus in the 7th, or the 7th lord or Venus with a node under a malefic aspect | HJH2 p14 |
| Venus with Mars and Mercury when afflicted; Mars with Venus as pleasure-seeking; the same pair is loving and faithful when well placed | HJH2 p19 |
| The 2nd, 7th and 10th lords together in the 10th | JP2 XIV.4 |
| The 12th for the private side; Jupiter's aspect and a strong lagna lord steady it | HJH2 p422-423 |
| The classical moral labels are not repeated | topic-relationships-marriage.md §10 |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes. Grade: **Weak** on one factor; **Moderate** only when the 7th, Venus and the
navamsa agree (the unit's `basis`, or a ranking row's `why`, names the 7th, Venus and the navamsa: checked); **Unknown**
where the birth time leaves the houses open; never Strong, never certain.

## 4. Caveats

- `depth` is required (no legacy form), same adult gate as intimacy, Unknown only on an approximate or unknown birth time. Conduct forecasts in any form are refused (you'll, going to, expect, awaits, on the cards, love triangle). Periods, planet periods, seasons and ages are refused; no periods table in the appendix; a capitalised given name as subject or possessor is refused. In a full kundli the relationship section gets this gate and the adult gate.

- Scope states: "This reads your own tendencies only. It does not predict conduct, it gives no verdict, and it says
  nothing about any partner."
- Never "you will have an affair", and no form of it (may, might, are likely to ...): refused even when negated, because
  it is a claim about the person. Nothing about a real partner's conduct or fidelity (the shared fidelity check and the
  type gate both refuse it). No certainty words, no verdicts, no moral labels, no period or window wording.
- Plain words over labels: "outside the marriage", "pull", "restlessness". The word "affair" is allowed only inside a
  tendency or a negated caveat.
- Added T11.32: conduct claims in more forms ("tend to", "inclined to", "do cheat", "you sleep around") and verdicts on the person
  ("You are faithful", "disloyal", "a cheater", "a two-timer", "a philanderer") are refused, hard. Partner and third-person conduct is
  deny-by-default: "your <anyone>" followed within four words by a conduct or desire word (mistress, paramour, flirts, texting, sees
  someone, lied ...) is refused unless <anyone> is on the closed own-trait list (same list as intimacy). Certainty words as in
  intimacy (unavoidable, certain, beyond doubt, bound to, written in your chart, absolutely). "A tie outside the marriage is
  unavoidable" and "The pull is certain" are refused. Known limit: word lists; a missing synonym gets through, and an own-trait
  noun missing from the list is over-blocked.
- The adult gate by birth date (above). Under 18: no report.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | the navamsa reading when its lagna class is `high` or `very high`; every unit on the 7th, 12th or D9 carries `sensitivity` |
| unknown time | drop all house-based sections and the ranking; the model keeps one house-free note section that says what was dropped and why |
| under 18, or no readable birth date | the whole report: it is not built |
| any time | any period, window, year, month or date; any statement about another person's conduct |
