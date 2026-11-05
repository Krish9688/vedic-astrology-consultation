"""The stable, vendor-neutral service layer. The CLI, the MCP server and the REST API all call these functions and
nothing else, so every client gets the same validated inputs, privacy rules and outputs.

Responsibilities stay separate: calculation (astro.calc), knowledge (the skill's local search scripts), reasoning
(the AI client following the skill's method — this layer supplies facts, sensitivity classes and the method text;
it does not pretend to reason), reports (render a Structured Report Model).
"""
from __future__ import annotations

import datetime as dt
import functools
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import zoneinfo
import sys
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from . import config, places, routing as ROUTING
from .calc import compute_full, engine, jaimini, sensitivity, strength

VERSION = "3.7.0"
SOURCE_URL = "https://github.com/Krish9688/vedic-astrology-consultation"
SOURCE_NOTICE = ("This service is free software under the GNU Affero General Public License v3 or later, with NO "
                 "WARRANTY. The Corresponding Source of the version running here is available at the 'source' URL. "
                 "If you run a modified version for other people over a network, set source_url in the config to "
                 "your modified source (AGPL-3.0 section 13).")
THIRD_PARTY = ("Swiss Ephemeris © Astrodienst AG (AGPL-3.0); pyswisseph; IANA tz database (public domain); "
               "place data, if installed: GeoNames (CC-BY 4.0)")
REMOTE = False   # set by the HTTP servers when they listen beyond localhost
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
TOPICS = ROUTING.TOPICS   # question → the skill's topic reference; the manifest astro/routing.py is the one source (SKILL.md is test-checked against it)


OFFSET = re.compile(r"^(?:UTC|GMT)?([+-])?(\d{1,2}):([0-5]\d)(?::([0-5]\d))?$", re.I)
OFFSET_COMPACT = re.compile(r"^(?:UTC|GMT)?([+-])(\d{2})([0-5]\d)$", re.I)   # ISO 8601 basic form, sign required: +0530
MAX_OFFSET_H = 14                                     # real civil offsets lie within -12..+14 (audit F-03)


# 20-minute standard offsets the tz database has used (council RC-07); any other 20-minute value, e.g. a mistyped +05:20
# for +05:30, is treated as non-standard (flagged when stated, refused from a zone).
TWENTY_MINUTE_STANDARD = {sg * (h * 3600 + m * 60) for sg, h, m in ((1, 7, 20), (1, 8, 20), (-1, 4, 40), (-1, 10, 40),
                                                                   (-1, 11, 20), (1, 12, 20), (1, 0, 20), (-1, 0, 20))}


def standard_offset(seconds) -> bool:
    """A standard-time offset is a whole number of quarter hours, or one of the historical 20-minute standard times
    (TWENTY_MINUTE_STANDARD). Anything else (e.g. +05:53:20, +04:51) is a local or city mean time (audit F-06)."""
    s = round(seconds)
    return s % 900 == 0 or s in TWENTY_MINUTE_STANDARD


def nonstandard_flag(hours) -> list:
    """Flag for an explicitly stated offset that is not a standard time (owner decision 2026-11-01: accepted as stated,
    never suggested)."""
    if standard_offset(hours * 3600):
        return []
    return [f"non-standard offset {utc_offset_str(dt.timedelta(hours=hours))}: not a standard time-zone offset (a local "
            "or city mean time); used exactly as stated - confirm it with the birth record"]


def utc_offset_hours(v) -> float:
    """'+05:30', '-03:00', 'UTC+05:45' or '+05:53:20'; decimal hours only in whole or quarter steps (5.5, -3.75).
    A decimal such as 5.30 is refused: it would silently mean 5 h 18 min, a 3.6° ascendant shift (audit H1)."""
    if isinstance(v, str):
        s = v.strip().replace(" ", "")
        m = OFFSET.match(s) or OFFSET_COMPACT.match(s)
        if m:
            sign, h, mi, se = (m.groups() + (None,))[:4]
            hours = int(h) + int(mi) / 60 + int(se or 0) / 3600
            hours = -hours if sign == "-" else hours
            if abs(hours) > MAX_OFFSET_H:
                raise ValueError(f"UTC offset {v!r} is outside -14:00..+14:00; write it as +HH:MM, e.g. +05:30")
            return hours
        if re.fullmatch(r"[+-]?\d{3,4}", s):
            raise ValueError(f"UTC offset {v!r}: write it as +HH:MM, e.g. +05:30 (or with a sign, +0530)")
        try:
            v = float(v)
        except ValueError:
            raise ValueError(f"UTC offset {v!r}: write it as +HH:MM, e.g. +05:30") from None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError("UTC offset: write it as +HH:MM, e.g. +05:30")
    if abs(v * 4 - round(v * 4)) > 1e-9:
        raise ValueError(f"UTC offset {v}: decimal hours must be whole or .25/.5/.75 (5.30 would mean 5 h 18 min); "
                         "write it as +HH:MM, e.g. +05:30")
    if abs(v) > MAX_OFFSET_H:
        raise ValueError(f"UTC offset {v} is outside -14:00..+14:00; write it as +HH:MM, e.g. +05:30")
    return float(v)


def tzdb_version():
    """IANA tz database release in use, in zoneinfo's own lookup order: the system's files, then the tzdata package."""
    for root in zoneinfo.TZPATH:
        try:
            with open(os.path.join(root, "tzdata.zi"), encoding="utf-8") as f:
                return f.readline().split()[-1]
        except (OSError, IndexError):
            continue
    try:
        import tzdata
        return tzdata.IANA_VERSION
    except (ImportError, AttributeError):
        return "unknown"


def resolve_zone(date, time, zone, lon, fold=None):
    """Local clock time in an IANA zone → (UTC offset hours, flags). Refuses what the database cannot settle: a clock
    time skipped by a transition, a repeated one without `fold`, and local mean time (the tz database's LMT offsets
    'should not be considered meaningful', data.iana.org/time-zones/theory.html)."""
    try:
        z = zoneinfo.ZoneInfo(zone)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"unknown IANA time zone {zone!r} (e.g. Asia/Kolkata, Europe/London)") from None
    local = dt.datetime.combine(date, dt.time.fromisoformat(time))
    a, b = local.replace(tzinfo=z, fold=0), local.replace(tzinfo=z, fold=1)
    if a.astimezone(dt.timezone.utc).astimezone(z).replace(tzinfo=None) != local and \
            b.astimezone(dt.timezone.utc).astimezone(z).replace(tzinfo=None) != local:
        raise ValueError(f"{date} {time} does not exist in {zone} (clocks jumped forward): check the birth record and "
                         "give the UTC offset explicitly")
    if a.utcoffset() != b.utcoffset() and fold is None:
        raise ValueError(f"{date} {time} occurs twice in {zone} (clocks went back): pass fold=0 for the first "
                         f"({utc_offset_str(a.utcoffset())}) or fold=1 for the second ({utc_offset_str(b.utcoffset())})")
    t = b if fold == 1 else a
    if t.tzname() == "LMT" or not standard_offset(t.utcoffset().total_seconds()):
        # No local mean time is ever offered or derived (owner rule: civil time with a stated offset, never LMT). The tz
        # database's LMT and its city mean times (e.g. Asia/Kolkata +05:53:20 before 1870, +05:21:10 to 1906) are refused.
        raise ValueError(f"{zone} on {date} is before standard time: the tz database gives a mean time "
                         f"({t.tzname()}), not a standard offset, so it cannot settle the clock. Give the UTC offset the "
                         "birth record states (+HH:MM)")
    flags = []
    if date.year < 1970:
        flags.append("IANA offsets before 1970 often come from unreliable sources (tz theory.html): confirm with the "
                     "birth record")
    if zone in ("Asia/Kolkata", "Asia/Calcutta", "Asia/Karachi", "Asia/Dhaka", "Asia/Colombo") and date.year < 1948:
        flags.append("pre-1948 South Asian offsets are disputed (railway, local and war time): confirm the clock used")
    return t.utcoffset().total_seconds() / 3600, flags


