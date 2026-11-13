"""Where the user's own book library lives: $ASTRO_KG / $ASTRO_LIBRARY_DB, then `knowledge_dir` in the astro settings
file (~/.config/astrology-consultation/config.toml, written by `astro setup --knowledge-dir`), then the standard data
folder. Nothing here is bundled with the skill; without a library the scripts say retrieval is unavailable."""
import os
import re
import tomllib



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
    roots.append(os.path.expanduser("~/.local/share/astrology-consultation/knowledge"))
    for r in roots:
        if os.path.exists(os.path.join(r, rel)):
            return os.path.join(r, rel)
    return os.path.join(roots[0], rel)


VARIANTS = [("sh", "s"), ("aa", "a"), ("ee", "i"), ("oo", "u")]   # common transliteration spellings


OWN_SYSTEMS = re.compile(r"(Parashari|Jaimini|Lal Kitab|Nadi|Kerala Prashna|Tajika|Muhurta)")


def own_source_ids(conn):
    """Ids of the books whose catalog system is one of this project's traditions (the index keeps it in `tradition`).
    Western, Hellenistic and reference-only books are left out: systems are never mixed unless the caller asks."""
    return [i for i, t in conn.execute("select id, tradition from sources") if OWN_SYSTEMS.match(t or "")]


def fts_terms(query, stop=("the", "and", "for", "with", "from", "its")):
    """Words of a question as FTS5 terms; a word with transliteration variants becomes (word OR variant ...),
    e.g. vimshottari → (vimshottari OR vimsottari)."""
    terms = []
    for w in re.findall(r"[A-Za-z]{3,}", query.lower()):
        if w in stop:
            continue
        alts = {w} | {w.replace(a, b) for a, b in VARIANTS if a in w}
        terms.append(w if len(alts) == 1 else "(" + " OR ".join(sorted(alts)) + ")")
    return terms
