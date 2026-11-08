"""Chart registry for the accuracy reference set (docs/ACCURACY-RUBRIC.md §4.1: a case names a chart by id, never
inline birth data). Every id resolves to a record already stored in the project's fixtures; nothing is copied here.

C1..C9      tests/reference_charts/crosscheck_2026_11.json (synthetic, 2026-11 cross-check)
<edge id>   tests/reference_charts/edge_suite.json (22 synthetic edge charts)
S1, S2, ayan-*, dst-gap-after, cal-*, south-west   EXTRA in tools/oracle_pyjhora.py (synthetic)
PVR-Ex118, PVR-Ex122   tests/test_tajika.py (published PVR textbook examples)
raman-1918  tests/reference_charts/raman_1918.json (published book example)

Imports nothing from astro, so the G1 reference script can use it.
"""
from __future__ import annotations

import ast
import functools
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XC = os.path.join(ROOT, "tests", "reference_charts", "crosscheck_2026_11.json")
ES = os.path.join(ROOT, "tests", "reference_charts", "edge_suite.json")
OR = os.path.join(ROOT, "tests", "fixtures", "oracle", "pyjhora-edge.json")
RAMAN = os.path.join(ROOT, "tests", "reference_charts", "raman_1918.json")
ORACLE_PY = os.path.join(ROOT, "tools", "oracle_pyjhora.py")
TAJIKA_PY = os.path.join(ROOT, "tests", "test_tajika.py")


def offset_hours(v):
    """'+05:30' / '-04:00' / 5.5 -> hours."""
    if isinstance(v, (int, float)):
        return float(v)
    sign = -1 if v.startswith("-") else 1
    h, m = v.lstrip("+-").split(":")[:2]
    return sign * (int(h) + int(m) / 60)


def _literal(path, name):
    """Value of a module-level `name = <literal>` in a Python file, read without importing it."""
    for node in ast.parse(open(path, encoding="utf-8").read()).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return node.value
    raise KeyError(f"{name} not in {path}")


def _clock(t):
    return t if t.count(":") == 2 else t + ":00"


@functools.lru_cache(maxsize=None)
def registry():
    out = {}
    for c in json.load(open(XC, encoding="utf-8"))["charts"]:
        i = c["input"]
        out[c["id"]] = dict(date=i["date"], time=_clock(i["time"]), tz=offset_hours(i["utc_offset"]), lat=i["lat"],
                            lon=i["lon"], source="crosscheck_2026_11.json")
    for c in json.load(open(ES, encoding="utf-8"))["charts"]:
        out[c["id"]] = dict(date=c["date"], time=_clock(c["time"]), tz=float(c["tz"]), lat=c["lat"], lon=c["lon"],
                            source="edge_suite.json")
    for c in ast.literal_eval(_literal(ORACLE_PY, "EXTRA")):
        out[c["id"]] = dict(date=c["date"], time=_clock(c["time"]), tz=float(c["tz"]), lat=c["lat"], lon=c["lon"],
                            source="oracle_pyjhora.py EXTRA")
    for name, cid in (("EX118", "PVR-Ex118"), ("EX122", "PVR-Ex122")):
        kw = {k.arg: ast.literal_eval(k.value) for k in _literal(TAJIKA_PY, name).keywords}
        out[cid] = dict(date=kw["date"], time=_clock(kw["time"]), tz=offset_hours(kw["tz"]), lat=kw["lat"],
                        lon=kw["lon"], source="tests/test_tajika.py")
    b = json.load(open(RAMAN, encoding="utf-8"))["birth"]
    out["raman-1918"] = dict(date=b["date"], time=_clock(b["time"]), tz=float(b["tz"]), lat=b["lat"], lon=b["lon"],
                             source="raman_1918.json")
    return out


def chart(cid):
    return registry()[cid]
