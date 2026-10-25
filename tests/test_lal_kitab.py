# Tests of the Lal Kitab block in scripts/lal_kitab.py (public and private editions since 3.7, owner decision
# 2026-10-25; they were private-only under council option B2). All inputs are synthetic.
import os
import sys

import pytest

from astro import config

pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(config.load().skill_dir, "scripts", "lal_kitab.py")),
                                reason="no Lal Kitab module in this skill folder")
TABLE = os.path.join(config.load().skill_dir, "data", "lal-kitab", "LalKitab_Varshaphal_Table_v2.2.csv")
needs_table = pytest.mark.skipif(not os.path.exists(TABLE), reason="the Varshaphal table is a private data file, not distributed")


def _chart_facts():
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import chart_facts as cf
    return cf


def test_lal_kitab_block_does_not_depend_on_the_private_kb():
    # the block is the same with and without the private knowledge base: it never reads it (3.7)
    cf = _chart_facts()
    lk = cf._lal_kitab()
    assert not hasattr(lk, "KB_FILE") and not hasattr(lk, "public_lk")
    ch = {"asc": {"sign": "Cancer"}, "planets": {
        "Su": {"sign": "Cancer"}, "Me": {"sign": "Leo"}, "Ve": {"sign": "Leo"}, "Ma": {"sign": "Virgo"}, "Ke": {"sign": "Scorpio"},
        "Sa": {"sign": "Aquarius"}, "Ju": {"sign": "Taurus"}, "Ra": {"sign": "Taurus"}, "Mo": {"sign": "Gemini"}}}
    out = cf.facts(ch)
    sec = out[out.index("# Lal Kitab"):]
    assert "Saturn H8: in PAKKA GHAR" in sec and "not installed" not in sec
    assert "  Rin (debt)" in sec and "  Remedy pre-check" in sec and "  Sleeping houses (LK1952" in sec


def test_lal_kitab_shared_pakka_houses_are_not_ally_or_rival():
    # council 2026-10-11 (R1/R3): houses 7, 8, 12 belong to two planets each; sharing a house is not an exchange
    cf = _chart_facts()
    lk = lambda pl: [l for l in cf.facts({"asc": {"sign": "Aries"}, "planets": {k: {"sign": v} for k, v in pl.items()}}).splitlines()
                     if l.startswith("- ")]
    shared = "\n".join(lk({"Ma": "Scorpio", "Sa": "Scorpio", "Ve": "Libra", "Me": "Libra", "Ju": "Pisces"}))
    assert "ALLY" not in shared and "rival" not in shared, shared
    exchange = "\n".join(lk({"Ma": "Capricorn", "Sa": "Scorpio"}))          # Mars in 10 (Saturn's), Saturn in 8 (Mars's)
    assert "ALLY with Sa" in exchange, exchange


# Golden outputs (LAL-KITAB-ROADMAP §5, council 6): the Lal Kitab block for 52 synthetic charts, frozen. Any change
# in lal_kitab.py shows here as a diff; regenerate with UPDATE_LK_GOLDEN=1 only after explaining every changed line.
GOLDEN = os.path.join(os.path.dirname(__file__), "lk_golden", "lk_golden.json")
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
         "Aquarius", "Pisces"]
BASE = dict(Su=1, Mo=2, Ma=3, Me=4, Ju=5, Ve=6, Sa=9, Ra=11, Ke=5)
TARGETED = {   # one chart per roadmap fix (lk_houses maps; Aries lagna)
    "F9 Mars in 8": dict(BASE, Ma=8), "F10 Saturn in 11": dict(BASE, Sa=11), "F10 Saturn with Jupiter": dict(BASE, Sa=5),
    "F11 Sun+Rahu": dict(BASE, Ra=1, Ke=7), "F11 Moon+Ketu": dict(BASE, Ke=2, Ra=8), "F11 Moon+Rahu": dict(BASE, Ra=2, Ke=8),
    "F11 Sun+Ketu": dict(BASE, Ke=1, Ra=7), "F5 Rahu in 7": dict(BASE, Ra=7, Ke=1), "F5 Rahu in 12": dict(BASE, Ra=12, Ke=6),
    "p48 Sun+Saturn in 10": dict(BASE, Su=10, Sa=10), "p41 Jupiter alone in 10": dict(BASE, Ju=10),
    "F8 aspects from 3, 5, 7": dict(BASE, Ve=7, Sa=3),
}


