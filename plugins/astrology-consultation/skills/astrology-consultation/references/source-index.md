# Source index, citation format and retrieval

Contents: [1. Sources](#1-sources) · [2. Reliability notes](#2-reliability-notes) · [3. Citation format](#3-citation-format) · [4a. Knowledge graph (local, private)](#4a-knowledge-graph-local-private) · [4. Retrieving passages (local, private)](#4-retrieving-passages-local-private) · [5. Web sources inherited from v2.2](#5-web-sources-inherited-from-v22)

The books in your own library (the folder set with `astro setup --knowledge-dir`) are the authoritative evidence.
Page-cited source maps are development material and are not loaded at runtime.

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
| KB | LalKitab_Shrimali_Knowledge_Base_v2.2 (private, not distributed in the public edition) | the owner's notes derived from LKS, audited v2–v2.2 | Lal Kitab (tagged LK/VED/AUTH/MIXED) | — | Section id + LKS PDF page |
| VT | LalKitab_Varshaphal_Table_v2.2.csv (private data file, not distributed) | Shrimali + LK1952 reconciliation | Lal Kitab annual table | — | age_year row |
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

Books with validated
source maps contribute page-cited rules to `kg.py find/sources`; books still pending are searchable page by page with
`search.py --src <ID>` and appear in the graph's page layer only. Nadi (DEVA2) and KP-style material stay in their own
notes like Jaimini and Lal Kitab.

In the library since v3.3 (searchable page by page; see the table above): BPHS, Saravali Vol 1, Jataka Parijata Vol 2,
K. N. Rao's *Timing through Vimshottari Dasha*, Sanjay Rath's *Crux*, P. V. R. Narasimha Rao's *Integrated Approach*.
Not in the library, and therefore only "external knowledge" if used: KP, Raman's *Varshaphal*, the other volumes and
works of these authors (v2.2 used some via web pages — see §5).

### 1a. Added 2026-11-12: Vedic books (searchable page by page; no source maps yet)

No rule from these books is in the graph. Read the page with `search.py --src <ID>` before using one, and cite PDF pages.

| ID | Work | Author / translator | Tradition and tier | Text layer | Use it for |
|---|---|---|---|---|---|
| PDK | Phaladeepika | Mantreswara, tr. and notes G. S. Kapoor | Classical Parashari (verse) + translator notes (traditional) | Clean text | The same verses as PD in a second translation, with notes: planets in the houses (ch. 8), rising signs (ch. 9), 7th house (ch. 10). Cite Adh./sloka; keep verse and note apart |
| BHRIGU | Bhrigu Sutras | translator not shown; attribution to Bhrigu unverified | Planet-in-house sutras (catalogued as Nadi; treat as traditional, not as classical verse) | Clean text | Each planet in each house with its conditions (dignity, lordship, companions) and the parallel lines of four other texts. Ages, illnesses and moral labels in it are never forecast |
| UKAL | Uttara Kalamrita | Kalidasa, tr. and notes P. S. Sastri | Classical Parashari (verse) + translator notes | Text + local OCR; lists lose items | What each house and planet signifies (ch. V), wealth and Viparita yogas (ch. IV). Check the page before citing |
| SARH | Saravali, Sanskrit with Hindi commentary | Kalyana Varma, Hindi by M. Chaturvedi | Classical Parashari (verse) | Local OCR, Hindi | The full text behind SAR1's paraphrase: planets in the houses (ch. 30). Search in Hindi |
| BEHARI2A, BEHARI2B | Planets in the Signs and Houses | Bepin Behari (two printings of one text; BEHARI2A is the cleaner copy) | Modern Parashari, one author's readings, unsourced | Clean text, some OCR slips | Sign-by-sign and planet-by-planet readings of each house, as one modern opinion. Never a stand-alone verdict; filter its moral, medical and death statements |
| SEERS | Astrology of the Seers | David Frawley | Modern Parashari introduction | Local OCR | Plain-language meanings of planets, signs and houses; not a rule source |
| BPHSGS2 | Brihat Parasara Hora Sastra Vol. 2 | Parasara, tr. G. C. Sharma | Classical Parashari (verse) | Local OCR, Sanskrit garbled | Dasha chapters in a second translation, to compare with BPHS |
| MC5, MCKDJ, MCKDJM, MCHI | Muhurta Chintamani (Sanskrit and Hindi editions) | Rama Daivajna, with commentaries | Classical Muhurta | Mixed, Sanskrit and Hindi | Electional rules only, not natal reading |
| MUHRAM | Muhurtha or Electional Astrology | B. V. Raman | Modern Muhurta | Clean text | Electional rules only |

A planet-in-house line from any of these is **one input**. Weigh it with the planet's lordship, dignity, aspects and
companions ([vedic-natal.md](vedic-natal.md) §3–5) before it enters an answer; PDK's own closing note says so.

### 1b. Added 2026-11-12: Western and Hellenistic books (a different system)

These use the tropical zodiac, other house systems, the outer planets and psychological meanings. **They are never
mixed into a Vedic reading and never cited as support for a Vedic rule.** They share the full-text index, but `search.py`, `kg.py` and the MCP search tools skip them by default (`kg.py` and the MCP tools have no switch: they always skip them) (only
the catalog systems Parashari, Jaimini, Lal Kitab, Nadi, Kerala Prashna, Tajika and Muhurta are searched); they are reached
only with `--src <ID>` or `--include-other-systems`. Use them only when the person asks for a Western view, in a
separate, labelled note, and say that this skill calculates sidereal positions, so their sign descriptions do not apply
to the chart as calculated.

| ID | Work | Author | System | Covers |
|---|---|---|---|---|
| TOMPKINS | The Contemporary Astrologer's Handbook | Sue Tompkins | Western modern | Signs, planets, aspects, houses, synthesis |
| RISKE | Llewellyn's Complete Book of Astrology | Kris Brandt Riske | Western modern | Signs, planets in signs and houses, aspects |
| TWELVEH | The Twelve Houses | author not shown; scan, local OCR | Western modern | The twelve houses and planets in them |
| KENTEG, WOOLFOLK, FORREST, ASTYOU, ARCHSTAN, DKASTRO, DKSECRETS | General introductions | Kent; Woolfolk; Forrest; Bloch and George; Stanley; Taylor (two titles, likely one text, not compared) | Western modern | Sun signs, rising signs, planets, houses |
| ARROYOKT, GREENESAT | Astrology, Karma & Transformation; Saturn | Stephen Arroyo; Liz Greene | Western modern (psychological) | Saturn, outer planets, ascendant, relationships |
| HANDPT, KENTTR | Planets in Transit; Astrological Transits | Robert Hand; April Elliott Kent | Western modern | Tropical transits |
| GREENELOV, GOLDYM | Astrology for Lovers; The Astrology of You and Me | Liz Greene; Gary Goldschneider | Western modern | Sun-sign relationships |
| BRENNAN | Hellenistic Astrology | Chris Brennan | Hellenistic (history and technique) | Places, lots, sect, time lords; its own system |
| TARNAS, ALTEA, GOLDBD | Cosmos and Psyche; Soul Signs; The Secret Language of Birthdays | Tarnas; Altea; Goldschneider and Elffers | Not chart technique | Reference only; never a source for a reading |

## 2. Reliability notes

- **Classical verse vs commentary.** PD and BJ mix verse translations with the translators' notes; BJ's Vimshottari
  material is Iyer's addition, not Varahamihira. Keep them apart when citing.
- **Raman's books** are his teaching and case experience; his own statistics (e.g. the 10th decided career in 15 of
  50+ charts) show the limits he acknowledges.
