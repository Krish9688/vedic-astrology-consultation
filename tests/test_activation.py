# P4-6: dasha activation table, topic network presets, retrospective calibration — synthetic chart S1 only
import copy
import importlib.util
import json
import os
import re

import pytest

from astro import cli, config, service as S
from astro.calc import activation as A

S1 = dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12)
ON = S.Options(on="2026-10-02", months=24)
EVENTS = [{"category": "career", "month": "2015-06"}, {"category": "marriage", "month": "2019-09"},
          {"category": "relocation", "month": "2021-02"}]


@pytest.fixture(scope="module")
def b():
    S.REMOTE = False
    return S.BirthInput(**S1)


@pytest.fixture(scope="module")
def facts(b):
    return S._facts_ids(S._compute(b, ON, extras=False))


@pytest.fixture(scope="module")
def act(b):
    return S.activation(b, ON, "marriage")


@pytest.fixture(scope="module")
def retro(b):
    return S.retrospective(b, copy.deepcopy(EVENTS))


def _strings(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, str):
        yield x


def test_ad_rows_match_chart_facts_lordships(act, facts):
    me = next(r for r in act["segments"] if r["ad"] == "Ra")["lords"]["Me"]
    # by hand: Taurus lagna, Mercury in Pisces = 11th, owns Gemini (2nd) and Virgo (5th); Moon in Cancer: 9th, owns 3/12
    assert (me["house_from_lagna"], me["owns_from_lagna"], me["house_from_moon"], me["owns_from_moon"]) == (11, [2, 5], 9, [3, 12])
    for r in act["segments"]:
        assert set(r["lords"]) == {r["md"], r["ad"]}
        for p, v in r["lords"].items():
            assert v["owns_from_lagna"] == facts[f"F.{p}.owns"] and v["house_from_lagna"] == facts[f"F.{p}.house"]
            assert (v["d9"], v["d10"], v["dignity"]) == (facts[f"F.{p}.d9"], facts[f"F.{p}.d10"], facts[f"F.{p}.dignity"])
            assert v["owns_from_moon"] == [h for h in range(1, 13) if facts[f"F.M{h}.lord"] == p]
            assert (p in act["network"]["planets"]) == (p in r["lords_in_network"]) == bool(v["network_roles"])


def test_segments_cover_the_horizon_without_gaps(act):
    seg = act["segments"]
    assert seg[0]["start"] <= act["from"] and seg[-1]["end"] > act["to"]
    assert all(a["end"] == b["start"] for a, b in zip(seg, seg[1:]))


def test_contacts_fall_in_their_segment(act, b):
    seen = []
    for r in act["segments"]:
        for c in r["contacts"]:
            assert r["start"] <= c["date"] < r["end"]
            assert c["natal"] in act["network"]["planets"] or c["natal"] in r["lords"]
            seen.append(c)
        for st in r["stations"]:
            assert r["start"] <= st["date"] < r["end"]
        for ep in r["station_episodes"]:
            assert r["start"] <= ep["stations"][0]["date"] < r["end"] and ep["band"] in ("close", "wide")
        for st in r["ju_sa_sign_stays"]:
            assert st["from"] < r["end"] and st["to"] > r["start"]
    assert seen and len(seen) == len({json.dumps(c, sort_keys=True) for c in seen})   # each contact once


def test_boundary_contact_goes_to_the_segment_that_starts_that_day(facts):
    periods = [{"lord": "Me", "start": "2020-01-01", "end": "2030-01-01",
                "sub": [{"lord": "Me", "start": "2020-01-01", "end": "2022-06-01"},
                        {"lord": "Ke", "start": "2022-06-01", "end": "2030-01-01"}]}]
    net = A.preset(facts, "career", "k")
    cts = [{"date": d, "transit": "Sa", "natal": "Me", "aspect": "conjunction", "direction": "direct"}
           for d in ("2022-05-31", "2022-06-01")]
    rows = A.table(facts, net, periods, "2021-01-01", "2023-01-01", "ad", cts, [], [], {"bav": {}, "sav": []})
    assert [c["date"] for c in rows[0]["contacts"]] == ["2022-05-31"]
    assert [c["date"] for c in rows[1]["contacts"]] == ["2022-06-01"]


