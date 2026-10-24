# Final check before sending

Contents: [Reasoning](#reasoning) · [Systems and sources](#systems-and-sources) · [Data and privacy](#data-and-privacy) · [Communication and safety](#communication-and-safety) · [Regression scenarios (for testing changes to the skill)](#regression-scenarios-for-testing-changes-to-the-skill) · [Life-first and report checks (v3.4)](#life-first-and-report-checks-v34)

Apply to the answer itself, proportionately (a short answer needs a quick pass). If a check fails, fix the reasoning,
not just the wording. Adding a disclaimer never repairs an unsupported claim.

## Reasoning

- [ ] The answer addresses the actual question and horizon; it is not a chart recital.
- [ ] Every main conclusion rests on at least two distinct channels (synthesis-method §4.1), or is graded Weak.
- [ ] House, lord and karaka were all considered; the same network was checked from the Moon where relevant.
- [ ] Functional lordship, dignity, dispositor, combustion and retrogression used correctly (verified by `chart_facts.py`).
      Sandhi is NOT checked by any script: for a planet within about 1° of a sign edge, or in a different Sripati
      bhava (the engine's `bhavas`), say so and judge it by hand.
- [ ] Every placement, conjunction and aspect restated in the reply matches the `chart_facts.py` output (no "together
      with" for planets in different houses; no aspect the script does not list).
- [ ] Yogas verified by definition and constituents; no double counting of a yoga and its parts; bhanga checked.
- [ ] The strongest contrary factor is stated, and delay vs denial is distinguished where relevant.
- [ ] Varga used only for its topic and only if time-stable; D1–varga conflict visible.
- [ ] Timing: significators → dasha/bhukti intensity → transit trigger → window with reasons; no
      transit-only event; no exact days.
- [ ] Grades use Strong/Moderate/Weak/Contradictory/Unknown; caps in synthesis-method §4.3 respected; no percentages.
- [ ] A realistic alternative manifestation is given for any event claim.
- [ ] Topic networks complete: e.g. an existing-relationship question examines the 5th house and lord as well as the
      7th/Venus network (topic-relationships §2); a money question separates 11th (income) from 2nd (retention).

## Systems and sources

- [ ] Nothing that rests on a book (claim_basis TEXT or COMMENTARY) is called tested, proven or validated: a source's
      statement is not evidence that the event happens (`render_report.py` rejects it in reports). TESTED needs a
      prediction-log result.
- [ ] No "scientifically proven", no accuracy or success percentage for astrology (own or anyone's), and no study figure
      beyond [evidence-card.md](evidence-card.md) rows with `accessed: true`; Vedic timing and Lal Kitab are "no controlled
      test located", never "refuted" or "validated" (`life_lint.py --mode audit` flags the wording).

- [ ] Disputed rules from the contradiction register named when they decide the answer.
- [ ] Citations (when given) are real pages retrieved from the index; source statement / inference / synthesis /
      external knowledge distinguishable; no invented verse.

## Data and privacy

- [ ] No positions, transits or dates from memory; calculated data labelled with tool, ayanamsa and time.
- [ ] Consent obtained before sending birth data to an external service; no default profile used for another person.
- [ ] Assumptions (house system, age convention, birth-time reliability) are stated where they matter.

## Communication and safety

- [ ] Answer-first, natural prose; technical terms translated; no placement dumps; caveats not repeated.
- [ ] Confident only where the grade is Strong; clearly tentative where Weak/Unknown.
- [ ] No death/longevity, diagnosis, fertility, infidelity, legal verdict or investment claims; classical deterministic
      statements not presented as forecasts.
- [ ] Remedies only if asked, through remedy-safety.md; nothing its §1 rules out; safe substitutes labelled as substitutes.
- [ ] No claim of human experience, intuition or guaranteed outcomes.

## Regression scenarios (for testing changes to the skill)

The behavioural test set lives in `tests/test-cases.md`. After any change to reasoning or voice files, rerun at least
the regression subset and compare with your earlier outputs, if you keep them. Also keep the v2.2 regression ideas:
removing natal support must weaken a transit-only claim; duplicating one placement as yoga/dignity/vargottama must not
raise confidence; changing the ascendant must change functional ownership; unstable birth time must stop a high varga
from confirming; reversed period dates must be caught; a diagnosis/death/guarantee request must be declined.
- [ ] Every rule cited by book/page was confirmed with `kg.py sources` or `search.py --page`; its tier (classical / traditional / modern / synthesis) matches how it is presented; external (not-in-library) knowledge is labelled.
- [ ] Jaimini material, if used, sits in its own labelled note and is not counted as extra Parashari evidence.
- [ ] **Consultation shape**: the first one or two sentences answer the question asked; the likeliest form and (if
  relevant) the window follow; the main counter-weight is named by what it controls; at most about four chart facts in
  the main text; no "because X is in Y" chains or one-paragraph-per-planet structure.
- [ ] **Roles**: no negative factor was turned into "delay" (or positive into "yes") without a second, independent
  factor supporting that role (consultation-reasoning §2).
- [ ] **Promise vs activation** stated separately for any timing claim; window granularity earned (timing.md §0);
  meeting/relationship windows kept apart from commitment/marriage windows.
- [ ] **Scenarios**: for description, comparison and open questions, the chosen manifestation was compared with at
  least one alternative, and the answer says why it is stronger (or that the chart does not separate them).
- [ ] **Calibration**: inferred claims (e.g. "through friends", "who initiates", appearance) are graded lower than
  directly represented ones; common placements and near-always-true transits are not presented as strong evidence.
- [ ] **One early sign to watch** is given for timed or thematic predictions.
- [ ] **Windows**: every narrower window names the layer that produces it (sub-period, transit contact); none without a
  basis. The period chosen as *the* window has its lord linked to the question's own network.
- [ ] **Promise grade** reflects the whole triad: a weak karaka or unsupported house keeps promise at Moderate at most.
- [ ] **Precision of facts**: orbs described honestly (exact ≤ ~1°, close 1–3°); no transit projected beyond the data;
  superlatives only from complete comparisons; the compared items named.
- [ ] **Counter-evidence kept**: the strongest counter-factor from the workbench appears in the answer with what it
  controls — the shorter answer must not drop it.
- [ ] **Secondary-system notes** (Jaimini) appear only if they change or confirm something; otherwise one line.
- [ ] **Recount before claiming a repeat**: any "this repeats from the Moon / Sun / in D9" statement was checked by
  recounting the houses from that reference (a lord that is the reference itself does not "repeat").
- [ ] **No workbench language** in the reply: no "network frozen", "channels", "tiers", "par excellence tier",
  "promise class", "role" — say what they mean in plain words.
- [ ] **One sharp window at most** (plus one secondary if distinct); no list of sub-sub-periods.
- [ ] **Slow-planet stays** use the calculated sign-change list, including retrograde returns ("leaves Pisces in June
  2027, returns October 2027 – February 2028"), never "until X" from one snapshot.
- [ ] **Absence claims name what was checked** ("the 12th lord, the 4th and the D9 12th show no residence-abroad
  signature") rather than "the usual indicators are not there".
- [ ] **No source footer or technical block** unless the person asked for detail or sources; no page or verse numbers
  in an ordinary consultation reply; at most one book named in passing.


## Life-first and report checks (v3.4)

- [ ] **Mode** matches the request: ordinary question → consultation; "in detail / why" → deep consultation with the
  technical reasons last; "report / PDF / write it up" → report (communication.md §0).
- [ ] **Life first**: each point opens with what it means in the person's life; chart facts appear after the
  consequence, in the same sentence, or in the technical section. Run `scripts/life_lint.py` on a substantial draft
  and fix what it flags, or keep it knowingly.
- [ ] **Cover-the-chart test**: with the chart words covered, each paragraph still says something specific about this
  person.
- [ ] **Birth-time sensitivity is calculated** (how many minutes until the ascendant or a decisive varga changes) —
  quote the engine's sensitivity table; if the data has none, say the margin is approximate and how it was estimated.
- [ ] **Transit contact dates** (a slow planet crossing a natal point) come from the engine's contact list, and Jupiter/
  Saturn houses "occupied and aspected" from its `transit_sign_aspects` windows — not from average motion or hand counting.
- [ ] Report: `render_report.py` passed; the short version, sections, timeline and watch list agree on events,
  windows and grades; every unit has a counter-factor and, if timed, a sign to watch; page/verse references only in
  the appendix; nothing personal saved inside the skill folder.
- [ ] **No invented history**: "again", "as before", "your difficult year" only when the data (or the person) shows
  the earlier event; a contact's earlier pass is claimed only if the contact list shows it.
- [ ] **Relationship questions keep the levels apart** even in a short life-first answer: meeting / relationship /
  commitment / marriage windows are named separately when they differ (topic-relationships-marriage.md).
- [ ] **Secondary systems and authors earn their sentence**: a Jaimini note or an author's name appears only if it
  changes or confirms the conclusion.
- [ ] **No fertility or longevity forecast slipped in** — no window for having a child, no age of parenthood, no "fewer/limited children", no lifespan; `life_lint.py` passes without SAFETY lines. The lint is a narrow backstop (a phrase list); a clean run does not prove the text is safe — read it.
