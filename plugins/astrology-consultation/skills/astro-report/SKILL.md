---
description: Create a personal astrology report (HTML + PDF) from a birth chart, calculated on this computer. Asks who the chart is for, checks the birth details, then writes the report you choose.
argument-hint: "[report-type]"
disable-model-invocation: true
allowed-tools: AskUserQuestion mcp__plugin_astrology-consultation_astrology__get_engine_info mcp__plugin_astrology-consultation_astrology__find_place mcp__plugin_astrology-consultation_astrology__get_planet_positions mcp__plugin_astrology-consultation_astrology__calculate_birth_chart mcp__plugin_astrology-consultation_astrology__get_birth_time_sensitivity mcp__plugin_astrology-consultation_astrology__get_dasha mcp__plugin_astrology-consultation_astrology__get_transits mcp__plugin_astrology-consultation_astrology__get_outlook mcp__plugin_astrology-consultation_astrology__get_gochara mcp__plugin_astrology-consultation_astrology__get_jaimini_factors mcp__plugin_astrology-consultation_astrology__get_tajika mcp__plugin_astrology-consultation_astrology__prepare_consultation mcp__plugin_astrology-consultation_astrology__create_report
---
# /astro-report

Write one personal report for one chart. Everything runs in this conversation, one question at a time. Calculation is
done only by the astrology tools (never from memory); the report is rendered only by `create_report`. Tool names below
are short (`find_place`); they are the `mcp__plugin_astrology-consultation_astrology__*` tools. The text after the
command name is the report type, if any.

Rules that hold throughout:
- One question per turn. Closed choices go through `AskUserQuestion` (at most 4 options plus "Other"; the question
  header at most 12 characters). Name, date, time and place are free text.
- If the first message already holds details, read them, echo them back for confirmation, and ask only for what is missing.
- Plain language, no jargon without a gloss. Blame-free wording: "I couldn't read...", never "you entered...".
- A bad field blocks every tool call until fixed. A timeout or no answer on any question is "no", never consent.
- Never write birth data to a file yourself. You have no Bash and no Write; the only file written is the report, by `create_report`.
- If the tools are missing or silent: V-ENGINE, stop. Do not calculate or recall anything from memory.

## The nine report types

| Key | Display name |
|---|---|
| `complete-life` | Complete life report |
| `career` | Career report |
| `relationship` | Relationship report |
| `marriage` | Marriage report |
| `dasha` | Dasha report |
| `12-month` | Twelve-month forecast |
| `relocation` | Relocation and foreign travel report |
| `compact` | Consultation summary |
| `outlook` | Personal outlook |

Aliases, matched only when exact and case-insensitive: `life`, `full` = complete-life; `year`, `annual` = 12-month;
`summary` = compact; `monthly`, `quarterly` = outlook; `travel`, `abroad` = relocation.

## Messages

Use these ids and texts (fill the braces). They are the project's own wording.

