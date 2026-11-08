# Calculation accuracy rubric (method C) — DRAFT for owner sign-off

Status: draft by node T2.2a, 2026-11-07. Nothing in this file has been run or scored. The builder (T2.2b) writes the
reference set and the scorer only after the owner signs section 1; the auditor (T2.2c) checks both before the run.

## 1. Purpose, scope and the fixed-before-run rule

**Purpose.** One number from 0 to 100 that says how far the local engine (`astro.calc`, `astro/service.py`) can be
trusted for the calculations a consultation uses, with every lost point traced to a named failing case.

**Scope.** The ten areas in section 2. Out of scope for this score: interpretation, yogas, Jaimini karakas and arudhas,
the birth-time sensitivity grid, transits, ingresses and contacts, Lal Kitab, report rendering (see open question Q12).

**Fixed before any run.** Before the first scored run, these are frozen in one commit and signed below: grade weights,
area weights, tolerances, the boundary rule, the formula, and the full case list (ids, grades, sources, expected
values). After results exist:

- no weight, tolerance, grade or expected value changes for that run;
- no case is added, removed or reclassified for that run (a reference found to be wrong after the run is still scored
  as it stood; the fix applies to the next run, with a dated note);
- a new run with changed rules gets a new rubric version and its own sign-off.

| Item | Value |
|---|---|
| Rubric version | 0.1 (draft) |
| Frozen at commit | _(empty)_ |
| Case list file and SHA-256 | _(empty)_ |
| Owner sign-off (name, date) | _(empty)_ |
| Owner's changes to this draft | _(empty)_ |

## 2. Coverage and the project's documented settings

Every case states its settings. Defaults are the documented ones below; a case that uses another setting says so.

### 2.1 Settings as documented (file:line in `[workspace]/`)

| Setting | Documented value | Where |
|---|---|---|
| Ephemeris | Swiss Ephemeris 2.10.03 via pyswisseph 2.10.3.2, files `sepl_18.se1`/`semo_18.se1` (SHA-256 pinned); Moshier fallback | `docs/CALCULATION-ENGINES.md:16`, `:29-32`; `astro/calc/engine.py:7-9` |
| Engine version | 3.7.0 | `astro/calc/engine.py:34` (the doc still says 3.6.1: `docs/CALCULATION-ENGINES.md:16`) |
| Ayanamsa | Lahiri (`SIDM_LAHIRI`); options true_chitra, kp, raman | `astro/calc/engine.py:68`, `:73-74` |
| Ayanamsa value used for positions | true (mean + nutation); mean also reported | `tools/crosscheck/README.md` "Engine notes"; `astro/calc/engine.py:95-99` |
| Positions | apparent geocentric sidereal (`FLG_SIDEREAL\|FLG_SWIEPH\|FLG_SPEED`, no `FLG_TRUEPOS`) | `astro/calc/engine.py:168` |
| Longitude rounding | rounded once to 0.0001° (0.36″) before sign, nakshatra, varga and dasha | `astro/calc/engine.py:456` |
| Nodes | mean (true optional); Ketu = Rahu + 180° | `astro/calc/engine.py:4`, `:166-175` |
| Rasi houses | whole sign from the sidereal ascendant (`houses_ex` "W" for Asc/MC) | `astro/calc/engine.py:4-5`, `:187`, `:195` |
| Bhavas | Sripati: madhyas = Porphyry ("O") cusps, sandhis = midpoints | `astro/calc/engine.py:200-209`; `docs/CALCULATION-ENGINES.md:44-45` |
| Vargas | 16 Parashari vargas, rules in `VARGA_METHODS` | `astro/calc/engine.py:37-53`; `docs/CALCULATION-ENGINES.md:46-68` |
| Nakshatra and pada | 13°20′ and 3°20′ divisions from 0° sidereal Aries | `astro/calc/engine.py:254-256` |
| Vimshottari | balance = unelapsed fraction of the Moon's nakshatra; 365.256363-day year (365.25, 360 optional); dates shown as local dates | `astro/calc/engine.py:6`, `:31`, `:259-285`, `:463` |
| Yogini | BPHS ch. 46 sl. 195-200 (p563): opening yogini = (nakshatra number + 3) mod 8; no sub-periods; Vimshottari year length | `astro/calc/engine.py:288-305`; `astro/service.py:498-509` |
| Chara | one school, `bphs_santhanam` (decision D-3); exclusive count, footed direction, sl. 155-167 rules; dates from birth in sidereal years (a labelled convention); ch. 51 antardashas | `astro/calc/chara.py:1-30`; `astro/service.py:486-494` |
| Panchang | tithi 12°, karana 6° of elongation; yoga (Sun+Moon)/13°20′; vara of the Hindu day (sunrise to sunrise) | `astro/calc/panchang.py:4-7`, `:25-32` |
| Sunrise | centre of the disc, standard refraction (`rise_trans`, `BIT_DISC_CENTER`); polar day/night: 06:00/18:00 local apparent time, flagged | `astro/calc/panchang.py:28-31`; `astro/calc/strength.py:119-140` |
| Hora | equal 60-minute horas from sunrise, Chaldean order | `astro/calc/strength.py:55` |
| Tajika | PVR ch. 27-28, 31; sidereal solar return near birth + n × 365.256363 d; Patyayini year 365.2425 d; year-lord friendship: owner default (Sun and Mercury enemies), "friends" variant printed | `astro/calc/tajika.py:1-10`, `:20`, `:44`, `:98-100`; `astro/service.py:438-439` |
| Shadbala | BPHS ch. 27 as worked by B. V. Raman; sub-rules in `SHADBALA_CONVENTIONS`; required rupas BPHS p299 | `astro/calc/strength.py:3-6`, `:28`, `:43-65` |
| Ashtakavarga | BPHS bindu tables, no shodhana; totals 48/49/39/54/56/52/39 = 337 | `astro/calc/strength.py:6`, `:287` |
| Time zones | IANA zone or explicit `+HH:MM`; gap refused, fold required; LMT era needs an explicit offset; time lords from the civil date of local sunrise | `docs/TESTING.md:23-36`; `docs/CALCULATION-ENGINES.md:143-147` |

