# Roadmap

Ordered by value to consultation quality, not by size. Each item names what would show it worked.

## Next

1. **Curate the 125 automatic cross-book disputes** into the contradiction register (both positions, what each
   controls). Measure: dispute retrieval precision on the retrieval-eval set.
2. **Re-extract the table-heavy and mixed-script books with Docling** (LKS image tables, BPHS broken lines), re-map the
   affected pages, rebuild. Measure: real-word score and citation page match before/after; graph checks.
3. **Regenerate benchmark fixtures with the v3.4 engine output** (birth-time sensitivity in minutes, slow-planet
   contact dates) so answers never estimate either; re-run the timing-heavy benchmark questions.
4. **A prediction log**: record dated forecasts from consultations (with consent) and score them later — the only way
   to learn which techniques actually discriminate. Methodology in consultation-reasoning §8 and the research notes.
5. **Report types beyond career/12-month in the benchmark**: relationship, marriage, relocation, complete-life.

## Later

- Local Ashtakavarga and Shadbala (removing the last reasons to call VedAstro), with the engine differences tested.
- Swiss Ephemeris `.se1` files for full-precision positions (currently the Moshier fallback, adequate for astrology).
- Time-zone database for historical offsets (today the offset must be given).
- A compatibility (synastry / kuta) report type with its own research pass.
- Public repository: decide a licence; remove or re-license the bundled Lal Kitab knowledge base (docs/COPYRIGHT.md).

## Not planned (evaluated and rejected)

Vector database (retrieval already 16/17), browser agents that need third-party keys (Jev), generic "humanizer" prose
rewriting, remedy upsell sections, month-by-month filler forecasts.
