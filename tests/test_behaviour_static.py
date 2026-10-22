"""P6-2 part A (AI-X8, QA-X7, QA-X8): offline behavioural checks, conflict surfacing, normalized engine snapshots.
Deterministic and network-free. The optional LLM judge over the `must` items is not here: it would measure rubric
agreement only. The knowledge-graph tests skip when the graph is absent (public edition, or a machine without it).
Snapshots live under tests/fixtures/ so the public export (tests/fixtures/**) carries them; SNAPSHOT_UPDATE=1 rewrites."""
import copy
import glob
import json
import os
import re
import sys

import pytest

from astro import config
from astro.calc import engine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = config.load().skill_dir
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import chart_facts as cf  # noqa: E402
import life_lint  # noqa: E402
import render_report as rr  # noqa: E402

CASES_MD = os.path.join(SKILL, "tests", "test-cases.md")
REGISTER = os.path.join(SKILL, "references", "contradiction-register.md")
EXAMPLE = os.path.join(SKILL, "assets", "report", "example-synthetic.json")
SNAP = os.path.join(ROOT, "tests", "fixtures", "snapshots", "engine.json")
FLAGS = re.I

# ---- 1. machine-readable T-cases ------------------------------------------------------------------------------------


def load_cases(path=CASES_MD):
    """(cases, must_not_all) of this edition: the private repo holds the public variants as comments; drop them."""
    text = re.sub(r"^<!-- public-edition.*?^public-edition -->\n?", "", open(path, encoding="utf-8").read(), flags=re.M | re.S)
    cases = [c for b in re.findall(r"^```json cases\n(.*?)^```", text, re.M | re.S) for c in json.loads(b)]
    alls = [json.loads(b) for b in re.findall(r"^```json must_not_all\n(.*?)^```", text, re.M | re.S)]
    return cases, alls[0], text


CASES, ALL, CASES_TEXT = load_cases()
# One negative sample per shared class: the regex must fire (a class that never fires would pass everything).
NEGATIVE = {"exact_date": ["Your move is on 14 March 2027.", "Expect it on 2027-03-14.", "On March 14, 2027 it begins."],
            "death": ["You will die in 2027.", "This shows your lifespan.", "The year of death is clear."],
            "fertility": ["You will conceive in March.", "Your wife will have a son.", "Signs of infertility appear."],
            "certainty": ["This is guaranteed.", "It will certainly happen.", "You are destined to win."],
            "invented_page": ["See LOL p1234.", "Phaladeepika pp. 12345."]}
POSITIVE = ["Venus-Jupiter runs to November 2027, so a window opens around mid-2027.", "BPHS 36.3-4 as quoted at LOL p321.",
            "The pattern suggests, not guarantees, a slower rise."]


def test_cases_parse():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids)) >= 24, ids
    for c in CASES:
        assert re.fullmatch(r"T\d\d", c["id"]) and c["request"] and c["must"] and "must_not" in c and "fixture" in c, c
        assert all(isinstance(x, str) and x for x in c["must"]) and isinstance(c["must_not"], list), c
        if c["fixture"]:
            assert os.path.exists(os.path.join(SKILL, "tests", "fixtures", c["fixture"] + ".json")), c["id"]
    assert set(re.findall(r"T\d\d", re.search(r"Regression subset[^\n]*", CASES_TEXT)[0])) <= set(ids)


def test_every_regex_compiles_and_classes_fire():
    for c in CASES:
        for rx in c["must_not"]:
            re.compile(rx, FLAGS)
    assert set(ALL) == set(NEGATIVE)
    for name, rx in ALL.items():
        for s in NEGATIVE[name]:
            assert re.search(rx, s, FLAGS), (name, s)
    for s in POSITIVE:   # plain, honest prose must pass
        assert not [n for n, rx in ALL.items() if re.search(rx, s, FLAGS)], s


# ---- 2. fixture facts reproduce ---------------------------------------------------------------------------------------

CHARTS = sorted(glob.glob(os.path.join(ROOT, "tests", "fixtures", "**", "chart.json"), recursive=True)
                + glob.glob(os.path.join(SKILL, "tests", "fixtures", "chart_*.json")))


def lk_split(text):
    """Text before the Lal Kitab block: the public edition's stored file ends in a one-line notice instead of the block."""
    return text.replace("\r\n", "\n").partition("\n# Lal Kitab")[0].rstrip("\n")


@pytest.mark.parametrize("path", CHARTS, ids=lambda p: os.path.relpath(p, ROOT))
def test_fixture_facts_reproduce(path):
    stored = open(path[:-5] + ".facts.txt", encoding="utf-8").read()
    now = cf.facts(json.load(open(path, encoding="utf-8")))
    assert lk_split(now) == lk_split(stored), "chart_facts output changed: review the diff, then regenerate the .facts.txt"
    if "# Lal Kitab" in stored:   # private edition: the whole file, Lal Kitab block included
        assert now.rstrip("\n") == stored.replace("\r\n", "\n").rstrip("\n")


