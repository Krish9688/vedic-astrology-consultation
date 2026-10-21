# Historical time-zone resolution (IANA tz database through zoneinfo) and offline place lookup. Synthetic birth data;
# the place tests use an invented gazetteer in the GeoNames format.
import datetime as dt
import os

import pytest

from astro import places, service as S

B = dict(date="1990-05-17", time="06:30", lat=19.07, lon=72.88)


def birth(**kw):
    return S.BirthInput(**(B | kw))


def test_zone_gives_the_offset_of_the_birth_moment():
    assert birth(zone="Asia/Kolkata").tz == 5.5
    b = birth(date="1943-06-01", zone="Asia/Kolkata")            # war time: +06:30, not today's +05:30
    assert b.tz == 6.5 and any("pre-1948" in f for f in b.tz_flags) and any("1970" in f for f in b.tz_flags)
    assert birth(date="1969-01-15", time="12:00", zone="Europe/London", lat=51.5, lon=-0.12).tz == 1.0   # BST all year
    assert birth(date="2021-07-04", time="13:15", zone="America/New_York", lat=40.71, lon=-74.01).tz == -4.0


def test_explicit_offset_still_works_and_must_agree_with_a_zone():
    assert birth(tz="+05:30").tz_source == "explicit UTC offset"
    assert birth(tz="+05:30", zone="Asia/Kolkata").tz == 5.5
    with pytest.raises(ValueError, match="disagrees"):
        birth(tz="+05:00", zone="Asia/Kolkata")
    with pytest.raises(ValueError, match="UTC offset at birth"):
        birth()


def test_skipped_and_repeated_clock_times_are_refused_not_guessed():
    ny = dict(lat=40.71, lon=-74.01, zone="America/New_York")
    with pytest.raises(ValueError, match="does not exist"):
        birth(date="2021-03-14", time="02:30", **ny)
    with pytest.raises(ValueError, match="occurs twice"):
        birth(date="2021-11-07", time="01:30", **ny)
    assert birth(date="2021-11-07", time="01:30", fold=0, **ny).tz == -4.0
    assert birth(date="2021-11-07", time="01:30", fold=1, **ny).tz == -5.0


def test_local_mean_time_era_needs_an_explicit_offset():
    with pytest.raises(ValueError, match=r"local mean time at this longitude: \+04:51:31"):
        birth(date="1850-01-01", zone="Asia/Kolkata")            # 72.88° E = 4 h 51 m 31 s


@pytest.mark.parametrize("bad", [dict(zone="Mars/Olympus"), dict(lat=95, tz="+00:00"), dict(lon=181, tz="+00:00"),
                                 dict(tz="+15:00"), dict(zone="Asia/Kolkata", fold=2)])
def test_invalid_zone_coordinates_and_boundaries(bad):
    with pytest.raises(ValueError):
        birth(**bad)


def test_zone_provenance_reaches_every_output():
    c = S.calculate_chart(birth(date="1943-06-01", zone="Asia/Kolkata"), full=False)
    assert c["meta"]["zone"] == "Asia/Kolkata" and c["meta"]["utc_offset"] == "+06:30"
    assert c["meta"]["utc_offset_source"].startswith("IANA Asia/Kolkata (tzdb ") and c["meta"]["utc_offset_flags"]
    assert S.dasha(birth(zone="Asia/Kolkata"))["meta"]["zone"] == "Asia/Kolkata"


GAZ = [  # GeoNames columns: id name ascii alternates lat lon class code cc cc2 admin1 a2 a3 a4 population elev dem zone date
    ["1", "Testpur", "Testpur", "Testapuram,Old Testpur", "17.4", "78.5", "P", "PPL", "IN", "", "40", "", "", "", "900000",
     "", "500", "Asia/Kolkata", "2024-01-01"],
    ["2", "Testpur", "Testpur", "", "25.4", "68.4", "P", "PPL", "PK", "", "05", "", "", "", "700000", "", "20",
     "Asia/Karachi", "2024-01-01"],
    ["3", "Testville", "Testville", "", "51.5", "-0.1", "P", "PPL", "GB", "", "ENG", "", "", "", "20000", "", "10",
     "Europe/London", "2024-01-01"],
]


@pytest.fixture
def gazetteer(tmp_path):
    d = tmp_path / "places"
    d.mkdir()
    (d / "cities15000.txt").write_text("\n".join("\t".join(r) for r in GAZ) + "\n", encoding="utf-8")
    (d / "admin1CodesASCII.txt").write_text("IN.40\tTestland\tTestland\t1\nPK.05\tTestprov\tTestprov\t2\n", encoding="utf-8")
    return str(tmp_path)


def test_place_names_that_match_several_places_are_ambiguous(gazetteer):
    r = places.search("testpur", gazetteer)
    assert r["ambiguous"] and [m["country"] for m in r["matches"]] == ["IN", "PK"]   # larger first, both returned
    assert r["matches"][0] | {} == r["matches"][0] and r["matches"][0]["region"] == "Testland"
    one = places.search("Testpur", gazetteer, country="PK")
    assert not one["ambiguous"] and one["matches"][0]["zone"] == "Asia/Karachi"
    assert places.search("Testapuram", gazetteer)["matches"][0]["geonameid"] == 1    # alternate names count
    assert places.search("nowhere", gazetteer)["matches"] == []


def test_place_lookup_without_the_gazetteer_says_how_to_install_it(tmp_path):
    with pytest.raises(FileNotFoundError, match="setup --places"):
        places.search("Testpur", str(tmp_path))


def test_service_find_place_is_offline_and_returns_zones(gazetteer, monkeypatch):
    monkeypatch.setattr(S.config, "load", lambda: S.config.Settings(data_dir=gazetteer))
    r = S.find_place("Testville")
    assert r["matches"][0]["zone"] == "Europe/London" and os.path.exists(os.path.join(gazetteer, "places", "cities15000.txt"))
    b = birth(lat=r["matches"][0]["lat"], lon=r["matches"][0]["lon"], zone=r["matches"][0]["zone"], date="1969-01-15")
    assert b.tz == 1.0 and dt.date(1969, 1, 15) == b.date
