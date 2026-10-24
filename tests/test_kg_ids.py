# P5-1: stable rule ids (R-<SRC>-NNNNNN) with rev/supersedes/withdrawn, typed disputes, the verification ladder,
# catalog v2 and the graph checks. Every input here is synthetic (invented source ids TST/TSU, invented sentences);
# no book text. The end-to-end tests run the real tools/kg/extract.py on a throw-away workspace built in tmp_path.
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KG = os.path.join(ROOT, "tools", "kg")
sys.path.insert(0, KG)
import rule_ledger as RL  # noqa: E402

DAY1, DAY2 = "2030-01-01", "2030-02-01"
SATURN = "saturn in the seventh house delays marriage and brings a serious older partner after many years"


def item(node, wording, key="TST p2", src="TST"):
    return dict(node=node, src=src, key=key, wording=wording)


def first_build(*items):
    return RL.assign({}, list(items), DAY1)


# ---------- id assignment ----------
def test_bootstrap_numbers_per_source_in_build_order():
    _, got, review = first_build(item("rule:TST:a", SATURN), item("rule:TSU:b", "jupiter blesses", "TSU p1", "TSU"),
                                 item("rule:TST:c", "mars gives courage", "TST p3"))
    assert [got[n]["rule_id"] for n in ("rule:TST:a", "rule:TSU:b", "rule:TST:c")] == \
        ["R-TST-000001", "R-TSU-000001", "R-TST-000002"]
    assert all(got[n]["rev"] == 1 for n in got) and review == []


def test_no_change_rebuild_gives_identical_ids_and_ledger():
    items = [item("rule:TST:a", SATURN), item("rule:TST:c", "mars gives courage in sports and contests", "TST p3")]
    led1, got1, _ = RL.assign({}, items, DAY1)
    led2, got2, review = RL.assign(led1, items, DAY2)
    assert json.dumps(led1, sort_keys=True) == json.dumps(led2, sort_keys=True)   # not even a date changes
    assert {n: e["rule_id"] for n, e in got1.items()} == {n: e["rule_id"] for n, e in got2.items()} and review == []


def test_edited_bullet_keeps_its_id_with_rev_plus_one():
    led1, got1, _ = first_build(item("rule:TST:a", SATURN))
    edited = SATURN.replace("serious", "steady")
    assert RL.similarity(SATURN, edited) >= 90
    led2, got2, review = RL.assign(led1, [item("rule:TST:a2", edited)], DAY2)
    e = got2["rule:TST:a2"]
    assert e["rule_id"] == got1["rule:TST:a"]["rule_id"] and e["rev"] == 2 and e["nodes"] == ["rule:TST:a", "rule:TST:a2"]
    assert e["revised_on"] == DAY2 and review == ["carried R-TST-000001 rev 2 (same page, wording %.0f)" % RL.similarity(SATURN, edited)]
    led3, got3, _ = RL.assign(led2, [item("rule:TST:a2", edited)], "2030-03-01")      # and stays stable afterwards
    assert got3["rule:TST:a2"]["rev"] == 2 and led3 == led2
    # the old graph node id still resolves, to the same R-id and its current node
    assert RL.resolve(led2, "rule:TST:a") == ("R-TST-000001", led2["rules"]["R-TST-000001"], "R-TST-000001")


def test_no_carry_forward_when_the_page_differs():
    led1, got1, _ = first_build(item("rule:TST:a", SATURN))
    led2, got2, review = RL.assign(led1, [item("rule:TST:a2", SATURN.replace("serious", "steady"), key="TST p3")], DAY2)
    new = got2["rule:TST:a2"]
    assert new["rule_id"] == "R-TST-000002" and new["rev"] == 1 and new["supersedes"] == "R-TST-000001"
    old = led2["rules"]["R-TST-000001"]
    assert old["status"] == "withdrawn" and old["withdrawn_on"] == DAY2 and old["superseded_by"] == "R-TST-000002"
    assert review and review[0].startswith("REVIEW R-TST-000001 withdrawn; successor R-TST-000002") and "different page" in review[0]
    assert RL.resolve(led2, "rule:TST:a")[2] == "R-TST-000002"                       # follows the successor


