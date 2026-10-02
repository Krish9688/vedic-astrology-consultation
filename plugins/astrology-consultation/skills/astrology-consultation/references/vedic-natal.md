# Parashari natal analysis: houses, lords, strength, yogas

Parashari/Vedic branch only. Never apply these sign-lordship rules inside a Lal Kitab reading (see
[lal-kitab-method.md](lal-kitab-method.md)). Run `scripts/chart_facts.py` on supplied positions first; it derives houses,
lordships, aspects, dignity, combustion, D9/D10, dispositor chains and the Phaladeepika XV tests without hand arithmetic.
How to weigh everything below is in [synthesis-method.md](synthesis-method.md).

## 1. Evidence roles (what each layer can and cannot do)

| Layer | Main evidence | Can justify | Cannot do alone |
|---|---|---|---|
| Validity | Consistent chart, convention, reliable time | Which conclusions are evaluable | Prove astrology works |
| Promise | Lagna/lord; topic house, lord, karaka and their links | A supported potential or a mixed/weak one | Guarantee an event |
| Delivery conditions | Functional role, dignity, dispositor, aspects, conjunctions, combustion, sandhi | How the potential is expressed or obstructed | Turn strength into benefit |
| Confirmation | Relevant stable varga; same network from Moon/Sun | Domain-specific reinforcement or limitation | Create an absent D1 event |
| Activation | MD/AD and their relationship | Which networks are foregrounded | Fix the exact form |
| Trigger | Verified transit, optional Ashtakavarga | Candidate windows inside activation | Produce a major event alone |

Order of work used by the sources: settle the lagna, lagna lord and its dispositor, and the Moon's strength first
(a weak lagna or lagna lord can stop even a fine raja yoga delivering) [LOL p367]; identify functional benefics and
malefics for the lagna "as soon as the dasas are determined" [HPA p44]; then judge houses, then yogas, then dasa, then
transit [HPA p44–134; LOL p367]. Classical texts put longevity first [PD XIII.1; HPA p36]; this skill does **not**
produce longevity or death judgements (see [communication.md](communication.md)).

## 2. Houses

| House | Working meanings |
|---|---|
| 1 | Body, vitality, agency, direction; lagna lord links the person to the house it occupies |
| 2 | Accumulated resources, speech, family, food, early education; retention of wealth |
| 3 | Initiative, skills, communication, younger siblings, short journeys; courage |
| 4 | Home, property, vehicles, mother, foundational schooling, inner contentment |
| 5 | Intelligence, learning, children, creativity, mantra, speculation, past merit |
| 6 | Work/service, competition, debt, disputes, illness symbolism, maternal relatives |
| 7 | Partnership, spouse, contracts, business dealings, public, travel away from home |
| 8 | Disruption, shared/inherited resources, research, hidden matters, longevity doctrine |
| 9 | Fortune, dharma, teachers, father (baseline), higher learning, long journeys |
| 10 | Work, status, responsibility, visible action, authority |
| 11 | Gains, income, networks, elder siblings, fulfilment |
| 12 | Expenditure, loss, separation, foreign residence, retreat, sleep, liberation |

Kendras 1/4/7/10 manifest; konas 1/5/9 support; 6/8/12 describe difficult processes with constructive uses; upachayas
3/6/10/11 improve with time and effort — planets in 3 and 6 start impaired and improve, those in 10 and 11 start good
and get better [LOL p291]. Treat any house as a lagna to read its sub-matters (bhavat bhavam) and read relatives from
their karaka's sign (father from the Sun, mother from the Moon…) [PD XV.20–24]. Name the reference point and stop after
one derivation step. Two derived-house rules from Light on Life [LOL p154–156]: a lord placed as far from its own house as
that house is from the lagna *perpetuates* the house's results (6th lord in the 11th: one ailment after another; 4th
lord in the 7th: one qualification after another); a lord in a good house from the lagna but 6/8/12 from the house it
rules first obstructs, then restores, the house's inanimate matters while more lastingly straining its living ones
(5th lord in the 10th: intelligence prospers, children are a concern) — with stated exceptions when the lord still
aspects its own house.

## 3. Functional nature (lordship) — the most common source of error

- Trine lords are always auspicious; lords of 3/6/11 cause trouble; 8th lord is bad unless also lagna lord (Sun/Moon as
  8th lord still good); 2nd and 12th lords are neutral and follow their associations [HPA p42–43; PD XX.41].
- Kendradhipati dosha: natural benefics owning kendras lose beneficence, natural malefics owning kendras improve.
  Jupiter and Venus as kendra lords are the most affected, Mercury less, the Moon less still [HPA p42–43; PD XX.50–51].
  Apply it as a qualification, not a blanket disaster.
- Yogakaraka (one planet owning a kendra and a kona): Saturn for Taurus/Libra, Mars for Cancer/Leo, Venus for
  Capricorn/Aquarius [LOL p315]. A kendra lord related to a kona lord by any of the five relationships
  (exchange, conjunction, mutual aspect, mutual kendra, mutual trine [PD XV.30]) forms raja yoga even if each also owns a
  bad house [PD XX.45].