def _golden_charts():
    import random
    rnd, charts = random.Random(20261018), {}
    for i in range(40):
        pl = {p: {"sign": rnd.choice(SIGNS)} for p in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra")}
        pl["Ke"] = {"sign": SIGNS[(SIGNS.index(pl["Ra"]["sign"]) + 6) % 12]}
        ch = {"asc": {"sign": rnd.choice(SIGNS)}, "planets": pl}
        if i % 8 == 7:
            ch["lk_houses"] = {"Su": rnd.randint(1, 12)}
        charts[f"seeded {i:02d}"] = ch
    for name, houses in TARGETED.items():
        charts[name] = {"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[h - 1]} for p, h in houses.items()},
                        "lk_houses": houses}
    return charts


def _lk_block(cf, ch):
    t = cf.facts(ch)
    return t[t.index("\n# Lal Kitab") + 1:].splitlines()


def test_lal_kitab_golden_outputs():
    import json
    cf = _chart_facts()
    now = {k: _lk_block(cf, ch) for k, ch in _golden_charts().items()}
    if os.environ.get("UPDATE_LK_GOLDEN"):
        os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
        json.dump(now, open(GOLDEN, "w"), indent=1, ensure_ascii=False)
    old = json.load(open(GOLDEN))
    diff = {k: ([x for x in old.get(k, []) if x not in v], [x for x in v if x not in old.get(k, [])])
            for k, v in now.items() if v != old.get(k)}
    assert not diff, json.dumps(diff, indent=1, ensure_ascii=False)[:4000]


# LAL-KITAB-ROADMAP §2 step 1 (council 4 R1 F8–F12), council 6 implementation
def _line(cf, houses, planet):
    ch = {"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[h - 1]} for p, h in houses.items()}, "lk_houses": houses}
    return next(x for x in _lk_block(cf, ch) if x.startswith(f"- {planet} "))


@pytest.mark.parametrize("bad", [{"Su": 13}, {"Su": 0}, {"Su": "7"}, {"Su": True}, {"Xx": 3}, ["Su", 1]])
def test_f12_lk_houses_validated(bad):
    """F12: only planet keys and integer houses 1–12; the Parashari facts still print."""
    cf = _chart_facts()
    out = cf.facts({"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Leo"}}, "lk_houses": bad})
    assert "Lal Kitab block failed (ValueError: lk_houses" in out and "H5 Leo: occ Su" in out


def test_f9_mars_in_8_exaltation_is_disputed():
    """F9: CR-L03 — Mars exalted in 10 certain, in 8 disputed (LK1952 p72–73 vs KB X1)."""
    cf = _chart_facts()
    assert "LK-exalted (disputed in 8: CR-L03; LK1952 p72: none exalted in 8)" in _line(cf, dict(BASE, Ma=8), "Mars")
    assert "LK-exalted (B4)" in _line(cf, dict(BASE, Ma=10), "Mars")


@pytest.mark.parametrize("houses", [dict(BASE, Sa=11), dict(BASE, Sa=3, Ju=3)])
def test_f10_dharmi_transforms_sinful_saturn(houses):
    """F10: KB B7 p41 calls Saturn in 3/11 sinful; p42 says it turns dharmi (11, or with Jupiter) — dharmi wins."""
    line = _line(_chart_facts(), houses, "Saturn")
    assert "DHARMI (B7 p42; transforms the 'sinful' placement of p41)" in line and "'sinful' placement (B7 p41)" not in line


@pytest.mark.parametrize("nodes,planet,label", [
    (dict(Ra=1, Ke=7), "Sun", "solar eclipse (Sun+Rahu: B7 p73; LK1952 p54)"),
    (dict(Ke=1, Ra=7), "Sun", "solar eclipse (Sun+Ketu: B7 p73; LK1952 p54 names Rahu only)"),
    (dict(Ra=2, Ke=8), "Moon", "lunar eclipse (Moon+Rahu: KB p201; LK1952 p54 names Ketu)"),
    (dict(Ke=2, Ra=8), "Moon", "lunar eclipse (Moon+Ketu: LK1952 p54)")])
def test_f11_eclipse_split_by_source(nodes, planet, label):
    """F11: p73 covers the Sun only; Moon+Rahu is p201; LK1952 p54 pairs Sun+Rahu and Moon+Ketu."""
    line = _line(_chart_facts(), dict(BASE, **nodes), planet)
    assert label in line and "eclipse: with node" not in line


