# Vimshottari against INDEPENDENT published values (not values produced by this engine). Public: the balance fraction
# (Lahiri table). Private fixtures (copyrighted books, skipped where absent): a full chart's signs and balance, and a
# published chart's dated mahadasha/antardasha/pratyantar boundaries — these also reject a 360-day year (27 days off).
# 1. N. C. Lahiri's Indian Ephemeris balance table, as reproduced in B. V. Raman, Hindu Predictive Astrology
#    (Table II and worked example): Moon at Taurus 25°10' → balance of Mars dasha 6 y 0 m 14 d (table rounding ±1 day).
# 2. Optional private fixture (copyrighted book chart, kept in private/reference/, never exported): a full chart whose
#    published sign placements and dasha balance the engine must reproduce. Skipped where the file is absent (CI, public).
import datetime as dt
import json
import os

import pytest

from astro.calc import engine as E

YMD_DAYS = lambda y, m, d: (y + m / 12 + d / 360) * 365.25    # tables count 12 months of 30 days per year


def balance_days(moon, ylen):
    b = dt.datetime(2000, 1, 1)
    md = E.vimshottari(moon, b, ylen)[0]
    return md["lord"], (md["end"] - b).total_seconds() / 86400 * 365.25 / ylen   # in table (Julian-year) days


def test_lahiri_table_taurus_25_10():
    lord, days = balance_days(30 + 25 + 10 / 60, E.YEAR["sidereal"])
    assert lord == "Ma"
    assert abs(days - YMD_DAYS(6, 0, 14)) <= 1.5, days


PRIV = os.path.join(os.path.dirname(__file__), "..", "private", "reference", "dasha_crux34.json")


@pytest.mark.skipif(not os.path.exists(PRIV), reason="private reference fixture not present")
def test_published_chart_signs_and_balance():
    ref = json.load(open(PRIV))
    b, x = ref["birth"], ref["expected"]
    c = E.compute(b["date"], b["time"], b["tz"], b["lat"], b["lon"], on="2026-01-01", extras=False)
    assert {k: c["bodies"][k]["sign"] for k in x["signs"]} == x["signs"]
    md = c["vimshottari"][0]
    assert md["lord"] == x["birth_dasha_lord"]
    born = dt.date.fromisoformat(b["date"])
    y, m, d = x["balance_ymd"]
    mm = born.month - 1 + m
    expect = dt.date(born.year + y + mm // 12, mm % 12 + 1, min(born.day, 28)) + dt.timedelta(days=d + born.day - min(born.day, 28))
    assert abs((dt.date.fromisoformat(md["end"]) - expect).days) <= ref["tolerance_days"]


KNRAO = os.path.join(os.path.dirname(__file__), "..", "private", "reference", "dasha_knrao.json")


@pytest.mark.skipif(not os.path.exists(KNRAO), reason="private reference fixture not present")
def test_published_dasha_boundaries():
    # Absolute MD/AD/PD dates from a published chart, and AD spacing from a second one (fixture explains why relative)
    ref = json.load(open(KNRAO))
    a, tol = ref["absolute"], ref["absolute"]["tolerance_days"]
    b, x = a["birth"], a["expected"]
    v = E.compute(b["date"], b["time"], b["tz"], b["lat"], b["lon"], on="2026-01-01", extras=False)["vimshottari"]
    md = {m["lord"]: m for m in v}
    near = lambda got, want, t: abs((dt.date.fromisoformat(got) - dt.date.fromisoformat(want)).days) <= t
    for lord, end in x["md_end"].items():
        assert near(md[lord]["end"], end, tol), (lord, md[lord]["end"], end)
    for key, start in x["ad_start"].items():
        m, s = key.split("-")
        assert near({r["lord"]: r for r in md[m]["sub"]}[s]["start"], start, tol), key
    for key, end in x["pd_end"].items():
        m, s, p = key.split("-")
        pd = {r["lord"]: r for r in {r["lord"]: r for r in md[m]["sub"]}[s]["sub"]}[p]
        assert near(pd["end"], end, tol), (key, pd["end"], end)
    r = ref["relative"]
    start = dt.datetime.fromisoformat(r["md_start"])
    nak_start = {"Ke": 0, "Ve": 1, "Su": 2, "Mo": 3, "Ma": 4, "Ra": 5, "Ju": 6, "Sa": 7, "Me": 8}[r["md"]] * 40 / 3
    ads = {s["lord"]: s for s in E.vimshottari(nak_start, start, E.YEAR["sidereal"])[0]["sub"]}
    for lord, end in r["ad_end"].items():
        assert abs((ads[lord]["end"].date() - dt.date.fromisoformat(end)).days) <= r["tolerance_days"], (lord, ads[lord]["end"], end)
