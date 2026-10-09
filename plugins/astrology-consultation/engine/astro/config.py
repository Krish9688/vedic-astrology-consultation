"""Settings and privacy modes. File: $ASTRO_CONFIG or ~/.config/astrology-consultation/config.toml (written by
`astro setup`). Nothing here is required: defaults give a fully local, calculation-only setup.

Privacy modes
  private  (default) local calculation, local books/graph, local reports; no birth data leaves the machine.
  hybrid   private + optional external calculation comparison (VedAstro), per call, with the data sent recorded.
  research hybrid + public web research tools may be used by the AI client; chart data is still never sent there.
"""
from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field

CONFIG_PATH = os.environ.get("ASTRO_CONFIG") or os.path.expanduser("~/.config/astrology-consultation/config.toml")
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, ".."))


@dataclass
class Settings:
    mode: str = "private"
    skill_dir: str = ""                 # the astrology-consultation skill folder (references, scripts)
    knowledge_dir: str = ""             # folder with index/library.sqlite and graphify-out/graph.json (optional)
    books_dir: str = ""                 # the user's own book PDFs (optional; never served)
    reports_dir: str = os.path.expanduser("~/Documents/astrology-reports")
    data_dir: str = os.path.expanduser("~/.local/share/astrology-consultation")
    vedastro_server: str = os.path.expanduser("~/VedAstro/server.mjs")
    allow_remote: bool = False          # HTTP transports bind to 127.0.0.1 unless this is true AND a token is set
    source_url: str = ""                # AGPL-3.0 s.13: your modified source, if you serve a changed engine
    share_library_remotely: bool = False   # serve book excerpts to non-localhost clients (off: copyright)
    api_token: str = ""                 # bearer token required for any non-localhost listener
    extra: dict = field(default_factory=dict)

    @property
    def external_allowed(self) -> bool:
        return self.mode in ("hybrid", "research")


def _default_skill_dir():
    for d in (os.path.join(PROJECT, "skill", "astrology-consultation"), os.path.join(PROJECT, "astrology-prediction"),
              os.path.join(PROJECT, "..", "skills", "astrology-consultation"),      # inside the Claude plugin
              os.path.expanduser("~/.claude/skills/astrology-consultation"),
              os.path.expanduser("~/.agents/skills/astrology-consultation")):
        if os.path.exists(os.path.join(d, "SKILL.md")):
            return d
    return ""


def load() -> Settings:
    s = Settings(skill_dir=_default_skill_dir())
    if os.path.exists(os.path.join(PROJECT, "index", "library.sqlite")):
        s.knowledge_dir = PROJECT
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
        for k, v in data.items():
            if not hasattr(s, k) or k == "extra":
                print(f"astro: unknown setting {k!r} in {CONFIG_PATH} (ignored)", file=sys.stderr)
                s.extra[k] = v
            elif type(v) is not type(getattr(s, k)):         # e.g. allow_remote = "false" would otherwise be truthy
                raise ValueError(f"setting {k!r} must be a {type(getattr(s, k)).__name__}, not {v!r}")
            else:
                setattr(s, k, os.path.expanduser(v) if isinstance(v, str) and k != "api_token" else v)
    for env, key in (("ASTRO_SKILL_DIR", "skill_dir"), ("ASTRO_KNOWLEDGE_DIR", "knowledge_dir")):
        if os.environ.get(env):          # set by the Claude plugin's launcher; wins over the file (paths move on update)
            setattr(s, key, os.environ[env])
    if s.mode not in ("private", "hybrid", "research"):
        raise ValueError(f"unknown privacy mode {s.mode!r}")
    return s


def write(s: Settings) -> str:
    os.makedirs(os.path.dirname(CONFIG_PATH), mode=0o700, exist_ok=True)
    skip = {"extra", "api_token"} | ({"skill_dir"} if os.environ.get("ASTRO_SKILL_DIR") else set())   # don't pin a plugin path
    lines = [f'{k} = {_toml(v)}' for k, v in s.__dict__.items() if k not in skip and v != ""]
    if s.api_token:
        lines.append(f"api_token = {_toml(s.api_token)}")
    with os.fdopen(os.open(CONFIG_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:   # never 0644, even briefly
        f.write("# astrology-consultation settings (astro setup)\n" + "\n".join(lines) + "\n")
    os.chmod(CONFIG_PATH, 0o600)
    return CONFIG_PATH


def _toml(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'
