# P4-1 / P4-2 acceptance: a positive, a negative and a boundary fixture for every candidate-yoga and Kuja definition
# id in scripts/chart_facts.py (references/yoga-definitions.md), each checking the citation field; and no result
# words in any candidate or Kuja line for the 52 synthetic Lal Kitab golden inputs. Synthetic charts only.
import os
import random
import re
import sys

import pytest

from astro import config


def _cf():
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import chart_facts
    return chart_facts


def _chart(asc, pl):
    a = {"sign": asc[0], "deg": asc[1]} if isinstance(asc, tuple) else {"sign": asc}
    return {"asc": a, "planets": {p: ({"sign": v[0], "deg": v[1]} if isinstance(v, tuple) else {"sign": v})
                                  for p, v in pl.items()}}


def _rows(asc, pl, show_all=False):
    cf = _cf()
    D = cf.derive(_chart(asc, pl))
    return {r[0]: r for r in cf.candidates(D, show_all) + cf.kuja(D)}


CITE = re.compile(r"(source map|BPHS|LOL|PD|HJH|CRUX|BJ).*not page-checked")
A = "Aries"
# (id, kind, asc, planets, expected): expected True / False / None (undetermined) / "absent" (the line is not printed).
# Boundaries sit at sign cusps (29.99 deg vs 0.0 deg), kendra edges, the combustion orb, the 180-degree Moon phase,
# the debilitation sign's last degree, the navamsa edge and Mercury's benefic status.
CASES = [
    ("GK-BPHS36", "pos", A, dict(Su=("Leo", 15), Mo=("Cancer", 10), Ju=("Cancer", 5), Ve=("Cancer", 8)), True),
    ("GK-BPHS36", "neg", A, dict(Su=("Leo", 15), Mo=("Cancer", 10), Ju=("Capricorn", 5), Ve=("Capricorn", 8)), False),
    ("GK-BPHS36", "bnd", A, dict(Su=("Cancer", 16.0), Mo=("Cancer", 10), Ju=("Cancer", 5), Ve=("Cancer", 20)), False),
    ("GK-BPHS36", "bnd", A, dict(Su=("Cancer", 16.5), Mo=("Cancer", 10), Ju=("Cancer", 5), Ve=("Cancer", 20)), True),
    ("KESARI-LOOSE", "pos", A, dict(Mo="Cancer", Ju="Libra"), True),
    ("KESARI-LOOSE", "neg", A, dict(Mo="Cancer", Ju="Leo"), False),
    ("KESARI-LOOSE", "bnd", A, dict(Mo="Cancer", Ju=("Libra", 0.0)), True),
    ("KESARI-LOOSE", "bnd", A, dict(Mo="Cancer", Ju=("Virgo", 29.99)), False),
    ("KEM-BARE", "pos", A, dict(Mo="Leo", Ma="Taurus", Me="Sagittarius", Ju="Aquarius", Ve="Taurus", Sa="Sagittarius"), True),
    ("KEM-BARE", "neg", A, dict(Mo="Leo", Me="Virgo"), False),
    ("KEM-BARE", "bnd", A, dict(Mo="Leo", Su="Virgo", Ra="Cancer", Ke="Capricorn", Me=("Leo", 29.99)), True),
    ("KEM-BARE", "bnd", A, dict(Mo="Leo", Su="Virgo", Ra="Cancer", Ke="Capricorn", Me=("Virgo", 0.0)), False),
    ("KEM-BPHS", "pos", A, dict(Mo="Leo", Ma="Taurus", Me="Sagittarius", Ju="Aquarius", Ve="Taurus", Sa="Sagittarius"), True),
    ("KEM-BPHS", "neg", A, dict(Mo="Leo", Ma="Taurus", Me="Sagittarius", Ju="Capricorn", Ve="Taurus", Sa="Sagittarius"), False),
    ("KEM-BPHS", "bnd", A, dict(Mo="Leo", Ju=("Sagittarius", 29.99)), True),
    ("KEM-BPHS", "bnd", A, dict(Mo="Leo", Ju=("Capricorn", 0.0)), False),
    ("PMP-Ju-BPHS", "pos", A, dict(Ju="Cancer"), True),
    ("PMP-Ma-BPHS", "pos", A, dict(Ma="Capricorn"), True),
    ("PMP-Me-BPHS", "pos", "Gemini", dict(Me="Virgo"), True),
    ("PMP-Ve-BPHS", "pos", "Gemini", dict(Ve="Pisces"), True),
    ("PMP-Sa-BPHS", "pos", A, dict(Sa="Libra"), True),
    ("PMP-Ju-BPHS", "neg", "Gemini", dict(Ju="Cancer"), False),
    ("PMP-Ju-BPHS", "bnd", "Virgo", dict(Ju=("Sagittarius", 0.0)), True),
    ("PMP-Ju-BPHS", "bnd", "Virgo", dict(Ju=("Scorpio", 29.99)), "absent"),
    ("PMP-Ju-LOL", "pos", "Scorpio", dict(Ju="Cancer"), True),
    ("PMP-Ju-LOL", "neg", "Gemini", dict(Ju="Cancer"), False),
    ("PMP-Ju-LOL", "bnd", "Leo", dict(Ju=("Sagittarius", 0.0)), True),
    ("PMP-Ju-LOL", "bnd", "Leo", dict(Ju=("Scorpio", 29.99)), "absent"),
    ("RAJA-KK-JuMo", "pos", A, dict(Ju="Cancer", Mo="Cancer"), True),
    ("RAJA-KK-JuMo", "neg", A, dict(Ju="Virgo", Mo="Virgo"), "absent"),
    ("RAJA-KK-JuSa", "bnd", A, dict(Ju="Aries", Sa="Libra"), True),
    ("RAJA-KK-JuSa", "bnd", A, dict(Ju="Aries", Sa="Leo"), "absent"),
    ("RAJA-KKP-Ju", "pos", A, dict(Ju="Cancer"), True),
    ("RAJA-KKP-Ju", "neg", A, dict(Ju="Gemini"), "absent"),
    ("RAJA-KKP-Mo", "bnd", A, dict(Mo=("Leo", 0.0)), True),
    ("RAJA-KKP-Mo", "bnd", A, dict(Mo=("Aries", 29.99)), "absent"),
    ("KUJA-BPHS80", "pos", A, dict(Ma="Libra", Ju="Taurus"), True),
    ("KUJA-BPHS80", "neg", A, dict(Ma="Libra", Ju="Aquarius"), False),
    ("KUJA-BPHS80", "bnd", A, dict(Ma=("Pisces", 29.99)), True),
    ("KUJA-BPHS80", "bnd", A, dict(Ma=("Aries", 0.0)), False),
    ("KUJA-POPULAR", "pos", A, dict(Ma="Libra"), True),
    ("KUJA-POPULAR", "neg", A, dict(Ma="Leo"), False),
    ("KUJA-POPULAR", "bnd", A, dict(Ma=("Cancer", 0.0)), True),
    ("KUJA-POPULAR", "bnd", A, dict(Ma=("Gemini", 29.99)), False),
    ("KUJA-PD11.3", "pos", A, dict(Ma="Libra"), True),
    ("KUJA-PD11.3", "neg", A, dict(Ma="Leo"), False),
    ("KUJA-PD11.3", "bnd", ("Libra", 3.3), dict(Ma="Gemini"), True),
    ("KUJA-PD11.3", "bnd", ("Libra", 3.34), dict(Ma="Gemini"), False),
    ("KUJA-PD11.3", "bnd", "Libra", dict(Ma="Gemini"), None),
    ("KUJA-HJH2", "pos", A, dict(Ma="Taurus"), True),
    ("KUJA-HJH2", "neg", A, dict(Ma="Aries"), False),
    ("KUJA-HJH2", "bnd", A, dict(Ma=("Taurus", 0.0)), True),
    ("KUJA-HJH2", "bnd", A, dict(Ma=("Aries", 29.99)), False),
    ("SUNAPHA-BPHS37", "pos", A, dict(Mo="Leo", Me="Virgo"), True),
    ("SUNAPHA-BPHS37", "neg", A, dict(Mo="Leo", Me="Virgo", Ve="Cancer"), False),
    ("SUNAPHA-BPHS37", "bnd", A, dict(Mo="Leo", Su="Virgo", Ra="Virgo", Me=("Virgo", 0.0)), True),
    ("SUNAPHA-BPHS37", "bnd", A, dict(Mo="Leo", Su="Virgo", Ra="Virgo", Me=("Leo", 29.99)), False),
    ("ANAPHA-BPHS37", "pos", A, dict(Mo="Leo", Ve="Cancer"), True),
    ("ANAPHA-BPHS37", "neg", A, dict(Mo="Leo", Me="Virgo"), False),
    ("ANAPHA-BPHS37", "bnd", A, dict(Mo="Leo", Ve=("Cancer", 29.99)), True),
    ("ANAPHA-BPHS37", "bnd", A, dict(Mo="Leo", Ve=("Leo", 0.0)), False),
    ("DURADHARA-BPHS37", "pos", A, dict(Mo="Leo", Me="Virgo", Ve="Cancer"), True),
    ("DURADHARA-BPHS37", "neg", A, dict(Mo="Leo", Me="Virgo"), False),
    ("DURADHARA-BPHS37", "bnd", A, dict(Mo="Leo", Me="Virgo", Ve=("Cancer", 29.99)), True),
    ("DURADHARA-BPHS37", "bnd", A, dict(Mo="Leo", Me="Virgo", Ve=("Leo", 0.0)), False),
    ("VESI-BPHS38", "pos", A, dict(Su="Leo", Sa="Virgo"), True),
    ("VESI-BPHS38", "neg", A, dict(Su="Leo", Sa="Virgo", Ma="Cancer"), False),
    ("VESI-BPHS38", "bnd", A, dict(Su="Leo", Mo="Virgo", Sa=("Virgo", 0.0)), True),
    ("VESI-BPHS38", "bnd", A, dict(Su="Leo", Mo="Virgo", Sa=("Leo", 29.99)), False),
    ("VOSI-BPHS38", "pos", A, dict(Su="Leo", Ma="Cancer"), True),
    ("VOSI-BPHS38", "neg", A, dict(Su="Leo", Sa="Virgo"), False),
    ("VOSI-BPHS38", "bnd", A, dict(Su="Leo", Ma=("Cancer", 29.99)), True),
    ("VOSI-BPHS38", "bnd", A, dict(Su="Leo", Ma=("Leo", 0.0)), False),
    ("UBHAYACHARI-BPHS38", "pos", A, dict(Su="Leo", Sa="Virgo", Ma="Cancer"), True),
    ("UBHAYACHARI-BPHS38", "neg", A, dict(Su="Leo", Sa="Virgo"), False),
    ("UBHAYACHARI-BPHS38", "bnd", A, dict(Su="Leo", Sa="Virgo", Ma=("Cancer", 29.99)), True),
    ("UBHAYACHARI-BPHS38", "bnd", A, dict(Su="Leo", Sa="Virgo", Ma=("Leo", 0.0)), False),
    ("VESI-PD6", "pos", A, dict(Su="Leo", Ju="Virgo"), True),
    ("VESI-PD6", "neg", A, dict(Su="Leo", Sa="Virgo"), False),
    ("VESI-PD6", "bnd", A, dict(Su="Leo", Me="Virgo"), True),                 # Mercury alone: benefic
    ("VESI-PD6", "bnd", A, dict(Su="Leo", Me="Virgo", Sa="Virgo"), False),    # Mercury with a malefic: malefic
    ("VOSI-PD6", "pos", A, dict(Su="Leo", Ve="Cancer"), True),
    ("VOSI-PD6", "neg", A, dict(Su="Leo", Ma="Cancer"), False),
    ("VOSI-PD6", "bnd", A, dict(Su="Leo", Ve=("Cancer", 29.99)), True),
    ("VOSI-PD6", "bnd", A, dict(Su="Leo", Ve=("Leo", 0.0)), False),
    ("UBHAYACHARI-PD6", "pos", A, dict(Su="Leo", Ju="Virgo", Ve="Cancer"), True),
    ("UBHAYACHARI-PD6", "neg", A, dict(Su="Leo", Ju="Virgo", Ma="Cancer"), False),
    ("UBHAYACHARI-PD6", "bnd", A, dict(Su="Leo", Ju="Virgo", Ve=("Cancer", 29.99)), True),
    ("UBHAYACHARI-PD6", "bnd", A, dict(Su="Leo", Ju="Virgo", Ve=("Leo", 0.0)), False),
    ("ADHI-BPHS37", "pos", A, dict(Mo="Aries", Ju="Libra"), True),
    ("ADHI-BPHS37", "neg", A, dict(Mo="Aries", Ju="Leo"), False),
    ("ADHI-BPHS37", "bnd", A, dict(Mo="Aries", Ju=("Virgo", 0.0)), True),
    ("ADHI-BPHS37", "bnd", A, dict(Mo="Aries", Ju=("Leo", 29.99)), False),
    ("ADHI-PD6", "pos", "Leo", dict(Mo="Aries", Ju="Capricorn"), True),        # 6th from the lagna only
    ("ADHI-PD6", "neg", A, dict(Mo="Aries", Ju="Leo"), False),
    ("ADHI-PD6", "bnd", A, dict(Su=("Aries", 11.0), Mo=("Libra", 10.0)), True),   # elongation 179: waxing, benefic
    ("ADHI-PD6", "bnd", A, dict(Su=("Aries", 9.0), Mo=("Libra", 10.0)), False),   # elongation 181: waning, malefic
    ("AMALA-BPHS36", "pos", A, dict(Ju="Capricorn"), True),
    ("AMALA-BPHS36", "neg", A, dict(Ju="Capricorn", Sa="Capricorn"), False),
    ("AMALA-BPHS36", "bnd", A, dict(Ju=("Capricorn", 0.0)), True),
    ("AMALA-BPHS36", "bnd", A, dict(Ju=("Sagittarius", 29.99)), False),
    ("AMALA-PD6", "pos", A, dict(Ju="Capricorn", Sa="Capricorn"), True),
    ("AMALA-PD6", "neg", A, dict(Sa="Capricorn"), False),
    ("AMALA-PD6", "bnd", A, dict(Mo="Leo", Ve=("Taurus", 29.99)), True),       # 10th from the Moon
    ("AMALA-PD6", "bnd", A, dict(Mo="Leo", Ve=("Gemini", 0.0)), False),
    ("BUDHADITYA-LOL", "pos", A, dict(Su=("Leo", 10), Me=("Leo", 20)), True),
    ("BUDHADITYA-LOL", "neg", A, dict(Su="Leo", Me="Virgo"), False),
    ("BUDHADITYA-LOL", "bnd", A, dict(Su=("Leo", 29.0), Me=("Leo", 29.99)), True),
    ("BUDHADITYA-LOL", "bnd", A, dict(Su=("Leo", 29.0), Me=("Virgo", 0.0)), False),
    ("LAKSHMI-BPHS36", "pos", A, dict(Ju="Cancer"), True),
    ("LAKSHMI-BPHS36", "neg", A, dict(Ju="Pisces"), False),
    ("LAKSHMI-BPHS36", "bnd", A, dict(Ju=("Cancer", 0.0)), True),
    ("LAKSHMI-BPHS36", "bnd", A, dict(Ju=("Gemini", 29.99)), False),
    ("LAKSHMI-PD6", "pos", A, dict(Ju="Sagittarius", Ve="Libra"), True),
    ("LAKSHMI-PD6", "neg", A, dict(Ju="Sagittarius", Ve="Virgo"), False),
    ("LAKSHMI-PD6", "bnd", A, dict(Ju="Sagittarius", Ve=("Libra", 0.0)), True),
    ("LAKSHMI-PD6", "bnd", A, dict(Ju="Sagittarius", Ve=("Virgo", 29.99)), False),
    ("VIPARITA-LOL", "pos", A, dict(Me="Scorpio", Ju="Virgo"), True),
    ("VIPARITA-LOL", "neg", A, dict(Me="Scorpio", Ma="Virgo"), False),         # 6th-8th exchange
    ("VIPARITA-LOL", "bnd", A, dict(Me="Scorpio", Ju=("Virgo", 0.0)), True),
    ("VIPARITA-LOL", "bnd", A, dict(Me="Scorpio", Ju=("Leo", 29.99)), False),
    ("VIPARITA-HJH", "pos", A, dict(Me="Scorpio"), True),
    ("VIPARITA-HJH", "neg", A, dict(Me="Virgo"), False),
    ("VIPARITA-HJH", "bnd", A, dict(Ju=("Gemini", 0.0)), True),                # 12th lord in the 3rd
    ("VIPARITA-HJH", "bnd", A, dict(Ju=("Taurus", 29.99)), False),
    ("VIPARITA-CRUX", "pos", A, dict(Ma="Virgo", Ju="Virgo"), True),
    ("VIPARITA-CRUX", "neg", A, dict(Ma="Leo", Ju="Leo"), False),
    ("VIPARITA-CRUX", "bnd", A, dict(Ma="Virgo", Ju=("Virgo", 29.99)), True),
    ("VIPARITA-CRUX", "bnd", A, dict(Ma="Virgo", Ju=("Libra", 0.0)), False),
    # neechabhanga, Venus debilitated in Virgo (H6 from Aries): sign lord Mercury, exaltation-sign lord Jupiter
    ("NB-DISP-Ve", "pos", A, dict(Ve="Virgo", Me="Cancer"), True),
    ("NB-DISP-Ve", "neg", A, dict(Ve="Virgo", Me="Leo", Mo="Aries"), False),
    ("NB-DISP-Ve", "bnd", A, dict(Ve="Virgo", Me=("Cancer", 0.0), Mo="Aries"), True),
    ("NB-DISP-Ve", "bnd", A, dict(Ve="Virgo", Me=("Gemini", 29.99), Mo="Aries"), False),
    ("NB-DISP-Ma", "bnd", A, dict(Ma="Cancer", Mo="Taurus"), None),            # the Moon from itself: undetermined
    ("NB-EXL-Ve", "pos", A, dict(Ve="Virgo", Ju="Capricorn"), True),
    ("NB-EXL-Ve", "neg", A, dict(Ve="Virgo", Ju="Leo", Mo="Aries"), False),
    ("NB-EXL-Ve", "bnd", A, dict(Ve="Virgo", Ju=("Capricorn", 0.0), Mo="Aries"), True),
    ("NB-EXL-Ve", "bnd", A, dict(Ve="Virgo", Ju=("Sagittarius", 29.99), Mo="Aries"), False),
    ("NB-ASP-Ve", "pos", A, dict(Ve="Virgo", Me="Pisces"), True),
    ("NB-ASP-Ve", "neg", A, dict(Ve="Virgo", Me="Virgo"), False),              # with it is not an aspect
    ("NB-ASP-Ve", "bnd", A, dict(Ve="Virgo", Me=("Pisces", 0.0)), True),
    ("NB-ASP-Ve", "bnd", A, dict(Ve="Virgo", Me=("Aquarius", 29.99)), False),
    ("NB-EXP-Sa", "pos", A, dict(Sa="Aries", Su="Capricorn"), True),           # the Sun is exalted in Aries
    ("NB-EXP-Sa", "neg", A, dict(Sa="Aries", Su="Leo", Mo="Aries"), False),
    ("NB-EXP-Sa", "bnd", A, dict(Sa="Aries", Su=("Capricorn", 0.0), Mo="Aries"), True),
    ("NB-EXP-Sa", "bnd", A, dict(Sa="Aries", Su=("Sagittarius", 29.99), Mo="Aries"), False),
    ("NB-EXP-Mo", "neg", A, dict(Mo="Scorpio", Su="Aries"), False),            # no planet is exalted in Scorpio
    ("NB-MUT-Ve", "pos", A, dict(Ve="Virgo", Me="Gemini", Ju="Virgo"), True),
    ("NB-MUT-Ve", "neg", A, dict(Ve="Virgo", Me="Gemini", Ju="Leo"), False),
    ("NB-MUT-Ve", "bnd", A, dict(Ve="Virgo", Me="Gemini", Ju=("Virgo", 29.99)), True),
    ("NB-MUT-Ve", "bnd", A, dict(Ve="Virgo", Me="Gemini", Ju=("Libra", 0.0)), False),
    ("NB-SELF-Ve", "pos", A, dict(Ve="Virgo", Mo="Gemini"), True),
    ("NB-SELF-Ve", "neg", A, dict(Ve="Virgo", Mo="Aries"), False),
    ("NB-SELF-Ve", "bnd", "Gemini", dict(Ve=("Virgo", 29.99)), True),          # last degree of the debilitation sign
    ("NB-SELF-Ve", "bnd", "Gemini", dict(Ve=("Libra", 0.0)), "absent"),        # own sign: no neechabhanga lines
    ("NB-D9-Ve", "pos", A, dict(Ve=("Virgo", 8.0)), True),                     # navamsa Pisces
    ("NB-D9-Ve", "neg", A, dict(Ve=("Virgo", 1.0)), False),
    ("NB-D9-Ve", "bnd", A, dict(Ve=("Virgo", 6.67)), True),
    ("NB-D9-Ve", "bnd", A, dict(Ve=("Virgo", 6.66)), False),
    ("NB-D9-Ve", "bnd", A, dict(Ve="Virgo"), None),
]


