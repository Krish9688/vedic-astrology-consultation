# P3-2: stable JSON fact ids (chart_facts.py --json, schemas/derived_facts.schema.json) next to the unchanged text. Synthetic charts only.
import hashlib
import json
import os
import re
import subprocess
import sys

import jsonschema
import pytest

from astro import config, service as S

SCRIPT = os.path.join(config.load().skill_dir, "scripts", "chart_facts.py")
SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "schemas", "derived_facts.schema.json")))
sys.path.insert(0, os.path.dirname(SCRIPT))
import chart_facts as cf  # noqa: E402

FULL = {"asc": {"sign": "Cancer", "deg": 12.5}, "planets": {
    "Su": {"sign": "Cancer", "deg": 10.2}, "Mo": {"sign": "Pisces", "deg": 3.1}, "Ma": {"sign": "Scorpio", "deg": 22.0},
    "Me": {"sign": "Cancer", "deg": 20.0}, "Ju": {"sign": "Sagittarius", "deg": 8.0}, "Ve": {"sign": "Libra", "deg": 14.0},
    "Sa": {"sign": "Cancer", "deg": 14.0, "retro": True}, "Ra": {"sign": "Taurus", "deg": 5.0}, "Ke": {"sign": "Scorpio", "deg": 5.0}}}
NO_DEG = {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Leo"}, "Mo": {"sign": "Cancer"}, "Ju": {"sign": "Cancer"}, "Ma": {"sign": "Libra"}}}
# sha256 of the Parashari part (everything before the Lal Kitab block) of facts() for FULL and NO_DEG, frozen before P3-2
TEXT_HASH = {"full": "0f8e894dee5c7d82", "nodeg": "7a84305f4014aa27"}


def _parashari(text):
    return text.split("\n# Lal Kitab")[0]


def test_json_validates_against_schema_and_cli():
    for ch in (FULL, NO_DEG):
        jsonschema.validate(cf.facts_json(ch), SCHEMA)
    p = subprocess.run([sys.executable, SCRIPT, "--json", "-"], capture_output=True, text=True)   # not a file: usage error, not a crash
    assert p.returncode != 0
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "chart.json")
        json.dump(FULL, open(path, "w"))
        out = subprocess.run([sys.executable, SCRIPT, "--json", path], capture_output=True, text=True, check=True).stdout
    assert json.loads(out) == json.loads(json.dumps(cf.facts_json(FULL)))
    jsonschema.validate(json.loads(out), SCHEMA)


