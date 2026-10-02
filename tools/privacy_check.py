#!/usr/bin/env python3
"""Refuse to publish private or restricted material. Runs in pre-commit and CI; complements Gitleaks (secrets).

usage: python3 tools/privacy_check.py [--archive] [PATH ...]   (default: every file tracked or staged in the git repo)
--archive: rules for the PRIVATE archive repository (see check()); never use it on the public repository.
Checks, generic (safe to keep in a public repo):
  - book files and binaries that must stay local: .pdf .epub .djvu .sqlite .db .tgz .zip .skill, anything > 5 MB
  - folders that hold personal or derived-from-books data: private/, backups/, text/, index/, graphify-out/,
    sourcemaps/<book parts>, knowledge/extraction.json, knowledge/chapters/, benchmark answers
  - absolute home paths (/Users/<name>/, /home/<name>/), e-mail addresses, .env files
Checks, personal (terms read from an untracked local file, never stored in the repo):
  - every line of $ASTRO_PRIVACY_TERMS (default ~/.config/astrology-consultation/privacy-terms.txt), case-insensitive,
    e.g. a birth date, birth time + place, a name. Missing file → personal checks skipped (as in CI).
Exit 1 on any finding.
"""
import os
import re
import subprocess
import sys
import tarfile
import zipfile

BLOCK_EXT = {".pdf", ".epub", ".djvu", ".sqlite", ".db", ".tgz", ".zip", ".skill", ".jsonl", ".env"}
BLOCK_DIRS = re.compile(r"(^|/)(private|backups|text|index|graphify-out|read|vendor|\.venv[^/]*)/")
BLOCK_FILES = re.compile(r"(^|/)(knowledge/extraction\.json|knowledge/chapters/|sourcemaps/(?!BRIEF|STATUS|README)[^/]+\.md$|"
                         r"sourcemaps/(staging|logs)/|tests/results/)")
HOME = re.compile(r"/(?:Users|home)/(?!runner\b|<)[A-Za-z0-9._-]+/")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.|anthropic\.com|users\.noreply\.github\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
MAX = 5 * 1024 * 1024
PACKAGE_EXT = {".skill", ".zip", ".tgz"}
ARCHIVE_OK = re.compile(r"(^|/)(knowledge/chapters/|knowledge/extraction\.json\.gz$|sourcemaps/)")
TEXT_EXT = {".md", ".py", ".json", ".txt", ".toml", ".yaml", ".yml", ".j2", ".css", ".html", ".cfg", ".sh", ".swift", ""}


def files(args):
    """(path to open, path to judge): a scanned folder's files are judged relative to that folder, so the folder's
    own location (e.g. /private/tmp/…) never matches a rule."""
    if args:
        out = []
        for a in args:
            if os.path.isdir(a):
                out += [(os.path.join(r, f), os.path.relpath(os.path.join(r, f), a)) for r, _, fs in os.walk(a)
                        for f in fs if ".git" not in os.path.relpath(r, a).split(os.sep)]
            else:
                out.append((a, a))
        return out
    r = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], capture_output=True, text=True)
    return [(f, f) for f in r.stdout.splitlines() if f]


def members(f):
    """Text members of a package (.skill/.zip/.tgz), so archived packages get the same personal-data checks."""
    try:
        if f.endswith((".tgz", ".tar.gz")):
            with tarfile.open(f) as t:
                for m in t.getmembers():
                    if m.isfile():
                        yield m.name, t.extractfile(m).read()
        else:
            with zipfile.ZipFile(f) as z:
                for n in z.namelist():
                    yield n, z.read(n)
    except (zipfile.BadZipFile, tarfile.TarError, OSError):
        yield "?", b""


def terms():
    p = os.environ.get("ASTRO_PRIVACY_TERMS") or os.path.expanduser("~/.config/astrology-consultation/privacy-terms.txt")
    if not os.path.exists(p):
        return []
    return [t.strip().lower() for t in open(p, encoding="utf-8") if t.strip() and not t.startswith("#")]


def scan_text(rel, text, T, paths=True):
    bad, low = [], text.lower()
    for rx, what in ((HOME, "absolute home path"), (EMAIL, "e-mail address")) if paths else ():
        m = rx.search(text)
        if m and "privacy_check" not in rel:
            bad.append(f"{rel}: {what} '{m.group()}'")
    if any(t in low for t in T):
        bad.append(f"{rel}: contains a personal term from the local privacy list")
    return bad


def check(paths, archive=False):
    """archive=True: the PRIVATE archive repository, which deliberately keeps book-derived analysis (source maps,
    chapter maps, the compressed graph) and the release packages. Personal data, secrets, books, page text and
    oversized files are refused exactly as in the public check; packages are opened and scanned member by member."""
    bad, T = [], terms()
    for f, rel in paths:
        rel = rel.replace(os.sep, "/").removeprefix("./")
        ext = os.path.splitext(rel)[1].lower()
        package = archive and ext in PACKAGE_EXT and re.match(r"(releases|legacy)/", rel)
        if BLOCK_DIRS.search("/" + rel) or (ext in BLOCK_EXT and not package) or \
                (BLOCK_FILES.search(rel) and not (archive and ARCHIVE_OK.search(rel))):
            bad.append(f"{rel}: must stay local (books, personal or book-derived data)")
            continue
        if os.path.getsize(f) > MAX:
            bad.append(f"{rel}: larger than 5 MB")
            continue
        if package:
            for name, data in members(f):
                # historical packages are kept byte-identical; pre-v3.4 ones embed the owner's library path, which is
                # acceptable in the private archive (and why they are never published) — personal terms still fail
                bad += scan_text(f"{rel}!{name}", data.decode("utf-8", "ignore"), T, paths=False)
            continue
        if ext not in TEXT_EXT:
            continue
        try:
            bad += scan_text(rel, open(f, encoding="utf-8").read(), T)
        except (UnicodeDecodeError, OSError):
            continue
    return bad, len(T)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--archive"]
    found, n = check(files(args), archive="--archive" in sys.argv)
    print(f"privacy check: {len(found)} finding(s); personal terms checked: {n or 'none (no local list)'}")
    for x in found:
        print("  ✗", x)
    sys.exit(1 if found else 0)
