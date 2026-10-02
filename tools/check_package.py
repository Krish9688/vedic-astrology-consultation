#!/usr/bin/env python3
"""Validate a skill folder (or .skill package) before release. Stdlib only, so it runs in CI and in release_skill.py.

usage: python3 tools/check_package.py <skill folder | package.skill>
Checks the Agent Skills frontmatter rules used by Anthropic's skill-creator quick_validate (kebab-case name ≤ 64,
description ≤ 1024 without angle brackets, allowed keys), that every file SKILL.md links to exists, that no
personal/benchmark folders are inside, and the privacy check on every text file.
"""
import os
import re
import subprocess
import sys
import tempfile
import zipfile

ALLOWED = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
FORBIDDEN = re.compile(r"(^|/)(private|tests/results|benchmark|backups)(/|$)")


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
    if target.endswith(".skill"):
        tmp = tempfile.mkdtemp()
        zipfile.ZipFile(target).extractall(tmp)
        target = os.path.join(tmp, os.listdir(tmp)[0])
    errs = check(target)
    print("package ok" if not errs else "\n".join("✗ " + e for e in errs))
    sys.exit(1 if errs else 0)
