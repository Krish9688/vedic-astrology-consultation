#!/usr/bin/env python3
"""Lal Kitab part of chart_facts.py (public and private editions since 3.7, owner decision 2026-10-25). The rule tables
below are the project's own restatement of rules in the Lal Kitab books (Shrimali 2013, the 1952 re-typeset), with
book/page locators; the book text itself is not reproduced. The private knowledge base in data/lal-kitab/ is NOT read
here and is not distributed in the public edition: section codes such as "KB B7" are provenance notes only. The logic
moved here unchanged from chart_facts.py (output verified identical on 42 charts, council 5, TEST-EVIDENCE E-029)."""
# ---- Lal Kitab tables (the project's restatement; provenance in the private knowledge base v2.2) ----
LK_PAKKA = dict(Su=[1], Mo=[4], Ma=[3, 8], Me=[7], Ju=[2, 5, 9, 12], Ve=[7], Sa=[8, 10], Ra=[12], Ke=[6])  # B7/p40 (X8 default)
LK_EXALT = dict(Su=[1], Mo=[2], Ma=[10, 8], Me=[6], Ju=[4], Ve=[12], Sa=[7])                            # B4, X1 (Mars 8 and 10)
LK_DEBIL = dict(Su=[7], Mo=[8], Ma=[4], Me=[12], Ju=[10], Ve=[6], Sa=[1])
LK_NODE_TABLE = dict(Ra=([3], [9]), Ke=([9, 12], [3, 6]))            # p33-34/60 table set (X3/X4 version A)
LK_NODE_CHAPTER = dict(Ra=([3, 6], [8, 9, 11]), Ke=([5, 9, 12], [6, 8]))  # p130-138 chapter set (version B)
# Timing tables (LAL-KITAB-ROADMAP §4; prose in timing.md §8, kept equal by tests/test_lal_kitab.py)
LK_MATURITY = dict(Ju=16, Su=22, Mo=24, Ve=25, Ma=28, Me=34, Sa=36, Ra=42, Ke=48)
LK_FORTUNE_RISE = dict(Me=23, Ma=34)                                  # the others rise at their maturity age
LK_CYCLE35 = dict(Ju=6, Su=2, Mo=1, Ve=3, Ma=6, Me=2, Sa=6, Ra=6, Ke=3)   # in cycle order; start needs a dated event
# LK1952 p61 (PDF; printed p40), image-checked 2026-10-19: start / middle / end planet of each cycle period, in months
LK_CYCLE35_SUB = dict(Ju=[("Ke", 24), ("Ju", 24), ("Su", 24)], Su=[("Ma", 8), ("Su", 8), ("Mo", 8)],
                      Mo=[("Ju", 4), ("Su", 4), ("Mo", 4)], Ve=[("Ma", 12), ("Ve", 12), ("Me", 12)],
                      Ma=[("Ma", 24), ("Sa", 24), ("Ve", 24)], Me=[("Mo", 8), ("Ma", 8), ("Ju", 8)],
                      Sa=[("Ra", 24), ("Me", 24), ("Sa", 24)], Ra=[("Ma", 24), ("Ke", 24), ("Ra", 24)],
                      Ke=[("Sa", 12), ("Ra", 12), ("Ke", 12)])
# LK1952 p56 (PDF; printed p35), image-checked: maturity age when the planet sits with another (Mars "nek" cases need
# the reader to judge nek/bad Mars; the Moon row "Rahu but with Saturn" is printed ambiguously — shown as printed)
LK_MATURITY_WITH = dict(Su=[(("Ra",), "0 (zero)"), (("Ke",), "11")],
                        Mo=[(("Ju", "Ve", "Me"), "12"), (("Ra", "Sa"), "8 (printed 'Rahu but with Saturn': reading unclear)")],
                        Ve=[(("Ju",), "60 for wealth"), (("Su",), "34"), (("Ma",), "8 if Mars is nek")],
                        Me=[(("Su", "Ma"), "17")],
                        Sa=[(("Ju",), "18 father's age, 27 wealth"), (("Su",), "24"), (("Ma", "Ve"), "12"), (("Me",), "45")],
                        Ra=[(("Ma",), "0 (zero) if Mars is nek"), (("Ke",), "45")],
                        Ke=[(("Ju",), "40"), (("Su", "Sa"), "24"), (("Ma",), "24 if Mars is nek"), (("Ra",), "15")])
# LK1952 p248 Farman 14 (image-checked): chart types; enemy pairs from its footnote list (printed after note 3)
LK1952_FOES = dict(Me={"Ju", "Mo", "Ma"}, Ve={"Ju", "Su", "Mo", "Ra"}, Sa={"Su", "Mo", "Ma"}, Ra={"Su", "Mo", "Ma", "Ju"},
                   Ke={"Su", "Mo", "Ma"})
