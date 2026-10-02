"""Calculation core: positions, vargas, dashas, transits, strength, Jaimini factors, sensitivity, comparison."""
import datetime as dt

from . import engine, jaimini, sensitivity, strength


def compute_full(date, time, tz, lat, lon, **kw):
    """engine.compute() plus local Shadbala, Ashtakavarga and Jaimini factors (no external service)."""
    c = engine.compute(date, time, tz, lat, lon, **kw)
    ut = dt.datetime.fromisoformat(f"{date}T{time}") - dt.timedelta(hours=tz)
    c["shadbala"] = strength.shadbala(c, ut, lat, lon, tz)
    c["ashtakavarga"] = strength.ashtakavarga(c)
    c["jaimini"] = jaimini.jaimini(c)
    c["sensitivity_grid"] = sensitivity.grid(date, time, tz, lat, lon, on=kw.get("on"), year=kw.get("year", "sidereal"))
    return c