- Nodes give the results of the house they occupy, the planets they join, their dispositor and their star lord; the
  strongest influence dominates [LOL p357; HPA p72]. "Rahu acts like Saturn, Ketu like Mars" is used by Raman in
  delegation [HJH2 p124].
- Keep five questions apart: what does the planet signify naturally; what does it rule here; how capable is it; what
  supports or burdens delivery; capable of what, *for this question*. Strong Saturn can deliver work *and* obligations.

## 4. Strength and condition

**Dignity** (conventional; BJ II, PD II; cross-checked in v2.2):

| Planet | Exalted | Debilitated | Own |
|---|---|---|---|
| Sun | Aries | Libra | Leo |
| Moon | Taurus | Scorpio | Cancer |
| Mars | Capricorn | Cancer | Aries, Scorpio |
| Mercury | Virgo | Pisces | Gemini, Virgo |
| Jupiter | Cancer | Capricorn | Sagittarius, Pisces |
| Venus | Pisces | Virgo | Taurus, Libra |
| Saturn | Libra | Aries | Capricorn, Aquarius |

Nodes: no default dignity (sources disagree). Moolatrikona degree ranges and compound friendship need a checked table
if decisive; natural friendship follows BJ II.16–17 (as coded in `chart_facts.py`). Natural relationship outranks
temporary [PD IV.10]; Raman compounds them (friend+friend = best friend, friend+enemy = neutral) [HPA p15–16].

**Combustion** (LOL Table 9.1, image-checked): Mercury 14° (12° retrograde), Venus 10° (8°), Mars 17°, Jupiter 11°,
Saturn 15°. It damages a planet's *outward* significations and the houses it rules, while often brightening inner
qualities (Sun–Mercury intellect) [LOL p297–298]. Combust benefics lose beneficence; combust malefics gain
maleficence; closer is worse; approaching is worse than separating [LOL p298]. Jupiter's aspect on a combust Mercury
greatly reduces the damage [HJH2 p357]. Raman's older line "utterly powerless" [HPA p16–17] is harsher — CR-V05.

**Retrogression** strengthens whatever the planet signifies, good or bad; it is not "karma" or automatic benefit
[LOL p299–300]. PD's "debilitated + retrograde = exalted" and "exalted + retrograde = debilitated" [PD IV.4, IX.20] are
read by LOL as cautions, not literal rules (CR-V06).

**Avasthas** temper, never reverse [LOL p300–301]. **Sandhi**: a planet on a bhava junction gives little of that house
[PD XV.13; HPA p75]. **Dispositor**: see synthesis-method §3. **Kendra strength**: lagna full, 7th ¾, 10th ½, 4th ¼
[PD IV.8]. **Jupiter** is the strongest warder-off of evil [PD IV.11]; its aspect repeatedly rescues houses in Raman's
cases [HJH2 p46; PM2 p20].

**Numerical strength.** Shadbala has six parts — sthana (positional: dignity, vargas), dig (directional), kala
(temporal), chesta (motional), naisargika (natural) and drik (aspectual) [EXT BPHS 27; PD IV lists the sources].
Use it to say *how able* a planet is to deliver, never *what* it delivers; engines implement it differently (see inputs.md — a >1 rupa spread is common), so a borderline pass/fail is never decisive; a high-Shadbala functional malefic
delivers its lordship more fully. Ishta/kashta phala (from the same engine) separate helpful from harmful capacity.
Shadbala minima for "strong" in rupas: Sun 6.5, Moon 6, Mars 5, Mercury 7, Jupiter 6.5,
Venus 5.5, Saturn 5 [PD IV.22–24]. Read only supplied values with units; never invent them; a Shadbala total that
includes dignity is not an extra vote. Ashtakavarga: house SAV > 30 good, 25–30 middling, < 25 weak, except 6/8/12
[HPA p103; BJ p141]; a planet's transits over zero-bindu signs in its own table are difficult [HPA p99–101].
Ashtakavarga has two layers: each planet's own table (BAV, 0–8 bindus per sign) for that planet's transits and
significations, and the sum (SAV, total 337) for houses. Kakshya (3°45′ sub-divisions of a sign) refine when in a
transit the bindu is delivered [PM2 p54–55]. Reduction methods (trikona/ekadhipatya shodhana) change the numbers:
ask which table the engine returns and never mix reduced and unreduced values.

## 5. Aspects and associations

Graha drishti: all planets aspect the 7th; Mars also 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th, counted inclusively
by sign [HPA p34–36; LOL p283]. PD records that some count only the 7th as fully effective (IV.9) — use all, note it
if decisive. Node aspects are school-dependent and omitted by default. Do not mix Jaimini or Tajika aspects into
Parashari judgements [HPA p34]. Aspect quality depends on the planets' natures and functions, not on the angle; Raman
rejects "squares/oppositions are bad" [HPA p36]. Exact-degree aspects to a cusp dominate [HJH2 p303].

