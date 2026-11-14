# Relationship report spec (`relationship`)

How the person relates, what draws them, the partner as tendencies, and the main windows. Owner template T2 inside the
shared frame ([README.md](README.md)); the spouse profile (T3) belongs to the marriage report, so only its trimmed,
low-confidence form appears here. The existing `relationship` type is kept: this spec aligns it (reports.md §2).

**Order (standard):** `windows` → `relate` → `partner`

The answer comes first, in the summary headline: the main window and its grade. Inputs: `birth`. Model:
`report_type: "relationship"`, `depth: "standard"`, the frame fields.

## 1. Sections and computed fields

| Section | Content (owner template T2) | Computed fields → engine tool |
|---|---|---|
| `windows` | the window ladder: (1) the promise, no date; (2) forming, the main window and one fallback; (3) formalising, only as a later rung. Each rung with its basis and grade; caution dates go to `watch_list` | network → `get_topic_network` (topic `marriage`); per-AD activation → `get_activation`; MD/AD → `get_dasha`; Jupiter and Saturn on the 7th or its lord, slow contacts → `get_transits` |
| `relate` | partnership temperament (7th sign), love style, the friction pattern in one sentence with its fix, who leads on what (communication, money, social life, decisions) | 7th house sign, occupants, 7th lord, Venus, 5th house and lord, 7th from the Moon → `calculate_birth_chart`; aspects on the 7th → `prepare_consultation` (derived facts, chart_facts `aspected_by`); Venus and 7th lord in D9 → `get_divisional_chart` (9) |
| `partner` | what draws the person and to whom; the partner as tendencies (nature, background, how you meet), each tied to a factor; appearance and age, if kept, graded Weak | Darakaraka → `get_jaimini_factors`; 7th lord and D9 7th → `calculate_birth_chart`, `get_divisional_chart` (9) |

Ranking: `ranking` rows rank the windows or the meeting routes by support (`item`, `support`, `why`, `window`).
Situation check: life facts come only from the person; put the question in `next_step` (current status). Follow-ups:
the marriage report (spouse profile) or a couples match. Sensitivity of every unit and window:
`get_birth_time_sensitivity`.

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| The 7th house refers to marriage, the partner and marital happiness | HJH2 p8 |
| Judge the 7th and its lord from the Moon too | HJH2 p20 |
| Venus is the kalatra karaka (significator of the partner) | HJH2 p39, p46 |
| The partner is read from the navamsa | BPHS p104 |
| Darakaraka: the planet with the least longitude signifies the spouse | JSR p295 |
| Upapada for the marriage itself (marriage report, not here) | BPHS p317 |
| A running dasha of the 7th-house network gives the event; transits only confirm | CRUX p290; timing.md §0 (the skill's own ladder) |
| Romance read from the 5th | common modern practice, not a rule found in this library (label it as such) |
| Meeting and marrying are separate events with separate windows; one main window, then the ladder | the skill's own rule (topic-relationships-marriage.md §1) |
| Affairs: own tendencies only | the skill's own rule (owner) |

## 3. Conventions

As the kundli spec: Lahiri, whole-sign houses, mean nodes, sidereal dasha years. The female-chart convention that
Jupiter signifies the husband is not used as a gendered rule; Jupiter is a general stabiliser.

## 4. Caveats

- The partner section prints the archetype caveat; looks and age words appear only there and are graded Weak.
- Fidelity and affairs: only the person's own tendencies, never a statement about a partner.
- No verdict on whether a named person is "the one"; a two-chart question is the match report.
- Intimate topics stay tasteful and tendency-level.
- Parashari only: no Lal Kitab readings or remedies ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | units resting on the 7th house or D9 carry `sensitivity`; drop the D9 reading when its lagna class is `high` or `very high`; windows in months |
| unknown time | `relate` keeps Venus by sign, and the Moon by sign only when it is the same across the whole birth day (else dropped with that reason); drop `windows` (dasha-based; at most labelled monthly markers of slow planets to Venus, or to the Moon under the same rule) and the house-based parts of `partner` |
| any time | height range, build and age gap: no engine calculation exists, so they are dropped (named in `dropped`) unless a cited rule and the chart both support a Weak tendency |