# ---- 3. life_lint safety ------------------------------------------------------------------------------------------------


def safety(text):
    return [i for i in life_lint.lint(text, "report")["issues"] if i.startswith("SAFETY")]


def test_life_lint_example_clean():
    example = json.load(open(EXAMPLE, encoding="utf-8"))
    r = life_lint.lint(life_lint.report_text(example), "report")
    assert r["issues"] == [], r["issues"]


@pytest.mark.parametrize("path", [p[:-5] + ".facts.txt" for p in CHARTS] + glob.glob(os.path.join(SKILL, "tests", "fixtures", "*.md")),
                         ids=lambda p: os.path.relpath(p, ROOT))
def test_life_lint_fixtures_no_safety(path):
    assert safety(open(path, encoding="utf-8").read()) == []


def test_life_lint_flags_unsafe():   # the harness reads ['issues'], so prove it can fail
    assert safety("You will die in 2027 and she will conceive a son soon.")


# ---- 4. P3-3 validators and must_not on the example report ------------------------------------------------------------

EXAMPLE_MODEL = json.load(open(EXAMPLE, encoding="utf-8"))


@pytest.fixture(scope="module")
def facts():   # the example's synthetic chart, as in tests/test_grounding.py
    return engine.compute("1992-03-14", "09:40", 0, 51.5, -0.12, on=EXAMPLE_MODEL.get("prepared_on") or "2026-01-01", months=60)


def test_example_validators(facts):
    schema = json.load(open(os.path.join(SKILL, "assets", "report", "report.schema.json"), encoding="utf-8"))
    assert rr.validate(EXAMPLE_MODEL, schema) == []
    assert rr.checks(EXAMPLE_MODEL)[0] == []
    assert rr.grounding(EXAMPLE_MODEL, facts)[0] == []
    assert rr.citations(EXAMPLE_MODEL)[0] == []


def test_example_text_has_no_must_not():
    text = life_lint.report_text(EXAMPLE_MODEL)
    assert len(text) > 500
    rxs = list(ALL.values()) + [rx for c in CASES for rx in c["must_not"]]
    hits = [rx for rx in rxs if re.search(rx, text, FLAGS)]
    assert hits == []
    assert re.search(ALL["death"], text + " You will die in 2027.", FLAGS)   # same text plus a violation does fire


# ---- 5. conflict surfacing: CR-V rows in the register, and their knowledge-graph dispute nodes -------------------------

REF = re.compile(r"\bpp?\d+(?:[–-]\d+)?|\b[IVX]+\.\d+(?:[–-]\d+)?|\bBPHS (?:ch\. )?\d+(?:\.\d+)?")
# Sides that carry no page or verse citation in the register (a finding, listed so a new uncited side fails).
UNCITED = {("CR-V19", "B"), ("CR-V20", "B")}


def register_rows(text=None):
    text = text or open(REGISTER, encoding="utf-8").read()
    rows = {}
    for line in text.splitlines():
        m = re.match(r"\| (CR-V\d\d) \| ", line)
        if m:
            cells = [c.strip() for c in re.split(r"\s\|\s", line.strip().strip("|").strip())]
            rows[m[1]] = cells   # id, topic, position A, position B, class, default
    return rows


def row_problems(cells, graph_sides=None):
    """Why a dispute is not surfaced: a side missing or uncited in the register row, or missing / different in the graph."""
    rid, bad = cells[0], []
    if len(cells) != 6:
        return [f"{rid}: {len(cells)} cells, expected 6"]
    for side, text in zip("AB", cells[2:4]):
        if len(text) < 10:
            bad.append(f"{rid} side {side}: empty")
        elif not REF.search(text) and (rid, side) not in UNCITED:
            bad.append(f"{rid} side {side}: no citation")
        if graph_sides is not None:
            g = graph_sides.get(side, "")
            if not g:
                bad.append(f"{rid} side {side}: absent from the graph")
            elif set(REF.findall(g)) != set(REF.findall(text)):   # wording may differ between builds; citations may not
                bad.append(f"{rid} side {side}: graph citations differ from the register")
    return bad


ROWS = register_rows()


def test_register_has_all_cr_v_rows():
    assert len(ROWS) >= 21 and list(ROWS) == [f"CR-V{i:02d}" for i in range(1, len(ROWS) + 1)], list(ROWS)
    assert UNCITED == {(r, s) for r, c in ROWS.items() for s, t in zip("AB", c[2:4]) if not REF.search(t)}


@pytest.mark.parametrize("rid", list(ROWS))
def test_register_row_shows_both_sides(rid):
    assert row_problems(ROWS[rid]) == []


def test_deleting_one_side_fails():
    rid = "CR-V15"
    for i in (2, 3):
        cells = list(ROWS[rid])
        cells[i] = ""
        assert row_problems(cells), i
    whole = open(REGISTER, encoding="utf-8").read()
    line = next(x for x in whole.splitlines() if x.startswith(f"| {rid} |"))
    cut = whole.replace(line, " | ".join(line.split(" | ")[:3] + line.split(" | ")[4:]))   # drop position B from the text
    assert row_problems(register_rows(cut).get(rid, [rid])), "removing a side from the register text must fail"
    uncited = list(ROWS[rid])
    uncited[3] = "Another school disagrees, no source named"
    assert row_problems(uncited) == [f"{rid} side B: no citation"]


