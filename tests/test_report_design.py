"""T2.3 report design: sensitivity states, the one legend, the per-type answer line, contrast."""
import copy
import json
import os
import re
import sys

from astro import config

SKILL = config.load().skill_dir
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import render_report as rr  # noqa: E402

REPORT = os.path.join(SKILL, "assets", "report")
EX = json.load(open(os.path.join(REPORT, "example-synthetic.json"), encoding="utf-8"))
SCHEMA = json.load(open(os.path.join(REPORT, "report.schema.json"), encoding="utf-8"))


def test_sens_state_maps_old_boolean_and_new_field():
    assert rr.sens_state({}) is None and rr.sens_state({"time_sensitive": False}) is None
    assert rr.sens_state({"time_sensitive": True}) == "depends"
    assert rr.sens_state({"sensitivity": "may_shift", "time_sensitive": True}) == "may_shift"
    assert rr.sens_state({"sensitivity": "bogus"}) is None
    assert set(SCHEMA["$defs"]["sensitivity"]["enum"]) == set(rr.SENS_LABELS)


def test_sensitivity_reaches_chip_bar_and_uncertainty_list():
    r = copy.deepcopy(EX)
    r["sections"][0]["units"][0]["sensitivity"] = "depends"
    r["timeline"][3]["sensitivity"] = "may_shift"
    r["summary"]["key_points"][0]["sensitivity"] = "stable"
    assert rr.validate(r, SCHEMA) == []
    html = rr.html_of(r)
    assert 'class="chip sens sens-depends"' in html and 'class="chip sens sens-stable"' in html
    assert "sens-may_shift" in html and "What moves with the birth time" in html
    assert [b["sens"] for b in rr.timeline(r["timeline"])["bars"]].count("may_shift") == 1
    plain = rr.html_of(EX)       # no states given: no marks, no list
    assert "What moves with the birth time" not in plain and 'class="chip sens ' not in plain.split("</style>")[1].split('id="legend"')[0]


def test_one_legend_with_every_label_and_an_answer_line_per_type():
    html = rr.html_of(EX)
    assert html.count('id="legend"') == 1
    for label in [*rr.CLAIM_LABELS.values(), *rr.SENS_LABELS.values(), *rr.LEGEND["grade"]]:
        assert label in html.split('id="legend"')[1].split("</table>")[0], label
    assert set(rr.ANSWERS) == set(rr.TYPE_NAMES)
    for t, line in rr.ANSWERS.items():
        assert line.endswith("?") and not re.search(r"\d|%|lucky|guarantee|best", line), t
    assert rr.ANSWERS["career"] in html and "ANSWERS" not in html


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def test_small_text_pairs_meet_aa():
    css = open(os.path.join(REPORT, "report.css"), encoding="utf-8").read()
    tok = dict(re.findall(r"--(\w+):\s*(#[0-9A-Fa-f]{6})", css))
    for fg, bg in [("ink", "ivory"), ("muted", "ivory"), ("muted", "paper"), ("muted", "mint"), ("forest", "pistachio"),
                   ("pine", "pistachio"), ("clay", "mint"), ("clay", "ivory"), ("pine", "ivory")]:
        a, b = sorted((_lum(tok[fg]), _lum(tok[bg])), reverse=True)
        assert (a + .05) / (b + .05) >= 4.5, (fg, bg)
