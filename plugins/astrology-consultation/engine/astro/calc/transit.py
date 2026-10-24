"""Transits against a natal chart: Parashari gochara from the natal Moon (Phaladeepika XXVI) with vedha, the transit
planet's condition, the lagna frame shown separately, sade sati, and a dated outlook for a day, week, month or year.
Calculation and rule lookup only: every row names its rule and source; interpretation is the skill's job.

Sources (page-cited source maps, not page-checked): PD XXVI.1-2 (p312: Moon's sign only; good houses), XXVI.3-8
(p313-314, image-checked: vedha pairs; no vedha between Sun and Saturn, Moon and Mercury), XXVI.30-32 (condition);
LOL p362 (lagna frame preferred by some); LOL p363-364 and HPA p130 (sade sati: a lens, never a verdict).
"""
from __future__ import annotations

import datetime as dt

from . import engine as E
from .strength import EXALT, NATURAL, SIGN_LORD, ashtakavarga

GOOD = {"Su": {3, 6, 10, 11}, "Mo": {1, 3, 6, 7, 10, 11}, "Ma": {3, 6, 11}, "Me": {2, 4, 6, 8, 10, 11},
        "Ju": {2, 5, 7, 9, 11}, "Ve": {1, 2, 3, 4, 5, 8, 9, 11, 12}, "Sa": {3, 6, 11}, "Ra": {3, 6, 10, 11},
        "Ke": {3, 6, 10, 11}}                                       # PD XXVI.2; nodes like the Sun
VEDHA = {"Su": {11: 5, 3: 9, 10: 4, 6: 12}, "Mo": {7: 2, 1: 5, 6: 12, 11: 8, 10: 4, 3: 9},
         "Ma": {3: 12, 11: 5, 6: 9}, "Sa": {3: 12, 11: 5, 6: 9}, "Me": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
         "Ju": {2: 12, 11: 8, 9: 10, 5: 4, 7: 3}, "Ve": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 12: 6, 11: 3}}
EXEMPT = {frozenset(("Su", "Sa")), frozenset(("Mo", "Me"))}         # PD XXVI.3-8
SOURCES = {"gochara": "PD XXVI.1-2 (p312): from the natal Moon's sign; good houses per planet",
           "vedha": "PD XXVI.3-8 (p313-314, image-checked): an obstructing planet in the paired house cancels a good "
                    "transit; no vedha Sun-Saturn or Moon-Mercury; HPA p133-134 differs for Mercury and Venus "
                    "(CR-V07): PD's table is used; PD gives no vedha for the nodes",
           "condition": "PD XXVI.30-32: own or exalted sign does no harm even in a bad house; debility or an enemy's "
                        "sign voids a good transit",
           "lagna_frame": "LOL p362: some count transits from the lagna; shown separately, never added to the Moon frame",
           "sade_sati": "LOL p363-364, HPA p130: Saturn in the 12th, 1st or 2nd from the natal Moon; a broad lens that "
                        "needs dasha confluence, never a verdict by itself",
           "vedha_intervals": "PD XXVI.3-8 table as in 'vedha', sampled at the sign changes of Sun, Mars, Mercury, Jupiter, "
                              "Venus and Saturn (engine sky(), local dates): an obstruction holds from the obstructor's or "
                              "the planet's ingress until the next change of either. Moon vedha omitted (the Moon changes "
                              "sign every ~2.3 days; Moon rows are in the day/week outlook)",
           "station_natal": "Convention, not a classical rule: a station of Mercury to Saturn within 3 deg (close) or "
                            "7 deg (wide band) of a natal point, conjunction only; one episode per retrograde loop and "
                            "point, listing both station dates when both fall in the band",
           "chandrashtama": "CRUX p99-100 (Rath, author): the Moon's transit of the 8th sign from the natal Moon is avoided "
                            "when choosing a day; texture only, low weight",
           "tara": "Tara order Janma, Sampat, Vipat, Kshema, Pratyak, Sadhana, Naidhana, Mitra, Parama Mitra (JP2 p407 "
                   "translator note; DEVA2 reader note): count from the birth star, mod 9; daily use is a convention, "
                   "texture only, low weight",
           "trigger": "timing.md §3: gochara, vedha and stations are triggers inside an already activated dasha period "
                      "only, never a prediction on their own (Jupiter touches the 7th on ~68% of days, PRED-F2)",
           "bindus": "BPHS ashtakavarga tables (engine ashtakavarga()): the planet's own BAV and the SAV of the sign it "
                     "transits; transit quality only, never a separate prediction"}
BODIES = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")


