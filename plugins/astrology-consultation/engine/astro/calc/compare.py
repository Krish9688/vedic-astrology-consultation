"""Astrology-aware comparison of two normalized charts (ChartFacts A = preferred/local, B = cross-check).

A generic object diff would call 330.3149 vs 330.3147 "different"; here differences are graded by what they change
astrologically. Verdicts:
  match · within tolerance · methodology (a documented rule difference) · configuration (a setting, e.g. 360-day
  years) · implementation (a known defect in one engine) · unresolved (needs investigation) · not comparable.
usage: python -m astro.calc.compare --local OUT/calc.json [--vedastro DIR] --out OUT
"""
from __future__ import annotations

import json

from .schema import Agreement, ChartFacts, ValidatedChartFacts

POS_TOL_ARCMIN = 1.0          # longitudes within 1′ = same fact for every technique used here
ASC_TOL_ARCMIN = 3.0          # ascendant: engines differ slightly in house/obliquity handling
BHAVA_TOL_DEG = 0.5           # bhava madhyas/sandhis
DASHA_TOL_DAYS = 3            # period boundaries within 3 days = same (rounding of the birth balance)
VERDICTS = ("match", "within tolerance", "methodology", "configuration", "implementation", "unresolved",
            "not comparable")

# Shadbala components that follow the same rule in the local engine and VedAstro (expected to match), and the
# documented reasons the others differ (checked on S2 and the owner's chart, 2026-10-02).
SHADBALA_SAME_RULE = {"dig", "ojayugma", "kendradi", "drekkana", "tribhaga", "naisargika"}
SHADBALA_NOTES = {
    "saptavargaja": ("methodology", "local uses BPHS 27.2–4 points 45/30/20/15/10/4/2; VedAstro the 45/30/22.5/15/"
                     "7.5/3.75/1.875 scale"),
    "abda_masa_vara_hora": ("methodology", "year/month lords depend on the Ahargana epoch, which engines count "
                            "differently"),
    "ayana": ("methodology", "declination method and cap differ (VedAstro caps at 60; local doubles the Sun per Raman)"),
    "cheshta": ("methodology", "Sun/Moon: local uses ayana/paksha bala (Raman), VedAstro 0; others: see note on "
                "the circular mean"),
    "sthana": ("methodology", "includes saptavargaja (point scale differs)"),
    "kala": ("methodology", "includes ayana, abda/masa and paksha conventions"),
}


def _arcmin(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d) * 60


def _year_days_note(a: ChartFacts, b: ChartFacts):
    ya, yb = a.provenance.dasha_year_days, b.provenance.dasha_year_days
    return None if not ya or not yb or abs(ya - yb) < 0.01 else f"dasha year {ya} vs {yb} days"


def compare(a: ChartFacts, b: ChartFacts) -> list[Agreement]:
    out = []
    for key in a.bodies:
        if key not in b.bodies:
            continue
        x, y = a.bodies[key], b.bodies[key]
        am = _arcmin(x.lon, y.lon)
        tol = ASC_TOL_ARCMIN if key == "Asc" else POS_TOL_ARCMIN
        out.append(Agreement(kind="position", key=key, a=f"{x.lon:.4f}", b=f"{y.lon:.4f}", delta=f"{am:.2f}′",
                             verdict="match" if am < 0.05 else "within tolerance" if am <= tol else "unresolved"))
        for kind, va, vb in (("sign", x.sign, y.sign), ("nakshatra", x.nakshatra, y.nakshatra),
                             ("pada", x.pada, y.pada)):
            if va != vb:
                out.append(Agreement(kind=kind, key=key, a=str(va), b=str(vb), verdict="unresolved",
                                     note=f"longitudes {am:.2f}′ apart straddle a boundary"))
        for D, sa in x.vargas.items():
            sb = y.vargas.get(D)
            if sb is None:
                continue
            if sa == sb:
                out.append(Agreement(kind="varga", key=f"{key}:{D}", a=sa, b=sb, verdict="match"))
                continue
            method = b.provenance.varga_notes.get(D) or a.provenance.varga_notes.get(D)
            out.append(Agreement(kind="varga", key=f"{key}:{D}", a=sa, b=sb,
                                 verdict="methodology" if method else "unresolved",
                                 note=method or f"longitudes {am:.2f}′ apart"))
    out += _dashas(a, b)
    out += _bhavas(a, b)
    out += _ashtakavarga(a, b)
    out += _shadbala(a, b)
    for h, sa in a.arudha.items():
        if h in b.arudha:
            sb = b.arudha[h]
            out.append(Agreement(kind="arudha", key=h, a=sa, b=sb, verdict="match" if sa == sb else "methodology",
                                 note="" if sa == sb else ("VedAstro gives the raw count; local applies the BPHS 29.45 exception "
                                                           "(landing in the house or its 7th → 10th from there)")))
    return out


