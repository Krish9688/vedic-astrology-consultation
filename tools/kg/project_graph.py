#!/usr/bin/env python3
"""Deterministic map of the project itself: files, folders, Python imports, tests, document links, external packages and
the engine's MCP tools, CLI commands and REST routes. Standard library only, no network, no timestamps (same tree, same
bytes). Works on all three layouts: the workspace, the private repository and the public repository.
It reads file names, module docstrings, top-level names and Markdown titles; it never reads book text or private folders.

usage: python3 tools/kg/project_graph.py [--root DIR] [--out DIR] [--edition workspace|private|public] [--check]
Writes project.json (Graphify's node-link schema, so `graphify query/explain --graph project.json` works) and project.html.
--check exits 1 if the project.json in --out is not what a fresh scan would write.
"""
import argparse
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph_view  # noqa: E402

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".ruff_cache", ".pytest_cache", ".hypothesis", ".DS_Store"}
OUTPUTS = {"project.json", "project.html"}
# the workspace also holds books, book text, personal folders and caches: only these source folders are ever walked
WORKSPACE_ROOTS = ("astro", "astrology-prediction", "plugin", "public-root", "repo-root", "schemas", "tests", "tools", "validation", "docs")
# prefix in the edition -> prefix in the workspace layout (used to name areas the same way in every edition)
LAYOUT = {"workspace": (),
          "private": (("skill/astrology-consultation/", "astrology-prediction/"),),
          "public": (("plugins/astrology-consultation/engine/astro/", "astro/"),
                     ("plugins/astrology-consultation/skills/astrology-consultation/", "astrology-prediction/"),
                     ("plugins/astrology-consultation/", "plugin/"))}
AREAS = (("astro/", "Engine"), ("astrology-prediction/", "Skill"), ("plugin/", "Plugin"), (".claude-plugin/", "Plugin"),
         ("public-root/", "Public edition root"), ("repo-root/", "Repository root"), ("tools/", "Tools"), ("tests/", "Tests"),
         ("validation/", "Validation"), ("schemas/", "Schemas"), ("docs/", "Docs"), (".github/", "Release and CI"),
         ("releases/", "Release and CI"), ("knowledge/", "Knowledge"), ("sourcemaps/", "Knowledge"), (".claude/", "Agent setup"),
         (".agents/", "Project records"), (".project-council/", "Project records"), ("research/", "Project records"),
         ("notes/", "Project records"), ("legacy/", "Project records"), ("archive/", "Project records"))
# records and book-derived notes stay on the map as files; their contents are not parsed for relationships
UNPARSED = ("knowledge/", "sourcemaps/", "releases/", ".agents/", ".project-council/", "research/", "notes/", "legacy/", "archive/")
DIST = {"swisseph": "pyswisseph", "fitz": "pymupdf", "docx": "python-docx", "yaml": "pyyaml", "PIL": "pillow",
        "graphify": "graphifyy", "dateutil": "python-dateutil"}
TEXT_REF = (".md", ".yml", ".yaml", ".toml", ".sh")
PATH_TOKEN = re.compile(r"(?<![\w/.-])(?:\.{0,2}/)?[\w@+-][\w@.+-]*(?:/[\w@.+-]+)+\.[a-z]{1,5}\b|`[\w.-]+\.(?:py|md|json|toml|sh|html|css|ya?ml)`")
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")


def posix(p):
    return p.replace(os.sep, "/")


def detect_edition(root):
    if os.path.isdir(os.path.join(root, "plugins", "astrology-consultation")):
        return "public"
    return "private" if os.path.isdir(os.path.join(root, "skill", "astrology-consultation")) else "workspace"


