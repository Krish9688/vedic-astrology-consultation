"""Conditional nakshatra-dasha applicability (BPHS ch. 46): for each of the nine alternative nakshatra dashas, does
its stated chart condition hold? Calculation only: no periods for these systems, and no choice between them.

Vimshottari is the default for every chart (BPHS ch. 46 sl. 2-5). The text gives no rule for choosing when several
conditions hold, so overlaps are flagged, never resolved. Where a translation or a commentary reads a condition
differently, each reading is a separate named row (contradiction register CR-V23, CR-V24). Each verdict is
re-checked at the birth-time sensitivity offsets (sensitivity.offsets), and the row shows where it flips.
Every locator is from the repo source map sourcemaps/BPHS_part4.md §4.2 and is not page-checked.
"""
from __future__ import annotations

import datetime as dt

from . import engine as E, sensitivity as SENS, strength as ST

DEFAULT = "Vimshottari default (BPHS 46.2-5)"
DEFAULT_SOURCE = ("BPHS ch. 46 sl. 2-5 (p496-497, pr 505-506): Vimshottari for people in general, the other "
                  "nakshatra dashas for special cases; source map sourcemaps/BPHS_part4.md §2, not page-checked")
NO_RULE = "more than one condition holds: BPHS gives no rule for choosing (source map BPHS_part4.md §4.2 reader note)"
MAP = "source map sourcemaps/BPHS_part4.md §4.2, not page-checked"
CONVENTIONS = {
    "houses": "whole-sign houses from the sidereal lagna; seven-planet sign lords (Scorpio Mars, Aquarius Saturn)",
    "kendra_trikona_from_lagna_lord": "houses 1, 4, 5, 7, 9, 10 counted from the lagna lord's sign; Rahu in the lagna "
                                      "lord's own sign counts as the 1st (a kendra)",
    "hora": "Parashari hora (engine D2): Leo half = Sun's hora, Cancer half = Moon's hora",
    "paksha": "Shukla while the Moon is less than 180° ahead of the Sun (tithis 1-15), else Krishna",
    "day_night": "day from sunrise to sunset, Sun's disc centre with refraction (strength._sun_events); polar day or "
                 "night uses 06:00/18:00 local apparent time (flag polar_fallback)",
}
KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}


def state(ut, lat, lon, node="mean"):
    """The inputs every condition needs, from the unrounded ephemeris at UT `ut`."""
    jd = E.jd_of(ut)
    r1, s, _, polar = ST._sun_events(jd, lat, lon)
    return {"Asc": E.asc(jd, lat, lon), **{k: v["lon"] for k, v in E.positions(jd, node).items()},
            "day": r1 <= jd < s, "polar_fallback": polar}


