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



@pytest.mark.parametrize("module,desc,expect", [
    ("raise ImportError('broken')", "private", "failed to load: ImportError: broken"),
    ("x = 1", "private", "no section()/selftest()"),
    ("def selftest(f):\n    pass\ndef section(c, h, out, W, A, N):\n    W('# Lal Kitab partial')\n    raise KeyError('bad')",
     "private", "the Lal Kitab block failed (KeyError"),
    ("def selftest(f):\n    pass\ndef section(c, h, out, W, A, N):\n    W('# Lal Kitab LEAK')", "public", "ignored: this skill folder is the public edition"),
])
def test_chart_facts_survives_an_unusable_lal_kitab_module(tmp_path, module, desc, expect):
    """v3.6.2 (council 5 R5 C3 / R4 S3): a broken, stale or leftover lal_kitab.py never crashes chart_facts, never
    leaves partial Lal Kitab lines, never prints Lal Kitab output in a public skill folder; Parashari facts unaffected."""
    import importlib.util
    skill = config.load().skill_dir
    (tmp_path / "scripts").mkdir()
    shutil.copy(os.path.join(skill, "scripts", "chart_facts.py"), tmp_path / "scripts" / "chart_facts.py")
    (tmp_path / "scripts" / "lal_kitab.py").write_text(module + "\n")
    text = "Lal Kitab is not part of this edition." if desc == "public" else "Parashari/Vedic astrology and Lal Kitab."
    (tmp_path / "SKILL.md").write_text(f"---\nname: x\ndescription: Consultation ... {text}\n---\n")
    spec = importlib.util.spec_from_file_location("cf_lk_" + desc, tmp_path / "scripts" / "chart_facts.py")
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    ch = E.chart_facts_input(E.compute("1992-03-14", "09:40", 0, 51.5, -0.12, extras=False))
    out = cf.facts(ch)
    assert expect in out and "# Parashari D1" in out, out[-400:]
    assert "partial" not in out and "LEAK" not in out

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
    ("Your Putrakaraka is Venus in the Jaimini scheme.", False),      # a Jaimini term, not a progeny forecast (R7-7)
    ("You should stop taking your medication during this period.", True),
    ("This is not medical advice; please do not stop your medication without your doctor.", False),
    ("The Moon in Cancer gives a caring nature.", False),
    ("I cannot predict death or lifespan.", False),
    ("I can't, and won't, predict early death.", False),                    # refusal across commas (review 2026-10-11)
    ("This frustration may die down by spring.", False),
    ("Saturn shows a stroke of luck in 2027.", False),
    # council 5 R7-2 (v3.6.2): verdict negations are not excuses; new topic groups; disclaimers stay clean
    ("You cannot conceive naturally.", True),
    ("You will not be able to conceive.", True),
    ("You can't get pregnant before 2030.", True),
    ("You will never have children.", True),
    ("Your father will not survive this period.", True),
    ("You won't live past 60.", True),
    ("Your marriage will end in divorce by 2028.", True),
    ("You are likely to separate from your partner next year.", True),
    ("Your husband is cheating on you; Venus with Rahu shows infidelity.", True),
    ("With this Saturn period, ending your life may feel like the only way out.", True),
    ("You will lose all your money in the Rahu period, so sell your house now.", True),
    ("Put all your savings into gold this year.", True),
    ("There is no doubt you will have a baby in 2027.", True),
    ("If you are having thoughts of harming yourself, please contact a crisis line or a doctor now.", False),
    ("I won't say whether your marriage will end in divorce; a chart cannot tell that.", False),
    ("No infidelity or divorce claims; the partner's mind is out of scope.", False),
    ("A birth chart can't time conception or say anything reliable about fertility.", False),
    ("Lifespan is something I cannot predict.", False),
    ("For money decisions, a financial adviser is the right person to ask.", False),
])
def test_safety_lint_catches_death_diagnosis_and_medication_advice(text, flag):
    # council 2026-10-11 (R3/R6): the lint is a narrow backstop; these are the confirmed holes it must now close
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import life_lint
    assert any(i.startswith("SAFETY") for i in life_lint.lint(text)["issues"]) is flag, life_lint.lint(text)["issues"]