def test_network_is_frozen_and_edits_are_refused(b, facts):
    n1, n2 = S.topic_network(b, "career"), S.topic_network(b, "career")
    assert n1["hash"] == n2["hash"] and n1["hash"].startswith("sha256:")      # deterministic: a rebuild proves it
    S.activation(b, S.Options(on="2026-10-02", months=2), n1)                 # unchanged: accepted
    for edit in (lambda n: n["planets"].append("Ra"), lambda n: n["entries"].pop(),
                 lambda n: n.update(house=7), lambda n: n.pop("hash")):
        bad = copy.deepcopy(n1)
        edit(bad)
        with pytest.raises(ValueError, match="network"):
            S.activation(b, ON, bad)
    other = S.BirthInput(**(S1 | {"time": "11:40"}))
    with pytest.raises(ValueError, match="another chart"):
        S.activation(other, ON, n1)


def test_children_network_is_theme_only(b):
    n = S.topic_network(b, "children")
    assert "Ju" in n["planets"] and "never laid over dates" in n["note"]
    with pytest.raises(ValueError, match="Theme network only"):
        S.activation(b, ON, n)
    with pytest.raises(ValueError, match="Theme network only"):
        S.retrospective(b, [{"category": "children", "month": "2015-01"}])


def test_meta_present(act, retro, b):
    for out in (act, retro, S.topic_network(b, "finance")):
        assert {"engine", "ayanamsa", "utc_offset"} <= set(out["meta"])


def test_every_preset_entry_is_source_tagged(facts):
    for t in A.PRESETS:
        n = A.preset(facts, t, "k")
        assert n["entries"] and all(e["source"] and e["page_checked"] is False for e in n["entries"])
        assert any(e["role"].startswith("(a)") for e in n["entries"])


def test_contradictory_factors_side_by_side(facts, act):
    career = A.preset(facts, "career", "k")
    karakas = {e["planet"]: e for e in career["entries"] if e["role"] == "(g) karaka"}
    assert set(karakas) == {"Su", "Ju"} and "CR-V09" in karakas["Ju"]["variant"] and "variant" not in karakas["Su"]
    sa = next(r["lords"]["Sa"] for r in A.table(facts, A.preset(facts, "marriage", "k"),
              [{"lord": "Sa", "start": "2020-01-01", "end": "2039-01-01",
                "sub": [{"lord": "Sa", "start": "2020-01-01", "end": "2039-01-01"}]}],
              "2021-01-01", "2022-01-01", "ad", [], [], [], {}))
    assert len(sa["network_roles"]) >= 3                 # every role kept separately, each with its own source
    me = next(r for r in act["segments"] if r["ad"] == "Ra")["lords"]["Me"]
    assert me["dignity"] == "DEBILITATED" and me["network_roles"]   # a debilitated network lord: both facts shown


def test_incomplete_source_support_is_flagged(facts, b):
    reloc = A.preset(facts, "relocation", "k")
    assert any("no karaka" in f for f in reloc["flags"]) and any("Rahu" in f for f in reloc["flags"])
    custom = S.topic_network(b, planets=["Ve", "Ju"])
    assert custom["flags"] and all("unsourced" in e["source"] for e in custom["entries"])
    with pytest.raises(ValueError):
        S.topic_network(b, planets=["Xx"])
    with pytest.raises(ValueError):
        S.topic_network(b, "career", ["Ve"])


def test_missing_moon_is_reported(facts):
    F = {k: v for k, v in facts.items() if not re.match(r"F\.(M\d|Mo\.|moon\.)", k)}
    F = {k: ([q for q in v if q != "Mo"] if isinstance(v, list) else v) for k, v in F.items()}
    n = A.preset(F, "marriage", "k")
    assert "Mo" not in n["planets"] and not any(e["role"].startswith("(f)") for e in n["entries"])
    assert any("Moon missing" in f for f in n["flags"])
    r = A.roles(F, "Ve", n)
    assert r["house_from_moon"] is None and r["owns_from_moon"] is None


