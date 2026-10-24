"""Chara (variable sign) dasha as taught in BPHS ch. 46 sl. 155-167 (Santhanam's translation), page-checked by the owner
on 2026-10-24 (VED-F30; research/VED/M5-draft-answers-A.md and -BC.md). One school only (`bphs_santhanam`, decision
D-3); Rath's JSR Chara and PVR's Narayana dasha are separate variants, not built, and never merged into this one.
Signs only: years per sign and the dasha order. Dates (start at birth, solar years) are a labelled convention added by
the service; BPHS states neither.
"""
from __future__ import annotations

from . import engine as E

SIGNS = ("Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi")
BODIES = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
LORDS = {0: ("Ma",), 1: ("Ve",), 2: ("Me",), 3: ("Mo",), 4: ("Su",), 5: ("Me",), 6: ("Ve",),
         7: ("Ma", "Ke"), 8: ("Ju",), 9: ("Sa",), 10: ("Sa", "Ra"), 11: ("Ju",)}     # sl. 157: Sc Ma+Ke, Aq Sa+Ra
DIGNITY = {"Su": (0, 6), "Mo": (1, 7), "Ma": (9, 3), "Me": (5, 11), "Ju": (3, 9), "Ve": (11, 5), "Sa": (6, 0)}
FORWARD = {0, 1, 2, 6, 7, 8}             # sl. 155-156 footed: padas 1 and 3 (Ar-Ge, Li-Sg) count forward
CONVENTIONS = {
    "count": "exclusive: signs completed from the sign to its lord (worked counts p547, p554)",
    "direction": "footed: Ar Ta Ge Li Sc Sg forward, the other six in reverse (sl. 155-156)",
    "lord_at_home": "a single lord in its own sign gives 12 (BPHS silent; Rath's rule, JSR p276); both Sc/Aq co-lords "
                    "at home give 12 (sl. 158)",
    "dignity": "+1 for an exalted lord, -1 for a debilitated one (sl. 165); no node table (sl. 165 names no node)",
    "co_lords": "Sc/Aq: one lord at home -> the other; else more conjoined planets, then exaltation (printed after the "
                "planet count), then dual > fixed > movable, then the larger count (sl. 158-166)",
    "sequence": "consecutive from the lagna, forward if the 9th from the lagna is in an odd pada (sl. 167)",
    "second_cycle": "not computed: BPHS does not state the second-cycle years (p547)",
    "disputes": "BPHS example (p547) prints Scorpio 6 where the rule gives 9 (Mars and Ketu tie, larger count -> "
                "Ketu); the rule is followed and the print recorded (owner, 2026-10-24). Capricorn 5 there is a "
                "misprint for 2 (Yogardha p551, Kendradi p553)",
}


def _idx(s):
    return s if isinstance(s, int) else SIGNS.index(s)


def _dig(planet, sign):
    ex, deb = DIGNITY.get(planet, (None, None))
    return 1 if sign == ex else -1 if sign == deb else 0


def _count(sign, lord, pos):
    n = ((pos[lord] - sign) if sign in FORWARD else (sign - pos[lord])) % 12
    return n + _dig(lord, pos[lord])


def _co_lord(sign, pos):
    """The lord of Sc or Aq that furnishes the count (sl. 158-166)."""
    a, b = LORDS[sign]
    home = [lord for lord in (a, b) if pos[lord] == sign]
    if len(home) == 1:
        return b if home[0] == a else a
    for step in (lambda lord: sum(pos[x] == pos[lord] for x in BODIES if x != lord),   # more conjoined planets
                 lambda lord: _dig(lord, pos[lord]) == 1,                                # exaltation
                 lambda lord: pos[lord] % 3,                                             # dual 2 > fixed 1 > movable 0
                 lambda lord: _count(sign, lord, pos)):                                  # the larger count
        if step(a) != step(b):
            return a if step(a) > step(b) else b
    return a                             # equal counts: either lord gives the same years


def _years(sign, pos):
    lords = LORDS[sign]
    if all(pos[lord] == sign for lord in lords):
        return 12
    lord = _co_lord(sign, pos) if len(lords) == 2 else lords[0]
    return _count(sign, lord, pos)


def _positions(positions):
    pos = {k: _idx(v) for k, v in positions.items()}
    missing = {"La", *BODIES} - set(pos)
    if missing:
        raise ValueError(f"missing positions: {sorted(missing)}")
    return pos


def sign_years(positions):
    """positions: {'La', 'Su'..'Ke': sign ('Ar'.. or 0-11)} -> {sign: years}, first cycle."""
    pos = _positions(positions)
    return {SIGNS[s]: _years(s, pos) for s in range(12)}


def dasha(positions):
    """[(sign, years)] in dasha order from the lagna (sl. 167); zero-year dashas are kept as rows (owner item D2)."""
    pos = _positions(positions)
    la = pos["La"]
    step = 1 if (la + 8) % 12 in FORWARD else -1
    return [(SIGNS[(la + step * i) % 12], _years((la + step * i) % 12, pos)) for i in range(12)]


def antardashas(sign):
    """BPHS ch. 51 sl. 7-12 (the default; it names the Chara dasha): movable -> all 12 in order, fixed -> every 6th
    sign, dual -> its kendras, then the 5th's, then the 9th's; forward from an odd sign, reverse from an even one.
    Twelve equal parts. Worked lists: PDF p614-615 (Aquarius, Pisces, Aries)."""
    s = _idx(sign)
    offs = (range(12), [5 * i for i in range(12)], [0, 3, 6, 9, 4, 7, 10, 1, 8, 11, 2, 5])[s % 3]
    step = 1 if s % 2 == 0 else -1                     # Ar, Ge, Le, Li, Sg, Aq are the odd signs
    return [SIGNS[(s + step * o) % 12] for o in offs]


def ch50_start(sign, positions):
    """BPHS ch. 50 sl. 90-96, the alternative: antardashas start from the sign holding the dasha lord (for Sc/Aq the
    lord that furnished the years). The chapter gives no order, so only the start is reported."""
    pos = _positions(positions)
    s = _idx(sign)
    lords = LORDS[s]
    if all(pos[lord] == s for lord in lords):
        return SIGNS[s]
    return SIGNS[pos[_co_lord(s, pos) if len(lords) == 2 else lords[0]]]


def signs_of(chart):
    """An engine chart (engine.compute) -> the sign positions this module takes."""
    return {("La" if k == "Asc" else k): E.SIGNS.index(v["sign"]) for k, v in chart["bodies"].items()}