def utc_offset_str(td):
    s = round(td.total_seconds())
    sign, s = ("-" if s < 0 else "+"), abs(s)
    return f"{sign}{s // 3600:02d}:{s % 3600 // 60:02d}" + (f":{s % 60:02d}" if s % 60 else "")


class BirthInput(BaseModel):
    date: dt.date
    time: str = Field(pattern=r"^\d{1,2}:\d{2}(:\d{2})?$")
    tz: Optional[float] = Field(default=None, ge=-14, le=14, description="UTC offset at the birth moment as +HH:MM "
                                "(include daylight saving); decimal hours only in whole or quarter steps")
    zone: Optional[str] = Field(default=None, max_length=64, description="IANA time zone, e.g. Asia/Kolkata: the offset "
                                "at the birth moment is taken from the tz database (historical rules included)")
    fold: Optional[int] = Field(default=None, ge=0, le=1, description="for a clock time that occurs twice: 0 = first, "
                                "1 = second")
    lat: float = Field(ge=-89.9, le=89.9, description="the ascendant is undefined at the poles")
    lon: float = Field(ge=-180, le=180)
    label: Optional[str] = Field(default=None, max_length=64)
    time_source: Optional[str] = Field(default=None, max_length=120)
    tz_source: Optional[str] = None
    tz_flags: list = Field(default_factory=list)
    calendar: str = Field(default="gregorian", pattern="^(gregorian|julian)$",
                          description="the calendar the date is written in; a Julian date is converted to Gregorian")
    julian_date: Optional[str] = Field(default=None, max_length=10, description="the date as written in the Julian "
                                       "calendar; set from `date` when calendar='julian'")
    date_source: Optional[str] = Field(default=None, max_length=120)

    @model_validator(mode="before")
    @classmethod
    def _julian(cls, data):
        """P8-3e: a Julian-calendar date (old records, pre-1752 Britain, pre-1918 Russia) becomes the Gregorian date the
        engine uses, through Swiss Ephemeris julday/revjul. The original stays in julian_date and is always the one
        converted, so a re-created input converts to the same day and no caller field can switch the conversion off."""
        if not isinstance(data, dict):
            return data
        if data.get("calendar") != "julian":
            return data | {"julian_date": None, "date_source": None}
        y, m, d = (int(x) for x in str(data.get("julian_date") or data.get("date", "")).split("-"))
        swe = engine.swe
        jd = swe.julday(y, m, d, 0.0, swe.JUL_CAL)
        if swe.revjul(jd, swe.JUL_CAL)[:3] != (y, m, d):
            raise ValueError(f"{y:04d}-{m:02d}-{d:02d} is not a date in the Julian calendar")
        gy, gm, gd = swe.revjul(jd, swe.GREG_CAL)[:3]
        if not 2 <= gy <= 2999:
            raise ValueError(f"Julian {y:04d}-{m:02d}-{d:02d} is Gregorian {gy:04d}-{gm:02d}-{gd:02d}, outside the years 2-2999")
        return data | {"date": f"{gy:04d}-{gm:02d}-{gd:02d}", "julian_date": f"{y:04d}-{m:02d}-{d:02d}",
                       "date_source": f"Julian calendar {y:04d}-{m:02d}-{d:02d}, converted to Gregorian {gy:04d}-{gm:02d}-{gd:02d}"}

    @field_validator("tz", mode="before")
    @classmethod
    def _offset(cls, v):
        return None if v is None else utc_offset_hours(v)

    @field_validator("date")
    @classmethod
    def _range(cls, v):
        if not 2 <= v.year <= 2999:
            raise ValueError("dates must lie between the years 2 and 2999 (Moshier outside 1800-2399)")
        return v

    @field_validator("time")
    @classmethod
    def _clock(cls, v):
        h, m, *s = (int(x) for x in v.split(":"))
        if not (0 <= h < 24 and 0 <= m < 60 and all(0 <= x < 60 for x in s)):
            raise ValueError("time must be a valid 24-hour clock time")
        return f"{h:02d}:{m:02d}:{(s or [0])[0]:02d}"   # zero-padded: the engine parses ISO times (P1-5)

    @model_validator(mode="after")
    def _resolve(self):
        if self.zone and self.tz is not None:   # P2-1: a manual offset always overrides; the IANA view is kept as a flag
            given = utc_offset_str(dt.timedelta(hours=self.tz))
            try:
                hours, flags = resolve_zone(self.date, self.time, self.zone, self.lon, self.fold)
                if abs(self.tz - hours) > 1 / 3600:
                    flags = [f"manual offset {given} overrides IANA {self.zone} "
                             f"({utc_offset_str(dt.timedelta(hours=hours))}, tzdb {tzdb_version()}): confirm it with "
                             "the birth record"] + flags
            except ValueError as e:              # a skipped/repeated clock time or the LMT era: the offset settles it
                if str(e).startswith("unknown IANA time zone"):
                    raise                        # a misspelt zone is still refused
                flags = [f"IANA {self.zone} cannot resolve this time ({e}); manual offset {given} used"]
            self.tz_flags = flags
            self.tz_source = f"manual UTC offset (zone {self.zone} given)"
        elif self.zone:
            hours, flags = resolve_zone(self.date, self.time, self.zone, self.lon, self.fold)
            self.tz, self.tz_flags = hours, flags
            self.tz_source = f"IANA {self.zone} (tzdb {tzdb_version()})" + (f", fold={self.fold}" if self.fold is not None else "")
        elif self.tz is None:
            raise ValueError("give the UTC offset at birth (+HH:MM) or an IANA time zone (zone)")
        else:
            self.tz_source = self.tz_source or "explicit UTC offset"
        if self.tz is not None and (f := nonstandard_flag(self.tz)) and not any(x.startswith("non-standard") for x in self.tz_flags):
            self.tz_flags = f + list(self.tz_flags)
        return self


class Options(BaseModel):
    on: Optional[dt.date] = None        # reference date for transits / running periods (default today)
    months: int = Field(default=24, ge=1, le=120)
    node: str = Field(default="mean", pattern="^(mean|true)$")
    year: str = Field(default="sidereal", pattern="^(sidereal|365.25|360)$")
    ayanamsa: str = Field(default="lahiri", pattern="^(" + "|".join(engine.AYANAMSAS) + ")$",
                          description="lahiri (default); true_chitra, kp or raman only as an explicit choice")

    model_config = {"frozen": True}


DEFAULTS = Options()


def _calc(fn):
    """Run a service function under the chosen ayanamsa (engine.using): natal, transit and derived figures in one call
    always share one mode, and calls with different modes never interleave."""
    @functools.wraps(fn)
    def run(*a, **k):
        o = k.get("o") or next((x for x in a if isinstance(x, Options)), None)
        name = o.ayanamsa if o else k.get("ayanamsa")   # Options-less tools (panchang) take a keyword ayanamsa (#47)
        with engine.using(name):   # None: keep the caller's mode (e.g. CLI --ayanamsa)
            return fn(*a, **k)
    return run


def _args(b: BirthInput, o: Options):
    return (b.date.isoformat(), b.time, b.tz, b.lat, b.lon), dict(
        node=o.node, year=o.year, on=(o.on or dt.date.today()).isoformat(), months=o.months)


def find_place(name: str, country: Optional[str] = None) -> dict:
    """Offline place lookup (GeoNames); nothing leaves the machine. Ambiguous names return every candidate."""
    return places.search(name[:120], config.load().data_dir, country=(country or "")[:2] or None)


