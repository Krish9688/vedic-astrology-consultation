#!/usr/bin/env python3
"""Derive structural chart facts from SUPPLIED positions. No ephemeris: it never computes where a planet is.

It removes hand-arithmetic errors (house counting, lordship, aspects, D9/D10, dispositors). It does NOT interpret.
The private edition adds a Lal Kitab block from scripts/lal_kitab.py; the public edition has no Lal Kitab part.

usage:  chart_facts.py chart.json            chart_facts.py --json chart.json (Parashari fact ids, schemas/derived_facts.schema.json)
        chart_facts.py --selftest
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
# BPHS moolatrikona: sign index, from°, to° (the same table as astro/calc/strength.py MOOLATRIKONA; a test keeps them equal)
MOOLATRIKONA = dict(Su=(4, 0, 20), Mo=(1, 3, 30), Ma=(0, 0, 12), Me=(5, 15, 20), Ju=(8, 0, 10), Ve=(6, 0, 15), Sa=(10, 0, 20))


def sidx(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"unknown sign {name!r}")   # "" would match Aries (every string starts with "")
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


def derive(chart):
    """The structural facts every section uses: signs, houses, lords, occupants, malefics, graha drishti."""
    asc = sidx(chart["asc"]["sign"])
    for who, v in [("asc", chart["asc"])] + list(chart["planets"].items()):   # council 4 R3 L3: fail loudly, not with a TypeError
        if who != "asc" and who not in ALL:
            raise ValueError(f"unknown planet key {who!r} (use {', '.join(ALL)})")
        d = v.get("deg")
        if d is not None and (isinstance(d, bool) or not isinstance(d, (int, float)) or not 0 <= d < 30):
            raise ValueError(f"{who} deg must be a number in [0, 30), not {d!r}")
    P = {p: dict(v, s=sidx(v["sign"])) for p, v in chart["planets"].items()}
    house = {p: (v["s"] - asc) % 12 + 1 for p, v in P.items()}
    sign_of_house = {h: (asc + h - 1) % 12 for h in range(1, 13)}
    lord = {h: SIGN_LORD[sign_of_house[h]] for h in range(1, 13)}
    occ = {h: [p for p in P if house[p] == h] for h in range(1, 13)}

    # benefic / malefic (LOL p280): Moon by phase, Mercury by association
    malefic, el = set(MALEFIC_BASE), None
    if "deg" in P.get("Mo", {}) and "deg" in P.get("Su", {}):
        el = ((P["Mo"]["s"] * 30 + P["Mo"]["deg"]) - (P["Su"]["s"] * 30 + P["Su"]["deg"])) % 360
        if el >= 180:
            malefic.add("Mo")
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
    return dict(asc=asc, asc_deg=chart["asc"].get("deg"), P=P, house=house, sign_of_house=sign_of_house, lord=lord, occ=occ, malefic=malefic, el=el,
                aspects_from=aspects_from, aspected_by=aspected_by)


# Candidate yogas and Kuja conventions (references/yoga-definitions.md). One function per NAMED definition;
# each reports whether its own conditions hold. Candidates, not results: strength, cancellation and timing stay with the
# skill's yoga procedure. Base rates come from tools/calc/yoga_baserates.py (these exact functions, random charts);
# definitions, sources and limits: references/yoga-definitions.md.
BPHS_MAP = "source map BPHS_part3.md §5 (BPHS ch. 34-38), not page-checked"
# share of 4000 random charts (1950-2010) in which the condition holds; regenerate with tools/calc/yoga_baserates.py
BASE_RATE = {"GK-BPHS36": "9%", "KEM-BARE": "45%", "KEM-BPHS": "3%", "KESARI-LOOSE": "34%", "KUJA-BPHS80": "15%",
             "KUJA-PD11.3": "10%", "KUJA-POPULAR": "88%", "PMP-BPHS": "34%", "PMP-LOL": "48%", "RAJA-KK": "68%",
             "RAJA-KKP": "61%"}
KENDRA, KONA, DUSTHANA = {1, 4, 7, 10}, {1, 5, 9}, {6, 8, 12}
MAHAPURUSHA = dict(Ma="Ruchaka", Me="Bhadra", Ju="Hamsa", Ve="Malavya", Sa="Sasa")


def _from(D, p, ref_sign):
    return (D["P"][p]["s"] - ref_sign) % 12 + 1


def _contact(D, p, by):
    """Planets in `by` that are with p or aspect p's house (graha drishti)."""
    return [q for q in sorted(by) if q in D["P"] and q != p and (D["house"][q] == D["house"][p] or D["house"][p] in D["aspects_from"](q))]


def _combust(D, p):
    P = D["P"]
    if p not in COMBUST or "deg" not in P[p] or "deg" not in P.get("Su", {}):
        return None
    d = abs(((P[p]["s"] * 30 + P[p]["deg"]) - (P["Su"]["s"] * 30 + P["Su"]["deg"]) + 180) % 360 - 180)
    return d <= COMBUST[p][1 if P[p].get("retro") else 0]