def _dashas(a, b):
    out, note = [], _year_days_note(a, b)
    if note:
        out.append(Agreement(kind="configuration", key="dasha year", a=str(a.provenance.dasha_year_days),
                             b=str(b.provenance.dasha_year_days), verdict="configuration",
                             note="boundary dates drift apart with age; the lord sequence must still match"))

    def walk(pa_list, pb_list, level, parent):
        for pa in pa_list:
            pb = next((p for p in pb_list if p.lord == pa.lord and abs((p.end - pa.end).days) < 400 * (4 - level)), None)
            if pb is None:
                continue
            name = f"{parent}{'–' if parent else ''}{pa.lord}"
            for label, da, db, clipped in (("start", pa.start, pb.start, pb.clipped), ("end", pa.end, pb.end, False)):
                if clipped and label == "start":
                    continue
                days = (da - db).days
                v = "match" if days == 0 else "within tolerance" if abs(days) <= DASHA_TOL_DAYS else \
                    "configuration" if note else "unresolved"
                out.append(Agreement(kind=["MD", "AD", "PD"][level - 1], key=f"{name} {label}", a=str(da), b=str(db),
                                     delta=f"{days:+d} d", verdict=v, note=note or ""))
            seq_a, seq_b = [s.lord for s in pa.sub], [s.lord for s in pb.sub]
            if seq_b and seq_a[-len(seq_b):] != seq_b:
                out.append(Agreement(kind="dasha", key=f"sub-period order in {name}", a=" ".join(seq_a),
                                     b=" ".join(seq_b), verdict="unresolved",
                                     note="sub-period order must be identical in every convention"))
            if level < 3:
                walk(pa.sub, pb.sub, level + 1, name)

    if a.vimshottari and b.vimshottari:
        lord = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        own = lambda f: lord[int(f.bodies["Mo"].lon // (40 / 3)) % 9]       # each engine's own Moon nakshatra lord
        fa, fb = a.vimshottari[0].lord, b.vimshottari[0].lord
        if fa != fb:
            v = "implementation" if own(b) == fa else "unresolved"
            out.append(Agreement(kind="dasha", key="mahadasha at birth", a=fa, b=fb, verdict=v,
                                 note=(f"B's own Moon nakshatra lord is {own(b)}, so its period list contradicts its "
                                       "own Moon position" if v == "implementation" else "")))
    walk(a.vimshottari, b.vimshottari, 1, "")
    return out


def _bhavas(a, b):
    out = []
    bb = {x["house"]: x for x in b.bhavas}
    for x in a.bhavas:
        y = bb.get(x["house"])
        if not y:
            continue
        for part in ("middle", "start"):
            d = _arcmin(x[part], y[part]) / 60
            out.append(Agreement(kind="bhava", key=f"H{x['house']} {part}", a=f"{x[part]:.3f}", b=f"{y[part]:.3f}",
                                 delta=f"{d:.3f}°", verdict="match" if d < 0.01 else
                                 "within tolerance" if d <= BHAVA_TOL_DEG else "methodology",
                                 note="" if d <= BHAVA_TOL_DEG else "house-division method differs"))
    return out


def _ashtakavarga(a, b):
    out = []
    for p, row in a.ashtakavarga.items():
        if p in b.ashtakavarga:
            diff = [i for i, (x, y) in enumerate(zip(row, b.ashtakavarga[p])) if x != y]
            out.append(Agreement(kind="ashtakavarga", key=f"BAV {p}", a=" ".join(map(str, row)),
                                 b=" ".join(map(str, b.ashtakavarga[p])), delta=f"{len(diff)} cells",
                                 verdict="match" if not diff else "unresolved"))
    return out


def _shadbala(a, b):
    out = []
    for p, comps in a.shadbala_components.items():
        other = b.shadbala_components.get(p, {})
        for k, va in comps.items():
            if k not in other or not isinstance(va, (int, float)):
                continue
            vb = other[k]
            d = va - vb
            if abs(d) < 0.5:
                v, note = "match", ""
            elif k == "tribhaga" and va == 60 and vb == 0 and p != "Ju":
                v, note = "implementation", ("VedAstro assigns no night-third lord to a birth between midnight and "
                                             "sunrise (owner's chart, 2026-10-02); local follows the rule")
            elif k in SHADBALA_SAME_RULE:
                v, note = "unresolved", "same rule in both engines — should match"
            else:
                v, note = SHADBALA_NOTES.get(k, ("unresolved", ""))
                if k == "cheshta" and p in ("Su", "Mo") and vb == 0:
                    note = "Sun/Moon: local uses ayana/paksha bala (Raman); VedAstro gives 0"
            out.append(Agreement(kind="shadbala", key=f"{p} {k}", a=f"{va:.2f}", b=f"{vb:.2f}", delta=f"{d:+.2f}",
                                 verdict=v, note=note))
    for p, va in a.shadbala_rupas.items():
        if p in b.shadbala_rupas:
            vb = b.shadbala_rupas[p]
            out.append(Agreement(kind="shadbala", key=f"{p} total", a=f"{va:.2f}", b=f"{vb:.2f}",
                                 delta=f"{va - vb:+.2f} rupas", verdict="methodology",
                                 note="sum of components with differing conventions; never argue from a pass/fail"))
    return out


def validate(a: ChartFacts, b: ChartFacts) -> ValidatedChartFacts:
    """A's facts, annotated with the cross-check against B. Flags every unresolved disagreement."""
    ag = compare(a, b)
    v = ValidatedChartFacts(**a.model_dump(), cross_check_engine=f"{b.provenance.engine} ({b.provenance.network})",
                            agreements=ag)
    v.flags += [f"{x.kind} {x.key}: {x.a} vs {x.b} ({x.note})" for x in v.disagreements()]
    return v


def summary(ag: list[Agreement]) -> dict:
    kinds = sorted({x.kind for x in ag})
    return {k: {v: sum(1 for x in ag if x.kind == k and x.verdict == v) for v in VERDICTS
                if any(x.kind == k and x.verdict == v for x in ag)} for k in kinds}


def table(ag: list[Agreement], show_matches=False) -> str:
    rows = [x for x in ag if show_matches or x.verdict not in ("match", "within tolerance")]
    lines = ["| Kind | Key | A | B | Δ | Verdict | Note |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {x.kind} | {x.key} | {x.a} | {x.b} | {x.delta or ''} | {x.verdict} | {x.note} |" for x in rows]
    sm = ["", "| Kind | " + " | ".join(VERDICTS) + " |", "|---|" + "---|" * len(VERDICTS)]
    for k, counts in summary(ag).items():
        sm.append(f"| {k} | " + " | ".join(str(counts.get(v, "")) for v in VERDICTS) + " |")
    return "\n".join(sm + ["", "Differences (matches and within-tolerance rows omitted):", ""] + lines)


def load_vedastro_dir(d, birth=None):
    import os

    from .adapters import from_vedastro
    rd = lambda n: json.load(open(os.path.join(d, n))) if os.path.exists(os.path.join(d, n)) else None
    return from_vedastro(rd("planet_data.json"), rd("ascendant.json"), rd("dasa_range.json"), rd("shadbala.json"),
                         birth=birth, ashtakavarga=rd("ashtakavarga.json"),
                         shadbala_components=rd("shadbala_components.json"), house_data=rd("house_data.json"))


if __name__ == "__main__":
    import argparse
    import os

    from .adapters import from_local

    ap = argparse.ArgumentParser()
    ap.add_argument("--local", required=True)
    ap.add_argument("--vedastro")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A = from_local(json.load(open(a.local)))
    if a.vedastro:
        B = load_vedastro_dir(a.vedastro, birth=A.birth)
        V = validate(A, B)
        md = (f"# Engine comparison\n\nA = {A.provenance.engine} ({A.provenance.network}, {A.provenance.ephemeris}); "
              f"B = {V.cross_check_engine}\n" + table(V.agreements))
    else:
        V, md = ValidatedChartFacts(**A.model_dump()), "# Engine comparison\n\nNo second engine supplied.\n"
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, "facts.json"), "w").write(V.model_dump_json(indent=1))
    open(os.path.join(a.out, "comparison.md"), "w").write(md + "\n")
    print(f"wrote {a.out}/facts.json, comparison.md ({len(V.disagreements())} unresolved)")