PAPI = {"Ra", "Ke", "Sa"}
# Artificial planets (KB B7 p41, 52; R17/X9 ⚠️ where the chapter headers differ; CR-L14): two planets in one house
LK_ARTIFICIAL = [
    (("Me", "Ve"), "Sun", ""), (("Su", "Ju"), "Moon", " (X9: chapter header p80 gives Su+Me; CR-L14: LK1952 also Ve+Ma)"),
    (("Su", "Me"), "exalted Mars", ""), (("Su", "Sa"), "debilitated Mars", ""), (("Ju", "Ra"), "Mercury", ""),
    (("Su", "Ve"), "Jupiter", " (X9: chapter header p105 gives Su+Me)"), (("Ra", "Ke"), "Venus", ""),
    (("Ju", "Ve"), "Saturn", " (Ketu-like; X9: chapter header p122 gives Ve+Me)"), (("Ma", "Me"), "Saturn", " (Mars/Rahu-like)"),
    (("Ma", "Sa"), "exalted Rahu", ""), (("Su", "Sa"), "debilitated Rahu", ""),
    (("Ve", "Sa"), "exalted Ketu", " (chapter-header table)"), (("Mo", "Sa"), "debilitated Ketu", " (chapter-header table)")]
LK_TIMING_SOURCES = {"LK_MATURITY": "KB B7 p51 (Shrimali); LK1952 p54 (image-checked) — both editions agree",
                     "LK_FORTUNE_RISE": "LK1952 p54-55 only", "LK_CYCLE35": "LK1952 p54, p60-61; anchoring p235-236"}
LK_NODE_PAGES = dict(Ra=({7: "p34, p60, p67; not in LK1952 p72", 6: "p34 list; LK1952 p72"},   # F5 + LK1952 p72 table
                         {12: "p34, p71; LK1952 p72"}), Ke=({}, {}))                                 # (council 7 image check)
# LK1952 p72 table (image-checked 2026-10-19): Jupiter pakka 2, 5, 9, 11; house 12 = Rahu only. Shrimali p40: 2, 5, 9, 12.
# Both shown; LK_PAKKA (Shrimali) stays the working default for rival/ally logic.
LK_PAKKA_LK1952_ONLY = {("Ju", 11)}
LK_PAKKA_DISPUTED = {("Ju", 12): "disputed: LK1952 p72 gives 12 to Rahu only"}
# LK1952 p123 (image-checked): arrows 1→7, 3→9,11, 4→10, 5→9, 6→12, 8→2 and the verse's strengths
LK_ASPECT_STRENGTH = {1: "full", 4: "full", 3: "11 half", 5: "half", 6: "quarter", 8: "quarter"}
# Sleeping (roadmap §2): house-specific conditions replace the generic "7th from it empty" test (B7 p44) where Shrimali
# gives one (H2, H10); where only LK1952 adds one (H1, H9), both are shown. Each: (houses that must all be empty, source)
LK_SLEEP = {2: [((10,), "B3 H2; LK1952 p119"), ((6,), "B3 H6, p67")], 10: [((2,), "B3 H10")],
            1: [((2,), "LK1952 p119")], 9: [((2,), "LK1952 p119")]}
LK_SLEEP_REPLACES_GENERIC = {2, 10}
# P4-7 (a): sleeping-house awakeners, identical in Shrimali B7 p45 and LK1952 p118-119 (no dispute). Definitions differ (CR-L27):
# Shrimali = nothing in the 7th from the planet (p44); LK1952 = the house the planet aspects is empty (p117-119); LK1952 p101
# adds that H11 is fully awake only when BOTH H1 and H3 hold planets. Source-map locators, not owner page-checked.
LK_AWAKENER = {1: "Mars", 2: "Moon", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Rahu", 7: "Venus", 8: "Moon", 9: "Jupiter",
               10: "Saturn", 11: "Jupiter", 12: "Ketu"}
# P4-7 (c): prohibited acts by placement, KB B13 p208-209 (consequence column deliberately not carried: it holds death
# claims, remedy-safety.md section 4). ((planet, house) pairs that must all hold, act). Venus 9: LK1952 p1158 words it as
# "no stipends to orphans/widows" (CR-L13). The row "H2 empty + malefics in 8" is not coded (the book does not define "malefics").
LK_DONT = [((("Mo", 6),), "donate milk; build a well, tap or pond (B13 p208-209)"),
           ((("Sa", 8),), "build a dharamshala (B13 p208-209)"),
           ((("Sa", 1), ("Ju", 5)), "give copper to beggars (B13 p208-209)"),
           ((("Ju", 10), ("Mo", 4)), "build a temple (B13 p208-209)"),
           ((("Ve", 9),), "adopt a child (B13 p208-209; LK1952 p1158 words it as no stipends to orphans or widows: CR-L13)"),
           ((("Mo", 12),), "feed sadhus; fund schools or free education (B13 p208-209)"),
           ((("Ju", 7),), "donate clothes (B13 p208-209)"),
           ((("Su", 7),), "donate in the morning or evening (B13 p208-209)"), ((("Su", 8),), "donate in the morning or evening (B13 p208-209)")]
