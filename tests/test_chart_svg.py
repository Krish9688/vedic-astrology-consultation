"""P7-1: North/South rasi chart SVG goldens, grid geometry, and the chart in a rendered report (HTML and PDF)."""
import copy
import json
import os
import re
import sys

import pytest

from astro import config

SKILL = config.load().skill_dir
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import chart_svg  # noqa: E402
import render_report as rr  # noqa: E402

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
EX = json.load(open(os.path.join(SKILL, "assets", "report", "example-synthetic.json"), encoding="utf-8"))
# synthetic placements, every sign style case: a stellium of 3+, the lagna cell shared, empty signs
POS = [{"body": b, "sign": s} for b, s in [("Ascendant", "Taurus"), ("Sun", "Aries"), ("Moon", "Taurus"),
       ("Mars", "Capricorn"), ("Saturn", "Capricorn"), ("Mercury", "Pisces"), ("Jupiter", "Leo"),
       ("Venus", "Aquarius"), ("Rahu", "Scorpio"), ("Ketu", "Taurus")]]


@pytest.mark.parametrize("style", ["north", "south"])
def test_svg_matches_golden(style):
    with open(os.path.join(FIX, f"chart_{style}.svg"), encoding="utf-8") as f:
        assert chart_svg.chart(POS, style) == f.read().rstrip("\n")


def test_south_grid_is_fixed_signs_clockwise_from_aries_at_row0_col1():
    svg = chart_svg.south(POS)
    cells = {m[2]: (int(float(m[1]) // 75), int(float(m[0]) // 75))
             for m in re.findall(r'<text x="([\d.]+)" y="([\d.]+)" class="n">(\w+)</text>', svg)}
    assert cells == {s[:3]: rc for s, rc in zip(chart_svg.SIGNS, chart_svg.SOUTH)}
    assert cells["Ari"] == (0, 1) and cells["Can"] == (1, 3) and cells["Lib"] == (3, 2) and cells["Cap"] == (2, 0)


def test_north_house_one_is_top_middle_and_counts_anticlockwise():
    svg = chart_svg.north(POS)
    nums = [int(n) for n in re.findall(r'class="n" text-anchor="middle">(\d+)<', svg)]
    assert nums == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1]          # Taurus rising: house h holds sign 1 + h
    assert chart_svg.NORTH[0] == (.5, .25) and chart_svg.NORTH[1][0] < .5 and chart_svg.NORTH[11][0] > .5


def test_report_draws_the_chosen_style_only_and_no_chart_without_a_lagna():
    pytest.importorskip("jinja2")
    r = copy.deepcopy(EX)
    assert "North Indian rasi chart" in rr.html_of(r) and "South Indian" not in rr.html_of(r)
    r["chart_style"] = "south"
    page = rr.html_of(r)
    assert "South Indian rasi chart" in page and "North Indian" not in page and "Lahiri" in page   # caption names method
    r["appendix"]["positions"] = [p for p in r["appendix"]["positions"] if p["body"] != "Ascendant"]
    assert "rasi chart" not in rr.html_of(r)


REPORT_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".venv-report", "bin", "python")


@pytest.mark.skipif(not os.path.exists(REPORT_PY), reason="report venv (WeasyPrint) not installed here")
@pytest.mark.parametrize("style", ["north", "south"])
def test_pdf_keeps_the_lagna_row(tmp_path, style):
    """M10 (2026-10-24): WeasyPrint dropped the red 'Asc …' row because it ignores a `font:` shorthand with a weight in
    SVG <style>; the PDF must carry the lagna label and the bodies in the lagna cell."""
    import subprocess
    svg = tmp_path / "c.svg"
    svg.write_text(chart_svg.chart(POS, style), encoding="utf-8")
    code = ("import sys, weasyprint, pymupdf; s = open(sys.argv[1]).read(); "
            "weasyprint.HTML(string='<!doctype html><meta charset=utf-8>' + s).write_pdf(sys.argv[2]); "
            "print(pymupdf.open(sys.argv[2])[0].get_text())")
    out = subprocess.run([REPORT_PY, "-I", "-c", code, str(svg), str(tmp_path / "c.pdf")], capture_output=True, text=True,
                         check=True).stdout
    assert "Asc" in out and "Mo" in out and "Ke" in out, out                           # lagna cell: Asc Mo Ke


def test_pdf_renders_with_the_chart(tmp_path):
    pytest.importorskip("jinja2")
    pytest.importorskip("weasyprint")
    hp, pp = rr.render(dict(copy.deepcopy(EX), chart_style="south"), str(tmp_path), "r")
    assert pp and open(pp, "rb").read(5) == b"%PDF-"
