# Normalized chart facts: the one structure every calculation engine is translated into (via adapters.py),
# so the consultation skill never reads an engine's own JSON. Calculation only — nothing here interprets.
# JSON Schema export: .venv/bin/python tools/calc/schema.py > astrology-prediction/assets/chart_facts.schema.json
from __future__ import annotations

import datetime as dt
import json
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

SIGNS = "Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius Capricorn Aquarius Pisces".split()
NAKS = ("Ashwini Bharani Krittika Rohini Mrigashira Ardra Punarvasu Pushya Ashlesha Magha PurvaPhalguni UttaraPhalguni "
        "Hasta Chitra Swati Vishakha Anuradha Jyeshtha Mula PurvaAshadha UttaraAshadha Shravana Dhanishtha Shatabhisha "
        "PurvaBhadrapada UttaraBhadrapada Revati").split()
BODIES = ("Asc", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
Sign = Literal[tuple(SIGNS)]
SCHEMA_VERSION = "1.0"


def sign_of(lon: float) -> str:
    return SIGNS[int((lon % 360) / 30 + 1e-9) % 12]


def nak_of(lon: float) -> tuple[str, int]:
    lon %= 360
    return NAKS[int(lon / (40 / 3) + 1e-9) % 27], int(lon / (10 / 3) + 1e-9) % 4 + 1


class Birth(BaseModel):
    date: dt.date
    time: dt.time
    utc_offset_hours: float = Field(ge=-14, le=14)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    time_source: Optional[str] = None          # e.g. "birth certificate", "family memory"

    def utc(self) -> dt.datetime:
        return dt.datetime.combine(self.date, self.time) - dt.timedelta(hours=self.utc_offset_hours)


class Provenance(BaseModel):
    engine: str                                  # "local-swisseph" | "vedastro"
    engine_version: Optional[str] = None
    network: Literal["local", "cloud:api.vedastro.org"]
    ayanamsa: str = "Lahiri"
    ayanamsa_deg: Optional[float] = None
    nodes: Literal["mean", "true", "unknown"] = "unknown"
    dasha_year_days: Optional[float] = None      # 365.256363 sidereal; VedAstro uses 360
    house_system: str = "whole sign"
    varga_notes: dict[str, str] = {}             # e.g. {"D7": "VedAstro non-Parashari variant"}
    ephemeris: Optional[str] = None              # "Swiss Ephemeris data files" | "Moshier …" | engine's own
    computed_at: Optional[str] = None            # ISO-8601 UTC
    settings: dict[str, str] = {}                # anything else that changes results (method names, conventions)


class Body(BaseModel):
    lon: float = Field(ge=0, lt=360)             # sidereal longitude
    sign: Sign
    deg: float = Field(ge=0, lt=30)
    nakshatra: str
    pada: int = Field(ge=1, le=4)
    retro: Optional[bool] = None
    vargas: dict[str, Sign] = {}                 # "D9" -> sign

    @model_validator(mode="after")
    def consistent(self):
        # engines round degrees differently; sign/nakshatra must still follow from the longitude
        if sign_of(self.lon) != self.sign:
            raise ValueError(f"sign {self.sign} does not match longitude {self.lon}")
        if abs((self.lon % 30) - self.deg) > 0.01:
            raise ValueError(f"deg {self.deg} does not match longitude {self.lon}")
        n, p = nak_of(self.lon)
        if (n, p) != (self.nakshatra, self.pada):
            raise ValueError(f"nakshatra {self.nakshatra}-{self.pada} does not match longitude {self.lon} ({n}-{p})")
        return self


class Period(BaseModel):
    lord: Literal["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    start: dt.date
    end: dt.date
    sub: list["Period"] = []
    clipped: bool = False                        # the engine cut this period at a requested range edge


class TransitBody(BaseModel):
    sign: Sign
    deg: float
    retro: Optional[bool] = None
    house_from_lagna: int = Field(ge=1, le=12)
    house_from_moon: int = Field(ge=1, le=12)


class Transits(BaseModel):
    on: dt.date
    bodies: dict[str, TransitBody]


class ChartFacts(BaseModel):
    schema_version: str = SCHEMA_VERSION
    birth: Birth
    provenance: Provenance
    bodies: dict[str, Body]
    vimshottari: list[Period] = []
    transits: Optional[Transits] = None
    ingresses: list[dict] = []                   # {"planet","date","from","to"}
    shadbala_rupas: dict[str, float] = {}        # Sun..Saturn only; engines differ (see docs/CALCULATION-ENGINES.md)
    shadbala_components: dict[str, dict[str, float]] = {}   # planet -> component -> virupas
    ashtakavarga: dict[str, list[int]] = {}      # planet -> 12 bindus by sign from Aries
    bhavas: list[dict] = []                      # {"house", "start", "middle", "end"} (degrees)
    arudha: dict[str, str] = {}                  # "A1".."A12" -> sign
    jaimini: dict = {}
    sensitivity: dict = {}                       # birth-time sensitivity (minutes, grid, classes)
    flags: list[str] = []

    @model_validator(mode="after")
    def checks(self):
        missing = [b for b in BODIES if b not in self.bodies]
        if missing:
            raise ValueError(f"missing bodies: {missing}")
        ra, ke = self.bodies["Ra"].lon, self.bodies["Ke"].lon
        if abs(((ra - ke) % 360) - 180) > 0.01:
            raise ValueError("Ketu must be exactly opposite Rahu")
        for a, b in zip(self.vimshottari, self.vimshottari[1:]):
            if (b.start - a.end).days > 1:
                raise ValueError(f"gap between {a.lord} and {b.lord} mahadashas")
        return self


class Agreement(BaseModel):
    kind: str            # position | sign | nakshatra | pada | varga | dasha | shadbala | methodology
    key: str             # e.g. "Mo", "Mo:D9", "MD Sa start"
    a: Optional[str] = None
    b: Optional[str] = None
    delta: Optional[str] = None
    verdict: Literal["match", "within tolerance", "methodology", "configuration", "implementation", "unresolved",
                     "not comparable"]
    note: str = ""


class ValidatedChartFacts(ChartFacts):
    """ChartFacts from the preferred (local) engine plus the cross-check against a second engine."""
    cross_check_engine: Optional[str] = None
    agreements: list[Agreement] = []

    def disagreements(self) -> list[Agreement]:
        return [x for x in self.agreements if x.verdict == "unresolved"]


if __name__ == "__main__":
    print(json.dumps(ValidatedChartFacts.model_json_schema(), indent=1))
