# Engine output → ChartFacts. One function per engine; each keeps the engine's conventions in `provenance`
# and never "corrects" a value — differences are for compare.py to report.
from __future__ import annotations

import datetime as dt
import json
import re

from .schema import NAKS, SIGNS, Birth, Body, ChartFacts, Period, Provenance, Transits, nak_of, sign_of

VA_NAME = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
           "Rahu": "Ra", "Ketu": "Ke"}
# VedAstro's nakshatra spellings → index (first letters are enough to disambiguate; unknown → None)
VA_NAK = {"ashw": 0, "bhar": 1, "krit": 2, "krith": 2, "rohi": 3, "mrig": 4, "arid": 5, "ardr": 5, "puna": 6,
          "push": 7, "asle": 8, "ashl": 8, "makh": 9, "magh": 9, "pubb": 10, "poorvaph": 10, "purvaph": 10,
          "utth": 11, "uttaraph": 11, "hast": 12, "chit": 13, "swat": 14, "vish": 15, "anur": 16, "jyes": 17,
          "jyesh": 17, "mool": 18, "mula": 18, "poorvas": 19, "purvas": 19, "uttaras": 20, "srav": 21, "shra": 21,
          "dhan": 22, "sata": 23, "shat": 23, "poorvab": 24, "purvab": 24, "uttarab": 25, "reva": 26}
VA_VARGA = {"D1": "PlanetRasiD1Sign", "D2": "PlanetHoraD2Signs", "D3": "PlanetDrekkanaD3Sign",
            "D4": "PlanetChaturthamshaD4Sign", "D7": "PlanetSaptamshaD7Sign", "D9": "PlanetNavamshaD9Sign",
            "D10": "PlanetDashamamshaD10Sign", "D12": "PlanetDwadashamshaD12Sign", "D16": "PlanetShodashamshaD16Sign",
            "D20": "PlanetVimshamshaD20Sign", "D24": "PlanetChaturvimshamshaD24Sign", "D27": "PlanetBhamshaD27Sign",
            "D30": "PlanetTrimshamshaD30Sign", "D40": "PlanetKhavedamshaD40Sign", "D45": "PlanetAkshavedamshaD45Sign",
            "D60": "PlanetShashtyamshaD60Sign"}


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


def _deg(x):
    return float((json.loads(x) if isinstance(x, str) else x)["TotalDegrees"])


def _va_date(s):  # "00:00 30/08/1995 +00:00" → local calendar date as VedAstro prints it
    return dt.datetime.strptime(s.split()[1], "%d/%m/%Y").date()


