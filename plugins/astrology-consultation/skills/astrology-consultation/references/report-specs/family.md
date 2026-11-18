# Family report spec (`family`)

Home, mother, father and (only if asked) siblings, and the windows for home and property. It describes the person's
own experience of these ties, never another person's health, life span or fate. Inside the shared frame
([README.md](README.md)). Method: [topic-home-family-children.md](../topic-home-family-children.md) §1 and §3.

**Order (standard):** `windows` → `home` → `mother` → `father` → `siblings`

Inputs: `birth`, and in `next_step` whether siblings are to be read. Model: `report_type: "family"`, `depth: "standard"`,
the frame fields. `siblings` is read only when the person asked: otherwise it is listed in `dropped` with the reason
"not asked". The `ranking` table ranks the home and family themes by support (`item`, `support`, `why`, `window`,
`caution`); `window` is given for home themes only. Children are not part of this report (see the children report).

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | two to four named windows for **home and property only** (settling, buying, renovating, moving, selling are separate events); each with dates, a one-line basis and what it activates. A window or timeline row may name a parent or sibling for neutral events only (a visit, a move, a plan, work), never for health, harm, loss or a pressure stretch | home network (below) → `get_topic_network`; activation → `get_activation`; MD/AD → `get_dasha`; Jupiter and Saturn on the 4th, its lord, Mars or Venus → `get_transits` |
| `home` | comfort and contentment at home, land and vehicles, the 4th lord with the lagna lord, Venus (comfort), Mars (land), the Moon; strain such as an enemy planet with the 4th lord or Rahu or Saturn on the 4th; the 12th for moving; D4 only as a labelled conditional reading | 4th, its lord, occupants, aspects → `calculate_birth_chart`, `prepare_consultation` (derived facts, chart_facts `aspected_by`); D4 → `get_divisional_chart` (4) |
| `mother` | the person's experience of the mother or mother figure: closeness, distance, support, responsibility; the 4th, its lord and the Moon, with the Moon's sign as a second lagna | houses, lords, Moon → `calculate_birth_chart`, `prepare_consultation`; D12 → `get_divisional_chart` (12) only on a robust time (see 2) |
| `father` | the same for the father or father figure: the 9th, its lord and the Sun, with the Sun's sign as a second lagna | houses, lords, Sun → `calculate_birth_chart`, `prepare_consultation`; D12 as above |
| `siblings` | only if asked: the relationship with younger siblings (3rd, its lord, Mars) and elder siblings or friends (11th, its lord, Jupiter); never whether a sibling exists | houses, lords → `calculate_birth_chart`; D3 only as a labelled conditional reading → `get_divisional_chart` (3) |

Sensitivity of every unit and window: `get_birth_time_sensitivity`.

### The custom networks

The engine has presets only for marriage, career, finance, relocation and education. Each network below is built with
`get_topic_network` and a `planets` list, frozen before any dates are looked at; the engine flags every entry as unsourced
and the report says so in `appendix.method`.

| Network | Planets | Used for |
|---|---|---|
| home | the 4th lord, the Moon, Mars, Venus (the table in topic-home-family-children.md §1: 4th lord, Moon for home, Mars for land, Venus for vehicles and comfort) | `windows` through `get_activation`; the `home` section |
| mother | the 4th lord and the Moon | the `mother` section only (who the period lords touch, by their natal roles) |
| father | the 9th lord and the Sun | the `father` section only |
| siblings | the 3rd lord and Mars (younger), the 11th lord and Jupiter (elder) | the `siblings` section only |

