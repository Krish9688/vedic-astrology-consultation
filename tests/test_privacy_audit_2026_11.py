# Privacy tooling fixes from the 2026-11-01 audit (F-01, F-02, F-05, F-08, F-09 = issue #49, F-10, F-32).
# Synthetic data only: every folder is built under tmp_path; no real private/ or report folder is touched. Sample
# birth records and home paths are assembled at run time so this file itself holds no record or home path.
import importlib.util
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "tools"))
import privacy_check as P  # noqa: E402

D, T = "-".join(("1990", "08", "15")), ":".join(("10", "30"))          # an invented date and time
DMY = "/".join(("15", "08", "1990"))
HOME_SAMPLE = "/" + "Users" + "/someone/x"


def _flagged(tmp_path, monkeypatch, rel, text):
    monkeypatch.setenv("ASTRO_PRIVACY_TERMS", str(tmp_path / "none.txt"))
    monkeypatch.setattr(P, "REVIEWED", set())
    f = tmp_path / "r" / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    return P.check([(str(f), rel)])[0]


# ---- F-01 privacy_check gaps ----
@pytest.mark.parametrize("text", [
    "t = datetime(" + ", ".join(("1990", "8", "15", "10", "30")) + ")",                 # (a) Python tuple
    f"astro chart --date {D} --time {T} --tz +05:30",                                    # (a) CLI flags
    f"astro chart --time={T} --birth-date={D}",
    '{"d": "' + D + '", "t": "' + T + '"}',                                              # (a) other JSON keys
    f"birth {DMY} {T}",                                                                  # (a) free text
])
def test_f01_new_record_shapes_are_flagged(tmp_path, monkeypatch, text):
    assert any("birth-data record" in x for x in _flagged(tmp_path, monkeypatch, "docs/x.md", text)), text


@pytest.mark.parametrize("text", ["released " + D + ", see the notes", "a birthday party", "datetime(2000, 1, 1)",
                                  "Rahu return every 18.6 years", "run at " + T + " daily"])
def test_f01_ordinary_text_is_not_a_record(tmp_path, monkeypatch, text):
    assert _flagged(tmp_path, monkeypatch, "docs/x.md", text) == []


def test_f01_exemption_is_exact_paths_only(tmp_path, monkeypatch):
    text = f"see {HOME_SAMPLE} and mail someone@" + "mailhost.org\n"
    assert len(_flagged(tmp_path, monkeypatch, "notes/my_privacy_check_notes.md", text)) == 2   # (b) substring no longer exempt
    assert _flagged(tmp_path, monkeypatch, "tools/privacy_check.py", text) == []
    assert P.path_exempt("/x/repo/tests/test_privacy_check.py") and not P.path_exempt("privacy_check.py")   # RP-06
    assert not P.path_exempt("tools/privacy_check_old.py") and not P.path_exempt("check.py")


B = "\\"                                                                                # Windows separator, joined at run time


@pytest.mark.parametrize("path,hit", [(f"C:{B}Users{B}someone{B}x", True), (f"C:{B * 2}Users{B * 2}someone{B * 2}x", True),
                                      ("D:/" + "Users/someone/x", True), (f"C:{B}Users{B}<name>{B}x", False),
                                      (f"C:{B}Users{B}Public{B}x", False)])
def test_f01_windows_home_paths(path, hit):
    assert bool(P.HOME.search(path)) is hit                                             # (d)