def test_no_carry_forward_below_90_on_the_same_page():
    led1, _, _ = first_build(item("rule:TST:a", SATURN))
    border = SATURN.replace("brings a serious older partner", "gives an older partner")
    assert 80 <= RL.similarity(SATURN, border) < 90
    led2, got2, review = RL.assign(led1, [item("rule:TST:b", border)], DAY2)
    assert got2["rule:TST:b"]["rule_id"] == "R-TST-000002" and got2["rule:TST:b"]["rev"] == 1
    assert led2["rules"]["R-TST-000001"]["superseded_by"] == "R-TST-000002" and "same page" in review[0]
    other = "venus in the twelfth house favours quiet comforts and private pleasures"
    assert RL.similarity(SATURN, other) < 80
    led3, got3, review = RL.assign(led1, [item("rule:TST:c", other)], DAY2)
    assert got3["rule:TST:c"]["rule_id"] == "R-TST-000002" and "superseded_by" not in led3["rules"]["R-TST-000001"]
    assert review == ["withdrawn R-TST-000001 (no successor)"] and "supersedes" not in got3["rule:TST:c"]


def test_carry_forward_is_one_to_one_and_numbers_are_never_reused():
    led1, _, _ = first_build(item("rule:TST:a", SATURN))
    twins = [item("rule:TST:x", SATURN.replace("many", "several")), item("rule:TST:y", SATURN.replace("serious", "steady"))]
    led2, got2, _ = RL.assign(led1, twins, DAY2)
    ids = sorted(got2[n]["rule_id"] for n in ("rule:TST:x", "rule:TST:y"))
    assert ids == ["R-TST-000001", "R-TST-000002"]
    led3, got3, _ = RL.assign(led2, [item("rule:TST:z", "moon in the fourth house gives a calm home")], "2030-03-01")
    assert got3["rule:TST:z"]["rule_id"] == "R-TST-000003"                           # 1 and 2 are withdrawn, not reused
    assert {e["status"] for k, e in led3["rules"].items() if k != "R-TST-000003"} == {"withdrawn"}


def test_similarity_is_the_token_sort_lcs_ratio():
    assert RL.similarity("abc", "abd") == pytest.approx(200 * 2 / 6)
    assert RL.similarity("house seventh", "seventh house") == 100
    assert RL._lcs("abcbdab", "bdcaba") == 4
    assert RL.wording("Saturn in H7 delays marriage. — PD p191 (pr 161)", "PD") == "saturn in h delays marriage"


# ---------- disputes ----------
@pytest.mark.parametrize("cid, klass, curated, want", [
    ("CR-E01", "U", None, "empirical"),
    ("XB-0123456789", "false_positive (curated 2026-10-02) — agreement", "false_positive", "reviewed_non_conflict"),
    ("XB-0123456789", "school (curated 2026-10-02)", "school", "school_difference"),
    ("XB-0123456789", "translation (curated 2026-10-02)", "translation", "edition_variant"),
    ("XB-0123456789", "compatible (curated 2026-10-02)", "compatible", "contradiction"),
    ("XB-0123456789", "uncurated (from a source map; review before relying)", None, "contradiction"),
    ("CR-S03", "", None, "school_difference"),
    ("CR-N01", "R (school)", None, "school_difference"),
    ("CR-V07", "T (row shift)", None, "edition_variant"),
    ("CR-V08", "T", None, "edition_variant"),
    ("CR-V09", "T/U", None, "contradiction"),
    ("CR-V10", "R", None, "contradiction"),
    ("CR-V11", "U (verse vs notes)", None, "contradiction"),
    ("CR-X02", "compatible (page images checked)", None, "contradiction"),
])
def test_dispute_type(cid, klass, curated, want):
    assert RL.dispute_type(cid, klass, curated) == want


# ---------- verification ladder ----------
PAGE = "The synthetic page says Saturn placed in the seventh house delays partnership for years."
ANCHOR = {"prefix": "page says", "exact": "Saturn placed in the seventh house", "suffix": "delays partnership"}


def ladder(**kw):
    args = dict(rule_id="R-TST-000001", flags=[], rule_text="Saturn placed seventh delays", page_texts=[PAGE],
                page_check=None, extraction_date=DAY1, today=DAY2)
    return RL.verification(**{**args, **kw})


