#!/usr/bin/env python3
"""Derive structural chart facts from SUPPLIED positions. No ephemeris: it never computes where a planet is.

It removes hand-arithmetic errors (house counting, lordship, aspects, D9/D10, dispositors, Lal Kitab states).
It does NOT interpret. Every Lal Kitab flag names the knowledge-base section/page to verify before use.

usage:  chart_facts.py chart.json            chart_facts.py --selftest
chart.json (degrees optional; without degrees D9/D10/combustion/Moon phase are skipped):
  {"asc": {"sign": "Cancer", "deg": 12.5},
   "planets": {"Su": {"sign": "Cancer", "deg": 10.2}, "Mo": {"sign": "Pisces", "deg": 3.1}, "Ma": {...},
               "Me": {...}, "Ju": {...}, "Ve": {...}, "Sa": {..., "retro": true}, "Ra": {...}, "Ke": {...}},
   "lk_houses": {"Su": 1, ...}   # optional: override Lal Kitab houses (e.g. from a bhava/chalit chart)
  }
Houses are whole-sign from the ascendant sign (Parashari baseline; also the KB B2 default for Lal Kitab).
"""
import json, sys

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]
P7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
ALL = P7 + ["Ra", "Ke"]
NAME = dict(Su="Sun", Mo="Moon", Ma="Mars", Me="Mercury", Ju="Jupiter", Ve="Venus", Sa="Saturn", Ra="Rahu", Ke="Ketu")
EXALT = dict(Su=0, Mo=1, Ma=9, Me=5, Ju=3, Ve=11, Sa=6)        # sign index; debilitation = +6
# Natural (naisargika) relationships: BJ II.16-17 (BJ p56-57); PD Adh.II sl.22 (PD p47).
FRIENDS = dict(Su={"Mo", "Ma", "Ju"}, Mo={"Su", "Me"}, Ma={"Su", "Mo", "Ju"}, Me={"Su", "Ve"}, Ju={"Su", "Mo", "Ma"}, Ve={"Me", "Sa"}, Sa={"Me", "Ve"})
ENEMIES = dict(Su={"Ve", "Sa"}, Mo=set(), Ma={"Me"}, Me={"Mo"}, Ju={"Me", "Ve"}, Ve={"Su", "Mo"}, Sa={"Su", "Mo", "Ma"})
SPECIAL_ASPECTS = dict(Ma=[4, 8], Ju=[5, 9], Sa=[3, 10])      # plus the 7th for all
COMBUST = dict(Me=(14, 12), Ve=(10, 8), Ma=(17, 17), Ju=(11, 11), Sa=(15, 15))  # LOL Table 9.1, p299 (pr 271), image-checked

# ---- Lal Kitab tables: Shrimali KB v2.2 (data/lal-kitab/...Knowledge_Base_v2.2.md) ----
LK_PAKKA = dict(Su=[1], Mo=[4], Ma=[3, 8], Me=[7], Ju=[2, 5, 9, 12], Ve=[7], Sa=[8, 10], Ra=[12], Ke=[6])  # B7/p40 (X8 default)
LK_EXALT = dict(Su=[1], Mo=[2], Ma=[10, 8], Me=[6], Ju=[4], Ve=[12], Sa=[7])                            # B4, X1 (Mars 8 and 10)
LK_DEBIL = dict(Su=[7], Mo=[8], Ma=[4], Me=[12], Ju=[10], Ve=[6], Sa=[1])
LK_NODE_TABLE = dict(Ra=([3], [9]), Ke=([9, 12], [3, 6]))            # p33-34/60 table set (X3/X4 version A)
LK_NODE_CHAPTER = dict(Ra=([3, 6], [8, 9, 11]), Ke=([5, 9, 12], [6, 8]))  # p130-138 chapter set (version B)
LK_FRIEND = dict(Su={"Mo", "Ju", "Ma"}, Mo={"Su", "Me"}, Ma={"Su", "Mo", "Ju"}, Me={"Su", "Ve", "Ra"}, Ju={"Su", "Ma", "Mo"},
                 Ve={"Sa", "Me", "Ke"}, Sa={"Me", "Ve", "Ra"}, Ra={"Sa", "Me", "Ke"}, Ke={"Ve", "Ra"})       # B4 (bracketed ones included)
LK_ENEMY = dict(Su={"Ra", "Ke", "Ve", "Sa"}, Mo={"Ra", "Ke"}, Ma={"Me", "Ke"}, Me={"Mo"}, Ju={"Ve", "Me"},
                Ve={"Su", "Mo", "Ra"}, Sa={"Su", "Mo", "Ma"}, Ra={"Su", "Ma", "Ve"}, Ke={"Mo", "Ma"})
