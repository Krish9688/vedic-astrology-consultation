# Accuracy pack: public copies (written by the exporter)

This repository shows the owner-signed rubric and the score reports (owner rule 2026-11-13); the frozen cases, the
scorer and the freeze record (`FREEZE.md`) are kept in the development repository. The public copies are redactions
(owner decision 2026-11-08): library PDF file names, private-folder paths and the name of the author's workspace folder
are replaced. No line is added or removed; nothing else changes. Python regular expressions, applied to each original
in this order (`re.sub`; group 1 is the quote character):

1. library PDF file name (quoted, PDF extension): `` (['`])((?:(?!\1)[^\n"\\]|"[ \t]*\n[ \t]*")*?)[.][pP][dD][fF]\1 `` → the opening quote, [library copy], the name's split-literal joins (if any, so no line is lost), the quote
2. private-folder path: `` privat[e]/(?:[\w.-]+/)* `` → `[private folder]/`
3. workspace folder name: `` _skill_[w]orkspace `` → `[workspace]`

To check a file: apply the substitutions to the original whose SHA-256 is listed, and compare the result's SHA-256
with the public one. Files with no substitution are byte-identical. The column "FREEZE.md" says whether the original
is one the freeze record lists and whether its hash matches it. A report's provenance lists the hashes of the case
files and scorer it was run with.

| File | FREEZE.md | Original SHA-256 | Public SHA-256 | Substitutions |
|---|---|---|---|---|
| `docs/ACCURACY-RUBRIC.md` | frozen, matches | `0ee28d62bb73da4dfd7458bf0a728c00f5708eca018d714a63c5a585df9f0893` | `02fd7a54c918e1e64c31bff7d0ef6ab95b4b31af8776ecb60a4e3b5af6567c07` | workspace folder name 1 |
| `docs/accuracy/report-2026-11-07-post-B4.md` | not frozen | `8e28bdf6aae19f2c06ae67c835b0bc79c4df61dcb7420e582a252c4328b60856` | `133710337619572c91c2e1451627d441ac9f5dc50bcdf172a06a5a5ed81c2d4c` | workspace folder name 1 |
| `docs/accuracy/report-2026-11-07.md` | not frozen | `82b0987ee6080b72097ce2d0e990ed70746894ecf75ea1781960b1f17dc67fc1` | `5d260badbdaee678f1be051cf4030d459ceefb4ae798bf766a6fcd211b9fb1a5` | workspace folder name 1 |
