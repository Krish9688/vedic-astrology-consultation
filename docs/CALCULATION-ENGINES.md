# Calculation engines

Calculation and interpretation are separate layers. The engines below compute facts; they never interpret. The skill
reads only normalized facts and never an engine's own JSON.

```
birth data ─► local engine (astro.calc, Swiss Ephemeris, private) ─► adapter ─► ChartFacts ─┐
          └─► another engine's normalized facts (optional, offline) ─────────► ChartFacts ─┴─► compare ─► ValidatedChartFacts
          └─► PyJHora (local, AGPL, validation only — never imported by astro)                         + comparison table
```

## 1. Engines

| Engine | Where it runs | Conventions | Role |
|---|---|---|---|
| **Local** — `astro.calc` (3.6.1) on pyswisseph 2.10.3.2 / Swiss Ephemeris 2.10.03 | on the machine; nothing leaves it | Lahiri; mean nodes (true optional); whole-sign houses + Sripati bhavas; 16 Parashari vargas; Vimshottari with 365.256363-day years (365.25 and 360 optional); local Shadbala, Ashtakavarga, Jaimini factors, birth-time sensitivity grid | preferred calculator; every interface (MCP, REST, CLI) uses it |
| **PyJHora 4.8.7** | local, separate `.venv-pyjhora` (AGPL — kept out of the package) | default ayanamsa TRUE_PUSHYA: call `set_ayanamsa_mode("LAHIRI")` | third opinion for Shadbala |

No engine in this project sends birth data anywhere; there is no cloud calculator.

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
  ascendant–MC quadrants (Swiss Ephemeris house system `O`), sandhis at the midpoints.
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

  Variants met elsewhere: other D2 schemes (not the Parashari hora), a different D7 rule for even signs, and D30
  variants (sometimes the other sign of the same lord). The local engine keeps the Parashari rule; the
  comparator labels the others *methodology*.
- **Vimshottari** to pratyantar; transits, slow-planet ingresses and exact Jupiter/Saturn/node contacts (dates are the
  local date of the change, like dasha dates); `transit_sign_aspects` — for transiting Jupiter and Saturn, each stay in
  a sign with the houses occupied and aspected (whole-sign graha drishti, Ju 5/7/9, Sa 3/7/10), from the lagna and the
  Moon. Combustion, natal graha drishti and the other derived facts come from the skill's `chart_facts.py` (one
  implementation, conventions named) and are returned by `prepare_consultation` as `derived_facts`.
- **Shadbala** (`strength.py`, BPHS ch. 27 as worked by B. V. Raman) — conventions in `SHADBALA_CONVENTIONS`:
  saptavargaja 45/30/20/15/10/4/2 over D1/D2/D3/D7/D9/D12/D30; dig from the ascendant/MC; natonnata from local
  apparent time; tribhaga from actual sunrise/sunset; abda/masa via the Ahargana from Creation (Burgess's 714,404,108,573 days to 1 Jan 1860, as BPHS ch. 27 prescribes; golden test: BPHS's 1 Jun 1984 example → Jupiter/Venus — v3.5 used a Kali-epoch count with the Creation formula and gave wrong lords);
  ayana (24° ± kranti)×1.25 with the kranti of the ecliptic point (BPHS bhuja method; v3.5 used true declination, which can leave 0–60); Sun's cheshta = ayana, Moon's = paksha (Raman); others' cheshta kendra with a
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

`astro/calc/compare.py` (`python -m astro.calc.compare --local calc.json --other facts.json --out OUT`) compares the
local engine with another engine's normalized facts (offline; nothing is fetched) and classifies every difference:

| Verdict | Meaning |
|---|---|
| match | < 0.05′, or identical sign/nakshatra/varga/lord |
| within tolerance | ≤ 1′ (ascendant ≤ 3′); bhava ≤ 0.5°; dasha boundary ≤ 3 days under the same year length |
| methodology | a documented school difference (variant varga, Shadbala sub-rule, arudha exception) |
| configuration | a setting differs (dasha year length) |
| implementation | the other engine contradicts its own inputs or a published worked example |
| unresolved | a real disagreement nobody has explained — a release blocker |
| not comparable | quantities that are not the same thing |

**Development cross-checks (history).** Until 3.6.0 the engine was also compared with an external cloud engine;
that comparison was removed on 2026-10-10 (the owner's decision: the local engine must stand on its own). Its record:
0 unresolved differences on the synthetic charts S1, S2 and one private chart; every remaining difference was a
documented convention (dasha year length, varga variants, Shadbala sub-rules) or a defect in the other engine. The
local engine is now validated by property tests, published worked examples (golden values), the 22-chart edge suite
and the PyJHora cross-check below. Dasha: the balance fraction is checked against one published table value
(N. C. Lahiri's table as reproduced by Raman) and, privately, one published chart; dasha year length and antardasha
boundaries are checked by arithmetic only. Since VedAstro's removal no second engine cross-checks every chart.

**Differences found in PyJHora** (reported, not copied):

| Engine | Finding | Verdict |
|---|---|---|
| PyJHora | cheshta mean taken as a plain average — fails when mean and true longitude straddle 0° Aries (Jupiter 12.6 instead of about 47 virupas on S2) | implementation |
| PyJHora | Saturn dig bala 73.3 virupas (exceeds the 60 maximum) | implementation |

## 6. Tests

`tests/test_calc_properties.py` (Hypothesis): longitude → sign/nakshatra/pada; boundaries; varga identities;
Vimshottari structure; time-zone shifts; nodes opposite. `tests/test_reference.py`: Lahiri at J2000, S1 engine
agreement, schema rejection, sensitivity, slow contacts. `tests/test_strength.py`: Raman 1918 drik golden
(`tests/reference_charts/`), Ashtakavarga totals property, Shadbala component ranges, circular mean across 0° Aries,
karaka/arudha properties, S1 sensitivity classes. `tests/test_service.py`: the MCP/REST/CLI interfaces and their
privacy guards. `tests/test_edge_cases.py`: invariants for western longitudes and negative offsets, DST, +05:45, +09:30,
southern hemisphere, equator, date line, the ephemeris-file range edge, outer-planet stations and node sign boundaries.
`tests/test_regressions.py`: one test per defect found in the 2026-10-03 review. All on synthetic or published charts.

**Time-lord convention (Shadbala vara, hora, abda, masa).** They are taken from the civil date of the local sunrise at
the UTC offset given. Positions, houses and dashas depend only on the instant and place (the edge-case suite restates
each test instant in UT and across the date line and requires identical results), but the time lords can change when the
same instant is given with a different civil offset — e.g. a date-line island restated from +14 to −10. Give the offset
that was legally in force at the birth place.

## 7. Limits

No time-zone database (give the UTC offset, including daylight saving); no Chara, Yogini or Narayana dasha (not added
without a second engine to compare against and tests); no ishta/kashta phala or bhava bala; outside 1800–2399 the
engine uses Moshier and says so.
