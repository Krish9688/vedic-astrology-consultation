"""Build tests/reference_charts/edge_suite.json — synthetic charts placed exactly on the edges a calculator gets wrong.
Each moment is found by bisection on the engine itself (so it really sits on the boundary), then the charts 30 s either
side are recorded with golden values. Golden values lock behaviour (regression); correctness comes from the
properties tested in test_reference_suite.py and the cross-engine comparisons. Re-run only on purpose:

    .venv/bin/python tests/reference_charts/build_edge_suite.py
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from astro.calc import engine as E  # noqa: E402

LONDON, TROMSO, SVALBARD, DELHI = (51.5, -0.12, 0), (69.65, 18.96, 1), (78.22, 15.65, 1), (28.61, 77.21, 5.5)


def bisect(f, a, b, minutes=0.05):
    """First moment in [a, b] where f changes value (f(a) != f(b))."""
    fa = f(a)
    while (b - a) > dt.timedelta(minutes=minutes):
        m = a + (b - a) / 2
        a, b = (m, b) if f(m) == fa else (a, m)
    return b


def moon(t):
    return E.positions(E.jd_of(t))["Mo"]["lon"]


def entry(cid, category, t_ut, place, check, **extra):
    lat, lon, tz = place
    local = t_ut + dt.timedelta(hours=tz)
    return {"id": cid, "category": category, "date": local.strftime("%Y-%m-%d"), "time": local.strftime("%H:%M:%S"),
            "tz": tz, "lat": lat, "lon": lon, "check": check, **extra}


def pair(cid, category, t_edge, place, check, **extra):
    """Two charts 30 s before and after an edge."""
    h = dt.timedelta(seconds=30)
    return [entry(f"{cid}-before", category, t_edge - h, place, check, **extra),
            entry(f"{cid}-after", category, t_edge + h, place, check, **extra)]


def main():
    t0 = dt.datetime(2001, 5, 10, 12)
    out = [entry("normal", "normal chart", dt.datetime(1985, 7, 20, 14, 30), DELHI, "baseline")]
    # Moon crossing a sign, a nakshatra and a pada boundary
    out += pair("moon-sign", "near sign boundary", bisect(lambda t: int(moon(t) // 30), t0, t0 + dt.timedelta(days=3)),
                LONDON, "Moon sign differs between before/after")
    out += pair("moon-nak", "near nakshatra boundary", bisect(lambda t: int(moon(t) / (40 / 3)), t0, t0 + dt.timedelta(days=1.2)),
                LONDON, "Moon nakshatra and first mahadasha lord differ; balance near full / near zero")
    out += pair("moon-pada", "near pada boundary", bisect(lambda t: int(moon(t) / (10 / 3)), t0, t0 + dt.timedelta(hours=8)),
                LONDON, "Moon pada and D9 sign differ")
    a = dt.datetime(1999, 3, 3, 6)
    out += pair("asc-sign", "near ascendant boundary",
                bisect(lambda t: int(E.asc(E.jd_of(t), LONDON[0], LONDON[1]) // 30), a, a + dt.timedelta(hours=2.5)),
                LONDON, "ascendant sign differs; sensitivity reports a change within 1 minute")
    a = dt.datetime(1999, 3, 3, 10)
    out += pair("d9-lagna", "birth time causing varga change",
                bisect(lambda t: E.varga(E.asc(E.jd_of(t), LONDON[0], LONDON[1]), 9), a, a + dt.timedelta(minutes=20)),
                LONDON, "D9 lagna differs while the D1 ascendant sign is the same")
    out.append(entry("polar-day", "high latitude", dt.datetime(1990, 6, 21, 10), TROMSO, "no sunrise/sunset: polar fallback flag"))
    out.append(entry("polar-night", "high latitude", dt.datetime(1990, 12, 21, 11), SVALBARD, "no sunrise/sunset: polar fallback flag"))
    # midnight and pre-sunrise in Delhi (Hindu day starts at sunrise)
    mid = dt.datetime(2003, 1, 15, 0, 0) - dt.timedelta(hours=5.5)
    out += pair("midnight", "near midnight", mid, DELHI, "weekday lord identical either side of civil midnight")
    out.append(entry("pre-sunrise", "before sunrise", dt.datetime(2003, 1, 15, 4, 30) - dt.timedelta(hours=5.5), DELHI,
                     "weekday lord = previous civil day's (Hindu day from sunrise)", civil_weekday="Wednesday", expected_vara="Ma"))
    out.append(entry("leap-2024", "leap year", dt.datetime(2024, 2, 29, 6, 15), DELHI, "29 February computes"))
    out.append(entry("leap-2000", "leap year", dt.datetime(2000, 2, 29, 23, 50), LONDON, "29 February 2000 (century leap year)"))
    # Mercury station: find the moment its speed changes sign
    s = dt.datetime(2005, 3, 1)
    station = bisect(lambda t: E.positions(E.jd_of(t))["Me"]["speed"] < 0, s, s + dt.timedelta(days=60), minutes=1)
    h = dt.timedelta(hours=12)
    out += [entry("me-station-before", "retrograde transition", station - h, LONDON, "Mercury retrograde flag differs"),
            entry("me-station-after", "retrograde transition", station + h, LONDON, "Mercury retrograde flag differs")]
    # Moon exactly at a nakshatra start: balance = the whole period of the new lord
    out += pair("dasha-edge", "dasha boundary", bisect(lambda t: int(moon(t) / (40 / 3)), dt.datetime(2010, 8, 1),
                                                     dt.datetime(2010, 8, 2, 6)), DELHI,
                "first mahadasha lord changes; balance ≈ full period after the edge")
    for e in out:
        c = E.compute(e["date"], e["time"], e["tz"], e["lat"], e["lon"], on="2026-01-01", extras=False)
        e["golden"] = {"asc": c["bodies"]["Asc"]["lon"], "moon": c["bodies"]["Mo"]["lon"],
                       "sun": c["bodies"]["Su"]["lon"], "first_md": c["vimshottari"][0]["lord"],
                       "first_md_end": c["vimshottari"][0]["end"], "moon_nak": c["bodies"]["Mo"]["nakshatra"],
                       "moon_pada": c["bodies"]["Mo"]["pada"], "d9_asc": c["bodies"]["Asc"]["vargas"]["D9"],
                       "me_retro": c["bodies"]["Me"]["retro"]}
    path = os.path.join(os.path.dirname(__file__), "edge_suite.json")
    json.dump({"built_with": E.ENGINE_VERSION, "ephemeris": E.ephemeris_info()["ephemeris"], "charts": out},
              open(path, "w"), indent=1, ensure_ascii=False)
    print(f"{len(out)} charts → {path}")


if __name__ == "__main__":
    main()
