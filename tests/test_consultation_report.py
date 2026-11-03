"""Consultation report (owner specification 2026-11-01): intake validation, the engine pack, the model checks, the
rendered report (all nine sections, every question), determinism and the PDF page check. Personas P2..P6 are invented
(tests/fixtures/consultation); the owner's chart is tested in test_private_regression.py, local only."""
import copy
import hashlib
import importlib.util
import json
import os
import re

import pytest

from astro import service as S

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "consultation")
PERSONAS = ["P2", "P3", "P4", "P5", "P6"]
SECTIONS = ["1. Client intake", "2. Methodology and settings", "3. Personalized kundli (Vedic)", "4. Lal Kitab view",
            "5. Life areas", "6. Answers to your questions", "7. Timeline", "8. Remedies and guidance", "9. Appendix"]


def load(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


def skill_mod(name):
    p = os.path.join(os.environ["ASTRO_SKILL_DIR"], "scripts", f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"t_{name}", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def C():
    return skill_mod("consultation")


@pytest.fixture(scope="module")
def RR():
    return skill_mod("render_report")


_PACKS = {}


def pack(p):
    if p not in _PACKS:
        r = S.consultation_pack(load(f"{p}-intake.json"))
        assert r["ok"], r
        _PACKS[p] = r["pack"]
    return _PACKS[p]


def has(mod):
    return importlib.util.find_spec(mod) is not None


# ---- spec test 5: missing or invalid input gives a clear error, never a broken report ----
@pytest.mark.parametrize("mutate, want", [
    (lambda i: i["birth"].update(date="2005-02-30"), "birth.date"),
    (lambda i: i.update(questions=[]), "questions: at least one"),
    (lambda i: i["questions"][0].update(text=""), "empty or too short"),
    (lambda i: i["questions"][0].update(category="astrology"), "category"),
    (lambda i: i["client"].update(full_name=""), "client.full_name"),
    (lambda i: i["client"].update(education="[CONFIRM or write not provided]"), "placeholder"),
    (lambda i: i["birth"].update(tz="+05:53"), "IST +05:30"),
    (lambda i: i["birth"].update(time="25:10"), "birth.time"),
    (lambda i: i["consent"].update(store_and_process=False), "consent"),
    (lambda i: i["client"].update(language="Gujarati"), "client.language"),
    (lambda i: i["birth"].update(time_reliability="approximate"), "time_uncertainty_min"),
])
def test_invalid_intake_is_refused_with_a_field_named_error(mutate, want):
    i = load("P2-intake.json")
    mutate(i)
    r = S.consultation_pack(i)
    assert not r["ok"] and any(want in e for e in r["errors"]), r


def test_unknown_city_without_coordinates_is_a_clear_error(monkeypatch):
    i = load("P2-intake.json")
    for k in ("lat", "lon"):
        del i["birth"][k]
    i["birth"]["place"] = "Atlantisville"
    monkeypatch.setattr(S, "find_place", lambda name, country=None: {"matches": [], "ambiguous": False})
    r = S.consultation_pack(i)
    assert not r["ok"] and "unknown place" in r["errors"][0], r


def test_raman_and_other_modes_are_refused():
    r = S.consultation_pack(load("P2-intake.json"), S.Options(ayanamsa="raman"))
    assert not r["ok"] and "Lahiri" in r["errors"][0]


# ---- the pack: every table comes from the engine ----
@pytest.mark.parametrize("p", PERSONAS)
def test_pack_has_every_calculated_section(p):
    pk = pack(p)
    assert pk["meta"]["ayanamsa"].startswith("Lahiri") and len(pk["planets"]) == 10
    assert set(pk["charts"]) == {"D1", "D9", "D10", "D7", "D4"}
    assert pk["dasha"]["mahadashas"] and pk["gochara"] and pk["events"]
    assert "LMT" in pk["method"]["time_zone"] and "never local mean time" in pk["method"]["time_zone"]
    if pk["unknown_time"]:
        assert pk["lal_kitab"] is None and "ascendant" in pk["lal_kitab_reason"]
    else:
        assert pk["lal_kitab"]["rows"] and len(pk["lal_kitab"]["rows"]) == 9


def test_indian_births_use_ist_and_the_toronto_birth_uses_its_historical_zone():
    for p in ("P2", "P3", "P5", "P6"):
        assert pack(p)["meta"]["utc_offset"] == "+05:30"
    p4 = pack("P4")
    assert p4["meta"]["utc_offset"] == "-04:00"                       # EDT: the first 01:30 of the fall-back night
    assert "America/Toronto" in p4["method"]["time_zone"] and "fold=0" in p4["method"]["time_zone"]


def test_the_second_0130_of_the_fallback_night_is_eastern_standard_time():
    i = load("P4-intake.json")
    i["birth"]["fold"] = 1
    r = S.consultation_pack(i)
    assert r["ok"] and r["pack"]["meta"]["utc_offset"] == "-05:00"


def test_midnight_birth_is_the_start_of_the_stated_date():
    p3 = pack("P3")
    assert p3["meta"]["birth_local"].startswith("2001-01-01 00:00:00")


def test_unknown_time_withholds_everything_the_time_decides():
    p5 = pack("P5")
    v = set(p5["varying_ids"])
    assert "F.asc.sign" in v and "F.H1.sign" in v and any(x.startswith("SB.") for x in v)
    assert p5["planets"][0]["varies"] == ["sign", "degree", "nakshatra", "pada"]


def test_approximate_time_measures_what_the_uncertainty_can_change():
    p6 = pack("P6")                         # ±45 min and the ascendant changes sign 43 min later
    assert "F.asc.sign" in p6["varying_ids"] and p6["dasha"]["shift_days"] > 45


# ---- model checks: every section, every question, every id ----
def test_p2_model_passes_all_checks(C, RR):
    sch = json.load(open(os.path.join(os.environ["ASTRO_SKILL_DIR"], "assets", "report", "report.schema.json")))
    errs, _ = C.all_checks(pack("P2"), load("P2-model.json"), RR, sch)
    assert errs == []


@pytest.mark.parametrize("mutate, want", [
    (lambda m: m["answers"].pop(), "must be answered exactly once"),
    (lambda m: m["chapters"].pop("health"), "chapters.health"),
    (lambda m: m["chapters"]["career"]["indicators"][0].update(fact_refs=["F.Xx.house"]), "unknown fact id"),
    (lambda m: m["chapters"]["career"]["indicators"][0].update(fact_refs=[], event_refs=[]), "must name the chart factors"),
    (lambda m: m["chapters"]["love"]["windows"][0].update({"from": "2033-01", "to": "2033-06"}), "does not contain the event"),
    (lambda m: m["chapters"]["love"]["windows"][0].update(event_refs=["ING.Sa.2099-01-01"]), "unknown engine event"),
    (lambda m: m["chapters"]["love"]["indicators"][0].update(fact_refs=["LK.Ju.house"]), "Lal Kitab facts belong in section 4"),
    (lambda m: m["lal_kitab"]["overview"].update(fact_refs=["F.Ju.house"]), "never merged"),
    (lambda m: m["kundli"]["moon"].update(text="See [TODO] later"), "placeholder"),
    (lambda m: m["timeline"].update(months_12=[]), "timeline.months_12"),
    (lambda m: m["kundli"].pop("transits"), "kundli.transits"),
])
def test_model_mutations_are_refused(C, RR, mutate, want):
    m = copy.deepcopy(load("P2-model.json"))
    mutate(m)
    errs, _ = C.model_checks(pack("P2"), m, RR)
    assert any(want in e for e in errs), errs


def test_remedies_without_consent_are_refused(C, RR):
    p = copy.deepcopy(pack("P2"))
    p["intake"]["consent"]["remedies_requested"] = False
    errs, _ = C.model_checks(p, load("P2-model.json"), RR)
    assert any("did not ask for remedies" in e for e in errs)


def test_safety_lint_runs_on_the_consultation_text(C, RR):
    m = copy.deepcopy(load("P2-model.json"))
    m["chapters"]["family"]["indicators"][0]["text"] = "Children are likely in the window from March 2029."
    sch = json.load(open(os.path.join(os.environ["ASTRO_SKILL_DIR"], "assets", "report", "report.schema.json")))
    errs, _ = C.all_checks(pack("P2"), m, RR, sch)
    assert any(e.startswith("SAFETY") for e in errs), errs


def test_unknown_time_model_may_not_cite_dates_or_time_bound_facts(C, RR):
    m = copy.deepcopy(load("P2-model.json"))
    errs, _ = C.model_checks(pack("P5"), m, RR)
    joined = " ".join(errs)
    assert "birth time unknown" in joined and "no dated windows" in joined


def test_approximate_time_needs_time_sensitive_marks(C, RR):
    p6 = pack("P6")
    m = {"kundli": {"lagna": {"text": "The lagna reading.", "fact_refs": ["F.asc.sign"]}}}
    errs, _ = C.model_checks(p6, m, RR)
    assert any("time_sensitive" in e for e in errs)
    m["kundli"]["lagna"]["time_sensitive"] = True
    errs, _ = C.model_checks(p6, m, RR)
    assert not any("kundli.lagna" in e and "time_sensitive" in e for e in errs)


# ---- full render per persona: all sections, every question, deterministic, PDF clean ----
def _render(p, out):
    return S.create_consultation_report(load(f"{p}-intake.json"), load(f"{p}-model.json"), None, S.DEFAULTS,
                                        load(f"{p}-verification.json"), out_dir=str(out))


@pytest.mark.parametrize("p", PERSONAS)
def test_persona_report_is_complete(p, tmp_path):
    if not os.path.exists(os.path.join(FIX, f"{p}-model.json")):
        pytest.skip(f"{p}-model.json not written yet")
    if not has("jinja2"):
        pytest.skip("jinja2 not installed")
    r = _render(p, tmp_path)
    assert r["ok"], r.get("errors")
    html = open(r["html"], encoding="utf-8").read()
    text = re.sub(r"<[^>]+>", " ", html)
    for s in SECTIONS:                                                    # spec test 1
        assert s in text, s
    for q in load(f"{p}-intake.json")["questions"]:                       # spec test 2
        assert q["text"] in html.replace("&#39;", "'").replace("&quot;", '"'), q["id"]
        assert f'id="{q["id"]}"' in html
    assert "Lahiri" in text and not re.search(r"Raman (?:ayanamsa|2[23]\.\d)", text)   # B. V. Raman the author may be cited
    assert not re.search(r"\bundefined\b|\{\{|\bNaN\b|\[CONFIRM", text)
    if r["pdf"]:                                                          # spec test 7
        assert r["pdf_problems"] == []
    if load(f"{p}-intake.json")["birth"]["time_reliability"] == "unknown":   # spec test 4
        assert "Birth time unknown" in text and "Moon chart" in text and "not cast" in text


@pytest.mark.parametrize("p", ["P2", "P5"])
def test_same_input_gives_the_same_files(p, tmp_path):                    # spec test 6
    if not os.path.exists(os.path.join(FIX, f"{p}-model.json")):
        pytest.skip(f"{p}-model.json not written yet")
    if not has("jinja2"):
        pytest.skip("jinja2 not installed")
    digests = []
    for k in ("a", "b"):
        r = _render(p, tmp_path / k)
        assert r["ok"], r.get("errors")
        digests.append({x: hashlib.sha256(open(r[x], "rb").read()).hexdigest() for x in ("html", "pdf", "docx") if r[x]})
    assert digests[0] == digests[1]


def test_files_are_owner_only(tmp_path):
    if not has("jinja2"):
        pytest.skip("jinja2 not installed")
    r = _render("P2", tmp_path)
    for x in ("html", "pdf", "docx"):
        if r[x]:
            assert oct(os.stat(r[x]).st_mode)[-3:] == "600"


def test_verification_records_agree_within_tolerance():                 # spec test 3 (reference values, stored)
    for p in PERSONAS:
        v = load(f"{p}-verification.json")
        assert v["failures"] == 0 and v["comparisons"] >= 200, p
        assert all(r["status"] == "PASS" for r in v["rows"]), p


def test_skill_documents_the_consultation_flow():
    ref = open(os.path.join(os.environ["ASTRO_SKILL_DIR"], "references", "consultation-report.md"), encoding="utf-8").read()
    assert "prepare_consultation_report" in ref and "create_consultation_report" in ref and "never LMT" in ref.replace("Never use LMT", "never LMT")
    sch = json.load(open(os.path.join(os.environ["ASTRO_SKILL_DIR"], "assets", "report", "consultation-model.schema.json")))
    assert set(sch["properties"]["chapters"]["required"]) == {"love", "career", "wealth", "foreign", "education", "family",
                                                              "health", "spirituality"}


def test_lk_remedy_dispute_both_directions(C):
    assert "not changed by remedies" in C.lk_remedy_dispute({"planet": "Jupiter", "house": 9, "pakka_ghar": "yes", "dignity": "—"})
    assert "not changed by remedies" in C.lk_remedy_dispute({"planet": "Moon", "house": 6, "pakka_ghar": "no", "dignity": "—"})
    assert "fixed (beyond remedy)" in C.lk_remedy_dispute({"planet": "Saturn", "house": 3, "pakka_ghar": "no", "dignity": "—"})
    assert "fixed (beyond remedy)" in C.lk_remedy_dispute({"planet": "Venus", "house": 6, "pakka_ghar": "no", "dignity": "exalted"})
    assert C.lk_remedy_dispute({"planet": "Mars", "house": 10, "pakka_ghar": "no", "dignity": "exalted"}) == ""
