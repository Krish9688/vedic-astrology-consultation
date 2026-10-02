# Search the local astrology library index. Every hit carries source id + PDF page for citation.
# usage: python3 search.py "seventh lord" [--src HJH2,PD] [-n 8] [--page SRC:N]
#   query uses SQLite FTS5 syntax: words AND-ed, "exact phrase", a OR b, NEAR(a b, 10), prefix*
#   --page SRC:N prints the full text of one page (to read context around a hit)
import argparse, os, sqlite3, sys

DB = os.environ.get("ASTRO_LIBRARY_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index", "library.sqlite")

ap = argparse.ArgumentParser()
ap.add_argument("query", nargs="?")
ap.add_argument("--src", help="comma-separated source ids")
ap.add_argument("-n", type=int, default=8)
ap.add_argument("--page", help="SRC:N full page text")
a = ap.parse_args()
c = sqlite3.connect(DB)

if a.page:
    s, n = a.page.split(":")
    r = c.execute("select printed, text from pages where src=? and page=?", (s, int(n))).fetchone()
    t = c.execute("select title from sources where id=?", (s,)).fetchone()
    if not r:
        sys.exit(f"no page {a.page}")
    print(f"[{s} {t[0]} | PDF p{n}{' | printed p' + r[0] if r[0] else ''}]\n{r[1]}")
    sys.exit()

if not a.query:
    for row in c.execute("select id, title, author, tradition from sources"):
        print(" | ".join(row))
    sys.exit()

sql = "select src, page, printed, snippet(pages, 3, '[', ']', ' … ', 40) from pages where pages match ?"
args = [a.query]
if a.src:
    ids = a.src.split(",")
    sql += f" and src in ({','.join('?' * len(ids))})"
    args += ids
sql += " order by rank limit ?"
args.append(a.n)
for s, p, pr, snip in c.execute(sql, args):
    print(f"{s} p{p}{' (printed ' + pr + ')' if pr else ''}: {' '.join(snip.split())}\n")
