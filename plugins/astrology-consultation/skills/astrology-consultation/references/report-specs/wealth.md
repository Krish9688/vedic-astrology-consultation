# Wealth report spec (`wealth`)

How money comes and stays for the person, the stronger and tighter stretches, sudden-gain tendencies and choices.
Inside the shared frame ([README.md](README.md)). Method: [topic-career-money.md](../topic-career-money.md) §5, §5a and §6.
Work type and rank belong to the career report; this one covers income, retention, outflow and unearned gains.

**Order (standard):** `windows` → `pattern` → `retention` → `sudden` → `choices`

Inputs: `birth`. Model: `report_type: "wealth"`, `depth: "standard"`, the frame fields. The `ranking` table ranks the
money themes or the windows by support (`item`, `support`, `why`, `window`, `caution`).

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | three to five named windows, stronger and tighter, each with dates, a one-line basis and what it activates; the other sections point to them by name | network → `get_topic_network` (topic `finance`); activation → `get_activation`; MD/AD → `get_dasha`; Jupiter and Saturn on the 11th, 2nd or their lords → `get_transits` |
| `pattern` | how income arrives: the 11th, its lord and occupants, read with the 2nd, from the lagna and the Moon; benefic or malefic occupant as a tendency, never an accusation | 11th, 2nd, lords, occupants, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`) |
| `retention` | what stays: the 2nd and its lord; outflow and debt (12th, 6th, 8th) with their periods; higher income beside higher expense | 2nd and 12th lords → `calculate_birth_chart`; SAV of the 11th, 10th, 12th and lagna → `get_ashtakavarga`; lord periods → `get_dasha` |
| `sudden` | unearned and sudden gains by kind: legacy or gift (8th), speculation or prize (5th), easy money (11th), luck (9th); the best two scenarios with their signatures, "present, not active" when no period fits | 8th, 5th, 9th, 11th lords and occupants → `calculate_birth_chart`; activation of the signature planets → `get_activation`, `get_dasha` |
| `choices` | what to do in which window (build, save, wait, review); no new computation | from the sections above |

Situation check: ask in `next_step` (earning, saving or in debt; what the question is about). Sensitivity of every
unit and window: `get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Income: the 11th with its lord and occupants; the source from the 11th occupant or the 11th lord's associate | PD XVI.29; HJH2 p372-379 |
| Read gains with the 2nd ("the 11th necessarily comprises the 2nd"), and with the lagna, 9th and 10th, from lagna and Moon | HJH2 p393, p399 |
| Retention: the 2nd and its lord; a weak or debilitated 2nd lord aspected by malefics means strain | HPA p51 |
| Dhana signatures: lords of 1, 2, 5, 9, 11 linked in kendras or konas; 2nd-11th exchange; lagna lord in the 2nd with the 2nd lord in the 11th | HJH2 p373-374; HPA p60 |
| Two or more of the 2nd, 5th, 9th and 11th lords tied and strong give wealth, undone when a 6th, 8th or 12th lord ties to the group; results in those lords' periods | UKAL IV.28 p94 (a stated rule; the engine does not compute it, so check it by hand from the printed placements and say so) |
| Sarvashtakavarga: 11th above 10th, 12th below 11th, lagna above 12th | PD XXIV.38; HPA p103 |
| Outflow and debt: 12th (expense, fines), 6th (loans, disputes), 8th (sudden loss, shared money); losses in periods of the 11th lord joined with the 12th lord, and of the lagna, 4th and 9th lords in the 8th | HJH2 p393 |
| Benefic in the 11th: honest gains; malefic: more questionable sources (say it with caution; never accuse) | HJH2 p372 |
| Unearned gains by house: 8th legacies, gifts, insurance, pension, wills | HJH2 p78; LOL p176-177; PVR p80; BHRIGU p34 |
| 5th speculation and games of chance; 11th easy money; 9th sudden gain as luck | HJH1 p98, p211; LOL p177; HJH2 p266 |
| The 2nd lord in the 8th: Raman reads little earning while inherited or saved wealth goes; the old list reads legacies. Keep both and say they differ | HJH1 p93; HJH1 p98 |
| Signatures: 12th lord in the 8th; 2nd lord in the lagna with the 9th lord or the Sun; 2nd lord well placed in the 9th with the 9th lord in the lagna; 2nd and 4th lords together in the 4th | HJH2 p420; HJH1 p91; HJH1 p93-94; HJH1 p104 |
| Prize or speculation: 2nd lord well fortified in the 5th; 11th lord in the 5th (a gambler's losses if afflicted); Ketu in the 11th | HJH1 p92-93; HJH2 p370; HJH2 p375, PD VIII.28-33, PDK p103 |
| One-off windfall: lagna lord exalted in the 8th beside an exalted 2nd lord (one case); lagna lord in the 2nd, 2nd lord in the 11th, 11th lord in the lagna | HJH2 p400; HPA p51 |
| 8th lord by house, one modern author, graded Weak | BEHARI2A p98 |
| Counter-factors: the same 8th is sudden loss; an afflicted 5th or 11th lord turns speculation to loss; gains by dusthana lords tend to come through a mishap | HJH2 p370; LOL p327 |
| Sudden gains: only the periods of the planets that form the signature activate them; Raman calls house-by-house results very general | topic-career-money.md §5a, §6; HJH2 p372 |
| Dasha-bhukti lords in 3 and 11 or kendras from each other favour rise; 6/8 or 2/12 hinder | HJH2 p260, p364 |
| Transit Jupiter over the dasha and bhukti lords often starts the good results within a long bhukti | LOL p364-365 |
| An 8th-house gain usually follows an ending; never predict a relative's death to explain it | topic-career-money.md §5a (the skill's own rule) |

Grade for `sudden`: one placement is Weak; Moderate needs two independent signatures, a sound 2nd and 11th and a
matching period; never higher (topic-career-money.md §5a). A dhana signature on a weak 2nd and 11th passes through the
hands: read the base first.

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. One placement counts once. Income and outflow are both
described. Timing: the running dasha gives the event, a transit only confirms (timing.md §0).

## 4. Caveats

- No amounts, no figures, no "rich" or "poor" label.
- No advice to buy, sell, trade, bet or buy tickets; no "right time to invest"; never a reason to count on an inheritance
  or a win; no dates for a win (topic-career-money.md §5a, §8).
- A 6th-house loan or 8th-house loss is a tendency of the period, not a prediction of default.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | units on the 11th, 2nd, 8th or 5th carry `sensitivity`; windows in months; drop a section whose factor class is `high` or `very high` |
| unknown time | `windows` becomes at most labelled monthly markers of slow planets to time-independent natal planets; drop `pattern`, `retention`, `sudden` (all house-based) and `choices` if nothing is left; drop the ranking if no theme has support without houses |
| any time | `sudden` without a matching period is "present, not active" |