def source_offer(s=None) -> dict:
    """AGPL-3.0 section 13: where network users get the Corresponding Source."""
    s = s or config.load()
    return {"license": "AGPL-3.0-or-later", "source": s.source_url or f"{SOURCE_URL}/tree/v{VERSION}",
            "source_notice": SOURCE_NOTICE, "third_party": THIRD_PARTY}


def engine_info() -> dict:
    s = config.load()
    return {"service": "astrology-consultation", "version": VERSION, "engine": engine.ENGINE_VERSION,
            **source_offer(s),
            **engine.ephemeris_info(), "ayanamsa": f"{engine.AYANAMSA_NAME} (default)", "ayanamsas": list(engine.AYANAMSAS), "privacy_mode": s.mode,
            "knowledge_available": bool(s.knowledge_dir), "skill_available": bool(s.skill_dir),
            "vargas": engine.VARGA_METHODS, "shadbala_conventions": strength.SHADBALA_CONVENTIONS,
            "jaimini_conventions": jaimini.CONVENTIONS}


def _compute(b: BirthInput, o: Options = DEFAULTS, full=False, **kw):
    """The one way service code computes a chart: the birth input's provenance (zone, offset source and warnings,
    time source, label) joins the calculation meta on every output."""
    a, okw = _args(b, o)
    c = compute_full(*a, **okw) if full else engine.compute(*a, **okw, **kw)
    c["meta"] |= {k: v for k, v in (("time_source", b.time_source), ("label", b.label), ("zone", b.zone),
                                    ("date_source", b.date_source),
                                    ("utc_offset_source", b.tz_source), ("utc_offset_flags", b.tz_flags)) if v}
    return c


@_calc
def calculate_chart(b: BirthInput, o: Options = DEFAULTS, full: bool = True) -> dict:
    return _compute(b, o, full=full)   # P1-5: time_source and label never dropped


@_calc
def planet_positions(b: BirthInput, o: Options = DEFAULTS) -> dict:
    c = _compute(b, o, extras=False)
    return {"meta": c["meta"], "bodies": {k: {x: v[x] for x in ("sign", "deg", "lon", "nakshatra", "pada", "retro")}
                                          for k, v in c["bodies"].items()}}


def _with_meta(c: dict, out: dict) -> dict:
    """Every chart-derived output carries the chart's calculation provenance (audit H3, PRED-F9)."""
    return out if "meta" in out else out | {"meta": c["meta"]}


@_calc
def divisional_chart(b: BirthInput, division: int, o: Options = DEFAULTS) -> dict:
    if division not in engine.VARGAS:
        raise ValueError(f"supported divisions: {engine.VARGAS}")
    c = _compute(b, o, extras=False)
    return _with_meta(c, {"division": f"D{division}", "method": engine.VARGA_METHODS[f"D{division}"],
                          "signs": {k: v["vargas"][f"D{division}"] for k, v in c["bodies"].items()}})


@_calc
def dasha(b: BirthInput, o: Options = DEFAULTS) -> dict:
    c = _compute(b, o, extras=False)
    on = _args(b, o)[1]["on"]
    running = next(([md["lord"], ad["lord"], pd["lord"]] for md in c["vimshottari"] for ad in md["sub"]
                    for pd in ad["sub"] if pd["start"] <= on < pd["end"]), None)
    return _with_meta(c, {"system": "Vimshottari", "year_days": engine.YEAR[o.year], "running_on": on,
                          "running": running, "periods": c["vimshottari"]})


def julian_to_gregorian(d) -> dt.date:
    """A date written in the Julian calendar ('YYYY-MM-DD' or a date) → the Gregorian date (Swiss Ephemeris
    julday/revjul), as BirthInput does. Parsed from integers: Julian 1700-02-29 is not a Gregorian date (RC-08)."""
    y, m, dd = (int(x) for x in str(d)[:10].split("-"))
    jd = engine.swe.julday(y, m, dd, 0.0, engine.swe.JUL_CAL)
    if engine.swe.revjul(jd, engine.swe.JUL_CAL)[:3] != (y, m, dd):
        raise ValueError(f"{str(d)[:10]} is not a date in the Julian calendar")
    return dt.date(*engine.swe.revjul(jd, engine.swe.GREG_CAL)[:3])


@_calc
def panchang(date, lat: float, lon: float, tz=None, zone: Optional[str] = None, *, ayanamsa: Optional[str] = None,
             calendar: str = "gregorian") -> dict:
    """Panchang of the Hindu day that begins at the sunrise of `date` at (lat, lon). No birth data needed.
    ayanamsa: None keeps the caller's mode (Lahiri by default); calendar='julian' converts the date first (#47)."""
    from .calc import panchang as P
    if calendar not in ("gregorian", "julian"):
        raise ValueError("calendar must be gregorian or julian")
    written = str(date)[:10]
    d = julian_to_gregorian(written) if calendar == "julian" else dt.date.fromisoformat(written)
    if not (-89.9 <= lat <= 89.9 and -180 <= lon <= 180):
        raise ValueError("latitude must be within ±89.9° and longitude within ±180°")
    if zone:
        hours, flags = resolve_zone(d, "12:00:00", zone, lon)
        if tz is not None and abs(utc_offset_hours(tz) - hours) > 1 / 3600:
            raise ValueError(f"tz disagrees with {zone} on {d}: give one")
    elif tz is not None:
        hours = utc_offset_hours(tz)
        flags = nonstandard_flag(hours)
    else:
        raise ValueError("give the UTC offset (+HH:MM) or an IANA time zone (zone)")
    out = P.day(d, lat, lon, hours)
    out["meta"] |= {k: v for k, v in (("zone", zone), ("utc_offset_flags", flags)) if v}
    if calendar == "julian":
        out["meta"]["date_source"] = f"Julian calendar {written}, converted to Gregorian {d}"
    return out


