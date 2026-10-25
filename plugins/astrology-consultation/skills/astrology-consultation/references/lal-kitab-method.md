# Lal Kitab method

Contents: [1. Sources and their standing](#1-sources-and-their-standing) · [2. Building the chart](#2-building-the-chart) · [3. Reading procedure (how to weigh Lal Kitab factors)](#3-reading-procedure-how-to-weigh-lal-kitab-factors) · [4. Timing in Lal Kitab (details in timing.md §8)](#4-timing-in-lal-kitab-details-in-timingmd-8) · [5. Disputes and what the author himself warns](#5-disputes-and-what-the-author-himself-warns)

> **If `data/lal-kitab/LalKitab_Shrimali_Knowledge_Base_v2.2.md` is not installed** (the public edition does not
> distribute it: it is a private knowledge base derived from a book that is still in copyright — check whether the file
> exists before relying on it). The method notes, rule tables and remedy notes in this folder, and the flags
> `scripts/chart_facts.py` prints, are the working rulebook:
> 1. Use the flags `scripts/chart_facts.py` prints, the rules in this file and in the topic files, and the timing rules in
>    timing.md §8 (maturity ages, sleeping planets waking, pair durations, the 35-year cycle).
> 2. Cite no knowledge-base section: section codes such as "KB B8" or "R42" in these files point into the private
>    knowledge base and are provenance notes, not sources you have opened. Cite a book page only when `search.py --page`
>    confirmed it in the user's own library or the reference file gives it; never invent one. Give no planet-in-house
>    ("B8") delineation beyond what the reference files state.
> 3. Give no specific Lal Kitab remedy beyond those in [remedy-safety.md](remedy-safety.md) or named by the person, and
>    only when remedies were requested.
> 4. The Varshaphal table is a private data file: when `scripts/varshaphal.py` says the table is not installed, give no
>    annual chart and say so.
> 5. Grade a Lal Kitab note with the same five grades; a single rule without confirmation is Weak.
> 6. Tell the person which parts of the detailed Lal Kitab rules (house delineations, annual table) are not installed.

Lal Kitab is its own system. Its evidence note is built without sign lordship, graha drishti, vargas, Vimshottari or
Tajika; it is compared with the Parashari note only at the convergence step ([synthesis-method.md](synthesis-method.md)
§4.4).

## 1. Sources and their standing

| Source | Standing | Use |
|---|---|---|
| **KB** — `data/lal-kitab/LalKitab_Shrimali_Knowledge_Base_v2.2.md` (private; the owner's notes on Shrimali's English book, audited v2–v2.2; not distributed in the public edition) | Working reference; faithful to *Shrimali*, not verified against the Urdu original | Default rulebook. Check Part 0 status (✅ ⚠️ ❓ 🔎) and system tags ([LK]/[VED]/[AUTH]/[MIXED]) before using any rule |
| **VT** — `data/lal-kitab/LalKitab_Varshaphal_Table_v2.2.csv` (private data file; not distributed in the public edition) | Reconciled annual table | RECOMMENDED columns only, via `scripts/varshaphal.py`; when you quote an annual chart, say it comes from this table, which age-year you used (running or completed) and that the other convention gives a different chart — never an annual chart without its table (round 10) |
| **Audit** — `data/lal-kitab/LalKitab_Validation_Audit_Report_v2.2.md` (private; not distributed) | Evidence limits | Read §7–10 when a Varshaphal or source-fidelity question arises |
| **LK1952** — Hindi re-typeset of the 1952 Urdu book (library index, `--src LK1952`) | The primary Lal Kitab text in the library, but a transliteration with its own errors | Confirms, extends or disputes KB rules; its doctrines below are cited by PDF page and edition page |

Shrimali mixes Vedic rules into Lal Kitab (Mangalik table by lagna, nakshatras, Kalsarpa, Kemadruma, sign exaltation):
those are [VED]/[MIXED] in the KB and must not be used as Lal Kitab doctrine without saying so.

**How to read the KB efficiently** (private installs only; it is 125 KB; never load all of it):
`grep -n "^### B" data/lal-kitab/LalKitab_Shrimali_Knowledge_Base_v2.2.md` to list sections, then read only the needed
range (B3 house table and house rules; B4 planet profiles; B5 aspects; B6 help grid; B7 planet states; B8 the
planet-in-house entry for each occupied house; B12 rin; B13 remedy toolkit; B17 Varshaphal; Part A5 contradictions;
Part C remedy audit).

## 2. Building the chart

1. Keep each planet's natal **house**; drop signs; label house 1 = Aries … 12 = Pisces [KB B2, R01]. This does not change
   the lagna or move planets. Whole-sign houses from the lagna sign are the KB default; if the user supplies a bhava/chalit
   map, say which is used and pass it as `lk_houses` to `chart_facts.py`. Confirm North/South Indian chart orientation.
2. Run `scripts/chart_facts.py` — it prints the LK house map, empty houses and per-planet flags (pakka ghar,
   LK exaltation/debilitation, node-dignity dispute, sleeping, friends/enemies in the house, sinful, dharmi, eclipse,
   rival/ally, LK aspect). With the KB installed each flag cites its KB section: open it before relying on it.
   Without the KB (public edition) the flags are printed without KB citations (top of this file).

## 3. Reading procedure (how to weigh Lal Kitab factors)

LK1952's own method: judge the **house condition before the planet** (the same planet reads differently by house and by
whether its "roots" — its pakka houses — hold enemies), then the pair/sequence effects, then time it
[LK1952_D §2; LK1952 p867–870]. In practice:

1. **Which houses answer the question?** Use the KB B3 house themes and karakas (e.g. 7 marriage, Venus + Mercury;
   10 work, Saturn; 2 wealth, Jupiter's seat; 4 home/mother, Moon; 5 children, Jupiter/Sun; 9 luck/ancestors, Jupiter).
2. **Occupants and their state**: pakka ghar ("sound state" per KB B7 p40–42: cannot be stopped — remediability disputed, CR-L01);
   LK exaltation/debilitation by house (⚠️ node sets X3/X4, plus the Rahu cells the book tables print; Mars exalted in
   10, in 8 disputed, CR-L03); friends/enemies in the same house; sleeping: nothing in the 7th from it [p44], except
   that 2 sleeps when 10 or 6 is empty [B3 H2, H6] and 10 when 2 is empty [B3 H10]; LK1952 p119 adds 1 and 9 sleeping
   when 2 is empty (both shown); LK1952's own test (the house a planet aspects is empty, p117–119; H11 needs H1 and H3
   occupied, p101) is printed beside Shrimali's 7th-house test, with empty houses and their awakeners (CR-L27), and a
   remedy pre-check line (X17, process rules per source) that prescribes nothing; dharmi (overrides sinful, p42), sinful, blind (also enemies together in 10, p48),
   rival, ally, established [p41–43]. LK1952 adds chart types (Farman 14, p248): blind, half-blind (Saturn 7 + Sun 4),
   baalig (Mercury 6 + Sun 1/5/11), nabalig (1, 4, 7, 10 empty, or Mercury with Rahu/Ketu/Saturn) — LK1952 rules,
   not Shrimali's; Jupiter's pakka ghar differs between the editions (CR-L26). Artificial planets (two planets in
   one house acting as a third, KB B7 p41, 52) are printed with the chapter-header variants where they differ (X9). Aspects: 7 and 10 aspect nothing (R11); 2→6, 5→9,11 and the table's 7→2 are
   disputed (CR-L02).
3. **Empty houses** are read through their helpers and rules: a house empty with its opposite also empty "sleeps"
   (house-specific rules in KB B3; awakening planets p45); empty 7th with occupied 1st, empty 10th → the 4th gives no
   effect, empty 2 and 8 excellent, etc. [KB B3 H1–H12]. Empty houses are not "no result".
4. **House interactions**: LK aspects are forward-only (1→7, 4→10, 8→2 …; table incomplete, ❓R10 — never fill gaps from
   Parashari); the mutual-help grid (a house helps the 5th from it and is helped by the 9th; fight with the 8th; deceit
   with the 10th) [KB B5–B6]; the 8→2→6→12 malefic chain; the "deceitful 10th" (bad 8 → bad 10; good 2 → good 10) [B7].
