"""Where the user's own book library lives: $ASTRO_KG / $ASTRO_LIBRARY_DB, then `knowledge_dir` in the astro settings
file (~/.config/astrology-consultation/config.toml, written by `astro setup --knowledge-dir`), then the standard data
folder. Nothing here is bundled with the skill; without a library the scripts say retrieval is unavailable."""
import os
import tomllib

LEGACY = os.path.expanduser("~/Documents/Astrology Books/_skill_workspace")   # the original author's layout


def knowledge_file(env, rel):
    if os.environ.get(env):
        return os.environ[env]
    cfg = os.environ.get("ASTRO_CONFIG") or os.path.expanduser("~/.config/astrology-consultation/config.toml")
    roots = []
    try:
        with open(cfg, "rb") as f:
            kd = tomllib.load(f).get("knowledge_dir")
        if kd:
            roots.append(os.path.expanduser(kd))
    except (OSError, tomllib.TOMLDecodeError):
        pass
    roots += [os.path.expanduser("~/.local/share/astrology-consultation/knowledge"), LEGACY]
    for r in roots:
        if os.path.exists(os.path.join(r, rel)):
            return os.path.join(r, rel)
    return os.path.join(roots[0], rel)
