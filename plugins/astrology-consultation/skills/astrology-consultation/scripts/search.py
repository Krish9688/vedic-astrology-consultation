# Search the local astrology library index. Every hit carries source id + PDF page for citation.
# usage: python3 search.py "seventh lord" [--src HJH2,PD] [-n 8] [--page SRC:N]
#   query uses SQLite FTS5 syntax: words AND-ed, "exact phrase", a OR b, NEAR(a b, 10), prefix*
#   --page SRC:N prints the full text of one page (to read context around a hit)
import argparse, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import knowledge_file  # noqa: E402
DB = knowledge_file("ASTRO_LIBRARY_DB", os.path.join("index", "library.sqlite"))

ap = argparse.ArgumentParser()
ap.add_argument("query", nargs="?")
ap.add_argument("--src", help="comma-separated source ids")
ap.add_argument("-n", type=int, default=8)
ap.add_argument("--page", help="SRC:N full page text")
a = ap.parse_args()
if not os.path.exists(DB):
    sys.exit(f"Book index not found at {DB}. It exists only on the machine where it was built; "
             "set ASTRO_LIBRARY_DB or answer without page retrieval and say so.")
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

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
try:
    rows = c.execute(sql, args).fetchall()
except sqlite3.OperationalError as e:
    sys.exit(f"Query syntax not understood by the index ({e}). Put phrases in double quotes, use AND/OR in capitals, "
             "and avoid bare punctuation, e.g. '\"tawny eyes\" OR honey'.")
for s, p, pr, snip in rows:
    print(f"{s} p{p}{' (printed ' + pr + ')' if pr else ''}: {' '.join(snip.split())}\n")
