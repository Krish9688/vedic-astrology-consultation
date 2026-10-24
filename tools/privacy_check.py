#!/usr/bin/env python3
"""Refuse to publish private or restricted material. Runs in pre-commit and CI; complements Gitleaks (secrets).

usage: python3 tools/privacy_check.py [--archive] [PATH ...]   (default: every file tracked or staged in the git repo)
--archive: rules for the PRIVATE archive repository (see check()); never use it on the public repository.
Checks, generic (safe to keep in a public repo):
  - book files and binaries that must stay local: .pdf .epub .djvu .sqlite .db .tgz .zip .skill, anything > 5 MB
  - folders that hold personal or derived-from-books data: private/, backups/, text/, index/, graphify-out/,
    sourcemaps/<book parts>, knowledge/extraction.json, knowledge/chapters/, benchmark answers
  - absolute home paths (/Users/<name>/, /home/<name>/), e-mail addresses, .env files
  - images and office documents outside an assets/ folder (a chart screenshot or a report scan cannot be read here)
  - birth-data records found by their structure ("Date of birth: …", "born on … at …", {"date": …, "time": …}) unless
    the record's fingerprint is in tools/birthdata-reviewed.txt (synthetic or published charts, reviewed by hand).
    `--records PATH…` lists fingerprints with the record for that review (local output only).
Checks, personal (terms read from an untracked local file, never stored in the repo):
  - every line of $ASTRO_PRIVACY_TERMS (default ~/.config/astrology-consultation/privacy-terms.txt), case-insensitive,
    e.g. a birth date, birth time + place, a name. Missing file → personal checks skipped (as in CI).
Exit 1 on any finding.
"""
import gzip
import hashlib
import os
import re
import subprocess
import sys
import tarfile
import unicodedata
import zipfile

BLOCK_EXT = {".pdf", ".epub", ".djvu", ".sqlite", ".db", ".tgz", ".zip", ".skill", ".jsonl", ".env", ".tar", ".7z", ".rar",
             ".xz", ".bz2", ".pkl", ".pickle"}   # archives cannot be checked member by member here
BLOCK_DIRS = re.compile(r"(^|/)(private|backups|text|index|graphify-out|read|vendor|\.venv[^/]*)/")
BLOCK_FILES = re.compile(r"(^|/)(knowledge/extraction\.json|knowledge/chapters/|sourcemaps/(?!BRIEF|STATUS|README)[^/]+\.md$|"
                         r"sourcemaps/(staging|logs)/|tests/results/)")
HOME = re.compile(r"/(?:Users|home)/(?!runner\b|<)[A-Za-z0-9._-]+/")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.|anthropic\.com|users\.noreply\.github\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
MAX = 5 * 1024 * 1024
# caches that running tools/tests writes into a scanned folder; no exporter or package ever includes them
CACHE_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".hypothesis"}
MEDIA_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".tif", ".tiff", ".bmp", ".doc", ".docx", ".xls", ".xlsx",
             ".ppt", ".pptx", ".odt", ".rtf", ".pages", ".numbers", ".key"}
ASSETS = re.compile(r"(^|/)assets/")
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2", ".ico"}
_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
_D = (r"(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|"
      rf"\d{{1,2}}(?:st|nd|rd|th)?[\s/-]*{_MON}[\s,/-]*\d{{4}}|{_MON}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s*\d{{4}})")
_T = r"\d{1,2}[:.]\d{2}"
_LABEL = (r"(?<![a-z])(?:date[\s_]*of[\s_]*birth|birth[\s_-]*(?:date(?:time)?|time|place)|d\.?\s?o\.?\s?b\.?|"
          r"time[\s_]*of[\s_]*birth|place[\s_]*of[\s_]*birth|t\.?\s?o\.?\s?b\.?|born(?:[\s_]*on)?|"
          r"जन्म\s*(?:तिथि|तारीख|दिनांक|समय|स्थान))(?![a-z])")
RECORD = [re.compile(rf"(?i){_LABEL}(?:\s*\([^)\n]{{0,25}}\))?[\s\"':=–-]{{0,6}}(?:{_D}|{_T})"),
          re.compile(r"(?is)[\"']?date[\"']?\s*[:=]\s*[\"']?\d{4}-\d{2}-\d{2}.{0,80}?[\"']?time[\"']?\s*[:=]\s*[\"']?\d{1,2}:\d{2}"),
          re.compile(r"(?is)[\"']?time[\"']?\s*[:=]\s*[\"']?\d{1,2}:\d{2}.{0,80}?[\"']?date[\"']?\s*[:=]\s*[\"']?\d{4}-\d{2}-\d{2}"),
          re.compile(r"(?i)[\"']?datetime[\"']?\s*[:=]\s*[\"']?\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")]
_ZW = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad")) | {0x966 + i: str(i) for i in range(10)}


def normalise(text):
    """NFKC, zero-width characters removed, Devanagari digits as ASCII: hiding tricks do not hide a record."""
    return unicodedata.normalize("NFKC", text).translate(_ZW)