def test_f8_aspect_disputes_on_the_right_rows():
    """F8: CR-L02 / R11 — 2→6 and 7→2 disputed, row 5's printed '9,11' doubted, row 3 undisputed, 7 and 10 aspect
    nothing (R11 ✅, KB p67, p69)."""
    cf = _chart_facts()
    h = dict(Su=1, Mo=2, Ma=3, Me=4, Ju=5, Ve=7, Sa=10, Ra=11, Ke=5)
    assert "LK aspect → H6 ❓" in _line(cf, h, "Moon")
    assert "LK aspect → H9,11 (11 half, LK1952 p123)" in _line(cf, h, "Mars") and "❓" not in _line(cf, h, "Mars")
    assert "LK aspect → H9 (half, LK1952 p123; B5 printed 9,11)" in _line(cf, h, "Jupiter")   # council 7: row 5 settled
    assert "LK aspect: none from H7 (R11) — disputed: a table prints → H2 ❓ (p38)" in _line(cf, h, "Venus")
    assert "LK aspect: none from H10 (R11)" in _line(cf, h, "Saturn")
    out = "\n".join(_lk_block(cf, {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Aries"}}}))
    assert "9, 11, 12 cast no aspect in either book's table" in out


# LAL-KITAB-ROADMAP §2 step 2: house-specific sleeping rules (KB B3; LK1952 p119), p48 blind chart, F5 node cells
FULL = dict(Su=1, Mo=2, Ma=3, Me=4, Ju=5, Ve=6, Sa=7, Ra=8, Ke=2)          # H9–H12 empty unless moved


@pytest.mark.parametrize("houses,planet,want,absent", [
    # H2: sleeps if 10 is empty (B3 H2; LK1952 p119) or 6 is empty (B3 H6, p67); 8 empty is good, not sleep
    (dict(FULL, Ve=10, Sa=6, Ra=11, Ke=5), "Moon", "SLEEPING? H2 rule: H8… ", None),
    (dict(FULL, Ve=6), "Moon", "SLEEPING? H10 empty (H2 rule: B3 H2; LK1952 p119)", None),
    (dict(FULL, Ve=10, Ju=8, Sa=9), "Moon", "SLEEPING? H6 empty (H2 rule: B3 H6, p67)", None),
    # H10 sleeps if 2 is empty (B3 H10), whatever is in 4
    (dict(FULL, Mo=9, Ke=9, Sa=10, Me=11), "Saturn", "SLEEPING? H2 empty (H10 rule: B3 H10)", None),
    # H1: Shrimali's generic test (7 empty) and LK1952's (2 empty) are both shown
    (dict(FULL, Mo=9, Ke=9), "Sun", "SLEEPING? H2 empty (H1 rule: LK1952 p119)", "7th from it"),
    # a house with no specific rule keeps the generic test
    (dict(FULL), "Jupiter", "SLEEPING? 7th from it (H11) empty (B7 p44, R14)", None),
])
def test_sleeping_house_rules(houses, planet, want, absent):
    line = _line(_chart_facts(), houses, planet)
    if want.endswith("H8… "):        # the two rules disagree: house rule says awake, generic says asleep
        assert "SLEEPING" not in line and "awake by the H2 rule (the generic 7th-house test, p44, says asleep)" in line
    else:
        assert want in line, line
    if absent:
        assert absent not in line, line


def test_blind_chart_enemies_together_in_10():
    """LKS p48: enemy planets in the 10th fight and turn blind; effect depends on the Moon."""
    cf = _chart_facts()
    ch = lambda h: {"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[x - 1]} for p, x in h.items()}, "lk_houses": h}
    out = "\n".join(_lk_block(cf, ch(dict(BASE, Su=10, Sa=10))))
    assert "Blind chart (B7 p48): enemy planets together in 10: Su+Sa — results uncertain, depend on the Moon" in out
    assert "Blind chart (B7 p48)" not in "\n".join(_lk_block(cf, ch(dict(BASE, Su=10, Mo=10))))   # friends


@pytest.mark.parametrize("h,label", [(7, "book tables: exalted (p34, p60, p67; not in LK1952 p72)"),
                                     (12, "book tables: debilitated (p34, p71; LK1952 p72)"),
                                     (6, "book tables: exalted (p34 list; LK1952 p72)")])
def test_f5_rahu_cells_from_the_book_tables(h, label):
    """F5: cells the printed tables carry but X3 version A leaves out, each with its pages."""
    line = _line(_chart_facts(), dict(BASE, Ra=h, Ke=(h + 5) % 12 + 1), "Rahu")
    assert label in line, line


def test_timing_tables_match_timing_md_and_sum():
    """LAL-KITAB-ROADMAP §4: maturity ages, fortune-rise ages and the 35-year cycle as one tested table (sources in
    lal_kitab.LK_TIMING_SOURCES); timing.md §8 must say the same."""
    import re
    lk = _chart_facts()._lal_kitab()
    names = dict(Ju="Jupiter", Su="Sun", Mo="Moon", Ve="Venus", Ma="Mars", Me="Mercury", Sa="Saturn", Ra="Rahu", Ke="Ketu")
    md = open(os.path.join(config.load().skill_dir, "references", "timing.md"), encoding="utf-8").read()
    ages = md[md.index("**Planet ages (maturity years)**"):md.index("3. **Sleeping planets wake**")]
    cycle = md[md.index("**35-year cycle**"):md.index("5. **Conjunction durations**")]
    for p, n in names.items():
        assert re.search(rf"{n} {lk.LK_MATURITY[p]}\b", ages), p
        assert re.search(rf"{n} {lk.LK_CYCLE35[p]} years?\b|{n} {lk.LK_CYCLE35[p]},", cycle), p
    assert sum(lk.LK_CYCLE35.values()) == 35 and list(lk.LK_CYCLE35) == list(names)
    assert lk.LK_FORTUNE_RISE == dict(Me=23, Ma=34)
    assert set(lk.LK_TIMING_SOURCES) == {"LK_MATURITY", "LK_FORTUNE_RISE", "LK_CYCLE35"}


@pytest.mark.parametrize("text,cat", [("Float coconuts in a running river for 43 days.", "unsafe-remedy"),
                                      ("Bury honey under the tree.", "unsafe-remedy"),
                                      ("Collect money from your sisters for the ritual.", "unsafe-remedy"),
                                      ("Donate milk and silver on Mondays.", "donation-check")])
def test_audit_remedy_wording_private(text, cat):
    """LAL-KITAB-ROADMAP §4: remedy wording is flagged for a remedy-safety.md check (paraphrased examples)."""
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import life_lint
    assert cat in {c for c, _, _ in life_lint.audit(text)}


def test_public_life_lint_keeps_the_remedy_probes():
    src = open(os.path.join(config.load().skill_dir, "scripts", "life_lint.py"), encoding="utf-8").read()
    assert "unsafe-remedy" in src and "<private-edition>" not in src


@needs_table
def test_varshaphal_year_17_shows_the_books_only_reading(capsys):
    """LAL-KITAB-ROADMAP §4 (council 6): every recommended row traces to a book page except year 17, whose cells 3–4
    were chosen by a majority that counted an untraced web chart. The 1952 edition's row is a valid permutation, so
    both readings are shown, as for 67/99/104 — the data file is unchanged."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("vp", os.path.join(config.load().skill_dir, "scripts", "varshaphal.py"))
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)
    rows = vp.load()
    assert rows[17]["alt"] and rows[17]["alt"] != rows[17]["rec"] and sorted(rows[17]["alt"]) == list(range(1, 13))
    vp.show({"Su": 3, "Mo": 4, "Ma": 1}, 17, rows)
    out = capsys.readouterr().out
    assert "1952 reading" in out and "untraced web chart" in out and "present both readings" in out


# Council 7 (2026-10-19): LK1952 page images checked (PDF p72 table, p73 text, p123 aspect page) — see the KB v2.3 notes
def test_jupiter_pakka_ghar_dispute_is_shown():
    """Shrimali p40: Jupiter pakka 2, 5, 9, 12; LK1952 p72 table: 2, 5, 9, 11 and house 12 to Rahu only."""
    cf = _chart_facts()
    assert "in PAKKA GHAR (B7 p40; disputed: LK1952 p72 gives 12 to Rahu only)" in _line(cf, dict(BASE, Ju=12), "Jupiter")
    assert "pakka ghar in LK1952 only (p72; B7 p40 lists 2, 5, 9, 12)" in _line(cf, dict(BASE, Ju=11), "Jupiter")
    assert "in PAKKA GHAR (B7 p40)" in _line(cf, dict(BASE, Ju=9), "Jupiter")


def test_aspect_rows_follow_both_books():
    """LK1952 p123: arrows 1→7, 3→9,11, 4→10, 5→9, 6→12, 8→2; verse: 1→7 and 4→10 full, 5→9 and 3→11 half, 8→2 and
    6→12 quarter. Row 5 is 9 in LK1952 (Shrimali p38 prints 9,11), so it is no longer doubtful."""
    cf = _chart_facts()
    h = dict(Su=1, Mo=2, Ma=3, Me=4, Ju=5, Ve=6, Sa=8, Ra=11, Ke=5)
    assert "LK aspect → H7 (full, LK1952 p123)" in _line(cf, h, "Sun")
    assert "LK aspect → H9 (half, LK1952 p123; B5 printed 9,11)" in _line(cf, h, "Jupiter")
    assert "LK aspect → H9,11 (11 half, LK1952 p123)" in _line(cf, h, "Mars")
    assert "LK aspect → H12 (quarter, LK1952 p123)" in _line(cf, h, "Venus")
    assert "LK aspect → H6 ❓" in _line(cf, h, "Moon")                        # 2→6: Shrimali only
    out = "\n".join(_lk_block(cf, {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Aries"}}}))
    assert "9, 11, 12 cast no aspect in either book's table (B5/p38 rows 1–7; LK1952 p123)" in out


def test_exaltation_cells_cite_lk1952():
    cf = _chart_facts()
    assert "LK1952 p72: none exalted in 8" in _line(cf, dict(BASE, Ma=8), "Mars")
    assert "book tables: exalted (p34, p60, p67; not in LK1952 p72)" in _line(cf, dict(BASE, Ra=7, Ke=1), "Rahu")
    assert "book tables: debilitated (p34, p71; LK1952 p72)" in _line(cf, dict(BASE, Ra=12, Ke=6), "Rahu")


# Council 7: LK1952 Farman 14 (PDF p248, image-checked) chart types — not in Shrimali; shown as LK1952 rules
@pytest.mark.parametrize("houses,want", [
    (dict(BASE, Sa=7, Su=4), "half-blind (Saturn 7 + Sun 4)"),
    (dict(BASE, Me=6, Su=5, Ve=3), "baalig (Mercury 6 + Sun in 1, 5 or 11)"),
    (dict(Su=2, Mo=3, Ma=5, Me=6, Ju=9, Ve=11, Sa=12, Ra=8, Ke=2), "nabalig (houses 1, 4, 7, 10 all empty)"),
    (dict(BASE, Me=9, Sa=9), "nabalig (Mercury with a papi: Sa)"),
    (dict(BASE, Me=10, Ju=10), "blind (enemies together in 10 per Farman 14: Me+Ju)"),
])
def test_farman14_chart_types(houses, want):
    cf = _chart_facts()
    ch = {"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[h - 1]} for p, h in houses.items()}, "lk_houses": houses}
    out = "\n".join(_lk_block(cf, ch))
    assert "Chart type (LK1952 p248, Farman 14; not in Shrimali): " in out and want in out, out


def test_no_chart_type_line_when_none_applies():
    out = "\n".join(_lk_block(_chart_facts(), {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Aries"},
                                               "Mo": {"sign": "Cancer"}, "Ju": {"sign": "Capricorn"}}}))
    assert "Chart type (LK1952 p248" not in out


@pytest.mark.parametrize("houses,planet,want", [
    (dict(BASE, Ra=1, Ke=7), "Sun", "maturity age with Ra: 0 (zero) (LK1952 p56, default 22)"),
    (dict(BASE, Ju=2), "Moon", "maturity age with Ju: 12 (LK1952 p56, default 24)"),
    (dict(BASE, Sa=5), "Saturn", "maturity age with Ju: 18 father's age, 27 wealth (LK1952 p56, default 36)"),
    (dict(BASE, Me=1), "Mercury", "maturity age with Su: 17 (LK1952 p56, default 34)"),
])
def test_conjunction_maturity_ages(houses, planet, want):
    assert want in _line(_chart_facts(), houses, planet)


def test_cycle35_sub_periods_fill_each_period():
    lk = _chart_facts()._lal_kitab()
    for p, years in lk.LK_CYCLE35.items():
        parts = lk.LK_CYCLE35_SUB[p]
        assert len(parts) == 3 and sum(m for _, m in parts) == years * 12, p
    assert lk.LK_CYCLE35_SUB["Ju"] == [("Ke", 24), ("Ju", 24), ("Su", 24)]
    assert lk.LK_CYCLE35_SUB["Mo"] == [("Ju", 4), ("Su", 4), ("Mo", 4)]


# P4-1 artificial planets (KB B7 p41, 52; ⚠️X9 chapter headers differ; CR-L14 LK1952 adds Venus+Mars for the Moon)
@pytest.mark.parametrize("houses,want", [
    (dict(BASE, Me=3, Ve=3), "H3 Me+Ve = artificial Sun"),
    (dict(BASE, Su=5), "H5 Su+Ju = artificial Moon (X9: chapter header p80 gives Su+Me; CR-L14: LK1952 also Ve+Ma)"),
    (dict(BASE, Su=9), "H9 Su+Sa = artificial debilitated Mars"),
    (dict(BASE, Su=9), "H9 Su+Sa = artificial debilitated Rahu"),
    (dict(BASE, Ve=5), "H5 Ju+Ve = artificial Saturn (Ketu-like; X9: chapter header p122 gives Ve+Me)"),
    (dict(BASE, Ve=9), "H9 Ve+Sa = artificial exalted Ketu (chapter-header table)"),
])
def test_artificial_planets(houses, want):
    out = "\n".join(_lk_block(_chart_facts(), {"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[h - 1]}
                                               for p, h in houses.items()}, "lk_houses": houses}))
    assert "Artificial planets (KB B7 p41, 52): " in out and want in out, out


def test_no_artificial_line_without_pairs():
    out = "\n".join(_lk_block(_chart_facts(), {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Aries"},
                                               "Mo": {"sign": "Leo"}}}))
    assert "Artificial planets" not in out


# R2 (research/LK/R2-lal-kitab-open-items.md) §1 35-year cycle [LK1952 p60-61, p235-236] and §2 rin signatures; synthetic
# lk_houses charts only. The cycle anchor is a made-up test input, never a real event.
def _text(cf, houses, **extra):
    ch = {"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[h - 1]} for p, h in houses.items()}, "lk_houses": houses, **extra}
    return "\n".join(_lk_block(cf, ch))


def _one(text, start):
    return next(x for x in text.splitlines() if x.startswith(start))


P236 = ("Ra 1–4 (partial), Ke 5–7, Ju 8–13, Su 14–15, Mo 16, Ve 17–19, Ma 20–25, Me 26–27, Sa 28–33, Ra 34–39, Ke 40–42, "
        "Ju 43–48")


@pytest.mark.parametrize("anchor", [dict(planet="Ve", year=17, edge="start"), dict(planet="Ve", year=19, edge="end")])
def test_c1_c2_cycle_p236_venus_example(anchor):
    line = _one(_text(_chart_facts(), BASE, lk_cycle_anchor=anchor), "  35-year cycle from")
    assert P236 in line and "Ju 113–118, Su 119–120; year-1 test (p236): FAIL (Rahu in H11, no EQ partner, weekday not supplied)" in line
    assert "'of that planet' not tested; the book says use another event" in line


def test_c3_c4_cycle_saturn_table_and_equivalence():
    cf = _chart_facts()
    line = _one(_text(cf, BASE, lk_cycle_anchor=dict(planet="Sa", year=1, edge="start")), "  35-year cycle from")
    assert "Sa 1–6, Ra 7–12, Ke 13–15, Ju 16–21, Su 22–23, Mo 24, Ve 25–27, Ma 28–33, Me 34–35, Sa 36–41" in line
    assert "PASS (Sa in H9)" in line and "(partial)" not in line
    assert "PASS (Ma≈Sa: Sa in H9)" in _text(cf, BASE, lk_cycle_anchor=dict(planet="Ma", year=1, edge="start"))


def test_c5_cycle_birth_weekday():
    cf, h = _chart_facts(), dict(BASE, Su=3)
    anchor = dict(planet="Su", year=1, edge="start")
    assert "PASS (birth-weekday planet Su)" in _text(cf, h, lk_cycle_anchor=anchor, lk_birth_weekday="Su")
    no = _text(cf, h, lk_cycle_anchor=anchor)
    assert "FAIL" in no and "weekday not supplied" in no


def test_c6_cycle_without_anchor_prints_candidates_only():
    import re
    line = _one(_text(_chart_facts(), BASE), "  35-year cycle")
    assert "in H1 Su; in H9 Sa; by equivalence (Ma≈Sa, Su≈Me, Su≈Mo) Mo, Ma, Me; birth-weekday planet not supplied" in line
    assert not re.search(r"\b[A-Z][a-z] \d+–\d+", line) and "from the supplied anchor" not in line


@pytest.mark.parametrize("extra", [
    dict(lk_cycle_anchor=dict(planet="Xx", year=5, edge="start")), dict(lk_cycle_anchor=dict(planet="Ve", year=0, edge="start")),
    dict(lk_cycle_anchor=dict(planet="Ve", year=121, edge="start")), dict(lk_cycle_anchor=dict(planet="Ve", year=5, edge="middle")),
    dict(lk_cycle_anchor=dict(planet="Ve", year=True, edge="start")), dict(lk_cycle_anchor=["Ve", 5]),
    dict(lk_cycle_anchor=dict(planet="Ve", year=5)), dict(lk_birth_weekday="Ra")])
def test_c7_cycle_inputs_validated(extra):
    cf = _chart_facts()
    out = cf.facts({"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Leo"}}, **extra})
    assert "Lal Kitab block failed (ValueError: lk_" in out and "H5 Leo: occ Su" in out


def _rin(houses):
    return _one(_text(_chart_facts(), houses), "  Rin (debt)")


def test_r1_rin_base_editions_disagree():
    line = _rin(BASE)
    assert ("LK1952 p146–150: zaati, table p146 (Sun: Ke in 5), zaati, list p150 (Sun: Ke in 5), "
            "matri (Moon: Me in 4; p150 list, table cell blank), stri (Venus: Mo in 2,7)") in line
    kb = line.split("KB B12 (Shrimali p164–174): ")[1].split(" | ")[0]
    assert kb == "stree, table p173–174 (Venus: Mo in 2,7)"
    assert "Gate facts (LK1952 p150; Shrimali verse p165 '5, 12, 2, 9 koi mand'): H2 Mo, H5 Ju+Ke, H9 Sa, H12 —." in line


def test_m4_rin_zaati_shows_both_page_readings_and_why_the_gate_is_open():
    """M4 (owner page check 2026-10-24, LK-F36): the Sun-in-5 enemy is 'Venus or paapi Ketu' on LK1952 p146 but 'Venus or
    a paapi grah' on p150; both are shown. The p150 gate names houses 2-5-9-12 without saying all or any."""
    line = _rin(dict(BASE, Ke=3, Sa=5))
    assert "zaati, list p150 (Sun: Sa in 5)" in line and "zaati, table p146" not in line
    assert "gate not evaluated: LK1952 p150 names houses 2-5-9-12 as a group but not whether all or any" in line
    assert "'planet itself malefic' is judged across the family's charts (p144)" in line


def _takraav(houses):
    return [x for x in _text(_chart_facts(), houses).splitlines() if x.startswith("  LK clash (takraav")]


def test_m4_takraav_line_and_house_9_exception():
    """D-4 (owner 2026-10-24): N clashes with N+7 (LK1952 p132-133 = KB B6); the clash on house 9 is helpful (p132)."""
    line = _takraav(BASE)
    assert line == ["  LK clash (takraav, 8th-house relation; LK1952 p132–133 and KB B6 p45–47 agree; not Parashari graha"
                    " yuddha): H2 Mo → H9 Sa (LK1952 p132 exception: clash on H9 helpful); H4 Me → H11 Ra; H6 Ve → H1 Su;"
                    " H9 Sa → H4 Me; H11 Ra → H6 Ve."]
    assert "sudden" not in line[0].lower() and "friends or foes" not in line[0]


def test_m4_takraav_absent_without_a_pair():
    assert _takraav(dict(Su=1, Mo=2, Ma=3, Me=1, Ju=2, Ve=3, Sa=1, Ra=2, Ke=3)) == []


def test_r2_rin_matri_ketu_in_4():
    line = _rin(dict(BASE, Ke=4, Ra=10, Me=7))
    lk, kb = line.split(" | ")[0], line.split(" | ")[1]
    assert "matri (Moon: Ke in 4)" in kb and "matri" not in lk


def test_r3_r4_r5_rin_mercury_rows_differ():
    r3 = _rin(dict(BASE, Ra=9, Ke=3, Me=12, Sa=10))
    assert r3.count("pitri (Jupiter: Me+Ra in 2,5,9,12)") == 2 and "LK1952 p149: Ra 9 + Me 12; KB B12: none" in r3
    assert "LK1952 p149: none; KB B12: Me 3 + Ra 9" in _rin(dict(BASE, Ra=9, Ke=3, Me=3, Sa=10))
    r5 = _rin(dict(BASE, Ma=9, Me=8, Sa=10))
    assert "LK1952 p149: Ma 9 + Me 8; KB B12: none" in r5
    assert "rishtedari (Mars: Me in 1,8)" in r5 and "bandhu (Mars: Me in 1,8)" in r5


def test_r6_r7_rin_saturn_text_needs_sun_and_moon():
    r6 = _rin(dict(BASE, Su=10))
    assert "zalimana (Saturn: Su in 10,11)" in r6 and "nirdayi, table p173–174 (Saturn: Su in 10,11)" in r6
    assert "nirdayi, text p171" not in r6
    r7 = _rin(dict(BASE, Su=10, Mo=11))
    for s in ("zalimana (Saturn: Su+Mo in 10,11)", "nirdayi, text p171 (Saturn: Su+Mo in 10,11)",
              "nirdayi, table p173–174 (Saturn: Su in 10,11)"):
        assert s in r7


def test_r8_r9_rin_line_prints_no_remedy():
    line = _rin(BASE).lower()
    assert not any(w in line.replace("remedies are not printed", "") for w in ("float", "feed", "donate", "river")) and "remed" in line


# P4-7 (a)/(c): LK1952 aspect-target sleep test beside Shrimali's 7th-house test, sleeping houses, remedy pre-check
def test_p47_h5_h9_empty_h11_occupied_editions_split():
    """Acceptance: planet in H5, H9 empty, H11 occupied -> LK1952 asleep, Shrimali awake (CR-L27)."""
    line = _line(_chart_facts(), dict(Su=1, Mo=2, Ma=3, Me=4, Ju=5, Ve=6, Sa=7, Ra=11, Ke=2), "Jupiter")
    assert ("editions' sleep tests: LK1952 aspect target H9 empty → asleep (p117–119), Shrimali 7th-house H11 occupied → awake"
            " (B7 p44), CR-L27 (verdicts differ, neither chosen)") in line and "SLEEPING?" not in line, line


def test_p47_h11_needs_h1_and_h3():
    cf = _chart_facts()
    line = _line(cf, dict(Su=1, Mo=2, Ma=5, Me=4, Ju=11, Ve=6, Sa=7, Ra=8, Ke=2), "Jupiter")
    assert "LK1952 H3 empty → not fully awake (H11 rule, p101), Shrimali 7th-house H5 occupied → awake" in line, line
    line = _line(cf, dict(Su=1, Mo=2, Ma=3, Me=4, Ju=11, Ve=6, Sa=7, Ra=8, Ke=2), "Jupiter")
    assert "LK1952 H1 and H3 both occupied → fully awake (H11 rule, p101), Shrimali 7th-house H5 empty → asleep" in line, line


def test_p47_sleeping_houses_and_no_aspect_houses():
    out = "\n".join(_lk_block(_chart_facts(), {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Aries"}}}))
    assert "empty and so asleep, with awakener: H2 Moon, H3 Mercury" in out and "H1 Mars" not in out.split("awakener:")[1].split(".")[0]
    assert "No LK1952 aspect-target test exists for planets in H7, H9, H10, H11, H12" in out and "borrowed from Parashari" in out


def test_p47_remedy_precheck_x17_and_no_verdict():
    cf = _chart_facts()
    out = "\n".join(_lk_block(cf, {"asc": {"sign": "Aries"}, "planets": {p: {"sign": SIGNS[h - 1]} for p, h in
                                    dict(BASE, Ju=4, Ve=12, Mo=6, Sa=1).items()}, "lk_houses": dict(BASE, Ju=4, Ve=12, Mo=6, Sa=1)}))
    line = next(x for x in out.splitlines() if x.startswith("  Remedy pre-check"))
    assert "do not donate the objects of exalted Jupiter H4" in line and "do not donate the objects of exalted Venus H12" in line
    assert "do not accept the objects of debilitated Saturn H1" in line
    assert "Moon 6: don't donate milk" in line                                  # B13 p208-209
    assert "43 days unbroken" in line and "any blood relative may perform" in line     # per-source process rules
    assert "no verdict" in line and "no remedy" not in line.lower().replace("no remedy-", "")
    assert "Shrimali" in line and "LK1952" in line and "fasting 40–43 is ❓" in line
    none = "\n".join(_lk_block(cf, {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Taurus"}}, "lk_houses": {"Su": 2}}))
    assert "no exalted planet Su–Sa" in none


def _rr():
    sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
    import render_report as rr
    return rr


CARD = {"planet": "Jupiter", "house": 2, "remedy": "Serve elders and teachers", "safety": "low-risk", "source": "KB p107"}


def _report(**kw):
    import copy
    import json
    rr = _rr()
    r = copy.deepcopy(json.load(open(os.path.join(rr.ASSETS, "example-synthetic.json"), encoding="utf-8")))
    r.update(kw)
    return r


def test_remedy_cards_render_only_when_requested_with_sources_in_the_appendix():
    pytest.importorskip("jinja2")
    rr = _rr()
    asked = rr.html_of(_report(remedies_requested=True, remedies=[CARD]))
    assert "Remedies you asked about" in asked and "No efficacy established." in asked
    assert asked.index("KB p107") > asked.index('id="appendix"')                   # locator in the appendix only
    assert "Remedies you asked about" not in rr.html_of(_report())
    assert "Remedies you asked about" not in rr.html_of(_report(remedies=[CARD]))   # cards without the request
    assert any("remedies_requested" in e for e in rr.checks(_report(remedies=[CARD]))[0])


@pytest.mark.parametrize("card,why", [
    (dict(CARD, safety=None), "safety class"),
    (dict(CARD, remedy="Keep a piece of ivory at home"), "never-recommend"),
    (dict(CARD, remedy="Offer milk to snakes"), "never-recommend"),
    (dict(CARD, remedy="Float coins in a river"), "marked low-risk"),
    (dict(CARD, remedy="Float coins in a river", safety="caution"), "safe form")])
def test_unsafe_or_unclassified_cards_fail_the_report(card, why):
    assert any(why in e for e in _rr().checks(_report(remedies_requested=True, remedies=[card]))[0])


def test_remedy_cards_are_wired_into_the_report_renderer():
    src = open(os.path.join(config.load().skill_dir, "scripts", "render_report.py"), encoding="utf-8").read()
    assert "import lk_remedies" in src and "lk_remedies.card_checks(r)" in src and "<private-edition>" not in src


# M3 / D-5 (owner page check 2026-10-24, LK-F35): month of effect, LK1952 p239/p241 and Shrimali p209-210/p219
def _varshaphal():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vp", os.path.join(config.load().skill_dir, "scripts", "varshaphal.py"))
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)
    return vp


def test_lk1952_month_occupied_house_uses_the_fixed_month():
    """p239 example: Mercury arrives in a natally occupied H2 -> its effect falls in Jeth (p241 table, H2)."""
    vp = _varshaphal()
    natal, annual = {"Su": 1, "Me": 5, "Ju": 2}, {"Su": 8, "Me": 2, "Ju": 9}
    assert vp.lk1952_month(natal, annual, "Me") == "Jeth (fixed month of H2: natally occupied) [LK1952 p239, p241]"


def test_lk1952_month_empty_house_counts_the_annual_sun_from_the_birthday():
    """p239 example: natal H4 empty, annual Mars in H4 with the annual Sun in H8 -> the 8th month from the birthday."""
    vp = _varshaphal()
    natal, annual = {"Su": 1, "Ma": 3}, {"Su": 8, "Ma": 4}
    assert vp.lk1952_month(natal, annual, "Ma") == \
        "month 8 counted from the birthday (annual Sun in H8; H4 natally empty) [LK1952 p239]"
    assert "annual Sun not given" in vp.lk1952_month({"Ma": 3}, {"Ma": 4}, "Ma")   # no Sun, no guess


def test_lk1952_month_table_is_the_p241_list():
    vp = _varshaphal()
    assert len(vp.LK1952_MONTHS) == 12 and vp.LK1952_MONTHS[0] == "Vaisakh" and vp.LK1952_MONTHS[1] == "Jeth"
    assert vp.LK1952_MONTHS[11] == "Chaitra"


def test_shrimali_month_counts_the_planets_own_house_from_the_birth_month():
    """Shrimali p209-210 example: a planet in H12 of the varshaphal, native born in February -> January."""
    vp = _varshaphal()
    assert vp.shrimali_month(12, birth_month=2) == "month 12 from the birth month = January [Shrimali p209-210]"
    assert vp.shrimali_month(1, birth_month=7) == "month 1 from the birth month = July [Shrimali p209-210]"
    assert vp.shrimali_month(5) == "month 5 from the birth month (birth month = 1) [Shrimali p209-210]"


@needs_table
def test_varshaphal_show_prints_both_editions_separately(capsys):
    vp = _varshaphal()
    vp.show({"Su": 1, "Me": 5, "Ju": 2}, 34, vp.load(), birth_month=2)
    out = capsys.readouterr().out
    assert "[LK1952 p239" in out and "[Shrimali p209-210]" in out
    assert "year's main effect: month" in out and "[LK1952 p241; Shrimali p219]" in out


# R44 (owner page check 2026-10-24, LK-F37): LK1952 p243 counts the running year ("16th year of age")
@needs_table
def test_varshaphal_dob_defaults_to_running_year_with_a_completed_note(capsys):
    import datetime
    vp = _varshaphal()
    vp.show_dob({"Su": 1, "Me": 5, "Ju": 2}, vp.load(), datetime.date(2000, 2, 10), datetime.date(2026, 9, 23))
    out = capsys.readouterr().out
    assert "Age-year 27 (running year, LK1952 p243)" in out and "completed-year" not in out.split("Note:")[0]
    assert out.count("Age-year") == 1
    assert "Note: the completed-years convention would give age-year 26" in out and "Shrimali states no convention" in out


@needs_table
def test_varshaphal_dob_completed_only_when_asked(capsys):
    import datetime
    vp = _varshaphal()
    vp.show_dob({"Su": 1}, vp.load(), datetime.date(2000, 2, 10), datetime.date(2026, 9, 23), convention="completed")
    out = capsys.readouterr().out
    assert "Age-year 26 (completed-year convention, not LK1952's)" in out and out.count("Age-year") == 1
