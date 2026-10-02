# Calculation engines

Calculation and interpretation are separate layers. The engines below compute facts; they never interpret. The skill
reads only normalized facts and never an engine's own JSON.

```
birth data ─► local engine (astro.calc, Swiss Ephemeris, private) ─► adapter ─► ChartFacts ─┐
          └─► VedAstro (cloud, only in hybrid mode / with consent) ─► adapter ─► ChartFacts ─┴─► compare ─► ValidatedChartFacts
          └─► PyJHora (local, AGPL, validation only — never imported by astro)                         + comparison table
```

## 1. Engines

| Engine | Where it runs | Conventions | Role |
|---|---|---|---|
| **Local** — `astro.calc` (v3.5.0) on pyswisseph 2.10.3.2 / Swiss Ephemeris 2.10.03 | on the machine; nothing leaves it | Lahiri; mean nodes (true optional); whole-sign houses + Sripati bhavas; 16 Parashari vargas; Vimshottari with 365.256363-day years (365.25 and 360 optional); local Shadbala, Ashtakavarga, Jaimini factors, birth-time sensitivity grid | preferred calculator; every interface (MCP, REST, CLI) uses it |
| **VedAstro** — `tools/vedastro_batch.py` / `vedastro-local` MCP | **sends date, time, offset and coordinates to `api.vedastro.org`** (never a name; label "chart") | Lahiri; mean nodes; 360-day dasha years; variant D2/D7/D30; see §5 | independent cross-check; each call logged to `calls.jsonl` |
| **PyJHora 4.8.7** | local, separate `.venv-pyjhora` (AGPL — kept out of the package) | default ayanamsa TRUE_PUSHYA: call `set_ayanamsa_mode("LAHIRI")` | third opinion for Shadbala |

The VedAstro MCP defaults to a personal `profile.json`; every call must pass `use_profile=false`.

## 2. Ephemeris

The engine looks for `.se1` files in `$ASTRO_EPHE_PATH`, `<project>/ephe`, then
`~/.local/share/astrology-consultation/ephe` (`astro setup --ephemeris` downloads them from the official
github.com/aloistr/swisseph repository and verifies pinned SHA-256s; a mismatch deletes the file). Without files it
falls back to the built-in Moshier ephemeris. `meta.ephemeris` and `meta.ephemeris_files` (short hashes) record which
was used in every output.

| File | Range | SHA-256 |
|---|---|---|
| `sepl_18.se1` (planets) | 1800–2399 CE | `ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66` |
| `semo_18.se1` (Moon) | 1800–2399 CE | `1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7` |

**Before/after benchmark** (400 dates, 1801–2399, sidereal Lahiri; maximum |Moshier − files|): Sun 0.09″, Moon 2.65″,
Mercury 0.12″, Venus 0.55″, Mars 1.14″, Jupiter 1.12″, Saturn 0.52″, mean node 0, true node 55.6″, ayanamsa 0.
Nothing changes at astrological precision unless a body sits within a few arcseconds of a boundary; the files matter
mainly for the true node and exact-boundary charts. CI runs on Moshier; local runs use the files.

## 3. What the local engine produces

`compute_full()` (`astro/calc/__init__.py`) returns, with provenance in `meta`:

- **Positions** with speed, sign, nakshatra-pada, retrograde flag; ascendant and MC.
- **Houses**: whole sign from the sidereal ascendant; **Sripati bhavas** — madhyas at the Porphyry trisection of the
  ascendant–MC quadrants (Swiss Ephemeris house system `O`), sandhis at the midpoints (matches VedAstro's
  HouseLongitude within 0.003°).
- **Vargas** — the rules in `engine.VARGA_METHODS`:

| D | Rule |
|---|---|
| D2 | Parashari hora: odd signs 0–15° Leo, 15–30° Cancer; even signs reversed |
| D3 | drekkana: 1st, 5th, 9th from the sign |
| D4 | 1st, 4th, 7th, 10th from the sign |
| D7 | odd signs from the sign, even from the 7th |
| D9 | movable from the sign, fixed from the 9th, dual from the 5th (continuous from Aries) |
| D10 | odd from the sign, even from the 9th |
| D12 | from the sign |
| D16 | movable from Aries, fixed from Leo, dual from Sagittarius |
| D20 | movable from Aries, fixed from Sagittarius, dual from Leo |
| D24 | odd from Leo, even from Cancer |
| D27 | fire from Aries, earth from Cancer, air from Libra, water from Capricorn |
| D30 | Parashari: odd 5/5/8/7/5° → Ar/Aq/Sg/Ge/Li; even 5/7/8/5/5° → Ta/Vi/Pi/Cp/Sc |
| D40 | odd from Aries, even from Libra |
| D45 | movable from Aries, fixed from Leo, dual from Sagittarius |
| D60 | from the sign, 30′ parts |

  Variants met elsewhere: other D2 schemes (VedAstro's D2 is not the Parashari hora), VedAstro's D7 for even signs,
  VedAstro's D30 (sometimes the other sign of the same lord). The local engine keeps the Parashari rule; the
  comparator labels the others *methodology*.
- **Vimshottari** to pratyantar; transits, slow-planet ingresses and exact Jupiter/Saturn/node contacts.
- **Shadbala** (`strength.py`, BPHS ch. 27 as worked by B. V. Raman) — conventions in `SHADBALA_CONVENTIONS`:
  saptavargaja 45/30/20/15/10/4/2 over D1/D2/D3/D7/D9/D12/D30; dig from the ascendant/MC; natonnata from local
  apparent time; tribhaga from actual sunrise/sunset; abda/masa via Raman's Ahargana from the Kali epoch (JD 588465.5);
  ayana (24° ± declination)×1.25; Sun's cheshta = ayana, Moon's = paksha (Raman); others' cheshta kendra with a
  **circular** mean; yuddha; drik on Raman's curve with the special-aspect additions (Mars +15, Jupiter +30,
  Saturn +45, capped at 60). Golden test: Raman's published 1918 example, drik bala for all seven planets within 0.02.
