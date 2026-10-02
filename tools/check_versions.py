#!/usr/bin/env python3
"""Fail unless the plugin, the engine and the skill carry the same release version (public repository layout).
plugin.json "3.5.0" ↔ engine pyproject "3.5.0" ↔ astro.service.VERSION "3.5.0" ↔ SKILL.md heading "v3.5"."""
import json
import os
import re
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(R, "plugins", "astrology-consultation")
plugin = json.load(open(os.path.join(P, ".claude-plugin", "plugin.json")))["version"]
engine = re.search(r'^version = "([^"]+)"', open(os.path.join(P, "engine", "pyproject.toml")).read(), re.M).group(1)
service = re.search(r'^VERSION = "([^"]+)"', open(os.path.join(P, "engine", "astro", "service.py")).read(), re.M).group(1)
skill = re.search(r"^# .*, v(\d+\.\d+)", open(os.path.join(P, "skills", "astrology-consultation", "SKILL.md")).read(), re.M).group(1)
ok = plugin == engine == service and plugin.startswith(skill + ".")
print(f"plugin {plugin} · engine {engine} · service {service} · skill v{skill} → {'consistent' if ok else 'MISMATCH'}")
sys.exit(0 if ok else 1)
