# Update one row of sourcemaps/STATUS.md from the validation report.  usage: python3 tools/kg/status.py BPHS_part1 [state]
import os, re, sys
WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
name = sys.argv[1]
state = sys.argv[2] if len(sys.argv) > 2 else None
v = os.path.join(WS, "validation", "sourcemaps", name + ".md")
b = sc = ""
if os.path.exists(v):
    t = open(v).read()
    b = re.search(r"bullets: (\d+)", t).group(1)
    sc = re.search(r"spot-check %: (\d+)", t).group(1) + "%"
    state = state or ("validated+promoted" if "(PASS)" in t and os.path.exists(os.path.join(WS, "sourcemaps", name + ".md")) else "failed")
p = os.path.join(WS, "sourcemaps", "STATUS.md")
L = open(p).read().splitlines()
for i, l in enumerate(L):
    if l.startswith(f"| {name} |"):
        c = [x.strip() for x in l.strip("|").split("|")]
        c[3], c[4], c[5] = state or c[3], b or c[4], sc or c[5]
        L[i] = "| " + " | ".join(c) + " |"
open(p, "w").write("\n".join(L) + "\n")
print(name, state, b, sc)