def _family(rid):
    return _cf().family(rid)


@pytest.mark.parametrize("rid,kind,asc,pl,want", CASES, ids=[f"{c[0]}-{c[1]}-{i}" for i, c in enumerate(CASES)])
def test_definition_fixture(rid, kind, asc, pl, want):
    shown = _rows(asc, pl)
    if want == "absent":
        assert rid not in shown, shown.get(rid)
        return
    row = _rows(asc, pl, show_all=True)[rid]
    assert row[2] is want, row
    assert CITE.search(row[4]), row[4]                          # citation field: a source and "not page-checked"
    if want is not False:                                        # a holding or undetermined line is always printed
        assert rid in shown
    assert _cf().BASE_RATE.get(_family(rid)), rid               # every definition carries a base rate


def test_every_definition_has_positive_negative_and_boundary_fixtures():
    cf = _cf()
    kinds = {}
    for rid, kind, *_ in CASES:
        kinds.setdefault(cf.family(rid), set()).add(kind)
    assert set(kinds) == set(cf.BASE_RATE), set(kinds) ^ set(cf.BASE_RATE)
    assert all(k == {"pos", "neg", "bnd"} for k in kinds.values()), {f: k for f, k in kinds.items() if k != {"pos", "neg", "bnd"}}


def test_failing_variant_prints_next_to_a_holding_one():
    """A yoga's variants print together once one holds, so the disagreement is visible (Saturn alone in the 2nd from
    the Sun: Vesi by BPHS 38, not by PD VI.8, which counts benefics)."""
    r = _rows(A, dict(Su="Leo", Sa="Virgo"))
    assert r["VESI-BPHS38"][2] is True and r["VESI-PD6"][2] is False
    assert "VOSI-BPHS38" not in r and "SUNAPHA-BPHS37" not in r


