#!/usr/bin/env python3
"""The one report catalog: read assets/report/registry.json, list the menu, resolve a name. Standard library only.

  report_catalog.py                  the menu, one line per report (planned ones marked "coming")
  report_catalog.py resolve NAME     JSON: {"status": "built|planned|unknown", "entry": {...}|null, "close": [...], "built": [...]}
  report_catalog.py --selftest
Used by the /report command; the astro-report skill reads the same registry file directly."""
import difflib
import json
import os
import sys

REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "report", "registry.json")


def load(path=REGISTRY):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["reports"]


def keys(entry):
    return [entry["id"], entry["name"].lower(), *entry.get("aliases", [])]


def menu_line(e):
    two = " (two charts)" if e.get("charts") == 2 else ""
    tag = "coming" if e["status"] != "built" else "ready"
    return f"{e['id']} [{tag}] {e['name']}{two}: {e['one_line']}"


def menu(reports=None):
    return "\n".join(menu_line(e) for e in (reports or load()))


def resolve(name, reports=None):
    """(entry, []) on an exact, case-insensitive id, alias or display-name match; else (None, up to 3 closest entries)."""
    reports = reports or load()
    q = (name or "").strip().lower()
    by_key = {k: e for e in reports for k in keys(e)}
    if q in by_key:
        return by_key[q], []
    close = []
    for k in difflib.get_close_matches(q, by_key, n=6, cutoff=0.6):
        if by_key[k] not in close:
            close.append(by_key[k])
    return None, close[:3]


def answer(name, reports=None):
    reports = reports or load()
    entry, close = resolve(name, reports)
    status = "unknown" if entry is None else ("built" if entry["status"] == "built" else "planned")
    return {"status": status, "entry": entry, "close": [{"id": e["id"], "name": e["name"]} for e in close],
            "built": [{"id": e["id"], "name": e["name"]} for e in reports if e["status"] == "built"]}


def selftest():
    r = load()
    assert len(r) >= 1 and all(e["status"] in ("built", "planned") for e in r)
    seen = [k for e in r for k in [e["id"], *e.get("aliases", [])]]
    assert len(seen) == len(set(seen)), "id or alias used twice"
    assert all(e["id"] in menu() for e in r)
    first = r[0]
    assert resolve(first["id"].upper(), r)[0] is first and resolve(first["aliases"][0], r)[0] is first
    assert resolve("zzzzqq", r) == (None, []) and resolve("carer", r)[0] is None
    print(f"report_catalog selftest ok: {len(r)} reports, {sum(e['status'] == 'built' for e in r)} built")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        selftest()
    elif a[:1] == ["resolve"] and len(a) == 2:
        print(json.dumps(answer(a[1]), indent=1))
    elif not a:
        print(menu())
    else:
        sys.exit(__doc__)
