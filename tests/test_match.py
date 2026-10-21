# Compatibility facts (Prasna Marga ch. XXI): counts and verse lookups on hand-computed synthetic longitudes.
from astro import service as S
from astro.calc import match as M


def says(out, verse):
    return [r["says"] for r in out["sign_count_readings"] + out["star_readings"] if r["verse"].startswith(verse)]


def test_mutual_seventh():
    out = M.facts({"moon": 10}, {"moon": 190})                     # Aries/Ashwini to Libra/Swati
    assert out["sign_count"] == {"girl_to_boy": 7, "boy_to_girl": 7} and out["star_count"]["girl_to_boy"] == 15
    assert says(out, "XXI.16") == ["mutual 7th: loving"] and says(out, "XXI.9-10") == ["very good even if the lords are enemies"]
    assert not says(out, "XXI.4") and not says(out, "XXI.26")       # 15 stars is not "more than 15"
    assert out["sign_lords"]["girl_lord_sees_boy_lord_as"] == "neutral"   # Mars to Venus


def test_same_star_on_the_barred_list():
    out = M.facts({"moon": 45}, {"moon": 46})                      # both Rohini
    assert out["star_count"]["girl_to_boy"] == 1 and out["sign_lords"]["same"]
    assert says(out, "XXI.15")[0].endswith("this star is one of them") and says(out, "XXI.16") == ["same star: 'fear from poison'"]


def test_second_sign_and_dina():
    out = M.facts({"moon": 0}, {"moon": 30})                       # Taurus 2nd from Aries; Krittika 3rd star
    assert out["sign_count"]["girl_to_boy"] == 2 and out["star_count"]["girl_to_boy"] == 3
    assert says(out, "XXI.4") == ["reject a boy in the 2nd-6th"] and set(says(out, "XXI.9-10")) == {"incompatible", "poverty"}
    assert says(out, "XXI.21-22")


def test_even_sign_girl_sixth_and_streedeergha_and_88th_pada():
    out = M.facts({"moon": 35}, {"moon": 185})                     # Taurus girl, Libra boy: 6th
    assert "even-sign girl: reject the 6th, accept the 8th" in says(out, "XXI.5")
    out = M.facts({"moon": 0}, {"moon": 291})                      # pada 1 -> pada 88; 22nd star
    assert out["pada_count_girl_to_boy"] == 88 and says(out, "XXI.23") and says(out, "XXI.26")


def test_sign_yoni_flags_capricorn_and_fixed_four():
    out = M.facts({"moon": 280, "asc": 45}, {"moon": 45, "asc": 45})
    assert out["sign_yoni"]["girl"] == ["bird", "animal"] and out["sign_yoni"]["ambiguous"]
    assert out["fixed_four"]["holds"] is False
    assert M.facts({"moon": 45, "asc": 45}, {"moon": 45, "asc": 45})["fixed_four"]["holds"]   # Taurus, D9 Taurus


def test_service_output_has_no_score_and_both_metas():
    b1 = S.BirthInput(date="1990-05-17", time="06:30", zone="Asia/Kolkata", lat=19.07, lon=72.88)
    b2 = S.BirthInput(date="1991-11-02", time="14:10", zone="Asia/Kolkata", lat=28.61, lon=77.21)
    out = S.compatibility(b1, b2)
    assert set(out["meta"]) == {"girl", "boy"} and out["meta"]["girl"]["zone"] == "Asia/Kolkata"
    assert "score" not in out and "Ashtakoota" in out["not_computed"]


def test_exact_star_and_pada_boundaries_fall_forward():
    """Review finding: 40° is Rohini (as engine.nak says), and 10° starts Ashwini's 4th pada."""
    out = M.facts({"moon": 40.0}, {"moon": 120.0})
    assert out["girl"]["nakshatra"] == "Rohini" and out["boy"]["nakshatra"] == "Magha"
    assert M.facts({"moon": 0.0}, {"moon": 10.0})["pada_count_girl_to_boy"] == 4