@_calc
def gochara(b: BirthInput, o: Options = DEFAULTS) -> dict:
    """Transits on `on` against the natal chart: PD XXVI gochara from the Moon with vedha and condition, lagna frame
    separate, sade sati."""
    from .calc import transit as TR
    c = _compute(b, o, extras=False)
    on = c["meta"]["transit_date"]
    jd = engine.jd_of(dt.datetime.fromisoformat(on + "T12:00") - dt.timedelta(hours=b.tz))
    moon, asc = int(c["bodies"]["Mo"]["lon"] // 30), int(c["bodies"]["Asc"]["lon"] // 30)
    sat = int(engine.positions(jd, o.node)["Sa"]["lon"] // 30)
    return _with_meta(c, {"on": on, "time": "12:00 local (birth UTC offset)", "rows": TR.gochara(jd, moon, asc, o.node, strength.ashtakavarga(c)),
                          "sade_sati": TR.sade_sati(sat, moon), "sources": TR.SOURCES})


@_calc
def outlook(b: BirthInput, period: str = "month", start=None, o: Options = DEFAULTS) -> dict:
    """Chart-specific factors for a day, week, month or year from `start` (default today): dashas, gochara, sade sati,
    sign changes, stations, slow-planet contacts and (day/week) the Moon's transit. Facts only; see timing.md §3a."""
    from .calc import transit as TR
    if period not in TR.PERIODS:
        raise ValueError(f"period must be one of {', '.join(TR.PERIODS)}")
    d = dt.date.fromisoformat(str(start)) if start else dt.date.today()
    o = Options(on=d, months=o.months, node=o.node, year=o.year, ayanamsa=o.ayanamsa)
    c = _compute(b, o, extras=False)
    y = yogini_dasha(b, o)["periods"]
    return _with_meta(c, TR.outlook(c, d, period, b.tz, y, o.node))


@_calc
def compatibility(girl: BirthInput, boy: BirthInput, o: Options = DEFAULTS) -> dict:
    """PM2 ch. XXI Moon-sign and birth-star counts between two charts, each with its verse, and four rule-fixed kootas
    (P8-2N1) as facts; no score, no total, no verdict.
    Needs both people's consent: it is two people's birth data."""
    from .calc import match
    cs = [_compute(b, o, extras=False) for b in (girl, boy)]
    pts = []
    for b in (girl, boy):                              # unrounded: chart longitudes are rounded to 0.0001°
        jd = engine.jd_of(dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz))
        pts.append({"moon": engine.positions(jd, o.node)["Mo"]["lon"], "asc": engine.asc(jd, b.lat, b.lon)})
    return match.facts(*pts) | {"source": "Prasna Marga II ch. XXI (Raman), p96-107; source map, not page-checked. "
                                          "kootas: Muhurta Chintamani ch. 6 (four rule-fixed kootas, research/KB/R3)",
                                "meta": {"girl": cs[0]["meta"], "boy": cs[1]["meta"]}}


@_calc
def tajika(b: BirthInput, year: Optional[int] = None, o: Options = DEFAULTS) -> dict:
    """Tajika annual chart (PVR ch. 27-28, 31) for year N of life (default: the year running on `on`): solar return at
    the birthplace, muntha, harsha bala, year-lord candidates, sahams, Mudda and Patyayini dashas, pancha vargeeya bala
    (Sun-Mercury enemies by default, the 'friends' variant shown beside it). Secondary to the natal chart."""
    from .calc import tajika as TJ
    c = _compute(b, o, extras=False)
    bj = engine.jd_of(dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz))
    P = engine.positions(bj, o.node)                  # unrounded: 0.0001° of Sun is ~9 s of return time
    natal = {"Su": P["Su"]["lon"], "Mo": P["Mo"]["lon"], "Asc": engine.asc(bj, b.lat, b.lon)}
    if year is None:
        on = engine.jd_of(dt.datetime.fromisoformat(c["meta"]["transit_date"] + "T12:00") - dt.timedelta(hours=b.tz))
        if on < bj:
            raise ValueError("the date asked about is before the birth")
        n = int((on - bj) / TJ.SIDEREAL_YEAR)
        n -= TJ.varsha_pravesh(bj, natal["Su"], n) > on
        n += TJ.varsha_pravesh(bj, natal["Su"], n + 1) <= on     # the return can fall just before the mean-year estimate
    elif year < 1:
        raise ValueError("year is the year of life, 1 or more (year 1 starts at birth)")
    else:
        n = year - 1
    a = TJ.annual(bj, natal, n, b.lat, b.lon, o.node)
    local = lambda jd: (dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=jd - 2451545.0, hours=b.tz, seconds=0.5)
                        ).strftime("%Y-%m-%d %H:%M:%S")                 # JD 2451545.0 = 2000-01-01 12:00 UT
    pos = lambda x: f"{engine.SIGNS[int(x // 30)]} {x % 30:.2f}"
    return _with_meta(c, {
        "year": a["year"], "completed_years": n, "varsha_pravesh": local(a["jd"]),
        "time": f"local clock at the birth UTC offset ({engine.fmt_offset(b.tz)}); cast for the birthplace",
        "annual_lagna": pos(a["asc"]), "day_or_night": "night" if a["night"] else "day",
        "positions": {p: pos(v["lon"]) for p, v in a["positions"].items()},
        "muntha": engine.SIGNS[a["muntha"]], "harsha_bala": a["harsha_bala"], "year_lord_candidates": a["candidates"],
        "year_lord": a["year_lord"], "year_lord_reason": a["year_lord_reason"],
        "sahams": {k: pos(v) for k, v in a["sahams"].items()},
        "mudda_dasha": [{"lord": r["lord"], "start": local(r["start_jd"])[:16], "end": local(r["end_jd"])[:16],
                         "solar_days": r["solar_days"]} for r in a["mudda"]],
        "patyayini_dasha": [{"lord": r["lord"], "start": local(r["start_jd"])[:16], "end": local(r["end_jd"])[:16],
                             "days": round(r["days"], 2), "antardashas": [
                                 {"lord": x["lord"], "start": local(x["start_jd"])[:16], "end": local(x["end_jd"])[:16]}
                                 for x in r["antardashas"]]} for r in a["patyayini"]],
        "pancha_vargeeya_bala": {k: v for k, v in a["pancha_vargeeya_bala"].items() if k != "by_variant"},
        "sources": TJ.SOURCES, "not_computed": TJ.NOT_COMPUTED})


@_calc
def chara_dasha(b: BirthInput, o: Options = DEFAULTS) -> dict:
    """Chara (sign) dasha, BPHS ch. 46 (Santhanam), first cycle: years per sign and dates from birth. A sign-based
    timing layer beside Vimshottari, not a replacement; Jaimini/Narayana variants are not computed."""
    from .calc import chara as CH
    from .calc.tajika import SIDEREAL_YEAR
    c = _compute(b, o, extras=False)
    jd = engine.jd_of(dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz))
    local = lambda x: (dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=x - 2451545.0, hours=b.tz, seconds=0.5)
                       ).strftime("%Y-%m-%d")                           # JD 2451545.0 = 2000-01-01 12:00 UT
    full = lambda s: engine.SIGNS[CH.SIGNS.index(s)]
    pos, rows = CH.signs_of(c), []
    for sign, years in CH.dasha(pos):
        end, part = jd + years * SIDEREAL_YEAR, years * SIDEREAL_YEAR / 12
        ads = [{"sign": full(a), "start": local(jd + k * part), "end": local(end if k == 11 else jd + (k + 1) * part)}
               for k, a in enumerate(CH.antardashas(sign))] if years else []
        rows.append({"sign": full(sign), "years": years, "start": local(jd), "end": local(end), "antardashas": ads,
                     "antardasha_ch50_start": full(CH.ch50_start(sign, pos))})
        jd = end
    return _with_meta(c, {
        "school": "bphs_santhanam", "dasas": rows,
        "year_length": "convention: sidereal solar years from birth (BPHS states no start or year length)",
        "antardasha_rule": "BPHS ch. 51 sl. 7-12 (names the Chara dasha; owner default 2026-10-24): 12 equal parts, "
                           "movable all signs in order, fixed every 6th, dual kendras of it, its 5th, its 9th; forward "
                           "from an odd sign. Alternative, BPHS ch. 50 sl. 90-96: start from the sign holding the dasha "
                           "lord (antardasha_ch50_start); that chapter gives no order",
        "conventions": CH.CONVENTIONS,
        "not_computed": "second cycle (years not stated in BPHS), Paka/Bhoga signs (ch. 51), Jaimini (Rath) and "
                        "Narayana (PVR) variants"})


@_calc
def yogini_dasha(b: BirthInput, o: Options = DEFAULTS) -> dict:
    """Yogini mahadashas (BPHS ch. 46 sl. 195-200); a secondary, conditional dasha - Vimshottari stays the default."""
    c = _compute(b, o, extras=False)
    ut = dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz)
    ylen, on = engine.YEAR[o.year], c["meta"]["transit_date"]
    fmt = lambda t: (t + dt.timedelta(hours=b.tz)).strftime("%Y-%m-%d")
    rows = [dict(r, start=fmt(r["start"]), end=fmt(r["end"])) for r in engine.yogini(c["bodies"]["Mo"]["lon"], ut, ylen)]
    return _with_meta(c, {"system": "Yogini", "source": "BPHS ch. 46 sl. 195-200 (p563): opening yogini = (birth "
                          "nakshatra number + 3) mod 8, years 1-8; the source gives no sub-period rule",
                          "year_days": ylen, "running_on": on,
                          "running": next((r["yogini"] for r in rows if r["start"] <= on < r["end"]), None),
                          "periods": rows})