- **OCR**: PD and HPA were OCR'd locally; tables may be damaged — the source maps mark `[image-checked]` where a page
  image was read. BJ digits are sometimes garbled (e.g. Saturn's 19 read as 9).
- **Lal Kitab**: KB/VT fidelity is to Shrimali's English book (plus LK1952 for the table), not to the Urdu original.
  LK1952 in this folder is a Hindi re-typeset with its own errors (e.g. VT rows 21, 78). Authorship is disputed (R52).
- **Books added 2026-11-12**: PDK and PD translate the same verses, so the two count as one authority, not two; where
  the translations differ, name both. BHRIGU names no translator and its attribution is unverified: cite it as "the
  Bhrigu Sutras translation", never as a sage's verse. UKAL's OCR drops list items. Behari gives no sources: modern
  opinion. House-by-house lines in all of them are blunt (death, illness, moral and caste labels) and pass through
  [vedic-natal.md](vedic-natal.md) §9 before use.
- **No source here establishes predictive validity.** Textual authority shows what a tradition teaches.

## 3. Citation format

`Source → chapter/verse → page → rule → application`, e.g.
"Phaladeepika XV.6 (PD p184, pr 154) — a house is destroyed when house, lord and karaka are all weak… → here the 7th,
its lord Mars and Venus are each afflicted, so the confluence condition is met."
Mark each claim as **source statement**, **inference**, **synthesis** or **external knowledge**.

## 4a. Knowledge graph (local, private)

`scripts/kg.py` reads the Graphify graph built from the library's books and the contradiction register
(in the configured library; override with `ASTRO_KG`). Every rule node carries source, page (PDF and
printed), verse, section, tier and the date and method of extraction. Tiers:
**classical** (verse or root text: PD, BJ, PM2 verses, LK1952), **traditional** (translator/commentator notes),
**modern** (Raman, LOL, Shrimali), **synthesis** (reader notes, this skill's inferences). Rules are paraphrases made
from full reads of each book, so confirm wording with `search.py --page` before quoting. On a blind set of 24 questions the
graph + full-text combination found a right page for 17, full-text search alone for 16: use the graph for disputes and
cross-book context, not as a better page finder (an earlier curated 16-of-17 figure overstated it).

## 4. Retrieving passages (local, private)

A full-text index of your books (one row per page, with source id and page) lives in the configured library
(override with `ASTRO_LIBRARY_DB`).

```bash
python3 scripts/search.py                                   # list sources
python3 scripts/search.py '"seventh lord" dasa' --src HJH2 -n 5
python3 scripts/search.py 'NEAR(Jupiter transit marriage, 20)' --src PM2,HJH2
python3 scripts/search.py 'कुंडली सोया' --src LK1952            # Devanagari works
python3 scripts/search.py --page PD:184                     # read the whole page
```

Search in each book's own vocabulary: Shrimali (LKS) writes "permanent house" (not *pakka ghar*), "debt" (not *rin*);
LK1952 is Hindi (पक्का घर, ऋण, वर्षफल); Raman writes "Dasa/Bhukti", LOL "dasha/bhukti", PD "Dasa/Apahara".
A plain question rarely matches a book's words, so search the book's vocabulary: appearance - physique, complexion,
stature, "rising Navamsa"; intimacy - "bed comforts", "bed pleasures", conjugal; sudden gains - legacy, lottery, windfall,
speculation. The books added in 2026-11 use other words again: PDK and BHRIGU write "Ascendant", "native", "posited",
"first house" and "comforts of bed"; UKAL uses Sanskrit names (Ravi, Chandra, Kuja, Budha, Guru, Shukra, Shani),
"Bhava" and "Karakatvas"; Behari writes "the individual", "marriage partner", "legacy", "libido"; SARH is Hindi
(लग्नस्थ शुक्र का फल, सप्तमभावस्थ, द्वादशभावस्थ). A plain-word query that finds no page with every word is retried once with OR and says so.
Use it to confirm a rule before citing it, to fetch a disputed passage, or to answer "where does this come from?".
Nothing leaves the machine. The index contains copyrighted text for the user's private use: quote briefly, paraphrase
otherwise, and do not bundle it into distributable packages. Rebuild with
`astro add-book` after adding books (procedure in the repository's docs/ADD-A-BOOK.md).

## 5. Web sources inherited from v2.2

v2.2's Vedic references were drawn from web transcriptions (wisdomlib Phaladeepika OCR, a BPHS blog transcription,
Barbara Pijan Lama's BPHS ch. 34 compilation, PVR's online textbook, Rath's argala article, publisher metadata for
K. N. Rao, Swiss Ephemeris docs, Drik Panchang). v3 replaces the Phaladeepika and Brihat Jataka web citations with the
local editions. PVR, Rath's *Crux*, BPHS and K. N. Rao's *Timing* are in the library since v3.3 (§1); what still rests
on the v2.2 web pages (Rath's argala article, PVR's online textbook) remains **external** and is flagged as such wherever
a rule uses it (vargas.md D9/D10 arithmetic and PVR varga usage; argala; double transit). The full v2.2 source ledger is
preserved in `docs/legacy-v2.2-sources.md`.
