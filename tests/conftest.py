import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))   # the astro package
# test this checkout's skill, never an installed copy (~/.claude/skills) a non-editable engine install would find
for _d in ("plugins/astrology-consultation/skills/astrology-consultation", "astrology-prediction", "skill/astrology-consultation"):
    _p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", _d))
    if os.path.exists(os.path.join(_p, "SKILL.md")):
        os.environ.setdefault("ASTRO_SKILL_DIR", _p)
        break