def test_verification_ladder_levels():
    check = {"rule_id": "R-TST-000001", "by": "owner", "on": DAY2, "method": "read the PDF page", "result": "supported",
             "anchor": ANCHOR}
    rec, prob = ladder(page_check=check)
    assert rec["level"] == "human-page-checked" and rec["anchor"] == ANCHOR and rec["by"] == "owner" and prob is None
    assert ladder(flags=["image-checked"])[0]["level"] == "image-checked"
    assert ladder()[0] == {"level": "text-layer", "by": "tools/kg/extract.py", "on": DAY2,
                           "method": ladder()[0]["method"]}
    assert ladder(rule_text="Jupiter blesses teachers")[0] == {"level": "none"}


def test_stale_or_long_anchor_is_not_used():
    stale = {"by": "owner", "on": DAY2, "anchor": dict(ANCHOR, exact="Mars placed in the tenth house")}
    rec, prob = ladder(page_check=stale, flags=["image-checked"])
    assert rec["level"] == "image-checked" and "stale anchor" in prob                # falls back, and is reported
    long_anchor = {"by": "owner", "anchor": {"exact": " ".join(["word"] * 16)}}
    rec, prob = ladder(page_check=long_anchor)
    assert rec == {"level": "none"} and "longer than 15 words" in prob
    assert RL.anchor_found(ANCHOR, PAGE.upper().replace(" ", "  "))                   # survives re-OCR spacing/case


def test_verification_table_gives_the_per_book_verified_share():
    recs = [("TST", {"level": "human-page-checked", "result": "supported"}), ("TST", {"level": "image-checked"}),
            ("TST", {"level": "human-page-checked", "result": "not-supported"}), ("TST", {"level": "none"}),
            ("TSU", {"level": "text-layer"})]
    rows = RL.verification_table(recs)
    assert rows[2] == "| TST | 4 | 1 | 0 | 1 | 2 | 50.0% |" and rows[3] == "| TSU | 1 | 0 | 1 | 0 | 0 | 0.0% |"


# ---------- graph checks ----------
def good_graph():
    rule = lambda i, src="TST": {"id": f"rule:{src}:{i}", "node_type": "Rule", "attributes": {
        "source": src, "rule_id": f"R-{src}-{i:06d}", "rev": 1, "verification": {"level": "none"}}}
    con = lambda c, t, **kw: {"id": f"contradiction:{c}", "node_type": "Contradiction",
                              "attributes": {"dispute_type": t, **kw}}
    return [rule(1), rule(2), rule(1, "TSU"), con("CR-V01", "contradiction"),
            con("XB-1", "reviewed_non_conflict", review_note="agreement"), con("CR-E01", "empirical")]


def test_graph_problems_accepts_a_valid_graph_and_names_each_fault():
    assert RL.graph_problems(good_graph(), 2) == []
    g = good_graph()
    g[3]["attributes"]["dispute_type"] = "false_positive (curated)"
    g[1]["attributes"]["rule_id"] = "R-TST-000001"
    g[2]["attributes"]["rule_id"] = "R-TST-000009"
    g[0]["attributes"]["verification"] = {"level": "checked", "anchor": {"exact": " ".join(["w"] * 16)}}
    g[4]["attributes"].pop("review_note")
    bad = "\n".join(RL.graph_problems(g, 3))
    for want in ("dispute_type 'false_positive (curated)'", "rule_id R-TST-000001 on 2 rules", "is not R-TSU-NNNNNN",
                 "verification level 'checked'", "anchor longer than 15 words", "without a review note",
                 "3 CONTRADICTS edges for 3 disputes"):
        assert want in bad, want


# ---------- catalog v2 ----------
def test_catalog_v2_schema_and_owner_checks():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.load(open(os.path.join(ROOT, "schemas", "catalog.v2.schema.json"), encoding="utf-8"))
    cat = json.load(open(os.path.join(ROOT, "knowledge", "catalog.json"), encoding="utf-8"))
    jsonschema.validate(cat, schema)
    for b in cat["books"]:                       # every value the repo cannot establish is named for the owner
        unknown = {k for k in ("publisher", "base_text", "tier_translation") if b[k] == "unknown"}
        assert unknown <= set(b["owner_checks"]), (b["id"], unknown)
    broken = json.loads(json.dumps(cat))
    broken["books"][0]["rights"]["death_years"] = {"Someone": "about 1950"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, schema)
    del broken["books"][0]["rights"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, schema)


