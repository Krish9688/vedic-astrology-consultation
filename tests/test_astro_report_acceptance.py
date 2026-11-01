# ASTRO-REPORT-SPEC.md §9 acceptance tests (T-T6) that the engine, the MCP tools and the renderer can prove without a live
# session. Dialogue-only items are manual checks in research/astro-report-2026-10-30/ACCEPTANCE-MAP.md.
# Birth data: the synthetic S1 chart (invented, 1992-03-14 09:40 London) and invented places/times only.
import inspect
import json
import os
import re
import sys
import tempfile

import pytest

from astro import config, mcp_server as M, service as S

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = next(p for d in ("plugin", "plugins/astrology-consultation")         # workspace and archive repo; public repo
              if os.path.isdir(p := os.path.join(HERE, "..", d)))
SKILL_MD = open(os.path.join(PLUGIN, "skills", "astro-report", "SKILL.md"), encoding="utf-8").read()
S1 = dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12)        # invented: the example report's own chart
RUN = dict(on="2026-09-27", months=60)
LONDON = dict(lat=51.5, lon=-0.12, zone="Europe/London")                    # invented births at a real zone
NAGPUR = dict(lat=21.15, lon=79.09, zone="Asia/Kolkata")
BIRTH_STRINGS = ("1992-03-14", "14 March 1992", "09:40", "London", "51.5", "-0.12")   # S1 as the example prints it


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Own config, data, reports and temp folders; the owner's settings are never read."""
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.toml"))
    monkeypatch.setattr(S, "REMOTE", False)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    (tmp_path / "config.toml").write_text(f'data_dir = "{tmp_path / "data"}"\nreports_dir = "{tmp_path / "reports"}"\n')
    (tmp_path / "tmp").mkdir()
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "tmp"))
    return tmp_path


def example():
    return json.load(open(os.path.join(config.load().skill_dir, "assets", "report", "example-synthetic.json"), encoding="utf-8"))


def report(model, name):          # the MCP tool itself (the function the server registers), with the birth input
    return M.create_report(model, name, **S1, **RUN)


def with_text(text):
    m = example()
    m["sections"][0]["units"][0]["meaning"] = text
    return m


def shift_named_row(model, months):
    row = next(x for x in model["timeline"] if x.get("basis", "").startswith(tuple("SMJRKV")))   # names its dasha period
    for k in ("start", "end"):
        y, m = int(row[k][:4]), int(row[k][5:7]) - 1 + months
        row[k] = f"{y + m // 12}-{m % 12 + 1:02d}"
    return model


