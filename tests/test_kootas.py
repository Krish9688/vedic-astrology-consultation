# Four rule-fixed Ashtakoota items (tara, bhakoot, graha maitri, nadi; R3-ashtakoota.md) on synthetic longitudes.
import json

from astro.calc import match as M
from astro.calc.strength import NATURAL

K = M.kootas


def cond(block, text):
    return next(c["holds"] for c in block["exception_conditions"] if c["condition"].startswith(text))


def test_same_star_and_same_star_different_pada():
    k = K({"moon": 41}, {"moon": 52})                         # both Rohini, Taurus; padas 1 and 4
    assert k["tara"]["counts"] == {"girl_to_boy": 1, "boy_to_girl": 1} and k["tara"]["points"] == 3
    assert "same_star" in k["tara"] and k["padas"] == {"girl": 1, "boy": 4}
    assert k["nadi"]["points"] == 0 and k["bhakoot"]["points"] == 7 and k["bhakoot"]["distance"] == "1/1"
    assert cond(k["nadi"], "same star, different padas") and not cond(k["nadi"], "same star, different signs")
    assert not cond(k["nadi"], "same sign, different stars")
    assert not cond(K({"moon": 45}, {"moon": 46})["nadi"], "same star, different padas")   # same pada


def test_nadi_exceptions_same_sign_or_same_star():
    k = K({"moon": 28}, {"moon": 32})                         # Krittika in Aries and in Taurus (antya)
    assert k["nadi"]["points"] == 0 and cond(k["nadi"], "same star, different signs")
    assert k["bhakoot"]["points"] == 0 and k["bhakoot"]["dosha"] == "2/12"
    k = K({"moon": 32}, {"moon": 45})                         # Krittika and Rohini, both Taurus, both antya
    assert k["nadi"]["points"] == 0 and cond(k["nadi"], "same sign, different stars")
    assert "exceptions_not_evaluated" in k["nadi"]


def test_nadi_different_and_madhya_note():
    k = K({"moon": 0}, {"moon": 15})                          # Ashwini adi, Bharani madhya
    assert k["nadi"]["points"] == 8 and k["nadi"]["max"] == 8 and "exception_conditions" not in k["nadi"]
    k = K({"moon": 15}, {"moon": 55})                         # Bharani, Mrigashira: both madhya
    assert k["nadi"]["points"] == 0 and "worst" in k["nadi"]["note"]


def test_nadi_lists_nine_each():
    names = {v: [M.E.NAKS[i] for i in range(27) if M.NADI.get(i, "antya") == v] for v in ("adi", "madhya", "antya")}
    assert all(len(x) == 9 for x in names.values())
    assert names["antya"] == ["Krittika", "Rohini", "Ashlesha", "Magha", "Swati", "Vishakha", "UttaraAshadha",
                              "Shravana", "Revati"]


def test_bhakoot_distances():
    for boy, dist, pts in ((190, "7/7", 7), (70, "3/11", 7), (100, "4/10", 7), (40, "2/12", 0), (130, "5/9", 0),
                           (160, "6/8", 0), (220, "8/6", 0), (250, "9/5", 0), (340, "12/2", 0)):
        k = K({"moon": 10}, {"moon": boy})                    # girl Aries
        assert (k["bhakoot"]["distance"], k["bhakoot"]["points"]) == (dist, pts), boy


def test_bhakoot_even_sign_bride_sixth_shows_both_readings():
    k = K({"moon": 35}, {"moon": 185})                        # Taurus girl, Libra boy 6th
    c = next(c for c in k["bhakoot"]["exception_conditions"] if c["condition"].startswith("bride in an even"))
    assert c["holds"] and any("MCJ p342" in r for r in c["readings"]) and any("PM2 XXI.5" in r for r in c["readings"])
    k = K({"moon": 10}, {"moon": 160})                        # Aries girl (odd), Virgo boy 6th
    assert cond(k["bhakoot"], "bride in an even") is False
    k = K({"moon": 10}, {"moon": 130})                        # Aries/Leo 5/9: lords Ma, Su mutual friends
    assert cond(k["bhakoot"], "the Moon-sign lords are mutual friends") and not cond(k["bhakoot"], "the Moon-sign lords are the same")
    assert cond(k["bhakoot"], "nadi purity") is (k["nadi"]["points"] == 8)
    assert cond(k["bhakoot"], "graha maitri") and not any(c["condition"].startswith("bride in") for c in k["bhakoot"]["exception_conditions"])
    k = K({"moon": 10}, {"moon": 220})                        # Aries/Scorpio 6/8: same lord Mars
    assert cond(k["bhakoot"], "the Moon-sign lords are the same")


