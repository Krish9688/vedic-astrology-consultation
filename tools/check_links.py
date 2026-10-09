#!/usr/bin/env python3
"""Fail on broken relative links in Markdown files. usage: python3 tools/check_links.py [ROOT] [--skip DIR ...]
(default ROOT: .; --skip: folders, relative to ROOT, whose links are checked elsewhere, e.g. public-root/)
External (http/mailto) links and pure #anchors are not checked; links inside code spans/blocks are ignored."""
import os
import re
import sys

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".hypothesis", ".ruff_cache"}


def broken(root, skip=()):
    bad = []
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in SKIP_DIRS and not x.startswith(".venv")
                 and os.path.relpath(os.path.join(d, x), root) not in skip]
        for f in fs:
            if not f.endswith(".md"):
                continue
            path = os.path.join(d, f)
            text = re.sub(r"```.*?```|`[^`\n]*`", "", open(path, encoding="utf-8").read(), flags=re.S)
            for link in re.findall(r"\]\(([^)\s]+)\)", text):
                target = link.split("#")[0]
                if not target or re.match(r"[a-z]+:", target):
                    continue
                if not os.path.exists(os.path.normpath(os.path.join(d, target))):
                    bad.append(f"{os.path.relpath(path, root)} → {link}")
    return bad


if __name__ == "__main__":
    args = sys.argv[1:]
    skip = {args[i + 1].rstrip("/") for i, a in enumerate(args) if a == "--skip"}
    pos = [a for i, a in enumerate(args) if a != "--skip" and (i == 0 or args[i - 1] != "--skip")]
    found = broken(pos[0] if pos else ".", skip)
    print(f"link check: {len(found)} broken")
    for b in found:
        print("  ✗", b)
    sys.exit(1 if found else 0)
