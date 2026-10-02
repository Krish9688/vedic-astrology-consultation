# Compatibility wrapper: the engine now lives in the astro package (astro/calc/engine.py).
# usage: .venv/bin/python tools/calc/local_chart.py --date 1992-03-14 --time 09:40 --tz 0 --lat 51.5 --lon -0.12 \
#            --out tests/fixtures/local/S1 [--node mean|true] [--year sidereal|365.25|360] [--on 2026-09-27] \
#            [--months 36] [--full]      (--full adds Shadbala, Ashtakavarga, Jaimini factors and the sensitivity grid)
#   (example: the synthetic test chart S1; personal charts go to private/<person>/, never into the repository)
import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from astro.calc import compute_full  # noqa: E402
from astro.calc.engine import *  # noqa: E402,F401,F403  (old imports keep working)
from astro.calc.engine import YEAR, compute, write_outputs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    for k in ("date", "time", "out"):
        ap.add_argument("--" + k, required=True)
    for k in ("tz", "lat", "lon"):
        ap.add_argument("--" + k, type=float, required=True)
    ap.add_argument("--node", default="mean", choices=["mean", "true"])
    ap.add_argument("--year", default="sidereal", choices=list(YEAR))
    ap.add_argument("--on", default=dt.date.today().isoformat())
    ap.add_argument("--months", type=int, default=36)
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    fn = compute_full if a.full else compute
    c = fn(a.date, a.time, a.tz, a.lat, a.lon, node=a.node, year=a.year, on=a.on, months=a.months)
    write_outputs(c, a.out)
    print(f"wrote {a.out}/calc.json, chart.json, calc.md ({c['meta']['ephemeris']})")


if __name__ == "__main__":
    main()
