# How to reach a judgement: synthesis, evidence and conflict

This is the core of the skill. Every other reference feeds this procedure. Source tags: `[PD]` Phaladeepika,
`[BJ]` Brihat Jataka, `[HJH2]`/`[HPA]` B. V. Raman, `[LOL]` Light on Life, `[PM2]` Prasna Marga II, `[LK]` Lal Kitab,
`[DESIGN]` this skill's own policy. Page citations resolve through [source-index.md](source-index.md).

## 1. The senior-practitioner sequence

Work through these questions in order. Most answers need only a few of them in the written reply, but skipping one
silently is how single-placement predictions happen.

1. **What exactly is being asked?** Event, quality, timing or decision? Over what horizon? Rewrite a vague question as
   a testable proposition ("formal marriage within 2027–2028", not "love life").
2. **Which houses carry it?** Primary house plus supporting houses (topic files list them). Also count the same house
   from the Moon: every Raman worked chart repeats the analysis from Chandra Lagna [HJH2 p29–77]. Use the Sun as a
   third reference for career and father [HJH2 p253; BJ p148]. A yoga or promise repeated from lagna, Moon and Sun is
   very strong; from two, above average; from lagna only, average [LOL p310, p317–318].
3. **Which lords?** For each relevant lord state: owns A and B → sits in C → linked to D (conjunction, aspect,
   exchange, dispositor) → therefore connects these topics. Functional nature comes from lordship, not natural
   benefic/malefic status (section 3 of [vedic-natal.md](vedic-natal.md)).
4. **Which karakas?** Natural significator of the matter (Venus for spouse, Jupiter for children, Sun for father…).
5. **Apply the triad test** (section 2): house, lord, karaka — strong, afflicted, or mixed.
6. **Occupants and aspects**, weighed by their functional role for this lagna, not by name alone.
7. **What strengthens or damages them?** Dignity, combustion, retrogression, dispositor condition, hemming,
   sandhi, nakshatra lord, navamsa placement.
8. **Yogas and cancellations** — verified definition, constituents, bhanga, and whether the yoga's planets get a dasha
   at a usable age [LOL p310].
9. **Divisional confirmation** — the relevant varga only ([vargas.md](vargas.md)).
10. **Dasha activation** → 11. **Transit trigger** → 12. **Lal Kitab layer**, if in scope
    ([lal-kitab-method.md](lal-kitab-method.md), [timing.md](timing.md)).
13. **Convergence**: does the theme repeat through independent channels? (section 4)
14. **Strongest evidence, secondary evidence, strongest contradiction.**
15. **Timing window** supported by activation plus trigger.
16. **What remains uncertain**, and what would change the reading.

### 1a. Full-reading coverage check (for topic reports and full readings)

Before writing, confirm each factor was looked at *or deliberately skipped with a reason* (a focused question may
skip many). None of them is a verdict alone; conclusions need two or more independent channels (§4).