- **Ashtakavarga** — BPHS bindu tables; bhinnashtakavarga per planet and sarvashtakavarga by sign and house
  (property test: totals 48/49/39/54/56/52/39 = 337 for every chart).
- **Jaimini** (`jaimini.py`) — chara karakas (7- and 8-planet schemes; Rahu as 30° − degree), arudha padas with the
  BPHS 29.45 exception, dual lordship of Scorpio/Aquarius, upapada, karakamsa, rasi drishti.
- **Birth-time sensitivity grid** (`sensitivity.py`) — recomputes the chart at −15, −10, −5, −2, −1, −0.5, 0, +0.5,
  +1, +2, +5, +10, +15 minutes and classifies each factor (ascendant sign and pada, D9/D10/D12/D60 lagnas, Moon
  nakshatra-pada, running MD–AD–PD): **robust** (no change within ±15′), **moderate** (changes only beyond ±5′),
  **high** (within ±2–5′), **very high** (within ±1′). Dasha boundaries move about 1.6–4.4 days per minute of birth
  time, depending on the Moon's speed.

## 4. The normalized schema

`astro/calc/schema.py` (Pydantic; JSON Schema in `schemas/chart_facts.schema.json`):

- `ChartFacts` — `birth`, `provenance` (engine, version, network, ephemeris, computed_at, settings, ayanamsa, nodes,
  dasha-year length, house system, varga notes), `bodies`, `vimshottari` (nested, clipped edges marked at every
  level), `transits`, `ingresses`, `bhavas`, `shadbala_rupas`, `shadbala_components`, `ashtakavarga`, `arudha`,
  `jaimini`, `sensitivity`, `flags`.
- Validation: sign, degree, nakshatra and pada must follow from the longitude; Ketu opposite Rahu; contiguous dashas.
- `ValidatedChartFacts` — preferred engine's facts plus `agreements`; `disagreements()` returns the unresolved rows.

## 5. Astrology-aware comparison

`astro/calc/compare.py` (`python -m astro.calc.compare --local calc.json --vedastro DIR --out OUT`) classifies every
difference:

| Verdict | Meaning |
|---|---|
| match | < 0.05′, or identical sign/nakshatra/varga/lord |
| within tolerance | ≤ 1′ (ascendant ≤ 3′); bhava ≤ 0.5°; dasha boundary ≤ 3 days under the same year length |
| methodology | a documented school difference (variant varga, Shadbala sub-rule, arudha exception) |
| configuration | a setting differs (dasha year length) |
| implementation | the other engine contradicts its own inputs or a published worked example |
| unresolved | a real disagreement nobody has explained — a release blocker |
| not comparable | quantities that are not the same thing |

**Results (v3.5).**
- *S1* (synthetic, 14 Mar 1992 09:40 UT, 51.5N 0.12W): positions match or within tolerance; no sign/nakshatra/pada
  flips; vargas agree except the D2/D7/D30 variants; dasha lords agree, dates differ by year length only.
- *S2* (second synthetic chart, details withheld until the v3.5 benchmark ends) and one private real chart (never
  published): **0 unresolved**. S2: positions 9 match + 1 within tolerance; vargas 125 match, 19 methodology;
  bhavas 24/24; Ashtakavarga all 84 cells; arudhas 7 match, 5 methodology; Shadbala components 48 same-rule matches,
  43 methodology. With the local engine set to 360-day years, the private chart's dashas match VedAstro at all three
  levels (13/13 MD, 118/118 AD, 1050/1050 PD within 3 days) — the year length is the only dasha difference.

**Differences found in the other engines** (reported, not copied):

| Engine | Finding | Verdict |
|---|---|---|
| VedAstro | dasha at birth on S2 starts from Venus although its own Moon nakshatra (Mula) gives Ketu | implementation |
| VedAstro | tribhaga bala for a post-midnight, pre-sunrise birth omits Mars | implementation |
| VedAstro | saptavargaja on a 22.5/7.5/3.75/1.875 scale; ayana capped at 60; Sun/Moon cheshta 0; abda/masa epoch | methodology |
| VedAstro | arudhas without the BPHS 29.45 exception | methodology |
| VedAstro, PyJHora | cheshta mean taken as a plain average — fails when mean and true longitude straddle 0° Aries (Jupiter 12.6 instead of about 47 virupas on S2) | implementation |
| PyJHora | Saturn dig bala 73.3 virupas (exceeds the 60 maximum) | implementation |

## 6. Tests

`tests/test_calc_properties.py` (Hypothesis): longitude → sign/nakshatra/pada; boundaries; varga identities;
Vimshottari structure; time-zone shifts; nodes opposite. `tests/test_reference.py`: Lahiri at J2000, S1 engine
agreement, schema rejection, sensitivity, slow contacts. `tests/test_strength.py`: Raman 1918 drik golden
(`tests/reference_charts/`), Ashtakavarga totals property, Shadbala component ranges, circular mean across 0° Aries,
karaka/arudha properties, S1 sensitivity classes. `tests/test_service.py`: the MCP/REST/CLI interfaces and their
privacy guards. All on synthetic or published charts.

## 7. Limits

No time-zone database (give the UTC offset, including daylight saving); no Chara, Yogini or Narayana dasha (not added
without a second engine to compare against and tests); no ishta/kashta phala or bhava bala; outside 1800–2399 the
engine uses Moshier and says so.