LK_OWN = dict(Su=[5], Mo=[4], Ma=[1, 8], Me=[3, 6], Ju=[9, 12], Ve=[2, 7], Sa=[10, 11])   # Kalpurush sign lords (Aries chart); nodes own none
LK_FRIEND = dict(Su={"Mo", "Ju", "Ma"}, Mo={"Su", "Me"}, Ma={"Su", "Mo", "Ju"}, Me={"Su", "Ve", "Ra"}, Ju={"Su", "Ma", "Mo"},
                 Ve={"Sa", "Me", "Ke"}, Sa={"Me", "Ve", "Ra"}, Ra={"Sa", "Me", "Ke"}, Ke={"Ve", "Ra"})       # B4 (bracketed ones included)
LK_ENEMY = dict(Su={"Ra", "Ke", "Ve", "Sa"}, Mo={"Ra", "Ke"}, Ma={"Me", "Ke"}, Me={"Mo"}, Ju={"Ve", "Me"},
                Ve={"Su", "Mo", "Ra"}, Sa={"Su", "Mo", "Ma"}, Ra={"Su", "Ma", "Ve"}, Ke={"Mo", "Ma"})
LK_ASPECT = {1: [7], 2: [6], 3: [9, 11], 4: [10], 5: [9], 6: [12], 7: [2], 8: [2]}  # B5/R10 ❓ rows 9-12 missing; 5 printed "9,11"; 7->2 printed but p67 says 7 aspects nothing
LK_ASPECT_DISPUTED = {2}        # CR-L02: no 2->6 arrow in LK1952 p123 (row 5 settled: LK1952 prints 5->9)
LK_ASPECT_NONE = {7, 10}        # R11 ✅ (p67, p69): 7 and 10 aspect nothing; the p38 table still prints 7->2 (F8)
LK_SINFUL = dict(Ju=[3, 6, 8, 9, 11], Ve=[3, 6, 8, 9, 11], Me=[3, 6, 8, 9, 11], Mo=[3, 6, 8, 9, 11], Sa=[3, 11], Ma=[2, 3, 9])  # B7 p41

# ---- 35-year cycle anchoring (R2 §1; edition [LK1952]; LK1952 p60-61, p235-236 -- NOT page-checked by the owner) ----
# Symmetric, NOT transitive: Me and Mo are not equivalent (p236 year-1 test: Mars~Saturn, Sun~Mercury, Sun~Moon)
LK_EQ = dict(Ma={"Sa"}, Sa={"Ma"}, Su={"Me", "Mo"}, Me={"Su"}, Mo={"Su"})
WEEKDAY_PLANETS = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")   # Rahu and Ketu are not weekday planets (p62)

# ---- Rin (ancestral debt) signatures (R2 §2): hurt planet, its houses, enemy occupants, note. Editions kept apart;
# no table row is chosen over another (CR-L04, CR-L05). LK1952 p144-150 page-checked by the owner 2026-10-24 (LK-F36):
# the Sun-in-5 enemy is "paapi Ketu" on p146 but "paapi grah" on p150, so both readings are rows. "ALL" = every listed
# enemy must be present (Shrimali text p171 reading "Sun and Moon").
RIN_LK1952 = [("pitri", "Ju", (2, 5, 9, 12), {"Ve", "Me", "Ra"}, ""), ("zaati, table p146", "Su", (5,), {"Ve", "Ke"}, ""),
              ("zaati, list p150", "Su", (5,), {"Ve"} | PAPI, ""),
              ("matri", "Mo", (4,), {"Ve", "Me", "Sa"}, "; p150 list, table cell blank"),
              ("stri", "Ve", (2, 7), {"Su", "Ra", "Mo"}, ""), ("rishtedari", "Ma", (1, 8), {"Me", "Ke"}, ""),
              ("ladki-bahan", "Me", (3, 6), {"Mo"}, ""), ("zalimana", "Sa", (10, 11), {"Su", "Mo", "Ma"}, ""),
              ("anjanme", "Ra", (12,), {"Su", "Ve", "Ma"}, ""), ("dargahi", "Ke", (6,), {"Mo", "Ma"}, "")]