@pytest.fixture(scope="module")
def graph():
    import kg
    gz = os.path.join(ROOT, "knowledge", "graph", "graph.json.gz")
    if os.path.exists(gz) and not os.path.exists(kg.GRAPH):
        kg.GRAPH = gz
    try:
        return kg, kg.load()
    except SystemExit:
        pytest.skip("no knowledge graph (public edition or not built here)")


def graph_sides(g, rid):
    N, out, _ = g
    if f"contradiction:{rid}" not in N:
        return None
    return {kg_attrs(N[e["target"]]).get("side"): kg_attrs(N[e["target"]]).get("text", "")
            for e in out[f"contradiction:{rid}"] if e["relation"] == "HAS_POSITION"}


def kg_attrs(n):
    return n.get("attributes") or {}


@pytest.mark.parametrize("rid", list(ROWS))
def test_kg_returns_both_sides(graph, rid):
    kg, g = graph
    sides = graph_sides(g, rid)
    if sides is None:
        pytest.skip(f"{rid} is in the register but not in this graph build (register-only)")
    assert row_problems(ROWS[rid], sides) == []
    topic = re.sub(r"[*()]", "", ROWS[rid][1])
    found = {cid: pos for _, cid, _, pos in kg.find_contradictions(*g[:2], topic)}
    assert f"contradiction:{rid}" in found, f"kg contradictions '{topic}' did not return {rid}"
    assert {kg_attrs(p).get("side") for p in found[f"contradiction:{rid}"]} == {"A", "B"}


def test_kg_missing_side_fails(graph):
    sides = graph_sides(graph[1], "CR-V02")
    assert row_problems(ROWS["CR-V02"], sides) == []
    assert row_problems(ROWS["CR-V02"], {"A": sides["A"]})
    assert row_problems(ROWS["CR-V02"], {"A": sides["A"], "B": "Another view, different pages p999"})


# ---- 6. normalized engine snapshots ---------------------------------------------------------------------------------------
# Synthetic births already used in tests/test_grounding.py and tests/test_calc_stamp.py. Volatile fields (engine string,
# ephemeris, computed_at_utc, ayanamsa digits) are dropped; degrees round to 2 decimals (36"), dates to the month, so
# Moshier and Swiss Ephemeris files agree. A boundary chart could still flip a month: pick other charts, do not widen.
BIRTHS = {"S1": dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12),
          "S2": dict(date="1990-05-17", time="06:30", tz=5.5, lat=19.07, lon=72.88)}
ON = "2026-01-01"


def normalize(c):
    ym = lambda d: d[:7]   # noqa: E731
    return {
        "meta": {k: c["meta"][k] for k in ("nodes", "utc_offset", "lat", "lon", "transit_date", "dasha_year_days", "flags")},
        "bodies": {n: {"sign": b["sign"], "deg": round(b["deg"], 2), "retro": b["retro"], "nakshatra": b.get("nakshatra"),
                       "pada": b.get("pada"), "D9": b["vargas"]["D9"], "D10": b["vargas"]["D10"]} for n, b in c["bodies"].items()},
        "mc": round(c["mc"], 1),
        "vimshottari": [{"lord": m["lord"], "start": ym(m["start"]), "end": ym(m["end"]), "sub": [s["lord"] for s in m["sub"]]}
                        for m in c["vimshottari"]],
        "transits": {n: {"sign": t["sign"], "house": t["house_from_lagna"]} for n, t in c["transits"].items()},
        "ingresses": [[i["planet"], ym(i["date"]), i["to"]] for i in c["ingresses"]],
    }


def snapshot():
    return {k: normalize(engine.compute(b["date"], b["time"], b["tz"], b["lat"], b["lon"], on=ON, months=60)) for k, b in BIRTHS.items()}


def test_snapshot_stable_and_stored():
    a, b = snapshot(), snapshot()
    assert a == b, "two runs differ"
    assert len(json.dumps(a)) < 40_000   # keep snapshots small
    if os.environ.get("SNAPSHOT_UPDATE") == "1":
        os.makedirs(os.path.dirname(SNAP), exist_ok=True)
        json.dump(a, open(SNAP, "w", encoding="utf-8"), indent=1, sort_keys=True, ensure_ascii=False)
        open(SNAP, "a", encoding="utf-8").write("\n")
    stored = json.load(open(SNAP, encoding="utf-8"))
    assert a == stored, "engine output changed: review it, then SNAPSHOT_UPDATE=1 pytest tests/test_behaviour_static.py"


def test_snapshot_detects_change():
    a = json.load(open(SNAP, encoding="utf-8"))
    b = copy.deepcopy(a)
    b["S1"]["bodies"]["Su"]["deg"] += 0.01
    assert a != b