def test_birth_time_precision_flags(b):
    assert any("source not stated" in f for f in S.activation(b, S.Options(on="2026-10-02", months=1))["birth_time"]["flags"])
    known = S.BirthInput(**S1, time_source="synthetic, exact")
    out = S.activation(known, S.Options(on="2026-10-02", months=1), "career", "pd")
    assert not any("source not stated" in f for f in out["birth_time"]["flags"])
    assert any("PD rows need" in f for f in out["birth_time"]["flags"]) and "pd" in out["segments"][0]


def test_retrospective_rows(retro, b):
    assert retro["summary"] == f"consistent with {sum(r['consistent'] for r in retro['events'])} of 3"
    assert "not proof" in retro["not_proof"] and retro["analysis"]["stored"].startswith("nothing")
    assert set(retro["analysis"]["networks"]) == {"career", "marriage", "relocation"}
    for r in retro["events"]:
        assert r["periods"] and r["consistent"] == bool(r["period_lords_in_network"])
    again = S.retrospective(b, copy.deepcopy(EVENTS))
    assert again["events"] == retro["events"] and again["summary"] == retro["summary"]   # deterministic


def test_retrospective_never_changes_or_stores(b, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.toml"))
    (tmp_path / "config.toml").write_text(f'data_dir = "{tmp_path / "data"}"\nreports_dir = "{tmp_path / "r"}"\n')
    monkeypatch.chdir(tmp_path)
    nets = {"career": S.topic_network(b, "career")}
    ev, before_nets = [EVENTS[0]], copy.deepcopy(nets)
    before = sorted(os.walk(tmp_path))
    S.retrospective(b, ev, nets)
    assert nets == before_nets and ev == [EVENTS[0]] and sorted(os.walk(tmp_path)) == before
    nets["career"]["planets"] = ["Su"]
    with pytest.raises(ValueError, match="hash differs"):
        S.retrospective(b, ev, nets)


@pytest.mark.parametrize("month", ["2015-13", "1991-01", "2999-01", "15-06"])
def test_retrospective_refuses_bad_months(b, month):
    with pytest.raises(ValueError, match="YYYY-MM"):
        S.retrospective(b, [{"category": "career", "month": month}])


def test_retrospective_is_local_only(b, monkeypatch):
    monkeypatch.setattr(S, "REMOTE", True)
    with pytest.raises(PermissionError, match="local"):
        S.retrospective(b, EVENTS)
    from astro import mcp_server, rest
    assert not any("retro" in n for n in vars(mcp_server)) and not any("retro" in r.path for r in rest.app.routes)
    assert {"/api/v1/activation", "/api/v1/network"} <= {r.path for r in rest.app.routes}


def test_outputs_pass_the_safety_lint(act, retro, b):
    path = os.path.join(config.load().skill_dir, "scripts", "life_lint.py")
    spec = importlib.util.spec_from_file_location("life_lint", path)
    ll = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ll)
    outs = [act, retro] + [S.topic_network(b, t) for t in A.PRESETS]
    hits = [(s, m.group()) for o in outs for s in _strings({k: v for k, v in o.items() if k != "meta"})
            for rx in (ll.SAFETY, ll.CHILD_TIMING, ll.SAFETY_MORE, *(r for _, r in ll.AUDIT)) for m in [rx.search(s)] if m]
    assert not hits


def test_cli_network_and_activation(tmp_path, capsys):
    p = tmp_path / "in.json"
    p.write_text(json.dumps(S1))
    cli.main(["network", str(p), "--topic", "marriage"])
    net = json.loads(capsys.readouterr().out)
    (tmp_path / "net.json").write_text(json.dumps(net))
    cli.main(["activation", str(p), "--network", str(tmp_path / "net.json"), "--on", "2026-10-02", "--months", "2"])
    assert json.loads(capsys.readouterr().out)["network"]["hash"] == net["hash"]
    cli.main(["retro", str(p), "--event", "career:2015-06"])
    assert "consistent with" in json.loads(capsys.readouterr().out)["summary"]
