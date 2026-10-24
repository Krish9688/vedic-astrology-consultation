#!/usr/bin/env python3
"""Lal Kitab Varshaphal (annual chart) lookup from the validated v2.2 table. Read-only; never edits the CSV.

usage:
  varshaphal.py --natal "Su=1,Mo=12,Ma=3,Me=2,Ju=11,Ve=2,Sa=8,Ra=11,Ke=5" --age 34
  varshaphal.py --natal "..." --dob 1990-05-14 --on 2026-09-23          # running year (LK1952 p243) + completed note
  varshaphal.py --natal "..." --dob 1990-05-14 --on 2026-09-23 --convention completed
  varshaphal.py --selftest

--natal: each planet's NATAL Lal Kitab house (1-12, counted from the birth lagna; signs are dropped).
Age-year N: 'running' = completed years + 1 (year 1 = birth to 1st birthday); 'completed' = completed years.
LK1952 counts the running year: its table example reads "in the 16th year of age" (p243, owner page check 2026-10-24,
LK-F37), so --dob shows the running year and notes the completed-years reading; Shrimali states no convention.
Each planet also gets its month of effect from both editions (KB R42): LK1952 p239/p241 and Shrimali p209-210; --dob
names the Shrimali calendar month.
Output uses RECOMMENDED_house_k. Years 67/99/104 also print the competing 1952 reading; year 17 prints the 1952 row as
the books-only reading (its recommended row leans on an untraced web chart).
"""
import argparse, csv, datetime, os, sys

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "lal-kitab", "LalKitab_Varshaphal_Table_v2.2.csv")
PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
CONFLICT_YEARS = {67, 99, 104}
# Year 17: the recommended cells 3-4 came from a majority that counted an untraced web chart (council 6 provenance check,
# 2026-10-18); the 1952 edition's row is a valid permutation, so it is shown as the books-only reading.
ALT_YEARS = CONFLICT_YEARS | {17}
# Month of effect (KB R42; owner page check 2026-10-24, LK-F35, decision D-5 (a)). The two editions are printed side
# by side and never merged. LK1952 p241: house -> Vikrami month, the year starting about 13 April.
LK1952_MONTHS = ["Vaisakh", "Jeth", "Asarh", "Sawan", "Bhadrapad", "Asuj", "Kartik", "Maghar", "Paush", "Magh",
                 "Phalgun", "Chaitra"]
CALENDAR = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "December"]