LK_ASPECT = {1: [7], 2: [6], 3: [9, 11], 4: [10], 5: [9], 6: [12], 7: [2], 8: [2]}  # B5/R10 ❓ rows 9-12 missing; 5 printed "9,11"; 7->2 printed but p67 says 7 aspects nothing
LK_SINFUL = dict(Ju=[3, 6, 8, 9, 11], Ve=[3, 6, 8, 9, 11], Me=[3, 6, 8, 9, 11], Mo=[3, 6, 8, 9, 11], Sa=[3, 11], Ma=[2, 3, 9])  # B7 p41
MALEFIC_BASE = {"Sa", "Ma", "Ra", "Ke", "Su"}


def sidx(name):
    for i, s in enumerate(SIGNS):
        if s.lower().startswith(str(name).lower()[:3]):
            return i
    raise ValueError(f"unknown sign {name!r}")


def varga(sign, deg, n):
    """Standard Parashari D9 / D10 sign index from sign index + degree within sign (vargas.md formulas)."""
    if n == 9:
        seg, start = int(deg // (10 / 3)), [0, 8, 4][sign % 3]   # movable: same; fixed: 9th; dual: 5th
        return (sign + start + seg) % 12
    seg = int(deg // 3)
    return (sign + (0 if sign % 2 == 0 else 8) + seg) % 12       # odd signs (Aries=1) start at sign; even at 9th


def facts(chart):
    asc = sidx(chart["asc"]["sign"])
    P = {p: dict(v, s=sidx(v["sign"])) for p, v in chart["planets"].items()}
    house = {p: (v["s"] - asc) % 12 + 1 for p, v in P.items()}
    sign_of_house = {h: (asc + h - 1) % 12 for h in range(1, 13)}
    lord = {h: SIGN_LORD[sign_of_house[h]] for h in range(1, 13)}
    occ = {h: [p for p in P if house[p] == h] for h in range(1, 13)}
    out = []
    W = out.append

    # benefic / malefic (LOL p280): Moon by phase, Mercury by association
    malefic = set(MALEFIC_BASE)
    if "deg" in P.get("Mo", {}) and "deg" in P.get("Su", {}):
        el = ((P["Mo"]["s"] * 30 + P["Mo"]["deg"]) - (P["Su"]["s"] * 30 + P["Su"]["deg"])) % 360
        moon_phase = f"{'waxing' if el < 180 else 'waning'}, {el:.0f}° from Sun" + (" (dim: near new Moon — weigh as weak)" if min(el, 360 - el) < 72 else "")
        if el >= 180:
            malefic.add("Mo")
    else:
        moon_phase = "unknown (no degrees)"
    if "Me" in P and any(q in malefic for q in occ[house["Me"]] if q != "Me"):
        malefic.add("Me")

    def aspects_from(p):
        hs = [7] + (SPECIAL_ASPECTS.get(p, []))
        return sorted({(house[p] - 1 + k - 1) % 12 + 1 for k in hs})

    aspected_by = {h: [] for h in range(1, 13)}
    for p in P:
        if p in ("Ra", "Ke"):
            continue
        for h in aspects_from(p):
            aspected_by[h].append(p)

    W(f"# Parashari D1 (whole-sign)  ascendant {SIGNS[asc]}" + (f" {chart['asc'].get('deg')}°" if "deg" in chart["asc"] else ""))
    W(f"Moon phase: {moon_phase}. Natural malefics here: {', '.join(sorted(malefic))}. Node aspects omitted (school-dependent).")
    for p in [q for q in ALL if q in P]:
        v, s = P[p], P[p]["s"]
        dign = []
        if p in EXALT:
            if s == EXALT[p]: dign.append("EXALTED")
            if s == (EXALT[p] + 6) % 12: dign.append("DEBILITATED")
            if SIGN_LORD[s] == p: dign.append("own sign")
        disp = SIGN_LORD[s]
        rel = ""
        if p in FRIENDS and disp != p:
            rel = "friend's sign" if disp in FRIENDS[p] else "enemy's sign" if disp in ENEMIES[p] else "neutral's sign"
        owns = [h for h in range(1, 13) if lord[h] == p]
        extra = []
        if v.get("retro"): extra.append("retrograde")
        if p in COMBUST and "deg" in v and "deg" in P.get("Su", {}):
            d = abs(((s * 30 + v["deg"]) - (P["Su"]["s"] * 30 + P["Su"]["deg"]) + 180) % 360 - 180)
            orb = COMBUST[p][1 if v.get("retro") else 0]
            if d <= orb: extra.append(f"COMBUST ({d:.1f}° from Sun, orb {orb}°)")
        if "deg" in v:
            d9, d10 = varga(s, v["deg"], 9), varga(s, v["deg"], 10)
            extra.append(f"D9 {SIGNS[d9]}{' VARGOTTAMA' if d9 == s else ''}, D10 {SIGNS[d10]}")
        conj = [q for q in occ[house[p]] if q != p]
        asp = [q for q in aspected_by[house[p]] if q != p]
        W(f"- {NAME[p]}: {SIGNS[s]}{' ' + str(v['deg']) + '°' if 'deg' in v else ''} H{house[p]}; {' '.join(dign) or 'no sign dignity'}"
          f"{'; ' + rel if rel else ''}; dispositor {NAME[disp]} (H{house.get(disp, '?')})"
          f"{'; owns H' + ','.join(map(str, owns)) if owns else ''}"
          f"{'; with ' + ','.join(conj) if conj else ''}{'; aspected by ' + ','.join(asp) if asp else ''}"
          f"{'; ' + '; '.join(extra) if extra else ''}")

    W("\n# Houses: occupants | aspects | lord placement | Phaladeepika XV.1/XV.6 strength tests (LOL p282-288)")
    for h in range(1, 13):
        L = lord[h]
        lh = house.get(L)
        prev_, next_ = occ[(h - 2) % 12 + 1], occ[h % 12 + 1]
        notes = []
        if prev_ and next_ and all(q in malefic for q in prev_ + next_): notes.append("HEMMED by malefics")
        if prev_ and next_ and not any(q in malefic for q in prev_ + next_): notes.append("flanked by benefics")
        m_dus = [q for k in (4, 8, 12) for q in occ[(h + k - 2) % 12 + 1] if q in malefic]
        m_tri = [q for k in (5, 9) for q in occ[(h + k - 2) % 12 + 1] if q in malefic]
        if m_dus: notes.append(f"malefics 4/8/12 from it: {','.join(m_dus)}")
        if m_tri: notes.append(f"malefics 5/9 from it: {','.join(m_tri)}")
        if lh in (6, 8, 12) and SIGN_LORD[P[L]['s']] != L: notes.append(f"lord in dusthana H{lh}")
        if L in aspected_by[h] or L in occ[h]: notes.append("lord occupies/aspects own house")
        W(f"- H{h} {SIGNS[sign_of_house[h]]}: occ {','.join(occ[h]) or '—'} | asp {','.join(aspected_by[h]) or '—'} | "
          f"lord {NAME[L]} in H{lh if lh else '?'}{' | ' + '; '.join(notes) if notes else ''}")

    # dispositor chain
    chains = []
    for p in P:
        seen, q = [p], SIGN_LORD[P[p]["s"]]
        while q in P and q not in seen:
            seen.append(q); q = SIGN_LORD[P[q]["s"]]
        chains.append("→".join(seen + ([q] if q in seen else [])))
    finals = sorted({p for p in P if p in P7 and SIGN_LORD[P[p]["s"]] == p})
    W("\nDispositor chains: " + "; ".join(chains) + (f". Final dispositor(s) in own sign: {', '.join(finals)}" if finals else ". No planet in own sign (chains end in a cycle)."))

    # ---- Lal Kitab ----
    lk = dict(house)
    lk.update(chart.get("lk_houses", {}))
    lk_occ = {h: [p for p in lk if lk[p] == h] for h in range(1, 13)}
    src = "supplied lk_houses override" if chart.get("lk_houses") else "whole-sign houses from lagna (KB B2 note)"
    W(f"\n# Lal Kitab fixed-Aries chart ({src}); signs dropped, house N = Kalpurush sign N")
    W("  " + "  ".join(f"H{h}:{'+'.join(lk_occ[h]) or '—'}" for h in range(1, 13)))
    W(f"  Empty houses: {', '.join(str(h) for h in range(1, 13) if not lk_occ[h])}")
    for p in [q for q in ALL if q in lk]:
        h, fl = lk[p], []
        if h in LK_PAKKA[p]: fl.append("in PAKKA GHAR (B7 p40)")
        if p in LK_EXALT:
            if h in LK_EXALT[p]: fl.append("LK-exalted (B4)")
            if h in LK_DEBIL[p]: fl.append("LK-debilitated (B4)")
        else:
            (te, td), (ce, cd) = LK_NODE_TABLE[p], LK_NODE_CHAPTER[p]
            if h in te or h in ce or h in td or h in cd:
                fl.append(f"node dignity ⚠️X3/X4: table-set {'exalt' if h in te else 'debil' if h in td else 'none'}, chapter-set {'exalt' if h in ce else 'debil' if h in cd else 'none'}")
        opp = (h + 5) % 12 + 1
        if not lk_occ[opp]: fl.append(f"SLEEPING? 7th from it (H{opp}) empty (B7 p44, R14)")
        mates = [q for q in lk_occ[h] if q != p]
        en = [q for q in mates if q in LK_ENEMY[p]]
        fr = [q for q in mates if q in LK_FRIEND[p]]
        if en: fl.append(f"with LK-enemies {','.join(en)}")
        if fr: fl.append(f"with LK-friends {','.join(fr)}")
        if p in LK_SINFUL and h in LK_SINFUL[p]: fl.append("'sinful' placement (B7 p41)")
        if (p in ("Ra", "Ke") and (h == 4 or "Mo" in mates)) or (p == "Sa" and (h == 11 or "Ju" in mates)): fl.append("DHARMI (B7 p42)")
        if p in ("Su", "Mo") and ({"Ra", "Ke"} & set(mates)): fl.append("eclipse: with node (B7 p73)")
        for q in lk:
            if q != p and h in LK_PAKKA.get(q, []) and lk[q] not in LK_PAKKA[p]:
                fl.append(f"rival? sits in {q}'s pakka ghar; {q} not in {p}'s (B7 p43)")
            if q != p and h in LK_PAKKA.get(q, []) and lk[q] in LK_PAKKA[p] and p < q:
                fl.append(f"ALLY with {q}: exchange of pakka houses (B7 p42)")
        tgt = LK_ASPECT.get(h)
        if tgt: fl.append(f"LK aspect → H{','.join(map(str, tgt))}{' ❓' if h in (3, 5, 7) else ''}")
        W(f"- {NAME[p]} H{h}: {'; '.join(fl) or '—'}")
    blind = [p for p in lk_occ[10] if p in LK_DEBIL and 10 in LK_DEBIL[p]]
    if blind: W(f"  Blind-chart check (B7 p41,48; H10 debilitated + mutual enemies): debilitated in 10: {blind} — verify enmity.")
    if "Ma" in lk and lk["Ma"] in (1, 4, 7, 8, 12): W("  Mangalik by house (B9, a [VED] rule reproduced by the author).")
    W("  Rin (debt) signatures: check KB B12 against this house map; judge debts from the natal chart only.")
    W("  Rows 9-12 of the LK aspect table are missing in source (R10); never fill them from Parashari aspects.")
    return "\n".join(out)


def selftest():
    # KB B2 p219 example: Cancer lagna; Sun 1; Me+Ve 2; Mars 3; Ketu 5; Sat 8; Jup+Rahu 11; Moon 12
    ch = {"asc": {"sign": "Cancer"}, "planets": {
        "Su": {"sign": "Cancer"}, "Me": {"sign": "Leo"}, "Ve": {"sign": "Leo"}, "Ma": {"sign": "Virgo"}, "Ke": {"sign": "Scorpio"},
        "Sa": {"sign": "Aquarius"}, "Ju": {"sign": "Taurus"}, "Ra": {"sign": "Taurus"}, "Mo": {"sign": "Gemini"}}}
    t = facts(ch)
    assert "H1:Su  H2:Me+Ve  H3:Ma  H4:—  H5:Ke" in t, t
    assert "Saturn H8: in PAKKA GHAR" in t and "Mars H3: in PAKKA GHAR" in t
    assert varga(0, 3 + 1 / 3, 9) == 1, "exactly 3°20' Aries -> second navamsa (Taurus)"
    assert varga(1, 0.5, 9) == 9, "Taurus 0°30' -> Capricorn navamsa"
    assert varga(1, 0.5, 10) == 9, "Taurus (even) D10 starts at 9th = Capricorn"
    assert varga(10, 5.0, 10) == 11, "Aquarius (odd, 11th sign) 5° -> second D10 = Pisces"
    # Jupiter in Cancer aspects Scorpio, Capricorn, Pisces (examples.md #4)
    ch2 = {"asc": {"sign": "Aries"}, "planets": {"Ju": {"sign": "Cancer"}, "Ve": {"sign": "Aquarius"}}}
    t2 = facts(ch2)
    assert "H11 Aquarius: occ Ve | asp —" in t2 and "H8 Scorpio: occ — | asp Ju" in t2, t2
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    elif len(sys.argv) == 2:
        print(facts(json.load(open(sys.argv[1]))))
    else:
        sys.exit(__doc__)
