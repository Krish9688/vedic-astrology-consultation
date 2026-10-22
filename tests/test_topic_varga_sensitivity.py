# P3-2: birth-time sensitivity covers the topic-varga lagnas (D2, D3, D4, D7, D24); each reported minute is checked by
# stepping the ascendant independently. Synthetic birth only.
import datetime as dt

import pytest

from astro.calc import engine as E

UT, LAT, LON = dt.datetime(1992, 3, 14, 9, 40), 51.5, -0.12


@pytest.mark.parametrize("n", [2, 3, 4, 7, 24])
def test_topic_varga_lagna_minutes_match_brute_force(n):
    s = E.sensitivity(UT, LAT, LON, E.positions(E.jd_of(UT))["Mo"]["lon"])[f"D{n} lagna (topic varga)"]
    lag = lambda m: E.varga(E.asc(E.jd_of(UT + dt.timedelta(minutes=m)), LAT, LON), n)
    for direction, sign in (("earlier", -1), ("later", 1)):
        m = s[direction]
        if m is None:                                            # no change within the 180-minute window
            assert all(lag(sign * k) == lag(0) for k in range(1, 181, 7))
        else:
            assert lag(sign * (m - 1)) == lag(0) != lag(sign * m), (n, direction, m)
