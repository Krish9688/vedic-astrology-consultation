# Consultation report (complete client report)

Use this when someone asks for a full consultation report that covers the kundli, Lal Kitab, life areas and answers
to their own questions. The other report types (`/astro-report`, reports.md) remain for focused reports.

## The division of labour
- **The engine prints every number.** Positions, houses, nakshatras, dignity, D9/D10/D7/D4, Vimshottari periods,
  yogas and dosha checks, Shadbala, Ashtakavarga, transits, the Lal Kitab chart and states, the varshaphal and the
  verification record are filled in from the chart. The engine recomputes the chart from the intake whenever the report
  is written.
- **You write only the interpretation model** (`assets/report/consultation-model.schema.json`). Every statement names
  the ids it rests on, taken from the writer's brief:
  - Fact ids: `F.*` (Parashari facts), `LK.*`, `SB.*`, `AV.*`, `GO.*`, `JA.*`, `DOSHA.*`.
  - Event ids: `DSH.*`, `ING.*`, `CON.*`.

  The engine refuses unknown ids, and it refuses any window that does not contain the events it cites (±45 days).

## Steps
1. **Intake** (the fields below):
   - **client:** full name, gender, current city and country, language (English), and relationship, occupation and
     education if given.
   - **birth:** date, time, `time_reliability` (exact, approximate with `time_uncertainty_min`, or unknown with no
     time), place, coordinates, and `tz` (`+05:30` for India) or an IANA `zone` (plus `fold` for a repeated hour).
     Never use LMT.
   - **consultation:** type (one-time, annual or follow-up), report date, focus, window, chart style.
   - **questions:** each with an id `Q1..`, the client's own words, a category and a priority.
   - **consent:** `store_and_process` is required; `print_birth_data`, `print_full_name` and `remedies_requested`
     are optional.

   Leave out anything not given; it prints as "Not provided". Bracketed placeholders are refused.
2. Call `prepare_consultation_report(intake)` (CLI: `astro consultation-report intake.json`). Field-named errors come
   back as a list; ask the person about each one instead of guessing.
3. Read the brief. Write the model:
   - The summary.
   - The kundli readings: lagna, Moon, Sun, current period, yogas, strengths, transits.
   - The Lal Kitab readings (LK ids only): overview, debts, varshaphal.
   - **Eight chapters:** love, career, wealth, foreign, education, family, health, spirituality. Each has indicators,
     the current period, windows (or `no_window_reason`) and cautions.
   - **One answer per question:** the answer, evidence, windows, confidence, what to do, and `answerable: false` with
     `limits` when the chart cannot answer.
   - The timeline: `months_12` and `years`.
   - Remedies, only if requested.
4. Call `create_consultation_report(intake, model)`. On errors, fix the model (at most two retries), never the output.

## Rules the engine enforces
- **Lahiri ayanamsa only.** Lal Kitab statements use LK ids only and appear only in section 4 and the remedies; the
  two systems are never merged.
- **Unknown time:**
  - No event ids, no windows and no timeline.
  - No id that changes during the birth date; houses are counted from the Moon.
  - The lagna and the current-period readings may be left out.
- **Approximate time:**
  - A statement that cites an id which varies within the stated uncertainty must set `time_sensitive: true`.
  - So must a statement or window that cites a dasha event when the period dates move by more than 45 days.
  - The report prints each of these with "depends on the exact birth time".
- **Safety:** the life-first lint runs on every string.
  - Children are never timed, so the family chapter and children questions use `no_window_reason`.
  - Health is wellness only and never a diagnosis.
  - Kuja and other dosha labels are conventions, never verdicts.
  - Remedies follow remedy-safety.md: Lal Kitab cards carry a safety class and the safe form, with the source
    locator.
  - The engine works out the CR-L01 edition dispute for every Lal Kitab card itself (`lk_remedy_dispute`) and prints
    it on the card and in appendix E, in either direction:
    - Shrimali: pakka ghar, and the Sun, Moon or Jupiter in house 6, are not changed by remedies.
    - 1952: placements that are neither dignified nor pakka are fixed, and so is every planet in house 6 except the
      Sun, Moon and Jupiter.
  - Every card says "no efficacy established".
  - Windows carry a `kind` (favourable, pressure or watch), and it is printed. A caution is never listed as a
    favourable window.
  - A sentence that cites a yoga or dosha which does not hold must say so; otherwise the engine warns.
- **Approximate-time display:** the dignity reads "varies with the sign" when the sign varies.
  - The Moon's degree is printed as a range, and other degrees to the arcminute.
  - The birth-chart captions name the other possible ascendant sign, and the transit table shows every possible
    house from the lagna.
  - Shadbala, Ashtakavarga and cusp tables are captioned as depending on the birth time.
  - The Lal Kitab annual houses count as time-varying when the natal LK houses vary.
- **Before rendering:** placeholders, "undefined" and similar strings are refused. After rendering, every page of the
  PDF is checked for text, page numbers and broken output.

## Personas used as permanent regression cases
- **P2:** female, exact time.
- **P3:** midnight birth.
- **P4:** Toronto, DST fall-back night, `fold: 0`.
- **P5:** unknown time.
- **P6:** approximate time, ±45 minutes.

These cases are kept with the test suite in the development repository.