### 2.2 Areas and sub-items

| # | Area | Sub-items |
|---|---|---|
| A1 | Positions, ayanamsa, houses | ayanamsa (mean, true; 4 modes); sidereal longitude and speed of Su..Sa, Ra/Ke (mean and true); retrograde flag; Asc, MC; Porphyry points; Sripati madhya/sandhi |
| A2 | Vargas, nakshatra, pada | D1 sign; nakshatra and pada of every body; D2..D60 signs of every body and the lagna |
| A3 | Vimshottari | first lord; balance; MD, AD, PD start dates (internal, unrounded) and shipped local dates |
| A4 | Yogini | opening yogini; MD sequence and dates |
| A5 | Chara | sign years; dasha order and direction; antardasha order; ch. 50 start sign |
| A6 | Panchang and sunrise | sunrise and sunset instants; tithi, nakshatra, yoga, karana, vara at birth and at sunrise; element change instants |
| A7 | Tajika | varsha pravesh instant; annual lagna; day/night; muntha; harsha bala; pancha vargeeya bala; year-lord candidates and year lord; sahams; Mudda and Patyayini dashas; completed-years count |
| A8 | Shadbala | the six balas and their sub-components in virupas; totals in rupas; required rupas; time lords (abda, masa, vara, hora) |
| A9 | Ashtakavarga | bhinnashtakavarga bindus per planet and sign; sarvashtakavarga by sign and house |
| A10 | Edge cases | polar day/night; DST, offsets (+05:45, +09:30, west, date line), tzdb history, gap/fold; sign, nakshatra, pada, ascendant and D9 boundaries; near-sunrise births; leap days, midnight, Julian calendar input, ephemeris range edges |

**One area per case.** A case on a chart built as an edge case (the edge suite, the near-sunrise and time-zone cases)
belongs to A10, whatever quantity it checks. Other charts' cases belong to the quantity's own area. No case counts twice.

## 3. Evidence grades

Each case carries exactly one grade. Grade is decided by the quantity first, then by the source.

**Step 1: is the quantity school-dependent?** If books in the library or independent engines compute it by different
rules (not merely with a different setting), the case is **G4**, whatever its source. Otherwise go to step 2.
A difference that one shared setting expresses (ayanamsa, node type, year length, sunrise limb, refraction) is a
**setting**, not a school: the case records the setting and keeps G1-G3.

**Step 2: what fixes the expected value?**

### G1 — astronomical fact (weight 4)
- Counts: values from pyswisseph called directly in the reference script, with no import of `astro` and the same
  ephemeris files, ayanamsa mode and node type as the case settings. Allowed: `calc_ut`, `houses_ex`, `get_ayanamsa*`,
  `rise_trans`, `solcross_ut` (or bisection on `calc_ut`), `utc_to_jd`/`julday`, plus the fixed divisions every school
  shares: sign = 30°, nakshatra = 13°20′, pada = 3°20′, tithi = 12°, karana = 6°, yoga = 13°20′ of (Sun + Moon),
  weekday of a Julian day.