def list_files(root, edition, outdir):
    out = []
    tops = WORKSPACE_ROOTS if edition == "workspace" else [""]
    for top in tops:
        for d, ds, fs in os.walk(os.path.join(root, top)):
            ds[:] = sorted(x for x in ds if x not in SKIP_DIRS and not x.startswith(".venv")
                           and x != "private" and not (x == "results" and posix(d).endswith("/tests")))
            for f in fs:
                if f == ".DS_Store" or f.endswith(".pyc") or f == "uv.lock":
                    continue
                path = os.path.join(d, f)
                if os.path.islink(path) or (f in OUTPUTS and os.path.dirname(path) == outdir):
                    continue
                if f == "graph.html" and posix(os.path.relpath(d, root)) == "knowledge/graph":
                    continue   # generated view of the knowledge graph
                out.append(posix(os.path.relpath(path, root)))
    return sorted(out)


def logical(rel, edition):
    for a, b in LAYOUT[edition]:
        if rel.startswith(a):
            return b + rel[len(a):]
    return rel


def area_of(log):
    return next((name for prefix, name in AREAS if log.startswith(prefix)), "Repository root")


def kind_of(log):
    name = os.path.basename(log)
    ext = os.path.splitext(name)[1].lower()
    if name == "SKILL.md" or re.search(r"(^|/)(commands|agents)/[^/]+\.md$", log):
        return "interface"
    if ext == ".py":
        return "test" if log.startswith("tests/") else "module" if log.startswith("astro/") else "script"
    if ext in (".sh", ".swift") or log.endswith("scripts/astro"):
        return "script"
    if ext in (".md", ".txt") or name.startswith(("LICENSE", "NOTICE")):
        return "doc"
    if ext in (".json", ".toml", ".yml", ".yaml", ".ini", ".cfg") or name.startswith("."):
        return "data" if log.startswith(("tests/fixtures", "tests/reference_charts", "tests/lk_golden", "docs/accuracy", "knowledge/")) else "config"
    return "data"


class Project:
    def __init__(self, root, edition, files):
        self.root, self.edition, self.files = root, edition, set(files)
        self.nodes, self.edges, self.broken = {}, set(), []
        self.skill = next((p for p, q in LAYOUT[edition] if q == "astrology-prediction/"), "astrology-prediction/")
        self.engine = next((p for p, q in LAYOUT[edition] if q == "astro/"), "astro/")
        self.suffix = {}
        for f in sorted(files):
            parts = f.split("/")
            for i in range(len(parts)):
                self.suffix.setdefault("/".join(parts[i:]), []).append(f)

    def node(self, nid, label, ntype, source, loc="", ft="code", **attrs):
        self.nodes.setdefault(nid, {"id": nid, "label": label, "file_type": ft, "source_file": source, "source_location": loc,
                                    "node_type": ntype, "attributes": {k: v for k, v in attrs.items() if v not in (None, "", [], {})}})
        return nid

    def edge(self, s, t, rel, inferred=False):
        if s != t:
            self.edges.add((s, t, rel, "INFERRED" if inferred else "EXTRACTED"))

    def read(self, rel):
        try:
            with open(os.path.join(self.root, rel), encoding="utf-8") as f:
                return f.read(4_000_000)
        except (UnicodeDecodeError, OSError):
            return None

    def resolve(self, token, from_dir, bare_ok=True):
        """A project file that this path-like token names, or None. Unique matches only: a wrong edge is worse than none."""
        t = token.strip("`").split("#")[0]
        t = t if t.startswith("../") else t.lstrip("./")
        if not t or re.match(r"[a-z]+:", t):
            return None
        norm = posix(os.path.normpath(os.path.join(from_dir, t)))
        for candidate in (norm, t, self.skill + t, self.engine + t):
            if candidate in self.files:
                return candidate
        for a, b in LAYOUT[self.edition]:      # docs name the workspace layout (astrology-prediction/...)
            if t.startswith(b) and a + t[len(b):] in self.files:
                return a + t[len(b):]
        if "/" not in t and not bare_ok:
            return None
        hits = self.suffix.get(t, [])
        return hits[0] if len(hits) == 1 else None


def file_id(rel):
    return "file:" + rel