def test_neechabhanga_is_clause_by_clause_never_one_flag():
    r = _rows(A, dict(Ve="Virgo", Me="Cancer", Mo="Aries"))
    assert {k for k in r if k.startswith("NB-")} == {f"NB-{c}-Ve" for c in ("DISP", "EXL", "ASP", "EXP", "MUT", "SELF", "D9")}
    assert not any("cancelled" in x[1].lower() or "cancelled" in x[3].lower() for k, x in r.items() if k.startswith("NB-"))


# 52 synthetic inputs of the Lal Kitab golden test (tests/test_lal_kitab.py, seed 20261018): the same signs,
# repeated here because that file is private-only; the Lal Kitab house maps are left out (candidates do not use them).
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
         "Aquarius", "Pisces"]
_BASE = dict(Su=1, Mo=2, Ma=3, Me=4, Ju=5, Ve=6, Sa=9, Ra=11, Ke=5)
_TARGETED = [dict(_BASE, Ma=8), dict(_BASE, Sa=11), dict(_BASE, Sa=5), dict(_BASE, Ra=1, Ke=7), dict(_BASE, Ke=2, Ra=8),
             dict(_BASE, Ra=2, Ke=8), dict(_BASE, Ke=1, Ra=7), dict(_BASE, Ra=7, Ke=1), dict(_BASE, Ra=12, Ke=6),
             dict(_BASE, Su=10, Sa=10), dict(_BASE, Ju=10), dict(_BASE, Ve=7, Sa=3)]


