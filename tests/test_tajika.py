# Tajika annual chart against the worked examples printed in PVR ch. 27-28 and 31 (published textbook charts).
import pytest

from astro import service as S

EX118 = S.BirthInput(date="1967-03-08", time="17:40", tz="+05:30", lat=26.3, lon=73.0667)    # PVR Example 118
EX122 = S.BirthInput(date="1972-06-01", time="04:16", tz="+05:30", lat=16.25, lon=81.2)      # PVR Example 122


def deg(pos):                     # "Pisces 4.98" -> absolute degrees
    sign, d = pos.split()
    return ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
            "Aquarius", "Pisces"].index(sign) * 30 + float(d)


def test_example_118_return_muntha_harsha_and_year_lord():
    r = S.tajika(EX118, 34)
    assert r["varsha_pravesh"].startswith("2000-03-08 04:41:")           # PVR: 4:41:21 am IST
    assert r["annual_lagna"].startswith("Capricorn") and r["day_or_night"] == "night" and r["muntha"] == "Taurus"
    assert abs(deg(r["positions"]["Mo"]) - deg("Pisces 15.233")) < 0.05    # PVR: Moon 15 Pi 14, Mars 24 Pi 58
    assert abs(deg(r["positions"]["Ma"]) - deg("Pisces 24.967")) < 0.05
    assert r["harsha_bala"] == {"Su": 0, "Mo": 15, "Ma": 0, "Me": 10, "Ju": 5, "Ve": 10, "Sa": 5}
    assert [c["planet"] for c in r["year_lord_candidates"]] == ["Ju", "Su", "Ve", "Sa", "Ma"]
    assert r["year_lord"] == "Ma" and "sextile" in r["year_lord_candidates"][4]["aspect_on_lagna"]


def test_example_118_sahams_including_night_reversal_and_30_degree_rule():
    s = S.tajika(EX118, 34)["sahams"]
    assert abs(deg(s["Samartha"]) - deg("Pisces 5.033")) < 0.1            # night-reversed, +30° added
    assert abs(deg(s["Vanik"]) - deg("Sagittarius 7.067")) < 0.1          # night-reversed, no +30°


def test_exercise_47_exact_return():
    assert S.tajika(EX118, 27)["varsha_pravesh"].startswith("1993-03-08 09:36:")   # PVR: exact 9:36:18 am


def test_example_122_vivaha_saham_and_mudda():
    r = S.tajika(EX122, 22)
    assert r["annual_lagna"].startswith("Virgo") and abs(deg(r["sahams"]["Vivaha"]) - deg("Sagittarius 2.367")) < 0.1
    m = r["mudda_dasha"]
    assert [x["lord"] for x in m[:2]] == ["Ra", "Ju"] and len(m) == 10 and m[-1]["lord"] == "Ra"
    assert round(sum(x["solar_days"] for x in m), 6) == 360
    # PVR prints Rahu to 14 Jul 1993; its own definition (a solar day = the Sun moving 1°) gives 16 Jul. Recorded in
    # SOURCES["mudda"]; this test pins the definition, not the example.
    assert m[0]["end"].startswith("1993-07-16") and "disagree" in r["sources"]["mudda"]


def test_default_year_follows_on_and_rejects_year_zero():
    assert S.tajika(EX118, None, S.Options(on="2000-03-07"))["year"] == 33
    assert S.tajika(EX118, None, S.Options(on="2000-03-09"))["year"] == 34
    with pytest.raises(ValueError):
        S.tajika(EX118, 0)
    with pytest.raises(ValueError):                                       # a date before birth has no Tajika year
        S.tajika(EX118, None, S.Options(on="1960-01-01"))
