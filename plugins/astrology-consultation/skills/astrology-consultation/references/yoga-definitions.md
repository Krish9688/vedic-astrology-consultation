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

Not included, with reason: **neechabhanga** (no agreed list of clauses in the library: print none rather than one
"cancelled" flag); **Sunapha, Anapha, Durudhura, Budhaditya and others** (not yet checked against the maps).

## What the base rates mean, and what they do not

Each line carries the share of 4,000 random charts (random moment 1950–2010, latitude −50° to 60°, Lahiri, whole-sign
houses) in which that definition's condition holds, measured with these exact functions by
`tools/calc/yoga_baserates.py`; a test regenerates them so they cannot drift from the code.

- They are frequencies of a **configuration**, not of any outcome. Nothing here was tested against lives.
- Random dates and places are not a population of real births (births cluster by season, region and time of day).
- They depend on the definition: the loose Kesari holds in about a third of charts, strict Gajakesari in about one in
  eleven; some kendra–kona relation holds in two thirds; popular Kuja in nine charts out of ten.
- A high rate means the bare condition carries little weight on its own. A low rate is not a promise either: the
  classical texts make every yoga depend on strength and on the dasha of its planets.
- Say which definition you use, and never present a common configuration as a rare or decisive one.
