# The /astro-report plugin skill: frontmatter, report-type menu vs the renderer, message ids, and the reports-folder guard
import os
import re
import sys

from astro import config, service as S

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_MD = next(p for d in ("plugin", "plugins/astrology-consultation")     # workspace and archive repo; public repo
                if os.path.exists(p := os.path.join(HERE, "..", d, "skills", "astro-report", "SKILL.md")))
from astro import mcp_server as _mcp  # noqa: E402   resolves in every layout (engine on the path in the public repo)
MCP_SRC = _mcp.__file__
sys.path.insert(0, os.path.join(config.load().skill_dir, "scripts"))
import render_report as rr  # noqa: E402

TEXT = open(SKILL_MD, encoding="utf-8").read()
FIELDS = {"description", "argument-hint", "disable-model-invocation", "allowed-tools"}      # confirmed Claude Code fields only


def _frontmatter():
    m = re.match(r"---\n(.*?)\n---\n", TEXT, re.S)
    assert m, "SKILL.md needs frontmatter"
    return dict(line.split(": ", 1) for line in m.group(1).splitlines())


def test_frontmatter_has_only_confirmed_fields():
    fm = _frontmatter()
    assert set(fm) == FIELDS
    assert fm["disable-model-invocation"] == "true" and fm["argument-hint"] == '"[report-type]"'
    assert "context" not in fm


def test_allowed_tools_are_real_astro_tools_without_bash_or_write():
    tools = _frontmatter()["allowed-tools"].split()
    assert "AskUserQuestion" in tools
    assert not {"Bash", "Write", "Edit"} & set(tools)
    prefix = "mcp__plugin_astrology-consultation_astrology__"
    served = set(re.findall(r"^def (\w+)\(", open(MCP_SRC, encoding="utf-8").read(), re.M))
    mcp = [t for t in tools if t != "AskUserQuestion"]
    assert mcp and all(t.startswith(prefix) and t[len(prefix):] in served for t in mcp), mcp
    assert {"find_place", "create_report", "get_birth_time_sensitivity"} <= {t[len(prefix):] for t in mcp}


def test_report_types_in_skill_equal_renderer_type_names():
    rows = re.findall(r"^\| `([a-z0-9-]+)` \| ([^|]+) \|$", TEXT, re.M)
    assert dict(rows) == rr.TYPE_NAMES
    for name in rr.TYPE_NAMES.values():          # and each display name reaches the two-step menu
        assert TEXT.count(name) >= 2, name


def test_every_message_id_and_the_confirmation_line_are_present():
    ids = set(re.findall(r"^\| (V-[A-Z0-9-]+) \|", TEXT, re.M))
    need = {"V-TYPE", "V-DATE-1", "V-DATE-2", "V-DATE-3", "V-DATE-4", "V-DATE-5", "V-DATE-6", "V-TIME-1", "V-TIME-2",
            "V-TIME-3", "V-STATUS", "V-PLACE-1", "V-PLACE-2", "V-PLACE-3", "V-COORD", "V-OFFSET-1", "V-ZONE-UNKNOWN",
            "V-ZONE-GAP", "V-ZONE-OVERLAP", "V-ZONE-LMT", "V-ZONE-1948", "V-ZONE-1970", "V-ZONE-MISMATCH",
            "V-ZONE-UNCONF", "V-CONSENT-OTHER", "V-IDENT", "V-OUTLOOK", "V-FOLDER", "V-SAFE-GUARANTEE",
            "V-SAFE-MEDICAL", "V-SAFE-CRISIS", "V-ENGINE", "V-RENDER"}
    assert need <= ids, need - ids
    assert "<place> — <IANA zone>, UTC<+HH:MM> on that date — correct?" in TEXT
    assert "None of these" in TEXT and "1895" in TEXT and "must be CONFIRMED" in TEXT       # pre-1948 clock is forced
    assert TEXT.index("### 2. Whose chart?") < TEXT.index("### 4. Date of birth")        # identity gate first
    assert len(TEXT.splitlines()) < 400


# --- reports folder guard (V-FOLDER) -----------------------------------------------------------------------------------
def _set_reports_dir(tmp_path, monkeypatch, d):
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.toml"))
    (tmp_path / "config.toml").write_text(f'data_dir = "{tmp_path / "data"}"\nreports_dir = "{d}"\n')


def test_folder_refusal_covers_git_tree_plugin_root_and_skill_folder(tmp_path, monkeypatch):
    work = tmp_path / "proj"
    (work / ".git").mkdir(parents=True)
    plugin = tmp_path / "plug"
    (plugin / "skills" / "astrology-consultation").mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin))
    skill = str(plugin / "skills" / "astrology-consultation")
    for bad in (work, work / "deep" / "er", plugin, plugin / "reports", plugin / "skills" / "astrology-consultation" / "x"):
        assert config.folder_refusal(str(bad), skill) == config.FOLDER_REFUSAL, bad
    link = tmp_path / "link"
    link.symlink_to(work)
    assert config.folder_refusal(str(link), skill) == config.FOLDER_REFUSAL      # symlinks resolve first
    assert config.folder_refusal(str(tmp_path / "ok" / "reports"), skill) == ""


def test_create_report_writes_nothing_into_a_git_tree(tmp_path, monkeypatch):
    work = tmp_path / "proj"
    (work / ".git").mkdir(parents=True)
    _set_reports_dir(tmp_path, monkeypatch, work / "reports")
    res = S.create_report({}, "anything")
    assert res == {"ok": False, "errors": [config.FOLDER_REFUSAL]}
    assert not (work / "reports").exists()
    _set_reports_dir(tmp_path, monkeypatch, tmp_path / "fine")
    assert config.FOLDER_REFUSAL not in S.create_report({}, "anything").get("errors", [])