def test_public_catalog_is_metadata_only(tmp_path):
    if not os.path.exists(os.path.join(ROOT, "tools", "export_public.py")):
        pytest.skip("public edition: the exporter is private")
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_public as ex
    ex.catalog(str(tmp_path))
    cat = json.load(open(tmp_path / "knowledge" / "catalog.json", encoding="utf-8"))
    allowed = {"id", "title", "author", "translator", "edition", "year", "language", "system", "tier", "text_file",
               "text_layer", "page_convention", "pages", "copyright", "added", "work_id", "volume", "publisher",
               "base_text", "tier_translation", "rights", "owner_checks"}
    assert cat["books"] and not [(b["id"], k) for b in cat["books"] for k in b if k not in allowed]
    assert "library_root" not in cat and not [b for b in cat["books"] if set(b["rights"]) - {
        "checked_on", "sources", "death_years", "redistribution"}]


# ---------- end to end: the real extract.py on a synthetic workspace ----------
def skill_dir():
    for d in (os.path.join(ROOT, "skill", "astrology-consultation"),
              os.path.join(ROOT, "plugins", "astrology-consultation", "skills", "astrology-consultation")):
        if os.path.exists(os.path.join(d, "scripts", "vocab.py")):
            return d
    pytest.skip("skill scripts (vocab.py) not found")


MAP = """# TST source map (synthetic test fixture, invented text)

## 1. Header
- Synthetic book used only by the tests; it has no real source at all.

## 3. Topic rules
### 3.1 Synthetic placements
- [AUTHOR] Saturn placed in the seventh house delays partnership and brings a serious older partner — p2
- [AUTHOR] Jupiter in the ninth house blesses the native with wise teachers and pilgrimages abroad — p3
- [AUTHOR] image-checked: Mars in the tenth house gives energetic leadership in engineering careers — p1

## 7. Contradiction notes
- [Reader note] Moon in the fourth house: comfort at home, TST p2 vs restless moves of residence, TSU p1
"""
REGISTER = """# Synthetic register

| ID | Topic | Version A | Version B | Class | Default |
|---|---|---|---|---|---|
| CR-V01 | Saturn in the seventh | Delay — TST p2 | Early union — TSU p1 | R | A [Low] |
| CR-V02 | Spelling slip | One reading — TST p1 | Another reading — TSU p2 | T | B [Medium] |
| CR-E01 | Empirical test | Holds — TST p3 | Fails — TSU p2 | U | none [Low] |

| ID | Issue | One system | Other system | Default |
|---|---|---|---|---|
| CR-S01 | House lords | Fixed lords — TST p1 | Lords by sign — TSU p1 | Never mix |
"""
PAGES = {"TST": ["Mars in the tenth house gives leadership; chapter on careers and engineering work.",
                 "Saturn placed in the seventh house delays partnership; an older partner is described.",
                 "A list of festival dates and numbers without any planets at all."],
         "TSU": ["Restless moves of residence for the Moon in the fourth.", "A short glossary page."]}


def bullet_hash(line):
    return hashlib.sha1(line[2:].strip().encode()).hexdigest()[:10]


GRAPH_CHECKS = os.path.join(ROOT, "validation", "graph_checks.py")