`get_activation` is run for the home network only. It is not run for the mother, father or siblings networks: a window
tied to a parent's planets would read as the timing of a parent event, which this report never gives.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Home: the 4th lord with the lagna lord in a good house, or in a kendra or kona, gives comfort and property | HPA p52; PD XVI.13 |
| The 4th lord and Venus well placed in the lagna and the 4th: vehicles and luxuries | HPA p52; PD XVI.13 |
| The 4th lord in the 12th: ancestral property at risk (a tendency, never a loss) | HPA p52 |
| The 4th lord with an enemy planet: property disputes; Rahu or Saturn with the 4th and its lord: old or worn dwellings | PD XVI.14; topic-home-family-children.md §1 |
| Acquisition, renovation, moving and selling are different events; 4th with 12th can mean moving or spending, not foreign property | topic-home-family-children.md §1 |
| Mother: the 4th (father: the 9th), its lord and the Moon (the Sun), with benefics placed favourably from the karaka | PD XVI.10; HJH2 p187-204 |
| Judge the 9th only after the Sun, the 9th lord, their influences and the running periods; never apply the rules literally | HJH2 p190, p204 |
| The relative's sign from the karaka as a second lagna: say the reference point, then stop after one step | PD XV.21; topic-home-family-children.md §1 |
| D12 is for parents and lineage; it is not evidence of a parent's medical condition or life span; it is used only on a robust time and is a labelled conditional reading | vargas.md (D12 row) |
| Younger siblings from the 3rd, its lord and Mars; elder from the 11th and Jupiter; counts from the navamsa or Ashtakavarga are traditional and unreliable | HJH2 p383-392; PD XXIV.9 |
| A running dasha gives the event; a transit only confirms | timing.md §0 (the skill's own ladder) |

The classical parent rules include death and illness rules (PD XVI.10; HPA p44, p52). They are never stated.

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. The 4th and 9th are taken from the lagna; the Moon and Sun
views are the second lagna named above. D12 and D4 are always conditional: D12 is used only when `time_reliability` is
exact and the D12 lagna class from `get_birth_time_sensitivity` is not `high` or `very high`; otherwise it is dropped
and listed. Siblings are discussed only when asked and never inferred.

## 4. Caveats

- The report describes the person's experience of a parent or sibling: closeness, distance, responsibility and
  support. It states: "No parent or sibling is forecast beyond visits, moves, plans and work."
- Never a parent's or sibling's illness, health, accident, danger, misfortune, frailty, care needs, life span, old age,
  mourning or death, and never the loss of a relative: refused dated or not. A forecast about a relative, with or
  without a date, is allowed only in the fixed shapes below ("Your brother may change jobs in 2028."). A window or
  timeline row may name a parent or sibling for those neutral events only, never for health, harm or loss.
- Never confirm or rule out that a sibling exists, nor read a sibling's fate.
- Never read a parent's character as a fact about that person: it is the native's experience and the chart's themes.
- No pregnancy, fertility or children timing here; children belong to their own report.
- Property: no legal title, no address, no price and no advice to buy or sell; a window says what the period activates.
- Fixed forecast shapes. A relative is a mother, father, parent, mom, mum, dad, ma, pa, brother, sister, sibling, aunt,
  uncle, cousin, niece, nephew, grandparent or other grand-relative, in-law, step-relative, relative or family member.
  A sentence whose subject or possessor is a relative, or he, she, they, his, her or their, passes only if the whole
  sentence is exactly:
  `<Relative> <MODAL> <PHRASE>[ <TIME>].`
  - `<Relative>`: "Your <relative>", "Your <relative> and you", or he, she, they.
  - `<MODAL>`: may, might, could, would, is likely to, are likely to.
  - `<PHRASE>`: visit you; visit your home; come to stay with you; stay with you for a while; move house; move to a new
    city; move abroad; move closer to you; move for work; travel for work; travel with you; go on a holiday; change
    jobs; start a new job; be promoted; retire; plan a family gathering; host a family gathering; plan a trip; help you
    with the move; help you with your home; get married; study abroad; graduate.
  - `<TIME>` (optional): in <Month> <YYYY>; in <YYYY>; between <YYYY> and <YYYY>; from <YYYY>; later in <YYYY>; during
    the <Planet> sub-period; during the <Planet> period.
  No other clause and no extra word. Anything else about a relative, present or past tense included, is written from
  the person's side ("you ..."): "a relative may appear only in a fixed forecast shape (see family.md); otherwise write
  it from your side ('you ...')". A sentence with "you" as its main subject that mentions a relative is allowed ("You may
  see more of your mother in 2028.", "You learned your love of home from your mother."), unless it also has a clause
  with he, she, they or a relative as its subject. The shape rule reads every sentence and label piece (text is cut at line breaks and colons; quotes, brackets and bullets
  are stripped) that has a relative as its subject anywhere in it ("In 2029 your father may ..."), a bare relative (Mum,
  Dad, Grandpa, Nana ...) or he, she, they; a relative as the object, and a sentence with "you" as the subject, are not
  shape-read and rely on the medical and death gate below. Known limit: the shapes over-block anything else about a relative; widen the PHRASE list only through review.
- Harm layer, kept as the second rule: a sentence where a relative word and a harm word sit in one clause (the list is
  `_HARM` in `render_report.py`) is refused, "you" sentences included ("You may see your mother in hospital."). It refuses a dated row, watch line, ranking window or unit timing that names a relative only when
  it also carries a harm word (a pressure row naming a relative counts), and any harm word in the mother, father or
  siblings section. A harm word missing from the list gets through (a known limit, noted in the code).
- Medical and death gate (every spec report, every string, whoever it is about): the checker refuses health, illness, doctors,
  hospitals, treatment, injury, accident, death, dying, funeral, lifespan, longevity, body-part and similar wording. Error:
  "health and death are not read in this practice; such predictions can harm the reader and are not good for their health".
  It is a word and phrase list (`_FORBID` in `render_report.py`), the floor for "you" and object sentences; a missing synonym
  gets through.
- Parashari only: no Lal Kitab readings, scapegoat chains or rin remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | D12, D4 and D3 (list in `dropped`) when the D4 or D3 lagna class is `high` or `very high` (D12: when its own lagna class is), and always D12 unless the time is exact and robust; units on the 4th, 9th or 3rd carry `sensitivity`; windows in months |
| unknown time | `windows` becomes at most labelled monthly markers of slow planets to time-independent natal planets; drop `home`, `mother`, `father`, `siblings` (house and lord based) and the ranking; the Moon-based mother note only if `birth.moon_stable` is true; the model keeps one house-free note section (the schema needs at least one section) that says what was dropped and why |
| not asked | `siblings` |
| any time | any window for a parent or a sibling; D12 as a confirmation |