def from_vedastro(planet_data: dict, ascendant: dict, dasa_range: dict | None = None,
                  shadbala: dict | None = None, birth: Birth | None = None, ashtakavarga: dict | None = None,
                  shadbala_components: dict | None = None, house_data: dict | None = None) -> ChartFacts:
    """Raw vedastro-local MCP results (tools/vedastro_batch.py files) → ChartFacts."""
    bodies, flags, notes = {}, [], {}
    for e in planet_data["payload"]["AllPlanetData"]:
        (name, v), = e.items()
        lon = _deg(v["PlanetNirayanaLongitude"])
        vargas = {}
        for D, key in VA_VARGA.items():
            if key in v:
                s = v[key]
                s = json.loads(s) if isinstance(s, str) else s
                vargas[D] = s["Name"] if isinstance(s, dict) else s
        n = VA_NAME[name]
        bodies[n] = _body(lon, v.get("IsPlanetRetrograde") == "True", vargas)
        label = v.get("PlanetConstellation", "")
        stem = label.split("-")[0].strip().lower()
        idx = next((i for k, i in sorted(VA_NAK.items(), key=lambda kv: -len(kv[0])) if stem.startswith(k)), None)
        if idx is not None and (NAKS[idx], int(label.split("-")[1])) != (bodies[n].nakshatra, bodies[n].pada):
            flags.append(f"VedAstro labels {n} as {label}, but its own longitude gives {bodies[n].nakshatra}-{bodies[n].pada}")
    asc = _deg(ascendant["GetAscendantLongitude"])
    bodies = {"Asc": _body(asc), **bodies}
    notes.update({  # found by tests/test_engine_compare.py on the synthetic S1 chart, 2026-09-27
        "D2": "VedAstro's D2 is not the Parashari hora (which uses only Leo and Cancer)",
        "D7": "VedAstro's current D7 differs from the Parashari rule for even signs (its 'SaptamshaSignOLD' matches it)",
        "D30": "VedAstro's trimshamsha sometimes gives the other sign of the same lord"})
    prov = Provenance(engine="vedastro", network="cloud:api.vedastro.org",
                      ayanamsa_deg=_deg(ascendant["AyanamsaDegree"]) if "AyanamsaDegree" in ascendant else None,
                      nodes="mean", dasha_year_days=360.0, varga_notes=notes)
    if birth is None:
        req = planet_data["request_sent"]["body"]["Time"]
        tm, dd, off = req["StdTime"].split()
        h, mnt = off.split(":")
        birth = Birth(date=dt.datetime.strptime(dd, "%d/%m/%Y").date(), time=tm,
                      utc_offset_hours=int(h) + (1 if int(h) >= 0 else -1) * int(mnt) / 60,
                      lat=req["Location"]["Latitude"], lon=req["Location"]["Longitude"])
    def nest(rows, depth):
        out = []
        for r in sorted(rows.values(), key=lambda r: _va_date(r["Start"])):   # VedAstro's dict order is not chronological
            s = _va_date(r["Start"])
            out.append(Period(lord=VA_NAME[r["Lord"]], start=s, end=_va_date(r["End"]),
                              sub=nest(r.get("SubDasas", {}), depth + 1) if depth < 3 else [],
                              clipped=s <= birth.date))   # periods running at birth are cut at the range start
        return out

    periods = nest(dasa_range["payload"]["DasaAtRange"], 1) if dasa_range else []
    if periods:
        periods[-1].clipped = True  # the last period is cut at the requested end date
    sb = {}
    if shadbala:
        for e in shadbala["payload"]["PlanetShadbalaPinda"]:
            (n, val), = e.items()
            if n not in ("Rahu", "Ketu"):  # VedAstro copies sign-lord values to the nodes: not classical
                sb[VA_NAME[n]] = round(float(val) / 60, 2)
    comps = {}
    for name, rows in (shadbala_components or {}).items():
        val = lambda m, rows=rows: float(rows[m]["payload"][m]) if rows.get(m, {}).get("ok") and m in rows[m].get("payload", {}) else None
        c = {k: val(m) for k, m in VA_COMPONENT.items()}
        amvh = [val(m) for m in VA_AMVH]
        c["abda_masa_vara_hora"] = sum(amvh) if all(x is not None for x in amvh) else None
        comps[VA_NAME[name]] = {k: v for k, v in c.items() if v is not None}
    bav = {}
    if ashtakavarga and "RAW_VEDASTRO_BHINNASHTAKAVARGA_BY_SIGN" in ashtakavarga:
        for name, row in ashtakavarga["RAW_VEDASTRO_BHINNASHTAKAVARGA_BY_SIGN"].items():
            if name in VA_NAME and VA_NAME[name] not in ("Ra", "Ke"):
                bav[VA_NAME[name]] = [row[sg] for sg in SIGNS]
    bhavas, arudha = [], {}
    if house_data:
        lagna = int(bodies["Asc"].lon // 30)
        for e in house_data["payload"]["AllHouseData"]:
            (hname, v), = e.items()
            h = int(hname[5:])
            b, m_, en = (float(x.split(":")[1]) for x in v["HouseLongitude"].split(","))
            bhavas.append({"house": h, "start": b, "middle": m_, "end": en})
            if v.get("ArudhaOfHouse", "").startswith("House"):
                arudha[f"A{h}"] = SIGNS[(lagna + int(v["ArudhaOfHouse"][5:]) - 1) % 12]
    return ChartFacts(birth=birth, provenance=prov, bodies=bodies, vimshottari=periods, shadbala_rupas=sb,
                      shadbala_components=comps, ashtakavarga=bav, bhavas=sorted(bhavas, key=lambda x: x["house"]),
                      arudha=arudha, flags=flags)


if __name__ == "__main__":
    import sys
    print(from_local(json.load(open(sys.argv[1]))).model_dump_json(indent=1)[:2000])