def decode(data):
    """Text of a file, or None when it cannot be read (then it is refused, never skipped)."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None
_REVIEWED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "birthdata-reviewed.txt")
REVIEWED = {ln.split()[0] for ln in open(_REVIEWED_FILE, encoding="utf-8") if ln.strip() and not ln.startswith("#")} \
    if os.path.exists(_REVIEWED_FILE) else set()
PACKAGE_EXT = {".skill", ".zip", ".tgz"}
ARCHIVE_OK = re.compile(r"(^|/)(knowledge/chapters/|knowledge/extraction\.json\.gz$|sourcemaps/|"
                        r"archive/skill-test-results/[^/]+(/[^/]+)?\.md$)")
TEXT_EXT = {".md", ".py", ".json", ".txt", ".toml", ".yaml", ".yml", ".j2", ".css", ".html", ".cfg", ".sh", ".swift", ".csv",
            ".log", ""}


def git_ignored(folder, rels):
    """Paths (relative to folder) that git ignores there, so they can never be published (e.g. Finder's .DS_Store).
    Tracked files are never reported by check-ignore, so a committed file is still scanned. Outside a git work
    tree (e.g. an export staging folder) nothing is skipped."""
    if not rels:
        return set()
    r = subprocess.run(["git", "-C", folder, "check-ignore", "--stdin", "-z"], input="\0".join(rels),
                       capture_output=True, text=True)
    return {p for p in r.stdout.split("\0") if p} if r.returncode in (0, 1) else set()


def files(args):
    """(path to open, path to judge): a scanned folder's files are judged relative to that folder, so the folder's
    own location (e.g. /private/tmp/…) never matches a rule."""
    if args:
        out = []
        for a in args:
            if os.path.isdir(a):
                found = [(os.path.join(r, f), os.path.relpath(os.path.join(r, f), a)) for r, _, fs in os.walk(a)
                         for f in fs if not CACHE_DIRS & set(os.path.relpath(r, a).split(os.sep)) and not f.endswith(".pyc")]
                ignored = git_ignored(a, [rel for _, rel in found])
                out += [x for x in found if x[1] not in ignored]
            else:
                out.append((a, a))
        return out
    r = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], capture_output=True, text=True)
    return [(f, f) for f in r.stdout.splitlines() if f and os.path.exists(f)]   # deleted-but-tracked files are not published


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
        yield "?", None


def terms():
    p = os.environ.get("ASTRO_PRIVACY_TERMS") or os.path.expanduser("~/.config/astrology-consultation/privacy-terms.txt")
    if not os.path.exists(p):
        return []
    return [t.strip().lower() for t in open(p, encoding="utf-8") if t.strip() and not t.startswith("#")]


def records(text):
    """(fingerprint, record) for each structural birth-data record; the fingerprint is of the record alone, so edits
    around a reviewed record need no new review. Fingerprints are listed only for synthetic or published records."""
    out, text = [], normalise(text)
    for rx in RECORD:
        for m in rx.finditer(text):   # the whole line(s) the record sits on: a reviewed head cannot cover a new tail
            a, b = text.rfind("\n", 0, m.start()) + 1, text.find("\n", m.end())
            snip = " ".join(text[a:b if b >= 0 else len(text)].lower().split())
            out.append((hashlib.sha256(snip.encode()).hexdigest()[:16], snip))
    return out


def scan_text(rel, text, T, paths=True):
    bad, low = [], normalise(text).lower()
    new = [h for h, _ in records(text) if h not in REVIEWED]
    if new:
        bad.append(f"{rel}: {len(new)} unreviewed birth-data record(s) — personal data stays in private/; if synthetic "
                   f"or published, review with --records and add to tools/birthdata-reviewed.txt")
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
        if ext in MEDIA_EXT and not ASSETS.search(rel):
            bad.append(f"{rel}: image or office document outside assets/ (cannot be checked for personal data)")
            continue
        if os.path.getsize(f) > MAX:
            bad.append(f"{rel}: larger than 5 MB")
            continue
        if package:
            for name, data in members(f):
                if data is None:
                    bad.append(f"{rel}: unreadable package (cannot be checked)")
                    continue
                n_ext = os.path.splitext(name)[1].lower()
                if BLOCK_DIRS.search("/" + name) or n_ext in BLOCK_EXT or (n_ext in MEDIA_EXT and not ASSETS.search(name)):
                    bad.append(f"{rel}!{name}: must stay local, or cannot be checked inside a package")
                    continue
                # historical packages are kept byte-identical; pre-v3.4 ones embed the owner's library path, which is
                # acceptable in the private archive (and why they are never published) — personal terms still fail
                bad += scan_text(f"{rel}!{name}", data.decode("utf-8", "ignore"), T, paths=False)
            continue
        if ext == ".gz" and not rel.endswith(".tar.gz"):     # compressed graph/extraction: same checks as text
            try:
                with gzip.open(f, "rt", encoding="utf-8") as g:
                    bad += scan_text(rel, g.read(), T)
            except (OSError, UnicodeDecodeError, EOFError):
                bad.append(f"{rel}: unreadable .gz")
            continue
        if rel.endswith(".tar.gz"):
            bad.append(f"{rel}: archive (cannot be checked member by member here)")
            continue
        if ext in FONT_EXT:
            continue
        try:
            text = decode(open(f, "rb").read())
        except OSError:
            text = None
        if text is None:   # fail closed: an unreadable file is never waved through
            bad.append(f"{rel}: cannot be read as UTF-8/UTF-16 text, so it cannot be checked")
            continue
        bad += scan_text(rel, text, T)
    return bad, len(T)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--records"]:
        for f, rel in files(sys.argv[2:]):
            text = decode(open(f, "rb").read())
            if text is not None:
                for h, snip in records(text):
                    print(h, "REVIEWED" if h in REVIEWED else "new", rel, "|", snip)
        sys.exit(0)
    args = [a for a in sys.argv[1:] if a != "--archive"]
    found, n = check(files(args), archive="--archive" in sys.argv)
    print(f"privacy check: {len(found)} finding(s); personal terms checked: {n or 'none (no local list)'}")
    for x in found:
        print("  ✗", x)
    sys.exit(1 if found else 0)
