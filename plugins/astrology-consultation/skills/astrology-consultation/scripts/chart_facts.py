#!/usr/bin/env python3
"""Derive structural chart facts from SUPPLIED positions. No ephemeris: it never computes where a planet is.

It removes hand-arithmetic errors (house counting, lordship, aspects, D9/D10, dispositors). It does NOT interpret.
The private edition adds a Lal Kitab block from scripts/lal_kitab.py; the public edition has no Lal Kitab part.

usage:  chart_facts.py chart.json            chart_facts.py --selftest
chart.json (degrees optional; without degrees D9/D10/combustion/Moon phase are skipped):
  {"asc": {"sign": "Cancer", "deg": 12.5},
   "planets": {"Su": {"sign": "Cancer", "deg": 10.2}, "Mo": {"sign": "Pisces", "deg": 3.1}, "Ma": {...},
               "Me": {...}, "Ju": {...}, "Ve": {...}, "Sa": {..., "retro": true}, "Ra": {...}, "Ke": {...}},
   "lk_houses": {"Su": 1, ...}   # optional, private edition only (see scripts/lal_kitab.py)
  }
Houses are whole-sign from the ascendant sign (Parashari baseline).
"""
import json, os, re, sys

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

MALEFIC_BASE = {"Sa", "Ma", "Ra", "Ke", "Su"}


def sidx(name):
    for i, s in enumerate(SIGNS):
        if s.lower().startswith(str(name).lower()[:3]):
            return i
    raise ValueError(f"unknown sign {name!r}")


def varga(sign, deg, n):
    """Standard Parashari D9 / D10 sign index from sign index + degree within sign (vargas.md formulas)."""
    if n == 9:
        seg, start = int(deg / (10 / 3) + 1e-9), [0, 8, 4][sign % 3]   # +1e-9: exactly 10°/20° start the next part (= engine.varga)
        return (sign + start + seg) % 12
    seg = int(deg / 3 + 1e-9)
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

    # Lal Kitab: scripts/lal_kitab.py exists only in the private edition (council B2, 2026-10-12)
    lk = _lal_kitab()
    if lk is None:
        W("\n# Lal Kitab: not part of this edition (no Lal Kitab chart, flags, rules or remedies).")
    elif isinstance(lk, str):
        W(f"\n# Lal Kitab: scripts/lal_kitab.py not used ({lk}). No Lal Kitab output; the facts above are unaffected.")
    else:
        n = len(out)
        try:
            lk.section(chart, house, out, W, ALL, NAME)
        except Exception as e:   # never let a broken private module take the Parashari facts down with it
            del out[n:]
            W(f"\n# Lal Kitab: the Lal Kitab block failed ({type(e).__name__}: {e}). No Lal Kitab output; the facts above are unaffected.")
        else:
            if len(out) == n:
                W("\n# Lal Kitab: scripts/lal_kitab.py produced no output.")
    return "\n".join(out)


def _lal_kitab():
    """The private edition's Lal Kitab module, loaded by path (callers may import this file by path too).
    Returns the module, None when absent (public edition), or a reason string when the file is present but unusable:
    it fails to load, lacks section()/selftest(), or sits in a public skill folder (a leftover private file)."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "lal_kitab.py")
    if not os.path.exists(path):
        return None
    try:
        desc = re.search(r"^description: .*$", open(os.path.join(here, "..", "SKILL.md"), encoding="utf-8").read(), re.M)
        if desc and "Lal Kitab is not part of this edition" in desc.group():   # the public edition's description
            return "ignored: this skill folder is the public edition — a file left over from the private edition? remove it"
    except OSError:
        pass
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("lal_kitab", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        return f"failed to load: {type(e).__name__}: {e}"
    if not (callable(getattr(mod, "section", None)) and callable(getattr(mod, "selftest", None))):
        return "it has no section()/selftest() — stale or foreign file?"
    return mod


def selftest():
    lk = _lal_kitab()
    assert not isinstance(lk, str), f"scripts/lal_kitab.py unusable: {lk}"
    if lk:
        lk.selftest(facts)   # private edition: the Lal Kitab block checks itself
    assert varga(0, 3 + 1 / 3, 9) == 1, "exactly 3°20' Aries -> second navamsa (Taurus)"
    assert varga(1, 0.5, 9) == 9, "Taurus 0°30' -> Capricorn navamsa"
    assert varga(1, 0.5, 10) == 9, "Taurus (even) D10 starts at 9th = Capricorn"
    assert varga(10, 5.0, 10) == 11, "Aquarius (odd, 11th sign) 5° -> second D10 = Pisces"
    # Jupiter in Cancer aspects Scorpio, Capricorn, Pisces (examples.md #4)
    ch2 = {"asc": {"sign": "Aries"}, "planets": {"Ju": {"sign": "Cancer"}, "Ve": {"sign": "Aquarius"}}}
    t2 = facts(ch2)
    assert "H11 Aquarius: occ Ve | asp —" in t2 and "H8 Scorpio: occ — | asp Ju" in t2, t2
    if not lk:
        assert "# Lal Kitab: not part of this edition" in t2, t2
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    elif sys.argv[1:] in (["-h"], ["--help"]):
        print(__doc__.strip())
    elif len(sys.argv) == 2:
        print(facts(json.load(open(sys.argv[1]))))
    else:
        sys.exit(__doc__)
