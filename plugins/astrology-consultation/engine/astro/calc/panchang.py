"""Panchang: tithi, vara, nakshatra and pada, soli-lunar yoga and karana for a local day or a moment. Calculation
only, from the same Swiss Ephemeris positions and Lahiri ayanamsa as the chart engine.

Definitions (LOL ch. 7, p207-224; the arithmetic is the standard definition): tithi = each 12° of the Moon's
elongation from the Sun (30 per lunar month; 15 = full Moon, 30 = new Moon); karana = half a tithi (60 per month:
Kimstughna first, then Bava..Vishti seven times eight, then Shakuni, Chatushpada, Naga); yoga = (sidereal Sun + Moon)
÷ 13°20' (27); vara = the weekday of the Hindu day, which runs from sunrise to sunrise.
"""
from __future__ import annotations

import datetime as dt

import swisseph as swe

from . import engine as E
from .strength import _sun_events

PAKSHA_TITHI = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami",
                "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"]
TITHI = [f"Shukla {t}" for t in PAKSHA_TITHI] + ["Purnima"] + [f"Krishna {t}" for t in PAKSHA_TITHI] + ["Amavasya"]
YOGA = ("Vishkambha Priti Ayushman Saubhagya Shobhana Atiganda Sukarma Dhriti Shula Ganda Vriddhi Dhruva Vyaghata "
        "Harshana Vajra Siddhi Vyatipata Variyan Parigha Shiva Siddha Sadhya Shubha Shukla Brahma Indra Vaidhriti").split()
MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
VARA = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]   # Python weekday() order
CONVENTIONS = {
    "positions": "Swiss Ephemeris apparent geocentric Sun and Moon; sidereal (the ayanamsa in meta; Lahiri by default) for nakshatra and yoga",
    "tithi_karana": "12° and 6° steps of the Moon's elongation from the Sun (independent of the ayanamsa)",
    "sunrise": "centre of the Sun's disc with standard refraction (Swiss Ephemeris rise_trans, BIT_DISC_CENTER); "
               "panchangs using the upper limb give sunrise about a minute earlier",
    "vara": "Hindu day from sunrise to sunrise; before sunrise the previous weekday runs",
    "polar": "where the Sun does not rise or set, 06:00/18:00 local apparent time (flagged)",
}


def _elong(jd):
    s = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    m = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    return (m - s) % 360


def _sum(jd):
    p = E.positions(jd)
    return (p["Su"]["lon"] + p["Mo"]["lon"]) % 360


def _moon(jd):
    return E.positions(jd)["Mo"]["lon"]


FUNCS = {"tithi": (_elong, 12.0), "karana": (_elong, 6.0), "yoga": (_sum, 40 / 3), "nakshatra": (_moon, 40 / 3)}


def _index(kind, jd):
    f, step = FUNCS[kind]
    return int(f(jd) / step + E.EPS) % round(360 / step)


def _end(kind, jd):
    """UT Julian day at which the element running at jd ends (bisection; every element lasts less than 2 days)."""
    f, step = FUNCS[kind]
    v0 = f(jd)
    target = (int(v0 / step + E.EPS) + 1) * step - v0           # degrees still to go
    lo, hi = jd, jd + 2.0
    for _ in range(50):                                          # 2 days / 2**50: far below a second
        mid = (lo + hi) / 2
        if (f(mid) - v0) % 360 < target:
            lo = mid
        else:
            hi = mid
    return hi


def _name(kind, i):
    if kind == "tithi":
        return TITHI[i]
    if kind == "karana":
        return "Kimstughna" if i == 0 else ["Shakuni", "Chatushpada", "Naga"][i - 57] if i >= 57 else MOVABLE[(i - 1) % 7]
    if kind == "yoga":
        return YOGA[i]
    return E.NAKS[i]


def elements(jd):
    """Panchang elements at a moment (UT Julian day)."""
    i_t = _index("tithi", jd)
    nk, pada, _ = E.nak(_moon(jd))
    return {"tithi": {"number": i_t + 1, "name": TITHI[i_t], "paksha": "Shukla" if i_t < 15 else "Krishna"},
            "karana": _name("karana", _index("karana", jd)), "yoga": _name("yoga", _index("yoga", jd)),
            "nakshatra": nk, "pada": pada}


def day(date, lat, lon, tz):
    """The Hindu day that begins with the sunrise of the civil `date` at (lat, lon); tz = UTC offset in hours.
    Elements prevailing at sunrise, and every change until the next sunrise, in local time."""
    E._sid()
    noon = E.jd_of(dt.datetime.combine(date, dt.time(12)) - dt.timedelta(hours=tz))
    r1, s, r2, polar = _sun_events(noon, lat, lon)
    local = lambda jd: (dt.datetime(*swe.revjul(jd, swe.GREG_CAL)[:3]) + dt.timedelta(   # rounded to the minute
        days=swe.revjul(jd, swe.GREG_CAL)[3] / 24 + tz / 24, seconds=30)).strftime("%Y-%m-%d %H:%M")
    y, m, d, _ = swe.revjul(r1 + tz / 24)
    changes = []
    for kind in ("tithi", "nakshatra", "yoga", "karana"):
        t = r1
        while True:
            end = _end(kind, t)
            changes.append({"element": kind, "name": _name(kind, _index(kind, t)), "ends": local(end)})
            if end >= r2:
                break
            t = end + 1e-7
    return {"date": date.isoformat(), "vara": VARA[dt.date(y, m, d).weekday()], "sunrise": local(r1),
            "sunset": local(s), "next_sunrise": local(r2), "polar_fallback": polar,
            "at_sunrise": elements(r1), "changes": changes, "conventions": CONVENTIONS,
            "meta": {"engine": f"astro {E.ENGINE_VERSION}", **E.ephemeris_info(r1), "ayanamsa": E.ayanamsa_name(),
                     "lat": lat, "lon": lon, "utc_offset": E.fmt_offset(tz)}}
