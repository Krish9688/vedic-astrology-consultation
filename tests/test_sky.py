# Sky events without birth data (council 6, P2-1): retrograde stations and sign changes, to check generic Moon-sign or
# "year ahead" reports. Expected dates are public almanac facts for 2026 (sidereal Lahiri for sign changes), ±1 day.
import datetime as dt

import pytest

from astro import service as S


def near(rows, want, **match):
    days = [abs((dt.date.fromisoformat(r["date"]) - dt.date.fromisoformat(want)).days) for r in rows
            if all(r[k] == v for k, v in match.items())]
    return days and min(days) <= 1


@pytest.fixture(scope="module")
def y2026():
    return S.sky("2026-01-01", "2026-12-31")


@pytest.mark.parametrize("date,station", [("2026-02-26", "retrograde"), ("2026-03-20", "direct"),
                                          ("2026-06-29", "retrograde"), ("2026-07-23", "direct"),
                                          ("2026-10-24", "retrograde"), ("2026-11-13", "direct")])
def test_mercury_stations_2026(y2026, date, station):
    assert near(y2026["stations"], date, planet="Me", station=station)


def test_mercury_turns_retrograde_three_times_in_2026(y2026):
    assert len([r for r in y2026["stations"] if r["planet"] == "Me" and r["station"] == "retrograde"]) == 3


def test_jupiter_2026(y2026):
    assert near(y2026["sign_changes"], "2026-06-02", planet="Ju", to="Cancer")
    assert near(y2026["sign_changes"], "2026-10-31", planet="Ju", to="Leo")
    assert near(y2026["stations"], "2026-03-11", planet="Ju", station="direct")
    assert near(y2026["stations"], "2026-12-13", planet="Ju", station="retrograde")


def test_sky_needs_no_birth_data_and_limits_the_span():
    r = S.sky("2026-01-01", "2026-01-31")
    assert set(r) >= {"stations", "sign_changes", "meta"} and "lat" not in r["meta"]
    with pytest.raises(ValueError):
        S.sky("2026-01-01", "2030-01-02")        # more than 3 years
    with pytest.raises(ValueError):
        S.sky("2026-02-01", "2026-01-01")


def test_cli_sky(capsys):
    import json
    from astro import cli
    cli.main(["sky", "2026-06-01", "2026-06-05"])
    out = json.loads(capsys.readouterr().out)
    assert any(r["planet"] == "Ju" and r["to"] == "Cancer" for r in out["sign_changes"])


# P3-5 (council 6): the sensitivity grid can look further than ±15 min and shows the Moon sign
def test_sensitivity_wider_window_and_moon_sign():
    from astro.calc import sensitivity as SE
    g = SE.grid("1992-03-14", "09:40", 0, 51.5, -0.12, on="2026-10-02", span_min=120)
    assert g["offsets_min"][0] == -120 and g["offsets_min"][-1] == 120 and 60 in g["offsets_min"]
    assert "Moon sign" in g["rows"] and g["classes"]["Moon sign"] == "robust"
    assert g["first_change_within_grid"]["ascendant sign"]["earlier"] is not None or \
        g["first_change_within_grid"]["ascendant sign"]["later"] is not None          # 2 h always moves the lagna
    d = SE.grid("1992-03-14", "09:40", 0, 51.5, -0.12, on="2026-10-02")
    assert d["offsets_min"] == SE.OFFSETS_MIN                                         # default unchanged
    with pytest.raises(ValueError):
        SE.grid("1992-03-14", "09:40", 0, 51.5, -0.12, span_min=1000)


def test_cli_sensitivity_span(tmp_path, capsys):
    import json
    from astro import cli
    f = tmp_path / "s1.json"
    f.write_text(json.dumps(dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12)))
    cli.main(["sensitivity", str(f), "--on", "2026-10-02", "--span", "60"])
    assert json.loads(capsys.readouterr().out)["offsets_min"][-1] == 60