@_calc
def dasha_applicability(b: BirthInput, o: Options = DEFAULTS, span_min: int = 15) -> dict:
    """Which BPHS ch. 46 conditional nakshatra dashas' chart conditions hold, with readings, overlaps and birth-time
    flips; Vimshottari stays the default. Information only (timing.md §0 step 6)."""
    from .calc import applicability as AP
    c = _compute(b, o, extras=False)
    ut = dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz)
    return _with_meta(c, AP.report(ut, b.lat, b.lon, o.node, span_min))


def _chart_key(c):
    m = c["meta"]
    mode = m["ayanamsa"].rsplit(" ", 1)[0]          # "Lahiri 23.85°" -> "Lahiri"; the default keeps the old key
    key = [m["birth_local"], m["lat"], m["lon"], m["nodes"]] + ([mode] if mode != engine.AYANAMSA_NAME else [])
    return "sha256:" + hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]


def _facts_ids(c):
    f = _derived_facts(c, ids=True)
    if isinstance(f, str):
        raise FileNotFoundError(f)
    return f["facts"]


@_calc
def topic_network(b: BirthInput, topic: Optional[str] = None, planets: Optional[list] = None,
                  o: Options = DEFAULTS) -> dict:
    """A significator network frozen by its hash (timing.md §0 step 3): Raman's (a)-(g) list plus the topic extras
    (marriage, career, finance, relocation, education, children), every entry source-tagged, or a caller-supplied
    planet list (flagged unsourced). Build it before looking at any dates."""
    from .calc import activation as A
    c = _compute(b, o, extras=False)
    F, key = _facts_ids(c), _chart_key(c)
    if (topic is None) == (planets is None):
        raise ValueError("give a topic or a planet list, not both")
    net = A.preset(F, topic, key) if topic else A.custom(planets, key, F)
    return net | {"frozen_at_utc": c["meta"]["computed_at_utc"], "meta": c["meta"]}


def _network(b, c, network):
    from .calc import activation as A
    if isinstance(network, str):                      # a topic name: built and frozen inside this call
        network = topic_network(b, network)
    return A.verify(network, _chart_key(c))


def _birth_time(b, c, level):
    ut = dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz)
    s = engine.sensitivity(ut, b.lat, b.lon, c["bodies"]["Mo"]["lon"], window_min=30)
    keep = ("ascendant sign (D1)", "D9 lagna", "D10 lagna", "Moon nakshatra (dasha lord)")
    flags = [] if b.time_source else ["birth-time source not stated: treat AD edges as approximate and PD rows as "
                                      "reference only (timing.md §0 step 0)"]
    if level == "pd":
        flags.append("PD rows need a documented birth time within about 5 minutes (timing.md §0 step 0)")
    near = {k: min(x for x in s[k].values() if x is not None) for k in keep if any(s[k].values())}
    flags += [f"{k} changes {m} min away: values that depend on it are birth-time sensitive"
              for k, m in near.items() if m <= 30]
    return {"time_source": b.time_source, "minutes_to_change": {k: s[k] for k in keep}, "flags": flags}