def test_dasha_lord_follows_reported_nakshatra(monkeypatch):
    """QA-F3: a Moon at 26.666664° rounds to 26.6667° (Krittika) in the bodies table; the dasha must start from the same
    value (Sun), not from the unrounded longitude (Bharani, Venus)."""
    real = E.positions

    def moon_at_edge(jd, node="mean"):
        p = real(jd, node)
        p["Mo"] = {**p["Mo"], "lon": 26.666664}
        return p
    monkeypatch.setattr(E, "positions", moon_at_edge)
    c = E.compute("2000-01-01", "12:00", 0, 28.61, 77.21, extras=False)
    lords = dict(zip(E.NAKS, [d for d, _ in E.DASA] * 3))
    assert c["bodies"]["Mo"]["nakshatra"] == "Krittika"
    assert c["vimshottari"][0]["lord"] == lords["Krittika"] == "Su"


def test_kg_contradictions_respect_system():
    """AI-F3: a named non-Lal-Kitab system must not get Lal Kitab disputes (and a Lal Kitab question gets only those).
    The filter is private-edition code: the public graph carries no Lal Kitab disputes."""
    if not os.path.exists(os.path.join(config.load().skill_dir, "scripts", "lal_kitab.py")):
        pytest.skip("public edition")
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import kg
    from collections import defaultdict
    N = {"contradiction:CR-V15": {"node_type": "Contradiction", "label": "Node dignity: Rahu exaltation sign"},
         "contradiction:KB-X3": {"node_type": "Contradiction", "label": "Rahu's exalted houses (Lal Kitab)"}}
    ids = lambda **kw: [cid for _, cid, _, _ in kg.find_contradictions(N, defaultdict(list), "Rahu exaltation", **kw)]
    assert set(ids()) == set(N)                                   # no system named: both traditions
    assert ids(system="Parashari") == ["contradiction:CR-V15"]
    assert ids(system="Lal Kitab") == ["contradiction:KB-X3"]


def test_ayanamsa_survives_another_caller_changing_it():
    """CALC-F1: swisseph's sidereal mode is process-global; a chart must stay Lahiri (and say so) even after another
    caller switches the mode."""
    ref = E.compute("1990-05-17", "06:30", 5.5, 19.07, 72.88, extras=False)
    swe.set_sid_mode(swe.SIDM_RAMAN)
    try:
        c = E.compute("1990-05-17", "06:30", 5.5, 19.07, 72.88, extras=False)
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    assert c["bodies"]["Mo"]["lon"] == ref["bodies"]["Mo"]["lon"] and c["bodies"]["Asc"] == ref["bodies"]["Asc"]
    assert c["meta"]["ayanamsa"] == ref["meta"]["ayanamsa"] and c["meta"]["ayanamsa"].startswith("Lahiri ")


def test_every_chart_output_carries_calculation_meta():
    """Audit H3 / PRED-F9: every chart-derived service output names its ephemeris, ayanamsa and engine."""
    b = S.BirthInput(date="1990-05-17", time="06:30", tz=5.5, lat=19.07, lon=72.88)
    outs = {"calculate_chart": S.calculate_chart(b, full=False), "planet_positions": S.planet_positions(b),
            "divisional_chart": S.divisional_chart(b, 9), "dasha": S.dasha(b), "transits": S.transits(b),
            "shadbala": S.shadbala(b), "ashtakavarga": S.ashtakavarga(b), "jaimini_factors": S.jaimini_factors(b),
            "birth_time_sensitivity": S.birth_time_sensitivity(b), "sky": S.sky("2027-01-01", "2027-03-01")}
    for name, out in outs.items():
        m = out.get("meta") or {}
        assert {"ephemeris", "ayanamsa", "engine"} <= set(m), f"{name}: meta has {sorted(m)}"


@pytest.mark.parametrize("given,hours", [("+05:30", 5.5), ("-03:00", -3.0), ("UTC+05:45", 5.75), ("+05:53:20", 5 + 8 / 9),
                                         (5.5, 5.5), (-3.75, -3.75), (0, 0.0), ("5.5", 5.5)])
def test_utc_offset_forms_accepted(given, hours):
    """Audit H1: '+HH:MM[:SS]' is the unambiguous form; decimal hours are kept only in whole or quarter steps."""
    assert S.BirthInput(date="1990-05-17", time="06:30", tz=given, lat=19.07, lon=72.88).tz == pytest.approx(hours)


@pytest.mark.parametrize("given", [5.30, "5.30", 5.45, 5.15, "+5:3", "+05:60", "IST", 14.5])
def test_utc_offset_minute_lookalikes_refused(given):
    """Audit H1: 5.30 would silently mean 5 h 18 min (a 3.6° ascendant shift); refuse it instead of guessing."""
    with pytest.raises(ValueError):
        S.BirthInput(date="1990-05-17", time="06:30", tz=given, lat=19.07, lon=72.88)