def make_ws(tmp_path):
    ws, lib = tmp_path / "ws", tmp_path / "lib"
    for d in ("tools/kg", "knowledge/curation", "text", "sourcemaps", "validation", "graphify-out",
              "astrology-prediction/references", "astrology-prediction/data/lal-kitab"):
        (ws / d).mkdir(parents=True)
    lib.mkdir()
    for f in ("extract.py", "rule_ledger.py"):
        shutil.copy(os.path.join(KG, f), ws / "tools" / "kg" / f)
    if os.path.exists(GRAPH_CHECKS):              # CI's sparse checkout leaves validation/ out (archive policy)
        shutil.copy(GRAPH_CHECKS, ws / "validation" / "graph_checks.py")
    os.symlink(os.path.join(skill_dir(), "scripts"), ws / "astrology-prediction" / "scripts")
    (ws / "astrology-prediction" / "references" / "contradiction-register.md").write_text(REGISTER)
    (ws / "astrology-prediction" / "data" / "lal-kitab" / "LalKitab_Shrimali_Knowledge_Base_v2.2.md").write_text("")
    books = []
    for src, pages in PAGES.items():
        (lib / f"{src}.pdf").write_bytes(f"synthetic {src}".encode())
        with open(ws / "text" / f"{src}.jsonl", "w") as f:       # generated in tmp only, never committed
            f.writelines(json.dumps({"page": i + 1, "text": t}) + "\n" for i, t in enumerate(pages))
        books.append(dict(id=src, title=f"Synthetic {src}", author="Nobody", edition="test", language="English",
                          system="Parashari", tier="modern", text_file=f"{src}.jsonl", text_layer="synthetic",
                          page_convention="PDF p", pages=len(pages), file=f"{src}.pdf",
                          sha256=hashlib.sha256(f"synthetic {src}".encode()).hexdigest()))
    cat = json.load(open(os.path.join(ROOT, "knowledge", "catalog.json"), encoding="utf-8"))
    json.dump({"version": 2, "tiers": cat["tiers"], "library_root": str(lib), "books": books},
              open(ws / "knowledge" / "catalog.json", "w"))
    (ws / "sourcemaps" / "TST.md").write_text(MAP)
    note = next(ln for ln in MAP.splitlines() if ln.startswith("- [Reader note]"))
    json.dump({"curated": "2030-01-01", "disputes": [{"id": "XB-" + bullet_hash(note), "class": "false_positive",
                                                      "note": "synthetic: recorded as agreement"}]},
              open(ws / "knowledge" / "curation" / "xb_curation.json", "w"))
    return ws


def extract(ws):
    r = subprocess.run([sys.executable, str(ws / "tools" / "kg" / "extract.py")], cwd=ws, capture_output=True,
                       text=True, timeout=600)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-3000:]
    ext = json.load(open(ws / "knowledge" / "extraction.json", encoding="utf-8"))
    return {n["id"]: n for n in ext["nodes"]}, ext["edges"]


def rule_ids(N):
    return {n["id"]: (n["attributes"]["rule_id"], n["attributes"]["rev"]) for n in N.values() if n["node_type"] == "Rule"}


def graph_checks(ws, N, edges):
    json.dump({"nodes": list(N.values()), "links": edges}, open(ws / "graphify-out" / "graph.json", "w"))
    return subprocess.run([sys.executable, str(ws / "validation" / "graph_checks.py")], cwd=ws, capture_output=True,
                          text=True, timeout=120)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    ws = make_ws(tmp_path_factory.mktemp("kg"))
    N, edges = extract(ws)
    return ws, N, edges


def test_extract_assigns_ids_types_and_ladder(built):
    ws, N, edges = built
    ids = rule_ids(N)
    assert sorted(i for i, _ in ids.values()) == [f"R-TST-{i:06d}" for i in range(1, 5)]
    by_text = {n["attributes"]["text"][:6]: n["attributes"] for n in N.values() if n["node_type"] == "Rule"}
    assert by_text["image-"]["verification"]["level"] == "image-checked"
    assert by_text["Saturn"]["verification"]["level"] == "text-layer"
    assert by_text["Jupite"]["verification"] == {"level": "none"}
    types = {k.split(":", 1)[1]: n["attributes"]["dispute_type"] for k, n in N.items() if n["node_type"] == "Contradiction"}
    xb = next(k for k in types if k.startswith("XB-"))
    assert types == {"CR-V01": "contradiction", "CR-V02": "edition_variant", "CR-E01": "empirical",
                     "CR-S01": "school_difference", xb: "reviewed_non_conflict"}
    assert N[f"contradiction:{xb}"]["attributes"]["review_note"] == "synthetic: recorded as agreement"
    contra = [e for e in edges if e["relation"] == "CONTRADICTS"]
    assert len(contra) == 4 and not [e for e in contra if xb in e["source"]]
    prov = (ws / "validation" / "provenance.md").read_text()
    assert "headline (type contradiction): 1" in prov and "## Verification ladder per book" in prov
    assert "| TST | 4 | 1 | 2 | 1 | 0 | 25.0% |" in prov
    led = json.load(open(ws / "knowledge" / "curation" / "rule_ids.json"))
    assert sorted(led["rules"]) == sorted(i for i, _ in ids.values())


