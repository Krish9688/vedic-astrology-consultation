#!/usr/bin/env python3
"""Lal Kitab Varshaphal (annual chart) lookup from the validated v2.2 table. Read-only; never edits the CSV.

usage:
  varshaphal.py --natal "Su=1,Mo=12,Ma=3,Me=2,Ju=11,Ve=2,Sa=8,Ra=11,Ke=5" --age 34
  varshaphal.py --natal "..." --dob 1990-05-14 --on 2026-09-23          # shows BOTH age conventions
  varshaphal.py --natal "..." --dob 1990-05-14 --on 2026-09-23 --convention running
  varshaphal.py --selftest

--natal: each planet's NATAL Lal Kitab house (1-12, counted from the birth lagna; signs are dropped).
Age-year N: 'running' = completed years + 1 (year 1 = birth to 1st birthday); 'completed' = completed years.
Neither examined book fixes the convention (KB B17, audit §10), so without --convention both are shown.
Output uses RECOMMENDED_house_k only. Years 67/99/104 also print the competing 1952 reading; year 17 is a majority row.
"""
import argparse, csv, datetime, os, sys

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "lal-kitab", "LalKitab_Varshaphal_Table_v2.2.csv")
PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
CONFLICT_YEARS = {67, 99, 104}


def load():
    rows = {}
    with open(CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n = int(r["age_year"])
            rec = [int(r[f"RECOMMENDED_house_{k}"]) for k in range(1, 13)]
            assert sorted(rec) == list(range(1, 13)), f"row {n} is not a permutation"
            alt = None
            if n in CONFLICT_YEARS:
                alt = [int(r[f"lk1952_house_{k}"]) for k in range(1, 13)]
                assert sorted(alt) == list(range(1, 13)), f"1952 row {n} is not a permutation"
            rows[n] = {"rec": rec, "alt": alt, "status": r["recommended_status"], "col7_derived": r["lk1952_col7_derived"]}
    assert sorted(rows) == list(range(1, 121)), "table must have ages 1..120"
    return rows


def parse_natal(s):
    natal = {}
    for part in s.split(","):
        p, h = part.split("=")
        p, h = p.strip()[:2].capitalize(), int(h)
        if p not in PLANETS or not 1 <= h <= 12:
            sys.exit(f"bad natal entry {part!r}: planet must be one of {PLANETS}, house 1-12")
        natal[p] = h
    return natal


def age_years(dob, on):
    done = on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))
    return {"completed": done, "running": done + 1}


def annual(natal, n, rows):
    row = rows[n]
    out = {p: row["rec"][h - 1] for p, h in natal.items()}
    alt = {p: row["alt"][h - 1] for p, h in natal.items()} if row["alt"] else None
    return out, alt, row


def show(natal, n, rows, label=""):
    if not 1 <= n <= 120:
        print(f"age-year {n}{label}: outside the 1-120 table; no annual chart.")
        return
    out, alt, row = annual(natal, n, rows)
    print(f"Age-year {n}{label}  [row status: {row['status']}]")
    by_house = {}
    for p, h in out.items():
        by_house.setdefault(h, []).append(p)
    for p in natal:
        diff = f"   | 1952 reading: {alt[p]}" if alt and alt[p] != out[p] else ""
        print(f"  {p}: natal {natal[p]:>2} -> annual {out[p]:>2}{diff}")
    print("  annual chart: " + "  ".join(f"H{h}:{'+'.join(by_house[h])}" for h in sorted(by_house)))
    if alt and alt != out:
        print(f"  WARNING year {n} is an unresolved source conflict (Shrimali vs LK1952 re-typeset); present both readings.")
    if n == 17:
        print("  NOTE year 17 is a documented cell-wise majority reconstruction, not a directly verified row.")


def selftest():
    rows = load()
    assert rows[16]["rec"][5 - 1] == 12, "1952 worked example: natal H5 at year 16 -> H12"
    assert rows[34]["rec"] == [10, 12, 2, 7, 5, 9, 11, 3, 1, 4, 8, 6], "Shrimali p220 year-34 example"
    for y in CONFLICT_YEARS:
        assert rows[y]["alt"] != rows[y]["rec"], f"year {y} should differ between sources"
    assert age_years(datetime.date(2000, 5, 14), datetime.date(2026, 5, 13)) == {"completed": 25, "running": 26}
    assert age_years(datetime.date(2000, 5, 14), datetime.date(2026, 5, 14)) == {"completed": 26, "running": 27}
    print("selftest ok: 120 valid rows, worked examples match, conflict rows detected, age arithmetic ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--natal")
    ap.add_argument("--age", type=int, help="age-year N if the convention is already settled")
    ap.add_argument("--dob", type=datetime.date.fromisoformat)
    ap.add_argument("--on", type=datetime.date.fromisoformat, help="reference date (default today)")
    ap.add_argument("--convention", choices=["running", "completed"])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(); sys.exit()
    if not a.natal:
        ap.error("--natal is required")
    rows, natal = load(), parse_natal(a.natal)
    if a.age:
        show(natal, a.age, rows)
    elif a.dob:
        ages = age_years(a.dob, a.on or datetime.date.today())
        for conv in ([a.convention] if a.convention else ["running", "completed"]):
            show(natal, ages[conv], rows, f" ({conv}-year convention)")
            print()
        if not a.convention:
            print("Convention not fixed by either source: state both, or ask which the user follows.")
    else:
        ap.error("give --age or --dob")