def candidates(D):
    """[(id, label, holds: True/False/None, detail, source)] for every definition whose planets are supplied."""
    P, house, lord = D["P"], D["house"], D["lord"]
    benefic = {"Ju", "Ve", "Me", "Mo"} - D["malefic"]
    rows = []
    if "Ju" in P and "Mo" in P:
        m = P["Mo"]["s"]
        k_l, k_m = house["Ju"] in KENDRA, _from(D, "Ju", m) in KENDRA
        contact = _contact(D, "Ju", benefic - {"Ju"})            # Jupiter is not its own benefic contact (VED-F4)
        deb, comb, enemy = P["Ju"]["s"] == 9, _combust(D, "Ju"), SIGN_LORD[P["Ju"]["s"]] in ENEMIES["Ju"]
        strict = (k_l or k_m) and bool(contact) and not deb and not enemy and comb is not True
        rows.append(("GK-BPHS36", "Gajakesari, strict: Jupiter in a kendra from the lagna or the Moon, joined or aspected "
                     "by a benefic, not debilitated, combust or in an enemy's sign",
                     None if strict and comb is None else strict,
                     f"kendra from lagna {'yes' if k_l else 'no'}, from Moon {'yes' if k_m else 'no'}; benefic contact "
                     f"{','.join(contact) or 'none'}; debilitated {'yes' if deb else 'no'}; enemy's sign "
                     f"{'yes' if enemy else 'no'}; combust {'unknown (no degrees)' if comb is None else 'yes' if comb else 'no'}",
                     f"BPHS 36.3-4, {BPHS_MAP}"))
        rows.append(("KESARI-LOOSE", "Kesari (loose 'Gajakesari'): Jupiter in a kendra from the Moon", k_m,
                     f"Jupiter M{_from(D, 'Ju', m)}", "Phaladeepika VI.14 per the BPHS translator (only 'Kesari'); called Gajakesari "
                     "by CRUX p28-30 and HJH1 p118 - source map BPHS_part3.md, not page-checked"))
    if "Mo" in P:
        m = P["Mo"]["s"]
        others = [q for q in ("Ma", "Me", "Ju", "Ve", "Sa") if q in P]
        flank = [q for q in others if _from(D, q, m) in (2, 12)]
        cancel = [q for q in others if P[q]["s"] == m or house[q] in KENDRA] + (["Mo"] if house["Mo"] in KENDRA else [])
        rows.append(("KEM-BARE", "Kemadruma (Varahamihira): no planet other than the Sun (nodes not counted) in the 2nd "
                     "or 12th from the Moon", not flank, f"2nd/12th from the Moon: {','.join(flank) or 'empty'}",
                     "Brihat Jataka XIII (p175-178), source map BJ.md, not page-checked; Varahamihira rejects the "
                     "other schools' versions"))
        rows.append(("KEM-BPHS", "Kemadruma (BPHS 37.11-13): besides the 2nd/12th, no planet but the Sun with the Moon or "
                     "in a kendra from the lagna - the Moon itself in a kendra counts (LOL p322; Garga/Parasara via BJ)",
                     not flank and not cancel,
                     f"a planet {'with the Moon or ' if any(P[q]['s'] == m for q in others) else ''}in a kendra: "
                     f"{','.join(cancel)}" if not flank and cancel else "2nd/12th occupied" if flank else
                     "nothing with the Moon or in a kendra", f"BPHS p398 (ch. 37 sl. 11-13), {BPHS_MAP}"))
    for q, name in MAHAPURUSHA.items():
        if q in P and (P[q]["s"] == EXALT[q] or SIGN_LORD[P[q]["s"]] == q):
            rows.append((f"PMP-{q}-BPHS", f"{name} (Pancha Mahapurusha): {NAME[q]} own/exalted in a kendra from the lagna",
                         house[q] in KENDRA, f"{NAME[q]} H{house[q]}; BPHS gives no cancellation in this chapter",
                         "BPHS ch. 75, source map BPHS_part6.md §5.1, not page-checked"))
            rows.append((f"PMP-{q}-LOL", f"{name}, LOL variant: kendra or kona from the lagna", house[q] in KENDRA | KONA,
                         f"{NAME[q]} H{house[q]}", "Phaladeepika VI.2-4 as given in LOL p311 (kendra or kona; BPHS "
                         "ch. 75: kendra only), source map LOL.md, not page-checked"))
    owns = {q: [h for h in range(1, 13) if lord[h] == q] for q in P}
    pairs = set()
    for a in {lord[h] for h in KENDRA}:
        for b in {lord[h] for h in KONA}:
            if a != b and a in P and b in P:
                pairs.add(tuple(sorted((a, b))))
    def dispute(qs):
        """BPHS 34.14-15: a lord that also owns a dusthana gives no yoga by these relations alone (not the luminaries);
        translator: the moolatrikona sign decides which lordship shows. PD XX.45: yoga even so."""
        out = []
        for q in qs:
            bad = sorted(set(owns[q]) & DUSTHANA)
            if q in ("Su", "Mo") or not bad:
                continue
            mt = (MOOLATRIKONA[q][0] - D["asc"]) % 12 + 1
            out.append(f"{NAME[q]} also owns H{','.join(map(str, bad))}" + (" (its moolatrikona: the evil lordship "
                       "prevails)" if mt in bad else " (moolatrikona in the good house: the good lordship shows)"
                       if mt in KENDRA | KONA else ""))
        return ("; DISPUTED - " + "; ".join(out) + ": BPHS 34.14-15 gives no yoga by relation alone, PD XX.45 gives "
                "yoga even so") if out else ""
    src = f"BPHS p356-358 (ch. 34 sl. 11-15), {BPHS_MAP}; PD XX.45 (p245) source map PD_part1.md, not page-checked"
    for a, b in sorted(pairs):
        same = P[a]["s"] == P[b]["s"]
        rel = (["joined in a kendra/kona"] if same and house[a] in KENDRA | KONA else []) + \
              (["exchange"] if SIGN_LORD[P[a]["s"]] == b and SIGN_LORD[P[b]["s"]] == a else []) + \
              (["mutual opposition"] if (house[b] - house[a]) % 12 == 6 else [])
        if rel:
            rows.append((f"RAJA-KK-{a}{b}", f"kendra-kona lord relation {NAME[a]}-{NAME[b]} (BPHS 34.11-12)", True,
                         f"{'/'.join(rel)}; {NAME[a]} owns H{','.join(map(str, owns[a]))}, {NAME[b]} owns "
                         f"H{','.join(map(str, owns[b]))}" + dispute((a, b)), src))
    for q in sorted({lord[h] for h in (5, 9)} | {lord[h] for h in (4, 7, 10)}):
        if q not in P or lord[1] == q:
            continue
        kona_lord, kendra_lord = q in {lord[5], lord[9]}, q in {lord[4], lord[7], lord[10]}
        placed = (kona_lord and house[q] in KENDRA) or (kendra_lord and house[q] in KONA - {1})
        if placed and not (kona_lord and kendra_lord):
            rows.append((f"RAJA-KKP-{q}", f"{'trinal' if kona_lord else 'angular'} lord {NAME[q]} placed in "
                         f"{'an angle' if kona_lord else 'a trine'} (BPHS 34.11-12)", True,
                         f"{NAME[q]} owns H{','.join(map(str, owns[q]))}, in H{house[q]}" + dispute((q,)), src))
    return rows