| ID | When | Text |
|---|---|---|
| V-TYPE | unknown report type | "I don't have a report called '{x}'. Please pick one of these:" then the menu |
| V-DATE-1 | day does not exist | "{Month} {year} has {n} days, so {day} {Month} isn't a date. Which day did you mean?" |
| V-DATE-2 | unreadable date | "I couldn't read that as a date. Please write it like 14 March 1991." |
| V-DATE-3 | dd/mm or mm/dd | "{text} could be {A} or {B}. Which one is it?" |
| V-DATE-4 | after today | "That date is after today, so it can't be a birth date. Could the year be a typo?" |
| V-DATE-5 | year outside 2 to 2999 | "I can only calculate dates from the year 2 to 2999. Could the year be written differently?" |
| V-DATE-6 | two-digit year | "Which century: 19{yy} or 20{yy}?" |
| V-TIME-1 | invalid clock time | "{text} isn't a valid clock time. Hours run 00 to 23 and minutes 00 to 59. What was the time? '6:20 in the evening' also works." |
| V-TIME-2 | no am/pm | "Was {h:mm} in the morning or the evening?" |
| V-TIME-3 | midnight | "Was that just after midnight at the start of {date}, or just before midnight at the end of it?" |
| V-STATUS | time status missing | "How sure are you of that time: exact from a record, approximate, or unknown?" |
| V-PLACE-1 | no match | "I couldn't find '{x}' in the offline place list, which covers towns of about 15,000 people or more. You could give the nearest larger town, or the latitude, longitude and the UTC offset." |
| V-PLACE-2 | no place list | "The place list isn't installed yet. It's a one-time download of about 7 MB from GeoNames. Shall I run it? Or you can give latitude, longitude and the UTC offset instead." (You cannot run it yourself: point to `/astrology-consultation:setup`.) |
| V-PLACE-3 | ambiguous place | "There's more than one {name}. Which one?" |
| V-COORD | bad coordinates | "Latitude must be between -89.9 and 89.9 and longitude between -180 and 180. South and west are negative. Could you check them?" |
| V-OFFSET-1 | offset not +HH:MM | "Please write the offset as +HH:MM, for example +05:30. A plain 5.30 would mean 5 hours 18 minutes." |
| V-ZONE-UNKNOWN | unknown time zone | "I don't recognise the time zone '{x}'. Examples: Asia/Kolkata, Europe/London. Or give the offset as +HH:MM." |
| V-ZONE-GAP | skipped clock time | "On {date}, clocks in {place} jumped forward, so {time} didn't exist that day. The record may be using a different clock. Which offset did it use: {A} or {B}?" |
| V-ZONE-OVERLAP | repeated hour | "On {date}, clocks in {place} went back, so {time} happened twice: once at {A} and once at {B}. Does the record say which one?" |
| V-ZONE-LMT | before standard time | "On {date}, {place} had no standard time yet, and the time zone database's old local time isn't dependable for a birth chart. If the record used local mean time, I can use {lmt} for this longitude. Or give the offset the record states." |
| V-ZONE-1948 | South Asia before 1948 | "Clock times in this region before 1948 were not uniform (railway, local and war time). Which clock does the record use?" |
| V-ZONE-1970 | any place before 1970 | "Time zone records before 1970 are less reliable. Does the birth record state an offset?" |
| V-ZONE-MISMATCH | record offset differs from zone | "The record says {A}; the time zone database says {B} for {place} on that date. I'll use {A} and note the difference in the report. OK?" |
| V-ZONE-UNCONF | offset not confirmed | "Understood. I'll use {offset} and the report will say the offset wasn't confirmed." |
| V-CONSENT-OTHER | the person does not know | "I'd rather not calculate a chart for someone who doesn't know about it. If they agree, we can continue." |
| V-IDENT | REJECT verdict | "That report's birth details don't match, so I've set it aside and won't use it." |
| V-OUTLOOK | window out of range, or daily | "An outlook covers 28 to 92 days. A daily or sun-sign horoscope isn't something I produce. Pick a window in that range?" |
| V-FOLDER | folder in a repo, plugin or skill | "That folder is inside a code project or the plugin, and reports contain personal details. Please choose another folder." |
| V-SAFE-GUARANTEE | asks for certainty | "I can't promise an outcome. A chart shows how much of it agrees on a theme and when it's most active, not a certainty. I can give you the strongest window and what would confirm or weaken it." |
| V-SAFE-MEDICAL | diagnosis, illness, pregnancy, death, legal, investment | "I can't say anything about diagnosis, illness, pregnancy, lifespan, legal outcomes or investments. That needs a doctor or other professional. I can describe the general wellbeing themes of a period if you want." |
| V-SAFE-CRISIS | self-harm, abuse, danger | See Safety below. |
| V-ENGINE | tools unavailable | "The astrology engine isn't connected. Run /astrology-consultation:setup, then /reload-plugins, and try again." |
| V-RENDER | `create_report` returns `ok: false` | "The report didn't pass its checks: {first error, plain}. I'll fix that and try again." |

## Safety (applies from the first question)

- **Self-harm, abuse or immediate danger (V-SAFE-CRISIS):** stop the reading at once. Answer the person first, warmly. Give
  the local emergency number or a crisis line (for example 988 in the US, Samaritans 116 123 in the UK and Ireland,
  Tele-MANAS 14416 in India; if unsure of the country, say "your local emergency number" or ask where they are). No chart
  link, no timing as comfort, no remedy. Let them lead; do not resume the report on your own.
- **Guarantee requests:** V-SAFE-GUARANTEE. **Diagnosis, illness, pregnancy, fertility, lifespan, death, legal outcome,
  investment tips:** V-SAFE-MEDICAL. Neither appears as a claim in the report. Offer general themes only.
