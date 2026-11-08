post-B4 re-run (engine fix 19b857d); NOT the score of record, which stays 95.85/100 (report-2026-11-07.md)

# Calculation accuracy: scored run

Run (UTC): 2026-11-07T18:11:02Z

**Total: 99.60 / 100.00** (K = coverage; the rubric requires K = 100)

Without the private G2 fixtures: 99.60 / 100.00. With them: not computed in this run (private fixtures not read; owner's private run).

## Per area

| Area | Weight | Cases scored (pass/n by grade) | Area score | Points |
|---|---|---|---|---|
| A1 Positions, ayanamsa, houses | 20 | G1 58/58, G3 27/27, G4 2/2 | 100.00% | 20.00 |
| A2 Vargas, nakshatra, pada | 15 | G1 11/11, G3 9/9, G4 9/9 | 100.00% | 15.00 |
| A3 Vimshottari | 14 | G2 2/2, G3 60/60 | 100.00% | 14.00 |
| A4 Yogini | 4 | G3 30/30 | 100.00% | 4.00 |
| A5 Chara | 5 | G4 6/6 | 100.00% | 5.00 |
| A6 Panchang and sunrise | 9 | G1 44/44, G3 22/22, G4 11/11 | 100.00% | 9.00 |
| A7 Tajika | 7 | G1 18/18, G2 13/15 | 94.29% | 6.60 |
| A8 Shadbala | 8 | G2 4/4, G3 1/1, G4 1/1 | 100.00% | 8.00 |
| A9 Ashtakavarga | 6 | G2 8/8, G3 11/11 | 100.00% | 6.00 |
| A10 Edge cases | 12 | G1 24/24, G3 14/14 | 100.00% | 12.00 |

## Per grade (reported, not part of T)

| Grade | Weight | Score |
|---|---|---|
| G1 | 4 | 100.00% |
| G2 | 3 | 97.33% |
| G3 | 2 | 100.00% |
| G4 | 1 | 100.00% |

## Failing cases (2; lost points sum 0.40 = K - T 0.40)

| Case | Area | Grade | Quantity | Lost | Failing atoms |
|---|---|---|---|---|---|
| A7-G2-009 | A7 | G2 | tajika_sahams | 0.20 | Samartha: expected 335.03333333333336, engine 334.98 (diff -3.2); Vanik: expected 247.06666666666666, engine 247.02 (diff -2.8) |
| A7-G2-010 | A7 | G2 | tajika_positions | 0.20 | Asc: expected 157.21666666666667, engine 157.26 (diff 2.6) |

## Different school (informational, never scored: 25)

| Row | Quantity | Result |
|---|---|---|
| A2-G4-I001 | varga school D2 method 1 | D2 method 1: 6000/7200 grid points |
| A2-G4-I002 | varga school D2 method 3 | D2 method 3: 6600/7200 grid points |
| A2-G4-I003 | varga school D2 method 4 | D2 method 4: 6600/7200 grid points |
| A2-G4-I004 | varga school D2 method 6 | D2 method 6: 6000/7200 grid points |
| A2-G4-I005 | varga school D24 method 2 | D24 method 2: 3000/7200 grid points |
| A2-G4-I006 | varga school D24 method 3 | D24 method 3: 3600/7200 grid points |
| A2-G4-I007 | varga school D30 method 2 | D30 method 2: 6720/7200 grid points |
| A2-G4-I008 | varga school D30 method 3 | D30 method 3: 6600/7200 grid points |
| A2-G4-I009 | varga school D30 method 4 | D30 method 4: 6720/7200 grid points |
| A2-G4-I010 | varga school D30 method 5 | D30 method 5: 6660/7200 grid points |
| A5-G4-I001 | sign years, other school: JSR p285 Sri Rama (Rath, Jaimini Chara) | same |
| A5-G4-I002 | sign years, other school: JSR p286 Einstein (Rath, Jaimini Chara) | same |
| A5-G4-I003 | sign years, other school: PVR Example 66, p247-249 (Narayana dasha) | same |
| A5-G4-I004 | sign years, other school: CRUX p72-74 Nehru (Narayana dasha; printed Le 10 read as 9, tests/test_chara.py) | same |
| A6-G4-I001 | hora lord at birth, day/12 and night/12 | differs: hora school Me / engine Su |
| A6-G4-I002 | hora lord at birth, day/12 and night/12 | differs: hora school Sa / engine Ju |
| A6-G4-I003 | hora lord at birth, day/12 and night/12 | same |
| A6-G4-I004 | hora lord at birth, day/12 and night/12 | same |
| A6-G4-I005 | hora lord at birth, day/12 and night/12 | same |
| A6-G4-I006 | hora lord at birth, day/12 and night/12 | differs: hora school Mo / engine Sa |
| A6-G4-I007 | hora lord at birth, day/12 and night/12 | differs: hora school Me / engine Sa |
| A6-G4-I008 | hora lord at birth, day/12 and night/12 | same |
| A6-G4-I009 | hora lord at birth, day/12 and night/12 | same |
| A6-G4-I010 | hora lord at birth, day/12 and night/12 | same |
| A6-G4-I011 | hora lord at birth, day/12 and night/12 | same |

## Excluded and boundary rows

| Case | Status | Note |
|---|---|---|
| A10-G4-001 | convention without source | no published school; only the flag is scored |
| A3-G2-003 | private | rubric Q5: scored only in the owner's private run; values never printed |
| A3-G2-004 | private | rubric Q5: scored only in the owner's private run; values never printed |
| A5-G4-002 | misprint | printed 5, corrected 2 (same book's other pages); excluded | engine: Cp=2 |
| A5-G4-003 | misprint | printed 6, rule value 9; excluded | engine: Sc=9 |
| A5-G4-009 | convention without source | BPHS states neither start nor year length |
| A7-G2-013 | misprint | recorded in astro/calc/tajika.py SOURCES['mudda']; excluded | engine: Ra.end=1993-07-16 |

Boundary atoms removed inside scored cases (rubric 6.2): 4.

## Provenance

- rubric: "docs/ACCURACY-RUBRIC.md"
- rubric_sha256: "0ee28d62bb73da4dfd7458bf0a728c00f5708eca018d714a63c5a585df9f0893"
- case_files_sha256: {"A1.json": "5f769435ac3aa4af8bd000849918820474d6cefe088dad2346c5b2f8ec1e6008", "A10.json": "ded2ac47f43c8a7482dc228e5c82b84355ca9ce7bbbdba5e44ec531debda7926", "A2.json": "11c194428091b04951d39e4d989b93aaf1bbb8244671f1cbb6dafea72afca884", "A3.json": "9be042512ee80a41c1125c946f794a90d0da5c8bcb6da6f71ef254b4e1c73266", "A4.json": "c401b33b0645e2057741a98149c3b7144edb1b939bcf1e381ea15eb184380a70", "A5.json": "682ec5e37acf8d0c682deaa3c4bded81fe3bf88293462a9a73de29c2b148b31b", "A6.json": "48a7e6367b4c4ab2e9c15f55f42c70f5a0c015fe250b3900492275681517be75", "A7.json": "0b892f5357dd22fd446d6f34e6478806cecb4f24112de134530d0bc1b5410bfc", "A8.json": "266a0d35bde2ec64df14ad7d9a298afff694f1c6d9bcbf8dde8792eb103cbecd", "A9.json": "ac302da1ce2212ba77246af7da382256534784ffb77c4c09dec94c2b40a786df", "different-school.json": "11c4697cb4c838a646d9d60d0cf4ad074c2aef07794c057066cedab526cf3e8b"}
- scorer_sha256: "7560e5c4409ae87f5cb5c54fdc6d4a1eb10ea2db788458263f6139d49aeabbbf"
- engine: "astro 3.7.0"
- engine_code: "workspace [workspace] (not a git work tree); private clone HEAD a96fff261563eaa40c4cbdffbcaae4da8ff98d3a"
- python: "3.15.2"
- pyswisseph: "2.10.3.2"
- swiss_ephemeris: "2.10.03"
- ephemeris_files_sha256: {"dir": "ephe", "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7", "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66"}
- tzdb: "2026e-rearguard"
- stored_reference_runs: ["B. V. Raman, Graha and Bhava Balas, quoted in the PyJHora source (jhora/horoscope/chart/strength.py) PyJHora 4.8.7 source: tests/reference_charts/raman_1918.json", "PyJHora 4.8.7: pyjhora-4.8.7-2026-10-22", "PyJHora 4.8.7: pyjhora-4.8.7-bav-2026-11-07", "PyJHora 4.8.7: tests/reference_charts/crosscheck_2026_11.json", "PyJHora 4.8.7: tests/reference_charts/crosscheck_2026_11.json (generated 2026-11-01)"]