RIN_KB = [("pitri", "Ju", (2, 5, 9, 12), {"Ve", "Me", "Ra"}, ""), ("swa", "Su", (5,), {"Ve"}, ""),
          ("matri", "Mo", (4,), {"Ke"}, ""), ("stree, text p170", "Ve", (2,), {"Su", "Ra", "Ke"}, ""),
          ("stree, table p173\u2013174", "Ve", (2, 7), {"Su", "Mo", "Ra"}, ""), ("bandhu", "Ma", (1, 8), {"Me", "Ke"}, ""),
          ("sister", "Me", (3, 6), {"Mo"}, ""), ("nirdayi, text p171", "Sa", (10, 11), {"Su", "Mo"}, "ALL"),
          ("nirdayi, table p173\u2013174", "Sa", (10, 11), {"Su"}, ""),
          ("ajanma, text p172", "Ra", (12,), {"Su", "Mo", "Ma"}, ""),
          ("ajanma, table p173\u2013174", "Ra", (12,), {"Su", "Ve", "Ma"}, ""), ("kudrati", "Ke", (6,), {"Mo", "Ma"}, "")]
# Mercury in the root ("first condition"): planet in 9 -> Mercury's houses. LK1952 p149; Shrimali KB B12 differs in two rows
MERC_LK1952 = {"Ju": (12,), "Su": (5,), "Mo": (4,), "Ve": (2, 7), "Ma": (1, 8), "Sa": (10, 11), "Ra": (12,), "Ke": (6,)}
MERC_KB = [((1, 8), "Ju"), ((2, 7), "Ve"), ((3,), "Ra"), ((4,), "Mo"), ((5,), "Su"), ((6,), "Ke"), ((10, 11), "Sa"), ((12,), "Ju")]


