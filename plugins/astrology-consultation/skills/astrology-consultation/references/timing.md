# Timing engine: dashas, transits, annual charts

Contents: [0. The timing ladder (how a window is earned) — read first](#0-the-timing-ladder-how-a-window-is-earned--read-first) · [1. Vimshottari: identify the significators first](#1-vimshottari-identify-the-significators-first) · [2. Reading a dasha–bhukti pair](#2-reading-a-dashabhukti-pair) · [3. Transits (gochara): triggers inside an activated period](#3-transits-gochara-triggers-inside-an-activated-period) · [4. Parashari annual chart (Tajika / varshaphala) — separate from Lal Kitab](#4-parashari-annual-chart-tajika--varshaphala--separate-from-lal-kitab)
[5. Building a window (short form of §0, with a worked report shape)](#5-building-a-window-short-form-of-0-with-a-worked-report-shape)
[6. Temporal modes (carried over from v2.2)](#6-temporal-modes-carried-over-from-v22)

Timing answers "when is the natal promise foregrounded?". It never creates a promise. Output a **window with its
reasons** ("the strongest activation is X–Y because A, B and C converge"), graded Strong/Moderate/Weak/Contradictory/
Unknown per [synthesis-method.md](synthesis-method.md). Never read current sky positions from memory; use supplied
data or a calculation tool (with the privacy disclosure in [inputs.md](inputs.md)).

## 0. The timing ladder (how a window is earned) — read first

Research behind this: `docs/ASTROLOGER-CONSULTATION-RESEARCH.md` (R2). Keep **promise** ("the chart can deliver X")
and **activation** ("X is foregrounded now") as separate statements in every answer.

**Step 0 — precision budget.** Every dasha date moves by about **n × 365.25 × v ÷ 800 days per minute** of birth-time
error, where n is the full length (years) of the dasha running at birth and v the Moon's speed in arcminutes per minute
of time (≈0.5–0.6; so roughly n ÷ 4 days per minute, e.g. 5 days for Venus) [R2-TP1; PVR]. The engine's sensitivity grid
gives the exact figure. The ayanamsa and year-length
convention move dates too; name the ones the data used — 360-day years run ~4 months earlier than sidereal-solar years
for a person in their early twenties (inputs.md).

| Birth time | Usable layers | Finest window to state |
|---|---|---|
| Unknown / ±2 h | Moon-based transits; MD if the Moon's nakshatra is stable | a year or more |
| ±15–30 min (remembered, rounded) | MD, AD (edges ± months) | half-year |
| ±5 min (documented) | + PD (edges ± 1–4 weeks) | a quarter; a month only with full convergence |
| Checked against 3–5 dated past events | + PD with confidence | a month; a 1–2-week "most concentrated" band only if a station/exact contact, PD and annual chart coincide |

Sookshma and deeper levels never give event dates (they are shorter than the date error) and explain everything in
hindsight [LOL p354; R2-TP1].

**Steps.**
1. Define the event (a datable event vs a process). Processes get activation bands only.
2. State the promise class ([consultation-reasoning.md](consultation-reasoning.md) §3). Weak promise → "if it happens,
   the most supportive period is…".
3. **Freeze the significator network before scanning dates** (house, lord, occupants, aspecting planets, karaka, the
   varga lord; at most two Jaimini indicators). Nothing may be added later to make a window work [R1-P8].
4. **Primary — MD/AD**: pairs with both lords in the network, then one; grade confluence (§2); drop pairs implausible
   for age and context. Output 1–3 activation bands. None → "timing support in this horizon is weak" — do not rescue
   it with fast transits.
5. **Peak inside a band — slow transits** (§3): contacts to the MD/AD lords' natal positions first, then network
   planets, then the network's signs; one frame (lagna for events, Moon for experience). A retrograde loop over one
   point is **one episode**; a station within a few degrees of a key point marks its peak. Transits show *when*, not
   *which way* — direction comes from the natal roles [R2-TP3, TP5].
6. **Secondary confirmation**, each counted once: a pre-chosen Jaimini sign dasha variant; the Tajika year lord or
   muntha lord (only from a supplied or calculated return chart) being the AD lord or a network planet. Disagreement is reported.
   **Secondary nakshatra dashas (rule for step 6).** Vimshottari is the default clock (BPHS 46.2-5) and stays
   primary. At most one secondary dasha clock (Yogini, or a BPHS ch. 46 conditional system such as Ashtottari) is
   used, chosen and named before any date is examined; it counts once, as one secondary confirmation, is never pooled
   with Vimshottari and never rescues a window Vimshottari does not give. `get_dasha_applicability`
   (`astro applicability`) reports which ch. 46 conditions hold: information, not a reason to switch clocks. State
   overlaps as such (BPHS gives no rule for choosing), name the reading where the texts differ
   ([contradiction-register.md](contradiction-register.md) CR-V23, CR-V24), and treat a condition that flips within
   the birth-time window as Unknown. The engine computes no periods for the conditional systems.
7. **Supporting only** (quality or fine placement, never occurrence): Ashtakavarga bindus of the transiting planet
   (quality: easy vs strained), double transit on the network (true most of the time — label it), eclipses/nodal
   contacts ("sensitised for about six months", not a timer), PD inside an earned band [R2-TP7–TP9].

   **Engine support for steps 3-7** (facts only). `get_topic_network` (`astro network --topic …`) builds the step-3
   network: Raman's (a)-(g) list plus the topic extras (marriage, career, finance, relocation, education; children is
   theme-only and never laid over dates), each entry with its source and a sha256 hash. Build it before any date is
   seen and pass it back unchanged: `get_activation` (`astro activation --network …`) refuses an edited network. Per
   AD (or PD) segment it lists the period lords' roles from lagna and Moon (from chart_facts), D9/D10 and dignity, and
   the contacts, Ju/Sa sign stays (with BAV/SAV) and station episodes that touch a period lord or the network. Variant
   entries and unsourced extras are flagged, not merged. `astro retro --event career:2019-05 …` is the local-only
   §8 calibration check ([consultation-reasoning.md](consultation-reasoning.md) §8): "consistent with N of M" against
   networks frozen first. Nothing is stored, and calibration is not proof.
8. **Show restraint even when finer windows exist**: give the broad activation and **at most one** "most
   concentrated" window (plus, if genuinely distinct, one secondary). Never list a run of pratyantardashas as
   separate bullets — the person needs the shape of the period, not the software table.
9. **Earn granularity**: half-year = MD/AD band + one slow contact; quarter = + one independent confirmation;
   month = + a station/exact contact on a period lord + PD agreement + documented birth time. Never a day.
10. **Say it naturally**: "The whole of … is active for this. It concentrates around … because … . After … it fades."
   Then the counter-evidence and what would move the window.

**30-day questions** [R2-TP15]: give the MD/AD/PD context first; if no slow contact, station or annual-month
activation falls inside the 30 days, give a *texture* outlook (what the period emphasises, better moments for
initiatives) and say plainly that no event-level timing is indicated. Without transit data for the month, say the
monthly layer is unknown rather than guessing.

## 1. Vimshottari: identify the significators first

For the house that carries the question, list the planets able to give its results. Raman uses the same list for every
house [HJH2 p20–21, p196, p258, p375, p432, p464]:

(a) the house lord · (b) planets aspecting the house · (c) planets in the house · (d) planets aspecting the lord ·
(e) planets associated with the lord · (f) the lord of the same house counted from the Moon · (g) the karaka.

Add topic-specific candidates from the topic file (e.g. marriage: dispositors of the 7th lord in rasi and navamsa,
Venus, the Moon, the 2nd lord's dispositor, 9th/10th lords "if earlier dashas are fruitless" [HJH2 p25–26, p31;
PM2 XX.65]; children: lagna lord, 5th lord, Jupiter and their navamsa lords [PM2 XIX.83]).

**Intensity grades** [HJH2 p21, p258]:

| Dasha lord | Bhukti lord | Result for that house |
|---|---|---|
| significator | significator | "par excellence" — main window |
| non-significator | significator | limited |
| significator | non-significator | small |

**Eliminate by age and plausibility**: drop dashas that fall in childhood or very late unless the chart indicates late
events; within the chosen dasha drop too-early bhuktis; choose the strongest remaining lord by position, aspect and
lordship [HJH2 p31–35, p462]. Results due in childhood periods go to parents [LOL p358].

## 2. Reading a dasha–bhukti pair

1. **What the dasha lord activates** — ten channels [LOL p340–341]: its yogas; natural nature; house occupied and planets
   joined; houses/planets aspected; planets joining/aspecting it; the same in its role as house lord; houses it owns;
   houses owned by its associates; houses influenced by its **dispositor** (often overlooked); its karakatva. Everything a
   text says about the planet applies in its period [PD XX.21].
2. **Its condition** sets the tone: strong lords give the good of their houses, weak ones the bad [PD XX.2–20]. A
   vargottama lord gives a good dasha; combust or debilitated gives mixed [PD XX.22]. A weak planet's good results come
   "in dreams and thoughts" [LOL p342]. A natural malefic's dasha keeps a flavour of struggle even when functionally
   good [LOL p346].
3. **The bhukti lord's relationship to the dasha lord**:
   - Houses from the dasha lord: the bhukti gives results of the house it occupies counted from the dasha lord; 6/8/12
     from it is unhappy [PD XX.29]. LOL finds this holds mainly when the bhukti lord is also afflicted [LOL p356–357].
   - Mutual 3/11 or kendras: rise; mutual aspect: raja-yoga results [HJH2 p260, p364].
   - Mutual 6/8 or 2/12: unfavourable [HPA p76; HJH2 p364, p473].
   - A dasha shows its results mainly in bhuktis of planets related to it by the five relationships [PD XX.44].
   - Kendra-lord dasha with kona-lord bhukti (or reverse) is good [PD XX.42, 49].
4. **Confluence or conflict**: list the bhukti's influences on the matter, mark each positive or negative, see whether
   they agree with the dasha; if they conflict, the stronger dominates [LOL p354–355].
5. **Within the period**: planets in prishtodaya signs deliver late in the dasha, ubhayodaya in the middle, sirshodaya
   early [PD XX.33; BJ XXII.5]; a mixed dasha can turn good in its second half [PD XX.57]; a dasha can split by halves
   [HJH2 p360]. Rahu joined to a good planet can turn evil at the end of that planet's dasha [PD XX.39].
6. **Do not go deeper than justified.** Five dasha levels "make everything explainable with hindsight and almost
   nothing predictable with foresight"; stay with dasha, bhukti and transit [LOL p354]. Pratyantar only when parent
   activation, birth-time stability and a trigger all support it.

Arithmetic: MD years — Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17 (120).
AD = MD × AD-lord years ÷ 120, starting with the MD lord [PD XXI.2]. Balance at birth from the Moon's remaining
nakshatra portion [PD XIX.2–3]. Year length/convention must be the one the table was produced with; never re-derive
dates by hand when a calculated table exists. Periods nest: check containment and gaps before interpreting.

## 3. Transits (gochara): triggers inside an activated period

- **Frames.** Classical gochara is from the natal Moon only [PD XXVI.1; HPA p132]. LOL prefers the lagna and notes practice
  is split [LOL p362]; PD itself uses lagna-based transit of the dasha lord in XX.34–35. Say which frame you use; do not
  count one contact twice from two frames.
- **Good houses from the Moon** [PD XXVI.2]: Sun 3, 6, 10, 11; Moon 1, 3, 6, 7, 10, 11; Mars/Saturn 3, 6, 11;
  Mercury 2, 4, 6, 8, 10, 11; Jupiter 2, 5, 7, 9, 11; Venus all but 6, 7, 10; nodes like the Sun.
- **Vedha** cancels a transit's result (Sun–Saturn and Moon–Mercury exempt) [PD XXVI.3–8; HPA p133–134]. The two
  sources' tables differ for Mercury and Venus (CR-V07); state the one used. Ignoring vedha is called the commonest
  cause of wrong transit predictions [HPA p134; PM2 XXII.54].
- **Condition modifies transit**: in own/exaltation sign a planet does no harm even in a bad house; debility, enemy
  sign or combustion voids good transits; aspects by benefics/enemies modify [PD XXVI.30–32]. Many Ashtakavarga bindus
  make even 6/8/12 transits good [PD XXVI.41]; Moon over natal sign needs > 4 bindus to help [HPA p133].
- **Dasha-lord transit**: a dasha lord strong at birth transiting own/exalted/friendly signs promotes the house it
  transits (from lagna); one weak at birth damages it [PD XX.34–35; LOL p359–361]. Transit Moon in 3/6/10/11/trine/7th
  from the dasha lord is good [PD XX.36].
- **Month-level**: a good bhukti fruits when the Sun enters the bhukti lord's exaltation sign, or Jupiter transits
  there; a bad one when the Sun transits its debility/enemy sign [PD XX.38] — LOL tested it and found it close but not
  exact [LOL p361–362]. Sun/Mars act early in a sign, Jupiter/Venus mid, Saturn/Moon late [BJ XXII.6; PD XXVI.25].
- **Jupiter–Saturn** (houses occupied and aspected: the engine's `transit_sign_aspects`, from lagna and Moon): Jupiter's houses improve, Saturn's suffer unless in own/exaltation,
  scaled by natal strength; in long bhuktis good results start in the year transit Jupiter stimulates the natal dasha
  and bhukti lords, bad ones when Saturn does [LOL p364–365] ("binary method"). K. N. Rao's double-transit practice
  (both contacting the event network) is a modern extension not in this library; label it if used.
- **Topic transits**: marriage — Jupiter over the 7th lord's rasi or navamsa sign or their trines; Venus, lagna lord,
  Moon-sign lord or 7th lord over the 7th/its lord's sign [PM2 XX.66]; the sign of (lagna longitude + 7th lord or 7th
  bhava longitude) activated by Jupiter [HJH2 p26, p462]. Children — Jupiter over the 5th lord's sign/navamsa sign from
  lagna, Moon and Jupiter, choosing the one with most bindus [PM2 XIX.84].
- **Sade sati** (Saturn over 12th/1st/2nd from the Moon) is a broad experience lens, needs dasha confluence, and is
  milder the second time [LOL p363–364; HPA p130]. Never a verdict by itself.
- A transit never produces a major event without natal promise and dasha activation [HJH2 p119–122; HPA p134].

### 3a. Personal outlook (daily, weekly, monthly, yearly)

Build it only from `get_outlook` (or `astro outlook --period day|week|month|year --on DATE`): it returns dated,
chart-specific factors, each with an id (F1, F2 …) and a source — running Vimshottari and Yogini periods, gochara from
the Moon (PD XXVI good houses, vedha, condition) with the lagna frame beside it, sade sati, sign changes, stations,
exact slow-planet contacts and, for a day or week, the Moon's transit. `get_gochara` gives the table for one date.
  Gochara rows carry the bindus of the transited sign (the planet's own BAV and the SAV, BPHS tables): they qualify a
  transit, never time or predict on their own.
  Year/month outlooks also list **vedha intervals** (dated spans in which a favourable transit is obstructed, sampled at
  the sign changes of Sun, Mars, Mercury, Jupiter, Venus, Saturn; PD table; Moon vedha omitted) and **station-near-natal
  episodes** (a station within 3° close, 7° wide of a natal point, one episode per retrograde loop; the orb is a
  convention, not a classical rule). All are triggers inside an activated dasha period only, never predictions alone.
  Every factor carries a `layer`: **event** (exact slow contact with a natal point, a station near one, a slow sign
  change, sade sati), **texture** (faster planets' sign changes, bare stations, and for a month or longer the
  chandrashtama spans [CRUX p99-100] and the Moon's daily tara from the birth star — low weight) or **backdrop** (dasha,
  gochara snapshot, vedha).
- **Written monthly or quarterly outlook** (report type `outlook`, 28-92 days): start from
  `render_report.py --outlook-draft outlook.json` (dasha first, then event-level factors or the texture-only statement,
  texture last), write the life meaning around those facts, and check with `--outlook outlook.json`: every unit names
  its factor ids, every sentence about a planet carries a chart anchor (a house from your Moon or lagna, a natal point,
  a dasha), a window without an event-level factor says "no event-level timing is indicated" and makes no event claim,
  and the client text stays within two pages.
- Every statement names the factor ids behind it and the tradition (Parashari gochara; Yogini is a secondary dasha).
  Lead with the running dasha, then the transits that touch its lords and houses (§0, §3); a favourable transit in an
  unfavourable period is a minor note.
- No sun-sign or Moon-sign text that would fit anyone: if the period has few factors, say it is a quiet period.
- A daily outlook is mostly the Moon's transit: keep it short and low-stakes. Never forecast health crises, deaths,
  accidents or legal outcomes (SKILL.md non-negotiable 6).
- Grade each item (Strong … Unknown) and keep the computed facts visibly separate from the interpretation.

## 4. Parashari annual chart (Tajika / varshaphala) — separate from Lal Kitab

Raman's simplified solar-return: chart for the Sun's return to its natal longitude; annual dashas (Sun 110, Moon 60,
Mars 32, Mercury 40, Jupiter 48, Venus 56, Saturn 4, Rahu 5, Lagna 10 days); judge the **natal dasha and gochara
first, then the annual chart, and combine** [HPA p128–131]. He himself calls this a snapshot and says his separate
*Varshaphal* book is more correct (not in this library), and the return table uses an outdated year length
[HPA p128]. Use only with a calculated return chart.

**Calculated Tajika year** (`get_tajika` / `astro tajika`, PVR ch. 27–28, 31; reproduces PVR Examples 118 and 122):
return moment at the birthplace, day or night year, muntha, harsha bala, the five year-lord candidates with their
Tajika aspect on the annual lagna, sahams and Mudda dasha. The year lord is printed only when the aspect tiers settle it
(pancha vargeeya bala is not computed); otherwise say "year lord undetermined" and list the shortlist. PVR notes that
Tajika has no basis in Parasara or Jaimini and gates it by the natal promise [PVR p377–378]: it confirms a window the
natal dasha and transits already show, counted once (§0 step 6), never creates one. Mudda dates follow PVR's stated
definition (a solar day = the Sun moving 1°); his own Example 122 fits a clock day about two days earlier, so quote a
Mudda boundary to the week, not the day.

## 5. Building a window (short form of §0, with a worked report shape)

1. Define the event class and horizon **before** looking at dates ("formal marriage", not "relationship activity").
2. State the natal promise and its grade (synthesis-method).
3. List significators (§1). Find dasha–bhukti pairs inside the horizon with an intensity grade. None → say timing
   support is weak in this horizon; do not rescue it with fast transits.
4. Inside those pairs, look for slow-transit contacts to the same network (§3). Keep the frame explicit.
5. **Converge**: the window where activation + trigger repeat the same network is the primary window.
   Rank multiple windows by activation strength, confirmation and contradiction. Retrograde passes are one contact
   sequence, not three events.
6. Widen edges for birth-time, dasha-convention and manifestation uncertainty. Do not treat a boundary date as a switch
   for lived experience, and never report an exact event day.
7. Say what would move the window: a verified transit date, a birth-time correction.

Report shape: "The main window is late 2027 to mid-2028. That is Venus–Jupiter: Venus is the 7th lord's dispositor and
Jupiter aspects the 7th; transit Jupiter crosses the 7th lord's navamsa sign in the same months. Before that, Saturn's bhukti looks like preparation and delay
rather than the event."

## 6. Temporal modes (carried over from v2.2)

- **Past**: if history is disclosed, call it retrospective interpretation; explain the period network at that time
  (not today's transits). For blind testing, record windows before seeing events; misses stay misses.
- **Present**: state the analysis date and the verified running MD/AD; separate the dasha backdrop, the bhukti
  channel and the transit trigger; external circumstances before conditional inner experience.
- **Future**: major periods, a few meaningful transitions, realistic alternatives, calibrated windows. Farther out means
  wider uncertainty about exact form. A period boundary is not a promised end to difficulty.
- For long reports keep one authoritative period table ([reports.md](reports.md)); split any window that crosses an AD
  boundary by lord.

Specialist modules need their own verified inputs and are otherwise omitted: Tajika details beyond §4's calculated
year, muhurta/tara, Jaimini sign dashas, Kalachakra (PD says use it only when the Moon's navamsa lord is strong and
calls nakshatra dasha "always the best" [PD XXII.30]), numerology.

