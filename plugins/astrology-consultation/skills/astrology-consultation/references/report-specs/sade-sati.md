# Sade Sati report spec (`sade-sati`)

Saturn's passage over the natal Moon: its phases with their pauses, the areas it presses on, how far the running dasha
agrees, and how to respond. Kantaka and Ashtama Shani appear as a separate, Weak section. Inside the shared frame
([README.md](README.md)). Sade sati is a broad lens, never a verdict (timing.md §3).

**Order (standard):** `windows` → `areas` → `fit` → `kantaka` → `response`

Inputs: `birth`, the period asked about (default: the current or next sade sati). Model: `report_type: "sade-sati"`,
`depth: "standard"`, the frame fields. The `ranking` table ranks the areas by support (`item`, `support`, `why`,
`window`, `caution`). Required sentence in `scope`: "Sade sati is a broad lens, never a verdict: it counts only where
the running period agrees."

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `windows` | the three phases (Saturn 12th, 1st and 2nd from the Moon) with their months, each pause and resumption named (a retrograde step out of the zone is a pause, not an end, F04); phases as timeline `pressure` rows only where the dasha agrees (`fit`), else `chapter` rows | `get_outlook` (period `year`, kind `sade_sati`: begins, pauses, resumes, ends) year by year; `get_gochara` (`sade_sati`) for the state on a date |
| `areas` | what each phase presses on in life (the 12th, 1st and 2nd from the Moon, read with the houses Saturn rules from the lagna), Saturn's condition and bindus | `get_gochara` (`house_from_lagna`, `condition`, `bav`, `sav` for `Sa`); `get_ashtakavarga` |
| `fit` | does the running dasha involve Saturn, the Moon or their houses; whether this is a first or a later sade sati; "no event-level timing is indicated" where nothing agrees | MD/AD → `get_dasha` |
| `kantaka` | Kantaka Shani (Saturn 4th, 7th or 10th from the Moon) and Ashtama Shani (8th from the Moon) in the period, with begin, pause, resume and end months; every unit graded Weak; the section text carries the no-source sentence (below) | `get_outlook` (kind `kantaka_ashtama`, spans with `start_kind`, `end_kind`); `get_gochara` (`kantaka_ashtama`) |
| `response` | how to meet each phase: pace, structure, patience, what to postpone; remedies only on request and by the shared rule (Parashari, no gems or costly rituals, a no-efficacy line) | from the sections above |

The `kantaka` section text must contain: "Kantaka Shani (Saturn in the 4th, 7th or 10th from the Moon) and Ashtama Shani
(Saturn in the 8th from the Moon) have no rule text in this library: CRUX p424 and p464 call Saturn in the 8th from the
Moon 'Kantaka Sani' in case studies only, and the 4th, 7th and 10th convention has no book source here. Both are a modern
convention, always graded Weak." (owner decision 4, 2026-11-20; sentence corrected 2026-11-20, T11.38). Every unit that names Kantaka or Ashtama is
graded Weak on every line. `spec_checks` enforces both.

Situation check: ask in `next_step` what feels heavy now and since when. Sensitivity: `get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| Sade sati: Saturn in the 12th, 1st or 2nd from the natal Moon; a broad lens that needs dasha confluence; milder the second time | LOL p363-364; HPA p130 |
| Classical gochara is from the natal Moon; Saturn's favourable houses are 3, 6, 11 | PD XXVI.1-2 (p312) |
| Own or exalted sign does no harm even in a bad house | PD XXVI.30-32 |
| Many bindus make even a 12th or 1st transit good | PD XXVI.41 |
| Saturn's houses suffer unless in own or exaltation, scaled by natal strength | LOL p364-365 |
| A transit never produces a major event without natal promise and dasha activation | HJH2 p119-122; HPA p134 |
| Kantaka Shani (4th, 7th, 10th) and Ashtama Shani (8th) | not checked: no rule text in this library; a modern convention computed by the engine (owner decision 4). CRUX p424, p464 (Rath, case studies) use the name "Kantaka Sani" for Saturn in the 8th from the Moon, a different use of the name |

## 3. Conventions

Lahiri, whole-sign houses, mean nodes, sidereal dasha years. Phases and pauses follow the engine's sign changes (F04
logic: a return into the zone within a year is a resumption). Kantaka and Ashtama use the same begin, pause, resume and
end logic. Write the sign Cancer as "the Cancer sign": the shared medical word list (`medical_words.py`) refuses the bare
word, an accepted over-block.

## 4. Caveats

- No illness, accident, death or fear framing, for the person or anyone else: sade sati and Ashtama read as pace,
  load and responsibility, never as danger or loss of life.
- No "bad years" label; a phase is pressure on named areas, with its counter-factor.
- Kantaka and Ashtama: modern convention, graded Weak, never the main finding.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | `areas` units from the lagna carry `sensitivity`; months only |
| unknown time | drop `windows`, `areas`, `fit` and `kantaka` (all counted from the Moon or the lagna; the word guard refuses "from the Moon" when the time is unknown) and the ranking; at most labelled monthly markers of Saturn to time-independent natal planets; `response` stays in general terms |
| any time | a phase with no dasha agreement is a `chapter` row only |
