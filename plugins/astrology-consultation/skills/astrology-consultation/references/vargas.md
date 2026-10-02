# Divisional charts: applications, conflicts and reliability

## What a varga is

A varga reassigns portions of natal zodiacal signs under a specified rule. It is not another observed sky at birth. Do not compute combustion, retrograde motion, physical angular distance or a new Moon phase from its graphic. Carry physical conditions from the actual natal positions and evaluate varga dignity separately.

Phaladeepika III reports differing views on Navamsa's equivalence to rasi/bhava and gives traditional effect fractions. These are not statistical probability weights. The modern topical-varga approach is especially explicit in P.V.R. Narasimha Rao's textbook, chapter 6. This package adopts D1 anchoring and selective confirmation as **DESIGN**, while recognizing schools that give Vargas greater autonomous interpretive importance. [P3, PVR]

## Use table

“Use” below means traditional/practitioner application, not scientifically demonstrated capability. Only use the parts stable under input uncertainty.

| Varga | Main application | D1 anchor and practical question | Limit / when not to use |
|---|---|---|---|
| D1 Rasi | Overall natal structure | All topics, lagna and topic network | Do not reduce to a single placement |
| D2 Hora | Wealth/resources | 2/11: acquisition versus retention | Two-sign and expanded methods differ; don't treat every D2 as twelve-house wealth analysis |
| D3 Drekkana | Siblings, effort/courage | 3/11: relationship or initiative | Method variants; do not infer a sibling's fate from this alone |
| D4 Chaturthamsa | Property and residence | 4: acquisition, move or quality of home | Cannot identify an address or legal title |
| D7 Saptamsa | Children/parenthood | 5 and its lord/karaka | Cannot diagnose fertility or establish pregnancy, child sex, number or safety |
| D9 Navamsa | Planetary dignity, dharma, partnership | D1 planet capacity; 7 for partnership | Not a replacement chart starting at marriage or a universal birthday |
| D10 Dasamsa | Work, responsibility, achievement | 10 and related income/service houses | Does not identify a guaranteed occupation, employer or promotion |
| D12 Dvadasamsa | Parents/lineage | 4/9 baseline, Sun/Moon | Not evidence of parents' medical conditions or life span |
| D16 Shodasamsa | Vehicles, comforts/enjoyment | 4 and Venus | Not an accident detector |
| D20 Vimsamsa | Spiritual practice | 5/9/12 and relevant karakas | No certification of enlightenment or religious worth |
| D24 Chaturvimsamsa / Siddhamsa | Learning/education | 4/5/9, Mercury/Jupiter | No guaranteed admission, score or degree |
| D27 Saptavimsamsa / Bhamsa | Strengths/weaknesses | Relevant D1 capacity and response | Higher sensitivity; not a clinical personality assessment |
| D30 Trimsamsa | Adversity/vulnerabilities | D1 topic under strain | Classical unequal portions differ from harmonic D30; not a disaster/diagnosis engine |
| D40 Khavedamsa | Maternal-line inheritance, auspicious/inauspicious effects (per BPHS 6–7, EXT) | 4 and Moon; secondary only | 45′ segments: needs a very reliable birth time; odd signs counted from Aries, even from Libra [BPHS ch. 6, PDF p92]. Never a verdict |
| D45 Akshavedamsa | Paternal-line inheritance, character/conduct (per BPHS 6–7, EXT) | 9 and Sun; secondary only | 40′ segments; movable signs from Aries, fixed from Leo, dual from Sagittarius [BPHS ch. 6, PDF p93]. Omit unless time is rectified |
| D60 Shashtyamsa | Broad karmic interpretation in some schools | Secondary philosophical context only here | Normally omit without robust time/method stability; never factual past-life claims |

The main topical correspondences are cross-referenced in [PVR] chapter 6, table 11 and [BP6] chapters 6–7; exact interpretive boundaries above are this package's safeguards.

## D1 and D9

### Cross-checking supplied standard D9/D10

When D1 degrees and a claimed standard Parashari D9/D10 are both supplied, cross-check the **nominal mapping** before interpreting the derived chart. This is a finite arithmetic check, not an ephemeris calculation or proof of birth-time stability. Use exact fractions or sufficient precision; do not round across a boundary.

For a planet or ascendant at `d` degrees within its D1 sign:

- D9: take zero-based segment `floor(d / (10/3))`. For a movable sign start counting at that sign; for a fixed sign start at its ninth sign; for a dual sign start at its fifth. Move forward by the zero-based segment, wrapping after Pisces.
- D10: take zero-based segment `floor(d / 3)`. For odd-numbered zodiac signs (Aries=1), start at that sign; for even-numbered signs start at its ninth. Move forward by the segment.
- Segments are start-inclusive/end-exclusive. At exactly 3°20′ in a sign, D9 uses the second segment, not the first. Apply the same rule separately to the ascendant.

These rules validate only the stated standard D9/D10 convention. If the supplied chart names another method, do not overwrite it with these rules. If its method is unstated, expose the discrepancy and ask which convention produced it. Do not extrapolate this arithmetic to every varga, especially unequal D30.

Distinguish **D1 placement** from **D9 dignity of the same planet**, and from **D9 houses/lords** when using a declared house-based varga method. A strong D1 planet with poor D9 condition may support external opportunity with weaker sustainment or satisfaction; do not assert that outcome automatically. A weak D1 planet with strong D9 condition can suggest resources for development without erasing the D1 difficulty. In either case, explain the topic-specific link and keep the conflict visible.

Vargottama means the same sign in D1 and D9 in its standard usage. It does not mean exalted. A vargottama debilitated planet retains debilitation in both charts. Repetition indicates consistency under that lens, not unconditional goodness, and the two placements are derived from the same longitude. Never count D9, pada and vargottama as three independent confirmations.

For marriage, separate formation, relationship quality and continuity. D9 dignity alone cannot date marriage or describe a spouse's exact appearance, profession or behavior. For career, D9 may qualify a planet while D10 provides the topic-specific lens; no need to analyze D7 or D20.

## Reliability before detail

For equal divisions, a Dn segment is 30°/n. This is zodiacal arc, **not a universal number of clock minutes**. Ascendant speed varies with latitude/time, and each planet moves at a different rate. D60's half-degree portions do not mean every planet changes D60 sign every two minutes. The often-used two-minute estimate concerns an approximate average ascendant segment crossing, not a reliability guarantee.

D30 is a warning against applying `longitude × n mod 360` to every varga. Classical unequal Trimsamsa uses portions of 5/5/8/7/5 degrees in odd signs and 5/7/8/5/5 in even signs, with assigned rulers. Verify the specific mapping rather than reconstructing it from its name. D2, D3 and D60 also have consequential method alternatives.

Classify each relevant chart:

- **Stable:** the facts used stay the same across the documented uncertainty interval and chosen method.
- **Partly stable:** some planetary signs survive, but ascendant/houses or key planets change. Use the invariant portion only.
- **Untested/unstable:** no sensitivity evidence or material changes. Do not use its changing facts to confirm the event.

The engine's sensitivity grid gives the evidence: a varga lagna classed robust, or whose first change lies beyond the
stated time uncertainty, is *Stable*; one that changes inside it is *Partly stable* at best (planet signs may still
hold — check them separately).

An untested varga can be discussed as a **conditional interpretation of supplied nominal facts**, but it must not increase confidence as though stability were established. State that condition before relying on its meaning, not only at the end. If nominal D9/D10 mapping is wrong, quarantine that supplied position; corrected arithmetic does not certify the rest of the chart.

With an approximate birth time, D9 planetary dignity may be stable even when D9 ascendant is not. Assess them separately. A chart's high division number is a risk indicator, not an automatic blanket prohibition. Birth-time error also shifts the Moon's dasha balance; see [timing.md](timing.md).

## Conflict procedure

1. Confirm the charts use consistent inputs and the intended method.
2. Compare the same proposition: D1 career opportunity versus D10 career condition; do not confuse status with contentment.
3. Explain support and contradiction without canceling both by slogan.
4. Preserve the D1-supported broad theme but lower exact-event/manifestation confidence where the varga contradicts it.
5. If the contradictory varga is unstable, label it unusable; do not pretend a contradiction was resolved in favor of the preferred result.

Never add higher Vargas simply to break a tie. Check the facts, reduce precision, or leave the question unresolved.

## Presenting a chart

Caption every chart with its division, method, orientation, source/status and relevant stability limit. North Indian format fixes houses; South Indian format fixes signs. Put the ascendant and a readable abbreviation key beside the chart. Match every plotted label against the supplied positions table, including nodes and empty cells. A nominal chart may be shown as supplied with an explicit untested-status caption; this does not grant it confirming weight.

D9/D10 and D1 share birth inputs. Explain what differentiated condition the varga adds rather than calling it an independent measurement. If a graph and table disagree, quarantine the conflicting placement and identify the source needed to resolve it. See [visuals.md](visuals.md) for the figure contract and text alternative.