def test_f01_no_args_outside_git_fails_closed(tmp_path):
    (tmp_path / "a.md").write_text("synthetic\n")
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(tmp_path.parent))
    r = subprocess.run([sys.executable, os.path.join(WS, "tools", "privacy_check.py")], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    assert r.returncode != 0 and "no files to check" in (r.stderr + r.stdout)          # (c) was "0 finding(s)", exit 0


# ---- F-05 export sanitiser must survive its own export ----
FILES_F05 = ["tools/export_repo.py", "tools/public_edition.py", "tools/report_gate.py", "tools/privacy_check.py",
             "tools/cc_hooks.py", "tests/test_export.py", "tests/test_privacy_boundary.py", "tests/test_privacy_check.py",
             "tests/test_privacy_audit_2026_11.py"]


def test_f05_exported_sanitiser_still_sanitises(tmp_path):
    ER = pytest.importorskip("export_repo", reason="exporters are private-edition tooling")
    src = open(os.path.join(WS, "tools", "export_repo.py"), encoding="utf-8").read()
    exported = ER.sanitize(src)
    assert exported == src                                   # nothing in the exporter is rewritten by its own rules
    (tmp_path / "export_repo.py").write_text(exported)
    spec = importlib.util.spec_from_file_location("export_repo_exported", tmp_path / "export_repo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import getpass
    home, user = os.path.expanduser("~"), getpass.getuser()
    sample = f"see {home}/notes and {home}/Documents/Astrology Books/x and private/{user}/y"
    out = mod.sanitize(sample)
    assert out != sample and home not in out and "~/notes" in out and "~/Documents/Astrology Books/x" in out
    if len(user) >= 3:
        assert f"private/{user}/" not in out and "private/<person>/y" in out


@pytest.mark.parametrize("rel", FILES_F05)
def test_f05_privacy_tooling_is_export_stable(rel):
    ER = pytest.importorskip("export_repo", reason="exporters are private-edition tooling")
    path = os.path.join(WS, rel)
    if not os.path.exists(path):
        pytest.skip(f"{rel} is not in this edition")
    text = open(path, encoding="utf-8").read()
    assert ER.sanitize(text) == text, f"{rel} would differ after export (A-05/A-17 drift)"


# ---- F-08 one hook matcher, both settings files and the guard's docstring ----
WANT = "WebSearch|WebFetch|Bash|Read|Grep|Glob|Write|Edit|NotebookEdit|mcp__.*"


def _guard_matchers(path):
    hooks = json.load(open(path, encoding="utf-8"))["hooks"]["PreToolUse"]
    return [h["matcher"] for h in hooks if any("cc_hooks.py" in x.get("command", "") and x["command"].rstrip().endswith("guard")
                                               for x in h["hooks"])]


def test_f08_settings_and_docstring_agree():
    files = [p for p in (os.path.join(WS, ".claude", "settings.json"), os.path.join(WS, "repo-root", ".claude", "settings.json"))
             if os.path.exists(p)]
    if not files:
        pytest.skip("no Claude Code settings in this edition")
    got = {p: _guard_matchers(p) for p in files}
    assert all(m == [WANT] for m in got.values()), got
    hooks_py = os.path.join(WS, "tools", "cc_hooks.py")
    if os.path.exists(hooks_py):
        doc = re.search(r"guard\s+PreToolUse\s+\(([^)]*)\)", open(hooks_py, encoding="utf-8").read()).group(1)
        assert doc == WANT
    for tool in ("WebSearch", "Read", "Grep", "Glob", "NotebookEdit", "mcp__astro__get_chart"):
        assert re.fullmatch(WANT, tool), tool


# ---- cc_hooks: synthetic library layout ----
@pytest.fixture
def H(tmp_path, monkeypatch):
    H = pytest.importorskip("cc_hooks", reason="Claude Code hooks are private-edition tooling")
    lib = tmp_path.resolve() / "Lib"
    root = lib / "_skill_workspace"
    for d in ("private/p1", "astrology-reports", "_skill_workspace/private/p2", "_skill_workspace/tools",
              "_skill_workspace/docs"):
        (lib / d).mkdir(parents=True)
    (lib / "private/p1/x.txt").write_text("synthetic")
    (root / "docs/a.md").write_text("synthetic")
    monkeypatch.setattr(H, "LIB", str(lib))
    monkeypatch.setattr(H, "ROOT", str(root))
    monkeypatch.setattr(H, "HOME_REPORTS", str(tmp_path / "home" / "astrology-reports"))
    H.lib, H.root = str(lib), str(root)
    return H


def _bash(H, cwd, cmd):
    return H.guard({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd})


def test_f02_case_changed_paths_are_protected(H):
    low = H.lib.replace("/Lib", "/lib") + "/PRIVATE/p1/x.txt"
    assert H.guard({"tool_name": "Read", "tool_input": {"file_path": low}, "cwd": H.root})
    assert H.guard({"tool_name": "Write", "tool_input": {"file_path": H.lib.upper() + "/ASTROLOGY-REPORTS/r.md"}, "cwd": H.root})
    assert _bash(H, H.root, f"cat {low}")
    assert H.protected_prefix(low.lower()) and H.protected_prefix(H.lib + "/docs") is None


@pytest.mark.parametrize("cmd", ["grep -rn x .", "grep -rn x ..", "rg x", "find . -name x", "ls -R", "du -sh .",
                                 "tar cf /tmp/a.tar .", "cp -r . /tmp/b", "rsync -a . /tmp/c", "zip -r /tmp/d.zip .",
                                 "grep -rn x --exclude-dir=docs .", "cd tools && cd .. && rg x",
                                 "cat private/p2/x", "ls private", "echo x > private/p2/y"])
def test_f09_blocked(H, cmd):
    assert _bash(H, H.root, cmd), cmd


@pytest.mark.parametrize("cmd", ["echo private", "grep -c private docs/a.md", "rg x . --glob '!private'",
                                 "grep -rn x --exclude-dir=private .", "find . -path ./private -prune -o -print",
                                 "grep -rn x tools docs", "cd tools && grep -rn x .", "ls -la", "du -sh tools"])
def test_f09_allowed(H, cmd):
    assert _bash(H, H.root, cmd) is None, cmd


def test_f09_library_root_needs_every_exclusion(H):
    assert _bash(H, H.lib, "rg x . --glob '!private'")                 # astrology-reports is there too
    # a report-folder name anywhere in a Bash command is refused (older, coarser rule kept): from the library root a
    # recursive search therefore cannot be made acceptable by exclusions — search a subfolder instead
    assert _bash(H, H.lib, "rg x . --glob '!private' --glob '!astrology-reports'")
    assert _bash(H, H.lib, "rg x _skill_workspace/docs") is None
    assert _bash(H, H.lib, "grep -c private _skill_workspace/docs/a.md") is None


def test_f09_grep_and_glob_tools(H):
    g = lambda tool, **inp: H.guard({"tool_name": tool, "tool_input": inp, "cwd": H.root})
    assert g("Grep", pattern="x") and g("Glob", pattern="**/*.md")
    assert g("Grep", pattern="x", path="tools") is None and g("Grep", pattern="x", glob="!private/**") is None
    assert g("Glob", pattern="docs/**/*.md") is None


def test_f08_mcp_tools_get_path_checks(H):
    g = lambda tool, **inp: H.guard({"tool_name": tool, "tool_input": inp, "cwd": H.root})
    assert g("mcp__fs__read_text_file", path=H.lib + "/private/p1/x.txt")
    assert g("mcp__shell__exec", command="cat ../private/p1/x.txt")
    assert g("mcp__astro__get_chart", date="2000-01-01", time="12:00", tz="+05:30") is None


# ---- F-10 web queries ----
@pytest.mark.parametrize("q,blocked", [(f"horoscope {D} New Delhi", True), (DMY, True), ("15 August 1990 Pune", True),
                                       ("August 15, 1990 kundli", True), ("solar eclipse 2024-04-08 path", False),
                                       ("Saturn ingress 2025-03-29 Pisces", False), ("Jupiter in Taurus 2099-05-01", False),
                                       ("Ashtakoota guna milan table", False)])
def test_f10_full_past_dates_in_web_queries(q, blocked):
    H = pytest.importorskip("cc_hooks", reason="Claude Code hooks are private-edition tooling")
    assert bool(H.guard({"tool_name": "WebSearch", "tool_input": {"query": q}})) is blocked, q


def test_f10_dated_url_paths_pass_but_query_strings_do_not():
    H = pytest.importorskip("cc_hooks", reason="Claude Code hooks are private-edition tooling")
    fetch = lambda url: H.guard({"tool_name": "WebFetch", "tool_input": {"url": url, "prompt": "summary"}})
    assert fetch("https://news.example.org/2024/05/01/story") is None
    assert fetch(f"https://x.example.org/chart?d={D}")


# ---- F-32 destructive commands ----
@pytest.mark.parametrize("cmd,blocked", [("rm --recursive build", True), ("rm -f -r build", True), ("rm -R build", True),
                                         ("git clean -fdx", True), ("git clean -n", False), ("find build -delete", True),
                                         ("git checkout -- .", True), ("git checkout -- a.py", False),
                                         ("git checkout main", False), ("rm build/a.txt", False)])
def test_f32_always_deny(tmp_path, cmd, blocked):
    H = pytest.importorskip("cc_hooks", reason="Claude Code hooks are private-edition tooling")
    assert bool(H.guard({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(tmp_path)})) is blocked, cmd


def test_git_worktree_dotgit_file_is_not_scanned(tmp_path):
    """A git worktree's .git is a FILE holding the absolute gitdir path; scanning '.' must skip it like the .git folder."""
    home = os.path.expanduser("~")
    (tmp_path / ".git").write_text("gitdir: " + os.path.join(home, "x", ".git", "worktrees", "w") + "\n")
    (tmp_path / "ok.md").write_text("nothing personal\n")
    r = subprocess.run([sys.executable, os.path.join(WS, "tools", "privacy_check.py"), "."], cwd=tmp_path,
                       capture_output=True, text=True)
    assert ".git" not in r.stdout, r.stdout


# ---- council round 2 (REVIEW-privacy.md RP-01..RP-09) ----
@pytest.mark.parametrize("cmd", ["rsync -a -I private/ o/", "rsync -a -x ../private/ o/", "tar -c -f o.tar -I private/x",
                                 "grep -rn x --exclude-dir=privatex .", "grep -rn x --exclude=private .",
                                 "rg x . -g !private_old", "bash -c grep -r x .", "sh -c rg x", "zsh -c cat private/p2",
                                 "grep -d recurse x .", "grep --directories recurse x .", "fd x", "mdfind -onlyin . x",
                                 "ugrep -r x .", "ditto . o", "pax -w .", "git grep --no-index x", "env -C . grep -r x .",
                                 "xargs -a docs/a.md grep -r x"])
def test_rp01_rp03_bypasses_are_blocked(H, cmd):
    assert _bash(H, H.root, cmd), cmd


@pytest.mark.parametrize("cmd", ["rsync -a docs/ o/", "tar -cf o.tar docs", "grep -rn x --exclude-dir=private .",
                                 "rg x . -g !private/**", "find . -path ./private -prune -o -print",
                                 "find . -not -path *private* -name x", "git grep x"])
def test_rp01_rp02_legitimate_commands_still_pass(H, cmd):
    assert _bash(H, H.root, cmd) is None, cmd


def test_rp02_grep_tool_exclusion_must_name_the_folder(H):
    g = lambda **inp: H.guard({"tool_name": "Grep", "tool_input": inp, "cwd": H.root})
    assert g(pattern="x", glob="!privatex") and g(pattern="x", glob="!private/**") is None


def test_rp09_mcp_string_arguments_braces_and_walks(H):
    g = lambda tool, **inp: H.guard({"tool_name": tool, "tool_input": inp, "cwd": H.root})
    assert g("mcp__fs__copy", source="private/p2", destination="/tmp/y")
    assert g("mcp__fs__read_multiple_files", files=["../private/p1/x.txt"])
    assert g("mcp__fs__search", query="x", uri="file://" + H.root)
    assert g("mcp__fs__dir_tree", path=".")
    assert g("mcp__browser__exec", code="open('../private/p1/x.txt').read()")
    assert H.guard({"tool_name": "Glob", "tool_input": {"pattern": "{private,docs}/*"}, "cwd": H.root})
    assert g("mcp__fs__dir_tree", path="docs") is None


@pytest.mark.parametrize("q", ["transit 1993-04-17 Pune horoscope", "Moon conjunction on 17 April 1993 Pune birth chart",
                               "kundli 17 Apr 93 Pune", "kundli 4/17/93 Pune", "kundli 17041993 Pune",
                               "kundli 1993 April 17 Pune", "kundli 17th of April 1993 Pune"])
def test_rp04_more_date_shapes_and_no_sky_event_loophole(q):
    H = pytest.importorskip("cc_hooks", reason="Claude Code hooks are private-edition tooling")
    assert H.guard({"tool_name": "WebSearch", "tool_input": {"query": q}}), q


def test_rp06_folder_scan_does_not_exempt_a_bare_privacy_check(tmp_path):
    home = "/" + "Users" + "/someone"                    # a synthetic home: the CI runner home is allow-listed
    (tmp_path / "privacy_check.py").write_text(f"x = '{home}/notes'\n")
    r = subprocess.run([sys.executable, os.path.join(WS, "tools", "privacy_check.py"), str(tmp_path)],
                       capture_output=True, text=True)
    assert "home path" in r.stdout, r.stdout


@pytest.mark.parametrize("text,hit", [("/" + "USERS/someone/x", True), ("c:" + B + "users" + B + "someone" + B, True),
                                      ("https://api.github.com/" + "users/someone/repos", False)])
def test_rp07_home_paths_any_case(text, hit):
    assert bool(P.HOME.search(text)) is hit


def test_rp06_ci_folder_scan_still_exempts_the_checker_itself():
    """CI runs `privacy_check.py --archive tools tests …` from the repo root: the checker and its test are judged by
    their repo-relative paths and stay exempt (a bare relative-to-folder name would not be)."""
    r = subprocess.run([sys.executable, os.path.join("tools", "privacy_check.py"), "--archive",
                        os.path.join("tools", "privacy_check.py"), "tests"], cwd=WS, capture_output=True, text=True)
    assert "privacy_check.py: absolute home path" not in r.stdout, r.stdout
