# Candidate yogas and Kuja conventions: definitions, sources, limits

`scripts/chart_facts.py` prints one line per **named definition** below: whether that definition's own conditions hold,
what was checked, the source, and how often the condition holds in random charts. It detects configurations; it does
not interpret them. Strength, cancellation beyond what is listed, dasha timing and meaning stay with the yoga procedure
in [vedic-natal.md](vedic-natal.md) §6.

Sources are the project's page-cited source maps (paraphrases made from full reads of each book). They are marked
"not page-checked" until the owner checks the printed page; the page numbers below are the maps' citations.

| Id | Definition as implemented | Source (map) | Handled | Not handled |
|---|---|---|---|---|
| GK-BPHS36 | Jupiter in a kendra from the lagna or the Moon, joined or aspected by a benefic (Jupiter is not its own benefic), not debilitated, combust or in an enemy's sign | BPHS ch. 36 sl. 3–4, p380 (BPHS_part3.md) | all clauses; "undetermined" when degrees are missing for combustion | benefic strength |
| KESARI-LOOSE | Jupiter in a kendra from the Moon | Phaladeepika VI.14 per the BPHS translator ("only Kesari"); CRUX p28–30 and HJH1 p118 call it Gajakesari | — | — |
| KEM-BARE | No planet but the Sun (nodes not counted) in the 2nd or 12th from the Moon | Brihat Jataka XIII, p175–178 (BJ.md); Varahamihira rejects the other schools' versions | — | BJ XIII.9 (benefics in upachayas override malefic yogas) is a general rule, not computed |
| KEM-BPHS | As above, and no planet but the Sun with the Moon or in a kendra from the lagna; the Moon itself in a kendra counts | BPHS ch. 37 sl. 11–13, p398 (BPHS_part3.md); "Moon in a kendra" per LOL p322 and Garga/Parasara via BJ | lists the planets that rule it out | "some" cancel by a planet in a kendra from the Moon (LOL p322) |
| PMP-*-BPHS | Mars, Mercury, Jupiter, Venus or Saturn in own or exaltation sign in a kendra from the lagna (Ruchaka, Bhadra, Hamsa, Malavya, Sasa) | BPHS ch. 75 (BPHS_part6.md §5.1); no cancellation given there | — | — |
| PMP-*-LOL | Same, kendra **or kona** | Phaladeepika VI.2–4 as given in LOL p311 | — | — |
| RAJA-KK-* | A kendra lord and a kona lord (different planets) related by exchange, by joining in a kendra or kona, or by mutual opposition | BPHS ch. 34 sl. 11–12, p356–357 (BPHS_part3.md) | **dispute**: a lord that also owns 6/8/12 gives no yoga by these relations alone (BPHS 34.14–15; not the luminaries; the moolatrikona sign decides, per the translator) vs yoga even so (PD XX.45, p245) | PD XX.45 counts all five XV.30 relationships |
| RAJA-KKP-* | A trinal lord placed in a kendra, or an angular lord in a trine | BPHS ch. 34 sl. 11–12 (translator's permutations 4–5) | the same dispute | sl. 13 yogakaraka (one planet owning both) is not printed |
| KUJA-BPHS80 | Mars in the 12th, 4th, 7th or 8th from the lagna, unaspected by and unassociated with any benefic | BPHS ch. 80 sl. 47–49, p955 (BPHS_part6.md) | benefic cancellation | the "partner with the same yoga" clause needs both charts |
| KUJA-POPULAR | Mars in the 1st, 2nd, 4th, 7th, 8th or 12th from the lagna, Moon or Venus | LOL p329–331, which says it is "not in any authoritative text" | Moon with Mars cancels; Mars own/exalted modifies or cancels (experts disagree) | partner and age (about 28–30) exceptions |
| KUJA-PD11.3 | Mars in the 7th, or the 7th sign and the descendant's navamsa both Mars's | Phaladeepika XI.3, p141–142 (PD_part1.md) | "undetermined" without the ascendant degree | — |
| KUJA-HJH2 | Mars in the 2nd, 12th, 4th, 7th or 8th from the lagna, Moon or Venus (no 1st) | HJH2 p70–71 (HJH2_part1.md §3.7); CR-V16 | membership; Raman's sign exemptions per house, "none in Leo or Aquarius" and Mars with Jupiter or the Moon are named in the line | Raman counts by bhava (here whole-sign); the units table and matching rule (gender-asymmetric) are not computed |

### Added in P4-1 (second set)

Lines of these yogas print only when one of a yoga's variants holds (or is undetermined); then every variant of that
yoga prints, so a failing variant stands next to a holding one. Neechabhanga prints every clause for every debilitated
planet. Benefics: Jupiter, Venus, Mercury unless with a malefic, and the Moon unless waning (as above). The 2nd/12th
yogas count Mars, Mercury, Jupiter, Venus and Saturn only (LOL p326 excludes the nodes explicitly; the BPHS and BJ maps
say only "other than the Sun / Moon"). All loci are the source maps' citations, not page-checked.

| Id | Definition as implemented | Source (map) | Handled | Not handled |
|---|---|---|---|---|
| SUNAPHA-BPHS37 / ANAPHA-BPHS37 / DURADHARA-BPHS37 | a planet in the 2nd from the Moon only / in the 12th only / in both | BPHS ch. 37 sl. 7–10, p397 (BPHS_part3.md); BJ XIII p175 (BJ.md); PD VI.5–7 p78 (PD_part2.md); LOL p326 | exclusive with KEM-BARE (the four add up to every chart) | BJ's rejected alternatives (kendras from the Moon, the Moon's navamsa sign) |
| VESI-BPHS38 / VOSI-BPHS38 / UBHAYACHARI-BPHS38 | any planet but the Moon in the 2nd from the Sun only / 12th only / both; each planet is labelled benefic or malefic | BPHS ch. 38 sl. 1–4, p398–399 (BPHS_part3.md); LOL p326 | **dispute** CR-V25 | HPA p59's mixed reading |
| VESI-PD6 / VOSI-PD6 / UBHAYACHARI-PD6 | the same with benefics only | PD VI.8–13, p80–82 (PD_part2.md) | CR-V25 | PD's malefic ("papa") versions are named, not given ids |
| ADHI-BPHS37 | a benefic in the 6th, 7th or 8th from the Moon (any of the seven fillings) | BPHS ch. 37 sl. 5, p397; BJ XIII p174 translator (seven variants) | **dispute** CR-V26; malefics there are listed | Saravali/Mandavya's combustion and malefic-aspect conditions; LOL's "6th and 8th only is a kind of Adhi" |
| ADHI-PD6 | the same from the Moon or the lagna | PD VI.42–43, p93–94; LOL p318 | CR-V26 | BPHS 36.37 Lagnadhi (a separate yoga) |
| AMALA-BPHS36 | only benefics in the 10th from the lagna or the Moon | BPHS ch. 36 sl. 5–6, p382 (translator: a malefic also there voids it) | **dispute** CR-V27 | bhava-chart reckoning (the translator) |
| AMALA-PD6 | a benefic in the 10th from the lagna or the Moon | PD VI.19–20, p84; LOL p318 | CR-V27 | LOL's "unafflicted" |
| BUDHADITYA-LOL | the Sun and Mercury in the same sign | LOL p319–320 (only map that defines it; HJH2 p48 uses it) | house and Mercury's combustion are shown | LOL's working conditions (a link to the 1st or 5th, both strong and unafflicted) |
| LAKSHMI-BPHS36 | the 9th lord in a kendra in its own or exaltation sign (the moolatrikona sign is one of these at sign level) | BPHS ch. 36 sl. 27–28, p389 | **dispute** CR-V28 | "with a strong lagna lord" |
| LAKSHMI-PD6 | the 9th lord and Venus each in own or exaltation sign in a kendra or kona | PD VI.21–25, p85–86; LOL p322 | CR-V28 | LOL's allowed variants (from the Moon) |
| VIPARITA-LOL | at least two of the 6th/8th/12th lords each in another of 6/8/12, an exchange between them not counted | LOL p327 | **dispute** CR-V29 | — |
| VIPARITA-HJH | one 6th/8th/12th lord in another dusthana, the 3rd included (Raman's "12th in 3rd") | HJH2 p296, p353 (HJH2_part2.md); HJH1 p307 (HJH1_part2.md) | CR-V29 | — |
| VIPARITA-CRUX | two different lords of the 3rd/6th/8th/12th joined in the 3rd, 6th, 8th or 12th | CRUX p30–32 (CRUX_part1.md) | CR-V29 | PVR p146 ideal form; BPHS ch. 39 debilitated-lord forms |
| NB-DISP-* | the debilitation-sign lord in a kendra from the lagna or the Moon | LOL p323 (1); PD VII.26–30, p110–112 (PD_part2.md); HJH2 p45, p366–368 | **clauses differ by source** CR-V30; the line notes LOL's kendra/kona condition for the raja yoga | strength of the cancelling planet (LOL: the better placed, the more relief) |
| NB-EXL-* | the lord of the planet's exaltation sign in a kendra from the lagna or the Moon | LOL p323 (2); PD VII.26–30; HJH2 | CR-V30 | — |
| NB-ASP-* | the debilitation-sign lord aspects the planet (graha drishti; being with it is not an aspect) | LOL p323 (3); PD VII.26–30 | CR-V30 | — |
| NB-EXP-* | the planet exalted in that sign in a kendra from the lagna or the Moon (none for the Moon in Scorpio) | LOL p323 (4); PD VII.26–30 translator | CR-V30 | node exaltation (CR-V15) |
| NB-MUT-* | the debilitation-sign lord and the exaltation-sign lord in mutual kendras (the same sign counts) | PD VII.26–30 | CR-V30 | — |
| NB-SELF-* | the debilitated planet itself in a kendra from the lagna or the Moon | PD VII.26–30 translator ("five kinds") | CR-V30 | — |
| NB-D9-* | the debilitated planet exalted in the navamsa; "undetermined" without a degree | HJH2 p366–368 | CR-V30 | Raman's chart-specific combinations (4) and (5) |

A neechabhanga clause that would hold only by counting the Moon as in a kendra from itself (the Moon as the lord in
question, or the Moon itself debilitated) prints "undetermined": the texts do not say whether that counts.

Not included, with reason: **neechabhanga as one "cancelled" flag** (the sources list different clauses; each clause
prints on its own line instead); **a separate "south-Indian 2nd-house" Kuja convention** (not located in the library as
a named regional rule; the only 2nd-house list found is HJH2 p70, printed as KUJA-HJH2).

## What the base rates mean, and what they do not

Each line carries the share of 4,000 random charts (random moment 1950–2010, latitude −50° to 60°, Lahiri, whole-sign
houses) in which that definition's condition holds, measured with these exact functions by
`tools/calc/yoga_baserates.py`; a test regenerates them so they cannot drift from the code.

- They are frequencies of a **configuration**, not of any outcome. Nothing here was tested against lives.
- Random dates and places are not a population of real births (births cluster by season, region and time of day).
- They depend on the definition: the loose Kesari holds in about a third of charts, strict Gajakesari in about one in
  eleven; some kendra–kona relation holds in two thirds; popular Kuja in nine charts out of ten; Budhaditya in half;
  Raman's one-lord Viparita in 58% against LOL's two-lord form in 6%. A neechabhanga rate is a share of all charts, not
  of charts with a debilitated planet.
- A high rate means the bare condition carries little weight on its own. A low rate is not a promise either: the
  classical texts make every yoga depend on strength and on the dasha of its planets.
- Say which definition you use, and never present a common configuration as a rare or decisive one.