def test_extract_no_change_rebuild_is_identical(built):
    ws, N, _ = built
    before = (ws / "knowledge" / "curation" / "rule_ids.json").read_bytes()
    N2, _ = extract(ws)
    assert rule_ids(N2) == rule_ids(N) and (ws / "knowledge" / "curation" / "rule_ids.json").read_bytes() == before


@pytest.mark.skipif(not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                  "validation", "graph_checks.py")),
                    reason="validation/ is not in this checkout (CI sparse checkout keeps archived analysis off the runner)")
def test_graph_checks_validates_the_enums(built):
    ws, N, edges = built
    r = graph_checks(ws, N, edges)
    assert r.returncode == 0 and "headline (type contradiction) 1" in r.stdout, r.stdout + r.stderr
    bad = json.loads(json.dumps(N))
    bad["contradiction:CR-V01"]["attributes"]["dispute_type"] = "false_positive (curated)"
    r = graph_checks(ws, bad, edges)
    assert r.returncode == 1 and "FAIL dispute types" in r.stdout, r.stdout + r.stderr


def test_extract_edit_keeps_id_and_page_change_does_not(tmp_path):
    ws = make_ws(tmp_path)
    N1, _ = extract(ws)
    sat = next(n for n in N1.values() if n["node_type"] == "Rule" and n["attributes"]["text"].startswith("Saturn"))
    jup = next(n for n in N1.values() if n["node_type"] == "Rule" and n["attributes"]["text"].startswith("Jupiter"))
    m = MAP.replace("serious older", "steady older").replace("pilgrimages abroad — p3", "pilgrimages abroad — p2")
    (ws / "sourcemaps" / "TST.md").write_text(m)
    N2, _ = extract(ws)
    sat2 = next(n for n in N2.values() if n["node_type"] == "Rule" and n["attributes"]["text"].startswith("Saturn"))
    jup2 = next(n for n in N2.values() if n["node_type"] == "Rule" and n["attributes"]["text"].startswith("Jupiter"))
    assert sat2["id"] != sat["id"] and sat2["attributes"]["rule_id"] == sat["attributes"]["rule_id"]
    assert sat2["attributes"]["rev"] == 2 and sat2["attributes"]["former_ids"] == [sat["id"]]
    assert jup2["attributes"]["rule_id"] == "R-TST-000005" and jup2["attributes"]["rev"] == 1   # page changed: new id
    led = json.load(open(ws / "knowledge" / "curation" / "rule_ids.json"))
    old = led["rules"][jup["attributes"]["rule_id"]]
    assert old["status"] == "withdrawn" and old["superseded_by"] == "R-TST-000005"
    assert jup2["attributes"]["supersedes"] == jup["attributes"]["rule_id"]
    assert "REVIEW " + jup["attributes"]["rule_id"] in (ws / "validation" / "provenance.md").read_text()
    assert RL.resolve(led, sat["id"])[0] == sat["attributes"]["rule_id"]               # old hash id still resolves


def test_real_graph_bootstrap_is_stable():
    """On the committed graph (private edition): a bootstrap assignment, then a rebuild, gives the same ids."""
    gz = os.path.join(ROOT, "knowledge", "extraction.json.gz")
    if not os.path.exists(gz):
        pytest.skip("no extraction.json.gz (public edition)")
    with gzip.open(gz, "rt", encoding="utf-8") as f:
        rules = [n for n in json.load(f)["nodes"] if n.get("node_type") == "Rule"]
    items = [dict(node=n["id"], src=n["attributes"]["source"], key=(n["attributes"].get("pages") or ["§"])[0],
                  wording=RL.wording(n["attributes"]["text"])) for n in rules]
    led, got, _ = RL.assign({}, items, DAY1)
    led2, got2, review = RL.assign(led, items, DAY2)
    assert led2 == led and review == [] and len({e["rule_id"] for e in got.values()}) == len(rules)
