"""P8-3e: Julian-calendar dates are converted to Gregorian through Swiss Ephemeris (CALC-X6 item 5: one Julian record
converted, range edges). Conversion checks use published calendar-reform dates, not anyone's birth record."""
import pytest

from astro import service as S

PLACE = dict(time="12:00", tz="+00:00", lat=51.5, lon=0.0)   # synthetic


@pytest.mark.parametrize("julian,gregorian", [
    ("1582-10-05", "1582-10-15"),     # the Gregorian reform: the day after Julian 4 October was Gregorian 15 October
    ("1752-09-03", "1752-09-14"),     # Britain: Wednesday 2 September 1752 was followed by Thursday 14 September
    ("1918-02-01", "1918-02-14"),     # Russia: 31 January 1918 was followed by 14 February
    ("1700-02-29", "1700-03-11"),     # a Julian leap day that does not exist in the Gregorian calendar
])
def test_julian_dates_convert_to_gregorian(julian, gregorian):
    b = S.BirthInput(date=julian, calendar="julian", **PLACE)
    assert b.date.isoformat() == gregorian and f"Julian calendar {julian}" in b.date_source


def test_caller_fields_cannot_switch_the_conversion_off_and_a_dump_converts_once():
    b = S.BirthInput(date="1752-09-03", calendar="julian", date_source="x", **PLACE)   # review finding (8e93bdb)
    assert b.date.isoformat() == "1752-09-14" and b.julian_date == "1752-09-03" and b.date_source != "x"
    again = S.BirthInput(**b.model_dump(mode="json"))
    assert again.date == b.date and again.julian_date == "1752-09-03"
    g = S.BirthInput(date="1752-09-03", date_source="x", julian_date="1700-01-01", **PLACE)   # Gregorian: ignored
    assert g.date.isoformat() == "1752-09-03" and g.julian_date is None and g.date_source is None


def test_julian_dates_outside_the_range_name_the_converted_date():
    with pytest.raises(ValueError, match="Gregorian 3000-01-20"):
        S.BirthInput(date="2999-12-31", calendar="julian", **PLACE)


def test_invalid_julian_date_is_refused():
    with pytest.raises(ValueError):
        S.BirthInput(date="1700-02-30", calendar="julian", **PLACE)
    with pytest.raises(ValueError):
        S.BirthInput(date="1752-09-03", calendar="hebrew", **PLACE)


def test_chart_from_julian_input_equals_the_gregorian_chart_and_says_so():
    j = S.calculate_chart(S.BirthInput(date="1752-09-03", calendar="julian", **PLACE), full=False)
    g = S.calculate_chart(S.BirthInput(date="1752-09-14", **PLACE), full=False)
    assert j["bodies"] == g["bodies"] and "converted to Gregorian 1752-09-14" in j["meta"]["date_source"]
    assert "date_source" not in g["meta"]                                    # Gregorian input: meta unchanged


@pytest.mark.parametrize("date,files", [("1799-12-31", False), ("1800-01-01", True), ("2399-12-31", True),
                                        ("2999-12-31", False)])
def test_range_edges_compute_and_name_the_ephemeris_actually_used(date, files):
    from astro.calc import engine
    eph = S.calculate_chart(S.BirthInput(date=date, **PLACE), full=False)["meta"]["ephemeris"]
    want_files = files and engine.EPHE_DIR is not None          # CI has no data files: Moshier everywhere
    assert eph.startswith("Swiss Ephemeris data files") == want_files and ("Moshier" in eph) != want_files


def test_dates_after_2999_are_refused():
    with pytest.raises(ValueError):
        S.BirthInput(date="3001-01-01", **PLACE)