@_calc
def activation(b: BirthInput, o: Options = DEFAULTS, network="career", level: str = "ad") -> dict:
    """Dasha activation table (timing.md §0 steps 3-7): for each AD (or PD) segment from `on` over `months`, the period
    lords' natal roles from chart_facts, and the slow contacts, Ju/Sa sign stays (with BAV/SAV) and stations inside it
    that touch a period lord or the frozen network. Facts only."""
    from .calc import activation as A
    if level not in ("ad", "pd"):
        raise ValueError("level must be ad or pd")
    c = _compute(b, o, extras=False)
    net = _network(b, c, network)
    F = _facts_ids(c)
    t0 = dt.datetime.fromisoformat(c["meta"]["transit_date"] + "T12:00") - dt.timedelta(hours=b.tz)
    t1 = t0 + dt.timedelta(days=30.44 * o.months)
    start, end = c["meta"]["transit_date"], (t1 + dt.timedelta(hours=b.tz)).date().isoformat()
    natal = {n: v["lon"] for n, v in c["bodies"].items() if n not in ("Ra", "Ke")}
    T = engine.positions(engine.jd_of(t0), o.node)
    ingr = engine.ingresses(t0, o.months, o.node, b.tz)
    stays = engine.transit_sign_aspects(t0, o.months, ingr, T, int(c["bodies"]["Asc"]["lon"] // 30),
                                        int(c["bodies"]["Mo"]["lon"] // 30), b.tz)
    from .calc import transit as TR
    stations = _stations(t0, t1, b.tz, o.node)
    lon_of = lambda p, d: engine.positions(engine.jd_of(dt.datetime.fromisoformat(d) + dt.timedelta(hours=12 - b.tz)),
                                           o.node)[p]["lon"]
    episodes = TR.station_episodes(stations, lon_of, natal)
    rows = A.table(F, net, c["vimshottari"], start, end, level, engine.contacts(t0, o.months, natal, o.node, b.tz),
                   stays, stations, strength.ashtakavarga(c), episodes)
    return _with_meta(c, {
        "from": start, "to": end, "level": level, "network": net, "segments": rows,
        "birth_time": _birth_time(b, c, level),
        "rules": {"date_boundary": "segments are start <= date < end (local dates at the birth UTC offset): a contact "
                                   "on a boundary date belongs to the segment that starts that day",
                  "stays": "a Ju/Sa sign stay is listed in every segment it overlaps; 'touches' = a period lord or "
                           "network planet natally in a sign the stay occupies or aspects (" +
                           engine.TRANSIT_ASPECTS_NOTE + ")",
                  "contacts": "exact Ju/Sa conjunctions and oppositions and node conjunctions with the natal positions "
                              "of period lords and network planets (engine contacts())",
                  "stations": "Mercury-Saturn stations in the segment, with period lords or network planets natally in "
                              "the station sign (sign level); 'station_episodes' = a retrograde loop whose station "
                              "falls within transit.ORBS of a period lord's or network planet's natal position "
                              "(transit.station_episodes(); placed by its first station date)"},
        "sources": {"method": "timing.md §0 steps 3-7; HJH2 p21 (dasha and bhukti lords both significators or one); "
                              "PVR §25.2 (a transit acts through what the planet rules natally)",
                    "lordships": "chart_facts.facts_json (derived_facts/1)", "bindus": "strength.ashtakavarga()"},
        "note": "Calculated facts and rule lookups only; which segment matters, and how, is the reader's judgement."})


def _stations(t0, t1, tz, node):
    out = []
    for st in engine.sky(t0, t1, node, tz)["stations"]:
        t = dt.datetime.fromisoformat(st["date"] + "T12:00") - dt.timedelta(hours=tz)
        out.append(st | {"sign": engine.SIGNS[int(engine.positions(engine.jd_of(t), node)[st["planet"]]["lon"] // 30)]})
    return out


RETRO_WINDOW_MONTHS = 3


@_calc
def retrospective(b: BirthInput, events: list, networks: Optional[dict] = None, o: Options = DEFAULTS) -> dict:
    """Calibration (consultation-reasoning §8): for each caller-supplied {category, month: YYYY-MM} event, the running
    periods and the slow contacts and stations within ±3 months, against the category's frozen network, with a
    'consistent with N of M' line. Local only; nothing is stored; networks are verified, never changed."""
    from .calc import activation as A
    if REMOTE:
        raise PermissionError("retrospective calibration handles personal event data: local use only, not for remote "
                              "clients")
    if not isinstance(events, list) or not 1 <= len(events) <= 12:
        raise ValueError("events: a list of 1 to 12 {category, month} items")
    c = _compute(b, o, extras=False)
    key, today = _chart_key(c), dt.date.today().isoformat()[:7]
    networks = dict(networks or {})
    evs = []
    for e in events:
        cat, ym = str(e.get("category", "")), str(e.get("month", ""))
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", ym) or not str(b.date)[:7] <= ym <= today:
            raise ValueError(f"event month {ym!r}: YYYY-MM between the birth month and this month")
        evs.append({"category": cat, "month": ym})
    for cat in dict.fromkeys(e["category"] for e in evs):   # every network is frozen before any event is examined
        networks[cat] = A.verify(networks[cat], key) if cat in networks else _network(b, c, cat)
    natal = {n: v["lon"] for n, v in c["bodies"].items() if n not in ("Ra", "Ke")}
    rows = []
    for e in evs:
        y, m = int(e["month"][:4]), int(e["month"][5:7]) - RETRO_WINDOW_MONTHS
        t0 = dt.datetime(y + (m - 1) // 12, (m - 1) % 12 + 1, 1) - dt.timedelta(hours=b.tz)
        months = 2 * RETRO_WINDOW_MONTHS + 1
        rows.append(A.event_row(e, networks[e["category"]], c["vimshottari"],
                                engine.contacts(t0, months, natal, o.node, b.tz),
                                _stations(t0, t0 + dt.timedelta(days=30.44 * months), b.tz, o.node)))
    n = sum(r["consistent"] for r in rows)
    return _with_meta(c, {
        "events": rows, "summary": f"consistent with {n} of {len(rows)}",
        "analysis": {"window": f"each event month ± {RETRO_WINDOW_MONTHS} months for contacts and stations",
                     "rule": "an event counts as consistent when an MD or AD lord running at any time in its month is "
                             "in that category's frozen network; contacts and stations are shown, not counted",
                     "networks": {k: v["hash"] for k, v in networks.items()},
                     "assumptions": [f"Vimshottari, {c['meta']['dasha_year_days']}-day year", f"{o.node} nodes",
                                     c["meta"]["ayanamsa"], "month precision: an event is placed anywhere in its month",
                                     "networks frozen before any event was examined; never changed afterwards"],
                     "stored": "nothing: the events exist only in this response"},
        "not_proof": "Calibration is not proof: a period lord in a network is common by chance (PRED-F2), and a match "
                     "says only that the method is consistent with the dates given. Do not change the method, the "
                     "network or the dasha variant after seeing these rows (consultation-reasoning §8)."})


@_calc
def transits(b: BirthInput, o: Options = DEFAULTS) -> dict:
    c = _compute(b, o)
    return _with_meta(c, {k: c[k] for k in ("transits", "ingresses", "slow_contacts")} | {"on": c["meta"]["transit_date"]})


@_calc
def shadbala(b: BirthInput, o: Options = DEFAULTS) -> dict:
    c = _compute(b, o, extras=False)
    ut = dt.datetime.fromisoformat(f"{b.date}T{b.time}") - dt.timedelta(hours=b.tz)
    return _with_meta(c, strength.shadbala(c, ut, b.lat, b.lon, b.tz))


@_calc
def ashtakavarga(b: BirthInput, o: Options = DEFAULTS) -> dict:
    c = _compute(b, o, extras=False)
    return _with_meta(c, strength.ashtakavarga(c))


@_calc
def jaimini_factors(b: BirthInput, o: Options = DEFAULTS) -> dict:
    c = _compute(b, o, extras=False)
    return _with_meta(c, jaimini.jaimini(c))


@_calc
def sky(start, end, tz=0.0, node: str = "mean") -> dict:
    """Retrograde stations and sign changes between two dates — no birth data (council 6, P2-1)."""
    a, b, tz = dt.date.fromisoformat(str(start)), dt.date.fromisoformat(str(end)), utc_offset_hours(tz)
    if not (a < b and (b - a).days <= 3 * 366 and -14 <= tz <= 14 and node in ("mean", "true")):
        raise ValueError("need start < end, at most 3 years apart, UTC offset -14..14, node mean or true")
    t0 = dt.datetime.combine(a, dt.time()) - dt.timedelta(hours=tz)
    t1 = dt.datetime.combine(b, dt.time(23, 59)) - dt.timedelta(hours=tz)
    return engine.sky(t0, t1, node, tz) | {"meta": {"from": a.isoformat(), "to": b.isoformat(), "utc_offset": tz,
        "nodes": node, "zodiac": f"sidereal {engine.ayanamsa_name()}", "ayanamsa": engine.ayanamsa_name(),
        **engine.ephemeris_info(engine.jd_of(t0)), "engine": f"astro {engine.ENGINE_VERSION}",
        "note": "sky facts only: the same for everyone; they say nothing about a person without a chart"}}


@_calc
def birth_time_sensitivity(b: BirthInput, o: Options = DEFAULTS, span_min: int = 15) -> dict:
    a, kw = _args(b, o)
    g = sensitivity.grid(*a, on=kw["on"], year=o.year, span_min=span_min)
    return _with_meta(_compute(b, o, extras=False), g | {"table_markdown": sensitivity.render(g)})


def _run_skill_script(name, *args):
    s = config.load()
    if not s.skill_dir:
        raise FileNotFoundError("skill folder not found (astro setup)")
    env = dict(os.environ)
    if s.knowledge_dir:
        env.setdefault("ASTRO_KG", os.path.join(s.knowledge_dir, "graphify-out", "graph.json"))
        env.setdefault("ASTRO_LIBRARY_DB", os.path.join(s.knowledge_dir, "index", "library.sqlite"))
    r = subprocess.run([sys.executable, os.path.join(s.skill_dir, "scripts", name), *args], capture_output=True,
                       text=True, env=env, timeout=120)
    if r.returncode != 0:   # pass the script's own one-line message, never a traceback or a local path
        msg = r.stderr.strip()
        if not msg or "Traceback" in msg:
            msg = f"{name} failed (exit {r.returncode}); run it locally to see why"
        raise ValueError(re.sub(r"(?:~|/)[^\s'\"]*/[^\s'\"]*", "<path>", msg))
    return r.stdout.strip()


def _library_gate():
    """Excerpts of the user's own books are for the user: not served to other people over a network unless the owner
    explicitly opts in (share_library_remotely = true)."""
    if REMOTE and not config.load().share_library_remotely:
        raise PermissionError("library lookup is not served to remote clients (set share_library_remotely = true "
                              "only if you are entitled to share these excerpts)")


def search_sources(query: str, sources: Optional[str] = None) -> str:
    """Full-text search of the user's own local library (page-cited). Needs a configured knowledge folder."""
    _library_gate()
    if not config.load().knowledge_dir:
        return "No local library configured — add your own books with `astro add-book` (see docs/ADD-A-BOOK.md)."
    return _run_skill_script("search.py", *(["--src", sources] if sources else []), "--", query[:300])


def rule_sources(rule: str) -> str:
    """Which books support or dispute a rule (knowledge graph), with pages and tiers."""
    _library_gate()
    if not config.load().knowledge_dir:
        return "No knowledge graph configured — retrieval is unavailable; reason from the skill's references."
    return _run_skill_script("kg.py", "sources", "--", rule[:300])


def skill_file(rel: str) -> str:
    """Read one file of the skill (SKILL.md, references/*.md, assets/report/*) — nothing outside the skill folder."""
    s = config.load()
    path = _inside(os.path.join(s.skill_dir, rel), s.skill_dir)
    if "/data/lal-kitab/" in path.replace(os.sep, "/").lower():   # book-derived KB: same rule as library excerpts (H-10); lower(): case-insensitive disks
        _library_gate()
    if not re.search(r"\.(md|json|css|j2)$", path):
        raise PermissionError("only skill documents can be read")
    return open(path, encoding="utf-8").read()


def analyze_question(question: str) -> dict:
    q = question.lower()
    topics = [t for t, rx in TOPICS.items() if re.search(rx, q)]
    timing = bool(re.search(ROUTING.TIMING_RX, q))
    return {"question": question, "topics": topics or ["open activation — see question-trees.md §8"],
            "timing_question": timing, "load": ROUTING.load(topics, timing)}


@_calc
def consultation_context(question: str, b: BirthInput, o: Options = DEFAULTS) -> dict:
    """Everything an AI client needs to answer like the skill: the routed method files, the calculated facts with
    provenance, and the birth-time sensitivity classes. The client does the reasoning."""
    c = calculate_chart(b, o)
    on = c["meta"]["transit_date"]
    running = next(([md["lord"], ad["lord"], pd["lord"]] for md in c["vimshottari"] for ad in md["sub"]
                    for pd in ad["sub"] if pd["start"] <= on < pd["end"]), None)
    facts = {"meta": c["meta"], "bodies": {k: {x: v[x] for x in ("sign", "deg", "nakshatra", "pada", "retro")}
                                           for k, v in c["bodies"].items()},
             "d9": {k: v["vargas"]["D9"] for k, v in c["bodies"].items()},
             "d10": {k: v["vargas"]["D10"] for k, v in c["bodies"].items()},
             "running_periods": running, "transits": c["transits"], "slow_contacts": c["slow_contacts"],
             "ingresses": c["ingresses"],
             "shadbala_rupas": {p: v["total_rupas"] for p, v in c["shadbala"]["planets"].items()},
             "sav_by_house": c["ashtakavarga"]["sav_by_house"], "jaimini": {k: c["jaimini"][k] for k in
                                                                             ("arudha_lagna", "upapada", "karakamsa")},
             "sensitivity_classes": c["sensitivity_grid"]["classes"],
             "transit_sign_aspects": c["transit_sign_aspects"], "transit_aspects_note": c["meta"]["transit_aspects"]}
    return {"analysis": analyze_question(question), "facts": facts, "derived_facts": _derived_facts(c),
            "derived_fact_ids": _derived_facts(c, ids=True)}


def _derived_facts(c, ids=False):
    """The skill's chart_facts.py output (houses, lordships, graha drishti, combustion, D9/D10, dispositors, PD XV tests,
    Lal Kitab flags) — one implementation, owned by the skill with its conventions named — so clients without a shell
    get the same derived facts. ids=True: the same facts as stable ids (chart_facts.facts_json, schemas/derived_facts.schema.json)."""
    path = os.path.join(config.load().skill_dir, "scripts", "chart_facts.py")
    if not os.path.exists(path):
        return "unavailable: the skill's scripts/chart_facts.py was not found"
    spec = importlib.util.spec_from_file_location("chart_facts", path)
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    chart = engine.chart_facts_input(c)
    return cf.facts_json(chart) if ids else cf.facts(chart)


# Facts that always need the birth time (static fallback when no birth input is given): lagna, houses, house
# placements and lordships, and every yoga (most are lagna-based). With a birth input the time-varying facts are
# measured instead (time_varying_facts), which also catches degrees and anything else that moves within the day.
TIME_BOUND_REF = re.compile(r"^F\.(asc|H\d+)\.|^F\.\w+\.(house|dispositor_house|owns|deg)$|^F\.yoga\.|^F\.moon\.elongation")
UNKNOWN_TIME = re.compile(r"^\s*(unknown|not known|n/?a|none|no (birth )?time)\s*($|[;,(:.-])"
                          r"|\b(birth )?time\s+(is\s+)?(unknown|not known)\b|\bno birth time\b", re.I)   # council RC-04
DAY_SAMPLES = ("00:00:00", "03:00:00", "06:00:00", "09:00:00", "12:00:00", "15:00:00", "18:00:00", "21:00:00", "23:59:00")


def time_unknown(model: dict, b: Optional["BirthInput"] = None) -> bool:
    src = (b.time_source if b else None) or (model.get("birth") or {}).get("time_source") or ""
    rel = str((model.get("birth") or {}).get("time_reliability") or "")
    return bool(UNKNOWN_TIME.search(src) or UNKNOWN_TIME.search(rel))


@_calc
def time_varying_facts(b: "BirthInput", o: "Options") -> set:
    """Fact ids whose value changes at some clock time of the birth date (council RC-01): with an unknown time none of
    them may be cited. Computed, not listed, so new lagna-based facts are covered automatically."""
    seen = {}
    for t in DAY_SAMPLES:
        f = _derived_facts(_compute(b.model_copy(update={"time": t}), o), ids=True)
        f = f.get("facts", {}) if isinstance(f, dict) else {}
        for k in set(seen) | set(f):
            seen.setdefault(k, set()).add(json.dumps(f.get(k), sort_keys=True, default=str))
    return {k for k, v in seen.items() if len(v) > 1}


def unknown_time_problems(model: dict, b: Optional["BirthInput"] = None, varying: Optional[set] = None,
                          windows: Optional[list] = None) -> list:
    """ASTRO-REPORT-SPEC item 26 enforced in the engine, not only in SKILL.md (#48): with an unknown birth time only a
    compact report is allowed, with no time-dependent facts (fact_refs), no event_refs and no dated windows anywhere."""
    if not time_unknown(model, b):
        return []
    errs = []
    if model.get("report_type") != "compact":
        errs.append(f"birth time unknown: only a compact report is allowed (got {model.get('report_type')!r})")
    cited = {x for s in model.get("sections", []) for u in s.get("units", []) for x in u.get("fact_refs", [])}
    refs = sorted(x for x in cited if TIME_BOUND_REF.search(x) or (varying is not None and x in varying))
    if refs:
        errs.append(f"birth time unknown: facts that depend on the birth time cannot be cited: {', '.join(refs[:8])}")
    kps = (model.get("summary") or {}).get("key_points", [])
    if model.get("timeline") or any(k.get("window") or k.get("event_refs") for k in kps) or windows:
        errs.append("birth time unknown: no dated windows, event_refs or dasha timeline (dasha dates depend on the "
                    "birth time)")
    return errs


@_calc   # audit F-04: the grounding recompute runs under the requested ayanamsa and the process lock
def create_report(model: dict, name: str = "report", b: Optional[BirthInput] = None, o: Options = DEFAULTS) -> dict:
    """Validate and render a Structured Report Model (assets/report/report.schema.json) to HTML (+PDF). Dates are checked
    against facts recomputed here from the birth input `b` (never client-supplied, never printed); a dated model needs it."""
    s = config.load()
    if not SAFE_NAME.match(name):
        raise ValueError("report name: letters, digits, dot, dash, underscore; ≤ 64 characters")
    if refusal := config.folder_refusal(s.reports_dir, s.skill_dir):
        return {"ok": False, "errors": [refusal]}        # V-FOLDER: nothing is written, not even the folder
    spec = importlib.util.spec_from_file_location("render_report", os.path.join(s.skill_dir, "scripts", "render_report.py"))
    rr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr)
    schema = json.load(open(os.path.join(s.skill_dir, "assets", "report", "report.schema.json")))
    if time_unknown(model, b):          # #48: refused before anything is rendered; dated windows anywhere count (RC-04)
        try:
            wins = rr._windows(model) if model.get("summary") else []
        except Exception:               # a malformed model is report_checks' job; the rule must still hold
            wins = []
        if problems := unknown_time_problems(model, b, time_varying_facts(b, o) if b else None, wins):
            return {"ok": False, "errors": problems}
    if b is None:
        if model.get("timeline") or any(k.get("window") or k.get("event_refs")             # RC-09
                                         for k in (model.get("summary") or {}).get("key_points", [])):
            return {"ok": False, "errors": ["grounding needs the birth input: pass the birth details (not printed) so the dates can be checked"]}
        errs, warns = rr.report_checks(model, schema)
    else:
        c = _compute(b, o)
        c["meta"]["months"] = o.months      # calc.json carries no horizon; without it later windows fall to "unverified"
        ids = _derived_facts(c, ids=True)
        if not isinstance(ids, dict) and any(u.get("fact_refs") for x in model.get("sections", []) for u in x.get("units", [])):
            return {"ok": False, "errors": [f"fact_refs cannot be checked: derived facts {ids}"]}     # fail closed
        errs, warns = rr.report_checks(model, schema, c, ids if isinstance(ids, dict) else None)
    if errs:
        return {"ok": False, "errors": errs}
    os.makedirs(s.reports_dir, mode=0o700, exist_ok=True)      # reports hold birth details: owner-only when created
    try:
        html, pdf = rr.render(model, s.reports_dir, name)
    except Exception as e:   # e.g. jinja2 or the PDF libraries missing: tell the client why (not a generic tool error)
        return {"ok": False, "errors": [f"report could not be rendered: {type(e).__name__}: {e}"]}
    for f in (html, pdf):
        if f:
            os.chmod(f, 0o600)      # the files hold birth details too, not only the folder (council R4)
    return {"ok": True, "warnings": warns, "html": html, "pdf": pdf}


def _inside(path, root):
    """Resolve `path` and refuse anything outside `root` (no traversal, no symlink escapes)."""
    if not root:
        raise FileNotFoundError("folder not configured (astro setup)")
    rp, rr = os.path.realpath(path), os.path.realpath(root)
    if os.path.commonpath([rp, rr]) != rr:
        raise PermissionError("path outside the allowed folder")
    return rp


# ---- consultation report (owner specification 2026-11-01): intake -> engine pack -> checked HTML/PDF/DOCX ----------
CONSULT_MONTHS = 60          # transit events for the 3-5 year overview


def _skill_mod(name):
    s = config.load()
    path = os.path.join(s.skill_dir or "", "scripts", f"{name}.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(f"skill_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _consult_birth(cm, intake):
    """BirthInput from an intake, resolving a place name offline when no coordinates are given. Errors are messages."""
    bi = cm.birth_input(intake)
    if bi.get("lat") is None or bi.get("lon") is None:
        place = intake["birth"]["place"]
        try:
            r = find_place(place)
        except FileNotFoundError as e:
            raise ValueError(f"birth.place '{place}': no coordinates given and {e}") from None
        hits = r.get("matches") or []
        if not hits:
            raise ValueError(f"birth.place '{place}': unknown place; check the spelling or give lat, lon and the time zone")
        if r.get("ambiguous"):
            names = "; ".join(f"{h.get('name')}, {h.get('admin1', '')} {h.get('country', '')}".strip() for h in hits[:5])
            raise ValueError(f"birth.place '{place}' matches several places ({names}); give the coordinates")
        h = hits[0]
        bi |= {"lat": h["lat"], "lon": h["lon"]}
        if not bi.get("tz") and not bi.get("zone") and h.get("zone"):
            bi["zone"] = h["zone"]
    try:
        return BirthInput(**bi)
    except Exception as e:          # pydantic: one readable line per problem
        errs = getattr(e, "errors", lambda: [])()
        msg = "; ".join(f"birth.{'.'.join(map(str, x.get('loc', [])))}: {x.get('msg')}" for x in errs) or str(e)
        raise ValueError(msg) from None


@_calc
def consultation_pack(intake: dict, o: Options = DEFAULTS, verification: Optional[dict] = None) -> dict:
    """Everything a consultation report prints, computed here from the intake: never typed by the writer.
    Returns {"ok": True, "pack": ...} or {"ok": False, "errors": [...]} with field-named messages."""
    cm = _skill_mod("consultation")
    if cm is None:
        return {"ok": False, "errors": ["the skill's scripts/consultation.py was not found (astro setup)"]}
    if errs := cm.validate_intake(intake):
        return {"ok": False, "errors": errs}
    if o.ayanamsa != "lahiri":
        return {"ok": False, "errors": [f"the consultation report uses the Lahiri ayanamsa only (got {o.ayanamsa})"]}
    try:
        b = _consult_birth(cm, intake)
    except ValueError as e:
        return {"ok": False, "errors": [str(e)]}
    o = o.model_copy(update={"on": dt.date.fromisoformat(intake["consultation"]["report_date"]), "months": CONSULT_MONTHS})
    c = _compute(b, o, full=True)
    samples, sample_ids, lk = [], [], _skill_mod("lal_kitab")
    unknown = intake["birth"]["time_reliability"] == "unknown"
    for t in cm.sample_times(intake):      # the uncertain birth time, measured: every id at every sample time
        d, clock = (t.split("T") if "T" in t else (str(b.date), t))
        cs = _compute(b.model_copy(update={"date": dt.date.fromisoformat(d), "time": clock}), o, full=True)
        fs = _derived_facts(cs, ids=True)
        fs = fs.get("facts", {}) if isinstance(fs, dict) else {}
        samples.append(cs)
        sample_ids.append(fs | cm.chart_ids(cs, fs, None if unknown else lk))
    eng = {"chart": c, "derived_text": _derived_facts(c), "derived_ids": _derived_facts(c, ids=True),
           "gochara": gochara(b, o), "samples": samples, "sample_ids": sample_ids, "months": CONSULT_MONTHS,
           "varying_facts": sorted(time_varying_facts(b, o)) if unknown else [], "verification": verification}
    if not isinstance(eng["derived_ids"], dict):
        return {"ok": False, "errors": [f"derived facts unavailable: {eng['derived_ids']}"]}
    rr = _skill_mod("render_report")
    pack = cm.build_pack(intake, eng, lk, _skill_mod("varshaphal"), rr)
    return {"ok": True, "pack": pack}


@_calc
def create_consultation_report(intake: dict, model: dict, name: Optional[str] = None, o: Options = DEFAULTS,
                               verification: Optional[dict] = None, formats=("html", "pdf", "docx"),
                               out_dir: Optional[str] = None) -> dict:
    """Check the interpretation model against the pack recomputed from the intake, then write HTML, PDF and DOCX to the
    reports folder (owner-only files). Refused with field-named errors when anything is missing or unsupported."""
    s = config.load()
    out_dir = os.path.expanduser(out_dir) if out_dir else s.reports_dir      # out_dir: CLI and Python only, never MCP
    if refusal := config.folder_refusal(out_dir, s.skill_dir):
        return {"ok": False, "errors": [refusal]}
    r = consultation_pack(intake, o, verification)
    if not r["ok"]:
        return r
    cm, rr = _skill_mod("consultation"), _skill_mod("render_report")
    if name is None:
        first = re.sub(r"[^a-z0-9]", "", intake["client"]["full_name"].split()[0].lower()) or "client"
        name = f"{first}-consultation-{intake['consultation']['report_date'].replace('-', '')}"
    if not SAFE_NAME.match(name):
        raise ValueError("report name: letters, digits, dot, dash, underscore; ≤ 64 characters")
    schema = json.load(open(os.path.join(s.skill_dir, "assets", "report", "report.schema.json")))
    try:
        out = cm.report(r["pack"], model, out_dir, name, rr, schema, formats)
    except Exception as e:      # rendering libraries missing or broken: say why, never a traceback
        return {"ok": False, "errors": [f"report could not be rendered: {type(e).__name__}: {e}"]}
    return out


def consultation_brief(intake: dict, o: Options = DEFAULTS) -> dict:
    """The writer's brief for a consultation report: every fact, id and dated event the interpretation may cite."""
    r = consultation_pack(intake, o)
    if not r["ok"]:
        return r
    return {"ok": True, "brief": _skill_mod("consultation").brief(r["pack"]),
            "model_schema": "skill://assets/report/consultation-model.schema.json",
            "method": "skill://references/consultation-report.md"}
