# Input contract and uncertainty

Contents: [Two valid starting points](#two-valid-starting-points) · [Record only what the question needs](#record-only-what-the-question-needs) · [Consistency checks](#consistency-checks) · [Whose report is it? (identity gate)](#whose-report-is-it-identity-gate) · [Sensitivity protocol (DESIGN)](#sensitivity-protocol-design) · [Compact intake example](#compact-intake-example) · [Calculation engines and their conventions (re-checked 2026-10-02, v3.5)](#calculation-engines-and-their-conventions-re-checked-2026-10-02-v35)

## Two valid starting points

For Lal Kitab, read `lal-kitab-method.md` before converting houses. The whole-sign calculation below is a declared **Parashari default**, not an automatic substitute for a user-supplied bhava/chalit house map or an agreed Lal Kitab natal-house source.

**Chart-first:** accept a transcribed chart, legible chart image or positions table plus relevant period data. Identify the chart format before interpreting numbers: North Indian charts fix houses; South Indian charts fix signs. Ask when a legend, digit or label is ambiguous. Confirm the transcription with the user if ambiguity would change the answer.

**Birth-data-first:** date, local clock time with its uncertainty/source, birthplace and coordinates, historical time zone/DST, and calculation conventions are needed for a new chart. Pass the UTC offset as `+HH:MM` (India: `+05:30`; never `5.30`, which means 5 h 18 min); the engine refuses decimal offsets other than whole or quarter hours. Better, pass `zone` (IANA, e.g. `Asia/Kolkata`) so the offset of the birth moment comes from the tz database's historical rules: `find_place` (or `astro place`) gives coordinates and zone offline, and when it says `ambiguous`, ask which place. The engine refuses a clock time skipped by a daylight-saving change, asks for `fold` (0 = first, 1 = second) when a time occurs twice, and refuses the pre-standard-time era (it suggests local mean time for the longitude instead). Before 1970, and in South Asia before 1948, it flags the offset as needing confirmation from the birth record: report that flag. **Confirm the offset before interpreting:** tell the person the resolved offset and its source (`meta.utc_offset`, `utc_offset_source`) and ask them to check it against the birth record. An offset taken from the birth record overrides the zone: pass both `tz` and `zone`; the engine uses `tz` and keeps the IANA value as a flag, which you report. The skill text contains no ephemeris; the plugin's local engine (`astro`, MCP server) calculates charts. If neither a verified chart nor the engine is available, either ask for the chart/period tables, or — with the user's explicit consent for that chart — use a calculation tool that is available in the session.

**Calculation tools and privacy.** Use the local engine below; it runs on this machine and sends nothing anywhere. If some other calculation service is available in a session, tell the user that birth data would leave the machine and get a yes before the first call; pass explicit coordinates and UTC offset, never a saved default profile. Report any engine's output as calculated data with ayanamsa and source; never fill gaps it leaves. Keep calculation, retrieval and interpretation separate in the answer.

**Deterministic helpers (local, no network):** `scripts/chart_facts.py` derives houses, lordships, aspects, dignity, combustion, D9/D10, dispositors, Phaladeepika XV tests and Lal Kitab house states from supplied positions; `scripts/varshaphal.py` does the Lal Kitab annual-table lookup. Use them instead of hand arithmetic; they never invent positions.

## Record only what the question needs

| Input | Why it matters |
|---|---|
| D1 ascendant sign and degree; Sun–Saturn and Rahu/Ketu longitudes | Ownership, signs, aspects, dignity, angular separation and boundary checks |
| Zodiac/ayanamsa, mean or true node, house system, source/version and export date | Prevent incompatible tables or editions from being merged; an old report is not current data |
| Birth-time uncertainty and its provenance | Reliability of ascendant, varga houses and calendar timing |
| Moon longitude/nakshatra and dasha convention | Starting balance and period boundaries |
| MD/AD start/end dates and time zone | Determine active periods at the actual requested date |
| Relevant varga with calculation method | Topic-specific confirmation, not a generic requirement to supply all charts |
| Shadbala/Ashtakavarga, if used, with units/method | Numeric strength cannot be inferred from appearance |
| Transit source, date/time, zodiac and anchor | A sign ingress is not a verified contact to a natal degree |
| Life context voluntarily provided | Distinguish a job offer from retirement, travel from migration, or relationship formation from an existing partnership decision |

For a timeless natal question, missing transit or dasha data need not block the answer. For current/future timing, missing period tables or ephemerides must be reflected in the answer.

## Consistency checks

- Longitudes must be finite and in [0°, 360°); degrees within signs in [0°, 30°). Do not round 29°59′ into the next sign before checking a boundary.
- In the default D1 whole-sign frame: house = ((planet sign index − ascendant sign index) mod 12) + 1. House ownership follows signs; Sun owns Leo, Moon Cancer, Mars Aries/Scorpio, Mercury Gemini/Virgo, Jupiter Sagittarius/Pisces, Venus Taurus/Libra, Saturn Capricorn/Aquarius.
- Rahu and Ketu should be opposite in a single consistent node model. A conjunction list must agree with the positions. Exact aspect claims require the declared aspect convention.
- Check obvious astronomical impossibilities in purported real D1 data, including implausible Mercury/Sun or Venus/Sun separation. Hypothetical partial packets must be labeled as such; they are not certified physical skies.
- Child periods belong inside their parent periods. Adjacent boundaries must not overlap or leave unexplained gaps. Use [start, end) when checking dates; display dates at the precision of the source. Check ordering before interpreting a date.
- Do not assume a rounded birth time is accurate to the minute just because software prints seconds.
- If a printed yoga conflicts with its listed placements, use neither the yoga label nor an invented repair. Explain the discrepancy and retain unaffected facts.

Validate a supplied interpretation as well as its positions: dignity must match the sign under the declared system; a weak strength score does not imply debilitation. Use the lookup in [vedic-natal.md](vedic-natal.md). Quarantine all conclusions depending on a bad premise, including summaries, timing, education and remedies. A corrected rule does not validate the rest of an old report.

For strength tables record raw unit, denominator/planet-specific benchmark, normalization and source. A printed percentage might be percent of a required minimum, not share of the chart's strength. A score below 100% is not automatically adequate, and above 100% is not a success probability. Rupa/virupa conversion and percent share are different operations; do not silently repair a suspected unit typo without the source. Distinguish SAV from BAV and pre/post-reduction values.

For weekday discrepancies distinguish the civil calendar day from a traditional sunrise-based vara. A pre-sunrise birth can legitimately have different labels. Preserve the convention rather than treating every mismatch as a birth-data error.

When sources conflict, record which input differs and its affected claims; a document calling itself authoritative is not evidence of calculation accuracy. Prefer the actual reproducible export over unsupported prose, but ask for resolution when neither source's authority can be established. See [reports.md](reports.md) for revision handling.

## Whose report is it? (identity gate)

Before a supplied report, chart or reading informs anyone's predictions, compare the birth data it prints with that
person's own data (the engine's `astro.identity` check does this field by field):