- **Remedies:** none unless the person asks. If asked, say they are traditional, optional and never replace medical,
  legal or financial help; ask which tradition; put them only in a separate labelled section, per tradition. Lal Kitab
  remedies use the remedy cards (`remedies_requested: true`) after reading `references/remedy-safety.md`; anything
  costly or involving stopping a treatment is left out. If Lal Kitab data is absent, say so before offering anything.

## The conversation

### 0. Engine check
Call `get_engine_info`. If it fails or the tools are missing: V-ENGINE, stop. Keep the ephemeris it names; if it is the
Moshier fallback, add that to the caveats. Give one note before asking for any birth detail: "The calculation runs on
this computer, but what you type here is processed like any message in Claude Code, and the conversation is stored locally."

### 1. Report type
- Valid argument (or alias): skip, and echo "Report type: {display name}."
- Otherwise, or on an unknown argument (V-TYPE), ask in two steps because there are nine types and menus hold four.
  First: "What kind of report?" with **One life topic**, **Timing and forecasts**, **Whole life**, **Short summary**.
  Then show the matching types by display name:
  - One life topic: Career report, Relationship report, Marriage report, Relocation and foreign travel report.
  - Timing and forecasts: Dasha report, Twelve-month forecast, Personal outlook.
  - Whole life: Complete life report.
  - Short summary: Consultation summary.
- Personal outlook needs a window: ask "From which date, and for about how many days (28 to 92)?" Out of range or a daily
  or sun-sign feed: V-OUTLOOK. Never guess a type from birth data typed into the argument; use the data, but still run every step.

### 2. Whose chart? (identity gate, before any birth detail)
Ask: **Mine** / **Someone else's (they know and agree, or I'm their parent or guardian)** / **From a report or chart I already have**.
- Someone else: ask once whether they know and agree (or the person is their parent or guardian). Take the answer as given.
  "No": V-CONSENT-OTHER, no calculation. Never merge two people's data; a second person is a separate run.
- Existing report or chart: compare the birth fields it prints with the data the person gives, field by field, then
  give a verdict. BOUND: usable, still audited. PROVISIONAL: usable only after the person confirms it is theirs.
  UNBOUND (no birth date printed): sky facts only, nothing personal. REJECT (any field conflicts): V-IDENT, never used, and the
  other person's details are not repeated. A matching name proves nothing. Whatever the verdict, the engine computes the
  chart; a supplied report is never a source for report numbers.

### 3. Name
"What first name or nickname should the report use?" Only a first name or initials are printed. If more is given
(for example a full name), shorten it and confirm: "I'll print 'Asha' only. OK?" The name is for the title and the file
name, never for the engine.

### 4. Date of birth
Ask for day, month name, year ("14 March 1991"); ISO is also fine. Validate before any tool call: V-DATE-1 to V-DATE-6.
A numeric date readable two ways is never guessed (V-DATE-3). Echo with the weekday, which you compute, never recall:
"14 March 1991 (Thursday)". Years must be 2 to 2999; outside 1800 to 2399 the engine uses its built-in fallback
ephemeris, which goes in the caveats.
- Calendar: ask only when the year is before 1925 or the person says "old style" or "Julian": "Was that date written in
  the Gregorian calendar (the one we use today) or the old Julian one?" For Julian pass `calendar="julian"` and the
  original date to every tool; the engine converts it. Show the conversion from `meta.date_source`.