def first_line(text):
    for line in (text or "").strip().splitlines():
        line = line.strip(" #-*\t")
        if line:
            return line[:150]
    return ""


def py_summary(tree, text):
    doc = ast.get_docstring(tree)
    if doc:
        return first_line(doc)
    return next((first_line(ln) for ln in text.splitlines() if ln.startswith("#") and not ln.startswith("#!")
                 and first_line(ln) and "private-edition" not in ln), "")


def ensure_folders(p, rel, log, area):
    """Area and folder nodes for a file; returns the folder the file sits in. Folders below the area follow the layout."""
    aid = p.node("area:" + re.sub(r"\W+", "-", area.lower()), area, "Area", "", ft="concept")
    prefix = next((pfx for pfx, name in AREAS if log.startswith(pfx)), "")
    parts = log[len(prefix):].split("/")[:-1]
    real = rel.split("/")[:-1]
    parent = aid
    for i, seg in enumerate(parts):
        real_dir = "/".join(real[:len(real) - len(parts) + i + 1])
        fid = p.node("dir:" + real_dir, seg, "Folder", real_dir, ft="concept", area=area)
        p.edge(parent, fid, "CONTAINS")
        parent = fid
    return parent


def package(p, name, from_file=""):
    dist = DIST.get(name, name).lower()
    return p.node("pkg:" + dist, dist, "Package", from_file, ft="concept")


def module_file(p, dotted, from_dir, level):
    """The project file for a dotted Python module, or None."""
    rel = dotted.replace(".", "/") if dotted else ""
    if level:
        base = from_dir
        for _ in range(level - 1):
            base = posix(os.path.dirname(base))
        bases = [base]
    elif dotted.split(".")[0] == "astro":
        bases = [posix(os.path.dirname(p.engine.rstrip("/")))]
    else:
        bases = [from_dir, p.skill + "scripts", "tools", "tools/kg", "tools/calc", "tools/crosscheck", ""]
    for b in bases:
        for tail in (rel + ".py", rel + "/__init__.py"):
            c = posix(os.path.normpath(os.path.join(b, tail)))
            if c in p.files:
                return c
    if not level and "." not in dotted:
        hits = p.suffix.get(dotted + ".py", [])
        return hits[0] if len(hits) == 1 else None
    return None


def link_import(p, rel, kind, target):
    if kind == "test" and kind_of(logical(target, p.edition)) != "test":
        p.edge(file_id(rel), file_id(target), "TESTS")
    else:
        p.edge(file_id(rel), file_id(target), "IMPORTS")


def add_entries(p, rel, tree, log):
    """Public interfaces of the engine: decorated MCP tools and REST routes, CLI sub-commands (literal names only)."""
    area = p.node("area:interfaces", "Interfaces", "Area", "", ft="concept")

    def entry(prefix, group, name, loc):
        gid = p.node("dir:interfaces/" + prefix, group, "Folder", "", ft="concept", area="Interfaces")
        p.edge(area, gid, "CONTAINS")
        nid = p.node(f"{prefix}:{name}", name, "Interface", rel, f"L{loc}", channel=group)
        p.edge(gid, nid, "CONTAINS")
        p.edge(file_id(rel), nid, "EXPOSES")

    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            for d in n.decorator_list:
                f = d.func if isinstance(d, ast.Call) else d
                attr = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
                if log.endswith("mcp_server.py") and attr in ("tool", "resource", "prompt"):
                    entry("mcp", "MCP tools", n.name, n.lineno)
                elif log.endswith("rest.py") and attr in ("get", "post", "put", "delete") and isinstance(d, ast.Call) and d.args \
                        and isinstance(d.args[0], ast.Constant):
                    entry("rest", "REST routes", f"{attr.upper()} {d.args[0].value}", n.lineno)
    if log.endswith("cli.py"):
        loops = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.For) and isinstance(n.iter, (ast.Tuple, ast.List)):
                names = [c.elts[0].value if isinstance(c, ast.Tuple) else c.value for c in n.iter.elts
                         if isinstance(c, ast.Constant) or (isinstance(c, ast.Tuple) and isinstance(c.elts[0], ast.Constant))]
                target = n.target.elts[0] if isinstance(n.target, ast.Tuple) else n.target
                if isinstance(target, ast.Name):
                    loops[target.id] = names
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "add_parser" and n.args:
                a = n.args[0]
                for name in ([a.value] if isinstance(a, ast.Constant) else loops.get(getattr(a, "id", ""), [])):
                    entry("cli", "CLI commands", str(name), n.lineno)