| Verdict | Meaning | Use |
|---|---|---|
| BOUND | Date, time and place match; an ambiguous dd/mm date is confirmed by the ascendant and Moon sign | May be used, still audited claim by claim |
| PROVISIONAL | No conflict, but a field is missing or the name differs | Only after the person confirms it is theirs |
| UNBOUND | No birth date printed (a generic Moon-sign or name-only report) | Sky facts only; nothing personal |
| REJECT | Any birth field conflicts | Someone else's report: never used for this person |

A matching name proves nothing, and removing a name does not make another person's report usable. Never merge two
people's data, and say plainly when a report was set aside and why, without repeating the other person's details.

## Sensitivity protocol (DESIGN)

When chart variants across the stated time interval are supplied or legitimately computed, compare the interval endpoints **and any boundaries inside it**, not just one nominal time. Record which of D1 ascendant, Moon nakshatra, varga signs, varga ascendant and MD/AD dates change. Equal endpoints can conceal intervening changes in a higher varga. No blanket ±2-hour assurance establishes Moon/nakshatra or dasha-date stability; a boundary may occur inside even a short interval. D60 has 30′ (0.5°) divisions, not 1°; this angular width is not a universal clock-minute tolerance. See [source-index.md](source-index.md), PVR-60 and PVR-B.