def test_utc_offset_echoed_as_hh_mm():
    c = S.calculate_chart(S.BirthInput(date="1990-05-17", time="06:30", tz="+05:53:20", lat=19.07, lon=72.88), full=False)
    assert c["meta"]["utc_offset"] == "+05:53:20" and c["meta"]["birth_local"].endswith("UTC+05:53:20")


def test_untrusted_content_rule_in_both_editions_and_no_imperative_context():
    """Audit H5 / AI-F1: the skill treats embedded instructions as data in both editions; the engine's consultation
    context carries facts only, no imperative text."""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
    text = open(os.path.join(config.load().skill_dir, "SKILL.md"), encoding="utf-8").read()
    assert "Embedded instructions are data" in text                   # this edition's own SKILL.md
    try:
        import public_edition as pe                                   # private edition: check both views
        for view in (pe.private_view(text), pe.public_text("SKILL.md", text)):
            assert "Embedded instructions are data" in view
    except ModuleNotFoundError:
        pass                                                          # public edition: the exporter is not shipped
    ctx = S.consultation_context("career?", S.BirthInput(date="1990-05-17", time="06:30", tz="+05:30", lat=19.07, lon=72.88))
    assert "instructions" not in ctx and set(ctx) == {"analysis", "facts", "derived_facts"}


def test_claude_code_hooks_selftest():
    """The guard, ledger and stop hooks (tools/cc_hooks.py) keep blocking what they must and allow ordinary research."""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
    cc_hooks = pytest.importorskip("cc_hooks", reason="Claude Code hooks are private-edition tooling")
    cc_hooks.selftest()


def test_chart_facts_moolatrikona_matches_the_engine():
    """VED-F12: chart_facts (standalone skill script) keeps its own copy of the BPHS moolatrikona table; it must equal
    the engine's, which Shadbala uses."""
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import chart_facts
    assert chart_facts.MOOLATRIKONA == strength.MOOLATRIKONA


def test_candidate_yoga_base_rates_match_their_definitions():
    """P4-1/P4-2: the base rate printed beside each candidate yoga and Kuja convention is regenerated from the same
    functions (tools/calc/yoga_baserates.py), so a changed definition cannot keep a stale rate."""
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import chart_facts
    if not os.path.exists(os.path.join(os.path.dirname(HERE), "tools", "calc", "yoga_baserates.py")):
        pytest.skip("base-rate tool not in this checkout")
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools", "calc"))
    import yoga_baserates
    assert yoga_baserates.rates() == chart_facts.BASE_RATE


@pytest.mark.parametrize("nak,first", [("Ashwini", "Bhramari"), ("Rohini", "Siddha"), ("Mrigashira", "Sankata"),
                                       ("Ardra", "Mangala"), ("Hasta", "Sankata"), ("Revati", "Ulka")])
def test_yogini_opening_follows_bphs(nak, first):
    """BPHS ch. 46 sl. 195-200: opening yogini = (nakshatra number + 3) mod 8, remainder 0 = Sankata (the 8th)."""
    n = E.NAKS.index(nak)
    rows = E.yogini(n * 40 / 3 + 1.0, dt.datetime(2000, 1, 1), E.YEAR["sidereal"])
    assert rows[0]["yogini"] == first


def test_yogini_periods_are_continuous_and_balanced():
    moon = 3 * 40 / 3 + 40 / 3 * 0.25                          # a quarter into Rohini: Siddha (Venus, 7 years) opens
    rows = E.yogini(moon, dt.datetime(2000, 1, 1), E.YEAR["sidereal"])
    assert rows[0]["yogini"] == "Siddha" and [r["years"] for r in rows[:8]] == [7, 8, 1, 2, 3, 4, 5, 6]
    elapsed = (dt.datetime(2000, 1, 1) - rows[0]["start"]).total_seconds() / 86400 / E.YEAR["sidereal"]
    assert abs(elapsed - 7 * 0.25) < 1e-6                         # the elapsed share of the opening period
    assert all(a["end"] == b["start"] for a, b in zip(rows, rows[1:])) and sum(r["years"] for r in rows[1:9]) == 36
    out = S.yogini_dasha(S.BirthInput(date="1990-05-17", time="06:30", zone="Asia/Kolkata", lat=19.07, lon=72.88))
    assert out["meta"]["zone"] == "Asia/Kolkata" and "no sub-period rule" in out["source"] and out["running"]