def kuja(D):
    """Mars from the lagna, Moon and Venus under each Kuja convention (VED-F5). Membership only, never a verdict."""
    P, house = D["P"], D["house"]
    if "Ma" not in P:
        return []
    ref = {"lagna": house["Ma"]} | {NAME[r]: _from(D, "Ma", P[r]["s"]) for r in ("Mo", "Ve") if r in P}
    benefic = {"Ju", "Ve", "Me", "Mo"} - D["malefic"]
    contact = _contact(D, "Ma", benefic)
    bphs = house["Ma"] in {12, 4, 7, 8}
    pop = [k for k, h in ref.items() if h in {1, 2, 4, 7, 8, 12}]
    seventh = (D["asc"] + 6) % 12
    mars_own = P["Ma"]["s"] in (0, 7, 9)
    with_moon = "Mo" in P and P["Mo"]["s"] == P["Ma"]["s"]
    asc_deg = D.get("asc_deg")
    amsa = None if asc_deg is None else varga(seventh, asc_deg, 9)     # navamsa of the descendant (asc + 180°)
    pd_rasi = SIGN_LORD[seventh] == "Ma"
    pd = house["Ma"] == 7 or (pd_rasi and amsa is not None and SIGN_LORD[amsa] == "Ma")
    pd_holds = pd if (house["Ma"] == 7 or not pd_rasi or amsa is not None) else None
    return [("KUJA-BPHS80", "BPHS 80.47-49: Mars 12/4/7/8 from the lagna; a benefic aspect or association cancels",
             bphs and not contact, f"Mars H{house['Ma']}" + (f"; cancelled by {','.join(contact)}" if bphs and contact else "")
             + "; the 'partner has the same yoga' clause needs both charts", "source map BPHS_part6.md (BPHS p955), not page-checked"),
            ("KUJA-POPULAR", "popular rule (LOL: 'not in any authoritative text'): Mars 1/2/4/7/8/12 from lagna, Moon or Venus",
             bool(pop), "Mars from " + ", ".join(f"{k} {h}" for k, h in ref.items()) + (f"; meets it from {', '.join(pop)}"
             if pop else "") + ("; LOL exception: Moon with Mars cancels it" if pop and with_moon else "") +
             ("; LOL exception: Mars own/exalted modifies or cancels it (experts disagree)" if pop and mars_own else "") +
             "; the partner and age (about 28-30) exceptions need more than this chart",
             "LOL p329-331, source map LOL.md, not page-checked"),
            ("KUJA-PD11.3", "Phaladeepika XI.3: Mars in the 7th, or the 7th sign and its navamsa both Mars's",
             pd_holds, f"Mars H{house['Ma']}; 7th sign {SIGNS[seventh]}" + (f", descendant navamsa {SIGNS[amsa]}"
             if amsa is not None else ", descendant navamsa unknown (no ascendant degree)"),
             "PD p141-142 (XI.3), source map PD_part1.md, not page-checked")]


def family(rid):
    """Base-rate key: PMP-Ve-BPHS -> PMP-BPHS (any Mahapurusha), RAJA-KK-MaMe -> RAJA-KK (any pair), else the id."""
    parts = rid.split("-")
    return f"PMP-{parts[2]}" if parts[0] == "PMP" else f"RAJA-{parts[1]}" if parts[0] == "RAJA" else rid


