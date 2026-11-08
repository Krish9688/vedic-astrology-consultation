# Accuracy pack: public copies (written by the exporter)

The owner-signed rubric and the files frozen in `FREEZE.md` are unchanged in the private source. Their public copies
here are redactions (owner decision 2026-11-08): library PDF file names, private-folder paths and the name of the
author's workspace folder are replaced. No line is added or removed; nothing else changes. Python regular expressions,
applied to each original in this order (`re.sub`; group 1 is the quote character):

1. library PDF file name (quoted, PDF extension): `` (['`])((?:(?!\1)[^\n"\\]|"[ \t]*\n[ \t]*")*?)[.][pP][dD][fF]\1 `` → the opening quote, [library copy], the name's split-literal joins (if any, so no line is lost), the quote
2. private-folder path: `` privat[e]/(?:[\w.-]+/)* `` → `[private folder]/`
3. workspace folder name: `` _skill_[w]orkspace `` → `[workspace]`

To check a file: apply the substitutions to the original whose SHA-256 is listed (and in `FREEZE.md`), and compare the
result's SHA-256 with the public one. Files with no substitution are byte-identical.

The scorer (`tools/accuracy_score.py`) records the case-file and scorer hashes in a report's provenance but does not
compare them with `FREEZE.md`; it checks only the pinned ephemeris files. A run on these public copies therefore scores
the same cases with the same values, and its provenance shows the public hashes below, not the frozen ones.

| File | FREEZE.md | Original SHA-256 | Public SHA-256 | Substitutions |
|---|---|---|---|---|
| `docs/ACCURACY-RUBRIC.md` | frozen, matches | `0ee28d62bb73da4dfd7458bf0a728c00f5708eca018d714a63c5a585df9f0893` | `02fd7a54c918e1e64c31bff7d0ef6ab95b4b31af8776ecb60a4e3b5af6567c07` | workspace folder name 1 |
| `docs/accuracy/A1.json` | frozen, matches | `5f769435ac3aa4af8bd000849918820474d6cefe088dad2346c5b2f8ec1e6008` | `5f769435ac3aa4af8bd000849918820474d6cefe088dad2346c5b2f8ec1e6008` | none (identical) |
| `docs/accuracy/A10.json` | frozen, matches | `ded2ac47f43c8a7482dc228e5c82b84355ca9ce7bbbdba5e44ec531debda7926` | `ded2ac47f43c8a7482dc228e5c82b84355ca9ce7bbbdba5e44ec531debda7926` | none (identical) |
| `docs/accuracy/A2.json` | frozen, matches | `11c194428091b04951d39e4d989b93aaf1bbb8244671f1cbb6dafea72afca884` | `11c194428091b04951d39e4d989b93aaf1bbb8244671f1cbb6dafea72afca884` | none (identical) |
| `docs/accuracy/A3.json` | frozen, matches | `9be042512ee80a41c1125c946f794a90d0da5c8bcb6da6f71ef254b4e1c73266` | `fc09ac9a230d2f58695f1ad76962a9ba539e3f1c629bb7cf5d410f833c5c1665` | library PDF file name 1, private-folder path 2 |
| `docs/accuracy/A4.json` | frozen, matches | `c401b33b0645e2057741a98149c3b7144edb1b939bcf1e381ea15eb184380a70` | `c401b33b0645e2057741a98149c3b7144edb1b939bcf1e381ea15eb184380a70` | none (identical) |
| `docs/accuracy/A5.json` | frozen, matches | `682ec5e37acf8d0c682deaa3c4bded81fe3bf88293462a9a73de29c2b148b31b` | `5f6820d3fbf66c611ab21581a7d4afcd8fc1442d925f7c51be65fa4e445fd93e` | library PDF file name 7 |
| `docs/accuracy/A6.json` | frozen, matches | `48a7e6367b4c4ab2e9c15f55f42c70f5a0c015fe250b3900492275681517be75` | `48a7e6367b4c4ab2e9c15f55f42c70f5a0c015fe250b3900492275681517be75` | none (identical) |
| `docs/accuracy/A7.json` | frozen, matches | `0b892f5357dd22fd446d6f34e6478806cecb4f24112de134530d0bc1b5410bfc` | `0b892f5357dd22fd446d6f34e6478806cecb4f24112de134530d0bc1b5410bfc` | none (identical) |
| `docs/accuracy/A8.json` | frozen, matches | `266a0d35bde2ec64df14ad7d9a298afff694f1c6d9bcbf8dde8792eb103cbecd` | `9a2d51f32b6a08a66d61362254a7ec3e8804d40c5cce40a708a19ddb86f6b42e` | library PDF file name 5 |
| `docs/accuracy/A9.json` | frozen, matches | `ac302da1ce2212ba77246af7da382256534784ffb77c4c09dec94c2b40a786df` | `ac302da1ce2212ba77246af7da382256534784ffb77c4c09dec94c2b40a786df` | none (identical) |
| `docs/accuracy/AUDIT-2026-11-07.md` | not frozen | `a2995405d3256cb33332e494a8b0897921f99b2e4e720675a2a617df4c3c6fe1` | `095c8052e3713f8e7922407434adfe3410b9f99864dac322c7285ea470291543` | workspace folder name 1 |
| `docs/accuracy/FREEZE.md` | not frozen | `943a2d762c4cbf2777375121698ea60009bfa19c4723bc782c7ec73524fd3457` | `943a2d762c4cbf2777375121698ea60009bfa19c4723bc782c7ec73524fd3457` | none (identical) |
| `docs/accuracy/different-school.json` | frozen, matches | `11c4697cb4c838a646d9d60d0cf4ad074c2aef07794c057066cedab526cf3e8b` | `11c4697cb4c838a646d9d60d0cf4ad074c2aef07794c057066cedab526cf3e8b` | none (identical) |
| `docs/accuracy/fixtures/pyjhora-bav.json` | frozen, matches | `fc47b0d10fc2bbe632dbd6085683a51c30322148dc7e3980899bb7a64cb29266` | `fc47b0d10fc2bbe632dbd6085683a51c30322148dc7e3980899bb7a64cb29266` | none (identical) |
| `docs/accuracy/report-2026-11-07-post-B4.md` | not frozen | `8e28bdf6aae19f2c06ae67c835b0bc79c4df61dcb7420e582a252c4328b60856` | `133710337619572c91c2e1451627d441ac9f5dc50bcdf172a06a5a5ed81c2d4c` | workspace folder name 1 |
| `docs/accuracy/report-2026-11-07.md` | not frozen | `82b0987ee6080b72097ce2d0e990ed70746894ecf75ea1781960b1f17dc67fc1` | `5d260badbdaee678f1be051cf4030d459ceefb4ae798bf766a6fcd211b9fb1a5` | workspace folder name 1 |
| `tools/accuracy_build_cases.py` | frozen, matches | `b6d79965f9963a38dbe050ab0c7cb46b911812f1e60cabd89828264aac619f8f` | `fc97ee44c8257fa717bc9e98da584c966dbe785782ecd765dee5e6a5f5adffe0` | library PDF file name 2, private-folder path 1 |
| `tools/accuracy_charts.py` | frozen, matches | `790a842dc77bcd2c61b0677e6f36933c984747eb4ee005661e76e5408c539ca1` | `790a842dc77bcd2c61b0677e6f36933c984747eb4ee005661e76e5408c539ca1` | none (identical) |
| `tools/accuracy_score.py` | frozen, matches | `7560e5c4409ae87f5cb5c54fdc6d4a1eb10ea2db788458263f6139d49aeabbbf` | `f2a9cc43e6783f577d5857389a6a0f693cffc69ac47370ad1f03457fdfab1a5d` | workspace folder name 1 |
| `tools/crosscheck/charts_consultation.json` | not frozen | `69e885efb9ddd40a6046d4403fd5517269032f2e0eeae982b43928a138dff2c7` | `69e885efb9ddd40a6046d4403fd5517269032f2e0eeae982b43928a138dff2c7` | none (identical) |
| `tools/crosscheck/charts_synthetic.json` | not frozen | `75da77220e23070f6243d676497abe689053a1cf277062abf9465d7d26d8e6e1` | `75da77220e23070f6243d676497abe689053a1cf277062abf9465d7d26d8e6e1` | none (identical) |
| `tools/oracle_pyjhora.py` | not frozen | `404179b0c598e483869b260e8059f0f8ae2e6287856d3c2fdafcf1d3265c3eb9` | `404179b0c598e483869b260e8059f0f8ae2e6287856d3c2fdafcf1d3265c3eb9` | none (identical) |