- Covers only: ayanamsa, longitudes, speeds and retrograde flags, Asc, MC, Porphyry points, sunrise/sunset, panchang
  element numbers and change instants, the solar-return instant, and sign/nakshatra/pada indices.
- Does not count: anything that needs a varga rule, a dasha rule or a strength rule; values produced by `astro.calc`
  (the edge suite's `golden` blocks were made by the engine 3.5.0, so they are regression snapshots, not evidence);
  a reference script that uses another ephemeris or other flags than the case records.
- Note: G1 shares the Swiss Ephemeris with the engine. It proves the wiring (time conversion, flags, ayanamsa, nodes,
  rounding, boundaries), not the ephemeris. Independent astronomy comes from G3 (Skyfield/JPL, USNO).

### G2 — published worked example (weight 3)
- Counts: a number printed in a book's worked example, exercise answer or table, with book, translator/edition, PDF
  page and printed page recorded, and the page checked by a person or agent that did not write the case.
- A known misprint is recorded as a case with status `misprint`: the printed value, the corrected value and the
  evidence (for example the same book's other pages). It is excluded from the denominator and listed in the report.
- Does not count: a value quoted second-hand (for example from another engine's source code) until the page is
  checked; a rule statement with no worked number (that fixes a G4 school, not a G2 value); a locator marked
  "not page-checked".

### G3 — independent-engine agreement (weight 2)
- Counts: an engine written by others and sharing no code with `astro`: PyJHora 4.8.7 (out of process, AGPL, numbers
  stored only), Skyfield with JPL DE421, USNO data, the IANA tz database through `zoneinfo`. The case records the
  engine version and every setting that matters (ayanamsa read back, nodes, `FLG_TRUEPOS` off, year length, varga
  method, sunrise limb and refraction), and they must match the case settings.
- Reference values are stored in a fixture; the run is offline and never re-runs the other engine.
- A known defect of the other engine (for example PyJHora's Saturn dig bala above 60, or its plain-average cheshta
  mean across 0° Aries: `docs/CALCULATION-ENGINES.md:127-130`) makes that row status `reference defect`, decided
  before the run, excluded and listed.
- Does not count: `tools/crosscheck/ref.py` for rule-derived outputs (vargas, Vimshottari): it calls swe directly but
  its rules are the project's own reading (see Q3). Its astronomical outputs may serve as G1 if it is extended to call
  `houses_ex` for Asc/MC instead of its own spherical trigonometry.

### G4 — convention case (weight 1)
- Counts: a school-dependent quantity, scored only against the school the project documents (section 7). The case
  names that school, where the project documents it (file:line), the source that fixes the documented school's value
  (a book page, or an independent engine set to that school), and the alternatives with their sources.
- A G4 case with no source for the documented school's value (for example Chara dates: BPHS states neither start nor
  year length, `astro/service.py:487`) is listed as `convention without source` and not scored.

## 4. Case schema and scoring

### 4.1 Case record (one JSON object per case; the builder chooses the file, never `.jsonl`)

| Field | Meaning |
|---|---|
| `id` | stable, `A<area>-G<grade>-<nnn>`; sort key |
| `area`, `sub_item` | from section 2.2 |
| `grade` | G1, G2, G3 or G4 |
| `source` | G1: reference script + swe call; G2: book, translator/edition, PDF page, printed page, example number, checker; G3: engine, version, run id; G4: school + its source |
| `settings` | ayanamsa, nodes, year length, sunrise limb/refraction, varga method, ephemeris; always written in full, never "default" |
| `input` | chart reference (fixture id: C1..C9, edge-suite id, S1, S2, published example number), never inline birth data |
| `quantity`, `expected`, `unit` | the value(s) compared; for a family, a list of atoms |
| `tolerance` | from section 6, in `unit` |
| `comparison` | `abs_diff`, `circular_diff` (longitudes), `exact`, `date_exact`, `instant_diff` |
| `boundary_margin` | distance of the reference value to the nearest category boundary, in the unit of section 6 |
| `status_before_run` | `scored`, `misprint`, `reference defect`, `convention without source`, `private` |
| `notes` | G4: documented school, alternatives and their sources; anything the auditor must know |

**Case = one quantity family on one chart**, e.g. "C4: D9 sign of all 10 points". It passes only if every atom
passes; failing atoms are listed. No partial credit (a family is small enough that a single wrong atom is a real
defect; boundary atoms are removed by the boundary rule, not by partial credit).

### 4.2 Outcomes

| Outcome | Counts in the denominator | Listed in the report |
|---|---|---|
| pass | yes | totals only |
| fail | yes | yes, with lost points and failing atoms |
| boundary (section 6.2) | no | yes |
| misprint (G2), reference defect (G3), convention without source (G4) | no | yes, separately |
| different school (informational G4 rows, section 5.3) | no | yes, in its own table |

### 4.3 Formula

Notation: area a, grade g; `n_ag` scored cases, `p_ag` passed; grade weight `W_g` (section 5.1); area weight `A_a`
(section 5.2, sums to 100).

1. Pass rate `r_ag = p_ag / n_ag` (a grade with `n_ag = 0` is absent from the area).
2. Effective grade weight `w_ag = W_g × min(n_ag, 5) / 5`. A grade with fewer than five cases counts proportionally
   less, so one lucky or unlucky case cannot carry a grade's full weight.
3. Area score `S_a = Σ_g w_ag × r_ag / Σ_g w_ag` (0 to 1).
4. Total `T = Σ_a A_a × S_a` over areas with at least one scored case. Coverage `K = Σ A_a` over those areas. The
   report prints both: "T / K". The builder must reach K = 100 before the run (Q9).
5. Lost points of a failing case c in area a, grade g: `L_c = A_a × (w_ag / Σ_g w_ag) / n_ag`. The sum of all `L_c`
   equals `K − T` exactly; the report lists every `L_c`.
6. Per-grade score (reported, not part of T): `G_g = Σ_a A_a × r_ag / Σ_a A_a`, over areas where g is present.

Why per-grade pass rates rather than one pooled count: pooled counting lets a large G3 sweep (for example 60 PyJHora
dasha cases) drown four G2 book examples, the opposite of the brief's intent that stronger evidence weighs more.

### 4.4 Determinism

- Fixed case order: sort by `id`. No random sampling; any sweep is a fixed list of inputs stored in the case file.
  If a property-style generator is used to build cases, its seed and the generated inputs are stored, and the run
  reads the stored inputs.
- Offline: all G2 and G3 expected values come from stored fixtures; nothing is fetched or re-run.
- The run fails (no score) if the Swiss Ephemeris files are missing or their SHA-256 differs from
  `docs/CALCULATION-ENGINES.md:31-32`: Moshier changes positions by up to 2.65″ (`:34`).
- The output records: rubric version, case-file SHA-256, engine version and git commit, Python, pyswisseph and Swiss
  Ephemeris versions, ephemeris file hashes, tzdb version, PyJHora version and run id of the stored fixture, Skyfield
  and DE421 hash if used, and the run's UTC time. Numbers in the report rounded to 2 decimals after computing.
- Two runs on the same commit must give byte-identical results apart from the run time.

## 5. Proposed weights

### 5.1 Grade weights

| Grade | Weight | Reason |
|---|---|---|
| G1 | 4 | A direct ephemeris value leaves no room for interpretation; failure means the engine's own wiring is wrong. |
| G2 | 3 | Independent humans computed and printed it; but print errors and old ephemerides add some doubt. |
| G3 | 2 | Independent code with matched settings; but engines share common mistakes and conventions. |
| G4 | 1 | Correct only relative to a chosen school; the evidence is often the project's own reading of a text. |

### 5.2 Area weights (sum 100)

| Area | Weight | Reason |
|---|---|---|
| A1 Positions, ayanamsa, houses | 20 | Every other figure derives from them. |
| A2 Vargas, nakshatra, pada | 15 | Used in every reading (D1, D9, D10, Moon nakshatra); errors are categorical. |
| A3 Vimshottari | 14 | The main timing tool of every consultation. |
| A4 Yogini | 4 | Secondary, conditional dasha (`astro/service.py:499`). |
| A5 Chara | 5 | One school, few published examples, used as a lens. |
| A6 Panchang and sunrise | 9 | Sunrise drives vara, hora, tribhaga and time lords; past defects lived here. |
| A7 Tajika | 7 | Annual forecasts; many rule lookups on top of one astronomical instant. |
| A8 Shadbala | 8 | Strength grades in readings; many sub-rules. |
| A9 Ashtakavarga | 6 | Used for transits; integer tables, simple but easy to mistype. |
| A10 Edge cases | 12 | Where real births break engines (DST, polar, boundaries, near sunrise). |

### 5.3 How G4 counts in the total (a better rule than "count only when matching")

The lead's suggestion was: G4 cases count only when they match the documented school; mismatches are "different
school". That rule can never lose points, so a G4 case would only ever add to the score. Proposed instead:

- **Scored G4 row:** expected value = the documented school's value. A fail means the engine does not follow the school
  the project says it follows. That is a real defect: it is scored and appears in the lost-points list.
- **Informational rows:** the same quantity under each alternative school (for example PyJHora's other D2 methods).
  A difference there is reported as "different school" in its own table, never scored, never in the lost points.

Example: D2 of a body. Scored G4 row: Parashari hora per `astro/calc/engine.py:38` (BPHS page to record), cross-read by
PyJHora D2 method 2 (0 of 7200 grid points differ, `tests/fixtures/oracle/pyjhora-edge.json`). Informational rows:
PyJHora D2 methods 1, 3, 4, 6 (6000-6600 of 7200 points differ) as "different school".

## 6. Tolerances

### 6.1 Per quantity

| Quantity | G1 | G2 | G3 | Reason |
|---|---|---|---|---|
| Ayanamsa (mean, true) | 0.1″ | printed precision | 0.1″ (PyJHora, same swe) | Same library and mode; the existing tests use 1e-5° (0.036″). |
| Longitude Su..Sa, nodes | 0.5″ | ½ of the last printed digit | 1″ PyJHora; 5″ Skyfield/DE421 | Engine rounds to 0.0001° (max 0.18″ error); DE421 and model differences reach a few arc-seconds. |
| Moon longitude | 0.5″ | ½ last digit | 1″ PyJHora; 10″ Skyfield | As above; the Moon's ephemeris differs most between sources. |
| Asc, MC, Porphyry points | 1″ | ½ last digit | 10″ | Pure spherical astronomy; other engines may compute obliquity/sidereal time slightly differently. |
| Speed | 1e-4°/day | n/a | 1e-3°/day | Only the sign matters for the retrograde flag. |
| Retrograde flag | exact | exact | exact | Except within 1 minute of a station (boundary rule). |
| Sign, nakshatra, pada, varga sign | exact | exact | exact | Categorical; boundary rule applies. |
| Dasha lords and order (Vimshottari, Yogini, Chara) | n/a | exact | exact | Categorical. |
| Vimshottari/Yogini instant (internal, unrounded Moon, same year length) | n/a | per book rounding | 1 s | Stored PyJHora run: max 0.115 s (`tests/fixtures/oracle/pyjhora-edge.json`). |
| Vimshottari/Yogini shipped local date | n/a | ±1 day (table rounding) unless the book gives exact times | exact date | Shipped dates are local dates (`engine.py:463`); boundary rule uses the 2380 s rounding bound (`tests/test_oracle_pyjhora.py:108`). |
| Sunrise, sunset | 1 s | 1 min (printed minutes) | 1 min (USNO rounds to minutes) | Same `rise_trans` call for G1. |
| Panchang element change instant | 5 s | 1 min | 1 min | Engine bisects to well below a second (`panchang.py:64`). |
| Tithi, nakshatra, yoga, karana, vara, hora lord | exact | exact | exact | Categorical; boundary rule applies. |
| Varsha pravesh instant | 1 s | 60 s | 30 s | PVR prints seconds, but a 1″ ayanamsa difference moves the return about 24 s. |
| Sahams, annual positions | 0.5″ (positions) | 2′ | 1′ | Sahams are sums of longitudes; books print arc-minutes. |
| Harsha bala, pancha vargeeya bala | n/a | exact (printed integers/units) | ±0.01 | Table lookups. |
| Shadbala component (virupas) | n/a | ½ of the last printed digit, min 0.02 | 0.5 virupa | Raman's drik example is printed to 0.01 (`tests/reference_charts/raman_1918.json`: 0.02). |
| Shadbala total (rupas) | n/a | ½ last digit, min 0.01 rupa | 0.05 rupa | Sums of components. |
| Ashtakavarga bindus | n/a | exact | exact | Integers. |
| UTC offset from tzdb | exact | n/a | exact | Legal offset at the instant. |

These are tighter than the development cross-check (1′ longitudes, 3′ ascendant, 3 days for dashas:
`tools/crosscheck/README.md` "Tolerances"). The score should catch what a consultation could notice; see Q8.

### 6.2 Boundary rule

- A categorical atom (sign, nakshatra, pada, varga sign, panchang element, retrograde flag, dasha date) is scored only
  if its reference value lies at least **2 × the grade's tolerance** from the nearest boundary of that category,
  measured in the unit of the tolerance (arc-seconds of D1 longitude for a varga; seconds of time for a date or a
  panchang element). Otherwise its outcome is `boundary`: excluded and listed.
- The margin is computed by the builder from the reference engine before the run and stored in `boundary_margin`
  (the cross-check golden already holds a `fragility` field per body: `tools/crosscheck/README.md`).
- Designed edge cases (A10) keep their atoms: the edge suite places each chart 30 s either side of the edge, which is
  far more than 2 × tolerance (the Moon moves about 16″ in 30 s; the ascendant about 7′). The builder re-derives each
  edge instant by bisection with swe directly, so the expected side comes from G1, not from the engine.
- Shipped dasha dates: if the reference instant lies within 2380 s of local midnight, the date atom is `boundary`.

## 7. G4 areas: documented school and alternatives

| Quantity | Documented school | Where documented | Alternatives (source) |
|---|---|---|---|
| D2 hora | Parashari: odd 0-15° Leo, 15-30° Cancer; even reversed | `engine.py:38`; `CALCULATION-ENGINES.md:50`, `:66-68` | PVR parivritti with even reversal; Raman method; parivritti dwaya (PyJHora D2 methods 1, 3, 4, 6) |
| D3 drekkana | Parashari 1st/5th/9th | `engine.py:39` | other drekkana schemes: to confirm from PyJHora's method list and PVR (to locate) |
| D7 saptamsha | even signs from the 7th | `engine.py:41` | other even-sign rule (`CALCULATION-ENGINES.md:66`) |
| D30 trimshamsha | Parashari 5/5/8/7/5 | `engine.py:50` | "other sign of the same lord" variant (`CALCULATION-ENGINES.md:67`) |
| Other vargas with several PyJHora methods | `VARGA_METHODS` | `engine.py:37-53` | the remaining "methodology" rows of the stored oracle record (10 in all, D2 included); the builder lists them by name |
| Sripati bhavas | madhya = Porphyry cusp, sandhi = midpoint | `engine.py:200-209` | Porphyry cusps as bhava starts; other cusp systems (sources to locate) |
| Chara dasha | BPHS ch. 46 (Santhanam), `bphs_santhanam` | `chara.py:1-30`; `service.py:486-494` | Rath's Jaimini Chara (JSR); PVR's Narayana dasha; K. N. Rao's Chara (not in the engine: `chara.py:3`) |
| Chara antardasha | BPHS ch. 51 sl. 7-12 (owner default 2026-10-24) | `service.py:488-491` | BPHS ch. 50 sl. 90-96 start from the lord's sign |
| Chara lord at home | 12 years (Rath's rule, JSR p276) | `chara.py:20-21` | BPHS is silent (`chara.py:20`); other schools' rule: to locate |
| Hora (time lord) | equal 60-minute horas from sunrise | `strength.py:55` | day and night each divided by 12 (Light on Life, PDF p211) |
| Shadbala sub-rules | `SHADBALA_CONVENTIONS` | `strength.py:43-65` | each entry names its variant: saptavargaja basis, dig from bhava madhyas, Santhanam's ayana variant, cheshta mean elements, yuddha by LOL (no Venus rule), drik curve |
| Tajika year lord friendship | Sun and Mercury enemies (Kesava's blocs) | `tajika.py:7-9` | "friends" variant (printed beside it) |
| Patyayini year | 365.2425 d (PVR p410-411, as mapped) | `tajika.py:44` | sidereal year |
| Polar sunrise fallback | 06:00/18:00 local apparent time | `panchang.py:31`; `strength.py:119-122` | no published school: `convention without source`; only the flag is scored (A10) |
| Chara dates | sidereal years from birth | `service.py:487` | BPHS states none: `convention without source` |

Settings, not G4: ayanamsa, node type, Vimshottari/Yogini year length, sunrise limb and refraction, sidereal (not
tropical) solar return. They are recorded in each case's `settings`.

## 8. Candidate case inventory

Abbreviations: XC = `tests/reference_charts/crosscheck_2026_11.json` (C1-C9, independent + PyJHora columns);
OR = `tests/fixtures/oracle/pyjhora-edge.json` (32 charts: 22 edge suite, S1, S2, 4 ayanamsa epochs, DST gap,
two Julian-calendar dates, south-west); ES = `tests/reference_charts/edge_suite.json`.

### A1 Positions, ayanamsa, houses
| Grade | Available | Gap / to build |
|---|---|---|
| G1 | XC independent column: ayanamsa, 9 bodies, Asc for C1-C9 (Asc via own trig: switch to `houses_ex`); `test_reference.py::test_lahiri_ayanamsa_j2000` (engine-based, rebuild as G1) | MC, Porphyry points, true node, speeds, other 3 ayanamsa modes at 4 epochs |
| G2 | none | a printed Lahiri ayanamsa value and a printed chart's longitudes (Raman, *Hindu Predictive Astrology*; PVR chart tables): to locate |
| G3 | OR: positions (300 atoms), ayanamsa (30), retro (150); XC PyJHora column; Skyfield via `tools/crosscheck/sky.py` (optional, not yet stored) | store a Skyfield run for C1-C9 |
| G4 | none stored | Sripati madhya/sandhi row, 1-2 cases |
| Rough count | G1 ~45, G2 ~2, G3 ~40, G4 ~2 | |

### A2 Vargas, nakshatra, pada
| Grade | Available | Gap |
|---|---|---|
| G1 | XC independent: sign, nakshatra, pada of 10 points, C1-C9 | add S1, S2 |
| G2 | none | a worked varga example (PVR ch. 2 or BPHS ch. 6-7): to locate |
| G3 | OR: 4800 varga atoms (chart method 1, D2 method 2) for school-free vargas | builder classifies each varga as school-free or G4 from PyJHora's method list |
| G4 | OR "varga rule" grid (25 rows: 15 match, 10 methodology) | BPHS page for each documented rule: to record |
| Rough count | G1 ~11, G2 ~1, G3 ~30, G4 ~10 + informational rows | |

### A3 Vimshottari
| Grade | Available | Gap |
|---|---|---|
| G2 | `test_dasha_reference.py::test_lahiri_table_taurus_25_10` (Lahiri table via Raman, *Hindu Predictive Astrology*; page to record); private fixtures `dasha_crux34`, `dasha_knrao` (`test_dasha_reference.py:31`, `:50`; not read by this node) | PVR Example 50 (PVR PDF p223); Raman HPA illustrations (HPA PDF p33-34, p129-130): to build and page-check |
| G3 | OR: MD 540, AD 4860 atoms; matched timing max 0.115 s | none |
| G4 | none (year length is a setting) | |
| Rough count | G2 ~4 public + 2 private, G3 ~60 | |

### A4 Yogini
| Grade | Available | Gap |
|---|---|---|
| G2 | rule only: BPHS ch. 46 sl. 195-200 (p563) | a printed Yogini worked example: to locate (not found in PVR text; K. N. Rao's *Timing through Vimshottari dasha* only mentions it, KNRT PDF p78) |
| G3 | OR: 240 Yogini MD atoms (30 charts) | none |
| Rough count | G2 0-1, G3 ~30 | |

### A5 Chara
| Grade | Available | Gap |
|---|---|---|
| G4 | `test_chara.py`: BPHS example (PDF p546-547, printed p555-556, page-checked by the owner 2026-10-24) sign years and sequence; printed tables; lord at home; ch. 51 orders; ch. 50 start | none needed to start; PyJHora Chara only as informational rows |
| Misprints (recorded, excluded) | Cp 5 (rule gives 2; Yogardha p551, Kendradi p553); Sc 6 (rule gives 9) | owner decision 2026-10-24 (`chara.py:27-30`) |
| Rough count | G4 ~8; misprint 2; convention without source 1 (dates) | |

### A6 Panchang and sunrise
| Grade | Available | Gap |
|---|---|---|
| G1 | XC independent: panchang at birth and at sunrise, C1-C9 | sunrise/sunset instants by direct `rise_trans` at fixed latitudes and dates (~12); change instants (~6) |
| G2 | definitions only (Light on Life ch. 7, PDF p207-224) | a printed almanac or worked panchang: to locate |
| G3 | OR: 180 panchang atoms; `test_panchang.py`: 4 USNO 2024 lunar-phase instants | USNO sunrise uses the upper limb: see Q4 |
| G4 | hora length (1 case, feeds A8 too: assign to A6) | |
| Rough count | G1 ~27, G3 ~34, G4 1 | |

### A7 Tajika
| Grade | Available | Gap |
|---|---|---|
| G1 | none | varsha pravesh instant by `solcross_ut` sidereal for C1-C9 at 3 ages (~10) |
| G2 | `test_tajika.py`, `test_tajika_annual_dashas.py`: PVR Examples 118 and 122, Exercise 47 (return, lagna, day/night, muntha, harsha bala, candidates, year lord, sahams, Mudda, Patyayini, PVB) | locators are "not page-checked" (`tajika.py:2`; `test_tajika_annual_dashas.py:1-2`): page-check before the run, or they cannot be G2 |
| G3 | none | PyJHora annual chart with matched settings (optional) |
| G4 | year-lord friendship variant; Patyayini year | |
| Rough count | G1 ~10, G2 ~12, G4 ~2 | |

### A8 Shadbala
| Grade | Available | Gap |
|---|---|---|
| G2 | uchcha bala (BPHS Santhanam printed p264; `test_strength.py:111`); required rupas (BPHS p299); abda/masa/vara (BPHS printed p271; `test_regressions.py:16`); Raman 1918 drik bala, 7 planets (`raman_1918.json`) | Raman's *Graha and Bhava Balas* is not in the library and the drik values are quoted from PyJHora's source: page-check or downgrade (Q6). A full worked Shadbala table: to locate |
| G3 | none stored | PyJHora Shadbala on S1/S2 for components whose sub-rules match; known PyJHora defects as `reference defect` |
| G4 | one case per `SHADBALA_CONVENTIONS` entry whose value a source fixes (~8) | sources for each |
| Rough count | G2 ~4-5, G3 0-7, G4 ~8 | |

### A9 Ashtakavarga
| Grade | Available | Gap |
|---|---|---|
| G2 | BAV totals = BPHS table sums (`test_strength.py:38`) | PVR Chart 6, Exercise 19 BAVs and SAV (PVR PDF p163-165, answer section to locate); PVR Example 39 SAV of the rasi chart (PVR PDF p166); BPHS bindu tables (BPHS PDF p835-843) as table-fidelity cases |
| G3 | none | PyJHora BAV/SAV for C1-C9 |
| Rough count | G2 ~3-4, G3 ~9 | |

### A10 Edge cases
| Grade | Available | Gap |
|---|---|---|
| G1 | ES: moon sign/nakshatra/pada, ascendant, D9 lagna, dasha-edge pairs (re-derive instants by swe); polar day/night flags; `test_strength.py:151`, `:159` near-sunrise regressions | turning-point sunrise cases at 50-65° N/S (from the T2a/T3v sweeps), ~6 |
| G3 | OR: 20 edge charts agree with PyJHora (fails on the 2 polar charts: not comparable); `test_timezones.py` tzdb cases (Kolkata 1943, London 1969, New York DST, Kathmandu 1986, gap and fold) | none |
| G4 | polar fallback convention: flag only | |
| Regressions to include | sunrise window (2a, T2a: fixed), tajika completed years (2a: fixed), varga EPS overflow for unrounded callers (2a: open) | |
| Rough count | G1 ~24, G3 ~28, G4 1 | |

### Totals (rough, before the builder's pass)

| | G1 | G2 | G3 | G4 | Total |
|---|---|---|---|---|---|
| Available now (needs rebuild into case records) | ~60 | ~10 | ~180 | ~20 | ~270 |
| After the listed gaps | ~120 | ~30 | ~240 | ~30 | ~420 |

The builder caps each grade at 60 cases per area, chosen by a fixed list, so the case file stays auditable.

## 9. Open questions for the owner

1. **G4 rule.** Accept section 5.3 (documented school scored, alternatives informational) instead of "G4 counts only
   when it matches"?
2. **Settings vs schools.** Treat ayanamsa, node type, year length, sunrise limb and refraction as settings (G1-G3 with
   matched settings), not G4?
3. **`ref.py` rule outputs.** The cross-check's own vargas and Vimshottari share no code with `astro` but share the
   authors' reading. Proposed: no grade (harness check only). Alternative: G3 at half weight.
4. **USNO sunrise.** USNO prints upper-limb sunrise to the minute; the engine uses the disc centre. Score as G3 with a
   2-minute tolerance, or informational only (proposed)?
5. **Private G2 cases** (`dasha_crux34`, `dasha_knrao`). Proposed: scored in the private run only; the report states
   the total with and without them, and never prints their values.
6. **Raman 1918 drik values** are quoted via PyJHora's source; the book is not in the library. Keep as G2 only after a
   page check; until then G3 (proposed)?
7. **PVR Tajika locators** are not page-checked. Page-check before the freeze (proposed), or grade them G3?
8. **Tolerances.** Accept 0.5″ (G1) and 1″ (PyJHora) for longitudes, tighter than the development cross-check's 1′?
9. **Unscored areas.** Proposed: no run until every area has scored cases (K = 100). Alternative: report T / K.
10. **Minimum-count factor** of 5 in `w_ag`: acceptable, or another number?
11. **Hora.** Confirm equal 60-minute horas as the documented school (Light on Life describes day/12 horas).
12. **Scope.** Jaimini karakas and arudhas (PVR Example 29 exists), the sensitivity grid and transit contacts are out
    of this score. Add them as an eleventh area later?
13. **Documentation drift** to fix before the freeze (outside this node): `CALCULATION-ENGINES.md:16` (3.6.1; lists
    Lahiri ICRC and Lahiri 1940, which `engine.py:73-74` does not offer) and `:151` ("no time-zone database; no Chara,
    Yogini" — both now exist). A rubric that quotes the docs needs them to match the code.
