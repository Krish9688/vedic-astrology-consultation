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

### Privacy modes of the `astro` service

| Mode | Calculation | External calls |
|---|---|---|
| `private` (default) | local only | none — `compare_engines` with `live=true` is refused |
| `hybrid` | local, plus an optional VedAstro cross-check per call | VedAstro receives date, time, offset and coordinates (label "chart"); each call is logged to `calls.jsonl` with its arguments |
| `research` | as hybrid | the AI client may also use public web research tools; chart data is still never sent to them |

The MCP and REST servers bind to 127.0.0.1; listening elsewhere needs `allow_remote = true` **and** an `api_token`
(bearer auth on every request). No access logs are written and birth data is never logged. `skill://` resources and
report paths are confined to their folders; only skill documents can be read. CLI input comes from a JSON file, so
birth details stay out of shell history. An AI client that connects to the service still sees what it is sent —
choosing the client (local model, ChatGPT, Claude…) is a separate privacy decision.

## 2. What external services may receive

| Service | Receives | When |
|---|---|---|
| **VedAstro** (`api.vedastro.org`, via the `vedastro-local` MCP, `tools/vedastro_batch.py` or `astro compare --live` in hybrid mode) | birth date, time, UTC offset, coordinates and a place label (not a name) | only with the person's consent, per chart; the local engine is preferred. The MCP's default `profile.json` holds personal data: every call passes `use_profile=false` |
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
3. **Gitleaks** — secrets in the working tree and the full git history (pre-commit and CI).
4. **Package check** — `tools/check_package.py` refuses a skill package containing private or benchmark folders or
   failing the privacy check.
5. **Synthetic fixtures** — every test and example uses the synthetic chart S1 or the fictional charts A/B; VedAstro
   fixtures were fetched with synthetic data only.

Findings during the 2026-09-27 audit, fixed: the local engine's usage comment contained the owner's birth data as its
example (never packaged; replaced with S1); `kg.py`, `search.py` and `source-index.md` in the v3.3 package contain an
absolute path with the account name (no birth data) — replaced by `~`-relative defaults in v3.4.

## 4. API keys

The VedAstro key lives in `~/VedAstro/` (`API key.env`, `.env`). Its value was never read, printed or copied by this
project; only variable names were listed. No key is needed for any other part of the project.
