# Source index, citation format and retrieval

The books in `~/Documents/Astrology Books` are the authoritative evidence. The Lal Kitab knowledge base and
Varshaphal CSV (in `data/lal-kitab/`) are validated *derived* references. Page-cited source maps built from full reads of
each book live in `_skill_workspace/sourcemaps/` (development material, not loaded at runtime).

## 1. Sources

| ID | Work | Author / translator, edition in folder | Tradition | Text layer | Page convention |
|---|---|---|---|---|---|
| PD | Phaladeepika | Mantreswara, tr. V. Subrahmanya Sastri, 1950 | Classical Parashari (verse + translator notes) | Image scan; local OCR (Apple Vision) | PDF p; printed ≈ PDF − 30; cite Adh./sloka |
| BJ | Brihat Jataka | Varahamihira, tr. N. Chidambaram Iyer (scan dated 1885 on title page; catalogue metadata says 1905) | Classical (verse + Iyer's notes, which add Vimshottari) | Old OCR layer | PDF p; printed ≈ PDF − 38; cite ch./stanza |
| PM2 | Prasna Marga Part II (ch. XVII–XXXII) | tr. & notes B. V. Raman | Kerala prashna classic; some natal chapters | Clean | PDF p; cite ch./stanza; mark {PRASHNA}/{NATAL} |
| HJH2 | How to Judge a Horoscope Vol. 2 (houses 7–12) | B. V. Raman, 5th ed. reprint | Modern Parashari teaching, ~230 worked charts | Clean | PDF p; printed = PDF − 7 |
| HPA | Hindu Predictive Astrology | B. V. Raman | Modern Parashari teaching; simplified Tajika annual | Scan; local OCR | PDF p (≈ two printed pages per PDF page) |
| LOL | Light on Life | H. de Fouw & R. Svoboda, 1996 | Modern Parashari teaching (+ Jaimini notes), 8 case charts | Clean | PDF p; printed = PDF − 28 |
| LKS | Lal Kitab (English) | Pt. Radhakrishna Shrimali, Diamond 2013 | Modern Lal Kitab popularisation; mixes Vedic rules | Clean | PDF p (no printed pages) |
| KB | LalKitab_Shrimali_Knowledge_Base_v2.2 | derived from LKS, audited v2–v2.2 | Lal Kitab (tagged LK/VED/AUTH/MIXED) | — | Section id + LKS PDF page |
| VT | LalKitab_Varshaphal_Table_v2.2.csv | Shrimali + LK1952 reconciliation | Lal Kitab annual table | — | age_year row |
| LK1952 | Lal Kitab 1952 | Pt. Roop Chand Joshi; Hindi re-typeset of the Urdu original by V. Nagpal | Primary Lal Kitab (transliteration, not facsimile) | Glyph-broken layer; local Hindi OCR | PDF p + edition page ("पेज नंबर"), ≈ PDF − 21 early |
| BPHS | Brihat Parasara Hora Sastra, Vols 1–2 | Parasara, tr. R. Santhanam (Ranjan) | Classical Parashari (verse + translator notes) | PDF text layer (Sanskrit garbled; English readable) | PDF p; cite ch./sloka |
| JSR | A Course on Jaimini's Upadesa Sutra, Vol. 1 | Sanjay Rath (translation + commentary) | Jaimini (SJC) | PDF text | PDF p; cite sutra no. |
| CRUX | Crux of Vedic Astrology: Timing of Events | Sanjay Rath, 1998 | Modern SJC timing (Parashari + Jaimini) | Local OCR | PDF p |
| PVR | Vedic Astrology: An Integrated Approach | P. V. R. Narasimha Rao | Modern textbook (Parashari, Jaimini, Tajika; §33 on rational method) | PDF text | PDF p; cite chapter § |
| KNRT | Timing Events through Vimshottari Dasha | K. N. Rao | Modern Parashari timing, case-based | Local OCR (original text layer garbled) | PDF p |
| HJH1 | How to Judge a Horoscope Vol. 1 (houses 1–6) | B. V. Raman | Modern Parashari teaching (companion to HJH2) | PDF text | PDF p |
| JP2 | Jataka Parijata Vol. 2 (ch. 10–18) | Vaidyanatha Dikshita, tr. V. Subrahmanya Sastri, Mysore 1933 | Classical Parashari | Local OCR (large scan) | PDF p; cite ch./sloka |
| SAR1 | Saravali Vol. 1 | Kalyana Varma; loose modern English rendering by Dr. Manoj Kumar | Classical content, paraphrased | PDF text | PDF p; verify wording before citing as the classical text |
| DEVA2 | Deva Keralam (Chandra Kala Nadi) Vol. 2 | Nadi text, tr. R. Santhanam | Nadi (separate system) | Local OCR | PDF p; cite verse |
| NAKS | The Nakshatras: The Stars Beyond the Zodiac | Komilla Sutton | Modern nakshatra teaching | PDF text | PDF p |

Added 2026-09-25/26. Mapping status is tracked in `_skill_workspace/sourcemaps/STATUS.md`: books with validated
source maps contribute page-cited rules to `kg.py find/sources`; books still pending are searchable page by page with
`search.py --src <ID>` and appear in the graph's page layer only. Nadi (DEVA2) and KP-style material stay in their own
notes like Jaimini and Lal Kitab.

Not in the library, and therefore only "external knowledge" if used: BPHS, Saravali, Jataka Parijata, K. N. Rao's
works, KP, Raman's *Varshaphal*, Sanjay Rath, P. V. R. Narasimha Rao (used by v2.2 via web pages — see §5).

## 2. Reliability notes

- **Classical verse vs commentary.** PD and BJ mix verse translations with the translators' notes; BJ's Vimshottari
  material is Iyer's addition, not Varahamihira. Keep them apart when citing.
- **Raman's books** are his teaching and case experience; his own statistics (e.g. the 10th decided career in 15 of
  50+ charts) show the limits he acknowledges.