| # | Factor | Where | Skip when |
|---|---|---|---|
| 1 | Chart context, input quality, birth-time sensitivity | inputs.md | never |
| 2–3 | Lagna, lagna lord (condition first: a weak lagna lord stops good yogas delivering) | vedic-natal §2–4 | never |
| 4–5 | Moon (mind, Moon chart, dasha seed); Sun (status, father, Sun chart) | step 2 above | never for Moon |
| 6–7 | Relevant houses and their lords, functional roles | topic file; vedic-natal §3 | never |
| 8 | Dignity, combustion, retrogression, dispositor, sandhi | vedic-natal §4 | — |
| 9–10 | Aspects and conjunctions (graha drishti only in this note) | vedic-natal §5 | — |
| 11 | Yogas: verified definition + bhanga + dasha at a usable age | vedic-natal §6 | none present |
| 12 | Nakshatras (Moon's star, star-lord of key planets) | vedic-natal §7 | not decisive |
| 13 | Relevant varga only (D9 always for dignity; D10/D7/D4/D2/D3/D12… by topic; D16+ only with a rectified time) | vargas.md | time unstable |
| 14 | Shadbala / Ashtakavarga, only from engine output | vedic-natal §4 | not supplied |
| 15–16 | Vimshottari dasha, bhukti, pratyantar | timing.md | no period table |
| 17 | Current transits (engine data only), vedha, AV bindus | timing.md | no transit data |
| 18 | Jaimini karakas/arudha as a separate labelled note | jaimini.md | not asked / would double count |
| 19 | Lal Kitab layer as a separate note | lal-kitab-method.md | not in scope |
| 20 | Supporting vs contradicting factors, recorded disputes | §5; `kg.py contradictions` | never |
| 21 | Timing convergence (promise → dasha → transit → annual) | timing.md | untimed question |
| 22 | Source check for any rule you cite | `kg.py sources` / `search.py` | — |
| 23 | Overall synthesis with grades | §4 | never |

"Promise first, then timing": the natal chart shows *what* is possible; dasha shows *when* it is foregrounded;
transit shows *which part* of that period. Raman gives natal positions and dashas primary weight and transits
secondary, "like catalysts" [HJH2 p26, p121–122]; transits activate natal promise but cannot change its nature
[LOL p360].

## 2. The triad test (house, lord, karaka) — Phaladeepika XV

This is the working engine for every life area [PD p182–191, XV.1–6, 25; LOL p281–289].

**A house prospers** when it is occupied or aspected by benefics, by its own lord, or by lords of good houses, without
malefic contact — and those planets are strong (not debilitated, combust, or in an enemy's sign). A malefic that
*owns* the house helps it: lordship beats natural nature here [PD XV.1; LOL p285]. Raman applies the same logic in
practice: Saturn aspecting the 7th does not delay marriage when Saturn is the 7th lord; hemming by the lagna lord and
7th lord is "toned down" [HJH2 p32–33].

**A house suffers** when house, lord and karaka are each devoid of strength: hemmed by malefics, joined or aspected only
by malefics or enemies, malefics in the 4th/8th/12th or 5th/9th from them, or the lord in 6/8/12 (unless in its own
sign) [PD XV.3–6; LOL p287–288]. `scripts/chart_facts.py` prints these tests for every house.

**Grading.** All three strong → the matter is enhanced; all three weak → the matter is impaired; anything between needs
judgement [LOL p302]. The verdict is "evident" only when several conditions coincide [PD XV.6] — this is the classical
statement of confluence.

**Mixed results add; they do not cancel.** A strong house with a weak lord gives *both* good and bad experiences of
that house, e.g. delightful children and grief over one child [LOL p279]. One strong protective factor can prevent the
worst without restoring happiness: Jupiter's aspect on the 7th from the Moon prevented a break-up "although life
itself is miserable" [HJH2 p46]. Strength sets the limit of delay or denial: a strong 7th lord and strong Venus
"cannot push it off too far" even with Saturn in the 7th [HJH2 p32, p60] — this is how to distinguish **delay from
denial**.

**Dusthana inversion.** Benefics promote a house and malefics decay it — reversed for the 6th, 8th and 12th, where a
malefic increases enemies/danger/loss per BJ's note but "destroys the evils" per PD's verse. The two sources disagree
on direction; see CR-V04 in [contradiction-register.md](contradiction-register.md) before relying on it.

## 3. Weighing: what dominates

Use these to decide which factor carries a conclusion. They are source rules, not a scoring formula.

- **Relevance beats prominence.** A condition of the topic's own house/lord/karaka outweighs an impressive but
  irrelevant exaltation elsewhere. [DESIGN, consistent with HJH2 p204: no single planet decides a bhava alone.]
- **Lordship over natural nature** for the houses a planet owns [PD XV.1]. Lagna lordship overrides a co-owned dusthana
  [PD XV.10]. A dusthana lord in its *other* own sign gives that house's results, not the dusthana's [PD XV.29].
- **Strength is capacity, not intent.** Strength says how much a planet can deliver; benefic/malefic nature and
  lordship say what it delivers [LOL p294]. A strong 8th lord gives *more* 8th-house events.
- **The dispositor is the planet's "soul".** A strong dispositor lifts a weak planet; an exalted planet with a
  debilitated dispositor under-delivers; a debilitated planet with a debilitated dispositor is the worst case
  [LOL p294–296]. Raman uses the same logic: malefic Mars aspecting Venus in Mars's own sign *strengthens* Venus
  [HJH2 p218].
- **Nakshatra lord as hidden modifier.** A planet in the star of a node, a maraka or the 6th/8th lord is weakened; in
  the star of a strong planet it is strengthened; a dasha lord gives its star lord's results [HJH2 p134, p352–363].
- **Dignity scale.** Good results scale exaltation full → moolatrikona ¾ → own ½ → friend ¼ → enemy little →
  debilitation/combust nil; reversed for malefics and bad-house lords [PD IV.7, XX.30; BJ p223–224].
- **Sandhi.** A planet at a house junction cannot give that house's results even when exalted [PD XV.13–14;
  HJH2 p255; HPA p75]. Only apply with a declared bhava-madhya method.
- **Specific over general.** Specific placements outrank generic lagna/sign delineations [LOL p402–403]; house-by-house
  cookbook results "must not be applied literally" [HJH2 p12, p190; HPA p50].
- **Chart tenor.** Where a theme dominates the whole chart (e.g. renunciation), read other combinations in its key:
  a strong 4th lord gives moral development "instead of a Rolls Royce" [LOL p418].
- **Subjective vs objective.** When natural benefics favour a matter but temporary malefics (lords of bad houses)
  also touch it, natural indications tend to prevail inwardly and temporary ones outwardly: accidents may occur,
  but the person is not disheartened [LOL p304].
- **A strong malefic has two faces**: great material benefit through its yogas and serious damage elsewhere
  (Monroe's exalted retrograde 8th-lord Saturn) [LOL p380].
- **Context and plausibility.** Fit results to the person's station, age, society and "physical possibility"
  [HPA p75; PD XXI.84; HJH2 p32]. Results due in childhood periods go to parents and guardians [LOL p358].
- **Weak planets deliver in dreams.** A powerless planet's promised good is experienced in thought, not events
  [BJ VIII.22 p127; LOL p342].

## 4. Convergence and the evidence hierarchy

### 4.1 Count channels, not labels

A prediction must emerge from convergence, never from one placement. Before calling something convergent, collapse
dependencies — each item below is **one** channel, however many names it carries:

- a conjunction and the yoga named after it; a yoga label and its constituents;
- D1 sign, navamsa sign, pada and vargottama of the same planet (same longitude);
- Shadbala and its dignity component; an Ashtakavarga total and its planet tables;
- MD and AD (nested periods); two reports of the same Saturn transit;
- Rahu and Ketu (one axis);
- a Lal Kitab reading of a planet-in-house and a Parashari reading of the *same* planet-in-house (same fact, two
  traditions) — see 4.4.

Distinct channels are things like: the house's own condition; its lord's condition; the karaka; the same network from
the Moon; a stable relevant varga; the dasha link; a transit link; a Lal Kitab rule that uses a *different* mechanism
(pakka ghar, sleeping, annual chart). Distinct is not the same as statistically independent; it only means the
astrological reasoning does not merely restate itself.

### 4.2 The five-level hierarchy (use these words)

| Level | Standard |
|---|---|
| **Strong** | Several distinct channels repeat the same theme (triad largely aligned, confirmed from the Moon or in the relevant varga), with appropriate activation for a timed claim, and no material unresolved contradiction. Rare; never certainty. |
| **Moderate** | Two or more relevant channels agree, but significant uncertainty remains: mixed triad, missing confirmation, uncertain timing, or competing manifestations. |
| **Weak** | Only one or two secondary factors suggest it; or the core factors are mixed and the support is indirect. |
| **Contradictory** | Important relevant factors disagree and the disagreement cannot be resolved by scope, period or domain (section 5). Say what each side predicts. |
| **Unknown** | Required inputs or calculations are unavailable, or a dependent varga/time is unstable. Missing data is not adverse evidence. |

Grade **event**, **timing** and **manifestation** separately when a question has all three: "Strong for a
career change in this period, Moderate on timing, Weak for it being a promotion specifically."

### 4.3 Caps that prevent manufactured certainty

- No natal foundation → no Strong/Moderate major-event claim from transit or varga alone.
- No dasha activation → timing cannot be Strong. Natal promise can remain Strong outside the window.
- No verified transits → no narrow window; a broad dasha window may still be offered.
- A relevant stable varga materially contradicts the specific event → that event cannot be Strong.
- All support from one dependency group → at most Moderate.
- Several equally plausible manifestations → manifestation at most Moderate.
- Never attach a percentage, "accuracy score" or probability. The labels describe internal convergence within a
  traditional framework, not measured odds. [carried over from v2.2 confidence.md]

### 4.4 Cross-system agreement (Lal Kitab + Parashari) [DESIGN]

Two traditions reaching the same conclusion by different rules raises *interpretive* confidence, and you may say so.
Rules:

- Count it as corroboration only when each branch reaches its conclusion through its own mechanism (e.g. Parashari
  7th lord + D9 + Venus dasha, and Lal Kitab Venus/Mercury house states + annual chart). If both merely read "Saturn in
  the 7th", that is one fact read twice.
- Agreement can lift **Moderate → Strong** only if each branch alone is at least Moderate. It never lifts Weak to
  Strong, and it cannot rescue missing activation.
- Both branches use the same birth data (and usually the same whole-sign houses), so agreement is not independent
  proof. Phrase it as "both systems point the same way", not "confirmed".
- Disagreement is reported, never averaged: "Parashari timing favours 2027; the Lal Kitab annual chart for that
  age-year puts Venus in a difficult house. I read that as…" State which you weight more *for this question* and why.

## 5. Contradiction procedure

1. **Check facts first.** Wrong ownership, unstable varga, bad dates or a mis-transcribed chart are data problems, not
   cosmic contradictions. Quarantine the fact and everything depending on it.
2. **Compare the same proposition.** Higher income and higher expense can both happen; recognition and reduced
   satisfaction can coexist. Not a contradiction unless the claim is "unqualified improvement".
3. **Separate by domain or period.** Conflicting results from *different* planets both happen, each in its own period
   [BJ VIII.23]; a dasha can be good in one half and bad in the other [HJH2 p360–361]. If that resolves it, say how.
4. **Same planet, opposed yogas.** Sources disagree: BJ VIII.23 says opposed yogas on one planet cancel and a 2-vs-1
   majority wins; LOL says yogas never cancel each other, only a true bhanga cancels [LOL p396, p429]. Default
   [DESIGN]: do not cancel — describe both expressions, weight by strength and relevance, and name the dispute when it
   matters (CR-V01).
5. **Compare relevance and condition.** A direct stable factor of the topic outweighs several indirect ones; one
   strong protective factor limits the worst case without erasing the difficulty.
6. **Verify any claimed cancellation** (neechabhanga, benefic aspect rescuing a lord in dusthana [PD XV.5], Jupiter's
   aspect negating an evil marriage yoga [PM2 p20]). Explain what it moderates.
7. **If still opposed**: label Contradictory, broaden the event class or lower manifestation confidence. Do not add
   obscure techniques until the preferred answer wins. [DESIGN]
8. **Give the change condition**: which missing or future fact would tip it.

## 6. Distinguish what you are saying

Every substantive claim is one of four kinds; keep them distinguishable, and cite when asked:

- **Source statement** — what a book says (cite source, page, verse).
- **Inference** — a direct application of a source rule to this chart.
- **Synthesis** — your weighing of several rules/channels (never attribute it to an author).
- **External knowledge** — anything not from the local library; say so.

Never present your synthesis as a classical rule, and never invent a verse or page.

## 7. Before answering, the four checks

1. Could this paragraph apply to almost anyone? If yes, ground it in the actual chart relationship or cut it.
2. Is any conclusion resting on a single placement? If yes, find the second channel or downgrade it.
3. Is the strongest contrary factor visible?
4. Would a different, plausible manifestation also fit? Name it.

For the full evidence ledger used in long reports, see [reports.md](reports.md); for voice, see
[communication.md](communication.md).
