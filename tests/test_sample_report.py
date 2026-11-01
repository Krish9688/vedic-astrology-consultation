"""The invented sample report (Asha): its model passes create_report with the birth input, a shifted window is refused,
and the shipped files carry no birth data."""
import copy
import json
import os

import pytest

from astro import config
from astro import service as S

SAMPLE = os.path.join(config.load().skill_dir, "assets", "report", "sample-invented")
MODEL = json.load(open(os.path.join(SAMPLE, "asha-invented.json"), encoding="utf-8"))
BIRTH = json.load(open(os.path.join(SAMPLE, "asha-birth-invented.json"), encoding="utf-8"))


def create(model, tmp_path, monkeypatch):
    s = config.load()
    s.reports_dir = str(tmp_path / "reports")      # the folder guard refuses the skill folder
    monkeypatch.setattr(config, "load", lambda: s)
    b = {k: v for k, v in BIRTH.items() if k != "on"}
    return S.create_report(model, "asha-career-test", S.BirthInput(**b), S.Options(on=BIRTH["on"]))


def shift(ym, n):
    y, m = int(ym[:4]), int(ym[5:7]) - 1 + n
    return f"{y + m // 12}-{m % 12 + 1:02d}"


def test_model_passes_create_report_with_no_errors(tmp_path, monkeypatch):
    r = create(MODEL, tmp_path, monkeypatch)
    assert r["ok"] is True and "errors" not in r
    html = open(r["html"], encoding="utf-8").read()
    assert "Asha" in html and "invented person" in html
    assert not [w for w in ("1991", "Pune", "06:20", "14 March") if w in html]      # birth data was not consented to


@pytest.mark.parametrize("row,n", [(2, -5), (1, 5)], ids=["window", "sub-period"])
def test_a_row_shifted_five_months_is_refused(tmp_path, monkeypatch, row, n):
    m = copy.deepcopy(MODEL)
    t = m["timeline"][row]
    t["start"], t["end"] = shift(t["start"], n), shift(t["end"], n)
    r = create(m, tmp_path, monkeypatch)
    assert r["ok"] is False and r["errors"]


def test_shipped_files_are_present_and_hold_no_birth_data():
    html = open(os.path.join(SAMPLE, "asha-career-20261030-1015.html"), encoding="utf-8").read()
    assert not [w for w in ("1991", "Pune", "06:20") if w in html]
    assert "birth" not in MODEL and len(open(os.path.join(SAMPLE, "README.md")).read().splitlines()) <= 15


@pytest.mark.parametrize("i", [1, 2, 3])
def test_i46_each_key_point_window_shifted_five_months_is_refused(tmp_path, monkeypatch, i):
    """#46: key points carry event_refs, so a window shifted ~5 months fails even for Saturn/Jupiter, which have many
    ingresses and contacts that proximity alone would still find."""
    m = copy.deepcopy(MODEL)
    k = m["summary"]["key_points"][i]
    assert k.get("event_refs"), "the sample's dated key points cite engine events"
    a, b = k["window"].split(" – ")
    mon = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

    def sh(t):
        mo, y = t.split()
        n = mon.index(mo) + 5
        return f"{mon[n % 12]} {int(y) + n // 12}"
    k["window"] = f"{sh(a)} – {sh(b)}"
    r = create(m, tmp_path, monkeypatch)
    assert r["ok"] is False and any("does not contain the engine event" in e for e in r["errors"]), r


def test_i46_unknown_event_ref_is_refused(tmp_path, monkeypatch):
    m = copy.deepcopy(MODEL)
    m["summary"]["key_points"][1]["event_refs"] = ["ING.Ju.2026-10-30"]           # off by a day: not an engine event
    r = create(m, tmp_path, monkeypatch)
    assert r["ok"] is False and any("unknown engine event" in e for e in r["errors"])


def test_rc02_a_second_ungrounded_window_in_text_is_still_checked(tmp_path, monkeypatch):
    m = copy.deepcopy(MODEL)
    k = m["summary"]["key_points"][3]                       # Saturn's period (event_refs DSH.Sa); no Saturn event Dec 2026
    k["text"] += " An early hint comes in Dec 2026 – Dec 2026."
    r = create(m, tmp_path, monkeypatch)
    assert r["ok"] is False and any("Dec 2026" in x and "matches no" in x for x in r["errors"]), r


def test_rc03_refs_may_fall_in_either_range_of_the_window(tmp_path, monkeypatch):
    m = copy.deepcopy(MODEL)
    k = m["summary"]["key_points"][1]
    k["window"], k["event_refs"] = "Oct 2026 – Nov 2026 and Jun 2027 – Jul 2027", ["ING.Ju.2026-10-31", "ING.Ju.2027-06-26"]
    r = create(m, tmp_path, monkeypatch)
    assert not [e for e in r.get("errors", []) if "does not contain" in e], r