5. **Sequence and pairs** [LK1952]: which planet sits in the *earlier* house decides who leads (Ketu before Jupiter spoils
   Jupiter; Mercury before Venus passes Mars's help to Venus) [LK1952 p864, p926, p947]; two planets in one house act as
   a **blended planet for a stated number of years**, then separate (e.g. Sun+Moon to 40, Venus+Mercury to 22,
   Mercury+Saturn to 12) [LK1952 p868–982; table in timing.md]; artificial (masnui) planets from pairs [KB B7 p41, 52;
   ⚠️X9]. Stated cancellations: a solar eclipse (Sun+Rahu) is cancelled by Venus+Mercury, a lunar one by a good Mercury;
   Rahu's disturbance stops at the Moon and only Ketu removes it [LK1952 p893–982].
6. **Planet-in-house results**: read the KB B8 entry *and its conditions* (e.g. Sun H10 with Venus in 4 …). The
   conditions are where the synthesis happens; the headline result alone is a single-placement reading. LK1952's own
   order [p252–254]: read each planet's single entry, then **always** the combined entry for planets sharing a house
   (largest groups first — combinations often reverse single results: Mars and Mercury are each bad in 8 but excellent
   together; Venus in 9 bad, Venus+Ketu in 9 good). A judgement from one planet alone "breeds doubt" [p252].
   **House = ground + building**: a house's sign-lord (by Kalpurush) is the ground and its pakka-ghar planet the
   building; if they are friends the house prospers, if enemies it suffers, and an occupant modifies the result by its
   relation to both [LK1952 p254]. Also ask **who receives the result**: the book often sends a planet's harm to a
   relative (maternal uncle, grandfather, son, spouse) rather than the native — frame as family themes, never as a
   prediction about a person. Many placements are **judged through one other planet** (Saturn decides Mars, Mercury
   and Rahu in 10; Jupiter decides Mars and Mercury in 11; Rahu/Ketu decide Saturn in 11) and **Mangalik Mars is
   cancelled** by Moon in 1/4/7/10, Sun in 6, or Sun/Moon/Jupiter in 3/4/8/9, unless a bad Saturn or Ketu joins
   [LK1952 p563–566, part C]. Conduct switches results (drink, lies, taking charity, broken promises).
7. **Family layer**: rin (ancestral debt) signatures from the natal chart only [KB B12; LK1952 p150]; scapegoat chains
   (Saturn → Venus, Mars → Ketu …) [B7 p48–50]. Present as traditional family-karma symbolism, never as blame or a curse.
   No debt is named: the p150 gate (houses 2-5-9-12) does not say all or any, and "the planet itself malefic" is judged
   across the family's charts [LK1952 p144]; LK1952 gives the Sun-in-5 enemy two ways (p146 "paapi Ketu", p150 "paapi
   grah"), both shown. The clash line (takraav, N with N+7) is a relation, never a "sudden blow" prediction; the clash
   on house 9 is helpful [LK1952 p132–133; KB B6].
8. **Fixed vs changeable**: LK1952 splits planets into *grah-phal* (fixed, "the king") and *rashi-phal* (doubtful,
   "the minister", open to remedy) [LK1952 p59–60, p176]; Shrimali's KB uses planet-effect vs house-effect [B7 p47].
   The two classify pakka-ghar and house-6 planets oppositely (CR-L01) — state both when it matters, then use
   [remedy-safety.md](remedy-safety.md) if remedies were requested.
9. **Check the chart against life first** (LK1952's method): the author tests a chart against the family house layout,
   relatives' histories, past events and palm lines before reading it, and anchors the 35-year cycle to a dated event
   [LK1952 p213–236]. With a computed chart only, ask for one or two dated past events when a timing claim depends on
   the cycle.
10. **Grade** the LK conclusion with the same five grades; a single B8 entry is Weak on its own; a house whose occupant,
   helper houses and annual chart agree is Strong within Lal Kitab.

## 4. Timing in Lal Kitab (details in [timing.md](timing.md) §8)

Varshaphal by age-year (running year per LK1952 p243, completed shown as a note; 67/99/104 both readings; 17 majority); planet
maturity years (Jupiter 16, Sun 22, Moon 24, Venus 25, Mars 28, Mercury 34, Saturn 36, Rahu 42, Ketu 48) and the
half/quarter points; pair durations; the 35-year cycle; month rules (KB R42 vs LK1952 p239–241, CR-L06); a planet
reaching annual house 1 acts first on its natal house, then its enemies, then its friends [KB B17].

## 5. Disputes and what the author himself warns

Show ⚠️ versions with pages (KB A5 X1–X23; LK1952 differences in
[contradiction-register.md](contradiction-register.md) §C). LK1952's author says not to announce death timings, to
reassure rather than frighten, not to reveal a predicted daughter, and that his calculations "may be wrong"
[LK1952 p1182, p1223–1224]. His method also relies on palm/body signs as a second channel; a chart-only reading lacks
that channel — say so when a rule depends on it.