Association blends meanings: a house lord in another house blends the two houses and may become the cause of that
house's result (7th lord in 2nd: money through spouse/partner) [LOL p293–294]. Yoga effects transfer to a planet
joining the yoga-formers [HJH2 p356]. Mutual aspect of the 7th lord and Venus holds a marriage together [HJH2 p39].
Hemming (kartari) by malefics weakens a house or planet; by benefics strengthens it [LOL p293; PD XV.6].

## 6. Yogas: define, verify, check bhanga, check delivery

For each material yoga: exact definition → actual constituents → their functional role and strength → cancellation or
modification → link to the question → whether its planets' dashas run at a usable age [LOL p310]. A software yoga
list is a list of candidates. Yogas describe principles, not literal promises [LOL p310–312]; many "fail" because the
planets are weak, cancelled or never get their period.

- **Raja yoga (dharma-karma adhipati):** kona lord + kendra lord related; 9th–10th strongest, 4th–5th valuable
  [LOL p313–314]. Place matters: a raja yoga in the 12th is not fully enjoyed, in the 6th suffers bhanga, 12th from the
  Moon carries seeds of fall [HJH2 p357–366]. Yogas raise the *degree* of success, not the *type* of career
  [HJH2 p288]. Mutual periods of Saturn and Venus are said to break raja yogas [HJH2 p364].
- **Pancha mahapurusha:** Mars/Mercury/Jupiter/Venus/Saturn in own or exaltation sign in a kendra (PD also allows
  kona per LOL); qualifies only with a strong dispositor; graded by repetition from three lagnas [LOL p311–313].
- **Gaja Kesari / Adhi / Amala / Budhaditya / Chandra-Mangala / Lakshmi / Saraswati / Viparita:** use the definitions
  in LOL ch. 10 [LOL p318–327]; Budhaditya works only when configured with lagna or 5th and both planets are strong
  [LOL p319]; Viparita needs at least two dusthana lords in other dusthanas and often comes through a mishap
  [LOL p327].
- **Kemadruma** (no planets 2nd/12th from the Moon) is said to neutralise good yogas [HPA p59]; benefics in upachayas
  from lagna or Moon override it [BJ XIII.9].
- **Neechabhanga** moderates debility; it does not guarantee effortless success. Verify the specific clause used.
- **Kuja dosha** is not in the authoritative texts; it is extremely common; cancels when both partners have it, when
  Mars is own/exalted (disputed), with Moon–Mars, and fades after ~28–30 [LOL p329–331]. Never a verdict on a marriage.
- **Kala Sarpa** is not classical, has no agreed effect and no known cancellation [LOL p331–333]; mention only if asked,
  as a disputed modern combination.
- **Bhanga of good yogas** exists but has no general rule (Saravali/Jataka Parijata examples) [LOL p333–334]. Yogas do
  not cancel each other; good and bad run side by side (see CR-V01).
- Rank vs type: judge *what kind* of work/relationship from houses and karakas; judge *how far it goes* from yogas.

## 7. Nakshatras

Use for a concrete job: Moon's Vimshottari starting point, a qualified behavioural texture, or the star-lord modifier
(synthesis-method §3). 27 equal sectors of 13°20′ from sidereal Aries; 4 padas of 3°20′.

| Lord | Nakshatras |
|---|---|
| Ketu | Ashwini, Magha, Mula |
| Venus | Bharani, Purva Phalguni, Purva Ashadha |
| Sun | Krittika, Uttara Phalguni, Uttara Ashadha |
| Moon | Rohini, Hasta, Shravana |
| Mars | Mrigashira, Chitra, Dhanishtha |
| Rahu | Ardra, Swati, Shatabhisha |
| Jupiter | Punarvasu, Vishakha, Purva Bhadrapada |
| Saturn | Pushya, Anuradha, Uttara Bhadrapada |
| Mercury | Ashlesha, Jyeshtha, Revati |

A pada and the D9 sign come from the same longitude: one channel. KP sub-lords, Nadi chains and tara-bala are separate
methods; name and verify before use.

## 8. Optional Jaimini / argala lens (separately named module) — full module: [jaimini.md](jaimini.md)

Rasi drishti: movable signs aspect fixed signs except the adjacent one; fixed aspect movable except the adjacent one;
dual aspect the other duals. Chara karakas need a declared 7/8-karaka scheme. Primary argala: influence from 2/4/11,
obstruction from 12/10/3. Arudha (image) and lived resources are not interchangeable. Keep this module labelled and
never pool its aspects with graha drishti. [carried over from v2.2 natal.md]

## 9. What the classical texts say that this skill will not state as fact

Death timing, longevity spans, widowhood, "certain" disease, child sex, caste/gender judgements and "destruction"
language appear throughout PD, BJ, HJH2, HPA and PM2 (each source map lists them in its §8). Report them only as "the
text says…" when the user asks about doctrine, never as a forecast. See [communication.md](communication.md).
