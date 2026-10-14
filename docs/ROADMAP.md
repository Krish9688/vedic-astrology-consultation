# Roadmap

Ordered by value to consultation quality, not by size. Each item names what would show it worked.
Updated 2026-10-03 (final-completion review in progress; this file is revised again when it ends).

## Done since the previous roadmap (v3.4 → v3.5 / 3.5.0)

- The 125 automatic cross-book disputes curated (contradiction register section F; graph: 0 unresolved).
- Local Shadbala and Ashtakavarga, with every difference from PyJHora classified.
- Swiss Ephemeris `.se1` files (1800–2399, checksum-verified download; Moshier outside that range).
- Engine output (sensitivity minutes, slow-planet contacts) used directly by the benchmark fixtures.
- A consent-gated prediction log (synthetic records only so far).
- All eight report types in the blind benchmark (round 9).
- Licence decided (split: AGPL engine, Apache-2.0 scripts/plugin, CC BY 4.0 text); public marketplace repository.

## Now (being worked)

1. **Re-benchmark** the round-9 items where v3.5 did not beat v3.4 (strength consultation, career report,
   complete-life report) and the life areas last tested in round 7 — on a fresh synthetic chart, blind.
2. **Re-extract low-quality OCR pages** (BPHS, SAR1, JSR, JP2, Lal Kitab image tables) — controlled A/B, replace a page
   only when the new text is measurably better; measure retrieval before/after.
3. **Blind retrieval evaluation** on unseen questions (done as a development set: full text 16/24, hybrid 17/24; an unseen holdout is still needed).
4. **Calculation edge-case suite**: southern hemisphere, western longitudes and negative offsets, DST, +05:45/+09:30,
   equator, date line, outside 1800–2399, outer-planet stations, node sign boundaries.
5. **Reports**: done in the 3.6 cycle — one-page summary type, Main-windows rule with a restatement warning, visual QA
   of all nine types (`tools/report_qa.py`); remaining: blind re-test (round 10, S3).
6. **Real-client verification**: Claude app plugin flow, a live model turn using the tools, ChatGPT/Codex migration.

## Later (deferred; decision and reasons recorded when the review ends)

- Time-zone database for historical offsets (today the UTC offset at birth must be given, including daylight saving).
- Chara / Yogini / Narayana dashas; ishta/kashta phala; bhava bala.
- A compatibility (synastry / kuta) report type with its own research pass.
- Hand-curated semantic graph relations (SUPPORTS, MODIFIED_BY).
- Further ayanamsas and house systems.

## Not planned (evaluated and rejected)

Vector database (no measured retrieval weakness), browser agents that need third-party keys (Jev), generic
"humanizer" prose rewriting, remedy upsell sections, month-by-month filler forecasts, Git LFS (gzip suffices), a public
tunnel for ChatGPT on the web (would expose birth data), a separate engine per AI client.