Use only invariant facts in the common interpretation. Describe variant-dependent alternatives conditionally. If no variant calculation is available, say stability is untested; do not declare a high varga stable. Do not rectify time by selecting whichever minute produces the desired story. Rectification needs multiple preselected events and held-out checks; this skill does not claim to establish a uniquely correct birth time.

Precise ephemeris arithmetic measures positions and dates. It does not establish astrological predictive validity. Ayanamsa and house-system differences are documented by [Swiss Ephemeris](https://www.astro.com/swisseph/swisseph.htm), sections 2.8 and 6.2.

## Compact intake example

“For this career question I can interpret the D1 facts you supplied. To assess the proposed year, I need the MD/AD date table; a D10 with its calculation method and birth-time reliability would help assess the professional outcome.”

Keep sensitive data out of saved examples. Save a reading or biography only when the user requests it; ask where it should go when no destination is specified.

## Calculation engines and their conventions (re-checked 2026-10-02, v3.5)

- **Local engine (preferred; private):** `astro.calc` — the `astrology-consultation` MCP server or the `astro` CLI. Swiss Ephemeris (full `.se1` files when installed, otherwise
  Moshier — `meta.ephemeris` says which), Lahiri, mean nodes, sidereal-year dashas (365.256363 days). Validated
  with property tests, published worked examples (golden values) and a 22-chart edge suite. During development it
  was also compared with other engines; the differences found were convention choices (year length, varga variants)
  or defects in the other engine — one engine's dasha dates were wrong by up to 2½ years.
- **Year length:** some programs count Vimshottari years as 360 days, so their period dates run earlier (about 5.26
  days per year of age); the local engine can produce that convention (`--year 360`) when a supplied table uses it.
- **Dasha dates are convention-dependent** (CR-N10): always say which engine/convention produced a window.
- **Shadbala:** use the local values (BPHS as worked by Raman; components and conventions listed in the output;
  drik bala reproduces Raman's worked example). Other engines use different sub-rules (saptavargaja scale, ayana cap,
  Sun/Moon cheshta), so totals differ between engines by design. A ratio below 1.00 is "just short of its
  minimum" — accurate wording when strength is discussed, never "just reaches". Within about 10% either side is
  borderline. Shadbala never sets or lowers a grade on its own: promise grades come from house, lord, karaka,
  aspects and D9; a borderline ratio is at most a nuance in the appendix.
- **Ashtakavarga:** local bhinnashtakavarga (BPHS tables); SAV by house is in the output.
- **Jaimini factors** (chara karakas in both schemes, arudhas with the BPHS 29.45 exception, upapada, karakamsa):
  other software may skip the arudha exception; say which rule produced an arudha. Karakas within 1′ are flagged.
- **Birth-time sensitivity — quote, never estimate.** The grid recomputes the chart at ±0.5, 1, 2, 5, 10 and 15
  minutes and classes each factor: **robust** (unchanged within ±15′), **moderate** (changes only beyond ±5′),
  **high** (within ±2–5′), **very high** (within ±1′). Compare the first change with the person's actual time
  uncertainty: a factor is usable as stable only if it survives that uncertainty (vargas.md *Stable*). Very high
  factors (often D60 lagna, ascendant pada, pratyantardasha) stay conditional unless the time is recorded to the
  minute. Exact Jupiter/Saturn/node contacts and sign changes are also in the output; never derive them from average
  motion.
- **Normalized facts:** an *unresolved* row must be mentioned where it affects the answer; *methodology* and
  *configuration* rows (360-day years, non-Parashari D2/D7/D30 variants, Shadbala sub-rules) only as a convention note.