- **OCR**: PD and HPA were OCR'd locally; tables may be damaged — the source maps mark `[image-checked]` where a page
  image was read. BJ digits are sometimes garbled (e.g. Saturn's 19 read as 9).
- **Lal Kitab**: KB/VT fidelity is to Shrimali's English book (plus LK1952 for the table), not to the Urdu original.
  LK1952 in this folder is a Hindi re-typeset with its own errors (e.g. VT rows 21, 78). Authorship is disputed (R52).
- **No source here establishes predictive validity.** Textual authority shows what a tradition teaches.

## 3. Citation format

`Source → chapter/verse → page → rule → application`, e.g.
"Phaladeepika XV.6 (PD p184, pr 154) — a house is destroyed when house, lord and karaka are all weak… → here the 7th,
its lord Mars and Venus are each afflicted, so the confluence condition is met."
Mark each claim as **source statement**, **inference**, **synthesis** or **external knowledge**.

## 4a. Knowledge graph (local, private)

`scripts/kg.py` reads the Graphify graph built from all eight books, the KB and the contradiction register
(`_skill_workspace/graphify-out/graph.json`, override with `ASTRO_KG`). Every rule node carries source, page (PDF and
printed), verse, section, tier and the date and method of extraction. Tiers:
**classical** (verse or root text: PD, BJ, PM2 verses, LK1952), **traditional** (translator/commentator notes),
**modern** (Raman, LOL, Shrimali), **synthesis** (reader notes, this skill's inferences). Rules are paraphrases made
from full reads of each book, so confirm wording with `search.py --page` before quoting. In a measured test the graph +
full-text combination found the right source pages for 16 of 17 questions against 9 of 17 for full-text search alone
(`_skill_workspace/validation/retrieval_eval.md`).

## 4. Retrieving passages (local, private)

A full-text index of all eight books (one row per page, with source id and page) is at
`~/Documents/Astrology Books/_skill_workspace/index/library.sqlite` (override with `ASTRO_LIBRARY_DB`).

```bash
python3 scripts/search.py                                   # list sources
python3 scripts/search.py '"seventh lord" dasa' --src HJH2 -n 5
python3 scripts/search.py 'NEAR(Jupiter transit marriage, 20)' --src PM2,HJH2
python3 scripts/search.py 'कुंडली सोया' --src LK1952            # Devanagari works
python3 scripts/search.py --page PD:184                     # read the whole page
```

Search in each book's own vocabulary: Shrimali (LKS) writes "permanent house" (not *pakka ghar*), "debt" (not *rin*);
LK1952 is Hindi (पक्का घर, ऋण, वर्षफल); Raman writes "Dasa/Bhukti", LOL "dasha/bhukti", PD "Dasa/Apahara".
Use it to confirm a rule before citing it, to fetch a disputed passage, or to answer "where does this come from?".
Nothing leaves the machine. The index contains copyrighted text for the user's private use: quote briefly, paraphrase
otherwise, and do not bundle it into distributable packages. Rebuild with
`python3 _skill_workspace/tools/build_index.py` after adding books (procedure in `_skill_workspace/docs/ARCHITECTURE.md`).

## 5. Web sources inherited from v2.2

v2.2's Vedic references were drawn from web transcriptions (wisdomlib Phaladeepika OCR, a BPHS blog transcription,
Barbara Pijan Lama's BPHS ch. 34 compilation, PVR's online textbook, Rath's argala article, publisher metadata for
K. N. Rao, Swiss Ephemeris docs, Drik Panchang). v3 replaces the Phaladeepika and Brihat Jataka web citations with the
local editions. PVR, Rath, BPHS and K. N. Rao remain **external** and are flagged as such wherever a rule still rests
on them (vargas.md D9/D10 arithmetic and PVR varga usage; argala; double transit). The full v2.2 source ledger is
preserved in `docs/legacy-v2.2-sources.md`.