def section(chart, house, out, W, ALL, NAME):
    """Append the Lal Kitab block to `out` (lines) for a chart whose whole-sign houses are `house`."""
    ov = chart.get("lk_houses", {})
    if not isinstance(ov, dict) or any(k not in ALL or type(v) is not int or not 1 <= v <= 12 for k, v in ov.items()):
        raise ValueError(f"lk_houses must map planet keys ({', '.join(ALL)}) to whole houses 1-12")   # F12
    lk = dict(house)
    lk.update(ov)
    anchor, wd = chart.get("lk_cycle_anchor"), chart.get("lk_birth_weekday")   # optional, user-supplied at run time (R2 §1)
    if anchor is not None and not (isinstance(anchor, dict) and set(anchor) == {"planet", "year", "edge"}
                                   and anchor["planet"] in LK_CYCLE35 and type(anchor["year"]) is int
                                   and 1 <= anchor["year"] <= 120 and anchor["edge"] in ("start", "end")):
        raise ValueError("lk_cycle_anchor must be {'planet': one of " + ", ".join(LK_CYCLE35) + ", 'year': whole year of life 1-120,"
                         " 'edge': 'start' or 'end'}")
    if wd is not None and wd not in WEEKDAY_PLANETS:
        raise ValueError(f"lk_birth_weekday must be one of {', '.join(WEEKDAY_PLANETS)}")
    lk_occ = {h: [p for p in lk if lk[p] == h] for h in range(1, 13)}
    src = "supplied lk_houses override" if chart.get("lk_houses") else "whole-sign houses from lagna (KB B2 note)"
    W(f"\n# Lal Kitab fixed-Aries chart ({src}); signs dropped, house N = Kalpurush sign N")
    W("  " + "  ".join(f"H{h}:{'+'.join(lk_occ[h]) or '—'}" for h in range(1, 13)))
    W(f"  Empty houses: {', '.join(str(h) for h in range(1, 13) if not lk_occ[h])}")
    for p in [q for q in ALL if q in lk]:
        h, fl = lk[p], []
        if h in LK_PAKKA[p]:
            fl.append(f"in PAKKA GHAR (B7 p40; {LK_PAKKA_DISPUTED[(p, h)]})" if (p, h) in LK_PAKKA_DISPUTED
                      else "in PAKKA GHAR (B7 p40)")
        elif (p, h) in LK_PAKKA_LK1952_ONLY:
            fl.append(f"pakka ghar in LK1952 only (p72; B7 p40 lists {', '.join(map(str, LK_PAKKA[p]))})")
        if p in LK_EXALT:
            if h in LK_EXALT[p]: fl.append("LK-exalted (disputed in 8: CR-L03; LK1952 p72: none exalted in 8)" if (p, h) == ("Ma", 8) else "LK-exalted (B4)")   # F9
            if h in LK_DEBIL[p]: fl.append("LK-debilitated (B4)")
        else:
            (te, td), (ce, cd) = LK_NODE_TABLE[p], LK_NODE_CHAPTER[p]
            be, bd = LK_NODE_PAGES[p]
            if h in te or h in ce or h in td or h in cd or h in be or h in bd:
                book = f", book tables: exalted ({be[h]})" if h in be else f", book tables: debilitated ({bd[h]})" if h in bd else ""
                fl.append(f"node dignity ⚠️X3/X4: table-set {'exalt' if h in te else 'debil' if h in td else 'none'}, chapter-set {'exalt' if h in ce else 'debil' if h in cd else 'none'}{book}")
        opp = (h + 5) % 12 + 1
        rules = [(e, src) for e, src in LK_SLEEP.get(h, []) if all(not lk_occ[x] for x in e)]
        fl += [f"SLEEPING? H{','.join(map(str, e))} empty (H{h} rule: {src})" for e, src in rules]
        if h not in LK_SLEEP_REPLACES_GENERIC:
            if not lk_occ[opp]: fl.append(f"SLEEPING? 7th from it (H{opp}) empty (B7 p44, R14)")
        elif not rules and not lk_occ[opp]:
            fl.append(f"awake by the H{h} rule (the generic 7th-house test, p44, says asleep)")
        fl += sleep_editions(h, opp, lk_occ)
        mates = [q for q in lk_occ[h] if q != p]
        en = [q for q in mates if q in LK_ENEMY[p]]
        fr = [q for q in mates if q in LK_FRIEND[p]]
        if en: fl.append(f"with LK-enemies {','.join(en)}")
        if fr: fl.append(f"with LK-friends {','.join(fr)}")
        sinful = p in LK_SINFUL and h in LK_SINFUL[p]
        dharmi = (p in ("Ra", "Ke") and (h == 4 or "Mo" in mates)) or (p == "Sa" and (h == 11 or "Ju" in mates))
        if sinful and not dharmi: fl.append("'sinful' placement (B7 p41)")
        if dharmi: fl.append("DHARMI (B7 p42; transforms the 'sinful' placement of p41)" if sinful else "DHARMI (B7 p42)")   # F10
        for q, label in (("Ra", "solar eclipse (Sun+Rahu: B7 p73; LK1952 p54)"),          # F11: each pairing, its source
                         ("Ke", "solar eclipse (Sun+Ketu: B7 p73; LK1952 p54 names Rahu only)")) if p == "Su" else (
                        ("Ra", "lunar eclipse (Moon+Rahu: KB p201; LK1952 p54 names Ketu)"),
                        ("Ke", "lunar eclipse (Moon+Ketu: LK1952 p54)")) if p == "Mo" else ():
            if q in mates: fl.append(label)
        for q in lk:
            # houses 7, 8, 12 are pakka ghar of two planets: sitting in one's OWN pakka ghar is not rivalry, and two
            # planets sharing a house are a conjunction, not an exchange (council 2026-10-11, R1/R3)
            if q != p and h in LK_PAKKA.get(q, []) and h not in LK_PAKKA[p] and lk[q] not in LK_PAKKA[p]:
                fl.append(f"rival? sits in {q}'s pakka ghar; {q} not in {p}'s (B7 p43)")
            if q != p and h in LK_PAKKA.get(q, []) and lk[q] in LK_PAKKA[p] and lk[q] != h and p < q:
                fl.append(f"ALLY with {q}: exchange of pakka houses (B7 p42)")
        for others, age in LK_MATURITY_WITH.get(p, []):
            hit = [q for q in others if q in mates]
            if hit:
                fl.append(f"maturity age with {'+'.join(hit)}: {age} (LK1952 p56, default {LK_MATURITY[p]})")
        tgt = LK_ASPECT.get(h)
        if h in LK_ASPECT_NONE:
            fl.append(f"LK aspect: none from H{h} (R11)" + (" — disputed: a table prints → H2 ❓ (p38)" if h == 7 else ""))
        elif tgt:
            st = LK_ASPECT_STRENGTH.get(h)
            note = " (half, LK1952 p123; B5 printed 9,11)" if h == 5 else f" ({st}, LK1952 p123)" if st else ""
            fl.append(f"LK aspect → H{','.join(map(str, tgt))}{note}{' ❓' if h in LK_ASPECT_DISPUTED else ''}")
        W(f"- {NAME[p]} H{h}: {'; '.join(fl) or '—'}")
    foes = sorted({"+".join(sorted((p, q), key=ALL.index)) for p in lk_occ[10] for q in lk_occ[10]
                   if p != q and (q in LK_ENEMY[p] or p in LK_ENEMY[q])}, key=lambda x: [ALL.index(y) for y in x.split("+")])
    if foes: W(f"  Blind chart (B7 p48): enemy planets together in 10: {', '.join(foes)} — results uncertain, depend on the Moon.")
    arts = [f"H{h} {a}+{b} = artificial {what}{note}" for h in range(1, 13) for (a, b), what, note in LK_ARTIFICIAL
            if a in lk_occ[h] and b in lk_occ[h]]
    if arts: W("  Artificial planets (KB B7 p41, 52): " + "; ".join(arts) + ".")
    types = []
    f14 = sorted({"+".join((p, q)) for p in lk_occ[10] for q in lk_occ[10] if q in LK1952_FOES.get(p, ())})
    if f14: types.append(f"blind (enemies together in 10 per Farman 14: {', '.join(f14)})")
    if lk.get("Sa") == 7 and lk.get("Su") == 4: types.append("half-blind (Saturn 7 + Sun 4)")
    if lk.get("Me") == 6 and lk.get("Su") in (1, 5, 11): types.append("baalig (Mercury 6 + Sun in 1, 5 or 11)")
    if all(not lk_occ[x] for x in (1, 4, 7, 10)): types.append("nabalig (houses 1, 4, 7, 10 all empty)")
    papi = sorted(q for q in PAPI if "Me" in lk and lk.get(q) == lk["Me"])
    if papi: types.append(f"nabalig (Mercury with a papi: {'+'.join(papi)})")
    if types: W("  Chart type (LK1952 p248, Farman 14; not in Shrimali): " + "; ".join(types) + ".")
    blind = [p for p in lk_occ[10] if p in LK_DEBIL and 10 in LK_DEBIL[p]]
    if blind: W(f"  Blind-chart check (B7 p41,48; H10 debilitated + mutual enemies): debilitated in 10: {blind} — verify enmity.")
    # P4-2: the Mangalik-by-house rule (Mars 1/4/7/8/12, KB B9) is a [VED] Parashari rule; it is printed once, by kuja(), not here
    W(rin_line(lk, lk_occ, ALL, NAME))
    if t := takraav_line(lk_occ): W(t)
    W(cycle_line(lk, lk_occ, ALL, NAME, anchor, wd))
    W(sleeping_houses_line(lk_occ))
    W(remedy_precheck_line(lk, ALL, NAME))
    W("  LK aspect table: 9, 11, 12 cast no aspect in either book's table (B5/p38 rows 1–7; LK1952 p123); 7 and 10 aspect"
      " nothing (R11). Never fill them from Parashari aspects.")


