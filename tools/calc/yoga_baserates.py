#!/usr/bin/env python3
"""How often each candidate-yoga / Kuja definition in chart_facts.py holds in random charts (VED-F3). A frequency of the
CONDITION only: it says nothing about outcomes, and random dates and places are not a population of real births.

usage: python3 tools/calc/yoga_baserates.py [N]      prints the BASE_RATE dict to paste into chart_facts.py
Random UT 1950-2010, latitude -50..60, longitude -180..180, seed 1; Lahiri, mean nodes, whole-sign houses.
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import swisseph as swe  # noqa: E402
from astro import config  # noqa: E402
from astro.calc import engine as E  # noqa: E402
sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
import chart_facts as CF  # noqa: E402


def rates(n=4000, seed=1):
    rnd, hits = random.Random(seed), {}
    for _ in range(n):
        jd = swe.julday(1950, 1, 1) + rnd.random() * 365.25 * 60
        lat, lon = rnd.uniform(-50, 60), rnd.uniform(-180, 180)
        pos, a = E.positions(jd), E.asc(jd, lat, lon)
        sd = lambda L: {"sign": E.SIGNS[int(L // 30)], "deg": round(L % 30, 4)}
        chart = {"asc": sd(a), "planets": {p: dict(sd(v["lon"]), retro=v["retro"]) for p, v in pos.items()}}
        D = CF.derive(chart)
        for fam in {CF.family(rid) for rid, _, holds, _, _ in CF.candidates(D) + CF.kuja(D) if holds}:
            hits[fam] = hits.get(fam, 0) + 1
    return {k: f"{100 * v / n:.0f}%" for k, v in sorted(hits.items())}


if __name__ == "__main__":
    r = rates(int(sys.argv[1]) if len(sys.argv) > 1 else 4000)
    print("BASE_RATE = {" + ", ".join(f'"{k}": "{v}"' for k, v in r.items()) + "}")