# --- 1, 5, 7, 9, 25, 26, 28, 29, 31, 34, 36, 38, 39: the skill text carries the rule -------------------------------------
def test_01_plugin_has_no_commands_key_and_keeps_setup_and_doctor():
    manifest = json.load(open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"), encoding="utf-8"))
    assert "commands" not in manifest
    assert all(os.path.exists(os.path.join(PLUGIN, "commands", f)) for f in ("setup.md", "doctor.md"))


def test_05_aliases_map_to_real_types_and_horoscope_is_not_one():
    from test_astro_report_skill import rr
    line = next(ln for ln in SKILL_MD.split("\n\n") if ln.startswith("Aliases"))
    pairs = re.findall(r"((?:`[a-z]+`(?:, )?)+) = ([a-z0-9-]+)", line)
    alias = {a: t for names, t in pairs for a in re.findall(r"`([a-z]+)`", names)}
    assert alias == {"life": "complete-life", "full": "complete-life", "year": "12-month", "annual": "12-month",
                     "summary": "compact", "monthly": "outlook", "quarterly": "outlook", "travel": "relocation",
                     "abroad": "relocation"}
    assert set(alias.values()) <= set(rr.TYPE_NAMES) and "horoscope" not in alias
    assert "case-insensitive" in line and "V-TYPE" in SKILL_MD


@pytest.mark.parametrize("item,phrases", [
    (7, ['"No": V-CONSENT-OTHER, no calculation']),
    (9, ["I'll print 'Asha' only. OK?", "Only a first name or initials are printed"]),
    (25, ["Approximate with uncertainty over 15 minutes", "Offer **Consultation\n  summary**"]),
    (26, ["Unknown: **Consultation summary** only", "go in `uncertainty.not_assessed`", '"unknown; 12:00\n  used as a placeholder"']),
    (29, ["It is the only calculation tool allowed before the confirmation screen's \"Start\"", 'Nothing is calculated until "Start"']),
    (31, ["aren't installed here, so I can give only the general flags", '"Not assessed" says why']),
    (34, ["stop the reading at once", "No chart\n  link, no timing as comfort, no remedy"]),
    (36, ["`<slug>-<report_type>-<YYYYMMDD>-<HHMM>`", "Never include birth data in the name"]),
    (38, ["at most 2 retries", "never claim a file that was not written", "fix the model (never the HTML)"]),
    (39, ["If the tools are missing or silent: V-ENGINE, stop. Do not calculate or recall anything from memory."]),
])
def test_skill_text_states_the_rule(item, phrases):
    for p in phrases:
        assert p in SKILL_MD, (item, p)


def test_28_progress_lines_have_no_numbers_or_chart_content():
    block = SKILL_MD.split("### Progress lines", 1)[1].split("###", 1)[0]
    lines = re.findall(r'^\d\. "([^"]+)"', block, re.M)
    assert len(lines) == 8 and lines[1] == "Calculating the chart on this computer..."
    assert not any(re.search(r"\d|Asc|lagna|Moon|Saturn|Jupiter|house", x, re.I) for x in lines), lines


def test_36_file_name_form_passes_the_engine_name_rule():
    assert S.SAFE_NAME.match("asha-career-20261030-1015") and not S.SAFE_NAME.match("asha/1991-03-14")


# --- 13: offsets ------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("bad", ["5.30", 5.3, "IST"])
def test_13_bare_offset_or_zone_abbreviation_is_refused_by_the_tool(bad):
    from mcp.server.mcpserver.exceptions import ToolError
    with pytest.raises(ToolError, match=r"\+HH:MM"):
        M.get_planet_positions(**(S1 | {"tz": bad}))


def test_13_hh_mm_offset_is_accepted():
    assert M.get_planet_positions(**(S1 | {"tz": "+05:30"}))["meta"]["utc_offset"] == "+05:30"


# --- 18-21: zone refusals and flags -----------------------------------------------------------------------------------
def test_18_dst_gap_is_refused_and_a_chosen_offset_is_flagged_through_to_the_chart():
    with pytest.raises(ValueError, match="does not exist in Europe/London"):
        S.BirthInput(date="1991-03-31", time="01:30", **LONDON)
    meta = S.calculate_chart(S.BirthInput(date="1991-03-31", time="01:30", tz="+01:00", **LONDON), full=False)["meta"]
    assert meta["utc_offset"] == "+01:00" and meta["zone"] == "Europe/London"
    assert any("cannot resolve this time" in f and "manual offset +01:00 used" in f for f in meta["utc_offset_flags"])


def test_19_dst_overlap_names_both_offsets_and_fold_settles_it():
    with pytest.raises(ValueError, match=r"occurs twice.*fold=0 for the first \(\+01:00\).*fold=1 for the second \(\+00:00\)"):
        S.BirthInput(date="1991-10-27", time="01:30", **LONDON)
    first = M.get_planet_positions(date="1991-10-27", time="01:30", fold=0, **LONDON)["meta"]
    second = M.get_planet_positions(date="1991-10-27", time="01:30", fold=1, **LONDON)["meta"]
    assert (first["utc_offset"], second["utc_offset"]) == ("+01:00", "+00:00")


@pytest.mark.parametrize("date,want", [("1938-06-01", {"1948", "1970"}), ("1895-06-01", {"1948", "1970"})])
def test_20_pre_1948_india_carries_both_flags(date, want):
    """1895 Asia/Kolkata (GAP G9): the tz database resolves it to a historic local time; it must at least be flagged."""
    flags = S.BirthInput(date=date, time="12:00", **NAGPUR).tz_flags
    assert {y for y in ("1948", "1970") if any(y in f for f in flags)} == want


def test_20_pre_1970_elsewhere_carries_only_the_1970_flag():
    flags = S.BirthInput(date="1965-06-01", time="12:00", **LONDON).tz_flags
    assert len(flags) == 1 and "1970" in flags[0]


def test_21_lmt_era_is_refused_with_the_lmt_offset_and_an_explicit_offset_is_recorded():
    with pytest.raises(ValueError, match=r"before standard time.*local mean time at this longitude: -00:00:29"):
        S.BirthInput(date="1840-06-01", time="12:00", **LONDON)
    b = S.BirthInput(date="1840-06-01", time="12:00", tz="-00:00:29", **LONDON)
    assert b.tz_source.startswith("manual UTC offset") and any("local mean time" in f for f in b.tz_flags)


# --- 23: Julian date ----------------------------------------------------------------------------------------------------
def test_23_julian_date_reaches_every_tool_converted():
    j = dict(date="1900-01-01", time="12:00", tz="+00:00", lat=51.5, lon=-0.12)
    jul = M.get_dasha(**j, calendar="julian", on="1950-01-01")
    greg = M.get_dasha(**(j | {"date": "1900-01-13"}), on="1950-01-01")
    assert jul["running"] == greg["running"] and jul["meta"]["birth_local"].startswith("1900-01-13")
    assert "calendar" in inspect.signature(M.create_report).parameters


# --- 27, 38: provenance through the MCP tool ---------------------------------------------------------------------------
def test_27_corrupted_dasha_date_is_caught_by_the_mcp_tool_and_nothing_is_written(isolated):
    assert report(example(), "clean")["ok"]
    bad = report(shift_named_row(example(), 2), "shifted")              # two months: past the documented 45-day rounding
    assert bad["ok"] is False and any("does not match its" in e for e in bad["errors"])       # 38: the ok:false shape
    assert not (isolated / "reports" / "shifted.html").exists()
    assert M.create_report(example(), "nobirth")["ok"] is False                                   # dates need the birth input


# --- 30: tradition separation ------------------------------------------------------------------------------------------
@pytest.mark.parametrize("unit,error", [
    (dict(system="lal_kitab", edition="lk1952", claim_type="rule", claim_basis="TEXT", rule_refs=["LK1952 p59"]),
     "outside an 'lk-' section"),
    (dict(system="parashari", claim_type="rule", claim_basis="TEXT", rule_refs=["LK1952 p59"]), "cites the Lal Kitab book"),
])
def test_30_mixed_traditions_are_refused_by_the_tool(unit, error):
    m = example()
    m["sections"][0]["units"][0].update(unit)
    res = report(m, "mixed")
    assert res["ok"] is False and any(error in e for e in res["errors"]), res


# --- 32, 33: safety and remedies ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("text", ["You will get pregnant soon.", "The native will die young."])
def test_32_medical_and_lifespan_claims_are_blocked(text):
    res = report(with_text(text), "unsafe")
    assert res["ok"] is False and any(e.startswith("SAFETY") for e in res["errors"])


@pytest.mark.parametrize("text", ["Success in this role is guaranteed.", "You will win the court case."])
def test_32_guarantee_and_legal_outcome_claims_are_blocked(text):
    assert report(with_text(text), "unsafe")["ok"] is False


def test_33_remedies_only_on_request_and_cards_are_checked():
    card = {"planet": "Jupiter", "house": 2, "remedy": "Serve elders and teachers", "safety": "low-risk", "source": "KB p107"}
    m = example()
    m["remedies"] = [card]
    res = report(m, "unasked")
    assert res["ok"] is False and any("remedies_requested" in e for e in res["errors"])
    m["remedies"] = [dict(card, remedy="Offer milk to a serpent")]
    m["remedies_requested"] = True
    assert any("never-recommend" in e for e in report(m, "never")["errors"])
    m["remedies"] = [card]
    ok = report(m, "asked")
    assert ok["ok"] and "Remedies you asked about (Lal Kitab)" in open(ok["html"], encoding="utf-8").read()
    plain = report(example(), "plain")
    assert "Remedies you asked about" not in open(plain["html"], encoding="utf-8").read()


# --- 35, 37, 40: delivery and privacy ----------------------------------------------------------------------------------
def test_35_no_consent_means_no_birth_strings_in_the_html():
    yes = open(report(example(), "consented")["html"], encoding="utf-8").read()
    assert "14 March 1992" in yes and "09:40" in yes                    # the search below would find them
    m = example()
    del m["birth"]
    html = open(report(m, "noconsent")["html"], encoding="utf-8").read()
    assert [s for s in BIRTH_STRINGS if s in html] == []


def test_35_no_consent_means_no_birth_strings_in_the_pdf():
    pytest.importorskip("weasyprint")
    fitz = pytest.importorskip("fitz")
    m = example()
    del m["birth"]
    pdf = report(m, "noconsent")["pdf"]
    text = "".join(p.get_text() for p in fitz.open(pdf))
    assert [s for s in BIRTH_STRINGS if s in text] == []


def test_36_plugin_root_is_refused_by_the_tool(isolated, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(isolated))             # reports_dir is inside it
    assert report(example(), "inplugin") == {"ok": False, "errors": [config.FOLDER_REFUSAL]}
    assert not (isolated / "reports").exists()


def test_37_without_weasyprint_pdf_is_null_and_the_html_is_kept(isolated, monkeypatch):
    monkeypatch.setitem(sys.modules, "weasyprint", None)                 # import fails as on a machine without it
    res = report(example(), "htmlonly")
    assert res["ok"] and res["pdf"] is None and os.path.exists(res["html"])
    assert not (isolated / "reports" / "htmlonly.pdf").exists()
    assert "If `pdf` is null (WeasyPrint missing), say exactly" in SKILL_MD


def test_40_a_run_leaves_only_the_report_and_no_temp_files(isolated):
    m = example()
    del m["birth"]
    res = report(m, "only")
    left = sorted(str(p.relative_to(isolated)) for p in isolated.rglob("*") if p.is_file())
    assert left == ["config.toml", "reports/only.html"] + (["reports/only.pdf"] if res["pdf"] else [])
    assert os.stat(res["html"]).st_mode & 0o777 == 0o600 and (isolated / "reports").stat().st_mode & 0o777 == 0o700