def scan_python(p, rel, kind, log, text):
    d = posix(os.path.dirname(rel))
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "", []
    stdlib = sys.stdlib_module_names
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [(a.name, 0, []) for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or "", n.level, [a.name for a in n.names])]
        for dotted, level, subs in names:
            hits = [module_file(p, f"{dotted}.{s}".lstrip("."), d, level) for s in subs]
            hits = [h for h in hits if h]
            whole = module_file(p, dotted, d, level) if dotted or level else None
            for t in hits or ([whole] if whole else []):
                if t != rel:
                    link_import(p, rel, kind, t)
            top = dotted.split(".")[0]
            if not hits and not whole and not level and top and top not in stdlib:
                p.edge(file_id(rel), package(p, top, rel), "DEPENDS_ON")
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 120 and re.fullmatch(r"[\w./@-]+\.[a-z]{1,5}", n.value):
            t = p.resolve(n.value, d)
            if t and t != rel:
                is_code = kind_of(logical(t, p.edition)) in ("module", "script")
                p.edge(file_id(rel), file_id(t), "TESTS" if kind == "test" and is_code else "USES", True)
    if log.startswith("astro/"):
        add_entries(p, rel, tree, log)
    defs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    return py_summary(tree, text), defs


def scan_text(p, rel, text):
    d = posix(os.path.dirname(rel))
    if rel.startswith(("public-root/", "repo-root/")):
        d = ""                 # these files are exported to the repository root and link from there
    if rel.endswith(".md"):
        body = re.sub(r"```.*?```", "", text, flags=re.S)
        for link in MD_LINK.findall(body):
            target = link.split("#")[0]
            if not target or re.match(r"[a-z]+:", target):
                continue
            hit = posix(os.path.normpath(os.path.join(d, target)))
            if hit in p.files:
                p.edge(file_id(rel), file_id(hit), "LINKS_TO")
            elif not os.path.isdir(os.path.join(p.root, hit)) and not (p.edition == "workspace" and d == ""):
                p.broken.append(f"{rel} -> {link}")
    for tok in PATH_TOKEN.findall(text):
        t = p.resolve(tok, d, bare_ok=tok.startswith("`"))
        if t and t != rel:
            p.edge(file_id(rel), file_id(t), "REFERENCES", True)


def scan_pyproject(p, rel, text):
    import tomllib
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return
    proj = data.get("project", {})
    deps = list(proj.get("dependencies", []))
    for group in proj.get("optional-dependencies", {}).values():
        deps += group
    for dep in deps:
        name = re.match(r"[A-Za-z0-9_.-]+", dep)
        if name:
            dist = name[0].lower().replace("_", "-")
            p.edge(file_id(rel), p.node("pkg:" + dist, dist, "Package", rel, ft="concept"), "DECLARES")


def release_of(root, edition):
    path = {"public": "plugins/astrology-consultation/.claude-plugin/plugin.json"}.get(edition, "plugin/.claude-plugin/plugin.json")
    try:
        return json.load(open(os.path.join(root, path), encoding="utf-8"))["version"]
    except (OSError, KeyError, ValueError):
        return "unknown"