def candidates_kuja(chart):
    """PD XI.3 verdict for a chart dict (selftest helper)."""
    return next(r[2] for r in kuja(derive(chart)) if r[0] == "KUJA-PD11.3")


def _candidate_section(D, W):
    W("\n# Candidate yogas and Kuja conventions (computed; named definitions, candidates only - not results)")
    W("Each line: definition id | holds? | details | source | how often the condition holds in random charts.")
    for rid, label, holds, detail, src in candidates(D) + kuja(D):
        mark = "HOLDS" if holds else "undetermined" if holds is None else "does not hold"
        rate = BASE_RATE.get(family(rid))
        W(f"- [{rid}] {label}: {mark}. {detail}. Source: {src}." + (f" Base rate {rate}." if rate else ""))
    W("Kuja lines are convention membership for comparison only, never a marriage verdict (CR-V16); several conventions"
      " fire in most charts.")


def _dignity(p, s):
    """Sign dignity words of planet p in sign index s (seven planets only): EXALTED / DEBILITATED / own sign."""
    out = []
    if p in EXALT:
        if s == EXALT[p]: out.append("EXALTED")
        if s == (EXALT[p] + 6) % 12: out.append("DEBILITATED")
        if SIGN_LORD[s] == p: out.append("own sign")
    return out


def _sign_relation(p, s):
    """'friend's sign' / 'enemy's sign' / 'neutral's sign' by the natural relation to the sign lord; '' for own sign and nodes."""
    disp = SIGN_LORD[s]
    if p in FRIENDS and disp != p:
        return "friend's sign" if disp in FRIENDS[p] else "enemy's sign" if disp in ENEMIES[p] else "neutral's sign"
    return ""


def _mt_state(p, v):
    """Moolatrikona: None (not the MT sign), 'deg?' (MT sign, no degree), True/False (MT sign; inside/outside the MT degrees)."""
    if MOOLATRIKONA[p][0] != v["s"]:
        return None
    lo, hi = MOOLATRIKONA[p][1:]
    return "deg?" if "deg" not in v else lo <= v["deg"] <= hi


def _compound(p, P):
    """Compound (panchadha) relation of p to its sign's dispositor: (dispositor, word), or None when it is p itself or absent."""
    s = P[p]["s"]
    disp = SIGN_LORD[s]
    if disp == p or disp not in P:
        return None
    nat = 1 if disp in FRIENDS[p] else -1 if disp in ENEMIES[p] else 0
    tmp = 1 if (P[disp]["s"] - s) % 12 + 1 in (2, 3, 4, 10, 11, 12) else -1
    return disp, {2: "great friend", 1: "friend", 0: "neutral", -1: "enemy", -2: "great enemy"}[nat + tmp]


def _d9_dignity(p, d9):
    return ("EXALTED" if d9 == EXALT[p] else "DEBILITATED" if d9 == (EXALT[p] + 6) % 12 else
            "own sign" if SIGN_LORD[d9] == p else "")


def _house_notes(D, h):
    """Phaladeepika XV.1/XV.6 tests for house h as [(code, text)]; the text goes into the report, the code into the JSON ids."""
    occ, malefic, lord, aspected_by, house, P = D["occ"], D["malefic"], D["lord"], D["aspected_by"], D["house"], D["P"]
    L = lord[h]
    lh = house.get(L)
    prev_, next_ = occ[(h - 2) % 12 + 1], occ[h % 12 + 1]
    notes = []
    if prev_ and next_ and all(q in malefic for q in prev_ + next_): notes.append(("HEMMED", "HEMMED by malefics"))
    if prev_ and next_ and not any(q in malefic for q in prev_ + next_): notes.append(("FLANKED_BENEFICS", "flanked by benefics"))
    m_dus = [q for k in (4, 8, 12) for q in occ[(h + k - 2) % 12 + 1] if q in malefic]
    m_tri = [q for k in (5, 9) for q in occ[(h + k - 2) % 12 + 1] if q in malefic]
    if m_dus: notes.append((f"MALEFICS_4_8_12:{','.join(m_dus)}", f"malefics 4/8/12 from it: {','.join(m_dus)}"))
    if m_tri: notes.append((f"MALEFICS_5_9:{','.join(m_tri)}", f"malefics 5/9 from it: {','.join(m_tri)}"))
    if lh in (6, 8, 12) and SIGN_LORD[P[L]['s']] != L: notes.append((f"LORD_IN_DUSTHANA:H{lh}", f"lord in dusthana H{lh}"))
    if L in aspected_by[h] or L in occ[h]: notes.append(("LORD_OCCUPIES_OR_ASPECTS", "lord occupies/aspects own house"))
    return notes


def _chains(P):
    """(dispositor chains as 'Su→Mo→...' strings, final dispositors: planets in their own sign)."""
    chains = []
    for p in P:
        seen, q = [p], SIGN_LORD[P[p]["s"]]
        while q in P and q not in seen:
            seen.append(q); q = SIGN_LORD[P[q]["s"]]
        chains.append("→".join(seen + ([q] if q in seen else [])))
    return chains, sorted({p for p in P if p in P7 and SIGN_LORD[P[p]["s"]] == p})


COMPUTED = "  [COMPUTED: calculated chart facts, not interpretation]"   # claim_basis of every line below (P3-1)


