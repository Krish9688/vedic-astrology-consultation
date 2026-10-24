#!/usr/bin/env python3
"""North and South Indian rasi charts as stdlib SVG (P7-1).

usage: python3 chart_svg.py --selftest
North: fixed houses, house 1 top middle, counted anticlockwise; each house shows its sign number.
South: fixed signs, Pisces top left and Aries beside it, counted clockwise; the lagna cell carries a corner stroke
and 'Asc'. Only signs are drawn (no degrees): the positions table stays the long description.
"""
import sys
from html import escape

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
         "Aquarius", "Pisces"]
ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
        "Rahu": "Ra", "Ketu": "Ke", "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl"}
LAGNA = ("ascendant", "lagna", "asc")
# South grid: (row, col) of each sign, Aries at row 0 col 1, clockwise round the rim
SOUTH = [(0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3), (3, 2), (3, 1), (3, 0), (2, 0), (1, 0), (0, 0)]
# North: label centre of houses 1..12 on a 0..1 square (house 1 is the top diamond, house 2 the triangle to its left)
NORTH = [(.5, .25), (.25, .1), (.1, .25), (.25, .5), (.1, .75), (.25, .9), (.5, .75), (.75, .9), (.9, .75),
         (.75, .5), (.9, .25), (.75, .1)]
SIZE = 300


def placements(positions):
    """appendix.positions rows ({'body', 'sign', ...}) -> (lagna sign index, {sign index: [abbreviations]})."""
    lagna, by_sign = None, {}
    for p in positions:
        body, sign = str(p.get("body", "")).strip(), str(p.get("sign", "")).strip().capitalize()
        if sign not in SIGNS:
            continue
        if body.lower() in LAGNA:
            lagna = SIGNS.index(sign)
        else:
            by_sign.setdefault(SIGNS.index(sign), []).append(ABBR.get(body, body[:2]))
    return lagna, by_sign


def _text(x, y, s, cls="b"):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="middle">{escape(s)}</text>'


def _bodies(cx, cy, names, first="b"):
    rows = [names[i:i + 3] for i in range(0, len(names), 3)]
    top = cy - 7 * (len(rows) - 1)
    return [_text(cx, top + 14 * i + 4, " ".join(r), first if i == 0 and r and r[0] == "Asc" else "b")
            for i, r in enumerate(rows)]


def _svg(body, label, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}" '
            f'role="img" aria-labelledby="ct cd" class="chart"><title id="ct">{escape(label)}</title>'
            f'<desc id="cd">{escape(desc)}</desc><style>line,rect,path{{stroke:#333;stroke-width:1.2;fill:none}}'
            # longhand: WeasyPrint ignores a `font:` shorthand with a weight in SVG <style> (the lagna row vanished, M10)
            '.b{font-family:sans-serif;font-size:12px;fill:#111}.n{font-family:sans-serif;font-size:9px;fill:#777}'
            '.a{font-family:sans-serif;font-size:12px;font-weight:bold;fill:#a33}'
            f'</style>{"".join(body)}</svg>')


def _desc(lagna, by_sign):
    parts = [f"{SIGNS[s]}: {', '.join(n)}" for s, n in sorted(by_sign.items())]
    return f"Lagna {SIGNS[lagna]}. " + ("; ".join(parts) or "no bodies listed") + "."


def north(positions):
    lagna, by_sign = placements(positions)
    if lagna is None:
        return None
    S = SIZE
    m = [f'<rect x="0" y="0" width="{S}" height="{S}"/>', f'<line x1="0" y1="0" x2="{S}" y2="{S}"/>',
         f'<line x1="{S}" y1="0" x2="0" y2="{S}"/>', f'<path d="M{S / 2} 0L{S} {S / 2}L{S / 2} {S}L0 {S / 2}Z"/>']
    for h, (fx, fy) in enumerate(NORTH):
        sign = (lagna + h) % 12
        cx, cy = fx * S, fy * S
        m.append(_text(cx, cy - (24 if h in (0, 3, 6, 9) else 16), str(sign + 1), "n"))
        m += _bodies(cx, cy, (["Asc"] if h == 0 else []) + by_sign.get(sign, []), "a")
    return _svg(m, "North Indian rasi chart", _desc(lagna, by_sign))


def south(positions):
    lagna, by_sign = placements(positions)
    if lagna is None:
        return None
    c = SIZE / 4
    m = [f'<rect x="0" y="0" width="{SIZE}" height="{SIZE}"/>']
    for i in (1, 2, 3):                       # rim cell borders; the 2x2 centre stays open
        m.append(f'<line x1="{c * i}" y1="0" x2="{c * i}" y2="{c}"/><line x1="{c * i}" y1="{3 * c}" x2="{c * i}" '
                 f'y2="{SIZE}"/><line x1="0" y1="{c * i}" x2="{c}" y2="{c * i}"/><line x1="{3 * c}" y1="{c * i}" '
                 f'x2="{SIZE}" y2="{c * i}"/>')
    m.append(f'<rect x="{c}" y="{c}" width="{2 * c}" height="{2 * c}"/>')
    for sign, (row, col) in enumerate(SOUTH):
        x, y = col * c, row * c
        m.append(f'<text x="{x + 4:.1f}" y="{y + 11:.1f}" class="n">{SIGNS[sign][:3]}</text>')
        names = by_sign.get(sign, [])
        if sign == lagna:
            m.append(f'<line x1="{x + c - 16:.1f}" y1="{y:.1f}" x2="{x + c:.1f}" y2="{y + 16:.1f}"/>')
            names = ["Asc"] + names
        m += _bodies(x + c / 2, y + c / 2, names, "a")
    return _svg(m, "South Indian rasi chart", _desc(lagna, by_sign))


def chart(positions, style="north"):
    return (south if style == "south" else north)(positions)


def selftest():
    pos = [{"body": "Ascendant", "sign": "Taurus"}, {"body": "Sun", "sign": "Aries"}, {"body": "Moon", "sign": "Taurus"}]
    lagna, by = placements(pos)
    assert lagna == 1 and by == {0: ["Su"], 1: ["Mo"]}, (lagna, by)
    assert SOUTH[0] == (0, 1) and SOUTH[11] == (0, 0) and len(set(SOUTH)) == 12      # Aries beside Pisces, top row
    assert all(r in (0, 3) or c in (0, 3) for r, c in SOUTH)                          # rim only, centre left empty
    n = north(pos)
    assert 'class="n" text-anchor="middle">2<' in n and 'class="a" text-anchor="middle">Asc Mo<' in n, n
    s = south(pos)
    assert s.count("Asc") == 1 and "Lagna Taurus." in s
    assert north([{"body": "Sun", "sign": "Aries"}]) is None                        # no lagna, no chart
    assert "&lt;x" in north(pos + [{"body": "<x>", "sign": "Leo"}])                 # names are escaped
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__.strip())
