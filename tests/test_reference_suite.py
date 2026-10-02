# Edge-case reference charts (synthetic; built by tests/reference_charts/build_edge_suite.py): each pair sits 30 s
# either side of a boundary. Properties prove the edge behaves; golden values lock positions (regression).
# Cross-checked on 2026-10-02 against PyJHora 4.8.7 (Lahiri): 20/20 charts agree on Moon nakshatra, pada, ascendant
# sign, D9 lagna, first mahadasha lord and weekday lord; PyJHora cannot compute the two polar charts.
import json
import os

import pytest

from astro.calc import compute_full, engine

D = json.load(open(os.path.join(os.path.dirname(__file__), "reference_charts", "edge_suite.json")))
C = {c["id"]: c for c in D["charts"]}
FILES = engine.ephemeris_info()["ephemeris"].startswith("Swiss")   # goldens were built with the data files
TOL = 0.001 if FILES else 0.002                                    # Moshier differs by < 3″ (≈0.0008°)


def full(cid):
    c = C[cid]
    return compute_full(c["date"], c["time"], c["tz"], c["lat"], c["lon"], on="2026-01-01")


@pytest.mark.parametrize("cid", list(C))
def test_golden(cid):
    c = C[cid]
    out = engine.compute(c["date"], c["time"], c["tz"], c["lat"], c["lon"], on="2026-01-01", extras=False)
    g = c["golden"]
    for k, body in (("asc", "Asc"), ("moon", "Mo"), ("sun", "Su")):
        assert abs((out["bodies"][body]["lon"] - g[k] + 180) % 360 - 180) < TOL, (cid, k)


def test_edges_flip():
    pairs = {"moon-sign": lambda c: int(c["golden"]["moon"] // 30), "moon-nak": lambda c: c["golden"]["moon_nak"],
             "moon-pada": lambda c: c["golden"]["moon_pada"], "asc-sign": lambda c: int(c["golden"]["asc"] // 30),
             "d9-lagna": lambda c: c["golden"]["d9_asc"], "dasha-edge": lambda c: c["golden"]["first_md"]}
    for p, f in pairs.items():
        assert f(C[f"{p}-before"]) != f(C[f"{p}-after"]), p
    assert int(C["d9-lagna-before"]["golden"]["asc"] // 30) == int(C["d9-lagna-after"]["golden"]["asc"] // 30)
    assert C["moon-nak-before"]["golden"]["first_md"] != C["moon-nak-after"]["golden"]["first_md"]
    assert C["me-station-before"]["golden"]["me_retro"] != C["me-station-after"]["golden"]["me_retro"]


def test_dasha_balance_at_nakshatra_start():
    c = C["dasha-edge-after"]                       # Moon 0°00′15″ Aries: almost the whole 7-year Ketu period remains
    start, end = c["date"], c["golden"]["first_md_end"]
    years = (int(end[:4]) - int(start[:4])) + (int(end[5:7]) - int(start[5:7])) / 12
    assert c["golden"]["first_md"] == "Ke" and 6.9 < years <= 7.0


def test_ascendant_sensitivity_detects_edge():
    s = full("asc-sign-before")["sensitivity_grid"]
    assert s["classes"]["ascendant sign"] == "very high" and s["first_change_within_grid"]["ascendant sign"]["later"] <= 1


def test_polar_charts_compute_with_fallback():
    for cid in ("polar-day", "polar-night"):
        tl = full(cid)["shadbala"]["time_lords"]
        assert tl["polar_sunrise_fallback"] is True, cid


def test_hindu_day_starts_at_sunrise():
    a, b = full("midnight-before")["shadbala"]["time_lords"], full("midnight-after")["shadbala"]["time_lords"]
    assert a["weekday"] == b["weekday"]                                  # civil midnight changes nothing
    assert full("pre-sunrise")["shadbala"]["time_lords"]["weekday"] == C["pre-sunrise"]["expected_vara"]


@pytest.mark.parametrize("cid", ["leap-2024", "leap-2000"])
def test_leap_days(cid):
    c = full(cid)
    assert c["meta"]["birth_local"].startswith(C[cid]["date"]) and c["ashtakavarga"]["sav_total"] == 337