def build(root, edition, outdir):
    files = list_files(root, edition, outdir)
    p = Project(root, edition, files)
    for rel in files:
        log = logical(rel, edition)
        kind, area = kind_of(log), area_of(log)
        folder = ensure_folders(p, rel, log, area)
        text = None if log.startswith(UNPARSED) else p.read(rel)
        summary, defs = "", []
        if text is not None:
            if rel.endswith(".py"):
                summary, defs = scan_python(p, rel, kind, log, text)
            elif rel.endswith(TEXT_REF):
                scan_text(p, rel, text)
                if rel.endswith(".md"):
                    summary = next((first_line(x) for x in text.splitlines() if x.startswith("#")), "")
            if os.path.basename(rel).endswith("pyproject.toml"):
                scan_pyproject(p, rel, text)
        role = "reference" if log.startswith("astrology-prediction/references/") else "schema" if log.startswith("schemas/") else None
        fid = p.node(file_id(rel), os.path.basename(rel), kind.capitalize(), rel, ft="code" if rel.endswith(".py") else "document", kind=kind,
                     area=area, summary=summary, defs=defs[:60], role=role, lines=text.count("\n") + 1 if text is not None else None)
        p.edge(folder, fid, "CONTAINS")
    return p


def to_node_link(p, edition, release):
    links = [{"source": s, "target": t, "relation": r, "confidence": c, "confidence_score": 1.0 if c == "EXTRACTED" else 0.7,
              "source_file": s.split(":", 1)[1] if s.startswith("file:") else ""} for s, t, r, c in sorted(p.edges)]
    return {"directed": True, "multigraph": False, "graph": {"name": "project", "edition": edition, "release": release,
                                                             "generator": graph_view.generator_sha()},
            "nodes": [p.nodes[k] for k in sorted(p.nodes)], "links": links, "hyperedges": []}


def dumps(g):
    """One node or edge per line, so a rebuild reads as a small diff."""
    head = {k: g[k] for k in ("directed", "multigraph", "graph")}
    rows = lambda xs: ",\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in xs)  # noqa: E731
    return (json.dumps(head, ensure_ascii=False)[:-1] + ',\n"nodes": [\n' + rows(g["nodes"]) + '\n],\n"links": [\n' + rows(g["links"])
            + '\n],\n"hyperedges": []}\n')


def generate(root, outdir, edition=None, switch=None):
    """Scan `root`, write project.json + project.html into `outdir`, return the graph and the scan."""
    root, outdir = os.path.abspath(root), os.path.abspath(outdir)
    edition = edition or detect_edition(root)
    p = build(root, edition, outdir)
    g = to_node_link(p, edition, release_of(root, edition))
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "project.json"), "w", encoding="utf-8", newline="") as f:
        f.write(dumps(g))
    graph_view.write_html(graph_view.project_view(g, switch), os.path.join(outdir, "project.html"))
    return g, p


def main():
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=here)
    ap.add_argument("--out")
    ap.add_argument("--edition", choices=sorted(LAYOUT))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    edition = a.edition or detect_edition(a.root)
    out = os.path.abspath(a.out or os.path.join(a.root, {"workspace": "graphify-out", "private": "knowledge/graph",
                                                         "public": "docs/project-graph"}[edition]))
    if a.check:
        p = build(os.path.abspath(a.root), edition, out)
        fresh = dumps(to_node_link(p, edition, release_of(a.root, edition)))
        try:
            same = open(os.path.join(out, "project.json"), encoding="utf-8").read() == fresh
        except OSError:
            same = False
        print("project graph is current" if same else "project graph is stale: run tools/kg/project_graph.py")
        sys.exit(0 if same else 1)
    switch = None if edition == "public" else graph_view.SWITCH_PROJECT
    g, p = generate(a.root, out, edition, switch)
    print(f"project graph ({edition} {g['graph']['release']}): {len(g['nodes'])} nodes, {len(g['links'])} edges -> {out}")
    for b in p.broken[:40]:
        print("  broken Markdown link:", b)


if __name__ == "__main__":
    main()