def rows(s):
    """One row per condition reading; `default` marks the reading used for the overlap count."""
    sign = lambda k: int(s[k] // 30) % 12
    lag = sign("Asc")
    lord = lambda h: ST.SIGN_LORD[(lag + h - 1) % 12]
    house = lambda k, frm=lag: (sign(k) - frm) % 12 + 1
    hora = "Sun" if E.varga(s["Asc"], 2) == 4 else "Moon"
    d9, d12 = E.varga(s["Asc"], 9), E.varga(s["Asc"], 12)
    shukla, day = (s["Mo"] - s["Su"]) % 360 < 180, s["day"]
    paksha, when = "Shukla" if shukla else "Krishna", "day" if day else "night"
    ll, l7, l10 = lord(1), lord(7), lord(10)
    ra_from_ll = house("Ra", sign(ll))
    rahu = ra_from_ll in KENDRA_TRIKONA and house("Ra") != 1
    pak = day != shukla                                   # day + Krishna, or night + Shukla
    rahu_in = {"lagna": E.SIGNS[lag], "lagna_lord": ll, "lagna_lord_sign": E.SIGNS[sign(ll)],
               "rahu_sign": E.SIGNS[sign("Ra")], "rahu_house_from_lagna_lord": ra_from_ll}
    pak_in = {"birth": when, "paksha": paksha}
    loc = lambda sl, p: f"BPHS ch. 46 sl. {sl} ({p}); {MAP}"
    ash = loc("17-23", "p504-507, pr 513-516")
    dwi = loc("37-39", "p514, pr 523")
    R = [
        ("Ashtottari", "Rahu condition (verse)", True,
         "Rahu in a kendra or trikona from the lagna lord, not in the lagna", rahu, rahu_in, ash),
        ("Ashtottari", "with Santhanam's paksha clause", False,
         "Rahu condition AND (day birth in Krishna paksha or night birth in Shukla paksha); clause added at sl. 23",
         rahu and pak, rahu_in | pak_in, ash),
        ("Ashtottari", "paksha clause alone (PVR's view 3)", False,
         "day birth in Krishna paksha or night birth in Shukla paksha", pak, pak_in,
         ash + "; PVR p240-242 (pr 228-230), source map sourcemaps/PVR_part2.md §4.2, not page-checked"),
        ("Shodashottari", "verse", True,
         "lagna in the Moon's hora with Krishna paksha birth, or in the Sun's hora with Shukla paksha birth",
         (hora == "Moon") != shukla, {"lagna_hora": hora, "paksha": paksha}, loc("24-26", "p508, pr 517")),
        ("Dwadashottari", "verse", True, "lagna in a Venus navamsa (D9 lagna Taurus or Libra)",
         d9 in (1, 6), {"D9_lagna": E.SIGNS[d9]}, loc("27-28", "p510, pr 519")),
        ("Panchottari", "verse", True, "lagna Cancer and in Cancer dwadashamsha",
         lag == 3 and d12 == 3, {"lagna": E.SIGNS[lag], "D12_lagna": E.SIGNS[d12]}, loc("29-31", "p510-512, pr 519-521")),
        ("Shatabdika", "verse", True, "lagna vargottama (same sign in D1 and D9)",
         lag == d9, {"lagna": E.SIGNS[lag], "D9_lagna": E.SIGNS[d9]}, loc("32-34", "p512, pr 521")),
        ("Chaturashiti-sama", "verse", True, "10th lord in the 10th",
         house(l10) == 10, {"10th_lord": l10, "10th_lord_house": house(l10)}, loc("35-36", "p514, pr 523")),
        ("Dwisaptati-sama", "English translation", True, "lagna lord in the lagna or in the 7th",
         house(ll) in (1, 7), {"lagna_lord": ll, "lagna_lord_house": house(ll)}, dwi),
        ("Dwisaptati-sama", "with the Sanskrit's 7th-lord clause (map query)", False,
         "lagna lord in the lagna or the 7th, or the 7th lord in the lagna",
         house(ll) in (1, 7) or house(l7) == 1,
         {"lagna_lord": ll, "lagna_lord_house": house(ll), "7th_lord": l7, "7th_lord_house": house(l7)}, dwi),
        ("Shashtihayani", "verse", True, "Sun in the lagna",
         house("Su") == 1, {"sun_house": house("Su")}, loc("40-41", "p516, pr 525")),
        ("Shattrimsha-sama", "verse", True,
         "day birth with the lagna in the Sun's hora, or night birth with the lagna in the Moon's hora",
         day == (hora == "Sun"), {"birth": when, "lagna_hora": hora}, loc("42-43", "p516-518, pr 525-527")),
    ]
    return [{"dasha": d, "reading": v, "default": df, "condition": c, "holds": h, "inputs": i, "source": src}
            for d, v, df, c, h, i, src in R]


def report(ut, lat, lon, node="mean", span_min=15):
    """Rows at the recorded birth time, each with the nearest offset (minutes) at which its verdict flips."""
    s = state(ut, lat, lon, node)
    base = rows(s)
    offs = [o for o in SENS.offsets(span_min) if o]
    alt = {o: rows(state(ut + dt.timedelta(minutes=o), lat, lon, node)) for o in offs}
    for i, r in enumerate(base):
        flips = [o for o in offs if alt[o][i]["holds"] != r["holds"]]
        r["flips_at_min"] = {"earlier": max((o for o in flips if o < 0), default=None),
                             "later": min((o for o in flips if o > 0), default=None)}
        r["birth_time_sensitive"] = bool(flips)
    applies = sorted({r["dasha"] for r in base if r["default"] and r["holds"]})
    by = {}
    for r in base:
        by.setdefault(r["dasha"], set()).add(r["holds"])
    return {"default": DEFAULT, "default_source": DEFAULT_SOURCE, "applies": applies,
            "overlap": len(applies) > 1, "overlap_note": NO_RULE if len(applies) > 1 else None,
            "reading_dependent": sorted(d for d, v in by.items() if len(v) > 1),
            "birth_time_sensitive": sorted({r["dasha"] for r in base if r["birth_time_sensitive"]}),
            "window_min": span_min, "polar_fallback": s["polar_fallback"], "rows": base, "conventions": CONVENTIONS,
            "note": "Applicability is information only: Vimshottari stays primary and any secondary clock is chosen "
                    "before looking at dates (timing.md §0 step 6). Periods of these systems are not computed."}
