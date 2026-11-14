#!/usr/bin/env python3
"""Build the public user guide (one offline HTML file). `--check` verifies it. Counts come from graph.json."""
import html, json, re, sys
from collections import Counter
from pathlib import Path

W = Path(__file__).resolve().parents[2]
GRAPH, REG = W / "graphify-out/graph.json", W / "astrology-prediction/assets/report/registry.json"
README, OUT = W / "public-root/README.md", W / "public-root/docs/USER-GUIDE.html"
E = html.escape


def stats():
    """Stream graph.json (pretty-printed, one object per 4-space block); keep counts and book titles only."""
    sec = buf = None
    types, rels, comm, titles = Counter(), Counter(), Counter(), set()
    for ln in open(GRAPH, encoding="utf-8"):
        if ln.startswith('  "nodes"'): sec = "n"; continue
        if ln.startswith('  "links"'): sec = "e"; continue
        if ln.startswith("  ]"): sec = None
        if sec is None: continue
        if ln.startswith("    {"): buf = []
        if buf is not None: buf.append(ln)
        if ln.startswith("    }"):
            o = json.loads("".join(buf).rstrip().rstrip(",")); buf = None
            if sec == "e": rels[o["relation"]] += 1; continue
            types[o["node_type"]] += 1
            comm[o.get("community_name") or ""] += 1
            if o["node_type"] == "Book": titles.add(o["label"])
            if o.get("attributes", {}).get("book"): titles.add(o["attributes"]["book"])
    norm = lambda s: re.sub(r"\W+", " ", s).strip().lower()
    tn = {norm(t) for t in titles}
    # skip a community named like a book title (exact, or the name contains a whole title)
    generic = [(n, c) for n, c in comm.most_common() if n and norm(n) not in tn
               and not any(len(x) > 3 and x in norm(n) for x in tn)]
    return {"types": dict(types), "rels": dict(rels), "books": types["Book"],
            "communities": generic[:12], "nodes": sum(types.values()), "edges": sum(rels.values())}, titles


def registry():
    r = json.loads(REG.read_text())["reports"]
    return [x for x in r if x["status"] == "built"], [x for x in r if x["status"] != "built"]


def quickstart():
    """The bash blocks of README 'Quick start', verbatim."""
    sec = re.search(r"## Quick start\n(.*?)\n## ", README.read_text(), re.S).group(1)
    return re.findall(r"```bash\n(.*?)```", sec, re.S)


