# Roadmap

Ordered by value to consultation quality, not by size. Each item names what would show it worked.
Status as of 2026-10-28: 3.7.0 is released; the items below were last revised 2026-10-21 and several "Later" entries are
done or decided since (Chara D-3, pancha vargeeya bala D-6, Lal Kitab public split). Current task status is
authoritative in `.project-council/PROJECT-STATUS.md`; open work is tracked as GitHub issues (private #37-#41, public #14-#15).

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
5. **Reports**: done in the 3.6 cycle — Main-windows rule (the one-page summary type was added, then removed in round 12; `compact` remains) with a restatement warning, visual QA
   of all nine types (`tools/report_qa.py`); remaining: blind re-test (round 10, S3).
6. **Real-client verification**: Claude app plugin flow, a live model turn using the tools, ChatGPT/Codex migration.

## Later (deferred; decision and reasons recorded when the review ends)

- ~~Time-zone database for historical offsets~~ done 2026-10-21: IANA `zone` with fold, gap and pre-standard-time
  refusals and pre-1970 / pre-1948 South Asia flags; offline GeoNames place lookup.
- ~~Yogini dasha~~ done 2026-10-21 (BPHS ch. 46 mahadashas; the source gives no sub-period rule).
- **Chara / Narayana dashas: blocked on a source decision.** BPHS ch. 46 sl. 155–167 gives a pada-based Chara dasha
  whose verse is garbled (source map ❓), whose worked example does not settle whether the count is inclusive or what a
  lord in its own sign gives, and which differs from the Narayana/Chara methods CRUX and KNRT use; the texts do not
  reconcile them (BPHS_part4 reader note). Needs the owner's page check of BPHS p544–547 and a choice of school before
  one variant-named implementation. Ishta/kashta phala and bhava bala remain deferred.
- ~~Compatibility~~ done 2026-10-21 as facts, not a score: Prasna Marga XXI sign and star counts with their verses
  (`get_compatibility`). **36-point Ashtakoota: blocked** — no point table in the library (PM2 assigns no unit scores;
  NAKS prints 32 points, ❓); vasya, gana, yoni-animal, nadi, rajju and vedha tables are not in the source maps.
- ~~Tajika annual chart core~~ done 2026-10-21 (PVR ch. 27–28, 31; reproduces Examples 118 and 122). Still open:
  pancha vargeeya bala (neutral-sign value missing in the source), Patyayini and Varsha Narayana dashas, cusp-based
  sahams; Tajaka Neelakanthi is not in the library.
- Transit layer done 2026-10-21: PD XXVI gochara with vedha, sade sati, a dated personal outlook; Panchang (checked
  against USNO) done the same day.
- Hand-curated semantic graph relations (SUPPORTS, MODIFIED_BY).
- Further ayanamsas and house systems.

## Not planned (evaluated and rejected)

Vector database (no measured retrieval weakness), browser agents that need third-party keys (Jev), generic
"humanizer" prose rewriting, remedy upsell sections, month-by-month filler forecasts, Git LFS (gzip suffices), a public
tunnel for ChatGPT on the web (would expose birth data), a separate engine per AI client.