def test_schema_rejects_bad_ids_and_values():
    good = cf.facts_json(NO_DEG)
    for bad in ({"X.Sa.house": 1}, {"F.": 1}, {"F.Sa house": 1}, {"F.Sa.x": {"a": 1}}, {"F.Sa.x": [[1]]}):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(dict(good, facts=bad), SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(dict(good, schema="derived_facts/2"), SCHEMA)


def test_ids_are_stable():
    a, b = cf.facts_json(FULL), cf.facts_json(json.loads(json.dumps(FULL)))
    assert a == b and list(a["facts"]) == list(b["facts"])
    other = json.loads(json.dumps(FULL))
    other["asc"]["sign"], other["planets"]["Ju"]["sign"] = "Leo", "Aries"
    ny = lambda j: {k for k in j["facts"] if not k.startswith("F.yoga.")}   # yoga ids exist only for definitions that apply
    assert ny(cf.facts_json(other)) == ny(a)                               # same planets present -> same ids
    nodeg = {"asc": {"sign": "Cancer"}, "planets": {p: {"sign": v["sign"]} for p, v in FULL["planets"].items()}}
    assert ny(cf.facts_json(nodeg)) == ny(a)           # absent degrees give null, not missing ids
    assert cf.facts_json(nodeg)["facts"]["F.Sa.combust"] is None and cf.facts_json(nodeg)["facts"]["F.Ju.d9"] is None
    ids = set(a["facts"])
    for want in ("F.asc.sign", "F.asc.deg", "F.Sa.combust", "F.Ju.d9_dignity", "F.H7.lord", "F.H7.notes", "F.M4.lord_house",
                 "F.moon.malefic_waning", "F.moon.malefic_72", "F.yoga.KUJA-PD11_3.holds", "F.dispositor.chains"):
        assert want in ids, want


def test_values_agree_with_the_text():
    text, f = cf.facts(FULL), cf.facts_json(FULL)["facts"]
    for h in range(1, 13):
        line = next(l for l in text.splitlines() if l.startswith(f"- H{h} "))
        assert f"lord {cf.NAME[f[f'F.H{h}.lord']]} in H{f[f'F.H{h}.lord_house']}" in line
        assert f"occ {','.join(f[f'F.H{h}.occupants']) or '—'} |" in line
    for p in ("Su", "Me", "Ve", "Sa", "Ju", "Ma"):
        line = next(l for l in text.splitlines() if l.startswith(f"- {cf.NAME[p]}: ") and " H" in l)
        assert ("COMBUST" in line) == (f[f"F.{p}.combust"] is True), (p, line)
        assert f"H{f[f'F.{p}.house']};" in line and f"D9 {f[f'F.{p}.d9']}" in line
        assert ("VARGOTTAMA" in line) == f[f"F.{p}.vargottama"]
        assert ("retrograde" in line) == f[f"F.{p}.retro"]
    assert f["F.Sa.combust"] is True and f["F.Me.combust"] is True and f["F.Ju.combust"] is False and f["F.Sa.retro"] is True
    assert f["F.Sa.dignity"] == "none" and f["F.Su.sign_relation"] == "friend's sign" and f["F.Me.sign_relation"] == "enemy's sign" and f["F.Ju.dignity"] == "own sign" and f["F.Ra.sign_relation"] is None
    assert f["F.Ra.moolatrikona"] is None and f["F.Mo.moolatrikona"] is None
    for line in text.splitlines():                                        # every candidate line has its three ids
        m = re.match(r"- \[([^\]]+)\]", line)
        if m:
            k = "F.yoga." + m.group(1).replace(".", "_")
            assert f[k + ".holds"] is (True if ": HOLDS." in line else None if ": undetermined." in line else False)
            assert f[k + ".detail"] and f[k + ".source"]
    assert ("Dispositor chains: " + "; ".join(f["F.dispositor.chains"])) in text
    assert f["F.moon.phase"] in ("waxing", "waning") and f["F.moon.malefic_waning"] == ("Mo" in cf.derive(FULL)["malefic"])


def test_no_lal_kitab_in_ids_and_conventions_named():
    j = cf.facts_json(dict(FULL, lk_houses={"Su": 4}))
    blob = json.dumps(j)
    assert "Lal Kitab" not in blob and "lk_" not in blob.lower()
    assert {"houses", "node_aspects", "waning_moon"} <= set(j["conventions"])


# candidate lines added by P4-1/P4-2 after the hash was frozen: removed before hashing, so every older line stays
# byte-identical (their own fixtures: tests/test_yoga_definitions.py)
P4_1_LINE = re.compile(r"^- \[(SUNAPHA|ANAPHA|DURADHARA|VESI|VOSI|UBHAYACHARI|ADHI|AMALA|BUDHADITYA|LAKSHMI|VIPARITA|NB|"
                       r"KUJA-HJH2)\b.*\n", re.M)


def test_text_output_unchanged():
    """Frozen Parashari text: the JSON refactor shared helpers with facts(); the words must not move."""
    plain = lambda ch: P4_1_LINE.sub("", _parashari(cf.facts(ch)).replace(cf.COMPUTED, "", 1))   # P3-1: header tag
    got = {k: hashlib.sha256(plain(ch).encode()).hexdigest()[:16] for k, ch in (("full", FULL), ("nodeg", NO_DEG))}
    assert got == TEXT_HASH, got


def test_consultation_context_carries_fact_ids():
    ctx = S.consultation_context("career?", S.BirthInput(date="1990-05-17", time="06:30", tz="+05:30", lat=19.07, lon=72.88))
    assert isinstance(ctx["derived_facts"], str) and ctx["derived_facts"].startswith("# Parashari D1")
    ids = ctx["derived_fact_ids"]
    assert ids["schema"] == "derived_facts/1"
    jsonschema.validate(ids, SCHEMA)
    assert ids["facts"]["F.H7.lord"] in cf.NAME
