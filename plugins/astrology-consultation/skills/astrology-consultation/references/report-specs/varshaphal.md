# Varshaphal report spec (`varshaphal`)

The Tajika annual chart for one year of life: its Mudda periods shown as seasons, the year chart itself and the areas
it highlights. The year chart confirms a window the birth chart and its running dasha already show; it never creates
one (timing.md §4). Inside the shared frame ([README.md](README.md)). Parashari Tajika only: never the Lal Kitab
Varshaphal table, which belongs to the Lal Kitab report.

**Order (standard):** `seasons` → `year` → `areas`

Inputs: `birth`, the year of life (default: the year running today). Model: `report_type: "varshaphal"`,
`depth: "standard"`, the frame fields. The `ranking` table ranks the year's areas by support (`item`, `support`, `why`,
`caution`). Required sentence in `scope`: "The year chart confirms a window the birth chart and its running periods
already show; it never creates one."

## 1. Sections and computed fields

| Section | Content | Computed fields → engine tool |
|---|---|---|
| `seasons` | the Mudda periods as seasons of the year (owner decision 12: Mudda only, Patyayini not shown): each lord's stretch named by its months, what it colours, and whether the natal dasha agrees; boundaries to the month (PVR's definition and his own example differ by about two days) | `get_tajika` (`mudda_dasha`); natal MD/AD → `get_dasha` |
| `year` | the year chart: varsha pravesh, annual lagna, day or night year, muntha and its house, harsha bala, the year lord with its reason, or "year lord undetermined" with the shortlist when the engine prints none | `get_tajika` (`varsha_pravesh`, `annual_lagna`, `day_or_night`, `muntha`, `harsha_bala`, `year_lord`, `year_lord_reason`, `year_lord_candidates`, `pancha_vargeeya_bala`) |
| `areas` | two to four life areas the year highlights, each only where the natal dasha or a natal window already points to it; each names the natal basis and the annual-chart factor that confirms it | `get_tajika` (`positions`, `sahams`, `muntha`); natal network → `get_topic_network`, `get_activation`; `get_dasha` |

The timeline carries the Mudda seasons as `chapter` rows (months) and labelled `watch` rows only: no `window` or
`pressure` row, because the year chart creates no window (`spec_checks` enforces this). No exact days anywhere, at any
birth-time class.

Situation check: ask in `next_step` what the person is planning this year. Sensitivity: `get_birth_time_sensitivity`
(the annual lagna and the muntha move with the birth time).

## 2. Method rules and their sources

| Rule | Source |
|---|---|
| The year begins when the Sun returns to its natal sidereal longitude, cast for the birthplace | PVR p379-380 |
| Muntha: the Nth sign from the natal lagna in the Nth year | PVR p386 |
| Harsha bala: four sources of 5 units | PVR p387-388 |
| Pancha vargeeya bala (computed by `get_tajika`; no neutral value, owner check D-6) | PVR p388-391 |
| Year lord: strong candidates (pancha vargeeya bala 10 or more) with a Tajika aspect on the annual lagna; otherwise "year lord undetermined" | PVR p391-393 |
| Sahams: A - B + C by day, reversed at night | PVR p394-395 |
| Mudda dasha: Vimshottari compressed to 360 solar days; PVR ranks it below Patyayini and Varsha Narayana | PVR p411-412 |
| Tajika has no basis in Parasara or Jaimini and is gated by the natal promise | PVR p377-378 |
| Judge the natal dasha and transits first, then the annual chart, and combine | HPA p128-131 |
| Raman calls his solar-return method a snapshot and the return table's year length outdated | HPA p128 |

## 3. Conventions

Lahiri, sidereal year, the birthplace for the return (relocation not applied). Pancha vargeeya bala uses the engine's
default (Sun and Mercury enemies) with the "friends" variant beside it when the year lord changes. One factor counts
once: an annual-chart factor that repeats a natal one is not a second confirmation.

## 4. Caveats

- When `get_tajika` prints no year lord, the report says "year lord undetermined" and lists the shortlist; it never
  picks one.
- No Patyayini or Varsha Narayana periods (owner decision 12; Varsha Narayana is not computed).
- A season is a colour of the months, never a dated event.
- Parashari Tajika only: no Lal Kitab readings, remedies or the Lal Kitab Varshaphal table ([README.md](README.md) §5).

## 5. What to drop

| Data | Drop |
|---|---|
| approximate time | `year` and `areas` units carry `sensitivity`; drop `year` when the annual lagna or the muntha changes within the time range |
| unknown time | drop `seasons` (the Mudda balance needs the Moon's exact longitude), `year` (annual lagna, muntha) and `areas`; at most labelled monthly markers; one house-free `note` section stays; the ranking is dropped |
| any time | an area with no natal basis is not written (the year chart never creates a window) |
