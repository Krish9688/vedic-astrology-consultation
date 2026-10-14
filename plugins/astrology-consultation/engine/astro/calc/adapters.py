# Engine output → ChartFacts. One function per engine; each keeps the engine's conventions in `provenance`
# and never "corrects" a value — differences are for compare.py to report.
from __future__ import annotations

import re

from .schema import Birth, Body, ChartFacts, Period, Provenance, Transits, nak_of, sign_of


def _body(lon, retro=None, vargas=None):
    n, p = nak_of(lon)
    return Body(lon=round(lon % 360, 6), sign=sign_of(lon), deg=round(lon % 30, 6), nakshatra=n, pada=p,
                retro=retro, vargas=vargas or {})


def from_local(calc: dict, time_source: str | None = None) -> ChartFacts:
    """astro.calc.engine.compute() / calc.json → ChartFacts (strength, Jaimini and sensitivity when present)."""
    m = calc["meta"]
    d, t, off = re.match(r"(\S+) (\S+) UTC([+-][\d.]+)", m["birth_local"]).groups()
    birth = Birth(date=d, time=t, utc_offset_hours=float(off), lat=m["lat"], lon=m["lon"], time_source=time_source)
    prov = Provenance(engine="local-swisseph", engine_version=m["engine"], network="local",
                      ayanamsa_deg=float(re.search(r"[\d.]+", m["ayanamsa"]).group()), nodes=m["nodes"],
                      dasha_year_days=m["dasha_year_days"], ephemeris=m.get("ephemeris"),
                      computed_at=m.get("computed_at_utc"), house_system="whole sign; Sripati bhavas")
    bodies = {n: _body(b["lon"], b["retro"] if n not in ("Asc",) else None, b["vargas"]) for n, b in calc["bodies"].items()}

    def per(rows):
        return [Period(lord=r["lord"], start=r["start"], end=r["end"], sub=per(r.get("sub", []))) for r in rows]

    sb = calc.get("shadbala", {}).get("planets", {})
    tr = calc.get("transits")
    return ChartFacts(birth=birth, provenance=prov, bodies=bodies, vimshottari=per(calc["vimshottari"]),
                      transits=Transits(on=m["transit_date"], bodies=tr) if tr else None,
                      ingresses=calc.get("ingresses", []), bhavas=calc.get("bhavas", []),
                      shadbala_rupas={p: v["total_rupas"] for p, v in sb.items()},
                      shadbala_components={p: {**v["virupas"], **{k: v["detail"][k] for k in COMPONENT_DETAIL}}
                                           for p, v in sb.items()},
                      ashtakavarga=calc.get("ashtakavarga", {}).get("bav", {}),
                      arudha=calc.get("jaimini", {}).get("arudha", {}), jaimini=calc.get("jaimini", {}),
                      sensitivity={k: calc[k] for k in ("birth_time_sensitivity_minutes", "sensitivity_grid") if k in calc})


COMPONENT_DETAIL = ("saptavargaja", "ojayugma", "kendradi", "drekkana", "tribhaga", "ayana", "abda_masa_vara_hora")
VA_COMPONENT = {"sthana": "PlanetSthanaBala", "dig": "PlanetDigBala", "kala": "PlanetKalaBala",
                "cheshta": "PlanetChestaBala", "naisargika": "PlanetNaisargikaBala",
                "saptavargaja": "PlanetSaptavargajaBala", "ojayugma": "PlanetOjayugmarasyamsaBala",
                "kendradi": "PlanetKendraBala", "drekkana": "PlanetDrekkanaBala", "tribhaga": "PlanetTribhagaBala",
                "ayana": "PlanetAyanaBala"}
VA_AMVH = ("PlanetAbdaBala", "PlanetMasaBala", "PlanetVaraBala", "PlanetHoraBala")
