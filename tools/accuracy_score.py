#!/usr/bin/env python3
"""Score the local engine against the frozen accuracy reference set (docs/ACCURACY-RUBRIC.md §4.3, §4.4).

Reads docs/accuracy/A1.json..A10.json and different-school.json, runs the engine for every case, compares atom by atom,
and writes <out>.json and <out>.md: total T / K, per area and per grade, every failing case with its lost points (they
sum to K - T), the different-school table, and the boundary / misprint / defect / convention / private rows.

usage: python tools/accuracy_score.py [--cases DIR] [--out PREFIX] [--allow-partial]
Deterministic: cases sorted by id, no sampling, no network; two runs differ only in the run-time line.
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import importlib.metadata as md
import json
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "tools")]

GRADE_W = {"G1": 4, "G2": 3, "G3": 2, "G4": 1}                                   # rubric §5.1 (frozen)
AREA_W = {"A1": 20, "A2": 15, "A3": 14, "A4": 4, "A5": 5, "A6": 9, "A7": 7, "A8": 8, "A9": 6, "A10": 12}   # §5.2
MIN_COUNT = 5                                                                   # §4.3 step 2
AREA_NAMES = {"A1": "Positions, ayanamsa, houses", "A2": "Vargas, nakshatra, pada", "A3": "Vimshottari",
              "A4": "Yogini", "A5": "Chara", "A6": "Panchang and sunrise", "A7": "Tajika", "A8": "Shadbala",
              "A9": "Ashtakavarga", "A10": "Edge cases"}
EXCLUDED = ("misprint", "reference defect", "convention without source", "private")
EPHE_SHA = {"sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
            "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7"}
FACTOR = {"arcsec": 3600.0, "arcmin": 60.0}          # expected values are degrees; tolerances in these units
SIGN2 = "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi".split()


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------------------- formula
def aggregate(rows):
    """rows: [{'id','area','grade','outcome'}] (outcome 'pass'/'fail' count; anything else is listed only).
    Returns the rubric §4.3 numbers; lost points of each failing case in 'lost'."""
    cells = {}
    for r in rows:
        if r["outcome"] in ("pass", "fail"):
            c = cells.setdefault((r["area"], r["grade"]), [0, 0])
            c[0] += 1
            c[1] += r["outcome"] == "pass"
    areas, T, K, lost = {}, 0.0, 0.0, {}
    for a in sorted({a for a, _ in cells}, key=lambda x: int(x[1:])):
        w = {g: GRADE_W[g] * min(n, MIN_COUNT) / MIN_COUNT for (aa, g), (n, _) in cells.items() if aa == a}
        rate = {g: cells[(a, g)][1] / cells[(a, g)][0] for g in w}
        S = sum(w[g] * rate[g] for g in w) / sum(w.values())
        areas[a] = {"weight": AREA_W[a], "score": S, "points": AREA_W[a] * S,
                    "grades": {g: {"n": cells[(a, g)][0], "passed": cells[(a, g)][1], "rate": rate[g],
                                   "effective_weight": w[g]} for g in sorted(w)}}
        T += AREA_W[a] * S
        K += AREA_W[a]
    for r in rows:
        if r["outcome"] == "fail":
            a, g = r["area"], r["grade"]
            ag = areas[a]["grades"]
            lost[r["id"]] = AREA_W[a] * (ag[g]["effective_weight"] / sum(x["effective_weight"] for x in ag.values())) \
                / ag[g]["n"]
    per_grade = {}
    for g in GRADE_W:
        present = [a for a in areas if g in areas[a]["grades"]]
        if present:
            per_grade[g] = sum(AREA_W[a] * areas[a]["grades"][g]["rate"] for a in present) / sum(AREA_W[a] for a in present)
    assert abs(sum(lost.values()) - (K - T)) < 1e-9, (sum(lost.values()), K - T)
    return {"T": T, "K": K, "areas": areas, "per_grade": per_grade, "lost": lost}


# --------------------------------------------------------------------------------------------------- comparisons
def _instant(v):
    return dt.datetime.fromisoformat(str(v).replace(" ", "T").rstrip("Z"))


def compare(kind, got, exp, tol, unit):
    """(ok, difference shown in the report)."""
    if got is None:
        return False, "missing"
    if kind == "exact":
        return got == exp, None if got == exp else f"got {got!r}"
    if kind in ("abs_diff", "circular_diff"):
        d = float(got) - float(exp)
        if kind == "circular_diff":
            d = (d + 180) % 360 - 180
        d *= FACTOR.get(unit, 1.0)
        return abs(d) <= tol + 1e-9, round(d, 6)          # 1e-9: a value exactly at the tolerance passes
    if kind in ("instant_diff", "local_diff"):
        d = (_instant(got) - _instant(exp)).total_seconds()
        return abs(d) <= tol + 1e-9, round(d, 3)
    if kind in ("date_exact", "date_diff"):
        d = (dt.date.fromisoformat(str(got)[:10]) - dt.date.fromisoformat(str(exp)[:10])).days
        return abs(d) <= (tol or 0), d
    raise ValueError(kind)


# ------------------------------------------------------------------------------------------------------ engine side
class Engine:
    """Runs the local engine for case inputs; one instance per scoring run (results cached per chart)."""

    def __init__(self):
        import accuracy_charts as AC
        from astro import service as S
        from astro.calc import chara, engine, panchang, strength, tajika
        self.AC, self.S, self.E, self.P, self.ST, self.TJ, self.CH = AC, S, engine, panchang, strength, tajika, chara

    def birth(self, cid):
        c = self.AC.chart(cid)
        return c, dt.datetime.fromisoformat(f"{c['date']}T{c['time']}") - dt.timedelta(hours=c["tz"])

    @functools.lru_cache(maxsize=None)
    def chart(self, cid, node="mean", mode="lahiri"):
        c, _ = self.birth(cid)
        with self.E.using(mode):
            return self.E.compute(c["date"], c["time"], c["tz"], c["lat"], c["lon"], node=node, on="2000-01-01",
                                  extras=False)

    def jd(self, cid):
        return self.E.jd_of(self.birth(cid)[1])

    @functools.lru_cache(maxsize=None)
    def shadbala(self, cid, mode="lahiri"):
        c, ut = self.birth(cid)
        with self.E.using(mode):
            return self.ST.shadbala(self.chart(cid, "mean", mode), ut, c["lat"], c["lon"], c["tz"])

    @functools.lru_cache(maxsize=None)
    def tajika(self, cid, year):
        c = self.AC.chart(cid)
        b = self.S.BirthInput(date=c["date"], time=c["time"], tz=c["tz"], lat=c["lat"], lon=c["lon"])
        return self.S.tajika(b, year)

    def iso(self, jd):
        return (dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=jd - 2451545.0)).isoformat(timespec="milliseconds")

    def pos(self, text):
        sign, d = text.split()
        return self.E.SIGNS.index(sign) * 30 + float(d)

    # every quantity returns {atom key: engine value}
    def q_ayanamsa(self, case):
        m = self.chart(case["input"]["chart"])["meta"]
        return {"mean": m["ayanamsa_deg_mean"], "true": m["ayanamsa_deg_true"]}

    def q_ayanamsa_epochs(self, case):
        out = {}
        for cid in case["input"]["charts"]:
            m = self.chart(cid, "mean", case["input"]["ayanamsa"])["meta"]
            out |= {f"{cid}.mean": m["ayanamsa_deg_mean"], f"{cid}.true": m["ayanamsa_deg_true"]}
        return out

    def q_longitude(self, case):
        b = self.chart(case["input"]["chart"], case["input"].get("node", "mean"))["bodies"]
        return {k: v["lon"] for k, v in b.items()}

    def q_motion(self, case):
        b = self.chart(case["input"]["chart"])["bodies"]
        return {f"{k}.{f}": v[f] for k, v in b.items() if k != "Asc" for f in ("speed", "retro")}

    def q_angles(self, case):
        c = self.chart(case["input"]["chart"])
        return {"Asc": c["bodies"]["Asc"]["lon"], "MC": c["mc"]}

    def q_bhava_middles(self, case):
        return {f"H{h['house']}": h["middle"] for h in self.chart(case["input"]["chart"])["bhavas"]}

    def q_bhava_sandhis(self, case):
        return {f"H{h['house']}.end": h["end"] for h in self.chart(case["input"]["chart"])["bhavas"]}

    def q_sign_nak_pada(self, case):
        out = {}
        for k, v in self.chart(case["input"]["chart"])["bodies"].items():
            out |= {f"{k}.sign": self.E.SIGNS.index(v["sign"]), f"{k}.nak": self.E.NAKS.index(v["nakshatra"]),
                    f"{k}.pada": v["pada"]}
        return out

    def q_vargas(self, case):
        return {f"{k}.{d}": self.E.SIGNS.index(s) for k, v in self.chart(case["input"]["chart"])["bodies"].items()
                for d, s in v["vargas"].items()}

    def _dasha_args(self, case):
        cid = case["input"]["chart"]
        return self.E.positions(self.jd(cid))["Mo"]["lon"], self.birth(cid)[1], case["input"]["year_days"]

    def q_vimshottari_md(self, case):
        v = self.E.vimshottari(*self._dasha_args(case), levels=1)
        return {m["lord"]: m["start"].isoformat(timespec="milliseconds") for m in v}

    def q_vimshottari_ad(self, case):
        v = self.E.vimshottari(*self._dasha_args(case), levels=2)
        return {f"{m['lord']}-{a['lord']}": a["start"].isoformat(timespec="milliseconds") for m in v for a in m["sub"]}

    def q_yogini_md(self, case):
        rows = self.E.yogini(*self._dasha_args(case), span_years=150)
        first = case["expected"][0]
        lord0, t0 = first["key"].split(":")[1], _instant(first["value"])
        k = next(i for i, r in enumerate(rows) if r["lord"] == lord0 and abs((r["start"] - t0).days) < 5)
        return {f"{i}:{r['lord']}": r["start"].isoformat(timespec="milliseconds") for i, r in enumerate(rows[k:])}

    def q_vimshottari_balance(self, case):
        b, ylen = dt.datetime(2000, 1, 1), self.E.YEAR["sidereal"]
        md0 = self.E.vimshottari(case["input"]["moon_lon_deg"], b, ylen, levels=1)[0]
        days = (md0["end"] - b).total_seconds() / 86400
        return {"lord": md0["lord"], "balance_table_days": days * 365.25 / ylen, "balance_years": days / ylen}

    def q_chara_years(self, case):
        return self.CH.sign_years(case["input"]["signs"])

    def q_chara_sequence(self, case):
        return {str(i): s for i, (s, _) in enumerate(self.CH.dasha(case["input"]["signs"]))}

    def q_chara_antardashas(self, case):
        return {str(i): s for i, s in enumerate(self.CH.antardashas(case["input"]["sign"]))}

    def _sun(self, cid):
        c, _ = self.birth(cid)
        return self.ST._sun_events(self.jd(cid), c["lat"], c["lon"])

    def q_sun_events(self, case):
        r1, s, r2, _ = self._sun(case["input"]["chart"])
        return {"sunrise": self.iso(r1), "sunset": self.iso(s), "next_sunrise": self.iso(r2)}

    def _elements(self, jd):
        return {k: self.P._index(k, jd) + 1 for k in ("tithi", "nakshatra", "yoga", "karana")}

    def q_panchang_birth(self, case):
        cid = case["input"]["chart"]
        return self._elements(self.jd(cid)) | {"vara": self.shadbala(cid)["time_lords"]["weekday"]}

    def q_panchang_sunrise(self, case):
        return self._elements(self._sun(case["input"]["chart"])[0])

    def q_element_changes(self, case):
        jd = self.jd(case["input"]["chart"])
        return {k: self.iso(self.P._end(k, jd)) for k in ("tithi", "nakshatra", "yoga", "karana")}

    def q_element_end_after(self, case):
        i, at = case["input"], _instant(case["expected"][0]["value"])
        return {i["kind"]: self.iso(self.P._end(i["kind"], self.E.jd_of(at) - i["search_from_days_before"]))}

    def q_hora(self, case):
        return {"hora": self.shadbala(case["input"]["chart"])["time_lords"]["hora"]}

    def q_varsha_pravesh(self, case):
        cid = case["input"]["chart"]
        bj = self.jd(cid)
        return {"return": self.iso(self.TJ.varsha_pravesh(bj, self.E.positions(bj)["Su"]["lon"],
                                                          case["input"]["completed"]))}

    def _tj(self, case):
        return self.tajika(case["input"]["chart"], case["input"]["year"])

    def q_tajika_return(self, case):
        return {"local": self._tj(case)["varsha_pravesh"]}

    def q_tajika_frame(self, case):
        r = self._tj(case)
        return {"lagna_sign": r["annual_lagna"].split()[0], "day_or_night": r["day_or_night"], "muntha": r["muntha"]}

    def q_tajika_positions(self, case):
        r = self._tj(case)
        return {"Asc": self.pos(r["annual_lagna"])} | {p: self.pos(v) for p, v in r["positions"].items()}

    def q_tajika_harsha(self, case):
        return self._tj(case)["harsha_bala"]

    def q_tajika_year_lord(self, case):
        r = self._tj(case)
        return {f"candidate{i + 1}": c["planet"] for i, c in enumerate(r["year_lord_candidates"])} | \
            {"year_lord": r["year_lord"]}

    def q_tajika_pvb(self, case):
        planets = self._tj(case)["pancha_vargeeya_bala"]["planets"]
        return {p: next(g["pvb"] for g in gs if self.TJ.PVB_DEFAULT in g["variants"]) for p, gs in planets.items()}

    def q_tajika_sahams(self, case):
        return {k: self.pos(v) for k, v in self._tj(case)["sahams"].items()}

    def q_tajika_mudda_lords(self, case):
        return {str(i): r["lord"] for i, r in enumerate(self._tj(case)["mudda_dasha"])}

    def q_tajika_mudda_end(self, case):
        return {f"{r['lord']}.end": r["end"][:10] for r in self._tj(case)["mudda_dasha"][:1]}

    def q_tajika_patyayini_order(self, case):
        return {str(i): r["lord"] for i, r in enumerate(self._tj(case)["patyayini_dasha"])}

    def q_tajika_patyayini_me(self, case):
        me = next(r for r in self._tj(case)["patyayini_dasha"] if r["lord"] == "Me")
        return {"Me.start": me["start"][:10], "Me.end": me["end"][:10]}

    def q_uchcha_bala(self, case):
        cid = case["input"]["chart"]
        c0, ut = self.birth(cid)
        c = json.loads(json.dumps(self.chart(cid)))
        for p, lon in case["input"]["override"].items():
            c["bodies"][p]["lon"] = lon
        res = self.ST.shadbala(c, ut, c0["lat"], c0["lon"], c0["tz"])["planets"]
        return {p: res[p]["detail"]["uchcha"] for p in case["input"]["override"]}

    def q_naisargika(self, case):
        return {p: v["virupas"]["naisargika"] for p, v in self.shadbala(case["input"]["chart"])["planets"].items()}

    def q_required_rupas(self, case):
        return {p: v["required_rupas"] * 60 for p, v in self.shadbala(case["input"]["chart"])["planets"].items()}

    def q_time_lords_date(self, case):
        b = self.S.BirthInput(date=case["input"]["date"], time="12:00", tz=5.5, lat=23.18, lon=75.78)   # Ujjain noon
        return self.S.shadbala(b)["time_lords"]

    def q_drik_bala(self, case):
        p = self.shadbala(case["input"]["chart"], case["input"]["ayanamsa"])["planets"]
        return {k: v["virupas"]["drik"] for k, v in p.items()}

    def q_war_winner(self, case):
        lat = case["input"]["latitudes"]
        return {a["key"]: self.ST.war_winner(*a["key"].split("-"), lat) for a in case["expected"]}

    def q_bav(self, case):
        i = case["input"]
        c = {"bodies": {p: {"lon": SIGN2.index(v) * 30 + 15} for p, v in i["signs"].items()}} if "signs" in i \
            else self.chart(i["chart"])
        av = self.ST.ashtakavarga(c)
        return {f"{p}.{SIGN2[k]}": v for p, row in av["bav"].items() for k, v in enumerate(row)} | \
            {f"SAV.{SIGN2[k]}": v for k, v in enumerate(av["sav"])}

    def q_polar_flag(self, case):
        return {"polar": self._sun(case["input"]["chart"])[3]}

    def q_vara(self, case):
        return {"vara": self.shadbala(case["input"]["chart"])["time_lords"]["weekday"]}

    def q_tz_offset(self, case):
        i = case["input"]
        t = dt.datetime.fromisoformat(i["local"])
        try:
            return {"offset": self.S.resolve_zone(t.date(), t.strftime("%H:%M"), i["zone"], 0.0, i["fold"])[0]}
        except ValueError as e:
            m = str(e)
            return {"offset": "gap" if "does not exist" in m else "fold required" if "occurs twice" in m else m}


# ------------------------------------------------------------------------------------------------------------ run
def evaluate(engine, case):
    """-> (atoms rows, error). Atom row: key, expected, engine value, ok / boundary, difference."""
    if case["quantity"] in ("none", "stored_note", "private_test"):
        return [], None
    try:
        got = getattr(engine, "q_" + case["quantity"])(case)
    except Exception as e:                       # an engine error is a failure of the case, never a crash of the run
        return [], f"{type(e).__name__}: {e}"
    rows = []
    for a in case["expected"]:
        kind = a.get("comparison", case["comparison"])
        tol = a.get("tolerance", case["tolerance"])
        thr = a.get("boundary_threshold", case.get("boundary_threshold"))
        ok, diff = compare(kind, got.get(a["key"]), a["value"], tol, case["unit"])
        boundary = thr is not None and a.get("boundary_margin") is not None and a["boundary_margin"] < thr
        rows.append({"key": a["key"], "expected": a["value"], "engine": got.get(a["key"]), "ok": ok,
                     "boundary": boundary, "diff": diff})
    return rows, None


def outcome(case, atoms, err):
    st = case["status_before_run"]
    if st == "different school":
        return "different school: " + ("engine error" if err else "not evaluated" if not atoms else
                                       "same" if all(a["ok"] for a in atoms) else "differs")
    if st != "scored":
        return st
    if err:
        return "fail"
    live = [a for a in atoms if not a["boundary"]]
    if not live:
        return "boundary"
    return "pass" if all(a["ok"] for a in live) else "fail"


def load(case_dir):
    files = sorted(f for f in os.listdir(case_dir) if f.endswith(".json") and (f[0] == "A" or f == "different-school.json"))
    cases, hashes = [], {}
    for f in files:
        p = os.path.join(case_dir, f)
        hashes[f] = sha(p)
        cases += json.load(open(p, encoding="utf-8"))["cases"]
    return sorted(cases, key=lambda c: (c["area"] == "informational", c["id"])), hashes


def check_ephemeris(engine):
    d = engine.E.EPHE_DIR
    if not d:
        sys.exit("Swiss Ephemeris files not found (Moshier would move positions by up to 2.65 arcsec): no score")
    for f, want in EPHE_SHA.items():
        if sha(os.path.join(d, f)) != want:
            sys.exit(f"{f} differs from the pinned SHA-256: no score")
    return {f: EPHE_SHA[f] for f in EPHE_SHA} | {"dir": os.path.relpath(d, ROOT)}


def provenance(engine, hashes, cases, ephe):
    git = subprocess.run(["git", "-C", os.path.join(os.path.dirname(ROOT), "astrology-consultation"), "rev-parse",
                          "HEAD"], capture_output=True, text=True).stdout.strip() or "unknown"
    runs = set()
    for c in cases:
        for src in (c["source"], c["source"].get("value_source")):
            if isinstance(src, dict) and src.get("run"):
                runs.add(f"{src.get('engine', '')} {src.get('version', '')}: {src['run']}".strip())
    runs = sorted(runs)
    rub = os.path.join(ROOT, "docs", "ACCURACY-RUBRIC.md")
    return {"rubric": "docs/ACCURACY-RUBRIC.md", "rubric_sha256": sha(rub), "case_files_sha256": hashes,
            "scorer_sha256": sha(os.path.abspath(__file__)), "engine": f"astro {engine.E.ENGINE_VERSION}",
            "engine_code": "workspace [workspace] (not a git work tree); private clone HEAD " + git,
            "python": platform.python_version(), "pyswisseph": md.version("pyswisseph"),
            "swiss_ephemeris": engine.E.swe.version, "ephemeris_files_sha256": ephe,
            "tzdb": engine.S.tzdb_version(), "stored_reference_runs": runs}


def fmt(x):
    return f"{x:.2f}"


def report_md(res):
    s, L = res["score"], []
    L += ["# Calculation accuracy: scored run", "", f"Run (UTC): {res['run_utc']}", "",
          f"**Total: {fmt(s['T'])} / {fmt(s['K'])}** (K = coverage; the rubric requires K = 100)", "",
          f"Without the private G2 fixtures: {fmt(s['T'])} / {fmt(s['K'])}. With them: {res['private_total']}.", "",
          "## Per area", "", "| Area | Weight | Cases scored (pass/n by grade) | Area score | Points |", "|---|---|---|---|---|"]
    for a, v in s["areas"].items():
        g = ", ".join(f"{k} {x['passed']}/{x['n']}" for k, x in v["grades"].items())
        L.append(f"| {a} {AREA_NAMES[a]} | {v['weight']} | {g} | {fmt(100 * v['score'])}% | {fmt(v['points'])} |")
    L += ["", "## Per grade (reported, not part of T)", "", "| Grade | Weight | Score |", "|---|---|---|"]
    L += [f"| {g} | {GRADE_W[g]} | {fmt(100 * v)}% |" for g, v in s["per_grade"].items()]
    fails = [r for r in res["cases"] if r["outcome"] == "fail"]
    L += ["", f"## Failing cases ({len(fails)}; lost points sum {fmt(sum(s['lost'].values()))} = K - T "
          f"{fmt(s['K'] - s['T'])})", "", "| Case | Area | Grade | Quantity | Lost | Failing atoms |", "|---|---|---|---|---|---|"]
    for r in fails:
        bad = [a for a in r["atoms"] if not a["ok"] and not a["boundary"]]
        atoms = r["error"] or "; ".join(f"{a['key']}: expected {a['expected']}, engine {a['engine']}"
                                        + (f" (diff {a['diff']})" if a["diff"] is not None else "") for a in bad[:6])
        if len(bad) > 6:
            atoms += f"; ... {len(bad) - 6} more"
        L.append(f"| {r['id']} | {r['area']} | {r['grade']} | {r['quantity']} | {fmt(s['lost'][r['id']])} | {atoms} |")
    ds = [r for r in res["cases"] if r["outcome"].startswith("different school")]
    L += ["", f"## Different school (informational, never scored: {len(ds)})", "", "| Row | Quantity | Result |", "|---|---|---|"]
    for r in ds:
        detail = r["outcome"].split(": ", 1)[1]
        if detail == "differs":
            detail += ": " + "; ".join(f"{a['key']} school {a['expected']} / engine {a['engine']}"
                                       for a in r["atoms"] if not a["ok"])[:300]
        elif detail == "not evaluated":
            detail = "; ".join(f"{a['key']}: {a['value']}" for a in r["expected_stored"])
        L.append(f"| {r['id']} | {r['sub_item']} | {detail} |")
    L += ["", "## Excluded and boundary rows", "", "| Case | Status | Note |", "|---|---|---|"]
    for r in res["cases"]:
        if r["outcome"] in EXCLUDED or r["outcome"] == "boundary":
            L.append(f"| {r['id']} | {r['outcome']} | {r['note']} |")
    nb = sum(a["boundary"] for r in res["cases"] if r["outcome"] in ("pass", "fail") for a in r["atoms"])
    L += ["", f"Boundary atoms removed inside scored cases (rubric 6.2): {nb}.", "", "## Provenance", ""]
    L += [f"- {k}: {json.dumps(v, sort_keys=True)}" for k, v in res["provenance"].items()]
    return "\n".join(L) + "\n"


def check_keys(case_dir):
    """Plumbing check before the frozen run: every extractor runs and returns every key its cases name. Values are
    never compared or printed, so this is not a scoring run."""
    engine, problems = Engine(), []
    check_ephemeris(engine)
    for c in load(case_dir)[0]:
        if c["quantity"] in ("none", "stored_note", "private_test"):
            continue
        try:
            got = getattr(engine, "q_" + c["quantity"])(c)
        except Exception as e:
            problems.append(f"{c['id']}: {type(e).__name__}: {e}")
            continue
        missing = [a["key"] for a in c["expected"] if a["key"] not in got]
        if missing:
            problems.append(f"{c['id']}: missing keys {missing[:5]}")
    return problems


def run(case_dir, out, allow_partial=False):
    engine = Engine()
    ephe = check_ephemeris(engine)
    cases, hashes = load(case_dir)
    rows = []
    for c in cases:
        atoms, err = evaluate(engine, c)
        o = outcome(c, atoms, err)
        note = c["notes"]
        if o == "boundary" or (o in EXCLUDED and atoms):
            note = (note + " | engine: " + "; ".join(f"{a['key']}={a['engine']}" for a in atoms))[:400]
        rows.append({"id": c["id"], "area": c["area"], "grade": c["grade"], "quantity": c["quantity"],
                     "sub_item": c["sub_item"], "outcome": o, "atoms": atoms, "error": err, "note": note,
                     "expected_stored": c["expected"] if c["quantity"] == "stored_note" else []})
    score = aggregate(rows)
    if score["K"] != 100 and not allow_partial:
        sys.exit(f"coverage K = {score['K']} (areas {sorted(score['areas'])}): rubric Q9 forbids a run below 100")
    # shortcut: the private G2 fixtures are scored only in the owner's private run (rubric Q5); this run never reads them
    private_total = "not computed in this run (private fixtures not read; owner's private run)"
    res = {"run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "score": score,
           "private_total": private_total, "cases": rows, "provenance": provenance(engine, hashes, cases, ephe)}
    js = json.dumps(res, indent=1, sort_keys=True, default=str, allow_nan=False)
    open(out + ".json", "w", encoding="utf-8").write(js + "\n")
    open(out + ".md", "w", encoding="utf-8").write(report_md(res))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=os.path.join(ROOT, "docs", "accuracy"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "accuracy", f"report-{dt.date.today().isoformat()}"))
    ap.add_argument("--allow-partial", action="store_true", help="score with K < 100 (tests only; rubric Q9)")
    ap.add_argument("--check-keys", action="store_true", help="plumbing check only: no values compared or shown")
    a = ap.parse_args(argv)
    if a.check_keys:
        problems = check_keys(a.cases)
        print("\n".join(problems) or "every case's keys are produced")
        return
    res = run(a.cases, a.out, a.allow_partial)
    s = res["score"]
    print(f"T/K = {s['T']:.2f} / {s['K']:.2f}; failing cases: {sum(r['outcome'] == 'fail' for r in res['cases'])}")


if __name__ == "__main__":
    main()
