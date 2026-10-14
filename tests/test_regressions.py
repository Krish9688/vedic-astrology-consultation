# Regression tests for defects found by the final-completion council (round 1, member A). Synthetic or published data.
import datetime as dt
import os
import shutil
import sys

import pytest
import swisseph as swe

from astro import config, service as S
from astro.calc import engine as E, strength

HERE = os.path.dirname(__file__)


def test_abda_masa_match_bphs_worked_example():
    """A-1: BPHS ch. 27 (Santhanam, printed p.271): 1 Jun 1984 → abbreviated Ahargana 65295, year lord Jupiter,
    month lord Venus, Ahargana mod 7 = 6 = Friday."""
    a = strength.ahargana_from_creation(dt.date(1984, 6, 1))
    assert a % 2520 == 65295 % 2520 and a % 7 == 6
    tl = S.shadbala(S.BirthInput(date="1984-06-01", time="12:00", tz=5.5, lat=28.61, lon=77.21))["time_lords"]
    assert (tl["year"], tl["month"], tl["weekday"]) == ("Ju", "Ve", "Ve")


def test_engine_to_chart_facts_keeps_retrograde():
    """A-2: retrograde Mercury 13.2° from the Sun is inside the direct orb (14°) but outside the retrograde orb (12°)."""
    c = E.compute("2026-02-27", "18:00", 0, 51.5, -0.12, extras=False)
    inp = E.chart_facts_input(c)
    assert inp["planets"]["Me"]["retro"] is True
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import chart_facts
    me = next(line for line in chart_facts.facts(inp).splitlines() if line.lstrip("- ").startswith("Me"))
    assert "retrograde" in me and "COMBUST" not in me


def test_ketu_retrograde_follows_rahu():
    """A-9: with true nodes Rahu can be direct; Ketu moves with it."""
    p = E.positions(swe.julday(1992, 1, 2, 0.0), node="true")
    assert p["Ke"]["retro"] == p["Ra"]["retro"]


def test_zero_minute_sensitivity_is_shown():
    """A-5: 0 minutes (the most time-sensitive case) must not render as '—' (= not within 3 h)."""
    c = E.compute("1992-03-14", "09:40", 0, 51.5, -0.12, months=1)
    c["birth_time_sensitivity_minutes"] = {"Moon pada": {"earlier": 0, "later": 383}}
    assert "Moon pada: 0 earlier / 383 later" in E.render_md(c)


def test_rounding_happens_once(monkeypatch):
    """A-3: a longitude within 0.00005° below a sign edge is reported consistently (sign, degree, nakshatra, vargas)."""
    real = E.positions
    monkeypatch.setattr(E, "positions", lambda jd, node="mean": dict(real(jd, node), Mo=dict(real(jd, node)["Mo"],
                                                                                             lon=119.99996999)))
    mo = E.compute("1992-03-14", "09:40", 0, 51.5, -0.12, extras=False)["bodies"]["Mo"]
    assert (mo["sign"], mo["deg"], mo["nakshatra"], mo["pada"]) == ("Leo", 0.0, "Magha", 1) and mo["vargas"]["D1"] == "Leo"


def test_node_co_lord_advancement_from_sign_end():
    """A-11: Scorpio co-lords Mars and Ketu with equal planet counts: Ketu at 25° has advanced only 5° (PVR p.204)."""
    from astro.calc.jaimini import _lord
    sg = {"Ma": 7, "Ke": 7}
    assert _lord(7, sg, {"Ma": 10.0, "Ke": 25.0}) == "Ma"
    assert _lord(7, sg, {"Ma": 3.0, "Ke": 25.0}) == "Ke"


def test_range_flags_and_refusals():
    """A-12/A-17: polar latitude and pre-1582 dates are flagged; years after 2999 and the poles are refused."""
    import pytest
    flags = E.compute("1550-06-01", "12:00", 0, 70.0, 20.0, extras=False)["meta"]["flags"]
    assert any("polar" in f for f in flags) and any("1582" in f for f in flags)
    assert E.compute("1992-03-14", "09:40", 0, 51.5, -0.12, extras=False)["meta"]["flags"] == []
    for bad in (dict(date="3001-01-01"), dict(lat=90.0)):
        with pytest.raises(ValueError):
            S.BirthInput(**(dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12) | bad))


def test_lal_kitab_without_kb_says_so(tmp_path):
    """B2 (2026-10-12): without scripts/lal_kitab.py (the public edition) chart_facts prints no Lal Kitab part and
    says so, and the method file tells the assistant to decline Lal Kitab analysis."""
    import importlib.util
    skill = config.load().skill_dir
    (tmp_path / "scripts").mkdir()
    shutil.copy(os.path.join(skill, "scripts", "chart_facts.py"), tmp_path / "scripts" / "chart_facts.py")
    spec = importlib.util.spec_from_file_location("cf_nokb", tmp_path / "scripts" / "chart_facts.py")
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    out = cf.facts(E.chart_facts_input(E.compute("1992-03-14", "09:40", 0, 51.5, -0.12, extras=False)))
    assert "# Lal Kitab: not part of this edition" in out and "Lal Kitab fixed-Aries" not in out
    assert "# Parashari D1" in out
    assert "does not provide Lal Kitab analysis" in open(os.path.join(skill, "references", "lal-kitab-method.md")).read()