def _condition(p, sign):
    if p not in EXALT:
        return None
    ex = int(EXALT[p] // 30)
    if sign == ex or SIGN_LORD[sign] == p:
        return "own or exalted sign"
    if sign == (ex + 6) % 12:
        return "debilitated"
    if SIGN_LORD[sign] in NATURAL[p][1]:
        return "enemy's sign"
    return None


def gochara(jd, moon_sign, asc_sign, node="mean", av=None):
    """One row per transiting body: houses from the Moon and lagna, PD reading with vedha and condition; with `av`
    (ashtakavarga() of the natal chart) also the bindus of the transited sign."""
    T = E.positions(jd, node)
    sign = {p: int(T[p]["lon"] // 30) for p in BODIES}
    hm = {p: (sign[p] - moon_sign) % 12 + 1 for p in BODIES}
    rows = []
    for p in BODIES:
        h, good, cond = hm[p], hm[p] in GOOD[p], _condition(p, sign[p])
        by = []
        if good and p in VEDHA and h in VEDHA[p]:
            by = [q for q in BODIES[:7] if q != p and hm[q] == VEDHA[p][h] and frozenset((p, q)) not in EXEMPT]
        if good:
            reading = ("favourable house, obstructed by vedha from " + ",".join(by) if by else
                       "favourable house, voided by " + cond if cond in ("debilitated", "enemy's sign") else
                       "favourable house")
        else:
            reading = "unfavourable house" + (", no harm (own or exalted sign)" if cond == "own or exalted sign" else "")
        rows.append({"planet": p, "sign": E.SIGNS[sign[p]], "retro": T[p]["retro"], "house_from_moon": h,
                     "house_from_lagna": (sign[p] - asc_sign) % 12 + 1, "condition": cond, "vedha_by": by,
                     "pd_reading": reading}
                    | ({"bav": av["bav"][p][sign[p]], "sav": av["sav"][sign[p]]} if av and p in av["bav"] else {}))
    return rows


def sade_sati(saturn_sign, moon_sign):
    h = (saturn_sign - moon_sign) % 12 + 1
    return {12: "first phase (Saturn 12th from the Moon)", 1: "peak (Saturn over the natal Moon sign)",
            2: "last phase (Saturn 2nd from the Moon)"}.get(h)


def _ord(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def vedha_intervals(sign0, changes, moon_sign, s0, s1):
    """Obstruction intervals of favourable transits. `sign0`: sign index of Su,Ma,Me,Ju,Ve,Sa at s0; `changes`: sky()
    sign_changes (date-sorted); dates are ISO local dates. Between consecutive change dates all signs are fixed, so
    each segment is evaluated once and equal consecutive states merge. -> [{planet, house, by:{q: house}, start, end}]"""
    sg, bounds, open_, out = dict(sign0), [s0] + sorted({c["date"] for c in changes}) + [s1], {}, []
    for i, a in enumerate(bounds[:-1]):
        for c in changes:
            if c["date"] == a and i and c["planet"] in sg:
                sg[c["planet"]] = E.SIGNS.index(c["to"])
        if a == bounds[i + 1]:
            continue
        hm = {q: (x - moon_sign) % 12 + 1 for q, x in sg.items()}
        for p in sg:
            h = hm[p]
            by = {q: hm[q] for q in sg if q != p and h in GOOD[p] and h in VEDHA[p] and hm[q] == VEDHA[p][h]
                  and frozenset((p, q)) not in EXEMPT}
            key = (h, tuple(by)) if by else None
            if open_.get(p, (0,))[0] == key and key:
                open_[p][1]["end"] = bounds[i + 1]
            elif key:
                open_[p] = (key, {"planet": p, "house": h, "by": by, "start": a, "end": bounds[i + 1]})
                out.append(open_[p][1])
            else:
                open_.pop(p, None)
    return out


ORBS = (3, 7)                                                       # close / wide band, degrees (convention)


def station_episodes(stations, lon_of, natal):
    """Stations of one planet's retrograde loop near natal points. `stations`: sky() stations (date-sorted),
    `lon_of(planet, date)` its longitude, `natal`: {name: lon}. A retrograde station and the next direct station of the
    same planet that both lie within the wide band of the same natal point form ONE episode."""
    loops, out = [], []
    for st in stations:
        mine = [lp for lp in loops if lp[0]["planet"] == st["planet"]]      # sky() interleaves planets
        if st["station"] == "retrograde" or not mine or len(mine[-1]) > 1:
            loops.append([st])
        else:
            mine[-1].append(st)
    for loop in loops:
        for n, nl in natal.items():
            near = [(abs((lon_of(s["planet"], s["date"]) - nl + 180) % 360 - 180), s) for s in loop]
            near = [(d, s) for d, s in near if d <= ORBS[1]]
            if near:
                o = min(d for d, _ in near)
                out.append({"planet": loop[0]["planet"], "natal": n, "orb": round(o, 2),
                            "band": "close" if o <= ORBS[0] else "wide",
                            "stations": [{"date": s["date"], "station": s["station"]} for _, s in near]})
    return out


PERIODS = {"day": 1, "week": 7, "month": 30, "quarter": 92, "year": 365}
TARAS = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana", "Naidhana", "Mitra", "Parama Mitra"]
FAST = {"Su", "Mo", "Ma", "Me", "Ve"}
# P7-2: event-level factors can carry a dated statement; texture is low weight; the backdrop frames both
EVENT_KINDS = {"contact", "station_natal", "sade_sati"}      # a bare station is the same for everyone: texture
TEXTURE_KINDS = {"moon", "tara", "chandrashtama", "station"}


def _layer(kind, planet=None):
    if kind in EVENT_KINDS or (kind == "ingress" and planet not in FAST):
        return "event"
    if kind in TEXTURE_KINDS or kind == "ingress":
        return "texture"
    return "backdrop"


def texture(add, t0, t1, tz, node, moon_sign, natal_moon):
    """Chandrashtama spans (Moon in the 8th sign from the natal Moon, 2-hour steps) and the Moon's tara from the birth
    star at each local noon. Low weight: colour inside a period, never an event."""
    span, t = None, t0
    while t < t1:                                  # a span still open at the end is closed at the window's end
        in8 = int(E.positions(E.jd_of(t), node)["Mo"]["lon"] // 30) == (moon_sign + 7) % 12
        last = t + dt.timedelta(hours=2) >= t1
        local = (t + dt.timedelta(hours=tz)).strftime("%Y-%m-%d %H:00")
        if in8 and span is None:
            span = local
        if span and (not in8 or last):
            end = local if not in8 else (t1 + dt.timedelta(hours=tz)).strftime("%Y-%m-%d %H:00")
            add("chandrashtama", f"Moon in the 8th sign from the natal Moon ({E.SIGNS[(moon_sign + 7) % 12]})"
                + ("; continues past the period" if in8 else ""), f"{span} to {end}", SOURCES["chandrashtama"])
            span = None
        t += dt.timedelta(hours=2)
    birth, days, d = int(natal_moon // (360 / 27)), {}, t0 + dt.timedelta(hours=12)
    while d < t1:
        nak = int(E.positions(E.jd_of(d), node)["Mo"]["lon"] // (360 / 27))
        days[(d + dt.timedelta(hours=tz)).date().isoformat()] = TARAS[(nak - birth) % 27 % 9]
        d += dt.timedelta(days=1)
    hard = [k for k, v in days.items() if v in ("Vipat", "Pratyak", "Naidhana")]
    add("tara", f"Moon's tara from the birth star: Vipat, Pratyak or Naidhana on {len(hard)} of {len(days)} days",
        f"{min(days)} to {max(days)}", SOURCES["tara"], days=days)


def outlook(c, start, period, tz, yogini_rows=None, node="mean"):
    """Dated, chart-specific factors for a period beginning on local date `start`. `c` is engine.compute output."""
    days = PERIODS[period]
    t0 = dt.datetime.combine(start, dt.time()) - dt.timedelta(hours=tz)
    t1 = t0 + dt.timedelta(days=days)
    s0, s1 = start.isoformat(), (start + dt.timedelta(days=days)).isoformat()
    moon_sign, asc_sign = int(c["bodies"]["Mo"]["lon"] // 30), int(c["bodies"]["Asc"]["lon"] // 30)
    factors, av = [], c.get("ashtakavarga") or ashtakavarga(c)

    def add(kind, text, when, source, **data):
        factors.append({"id": f"F{len(factors) + 1}", "kind": kind, "fact": text, "when": when, "source": source,
                        **data, "layer": _layer(kind, data.get("planet"))})

    for md in c["vimshottari"]:
        for ad in md["sub"]:
            for pd in ad["sub"]:
                if pd["start"] < s1 and pd["end"] > s0:
                    add("dasha", f"Vimshottari {md['lord']}-{ad['lord']}-{pd['lord']}", f"{pd['start']} to {pd['end']}",
                        "Vimshottari (BPHS ch. 46), engine periods", lords=[md["lord"], ad["lord"], pd["lord"]])
    for y in yogini_rows or []:
        if y["start"] < s1 and y["end"] > s0:
            add("dasha", f"Yogini {y['yogini']} ({y['lord']})", f"{y['start']} to {y['end']}",
                "Yogini (BPHS ch. 46 sl. 195-200), secondary dasha", lords=[y["lord"]])
    for r in gochara(E.jd_of(t0), moon_sign, asc_sign, node, av):
        if r["planet"] != "Mo" or days > 7:
            add("gochara", f"{r['planet']} in {r['sign']}: {r['house_from_moon']} from the Moon, "
                f"{r['house_from_lagna']} from the lagna - {r['pd_reading']}"
                + (f" (bindus: own {r['bav']}, SAV {r['sav']})" if "bav" in r else ""), f"at {s0}",
                SOURCES["gochara"] + "; " + SOURCES["vedha"] + ("; " + SOURCES["bindus"] if "bav" in r else ""), **r)
    sky = E.sky(t0, t1, node, tz)
    ss = sade_sati(int(E.positions(E.jd_of(t0), node)["Sa"]["lon"] // 30), moon_sign)
    if ss:
        add("sade_sati", f"Sade sati: {ss}", f"at {s0}", SOURCES["sade_sati"])
    for ch in sky["sign_changes"]:
        add("ingress", f"{ch['planet']} moves {ch['from']} -> {ch['to']} "
            f"({(E.SIGNS.index(ch['to']) - moon_sign) % 12 + 1} from the Moon)", ch["date"], "engine sky()",
            planet=ch["planet"], house_from_moon=(E.SIGNS.index(ch["to"]) - moon_sign) % 12 + 1,
            house_from_lagna=(E.SIGNS.index(ch["to"]) - asc_sign) % 12 + 1)
        if ch["planet"] == "Sa":
            new = sade_sati(E.SIGNS.index(ch["to"]), moon_sign)
            add("sade_sati", f"Sade sati {'now: ' + new if new else 'ends'}", ch["date"], SOURCES["sade_sati"])
    lon_of = lambda p, d: E.positions(E.jd_of(dt.datetime.fromisoformat(d) + dt.timedelta(hours=12 - tz)), node)[p]["lon"]
    for st in sky["stations"]:
        sg = int(lon_of(st["planet"], st["date"]) // 30)
        add("station", f"{st['planet']} turns {st['station']}", st["date"], "engine sky()", planet=st["planet"],
            house_from_moon=(sg - moon_sign) % 12 + 1, house_from_lagna=(sg - asc_sign) % 12 + 1)
    natal = {n: b["lon"] for n, b in c["bodies"].items() if n not in ("Ra", "Ke")}
    T0 = E.positions(E.jd_of(t0), node)
    for v in vedha_intervals({p: int(T0[p]["lon"] // 30) for p in ("Su", "Ma", "Me", "Ju", "Ve", "Sa")},
                             sky["sign_changes"], moon_sign, s0, s1):
        add("vedha", f"{v['planet']}'s favourable {_ord(v['house'])} obstructed by vedha from "
            + ", ".join(f"{q} in the {_ord(h)}" for q, h in v["by"].items())
            + ("; obstruction ends on the end date" if v["end"] < s1 else "; continues past the period"),
            f"{v['start']} to {v['end']}", SOURCES["vedha_intervals"], **v)
    for ep in station_episodes(sky["stations"], lon_of, natal):
        add("station_natal", f"{ep['planet']} stations ({', '.join(x['station'] + ' ' + x['date'] for x in ep['stations'])}) "
            f"{ep['orb']} deg from natal {ep['natal']} ({ep['band']} band, orb a convention)",
            f"{ep['stations'][0]['date']} to {ep['stations'][-1]['date']}", SOURCES["station_natal"], **ep)
    for ct in E.contacts(t0, days / 30.44, natal, node, tz):
        if s0 <= ct["date"] < s1:
            add("contact", f"transit {ct['transit']} {ct['aspect']} natal {ct['natal']} ({ct['direction']})",
                ct["date"], "exact contact of a slow planet with a natal point (engine contacts())",
                transit=ct["transit"], natal=ct["natal"], aspect=ct["aspect"])
    if days <= 7:                                                   # the Moon's own transit, sign by sign
        t, prev = t0, None
        while t < t1:
            r = next(x for x in gochara(E.jd_of(t), moon_sign, asc_sign, node) if x["planet"] == "Mo")
            if r["sign"] != prev:
                add("moon", f"Moon in {r['sign']}: {r['house_from_moon']} from the natal Moon - {r['pd_reading']}",
                    (t + dt.timedelta(hours=tz)).strftime("%Y-%m-%d %H:00"), SOURCES["gochara"], **r)
                prev = r["sign"]
            t += dt.timedelta(hours=2)
    else:                                                           # texture for a month or longer (P7-2)
        texture(add, t0, t1, tz, node, moon_sign, c["bodies"]["Mo"]["lon"])
    return {"period": period, "from": s0, "to": s1, "factors": factors, "sources": SOURCES,
            "note": "Chart-specific calculated facts and rule lookups only. " + SOURCES["trigger"] + ". A written horoscope must name the factor "
                    "ids it uses; a period with few factors is a quiet period, not a reason for generic text."}