def sleep_editions(h, opp, lk_occ):
    """P4-7 (a): the two editions' sleep tests side by side (CR-L27). Printed only when LK1952 does not say awake, or
    Shrimali says asleep; never decides between them. H7, H9, H10, H12 have no LK1952 aspect target (see the houses line)."""
    shr = None if h in LK_SLEEP_REPLACES_GENERIC else f"7th-house H{opp} {'occupied → awake' if lk_occ[opp] else 'empty → asleep'} (B7 p44)"
    if h == 11:
        gone = [x for x in (1, 3) if not lk_occ[x]]
        lk = ("H1 and H3 both occupied → fully awake" if not gone else f"H{' and H'.join(map(str, gone))} empty → not fully awake") + " (H11 rule, p101)"
        bad = bool(gone)
    elif h in LK_ASPECT and h not in LK_ASPECT_NONE:
        tg = LK_ASPECT[h]
        occ = [x for x in tg if lk_occ[x]]
        bad = len(occ) < len(tg)
        lk = f"aspect target {', '.join(f'H{x} ' + ('occupied' if lk_occ[x] else 'empty') for x in tg)} → " + (
            "awake" if not bad else "asleep" if not occ else "split, the book gives no rule for two targets") + " (p117–119)"
    else:
        return []
    if not bad and not (shr and "asleep" in shr):
        return []
    return [f"editions' sleep tests: LK1952 {lk}, Shrimali {shr or 'house rule above'}, CR-L27"
            + (" (verdicts differ, neither chosen)" if shr and ("asleep" in shr) != bad else "")]


def sleeping_houses_line(lk_occ):
    """P4-7 (a): empty houses with their awakeners (Shrimali B7 p45 = LK1952 p118-119); occupied houses are always awake."""
    empty = [f"H{h} {LK_AWAKENER[h]}" for h in range(1, 13) if not lk_occ[h]]
    return ("  Sleeping houses (LK1952 p117–119; awakeners agree with Shrimali B7 p45; source-map locators, not owner-checked): "
            f"empty and so asleep, with awakener: {', '.join(empty) or 'none'}. Occupied houses are always awake (p118); the book's"
            " 'unaspected' half of the definition is not computed. No LK1952 aspect-target test exists for planets in H7, H9, H10,"
            " H11, H12 (no arrow, or they aspect nothing): H11 uses its own p101 rule, H9 and H10 their house rules, H7 and H12 only"
            " Shrimali's 7th-house test; nothing is borrowed from Parashari aspects (CR-L27).")