def test_transit_sign_aspects_and_local_ingress_dates():
    """D1: whole-sign graha drishti windows for transiting Jupiter/Saturn follow the ingress list exactly.
    A-8: ingress dates are local dates of the change (Jupiter enters Cancer 2026-06-01 ~20:20 UT = 2026-06-02 IST)."""
    c = E.compute("1992-03-14", "09:40", 5.5, 28.61, 77.21, on="2026-01-01", months=24)
    ju_cancer = [r for r in c["ingresses"] if r["planet"] == "Ju" and r["to"] == "Cancer"]
    assert ju_cancer and ju_cancer[0]["date"] == "2026-06-02"
    asc, moon = E.SIGNS.index(c["bodies"]["Asc"]["sign"]), E.SIGNS.index(c["bodies"]["Mo"]["sign"])
    for p, asp in E.TRANSIT_ASPECTS.items():
        rows = [r for r in c["transit_sign_aspects"] if r["planet"] == p]
        assert rows[0]["from"] == "2026-01-01" and all(a["to"] == b["from"] for a, b in zip(rows, rows[1:]))
        assert [r["to"] for r in rows[:-1]] == [r["date"] for r in c["ingresses"] if r["planet"] == p]
        for r in rows:
            s = E.SIGNS.index(r["sign"])
            signs = [s] + [(s + k - 1) % 12 for k in asp]
            assert r["houses_from_lagna"] == [(x - asc) % 12 + 1 for x in signs]
            assert r["houses_from_moon"] == [(x - moon) % 12 + 1 for x in signs]
    assert "never a promise" in c["meta"]["transit_aspects"]


def test_consultation_context_carries_derived_facts():
    """D2/B-11: MCP/REST clients get the skill's chart_facts output (one implementation) and the transit windows."""
    ctx = S.consultation_context("When will my career change?", S.BirthInput(date="1992-03-14", time="09:40", tz=0,
                                                                            lat=51.5, lon=-0.12))
    d = ctx["derived_facts"]
    assert "# Parashari D1" in d and ctx["facts"]["transit_sign_aspects"]
    assert ("Lal Kitab fixed-Aries chart" in d) == _private_edition() and ("not part of this edition" in d) != _private_edition()


def test_retrieval_text_fixes():
    """C-2/C-12: OCR'd ordinals are normalised for the index; transliteration variants are searched together."""
    sys.path.insert(0, os.path.join(HERE, "..", "tools"))
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    from build_index import normalise
    from paths import fts_terms
    assert normalise("7th lord in the l2th, llth or l0th; the lst house; still") == \
        "7th lord in the 12th, 11th or 10th; the 1st house; still"
    assert fts_terms("Vimshottari dasa") == ["(vimshottari OR vimsottari)", "dasa"]


@pytest.mark.parametrize("script", ["chart_facts.py", "life_lint.py", "render_report.py"])
def test_skill_scripts_answer_help(script):
    # AUD-09: `--help` was opened as a file path (FileNotFoundError) instead of printing usage
    import subprocess
    path = os.path.join(config.load().skill_dir, "scripts", script)
    r = subprocess.run([sys.executable, path, "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "usage" in r.stdout.lower(), r.stderr[-300:]



def _private_edition():
    return os.path.exists(os.path.join(config.load().skill_dir, "scripts", "lal_kitab.py"))


def _chart_facts():
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import chart_facts as cf
    return cf


def test_chart_facts_varga_matches_engine_at_exact_boundaries():
    # council 2026-10-11 (R3 M1): exactly 10° / 20° fell one navamsa short and disagreed with the engine
    cf = _chart_facts()
    for s in range(12):
        for d in (10 / 3, 20 / 3, 10.0, 20.0, 3.0, 15.0, 27.0):
            for n in (9, 10):
                assert cf.varga(s, d, n) == E.varga(s * 30 + d, n), (s, d, n)



@pytest.mark.parametrize("text,flag", [
    ("Your father will not suffer; he may pass away in 2031.", True),       # negation in another clause (R3 M3)
    ("Your child may die young according to this chart.", True),
    ("This placement indicates cancer in later life.", True),
    ("Your houses show Cancer rising, a protective manner.", False),   # the sign, not the illness (council 5 R5 C1)
    ("You should stop taking your medication during this period.", True),
    ("This is not medical advice; please do not stop your medication without your doctor.", False),
    ("The Moon in Cancer gives a caring nature.", False),
    ("I cannot predict death or lifespan.", False),
    ("I can't, and won't, predict early death.", False),                    # refusal across commas (review 2026-10-11)
    ("This frustration may die down by spring.", False),
    ("Saturn shows a stroke of luck in 2027.", False),
])
def test_safety_lint_catches_death_diagnosis_and_medication_advice(text, flag):
    # council 2026-10-11 (R3/R6): the lint is a narrow backstop; these are the confirmed holes it must now close
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import life_lint
    assert any(i.startswith("SAFETY") for i in life_lint.lint(text)["issues"]) is flag, life_lint.lint(text)["issues"]
