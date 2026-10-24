"""Phase 5 acceptance gaps found by the 2026-10-22 audit: panchang properties (P4-3) and the Kuja lint (P4-2).
Synthetic dates and places only."""
import datetime as dt
import os
import random
import sys

import pytest

from astro import config
from astro.calc import engine as E, panchang as P


def test_tithi_and_karana_follow_the_elongation_formula_everywhere():
    """P4-3: tithi = floor(elongation / 12°) + 1 and karana = floor(elongation / 6°), at random moments 1900-2100."""
    rnd = random.Random(20261022)
    for _ in range(300):
        jd = E.jd_of(dt.datetime(1900, 1, 1)) + rnd.uniform(0, 73000)
        el = P._elong(jd)
        if min(el % 6, 6 - el % 6) < 1e-6:                    # a boundary to the microdegree: skip, not a property
            continue
        assert P._index("tithi", jd) == int(el // 12)
        assert P.elements(jd)["tithi"]["number"] == int(el // 12) + 1
        assert P._index("karana", jd) == int(el // 6)


@pytest.mark.parametrize("place", [(19.07, 72.88, 5.5), (51.5, -0.12, 0), (-33.87, 151.21, 10), (40.71, -74.01, -5)])
def test_vara_changes_at_sunrise_and_days_chain(place):
    """P4-3: the Hindu day runs sunrise to sunrise; its vara is the weekday of the civil date of its sunrise, so
    consecutive days chain (next_sunrise = following sunrise) and the vara advances by exactly one."""
    lat, lon, tz = place
    d0 = dt.date(2025, 3, 10)
    days = [P.day(d0 + dt.timedelta(days=k), lat, lon, tz) for k in range(8)]
    for a, b in zip(days, days[1:]):
        assert a["next_sunrise"] == b["sunrise"], (a["next_sunrise"], b["sunrise"])
        assert P.VARA.index(b["vara"]) == (P.VARA.index(a["vara"]) + 1) % 7
        assert a["vara"] == P.VARA[dt.date.fromisoformat(a["date"]).weekday()]
        assert a["sunrise"][:10] == a["date"]


def _lint():
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import life_lint
    return lambda t: [i for i in life_lint.lint(t)["issues"] if i.startswith("SAFETY")]


@pytest.mark.parametrize("text", [
    "You are manglik, so marriage needs care.",
    "You are not manglik.",
    "Your chart has strong mangal dosha.",
    "Kuja dosha will harm your marriage.",
    "Mars in the 7th will harm your spouse.",
    "Your husband will suffer under this period.",
])
def test_kuja_verdicts_and_spouse_harm_are_blocked(text):
    """P4-2: Kuja conventions are listed for comparison, never a verdict on a person or harm to a spouse."""
    assert _lint()(text), text


@pytest.mark.parametrize("text", [
    "Three Kuja conventions apply differently here; they are listed for comparison only, never a marriage verdict.",
    "Mars from the Moon meets the popular Kuja rule, which LOL says is in no authoritative text.",
    "Partnership questions deserve patience in this period.",
])
def test_kuja_descriptions_pass(text):
    assert not _lint()(text), text