def remedy_precheck_line(lk, ALL, NAME):
    """P4-7 (c): mechanical pre-check for the remedy-safety gate. States facts per source; prescribes nothing, and never says
    that no remedy is possible (CR-L01: the sources disagree, remedy-safety.md section 1)."""
    ex = [f"{NAME[p]} H{lk[p]}" for p in LK_EXALT if lk.get(p) in LK_EXALT[p]]
    de = [f"{NAME[p]} H{lk[p]}" for p in LK_DEBIL if lk.get(p) == LK_DEBIL[p][0]]
    x17 = ("X17 donation check (KB B1 p208, LK1952 p1157; p210 and LK1952 p177 say to donate the planet's objects, so check before "
           "any donation): " + ("; ".join(f"do not donate the objects of exalted {x}" for x in ex) if ex else "no exalted planet Su–Sa")
           + "; " + ("; ".join(f"do not accept the objects of debilitated {x}" for x in de) if de else "no debilitated planet Su–Sa")
           + ("; Mars in 8 exalted only per Shrimali (CR-L03)" if lk.get("Ma") == 8 else "") + "; Rahu/Ketu dignity not tested (X3/X4)")
    donts = [f"{'+'.join(NAME[q] + ' ' + str(h) for q, h in need)}: don't {act}" for need, act in LK_DONT
             if all(lk.get(q) == h for q, h in need)]
    shr = [NAME[p] for p in ALL if p in lk and (lk[p] in LK_PAKKA[p] or (p in ("Su", "Mo", "Ju") and lk[p] == 6))]
    k52 = [NAME[p] for p in ALL if p in lk and ((lk[p] in LK_PAKKA[p] and (p, lk[p]) not in LK_PAKKA_DISPUTED)
           or (p, lk[p]) in LK_PAKKA_LK1952_ONLY or lk[p] in LK_OWN.get(p, ()) or lk[p] in LK_EXALT.get(p, ()) or lk[p] in LK_DEBIL.get(p, ()))
           and not (lk[p] == 6 and p not in ("Su", "Mo", "Ju"))]
    return ("  Remedy pre-check (not a prescription; remedies only when asked, remedy-safety.md): " + x17 + " | prohibited acts for "
            "the placement (book advice, never an obligation): " + ("; ".join(donts) or "none of the coded placements") + " | remediability, "
            f"both readings (CR-L01, no verdict): Shrimali B7 p42, p47, p67 'cannot be stopped' (pakka ghar, or Sun/Moon/Jupiter in 6): "
            f"{', '.join(shr) or 'none'}; LK1952 p59–60, p91 remediable class (pakka, own house, exalted or debilitated; in H6 only "
            f"Sun/Jupiter/Moon): {', '.join(k52) or 'none'}, the others fall outside the listed classes unless a 'sathi' applies (not tested)"
            " | process rules: Shrimali B1 p9, C2 — 43 days unbroken, restart if broken, daylight, performed by the person (touching the items"
            " for a proxy), one at a time with a gap (stated for the debt chapter, scope unclear); LK1952 p175, p177 — 40 to 43 days,"
            " break voids it, daylight, any blood relative may perform, lineage remedies weekly for 40–43 weeks (p145)."
            " Safety class: donations and prohibitions are ⚠️ caution; fasting 40–43 is ❓ ambiguous (remedy-safety.md section 2).")


def rin_line(lk, lk_occ, ALL, NAME):
    """R2 section 2: signature flags only, both editions shown separately; names no debt, prints no remedy."""
    def hits(table):
        out = []
        for debt, hurt, houses, foes, note in table:
            got = [q for q in ALL if q in foes and q != hurt and lk.get(q) in houses]
            if got and (note != "ALL" or len(got) == len(foes)):
                out.append(f"{debt} ({NAME[hurt]}: {'+'.join(got)} in {','.join(map(str, houses))}{'' if note == 'ALL' else note})")
        return ", ".join(out) or "none"
    ml = [f"{p} 9 + Me {lk['Me']}" for p, hs in MERC_LK1952.items() if lk.get(p) == 9 and lk.get("Me") in hs]
    mk = [f"Me {lk['Me']} + {p} 9" for hs, p in MERC_KB if lk.get("Me") in hs and lk.get(p) == 9]
    gate = ", ".join(f"H{h} {'+'.join(lk_occ[h]) or '—'}" for h in (2, 5, 9, 12))
    return ("  Rin (debt) signatures — natal chart only (LK1952 p150); editions shown separately; no debt is named (gate not"
            " evaluated: LK1952 p150 names houses 2-5-9-12 as a group but not whether all or any must be afflicted; 'planet"
            " itself malefic' is judged across the family's charts (p144)): "
            f"LK1952 p146–150: {hits(RIN_LK1952)} | KB B12 (Shrimali p164–174): {hits(RIN_KB)} | "
            f"Mercury in the root: LK1952 p149: {', '.join(ml) or 'none'}; KB B12: {', '.join(mk) or 'none'} | "
            f"Gate facts (LK1952 p150; Shrimali verse p165 '5, 12, 2, 9 koi mand'): {gate}. "
            "Remedies are not printed (remedy-safety.md).")


