# Reference charts (public or synthetic only)

| File | Kind | What it checks |
|---|---|---|
| `raman_1918.json` | book example (B. V. Raman, *Graha and Bhava Balas*) | Drik Bala: aspect curve, special-aspect additions, benefic/malefic signs |
| `../fixtures/local/S1`, `../fixtures/vedastro/S1_*` | synthetic chart S1 | positions, vargas, dashas against VedAstro |
| property tests (`test_calc_properties.py`) | synthetic boundary cases | sign/nakshatra/pada boundaries, varga identities, dasha structure, time zones |

No real person's private birth data may be added here (the privacy check blocks it).

## edge_suite.json — synthetic boundary charts (v3.5)

22 synthetic charts built by `build_edge_suite.py`, each moment found by bisection so it sits exactly on an edge, with a
chart 30 s either side: normal chart, Moon sign / nakshatra / pada boundaries, ascendant sign boundary, a birth time
that flips the D9 lagna, polar day (Tromsø) and polar night (Svalbard), civil midnight and pre-sunrise in Delhi (the
Hindu day starts at sunrise), 29 February 2024 and 2000, a Mercury station, and a Moon exactly at a nakshatra start
(dasha boundary). Tested in `tests/test_reference_suite.py` (properties + golden positions).
Independent check (2026-10-02): PyJHora 4.8.7 with Lahiri agrees on all 20 charts it can compute (Moon nakshatra, pada,
ascendant sign, D9 lagna, first mahadasha lord, weekday lord); it fails on the two polar charts.
No real person's chart is used anywhere in this folder.