def facts(chart):
    D = derive(chart)
    asc, P, house, sign_of_house, lord, occ, malefic, el, aspects_from, aspected_by = (
        D[k] for k in ("asc", "P", "house", "sign_of_house", "lord", "occ", "malefic", "el", "aspects_from", "aspected_by"))
    out = []
    W = out.append
    moon_phase = ("unknown (no degrees)" if el is None else f"{'waxing' if el < 180 else 'waning'}, {el:.0f}° from Sun"
                  + (" (dim: near new Moon — weigh as weak)" if min(el, 360 - el) < 72 else ""))

    W(f"# Parashari D1 (whole-sign)  ascendant {SIGNS[asc]}" + (f" {chart['asc'].get('deg')}°" if "deg" in chart["asc"] else "") + COMPUTED)
    W(f"Moon phase: {moon_phase}. Natural malefics here: {', '.join(sorted(malefic))}. Node aspects omitted (school-dependent).")
    for p in [q for q in ALL if q in P]:
        v, s = P[p], P[p]["s"]
        dign = _dignity(p, s)
        disp = SIGN_LORD[s]
        rel = _sign_relation(p, s)
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
        notes = [t for _, t in _house_notes(D, h)]
        W(f"- H{h} {SIGNS[sign_of_house[h]]}: occ {','.join(occ[h]) or '—'} | asp {','.join(aspected_by[h]) or '—'} | "
          f"lord {NAME[L]} in H{lh if lh else '?'}{' | ' + '; '.join(notes) if notes else ''}")

    # dignity detail (VED-F12): moolatrikona, compound (panchadha) relation to the dispositor, D9 dignity
    W("\n# Dignity detail (computed): moolatrikona | compound relation to the dispositor | D9 dignity")
    for p in [q for q in P7 if q in P]:
        v, s = P[p], P[p]["s"]
        parts = []
        mt = _mt_state(p, v)
        if mt is not None:
            lo, hi = MOOLATRIKONA[p][1:]
            parts.append("MT sign (degree needed)" if mt == "deg?" else
                         "MOOLATRIKONA" if mt else f"MT sign, outside the MT degrees ({lo}–{hi}°)")
        comp = _compound(p, P)
        if comp:
            parts.append(f"towards dispositor {NAME[comp[0]]}: {comp[1]}")
        if "deg" in v:
            d9 = varga(s, v["deg"], 9)
            d9d = _d9_dignity(p, d9)
            parts.append(f"D9 {SIGNS[d9]}" + (f" {d9d}" if d9d else ""))
        W(f"- {NAME[p]}: {'; '.join(parts) or '—'}")
    if el is not None:
        near = min(el, 360 - el) < 72
        W(f"Moon as malefic, two conventions (B-20 open): waning = malefic (LOL p280): {'yes' if el >= 180 else 'no'}; "
          f"within 72° of the Sun: {'yes' if near else 'no'}. The tests above use the first.")

    # from the Moon (B-21): the same counting from the Chandra lagna
    if "Mo" in P:
        m = P["Mo"]["s"]
        mh = {p: (v["s"] - m) % 12 + 1 for p, v in P.items()}
        W(f"\n# From the Moon (Chandra lagna {SIGNS[m]}): occupants | lord placement, counted from the Moon")
        for h in range(1, 13):
            L = SIGN_LORD[(m + h - 1) % 12]
            W(f"- M{h} {SIGNS[(m + h - 1) % 12]}: occ {','.join(q for q in P if mh[q] == h) or '—'} | "
              f"lord {NAME[L]} in M{mh.get(L, '?')}")

    _candidate_section(D, W)

    # dispositor chain
    chains, finals = _chains(P)
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


SCHEMA_ID = "derived_facts/1"
CONVENTIONS = {
    "houses": "whole-sign from the ascendant sign (Parashari baseline)",
    "node_aspects": "omitted (school-dependent); Rahu and Ketu aspect nothing here",
    "aspects": "graha drishti: the 7th for all, plus Mars 4/8, Jupiter 5/9, Saturn 3/10",
    "malefics": "Sun, Mars, Saturn, Rahu, Ketu; Moon when waning; Mercury when with a malefic (LOL p280)",
    "waning_moon": "both shown until B-20 is decided: F.moon.malefic_waning (waning = malefic; the malefic set and the "
                   "tests use this one) and F.moon.malefic_72 (within 72 degrees of the Sun)",
    "combustion": "LOL Table 9.1 orbs, the retrograde orb when retrograde; null without degrees or for Sun, Moon, nodes",
    "moolatrikona": "BPHS table (same as astro/calc/strength.py); null when the sign is not the MT sign, or no degree",
    "compound_to_dispositor": "natural plus temporary (panchadha) relation to the sign lord; null for own sign or lord absent",
    "yogas": "candidates under named definitions, not results; F.yoga.<ID>.holds is null when undetermined; "
             "'.' in an ID becomes '_'",
    "dignity": "'+'-joined EXALTED / DEBILITATED / own sign, or 'none' (seven planets; the nodes have none)",
    "nulls": "null means the data needed (degrees, a planet) was not supplied or the fact does not apply",
}