def takraav_line(lk_occ):
    """D-4 (owner 2026-10-24, LK-F36): planets of house N clash with those of N+7 (LK1952 p132-133 = KB B6 p45-47); the
    clash on house 9 is helpful (p132). Never the 'sudden blow' wording (p135-139). None when no pair exists."""
    pairs = []
    for n in range(1, 13):
        m = (n + 6) % 12 + 1
        if lk_occ[n] and lk_occ[m]:
            note = " (LK1952 p132 exception: clash on H9 helpful)" if m == 9 else ""
            pairs.append(f"H{n} {'+'.join(lk_occ[n])} → H{m} {'+'.join(lk_occ[m])}{note}")
    if pairs:
        return ("  LK clash (takraav, 8th-house relation; LK1952 p132–133 and KB B6 p45–47 agree; not Parashari graha"
                " yuddha): " + "; ".join(pairs) + ".")


def cycle_line(lk, lk_occ, ALL, NAME, anchor, wd):
    """R2 section 1 [LK1952]: schedule only from a user-supplied anchor; without one, year-1 candidates only."""
    if anchor is None:
        direct = {q for h in (1, 9) for q in lk_occ[h]}
        eq = [q for q in ALL if q in {e for d in direct for e in LK_EQ.get(d, ())} - direct]
        return ("  35-year cycle (LK1952 p60–61, p235–236; Shrimali gives only the shares): start not fixed by the chart."
                f" Year-1 candidates by the p236 test: in H1 {'+'.join(lk_occ[1]) or '—'}; in H9 {'+'.join(lk_occ[9]) or '—'};"
                f" by equivalence (Ma≈Sa, Su≈Me, Su≈Mo) {', '.join(eq) or '—'}; birth-weekday planet {wd or 'not supplied'}."
                " A schedule needs a dated event (lk_cycle_anchor).")
    order, P, Y = list(LK_CYCLE35), anchor["planet"], anchor["year"]
    j = order.index(P)
    s0 = Y if anchor["edge"] == "start" else Y - LK_CYCLE35[P] + 1
    seq = [(P, s0)]
    while s0 > 1:                                   # walk back until year 1 is covered; the first period may be partial
        j = (j - 1) % 9
        s0 -= LK_CYCLE35[order[j]]
        seq.insert(0, (order[j], s0))
    j, s = order.index(P), seq[-1][1]
    while True:                                     # walk forward to year 120 (last period truncated)
        s += LK_CYCLE35[order[j]]
        j = (j + 1) % 9
        if s > 120:
            break
        seq.append((order[j], s))
    txt = []
    for q, st in seq:
        lo, en = max(st, 1), min(st + LK_CYCLE35[q] - 1, 120)
        txt.append(f"{q} {lo if lo == en else f'{lo}–{en}'}{' (partial)' if st < 1 else ''}")
    y1 = seq[0][0]
    partners = sorted(LK_EQ.get(y1, ()), key=ALL.index)
    for q in [y1] + partners:
        if lk.get(q) in (1, 9):
            res = f"PASS ({'' if q == y1 else f'{y1}≈{q}: '}{q} in H{lk[q]})"
            break
    else:
        if wd and (wd == y1 or wd in partners):
            res = f"PASS (birth-weekday planet {wd if wd == y1 else f'{y1}≈{wd}'})"
        else:
            res = (f"FAIL ({NAME[y1]} in H{lk[y1]}, " if y1 in lk else f"FAIL ({NAME[y1]} not placed, ") + (
                "no EQ partner in H1 or H9, " if partners else "no EQ partner, ") + (
                f"birth-weekday planet {wd} does not match)" if wd else "weekday not supplied)")
    return ("  35-year cycle from the supplied anchor "
            f"({P} {'starts' if anchor['edge'] == 'start' else 'ends'} in year {Y}; LK1952 p235–236; years of life counted from 1): "
            f"{', '.join(txt)}; year-1 test (p236): {res}; 'of that planet' not tested"
            f"{'; the book says use another event' if res.startswith('FAIL') else ''}.")


def selftest(facts):
    """Checks of the Lal Kitab block, run by chart_facts.py --selftest."""
    # KB B2 p219 example: Cancer lagna; Sun 1; Me+Ve 2; Mars 3; Ketu 5; Sat 8; Jup+Rahu 11; Moon 12
    ch = {"asc": {"sign": "Cancer"}, "planets": {
        "Su": {"sign": "Cancer"}, "Me": {"sign": "Leo"}, "Ve": {"sign": "Leo"}, "Ma": {"sign": "Virgo"}, "Ke": {"sign": "Scorpio"},
        "Sa": {"sign": "Aquarius"}, "Ju": {"sign": "Taurus"}, "Ra": {"sign": "Taurus"}, "Mo": {"sign": "Gemini"}}}
    t = facts(ch)
    assert "H1:Su  H2:Me+Ve  H3:Ma  H4:—  H5:Ke" in t, t
    assert "Saturn H8: in PAKKA GHAR" in t and "Mars H3: in PAKKA GHAR" in t, t
