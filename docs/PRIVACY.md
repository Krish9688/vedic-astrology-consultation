# Privacy

Birth data identifies a person and, with a chart, reveals things they may not want shared. This project keeps it on
the owner's machine unless the owner explicitly decides otherwise.

## 1. What stays local

| Data | Where | Leaves the machine? |
|---|---|---|
| Birth data and personal charts | `_skill_workspace/private/<person>/` | no |
| Local calculations (Swiss Ephemeris) | computed on the Mac | no |
| Books, extracted page text, full-text index, source maps, knowledge graph | `Astrology Books/` and `_skill_workspace/` | no |
| Consultations and reports about real people | wherever the person saves them; never in the skill or repository | no |
| Benchmark answers, grades, keys, the benchmark database | `_skill_workspace/private/benchmark/` | no |
| The list of personal terms the privacy check blocks | `~/.config/astrology-consultation/privacy-terms.txt` (outside every repository) | no |
| Service settings (`astro setup`) | `~/.config/astrology-consultation/config.toml`, mode 600 | no |
| Prediction log (consent-gated) | `~/.local/share/astrology-consultation/predictions.sqlite`, mode 600; not exposed over MCP or REST | no |

**Retention.** `astro purge --older-than DAYS` lists report files (`.html`, `.pdf` in the reports folder) and
prediction-log rows older than DAYS; add `--yes` to delete them (the log is vacuumed so deleted text does not linger).
Keep the data folder and the reports folder out of cloud sync and backups you do not control.

### Privacy modes of the `astro` service

| Mode | Calculation | External calls |
|---|---|---|
| `private` (default) | local only | none |
| `research` | local only | the AI client may also use public web research tools; chart data is still never sent to them |

There is no external calculation service: the former `hybrid` mode (a cloud engine cross-check) was removed on
2026-10-10, and an old `mode = "hybrid"` setting is read as `private`. If you used hybrid mode in 3.5.0 or 3.6.0,
its call log (`vedastro/calls.jsonl` in the engine's data folder) may still hold birth details sent to that service;
nothing reads it any more — delete it.

The MCP and REST servers bind to 127.0.0.1; listening elsewhere needs `allow_remote = true` **and** an `api_token`
(bearer auth on every request). No access logs are written and birth data is never logged. `skill://` resources and
report paths are confined to their folders; only skill documents can be read. CLI input comes from a JSON file, so
birth details stay out of shell history. An AI client that connects to the service still sees what it is sent —
choosing the client (local model, ChatGPT, Claude…) is a separate privacy decision.

## 2. What external services may receive

| Service | Receives | When |
|---|---|---|
| Agent Reach (Exa search, Jina Reader, YouTube) | public research queries only | never chart data or names |
| Hugging Face | nothing about the project — Docling downloads its models once | on first Docling use |
| GitHub | only the allowlisted, scanned repository files | on push |
| Claude (the model) | whatever is in the conversation | normal use; the skill asks before sending data to any *other* service |
| Jev Ultrafast (not installed) | would send page state to TypeSafe and OpenRouter and drive the user's real Chrome | rejected for this reason |

## 3. How publication is guarded

1. **Allowlist export** — `tools/export_repo.py` copies only listed paths into the repository and rewrites absolute
   home paths (`/Users/<name>/` → `~/`) and `private/<name>/` → `private/<person>/`.
2. **Privacy check** — `tools/privacy_check.py` blocks books and binaries (.pdf, .jsonl, .sqlite, .skill, …),
   personal and book-derived folders (private/, text/, index/, graphify-out/, source-map parts, benchmark results),
   files over 5 MB, absolute home paths, e-mail addresses, and every term in the local personal list (birth date in
   several formats, birth time with place, name). Runs in pre-commit and CI.
   Since 2026-10-18 (council 6) it also finds **birth-data records by their structure** — a labelled date/time/place of
   birth in many formats (dd/mm, month names, ordinals, `date_of_birth`-style keys, Hindi labels), and JSON records with
   a date and a time — after normalising Unicode and removing zero-width characters, so a person's data is caught even
   when no local term list exists (as in CI). A record passes only if the fingerprint of its whole line is listed in
   `tools/birthdata-reviewed.txt` (synthetic test charts and published book examples, reviewed by hand; fingerprints
   only, no dates). It refuses images and office documents outside an `assets/` folder, archives it cannot open,
   unreadable or non-UTF-8 text (fail closed), and package members in blocked folders.
3. **Gitleaks** — secrets in the working tree and the full git history (pre-commit and CI).
4. **Package check** — `tools/check_package.py` refuses a skill package containing private or benchmark folders or
   failing the privacy check.
5. **Synthetic fixtures** — every test and example uses the synthetic chart S1 or the fictional charts A/B, all
   calculated with the local engine.
6. **Packages are scanned before they are written** — `tools/build_package.py` runs the privacy check on every file
   and refuses to build on any finding.
7. **Reviewed files and contents** — every manifest line is `sha256  path` of the exported (sanitised) content. The
   public export must equal `tools/public-manifest.txt` and the private archive `tools/archive-manifest.txt`; a new,
   deleted, renamed or edited file — or an edited manifest line — fails the export (the archive before anything is
   copied). Updating a manifest is a two-step review: `--review` lists the differences and prints a token;
   `--write-manifest TOKEN` accepts exactly those differences (any later change invalidates the token) and only after
   the privacy check (and, for the public export, the B2 gate) passes on the exported copies. Symbolic links are never
   exported. Generated archive extras (compressed graph, environment lists, local-only manifest) are not in the
   manifest but are privacy-scanned in the archive.
8. **Other people's data** stays in an ignored local folder that no export rule reaches, under random identifiers,
   with a registry of source, permission, purpose and retention date; tests (`tests/test_privacy_boundary.py`, private)
   prove that every export path and the privacy check exclude it. Removing a name does not make a record shareable.
9. **Whose report is it?** — `astro.identity` compares the birth data a report prints with a person's own; only a
   matching (BOUND) report, or one the person confirms (PROVISIONAL), may inform that person's reading. Results name
   fields and statuses, never values.

Findings during the 2026-09-27 audit, fixed: the local engine's usage comment contained the owner's birth data as its
example (never packaged; replaced with S1); `kg.py`, `search.py` and `source-index.md` in the v3.3 package contain an
absolute path with the account name (no birth data) — replaced by `~`-relative defaults in v3.4.

## 4. API keys

No API key is needed for any part of the project. (The former VedAstro installation and its key file were moved to the
macOS Trash on 2026-10-10; the key's value was never read, printed or copied by this project.)