def facts_json(chart):
    """The same facts as facts() as stable ids: {"schema", "conventions", "facts": {"F.Sa.house": 7, ...}}.
    Parashari only (no Lal Kitab). Every value comes from derive()/candidates()/kuja() and the helpers the text uses.
    IDs: F.asc.{sign,deg}; F.<P>.{sign,deg,house,retro,dignity,sign_relation,dispositor,dispositor_house,owns,with,
    aspected_by,combust,d9,d10,vargottama,moolatrikona,compound_to_dispositor,d9_dignity} per planet P present;
    F.H<h>.{sign,occupants,aspected_by,lord,lord_house,notes} h=1..12; F.M<h>.{sign,occupants,lord,lord_house} from the
    Moon (when present); F.moon.{phase,elongation,malefic_waning,malefic_72}; F.malefics;
    F.yoga.<ID>.{holds,detail,source}; F.dispositor.{chains,finals}."""
    D = derive(chart)
    asc, P, house, soh, lord, occ, el = (D[k] for k in ("asc", "P", "house", "sign_of_house", "lord", "occ", "el"))
    F = {"F.asc.sign": SIGNS[asc], "F.asc.deg": D["asc_deg"]}
    for p in [q for q in ALL if q in P]:
        v, s = P[p], P[p]["s"]
        deg = v.get("deg")
        disp, comp = SIGN_LORD[s], _compound(p, P) if p in P7 else None
        d9 = varga(s, deg, 9) if deg is not None else None
        mt = _mt_state(p, v) if p in P7 else None
        F |= {f"F.{p}.sign": SIGNS[s], f"F.{p}.deg": deg, f"F.{p}.house": house[p], f"F.{p}.retro": bool(v.get("retro")),
              f"F.{p}.dignity": "+".join(_dignity(p, s)) or "none", f"F.{p}.sign_relation": _sign_relation(p, s) or None,
              f"F.{p}.dispositor": disp, f"F.{p}.dispositor_house": house.get(disp),
              f"F.{p}.owns": [h for h in range(1, 13) if lord[h] == p],
              f"F.{p}.with": [q for q in occ[house[p]] if q != p],
              f"F.{p}.aspected_by": [q for q in D["aspected_by"][house[p]] if q != p],
              f"F.{p}.combust": _combust(D, p),
              f"F.{p}.d9": None if d9 is None else SIGNS[d9],
              f"F.{p}.d10": None if deg is None else SIGNS[varga(s, deg, 10)],
              f"F.{p}.vargottama": None if d9 is None else d9 == s,
              f"F.{p}.moolatrikona": None if mt in (None, "deg?") else mt,
              f"F.{p}.compound_to_dispositor": comp[1] if comp else None,
              f"F.{p}.d9_dignity": None if d9 is None or p not in P7 else _d9_dignity(p, d9) or "none"}
    for h in range(1, 13):
        L = lord[h]
        F |= {f"F.H{h}.sign": SIGNS[soh[h]], f"F.H{h}.occupants": occ[h], f"F.H{h}.aspected_by": D["aspected_by"][h],
              f"F.H{h}.lord": L, f"F.H{h}.lord_house": house.get(L), f"F.H{h}.notes": [c for c, _ in _house_notes(D, h)]}
    if "Mo" in P:
        m = P["Mo"]["s"]
        mh = {p: (v["s"] - m) % 12 + 1 for p, v in P.items()}
        for h in range(1, 13):
            L = SIGN_LORD[(m + h - 1) % 12]
            F |= {f"F.M{h}.sign": SIGNS[(m + h - 1) % 12], f"F.M{h}.occupants": [q for q in P if mh[q] == h],
                  f"F.M{h}.lord": L, f"F.M{h}.lord_house": mh.get(L)}
    F |= {"F.moon.phase": None if el is None else "waxing" if el < 180 else "waning",
          "F.moon.elongation": None if el is None else round(el, 1),
          "F.moon.malefic_waning": None if el is None else el >= 180,
          "F.moon.malefic_72": None if el is None else min(el, 360 - el) < 72,
          "F.malefics": sorted(D["malefic"])}
    for rid, label, holds, detail, src in candidates(D) + kuja(D):
        k = f"F.yoga.{rid.replace('.', '_')}"
        F |= {f"{k}.holds": holds, f"{k}.detail": detail, f"{k}.source": src}
    chains, finals = _chains(P)
    F |= {"F.dispositor.chains": chains, "F.dispositor.finals": finals}
    return {"schema": SCHEMA_ID, "conventions": CONVENTIONS, "facts": F}


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
    ch3 = {"asc": {"sign": "Cancer"}, "planets": {"Sa": {"sign": "Aquarius"}, "Mo": {"sign": "Gemini"}}}
    t3 = facts(ch3)   # whole-sign houses from a non-Aries lagna: Aquarius is the 8th from Cancer, Gemini the 12th
    assert "H8 Aquarius: occ Sa" in t3 and "H12 Gemini: occ Mo" in t3, t3
    if not lk:
        assert "# Lal Kitab: not part of this edition" in t2, t2
    # dignity detail: MT boundaries, compound relation, D9 dignity; Moon block from a non-Aries Moon
    ch4 = {"asc": {"sign": "Aries"}, "planets": {"Su": {"sign": "Leo", "deg": 20.0}, "Ma": {"sign": "Aries", "deg": 12.5},
                                                  "Ju": {"sign": "Gemini", "deg": 1.0}, "Me": {"sign": "Sagittarius", "deg": 5.0},
                                                  "Mo": {"sign": "Cancer", "deg": 5.0}}}
    t4 = facts(ch4)
    assert "- Sun: MOOLATRIKONA" in t4 and "- Mars: MT sign, outside the MT degrees (0–12°)" in t4, t4
    # Jupiter in Gemini: dispositor Mercury is a natural enemy and 7th from Jupiter (temporary enemy) -> great enemy
    assert "- Jupiter: towards dispositor Mercury: great enemy" in t4, t4
    # Mercury in Sagittarius: dispositor Jupiter natural neutral, 7th away (temporary enemy) -> enemy; 5° -> D9 Taurus
    assert "- Mercury: towards dispositor Jupiter: enemy; D9 Taurus" in t4, t4
    assert "- Sun: MOOLATRIKONA; D9 Libra DEBILITATED" in t4 and "Mars: MT sign, outside the MT degrees (0–12°); D9 Cancer DEBILITATED" in t4
    ch6 = {"asc": {"sign": "Aries"}, "planets": {"Mo": {"sign": "Taurus", "deg": 3.0}, "Ma": {"sign": "Scorpio", "deg": 5.0},
                                                  "Ve": {"sign": "Libra", "deg": 15.01}, "Su": {"sign": "Leo", "deg": 0.0}}}
    t6 = facts(ch6)   # MT boundaries are inclusive (Moon 3°, Sun 0°) and end at the stated degree (Venus 15.01° is outside)
    assert "- Moon: MOOLATRIKONA" in t6 and "- Sun: MOOLATRIKONA" in t6 and "Venus: MT sign, outside the MT degrees (0–15°)" in t6, t6
    # Venus in Libra is the 6th from the Moon's Taurus (temporary enemy) and a natural neutral to the Moon -> enemy
    assert "- Moon: MOOLATRIKONA; towards dispositor Venus: enemy" in t6, t6
    ch7 = {"asc": {"sign": "Aries"}, "planets": {"Ma": {"sign": "Virgo"}, "Me": {"sign": "Libra"}}}
    # compound neutral: Mercury is Mars's natural enemy (-1) but Libra is the 2nd from Virgo (temporary friend, +1) -> neutral
    assert "- Mars: towards dispositor Mercury: neutral" in facts(ch7), facts(ch7)
    ch5 = {"asc": {"sign": "Aries"}, "planets": {"Ju": {"sign": "Taurus", "deg": 1.0}}}   # fixed sign: D9 from the 9th
    assert "- Jupiter: D9 Capricorn DEBILITATED" in facts(ch5), facts(ch5)   # no relation line: Venus not supplied
    assert "# From the Moon (Chandra lagna Cancer)" in t4 and "- M2 Leo: occ Su | lord Sun in M2" in t4, t4
    assert "- M1 Cancer: occ Mo | lord Moon in M1" in t4 and "- M12 Gemini: occ Ju" in t4, t4
    def rows(asc, **pl):   # {id: (holds, detail)} for a synthetic chart: pl = planet -> (sign, deg) or sign
        ch = {"asc": {"sign": asc}, "planets": {p: ({"sign": v[0], "deg": v[1]} if isinstance(v, tuple) else {"sign": v})
                                                for p, v in pl.items()}}
        D = derive(ch)
        return {r[0]: (r[2], r[3]) for r in candidates(D) + kuja(D)}
    g = rows("Aries", Su=("Leo", 15), Mo=("Cancer", 10), Ju=("Cancer", 5), Ve=("Cancer", 8))
    assert g["GK-BPHS36"][0] is True and g["KESARI-LOOSE"][0] is True, g        # exalted Jupiter H4 with Venus
    assert g["RAJA-KK-JuMo"][0] is True                                         # 4th and 9th lords conjunct
    g = rows("Aries", Su=("Leo", 15), Mo=("Cancer", 10), Ju=("Capricorn", 5), Ve=("Capricorn", 8))
    assert g["GK-BPHS36"][0] is False and g["KESARI-LOOSE"][0] is True, g       # debilitated: strict fails, loose holds
    g = rows("Aries", Mo="Cancer", Ju="Cancer", Ve="Cancer", Su="Leo")          # no degrees: combustion unknown
    assert g["GK-BPHS36"][0] is None and "unknown" in g["GK-BPHS36"][1], g
    g = rows("Aries", Mo="Leo", Ma="Taurus", Me="Sagittarius", Ju="Aquarius", Ve="Taurus", Sa="Sagittarius")
    assert g["KEM-BARE"][0] is True and g["KEM-BPHS"][0] is True, g             # nothing flanks or cancels
    g = rows("Aries", Mo="Leo", Ma="Taurus", Me="Sagittarius", Ju="Capricorn", Ve="Taurus", Sa="Sagittarius")
    assert g["KEM-BARE"][0] is True and g["KEM-BPHS"][0] is False and "Ju" in g["KEM-BPHS"][1], g   # Jupiter H10 kendra
    assert rows("Aries", Mo="Leo", Me="Virgo")["KEM-BARE"][0] is False          # Mercury 2nd from the Moon
    g = rows("Gemini", Sa="Libra", Ma="Capricorn")                              # Saturn exalted H5, Mars exalted H8
    assert g["PMP-Sa-BPHS"][0] is False and g["PMP-Sa-LOL"][0] is True and g["PMP-Ma-BPHS"][0] is False, g
    g = rows("Aries", Ma="Leo", Su="Leo")                                       # Mars (1st/8th lord) with the 5th lord
    assert g["RAJA-KK-MaSu"][0] is True and "DISPUTED" in g["RAJA-KK-MaSu"][1], g
    g = rows("Aries", Ma="Libra", Ju="Taurus")                                  # Mars H7; Jupiter in Taurus aspects 6,8,10
    assert g["KUJA-BPHS80"][0] is True and g["KUJA-PD11.3"][0] is True and g["KUJA-POPULAR"][0] is True, g
    g = rows("Aries", Ma="Libra", Ju="Aquarius")                                # Jupiter's 9th aspect reaches Libra
    assert g["KUJA-BPHS80"][0] is False and "cancelled by Ju" in g["KUJA-BPHS80"][1], g
    assert rows("Aries", Ma="Leo")["KUJA-POPULAR"][0] is False                  # 5th from the lagna (no Moon/Venus given)
    assert family("PMP-Ve-BPHS") == "PMP-BPHS" and family("RAJA-KK-MaMe") == "RAJA-KK" and family("KEM-BARE") == "KEM-BARE"
    assert not re.search(r"(?i)\b(fame|king|wealth|rich|guarantee)", facts(
        {"asc": {"sign": "Aries"}, "planets": {"Mo": {"sign": "Cancer"}, "Ju": {"sign": "Cancer"}, "Ma": {"sign": "Libra"}}}))
    # BPHS 34.11-12: lords joined only in a kendra/kona count; mutual aspect means opposition (no special aspects)
    assert not any(k.startswith("RAJA-KK-") for k in rows("Aries", Mo="Virgo", Ju="Virgo"))       # joined in H6
    assert not any(k.startswith("RAJA-KK-") for k in rows("Aries", Ju="Aries", Sa="Leo"))         # Ju 5th aspect only
    assert rows("Aries", Ju="Aries", Sa="Libra")["RAJA-KK-JuSa"][1].startswith("mutual opposition")
    assert rows("Aries", Ju="Cancer")["RAJA-KKP-Ju"][0] is True                                   # 9th lord in H4
    d = rows("Taurus", Me="Leo", Sa="Leo")["RAJA-KK-MeSa"][1]                                     # Me owns 2/5; Sa 9/10
    assert "DISPUTED" not in d, d                                                                 # neither owns 6/8/12
    d = rows("Aries", Ju="Cancer", Mo="Cancer")["RAJA-KK-JuMo"][1]                                # Ju owns 9/12; Mo 4
    assert "Jupiter also owns H12 (moolatrikona in the good house" in d and "Moon also" not in d, d   # luminary exempt
    assert rows("Aries", Mo="Leo", Ma="Taurus", Me="Sagittarius", Ju="Aquarius", Ve="Taurus",
                Sa="Sagittarius")["KEM-BPHS"][0] is True
    assert rows("Aries", Mo="Cancer", Me="Gemini")["KEM-BARE"][0] is False
    assert rows("Aries", Mo="Cancer", Ma="Taurus")["KEM-BPHS"][0] is False                        # Moon in kendra H4
    k = rows("Aries", Ma="Cancer", Mo="Cancer")["KUJA-POPULAR"][1]
    assert "Moon with Mars cancels" in k and rows("Aries", Ma="Capricorn")["KUJA-POPULAR"][0] is False   # H10
    assert "own/exalted" in rows("Aries", Ma="Aries")["KUJA-POPULAR"][1]
    pd = lambda deg: candidates_kuja({"asc": {"sign": "Libra", "deg": deg}, "planets": {"Ma": {"sign": "Gemini"}}})
    assert pd(2.0) is True and pd(5.0) is False and pd(None) is None    # 7th Aries: navamsa Aries (Ma) / Taurus / unknown
    j = facts_json(ch4)   # the ids agree with the text
    f = j["facts"]
    assert j["schema"] == "derived_facts/1" and f["F.Su.moolatrikona"] is True and f["F.Ma.moolatrikona"] is False, f
    assert f["F.Ju.compound_to_dispositor"] == "great enemy" and f["F.Su.d9_dignity"] == "DEBILITATED", f
    assert f["F.Ma.combust"] is False and facts_json(ch2)["facts"]["F.Ju.combust"] is None and facts_json(ch2)["facts"]["F.Ju.d9"] is None
    assert f["F.moon.malefic_waning"] is not None and f["F.M2.occupants"] == ["Su"] and f["F.H7.lord"] == "Ve"
    assert all(re.fullmatch(r"F\.[A-Za-z0-9_]+(\.[A-Za-z0-9_\-]+)*", k) for k in f), [k for k in f if not re.fullmatch(r"F\.[A-Za-z0-9_]+(\.[A-Za-z0-9_\-]+)*", k)]
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    elif sys.argv[1:] in (["-h"], ["--help"]):
        print(__doc__.strip())
    elif len(sys.argv) == 2:
        print(facts(json.load(open(sys.argv[1]))))
    elif len(sys.argv) == 3 and sys.argv[1] == "--json":
        print(json.dumps(facts_json(json.load(open(sys.argv[2]))), indent=1, ensure_ascii=False))
    else:
        sys.exit(__doc__)
