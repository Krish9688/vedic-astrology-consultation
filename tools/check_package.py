#!/usr/bin/env python3
"""Validate a skill folder (or .skill package) before release. Stdlib only, so it runs in CI and in release_skill.py.

usage: python3 tools/check_package.py <skill folder | package.skill> [--notes RELEASE-NOTES.md]
Checks the Agent Skills frontmatter rules used by Anthropic's skill-creator quick_validate (kebab-case name ≤ 64,
description ≤ 1024 without angle brackets, allowed keys), that every file SKILL.md links to exists, that no
personal/benchmark folders are inside, and the privacy check on every text file. With --notes: the release notes must
not claim that no book-derived data ships when the package carries the Lal Kitab knowledge base (data/lal-kitab/).
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


def notes_errors(folder, notes_text):
    """Release notes must not deny shipping book-derived material that the package contains."""
    has_kb = os.path.isdir(os.path.join(folder, "data", "lal-kitab"))
    m = NO_BOOK_CLAIM.search(notes_text)
    return [f"release notes claim {m.group(0)!r} but the package ships data/lal-kitab/ (book-derived)"] if has_kb and m else []


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
