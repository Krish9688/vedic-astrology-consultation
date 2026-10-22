#!/usr/bin/env python3
"""Validate a skill folder (or .skill package) before release. Stdlib only, so it runs in CI and in release_skill.py.

usage: python3 tools/check_package.py <skill folder | package.skill> [--notes RELEASE-NOTES.md]
Checks the Agent Skills frontmatter rules used by Anthropic's skill-creator quick_validate (kebab-case name ≤ 64,
description ≤ 1024 without angle brackets, allowed keys), that every file SKILL.md links to exists, that no
personal/benchmark folders are inside, and the privacy check on every text file. With --notes: the release notes must
not claim that no book-derived data ships when the package carries the Lal Kitab knowledge base (data/lal-kitab/),
and a 'matched <tool>' claim must cite 'provenance: <run_id>' of a tests/fixtures/oracle/ run record of that tool.
"""
import os
import re
import subprocess
import sys
import tempfile
import zipfile

ALLOWED = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
FORBIDDEN = re.compile(r"(^|/)(private|tests/results|benchmark|backups|trash)(/|$)")
# Tripwire, not proof: catches the usual ways of denying that book-derived material ships (AUD-01).
_VERB = r"(?:is|are)?\s*(?:distributed|shipped|ships|included|bundled|contained|packaged|published)"
NO_BOOK_CLAIM = re.compile(
    r"\bno(?:thing)?\s+(?:copyrighted\s+)?(?:books?|book[- ]derived|data derived from (?:any )?books?|derived from books?)"
    r"(?:\s+or\s+book[- ]derived)?(?:\s+(?:data|text|content|material))?\s+" + _VERB
    + r"|\bcontains no book[- ]derived|\bno book[- ]derived (?:data|text|content|material)", re.I)


def notes_errors(folder, notes_text, provenance_dir=None):
    """Release notes must not deny shipping book-derived material that the package contains, and may not claim to
    match another tool without citing a provenance record of that tool's run."""
    has_kb = os.path.isdir(os.path.join(folder, "data", "lal-kitab"))
    m = NO_BOOK_CLAIM.search(notes_text)
    errs = [f"release notes claim {m.group(0)!r} but the package ships data/lal-kitab/ (book-derived)"] if has_kb and m else []
    return errs + match_claim_errors(notes_text, provenance_dir)


# 'matched <tool>' needs a provenance record (P6-1; blind round 7 found a 'matched JHora' claim for a chart JHora never
# ran on). The line must cite `provenance: <run_id>` of a record for that same tool with 0 unresolved rows.
PROVENANCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "oracle")
PROVENANCE_FIELDS = {"run_id": str, "tool": str, "tool_version": str, "local_engine": str, "date": str, "harness": str,
                     "ephemeris": dict, "settings": dict, "charts": list, "verdicts": dict}
_TOOLS = r"PyJHora|JHora|Jagannatha\s+Hora|VedAstro|Parashara'?s\s+Light|Kala|Maitreya|JPL\s+Horizons|Horizons"
MATCH_CLAIM = re.compile(r"(?<![\"'‘“])\b(?:matched|matches|match(?:es|ed)?\s+with|agree[sd]?\s+with|"
                         r"in\s+agreement\s+with|identical\s+to|verified\s+against)\s+(?:the\s+)?(" + _TOOLS + r")\b", re.I)
CITE = re.compile(r"provenance:\s*([\w.-]+)")


def provenance_errors(rec):
    """Shape of one provenance record (the 'provenance' object of a tests/fixtures/oracle/*.json run file)."""
    errs = [f"provenance field {k!r} missing or not {t.__name__}" for k, t in PROVENANCE_FIELDS.items()
            if not isinstance(rec.get(k), t)]
    v = rec.get("verdicts") if isinstance(rec.get("verdicts"), dict) else {}
    errs += [f"verdicts.{k} missing" for k in ("agree", "explained", "unresolved") if not isinstance(v.get(k), int)]
    return errs


def provenance_records(provenance_dir=None):
    import json
    d, out = provenance_dir or PROVENANCE_DIR, {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".json"):
            rec = json.load(open(os.path.join(d, f), encoding="utf-8")).get("provenance")
            if isinstance(rec, dict) and not provenance_errors(rec):
                out[rec["run_id"]] = rec
    return out


def match_claim_errors(notes_text, provenance_dir=None):
    recs, errs = None, []
    norm = lambda s: re.sub(r"\s+", " ", s).lower()
    for line in notes_text.splitlines():
        for m in MATCH_CLAIM.finditer(line):
            recs = provenance_records(provenance_dir) if recs is None else recs
            cited = [recs.get(c) for c in CITE.findall(line)]
            ok = [r for r in cited if r and norm(r["tool"]) == norm(m.group(1)) and r["verdicts"]["unresolved"] == 0]
            if not ok:
                errs.append(f"release notes claim {m.group(0)!r} without citing a provenance record of a {m.group(1)} "
                            f"run with 0 unresolved rows (add 'provenance: <run_id>' from tests/fixtures/oracle/)")
    return errs


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if k.strip() and not line.startswith(" "):
            out[k.strip()] = v.strip()
    return out


def check(folder):
    errs = []
    sk = os.path.join(folder, "SKILL.md")
    if not os.path.exists(sk):
        return ["SKILL.md not found"]
    text = open(sk, encoding="utf-8").read()
    fm = frontmatter(text)
    if fm is None:
        return ["no YAML frontmatter"]
    if set(fm) - ALLOWED:
        errs.append(f"unexpected frontmatter keys {sorted(set(fm) - ALLOWED)}")
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        errs.append(f"bad name {name!r}")
    if not desc or len(desc) > 1024 or "<" in desc or ">" in desc:
        errs.append(f"description missing, too long ({len(desc)}) or contains angle brackets")
    for link in re.findall(r"\]\(([^)#]+)\)", text):
        if not link.startswith("http") and not os.path.exists(os.path.join(folder, link)):
            errs.append(f"SKILL.md links to missing file {link}")
    for root, dirs, files in os.walk(folder):
        rel = os.path.relpath(root, folder).replace(os.sep, "/")
        if FORBIDDEN.search(rel):
            errs.append(f"folder {rel} must not be packaged")
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable, os.path.join(here, "privacy_check.py"), folder], capture_output=True, text=True)
    if r.returncode:
        errs.append("privacy check failed:\n" + r.stdout)
    return errs


if __name__ == "__main__":
    target = sys.argv[1]
    notes = sys.argv[sys.argv.index("--notes") + 1] if "--notes" in sys.argv else None
    if target.endswith(".skill"):
        tmp = tempfile.mkdtemp()
        zipfile.ZipFile(target).extractall(tmp)
        target = os.path.join(tmp, os.listdir(tmp)[0])
    errs = check(target) + (notes_errors(target, open(notes, encoding="utf-8").read()) if notes else [])
    print("package ok" if not errs else "\n".join("✗ " + e for e in errs))
    sys.exit(1 if errs else 0)