def load():
    rows = {}
    with open(CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n = int(r["age_year"])
            rec = [int(r[f"RECOMMENDED_house_{k}"]) for k in range(1, 13)]
            assert sorted(rec) == list(range(1, 13)), f"row {n} is not a permutation"
            alt = None
            if n in ALT_YEARS:
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


def lk1952_month(natal, out, p):
    """LK1952 p239: arriving in a natally occupied house -> that house's fixed month (p241); in a natally empty house ->
    the month numbered by the annual Sun's house, counted from the birthday."""
    h = out[p]
    if h in natal.values():
        return f"{LK1952_MONTHS[h - 1]} (fixed month of H{h}: natally occupied) [LK1952 p239, p241]"
    if "Su" not in out:
        return f"H{h} natally empty: month = annual Sun's house, annual Sun not given [LK1952 p239]"
    return f"month {out['Su']} counted from the birthday (annual Sun in H{out['Su']}; H{h} natally empty) [LK1952 p239]"


def shrimali_month(h, birth_month=None):
    """Shrimali p209-210: the planet's own varshaphal house h = month h, counting the birth month as month 1."""
    if birth_month is None:
        return f"month {h} from the birth month (birth month = 1) [Shrimali p209-210]"
    return f"month {h} from the birth month = {CALENDAR[(birth_month + h - 2) % 12]} [Shrimali p209-210]"


def show(natal, n, rows, label="", birth_month=None):
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
        print(f"      month: {lk1952_month(natal, out, p)}")
        print(f"      month: {shrimali_month(out[p], birth_month)}")
    print("  annual chart: " + "  ".join(f"H{h}:{'+'.join(by_house[h])}" for h in sorted(by_house)))
    if "Su" in out:
        print(f"  year's main effect: month {out['Su']} from the birthday (annual Sun in H{out['Su']}) "
              "[LK1952 p241; Shrimali p219]")
    if alt and alt != out:
        print("  months above use the recommended reading; recompute them for the 1952 reading.")
    if n == 17:
        print("  NOTE year 17 is a cell-wise majority reconstruction that counted an untraced web chart; the 1952 "
              "edition's row (a valid permutation) is the books-only reading — present both readings when they differ.")
    elif alt and alt != out:
        print(f"  WARNING year {n} is an unresolved source conflict (Shrimali vs LK1952 re-typeset); present both readings.")


def selftest():
    rows = load()
    assert rows[16]["rec"][5 - 1] == 12, "1952 worked example: natal H5 at year 16 -> H12"
    assert rows[34]["rec"] == [10, 12, 2, 7, 5, 9, 11, 3, 1, 4, 8, 6], "Shrimali p220 year-34 example"
    for y in CONFLICT_YEARS:
        assert rows[y]["alt"] != rows[y]["rec"], f"year {y} should differ between sources"
    assert age_years(datetime.date(2000, 5, 14), datetime.date(2026, 5, 13)) == {"completed": 25, "running": 26}
    assert age_years(datetime.date(2000, 5, 14), datetime.date(2026, 5, 14)) == {"completed": 26, "running": 27}
    assert lk1952_month({"Ju": 2}, {"Me": 2}, "Me").startswith("Jeth"), "LK1952 p239: occupied H2 -> Jeth"
    assert lk1952_month({"Su": 1}, {"Su": 8, "Ma": 4}, "Ma").startswith("month 8"), "LK1952 p239: empty H4, Sun 8"
    assert "January" in shrimali_month(12, birth_month=2), "Shrimali p210: February birth, H12 -> January"
    print("selftest ok: 120 valid rows, worked examples match, conflict rows detected, age arithmetic ok, months ok")


def show_dob(natal, rows, dob, on, convention=None):
    """Age-year from the birth date: the running year by default (LK1952 p243), the completed year only when asked."""
    ages = age_years(dob, on)
    if convention == "completed":
        show(natal, ages["completed"], rows, " (completed-year convention, not LK1952's)", birth_month=dob.month)
        return
    show(natal, ages["running"], rows, " (running year, LK1952 p243)", birth_month=dob.month)
    print(f"Note: the completed-years convention would give age-year {ages['completed']} (LK1952 p243 counts the running"
          " year, 'the 16th year of age'); Shrimali states no convention.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--natal")
    ap.add_argument("--age", type=int, help="age-year N if the convention is already settled")
    ap.add_argument("--dob", type=datetime.date.fromisoformat)
    ap.add_argument("--on", type=datetime.date.fromisoformat, help="reference date (default today)")
    ap.add_argument("--convention", choices=["running", "completed"])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(CSV):   # the table is a private data file: not distributed in the public edition (book still in copyright)
        if a.selftest:
            print("selftest skipped: the Varshaphal table is not installed (private data file)")
            sys.exit(0)
        sys.exit("The Lal Kitab Varshaphal table (a private data file; the book is still in copyright) is not installed. "
                 "Say so to the user and give no annual chart; do not reconstruct the table from memory.")
    if a.selftest:
        selftest(); sys.exit()
    if not a.natal:
        ap.error("--natal is required")
    rows, natal = load(), parse_natal(a.natal)
    if a.age:
        show(natal, a.age, rows)
    elif a.dob:
        show_dob(natal, rows, a.dob, a.on or datetime.date.today(), a.convention)
    else:
        ap.error("give --age or --dob")
