"""Birth-time sensitivity grid: recompute the time-dependent factors at fixed offsets and classify each factor.

Classes (per factor, using the nearest offset at which it changes, either direction):
  robust      — unchanged across ±15 min
  moderate    — first changes between ±5 and ±15 min
  high        — first changes between ±1 and ±5 min
  very high   — changes within ±1 min (treat as unknown unless the birth time is verified to the minute)
The reasoning layer uses these classes to say which conclusions depend on the exact birth time.
"""
from __future__ import annotations

import datetime as dt

from . import engine as E

OFFSETS_MIN = [-15, -10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10, 15]


def _state(ut, lat, lon, on_ut, ylen):
    jd = E.jd_of(ut)
    A = E.asc(jd, lat, lon)
    P = E.positions(jd)
    moon = P["Mo"]["lon"]
    an, ap, _ = E.nak(A)
    mn, mp, _ = E.nak(moon)
    mds = E.vimshottari(moon, ut, ylen, levels=3)
    run = "–".join(next(((md["lord"], ad["lord"], pd["lord"]) for md in mds for ad in md["sub"] for pd in ad["sub"]
                         if pd["start"] <= on_ut < pd["end"]), ("?", "?", "?")))
    return {"ascendant sign": E.SIGNS[int(A // 30)], "ascendant nakshatra-pada": f"{an}-{ap}",
            "D9 lagna": E.SIGNS[E.varga(A, 9)], "D10 lagna": E.SIGNS[E.varga(A, 10)],
            "D12 lagna": E.SIGNS[E.varga(A, 12)], "D60 lagna": E.SIGNS[E.varga(A, 60)],
            "Moon nakshatra-pada": f"{mn}-{mp}", "running MD–AD–PD": run,
            "_md_start": mds[0]["start"]}


def grid(date, time, tz, lat, lon, on=None, year="sidereal"):
    base_ut = dt.datetime.fromisoformat(f"{date}T{time}") - dt.timedelta(hours=tz)
    on_ut = dt.datetime.fromisoformat((on or dt.date.today().isoformat()) + "T12:00") - dt.timedelta(hours=tz)
    ylen = E.YEAR[year]
    states = {o: _state(base_ut + dt.timedelta(minutes=o), lat, lon, on_ut, ylen) for o in OFFSETS_MIN}
    factors = [k for k in states[0] if not k.startswith("_")]
    rows = {f: [states[o][f] for o in OFFSETS_MIN] for f in factors}
    classes, first = {}, {}
    for f in factors:
        changed = [o for o in OFFSETS_MIN if states[o][f] != states[0][f]]
        near = min((abs(o) for o in changed), default=None)
        first[f] = {"earlier": max((o for o in changed if o < 0), default=None),
                    "later": min((o for o in changed if o > 0), default=None)}
        classes[f] = ("robust" if near is None else "moderate" if near > 5 else "high" if near > 1 else "very high")
    shift = {o: round((states[o]["_md_start"] - states[0]["_md_start"]).total_seconds() / 86400, 1)
             for o in OFFSETS_MIN}
    return {"offsets_min": OFFSETS_MIN, "rows": rows, "classes": classes, "first_change_within_grid": first,
            "dasha_boundary_shift_days": shift,
            "note": "dasha dates move by the shift shown when the birth time moves; lords change only where the "
                    "running-period row changes"}


def render(g):
    head = "| Factor | " + " | ".join(f"{o:+g}′" for o in g["offsets_min"]) + " | Class |"
    lines = [head, "|---|" + "---|" * (len(g["offsets_min"]) + 1)]
    for f, vals in g["rows"].items():
        base = vals[g["offsets_min"].index(0)]
        cells = [("**" + v + "**") if v != base else "·" for v in vals]
        cells[g["offsets_min"].index(0)] = base
        lines.append(f"| {f} | " + " | ".join(cells) + f" | {g['classes'][f]} |")
    lines.append("| dasha boundaries (days) | " + " | ".join(f"{g['dasha_boundary_shift_days'][o]:+g}"
                                                          for o in g["offsets_min"]) + " | — |")
    return "\n".join(lines) + "\n\n· = same as the recorded time; bold = changed.\n"
