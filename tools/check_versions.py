#!/usr/bin/env python3
"""Fail unless the plugin, the engine and the skill carry the same release version (public repository or private archive layout).
plugin.json "3.5.0" ↔ engine pyproject "3.5.0" ↔ astro.service.VERSION ↔ astro.calc.engine.ENGINE_VERSION ↔ SKILL.md heading "v3.5"."""
import json
import os
import re
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(R, "plugins", "astrology-consultation")
if os.path.isdir(P):                                   # public repository
    F = {"plugin": f"{P}/.claude-plugin/plugin.json", "engine": f"{P}/engine/pyproject.toml",
         "service": f"{P}/engine/astro/service.py", "calc": f"{P}/engine/astro/calc/engine.py",
         "skill": f"{P}/skills/astrology-consultation/SKILL.md"}
else:                                                  # private archive (workspace layout mapped by export_repo.py)
    F = {"plugin": f"{R}/plugin/.claude-plugin/plugin.json", "engine": f"{R}/plugin/engine-pyproject.toml",
         "service": f"{R}/astro/service.py", "calc": f"{R}/astro/calc/engine.py",
         "skill": f"{R}/skill/astrology-consultation/SKILL.md", "package": f"{R}/pyproject.toml"}
txt = lambda k: open(F[k], encoding="utf-8").read()
plugin = json.loads(txt("plugin"))["version"]
engine = re.search(r'^version = "([^"]+)"', txt("engine"), re.M).group(1)
service = re.search(r'^VERSION = "([^"]+)"', txt("service"), re.M).group(1)
calc = re.search(r'^ENGINE_VERSION = "([^"]+)"', txt("calc"), re.M).group(1)
skill = re.search(r"^# .*, v(\d+\.\d+)", txt("skill"), re.M).group(1)
package = re.search(r'^version = "([^"]+)"', txt("package"), re.M).group(1) if "package" in F else engine
ok = plugin == engine == service == calc == package and plugin.startswith(skill + ".")
print(f"plugin {plugin} · engine {engine} · package {package} · service {service} · calc {calc} · skill v{skill} → {'consistent' if ok else 'MISMATCH'}")
sys.exit(0 if ok else 1)
