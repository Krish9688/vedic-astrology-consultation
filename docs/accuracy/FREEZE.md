# Accuracy reference set: freeze record (before the scored run)

Frozen by node T2.2b on 2026-11-07, before the single scored run. Rubric: `docs/ACCURACY-RUBRIC.md` version 0.1,
owner-signed 2026-11-07, SHA-256 `0ee28d62bb73da4dfd7458bf0a728c00f5708eca018d714a63c5a585df9f0893` (unchanged by
this node). After the run no case, tolerance, grade or expected value changes for that run (rubric §1).

| File | SHA-256 |
|---|---|
| `docs/accuracy/A1.json` | `5f769435ac3aa4af8bd000849918820474d6cefe088dad2346c5b2f8ec1e6008` |
| `docs/accuracy/A2.json` | `11c194428091b04951d39e4d989b93aaf1bbb8244671f1cbb6dafea72afca884` |
| `docs/accuracy/A3.json` | `9be042512ee80a41c1125c946f794a90d0da5c8bcb6da6f71ef254b4e1c73266` |
| `docs/accuracy/A4.json` | `c401b33b0645e2057741a98149c3b7144edb1b939bcf1e381ea15eb184380a70` |
| `docs/accuracy/A5.json` | `682ec5e37acf8d0c682deaa3c4bded81fe3bf88293462a9a73de29c2b148b31b` |
| `docs/accuracy/A6.json` | `48a7e6367b4c4ab2e9c15f55f42c70f5a0c015fe250b3900492275681517be75` |
| `docs/accuracy/A7.json` | `0b892f5357dd22fd446d6f34e6478806cecb4f24112de134530d0bc1b5410bfc` |
| `docs/accuracy/A8.json` | `266a0d35bde2ec64df14ad7d9a298afff694f1c6d9bcbf8dde8792eb103cbecd` |
| `docs/accuracy/A9.json` | `ac302da1ce2212ba77246af7da382256534784ffb77c4c09dec94c2b40a786df` |
| `docs/accuracy/A10.json` | `ded2ac47f43c8a7482dc228e5c82b84355ca9ce7bbbdba5e44ec531debda7926` |
| `docs/accuracy/different-school.json` | `11c4697cb4c838a646d9d60d0cf4ad074c2aef07794c057066cedab526cf3e8b` |
| `docs/accuracy/fixtures/pyjhora-bav.json` (stored PyJHora run) | `fc47b0d10fc2bbe632dbd6085683a51c30322148dc7e3980899bb7a64cb29266` |
| `tools/accuracy_score.py` (scorer) | `7560e5c4409ae87f5cb5c54fdc6d4a1eb10ea2db788458263f6139d49aeabbbf` |
| `tools/accuracy_build_cases.py` (case builder, G1 reference script) | `b6d79965f9963a38dbe050ab0c7cb46b911812f1e60cabd89828264aac619f8f` |
| `tools/accuracy_charts.py` (chart-id registry) | `790a842dc77bcd2c61b0677e6f36933c984747eb4ee005661e76e5408c539ca1` |

Scored cases by area and grade (status `scored`):

| Area | G1 | G2 | G3 | G4 | Excluded rows |
|---|---|---|---|---|---|
| A1 Positions, ayanamsa, houses | 58 | 0 | 27 | 2 | |
| A2 Vargas, nakshatra, pada | 11 | 0 | 9 | 9 | |
| A3 Vimshottari | 0 | 2 | 60 | 0 | 2 private |
| A4 Yogini | 0 | 0 | 30 | 0 | |
| A5 Chara | 0 | 0 | 0 | 6 | 2 misprint, 1 convention without source |
| A6 Panchang and sunrise | 44 | 0 | 22 | 11 | |
| A7 Tajika | 18 | 15 | 0 | 0 | 1 misprint |
| A8 Shadbala | 0 | 4 | 1 | 1 | |
| A9 Ashtakavarga | 0 | 8 | 11 | 0 | |
| A10 Edge cases | 24 | 0 | 14 | 0 | 1 convention without source |

387 scored cases; 25 different-school rows (informational). Every area has scored cases: K = 100 (rubric Q9).

Before the freeze the scorer was run only in `--check-keys` mode (every extractor runs and returns every key its cases
name; no value is compared or shown), to keep scorer wiring errors out of the score.