def test_tara_both_directions_and_kashyapa():
    k = K({"moon": 0}, {"moon": 30})                          # Ashwini -> Krittika: 3 (rem 3), back 26 (rem 8)
    t = k["tara"]
    assert t["counts"] == {"girl_to_boy": 3, "boy_to_girl": 26} and t["favourable"] == {"girl_to_boy": False, "boy_to_girl": True}
    assert t["points"] == 1.5 and t["variants"][0]["girl_to_boy_favourable"] is False
    assert K({"moon": 30}, {"moon": 0})["tara"]["favourable"] == {"girl_to_boy": True, "boy_to_girl": False}
    pts = {K({"moon": a * 40 / 3 + 1}, {"moon": b * 40 / 3 + 1})["tara"]["points"] for a in range(27) for b in range(27)}
    assert pts == {3, 1.5}                                    # counts sum to 29 (R3 §3.3): never 0


def test_graha_maitri_reproduces_mcj_chakra():
    order = "Su Mo Ma Me Ju Ve Sa".split()
    chakra = [[5, 5, 5, 4, 5, 0, 0], [5, 5, 4, 1, 4, .5, .5], [5, 4, 5, .5, 5, 3, .5], [4, 1, .5, 5, .5, 5, 4],
              [5, 4, 5, .5, 5, .5, 3], [0, .5, 3, 5, .5, 5, 5], [0, .5, .5, 4, 3, 5, 5]]   # MCJ p338 via R3 §3.5
    assert set(NATURAL) == set(order)
    assert [[M._maitri(a, b) for b in order] for a in order] == chakra
    k = K({"moon": 10}, {"moon": 190})                        # Mars and Venus: both neutral
    assert k["graha_maitri"]["points"] == 3 and k["graha_maitri"]["inputs"] == {"girl": "Ma", "boy": "Ve"}
    assert cond(k["graha_maitri"], "bhakoot gets 7")          # MC 6.33, 1/7 pair
    assert K({"moon": 70}, {"moon": 100})["graha_maitri"]["points"] == 1   # Mercury-Moon: friend + enemy
    assert "navamsa_lords" in k["graha_maitri"] and "exception_conditions" not in K({"moon": 10}, {"moon": 130})["graha_maitri"]


def test_raman_1948_partial_illustration():
    """R3 §7: Raman 1948's Mrigashira-Dhanishtha illustration (12-kuta, partial): graha maitri complete, nadi absent."""
    k = K({"moon": 55}, {"moon": 295})                        # Mrigashira in Taurus (Ve), Dhanishtha in Capricorn (Sa)
    assert k["graha_maitri"]["points"] == 5 and k["nadi"]["points"] == 0


def test_no_sum_no_verdict_and_not_computed():
    banned = ("total", "compatib", "match score", "score", "verdict", "recommend", "36")
    for a in range(0, 360, 7):
        for b in range(3, 360, 29):
            text = json.dumps(K({"moon": a}, {"moon": b})).lower()
            assert not any(w in text for w in banned), (a, b)
            assert '"points": ' in text
    k = K({"moon": 0}, {"moon": 100})
    assert set(k["not_computed"]) == {"vashya", "yoni", "gana", "varna"}
    assert all(k["not_computed"][x] for x in k["not_computed"])
    assert {k[x]["max"] for x in ("tara", "bhakoot", "graha_maitri", "nadi")} == {3, 7, 5, 8}
    assert all("not page-checked" in k[x]["source"] for x in ("tara", "bhakoot", "graha_maitri", "nadi"))


def test_facts_carries_kootas():
    out = M.facts({"moon": 10}, {"moon": 190})
    assert out["kootas"]["variant"] == "MC-Piyushadhara-Joshi1979" and "Ashtakoota" in out["not_computed"]


def test_value_words_appear_only_inside_attributed_source_readings():
    # review 2026-10-23: words like 'auspicious' or 'poison' may only quote a source, never describe the couple
    import re
    words = re.compile(r"\b(?:good|bad|auspicious|inauspicious|poison|fear|lucky|unlucky|harmon\w*)\b", re.I)

    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k not in ("readings", "variants", "note", "rule", "source")}
        return [strip(v) for v in x] if isinstance(x, list) else x
    for g in range(0, 360, 7):
        for b in (41.0, 52.0, 130.0, 250.0, 333.0):
            k = M.kootas({"moon": float(g)}, {"moon": b})
            assert not words.search(json.dumps(strip(k))), (g, b, words.findall(json.dumps(strip(k))))