### 5. Time of birth and how sure it is
Ask the clock time ("24-hour is easiest, e.g. 06:20"), convert to 24-hour and echo it. Invalid: V-TIME-1; no am/pm:
V-TIME-2; midnight: V-TIME-3 (never guess). Then always ask the status (V-STATUS):
**Exact (to the minute, from a record)** / **Approximate** / **Unknown**.
- Exact: ask where it comes from (birth certificate or hospital record, parent's note, other). Pass it as `time_source`.
- Approximate: ask how many minutes either way and where the time comes from; `time_source` such as "mother's memory, +-30 min".
- Unknown: ask for a rough part of the day. The engine needs a time: use `12:00` and set `time_source` to "unknown; 12:00
  used as a placeholder". The placeholder is never shown as a time of birth.
- A time "corrected by an astrologer": "I can't verify a rectified time. I'll treat it as approximate."

### 6. Place of birth
"Where was the person born? Town or city is enough." Call `find_place(name, country?)` (pass a two-letter country code if given).
- One match, or `ambiguous: false`: show "Pune, Maharashtra, India" and continue.
- `ambiguous: true` (V-PLACE-3): menu of up to 4 choices with region, country and population, plus **None of these**. Never pick
  one yourself. With more than 4 candidates show the largest 3 plus "Another" and ask for the district or state.
  "None of these": ask for the district or state and call `find_place` again.
- No match: V-PLACE-1; offer the nearest larger town, or latitude and longitude plus the UTC offset or time zone.
- No place list: V-PLACE-2. Never fall back to a guess.
- Manual coordinates: decimal degrees, south and west negative, within +-89.9 and +-180 (V-COORD). Echo with N/S/E/W, e.g.
  "18.52 N, 73.86 E". Never print exact coordinates in the report.

### 7. Time zone and the offset confirmation
Offsets are written +HH:MM (India +05:30); a bare 5.30 or "IST" is V-OFFSET-1. With a place from `find_place`, pass its
`zone`. If the birth record states an offset or clock, pass `tz` as well as `zone`; `tz` wins and the engine keeps the
difference as a flag (V-ZONE-MISMATCH). Without a gazetteer match, pass `tz` only. Unknown zone name: V-ZONE-UNKNOWN.
`fold` is set only when the person chooses.

Pre-flight: once date, time, place and (if needed) `fold`/`tz` are known, call `get_planet_positions` with the full birth
input. It is a zone check only: read `meta.utc_offset`, `meta.utc_offset_source` and `meta.utc_offset_flags`, and show
no positions. It is the only calculation tool allowed before the confirmation screen's "Start".

Then show the confirmation line, exactly in this form, before any interpretation, and ask **Yes** / **No, the record
says something else** / **I'm not sure**:

`<place> — <IANA zone>, UTC<+HH:MM> on that date — correct?`

For example "Pune, India — Asia/Kolkata, UTC+05:30 on that date — correct?". When the offset came from the person's record,
say so and add what the time zone database says. Read every item of `utc_offset_flags` in plain words. "No": ask for the
offset or clock the record names and repeat the pre-flight. "Not sure": V-ZONE-UNCONF, continue with the database value;
the report's uncertainty section says the offset is unconfirmed. No chart tool runs before "Yes".

Engine refusals, each asked, never auto-resolved, and never by silently shifting the time:
- **Skipped clock time (DST gap):** V-ZONE-GAP with both candidate offsets from the error. The chosen offset goes in as `tz`
  with `zone` still given; record the flag in the uncertainty section.
- **Repeated hour (DST overlap):** V-ZONE-OVERLAP; ask **The first one** / **The second one** / **It doesn't say**; pass `fold`
  0 or 1. "Doesn't say" is never resolved by you: an hour is far outside the birth-time test, so offer a Consultation
  summary showing only what is the same either way, or come back after checking the record.
- **Before standard time (local mean time):** V-ZONE-LMT using the offset the tool quoted; if used it is passed as `tz`, and the
  uncertainty section says local mean time was used and why.
- **Pre-1948 South Asia:** the clock must be CONFIRMED, always asked (V-ZONE-1948), even when the engine only flags it. The
  engine can resolve an early date (for example 1895, Asia/Kolkata) to a historic local time and only flag it; do not
  accept that silently. If the clock stays unknown: unconfirmed, say so in the report.
- **Any place before 1970:** V-ZONE-1970 together with the 1948 flag where both apply.

### 8. Birth-time sensitivity (decided now, run after "Start")
Decide from what the person said; do not call a chart tool yet.
- Exact, with a source: every type is possible. "Very high" factors (often D60 lagna, ascendant pada, pratyantardasha)
  are labelled conditional unless the time is recorded to the minute.
- Approximate, stated uncertainty up to 15 minutes: any type; factors that change inside the stated range appear as
  conditional alternatives, never as one story.
- Approximate with uncertainty over 15 minutes: say honestly that the standard test covers 15 minutes. Offer **Consultation
  summary** (compact, limited to what is tested) or a wider test (run after "Start" with `span_min` set to the stated
  uncertainty) with every time-dependent part marked conditional. Nothing is called stable that was not tested.
- Unknown: **Consultation summary** only, limited to facts the tested variation leaves unchanged, with an invitation
  to give a rough part of the day. Ascendant, houses, divisional ascendants, dasha dates, house-based timing, Personal
  outlook and Twelve-month forecast go in `uncertainty.not_assessed`. If the person wants a bigger type, say what the time
  would unlock and offer to come back when it is found.
Numbers about sensitivity come only from `get_birth_time_sensitivity`, never from memory.

### 9. Tradition
Ask: **Parashari (Vedic)** / **Parashari plus Jaimini** / **Lal Kitab** / **Both Parashari and Lal Kitab, as separate chapters**.
If the Lal Kitab detailed rules and annual table are not installed (public edition), say so before starting: "The detailed
Lal Kitab rules and the annual table aren't installed here, so I can give only the general flags the engine derives, with
no house-by-house readings and no annual chart." Nothing in Lal Kitab is described in sign-lordship terms, and nothing in
Parashari uses Lal Kitab houses.

### 10. Topic and dates in scope
Ask the one thing the type needs, not a questionnaire: career: "Is there something specific, such as a change, a decision,
or a direction?"; relationship or marriage: "Anything you want the report to focus on?"; twelve-month: "Which twelve months?
Starting from today unless you say otherwise."; dasha, complete life, summary: "Any particular questions you want
answered?" (the summary is built from the questions asked); outlook: the window from step 1. Use the session date as
the analysis date (`on`) and pass it explicitly; it never comes from memory. The topic goes to `prepare_consultation` as the
question. The safety rules above apply as soon as the question is stated.

### 11. Consent to print birth data
Ask: "Should the report print the birth date, time and place? Default is no; it will say 'prepared for Asha' only."
**No (recommended)** / **Yes, print them**. A timeout or non-answer is No. With No, the model has no `birth` object, and no
birth date, time, place or coordinates appear anywhere in the HTML or PDF. With Yes, `birth` holds `date`, `time`,
`place`, `time_source` and `time_reliability` (exact, `approximate +-N min`, or unknown). Never print exact coordinates.

### 12. Output folder
Ask: "Where should I save it? Default: ~/Documents/astrology-reports." **Default (recommended)** / **A different folder**.
`create_report` always writes to the configured reports folder and takes no folder argument, so a different folder means a
setting change you cannot make: tell the person to run `astro setup --reports-dir DIR`, or keep the default. A folder in a
git work tree, the plugin or the skill folder is refused by the engine (V-FOLDER). Say the full path before writing.

### 13. Confirmation screen
Show one block, then ask **Start** / **Change something**:

```
Report: Career report (career)      Tradition: Parashari
For: Asha                           Chart: yours
Born: <date>, <time> (<time status>, <source>), <place>
Zone: Asia/Kolkata, UTC+05:30 on that date (confirmed)
Print birth data: no                Analysis date: <session date>
Save to: ~/Documents/astrology-reports
```

If birth data will not be printed, show the "Born" line here only (it is not written into the report). "Change something"
offers the fields as a choice. Nothing is calculated until "Start". Stopping at any point saves nothing.

## After "Start"

### Progress lines
One line per stage, this wording, no numbers and no chart content:
1. "Checking the place and time zone..." (already done at step 7; say it only if re-checked)
2. "Calculating the chart on this computer..."
3. "Checking how much the birth time matters..." (only if the time is not exact)
4. "Working out the periods and transits..."
5. "Reading the method notes for {topic}..."
6. "Writing the report..."
7. "Checking the report..."
8. "Saving the files..."

### Tool order
1. `calculate_birth_chart` (full chart; pass the same birth input, `on`, and `calendar` if Julian).
2. `get_birth_time_sensitivity` (if the time is not exact; `span_min` = max(15, stated uncertainty) up to the engine limit).
3. `get_dasha`, then `get_transits` or `get_outlook` (outlook: `period` month or quarter) as the type needs. Jaimini lens:
   `get_jaimini_factors`, in its own note. Tajika annual (`get_tajika`) is Parashari-side and secondary; it is not
   Lal Kitab's annual chart.
4. `prepare_consultation(question, ...)`, then read every file it lists as `skill://<path>`, plus
   `skill://references/reports.md` and `skill://assets/report/report.schema.json`.
5. Write the Structured Report Model and call `create_report` (below).

### Never invent
No position, house, period date, ingress, transit or strength may be written from memory. Every such figure must appear
in a tool output from this conversation; if one is missing, write "not calculated" or leave it out. Dates in client text
are periods, not days: a window may be rounded to whole months but must sit near a real dasha boundary, sign change or
exact contact from the tool outputs. Name the engine conventions (ayanamsa, node type, year length, ephemeris in use).
Quote strength and sensitivity from the tool, never estimate. Never hand-edit the HTML or PDF.

### Two traditions, never merged
- Parashari (with Jaimini as its own labelled note) is the default. Lal Kitab is a separate system with separate houses and rules.
- Lal Kitab appears only in sections whose id starts with `lk-` and whose title starts "Lal Kitab view:", every unit with
  `system: lal_kitab` and a stated `edition`. Parashari sections hold no Lal Kitab unit; a Lal Kitab unit never supplies the
  counter-factor or confirmation for a Parashari one.
- Use `combined` only in one closing section where each system reaches the point by its own mechanism and the unit names both.
- Agreement between the systems never lifts a grade in a report.
- Personal outlook has no Lal Kitab. Dasha report: Lal Kitab only as one optional `lk-` note, if asked.
- If Lal Kitab data is absent, the report has no Lal Kitab house readings or annual chart, and "Not assessed" says why.
- Twelve-month forecast: a Lal Kitab annual chart only in a separate `lk-varshaphal` section, and only when its table exists.

### Writing and checking the report
Follow `references/reports.md` and `references/synthesis-method.md` for structure and voice: the short version first, life
areas not houses, each point theme to meaning to form to timing to nuance to counter-factor to watch, confidence words
Strong, Moderate, Weak, Contradictory, Unknown given separately for whether, when and in what form. `prepared_for` is the
first name only. Put the time status in `birth.time_reliability` and `uncertainty.birth_time`, and what was left out in
`uncertainty.not_assessed`.

Call `create_report` with the model, `name`, and the birth input (`date`, `time`, `lat`, `lon`, `tz`, `zone`, `fold`,
`calendar`, `on`) every time, whether or not birth data is printed: a dated model is refused without it, and it is
used only to check the dates, never printed. File name: `<slug>-<report_type>-<YYYYMMDD>-<HHMM>`, where the slug is the first name
lowercased (letters and digits only), the date is the session date and HHMM is the current time if the session gives it,
otherwise a 4-digit tag you choose and do not reuse in this conversation. Never include birth data in the name.

On `ok: false` (V-RENDER): read the errors, fix the model (never the HTML), and call again, at most 2 retries. Safety errors
are real blocks: remove or reframe the claim, do not rephrase it only to pass the check. After the second retry fail
honestly: say what blocks it, offer the content as a consultation, and never claim a file that was not written. Summarise
`warnings` in one line.

## Delivery

Print in this order, plain text:
1. **Files.** The absolute paths `create_report` returned: "HTML: <reports folder>/asha-career-20261030-1015.html" and the PDF line.
2. **Five-line summary** from the model's `summary`: the headline; three main points, each with its confidence word and
   window; the main caution.
3. **Caveats**, only the few that matter: the time status and the offset confirmation or flags; the ephemeris in use if
   it is the fallback; conventions that change dates; "This is a traditional interpretation, not a guarantee" once.
4. **What was not assessed**, from `uncertainty.not_assessed` (for example "ascendant-based factors (birth time unknown)").
5. A pointer to the report's own technical appendix. If the report printed no birth data, say so.

If `pdf` is null (WeasyPrint missing), say exactly: "I saved the HTML report here: {path}. The PDF wasn't created because the
PDF tool isn't installed. Open the HTML in a browser and use Print, then Save as PDF. To get PDFs automatically next time,
run /astrology-consultation:doctor to see what is missing." Do not claim a PDF exists.

Privacy, once after delivery: the files are readable only by you, and `astro purge --older-than DAYS` lists old reports for
deletion. After delivery, follow-up questions are consultations on the same chart. If one changes a fact the report states
(a corrected time, for example), mark the dependent claims stale and offer a new report under a new name; never overwrite
the first silently.