def svg(s):
    t = s["types"]
    r = {k: 0 for k in ("PART_OF", "RULE_FROM", "MENTIONS", "APPLIES_TO", "DISCUSSED_IN", "HAS_POSITION", "WRITTEN_BY", "CONTRADICTS")}
    r.update(s["rels"])
    def node(x, y, name, cls, w=118):
        return (f'<g class="n {cls}"><rect x="{x - w // 2}" y="{y - 21}" width="{w}" height="42" rx="9"/>'
                f'<text x="{x}" y="{y - 2}">{name}</text><text x="{x}" y="{y + 13}" class="c">{t.get(name, 0):,}</text></g>')
    def edge(x1, y1, x2, y2, rel, lx, ly, n):
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#a)"/>'
                f'<text class="e" x="{lx}" y="{ly}">{rel} {n:,}</text>')
    cons = ["Topic", "Planet", "House", "Sign", "Yoga", "Technique", "Nakshatra", "DivisionalChart", "LalKitabConcept"]
    o = ['<svg viewBox="0 0 760 500" role="img" aria-labelledby="gt gd"><title id="gt">Knowledge graph schema</title>'
         '<desc id="gd">Pages belong to books. Rules cite pages. Rules and pages point to concept nodes. '
         'Contradictions hold opposed positions.</desc>'
         '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0L10 5L0 10z" class="ah"/></marker></defs>']
    o += [edge(299, 60, 177, 60, "PART_OF", 238, 50, r["PART_OF"]),
          edge(360, 81, 360, 159, "RULE_FROM", 300, 124, r["RULE_FROM"]),
          edge(419, 52, 524, 100, "MENTIONS", 470, 60, r["MENTIONS"]),
          edge(419, 175, 524, 160, "APPLIES_TO", 470, 190, r["APPLIES_TO"]),
          edge(360, 201, 360, 279, "DISCUSSED_IN", 292, 244, r["DISCUSSED_IN"]),
          edge(360, 321, 360, 399, "HAS_POSITION", 292, 366, r["HAS_POSITION"]),
          edge(117, 81, 117, 159, "WRITTEN_BY", 60, 124, r["WRITTEN_BY"]),
          '<path d="M419 430 C500 425 500 465 419 462" fill="none" marker-end="url(#a)"/>'
          f'<text class="e" x="500" y="450">CONTRADICTS {r["CONTRADICTS"]:,}</text>']
    o += [node(117, 60, "Book", "s"), node(360, 60, "Page", "s"), node(117, 180, "Person", "s"),
          node(360, 180, "Rule", "k"), node(360, 300, "Contradiction", "k"), node(360, 430, "Position", "k")]
    o += [node(582 + 118 * (i % 2), 100 + 62 * (i // 2), c, "t", 112) for i, c in enumerate(cons)]
    return "".join(o) + "</svg>"


def pages(s, built, planned):
    qs = quickstart()
    rows = "".join(f"<li><b>{E(x['name'])}</b> <code>{E(x['id'])}</code> &mdash; {E(x['one_line'])}</li>" for x in built)
    soon = "".join(f"<li>{E(x['name'])}</li>" for x in planned)
    mx = s["communities"][0][1]
    bars = "".join(f'<li><span>{E(n)}</span><b>{c:,}</b><i style="width:{100 * c // mx}%"></i></li>' for n, c in s["communities"])
    P = [("What this skill is", """<p>A Vedic astrology consultation for Claude. It has three parts: a <b>local calculation engine</b>
(positions, dashas, transits, strengths), <b>method files</b> that say how to reason from those facts, and a
<b>cited book library</b> behind the rules.</p><p>Facts are computed. Interpretation follows documented methods.
Nothing is sent to an outside service. This is not medical, legal or financial advice, and astrology's predictive
validity is not scientifically established.</p>"""),
         ("Install and first use", f"""<p>In Claude Code:</p><pre>{E(qs[0].strip())}</pre>
<p>Then run <code>/astrology-consultation:setup</code> in a session and <code>/reload-plugins</code>. Setup builds a private
Python environment and downloads the ephemeris files. It needs Python 3.11+ or uv, and internet once.</p>
<p>No Claude? Use the engine alone:</p><pre>{E(qs[1].strip())}</pre>
<p>Then ask, for example: &ldquo;Calculate my chart.&rdquo; Platforms: macOS and Linux (Windows via WSL 2).</p>"""),
         ("Asking questions", """<p>Ask in plain chat. Give the <b>birth date, birth time and birth place</b>, and say where the time came from
(birth certificate, family memory, a rectified time). The source matters because a few minutes can change the rising sign.</p>
<p>You get a short, life-first answer:</p><ul><li>what it means for you and its likely form</li>
<li>a <b>grade</b> for how clearly the chart agrees</li><li><b>timing</b> as periods</li>
<li>a <b>counter-factor</b>: what pulls the other way</li><li><b>what to watch</b></li></ul>"""),
         ("Reports", f"""<p>Type <code>/report</code> to see the menu, then pick a type. {len(built)} report types render today;
{len(planned)} more are listed and coming soon. The list below is read from the report registry.</p>
<h3>Built</h3><ul>{rows}</ul><h3>Coming soon</h3><ul class="cols">{soon}</ul>"""),
         ("How to read a report", """<p><b>Grades</b> (Strong, Moderate, Weak) say how clearly the chart agrees with itself on a point.
They do not say whether the area of life is good or bad.</p>
<p><b>Windows and phases</b> are stretches of time when a theme is active. Read them as weather, not verdicts.</p>
<p>The appendix <b>&ldquo;Why each conclusion&rdquo;</b> lists the evidence behind every statement, so you can check it.</p>
<p><b>Birth-time sensitivity</b> shows which statements survive a few minutes of error. If it says high, treat that statement as uncertain.</p>"""),
         ("The knowledge graph", f"""<p>The rules come from a library of {s['books']} books, held as a graph of
{s['nodes']:,} nodes and {s['edges']:,} edges. Each rule points to the page that supports it.</p>{svg(s)}
<p class="leg"><b>Node</b>: a thing (a book, a page, a rule, a planet); the number under its name is how many exist.
<b>Edge</b>: an arrow from one node to another; the number is how many exist.
<b>Colour</b>: <span class="k1">sage = sources</span> <span class="k2">parchment, dashed = claims</span> <span class="k3">mint = concepts</span>.</p>
<p>The graph is built deterministically from page-cited rule maps. It never merges rules, and it keeps disagreements
as Contradiction nodes. The public edition ships the tools, not the private library graph.</p>
<h3>12 largest topics (nodes per topic)</h3><ul class="bars">{bars}</ul>"""),
         ("What it does well", """<ul><li>Positions and dates are <b>computed and checked against the engine</b>, never recalled.</li>
<li><b>Every claim is graded</b>: Strong, Moderate, Weak, Contradictory or Unknown.</li>
<li>Rules are <b>page-cited</b>, so a reader can look the source up.</li>
<li><b>Contradictions are kept</b>, not smoothed over.</li><li>Safety limits are built in (see Safety and privacy).</li></ul>"""),
         ("Known limits", """<p>An independent review by two reviewers of a full Kundli report found these problems. They are listed
so you can read reports with them in mind.</p><ul>
<li>Grade words collide with ordinary adjectives, so &ldquo;strong&rdquo; can be misread.</li>
<li>Most grades land on Moderate, which limits how well they separate strong points from weak ones.</li>
<li>Phase notes inherit the grade of their window instead of being graded on their own.</li>
<li>A planet that rules a hard house is framed only by its natural meaning, not by that functional role.</li>
<li>A transit date can be printed without an evidence file behind it.</li>
<li>Western books are in the library but are never used for Vedic readings.</li>
<li>There is no muhurta (choosing a date) module.</li>
<li>PDF output needs WeasyPrint; without it, print the HTML report from a browser.</li>
<li>Some report types are still planned.</li></ul>"""),
         ("What you can learn", """<ul><li>How a careful astrologer moves from <b>computed facts</b> to a <b>graded judgement</b>.</li>
<li>Reading timing as <b>phases, not verdicts</b>.</li>
<li>Why <b>counter-factors</b> matter: every claim should say what pulls the other way.</li>
<li>How to <b>check a claim's source</b> in the appendix, and judge whether it supports the claim.</li></ul>"""),
         ("Safety and privacy", """<ul><li>Health: no diagnosis and no body claims.</li>
<li>Remedies are Parashari only: no gems, no costly rituals, and every remedy carries a line saying no efficacy is claimed.</li>
<li>No verdicts on other people.</li><li>Your data stays on your computer.</li></ul>"""),
         ("Glossary", """<dl><dt>Lagna</dt><dd>The rising sign at birth; it sets the houses.</dd>
<dt>Dasha</dt><dd>A planetary period in a fixed sequence that times life themes.</dd>
<dt>Antardasha</dt><dd>A sub-period inside a dasha.</dd>
<dt>Sade Sati</dt><dd>Saturn's roughly seven-and-a-half-year passage around the Moon sign.</dd>
<dt>Shadbala</dt><dd>A six-fold measure of a planet's strength.</dd>
<dt>Ashtakavarga</dt><dd>A points system showing how supportive each sign is.</dd>
<dt>Navamsa (D9)</dt><dd>The ninth-part chart; it refines a planet's real strength.</dd>
<dt>Karaka</dt><dd>A planet that signifies a theme, such as Venus for relationships.</dd>
<dt>Yoga</dt><dd>A named combination of planets that points to a result.</dd></dl>""")]
    return P


CSS = """:root{color-scheme:light dark;
--paper:#F7F3E8;--ivory:#FFFDF7;--parchment:#E9E0CE;--botanical:#3F6B52;--forest:#2F503E;--pine:#203629;
--mint:#ECF0EE;--pistachio:#CFDAD4;--eucalyptus:#A9BCB1;--sage:#6E7E75;--moss:#5C7768;--ink:#26342C;--muted:#58685A;
--clay:#8B5039;--bronze:#9A783E;--focus:#3F6B52;
--serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;--sans:"Avenir Next","Helvetica Neue",Helvetica,Arial,sans-serif;
--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;--r:6px;--gap:16px}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){
--paper:#17211B;--ivory:#1E2A23;--parchment:#26332B;--botanical:#7FB295;--forest:#A9CDB7;--pine:#D5E8DC;
--mint:#243229;--pistachio:#2F4237;--eucalyptus:#4D6657;--sage:#8FA396;--moss:#86A794;--ink:#E8EFE9;--muted:#A5B5AA;
--clay:#D69A82;--bronze:#C9A45F;--focus:#A9CDB7}}
:root[data-theme=dark]{
--paper:#17211B;--ivory:#1E2A23;--parchment:#26332B;--botanical:#7FB295;--forest:#A9CDB7;--pine:#D5E8DC;
--mint:#243229;--pistachio:#2F4237;--eucalyptus:#4D6657;--sage:#8FA396;--moss:#86A794;--ink:#E8EFE9;--muted:#A5B5AA;
--clay:#D69A82;--bronze:#C9A45F;--focus:#A9CDB7}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 var(--sans)}
header,main,footer{max-width:760px;margin:0 auto;padding:0 var(--gap)}
header{max-width:none;background:var(--ivory);border-bottom:2px solid var(--bronze);padding:12px 0}
header>*{max-width:760px;margin-left:auto;margin-right:auto;padding:0 var(--gap)}
h1,h2,h3{font-family:var(--serif);color:var(--forest);font-weight:600;line-height:1.2}
h1{font-size:1.3rem;margin:0}h2{font-size:1.5rem;margin:.6rem 0;padding-top:6px;border-top:2px solid var(--botanical)}
h3{font-size:1.05rem;margin:1.2rem 0 .3rem}
.page{background:var(--ivory);border:1px solid var(--pistachio);border-radius:var(--r);padding:8px var(--gap) var(--gap);overflow-wrap:anywhere}
.js .page{display:none}.js .page.on{display:block}
pre{background:var(--mint);border:1px solid var(--pistachio);border-left:3px solid var(--botanical);padding:10px;border-radius:var(--r);overflow-x:auto;font:.85rem/1.5 var(--mono)}
code{font:.9em var(--mono)}ul{padding-left:1.2rem}.cols{columns:2}dt{font-weight:600;color:var(--forest);margin-top:.5rem}dd{margin:0}
nav.bar{display:flex;gap:8px;align-items:center;justify-content:space-between;margin:12px 0}
button,summary{font:inherit;min-height:44px;padding:0 var(--gap);border:1px solid var(--botanical);background:var(--ivory);color:var(--forest);border-radius:var(--r);cursor:pointer}
button:hover,summary:hover{background:var(--mint)}
button:disabled{opacity:.4;cursor:default}summary{display:inline-flex;align-items:center}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px}#ctr{color:var(--muted)}
details ol{padding-left:1.4rem}details a{color:var(--forest);display:inline-block;padding:6px 0}
a{color:var(--forest)}
svg{width:100%;height:auto;max-width:100%}svg text{fill:var(--ink);font-size:13px;text-anchor:middle}
svg .c{font-size:11px;fill:var(--muted)}svg .e{font-size:10.5px;fill:var(--muted)}svg line,svg path{stroke:var(--sage);stroke-width:1.5}svg .ah{fill:var(--sage);stroke:none}
.n rect{stroke:var(--moss);stroke-width:1}.s rect{fill:var(--pistachio)}.k rect{fill:var(--parchment);stroke-dasharray:4 2}.t rect{fill:var(--mint)}
.k1,.k2,.k3{padding:0 6px;border-radius:4px;border:1px solid var(--moss)}.k1{background:var(--pistachio)}.k2{background:var(--parchment);border-style:dashed}.k3{background:var(--mint)}
.bars{list-style:none;padding:0}.bars li{display:grid;grid-template-columns:1fr auto;gap:2px 8px;margin:6px 0}
.bars i{grid-column:1/-1;height:8px;background:var(--botanical);border-radius:4px}
footer{color:var(--muted);font-size:.85rem;padding-bottom:24px}@media(max-width:480px){.cols{columns:1}}"""

JS = """const P=[...document.querySelectorAll('.page')],c=document.getElementById('ctr'),pv=document.getElementById('pv'),nx=document.getElementById('nx');
let i=0;function go(n,h){i=Math.max(0,Math.min(P.length-1,n));P.forEach((p,k)=>p.classList.toggle('on',k==i));
c.textContent=(i+1)+' / '+P.length;pv.disabled=i==0;nx.disabled=i==P.length-1;if(h!==0)history.replaceState(null,'','#p'+(i+1));scrollTo(0,0)}
const fromHash=()=>go((parseInt((location.hash.match(/p(\\d+)/)||[])[1])||1)-1,0);
pv.onclick=()=>go(i-1);nx.onclick=()=>go(i+1);addEventListener('hashchange',fromHash);
document.querySelectorAll('details a').forEach(a=>a.onclick=e=>{e.preventDefault();go(+a.dataset.n);a.closest('details').open=false});
addEventListener('keydown',e=>{if(e.target.closest('input,textarea,select')||e.altKey||e.ctrlKey||e.metaKey)return;
if(e.key=='ArrowLeft')go(i-1);if(e.key=='ArrowRight')go(i+1)});
let x0=null;addEventListener('touchstart',e=>x0=e.touches[0].clientX,{passive:true});
addEventListener('touchend',e=>{if(x0===null)return;const d=e.changedTouches[0].clientX-x0;x0=null;if(Math.abs(d)>60)go(i+(d<0?1:-1))},{passive:true});
fromHash()"""


def counts(s):
    return {"types": s["types"], "rels": s["rels"], "communities": [list(c) for c in s["communities"]]}


def build():
    s, _ = stats()
    P = pages(s, *registry())
    toc = "".join(f'<li><a href="#p{k}" data-n="{k - 1}">{E(h)}</a></li>' for k, (h, _) in enumerate(P, 1))
    body = "".join(f'<section class="page" id="p{k}" aria-labelledby="h{k}"><h2 id="h{k}">{E(h)}</h2>{b}</section>'
                   for k, (h, b) in enumerate(P, 1))
    meta = E(json.dumps(counts(s), sort_keys=True), quote=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Astrology Consultation User Guide</title><meta name="kg-counts" content="{meta}"><style>{CSS}</style></head>
<body><script>document.documentElement.className='js'</script>
<header><h1>Astrology Consultation: User Guide</h1><details><summary>Contents</summary><ol>{toc}</ol></details></header>
<main><nav class="bar" aria-label="Page navigation"><button id="pv" type="button">&larr; Prev</button>
<span id="ctr" aria-live="polite">1 / {len(P)}</span><button id="nx" type="button">Next &rarr;</button></nav>{body}</main>
<footer>Graph counts were read from the graph file when this guide was built. Left and Right arrow keys, or a swipe, turn the page.</footer>
<script>{JS}</script></body></html>
""", encoding="utf-8")
    print(f"pages={len(P)} nodes={s['nodes']} edges={s['edges']} books={s['books']}")
    print("node types:", s["types"]); print("relations:", s["rels"]); print("communities:", s["communities"])
    print(f"{OUT} {OUT.stat().st_size} bytes")


def check():
    if not OUT.exists(): return ["HTML missing"]
    h = OUT.read_text(encoding="utf-8"); bad = []
    s, titles = stats()
    m = re.search(r'name="kg-counts" content="([^"]*)"', h)
    if not m or json.loads(html.unescape(m.group(1))) != json.loads(json.dumps(counts(s))):
        bad.append("stale: counts differ from graph.json")
    for w in sorted(titles | {"_skill_workspace", "/Users/", "private/"}):
        if re.search(r"(?<![\w/])" + re.escape(w) + r"(?!\w)", h): bad.append(f"forbidden string: {w!r}")
    if re.search(r'<script[^>]+src=|<link[^>]+href=|@import|https?://fonts', h): bad.append("external resource")
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = check(); print("\n".join(bad) or "OK"); sys.exit(1 if bad else 0)
    build()