def _golden_inputs():
    rnd, charts = random.Random(20261018), []
    for i in range(40):
        pl = {p: {"sign": rnd.choice(SIGNS)} for p in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra")}
        pl["Ke"] = {"sign": SIGNS[(SIGNS.index(pl["Ra"]["sign"]) + 6) % 12]}
        ch = {"asc": {"sign": rnd.choice(SIGNS)}, "planets": pl}
        if i % 8 == 7:
            rnd.randint(1, 12)                                   # keep the private generator's random stream
        charts.append(ch)
    return charts + [{"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[h - 1]} for p, h in t.items()}}
                     for t in _TARGETED]


RESULT_WORDS = re.compile(r"(?i)\b(fame|famous|king|kings|kingly|royal|wealth\w*|rich|riches|guarantee\w*|prosper\w*|"
                          r"success\w*|fortun\w*|widow\w*|death|dies?|poverty|penury|ruler|minister|millionaire|"
                          r"certain(ly)?|doom\w*|destin\w*)\b")


def test_golden_inputs_match_the_private_generator():
    path = os.path.join(os.path.dirname(__file__), "test_lal_kitab.py")
    if not os.path.exists(path):
        pytest.skip("public edition: no Lal Kitab golden test")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_lk_private", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    theirs = [{"asc": c["asc"], "planets": c["planets"]} for c in mod._golden_charts().values()]
    assert theirs == _golden_inputs() and len(theirs) == 52


def test_no_result_words_in_candidate_or_kuja_lines_for_the_52_golden_inputs():
    cf = _cf()
    for ch in _golden_inputs():
        D = cf.derive(ch)
        for rid, label, holds, detail, src in cf.candidates(D, show_all=True) + cf.kuja(D):
            text = f"{label} {detail} {src}"
            assert not RESULT_WORDS.search(text), (rid, RESULT_WORDS.search(text).group(), text)
        sec = cf.facts(ch).split("# Candidate yogas")[1].split("\nDispositor chains")[0]
        assert not RESULT_WORDS.search(sec), RESULT_WORDS.search(sec).group()
