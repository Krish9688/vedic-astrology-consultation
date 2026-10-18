"""Report identity gate (council 6, P1-1): does a report's printed birth data belong to a given person?

extract_fields(text) reads the labelled fields a report prints (name, date/time/place of birth, ascendant, Moon sign,
generation date). match(profile, fields) compares them with the person's profile and returns a verdict:
  BOUND        date, time and place match (an ambiguous dd/mm date also needs the ascendant and Moon sign to match)
  PROVISIONAL  no conflict, but something is missing or the name differs: the owner must review before use
  UNBOUND      no birth date printed (a name or a Moon sign alone identifies no one)
  REJECT       any birth field conflicts: the report belongs to someone else
admit(result, reviewed) is the gate itself. Results name fields and statuses only, never the values, so they are safe
to print or log.
"""
import datetime as dt
import re

SIGNS = {"Aries": "mesha mesh", "Taurus": "vrishabha vrishabh vrishab vrisha vrushabh", "Gemini": "mithuna mithun",
         "Cancer": "karka kark karkata", "Leo": "simha simh singh", "Virgo": "kanya", "Libra": "tula",
         "Scorpio": "vrishchika vrischika vrishchik vrushchik", "Sagittarius": "dhanu dhanus",
         "Capricorn": "makara makar", "Aquarius": "kumbha kumbh", "Pisces": "meena meen mina"}
_SIGN = {w: s for s, ws in SIGNS.items() for w in ws.split() + [s.lower()]}
MONTHS = {m: i + 1 for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}
_DATE = (r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\.?,?\s+\d{4}|"
         r"[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}")
_LABEL = {
    "name": r"(?:native(?:'s)?\s+)?name",
    "date": r"date\s+of\s+birth|birth\s*date|d\.?o\.?b\.?",
    "time": r"time\s+of\s+birth|birth\s*time|t\.?o\.?b\.?",
    "place": r"place\s+of\s+birth|birth\s*place|p\.?o\.?b\.?",
    "lagna": r"ascendant(?:\s*/\s*lagna)?|lagna",
    "moon_sign": r"moon\s+sign(?:\s*/\s*rashi)?|janma\s+rashi|rashi|rasi",
    "generated": r"(?:report\s+)?generated\s+on|report\s+date|date\s+of\s+report|prepared\s+on",
}
BIRTH = ("date", "time", "place", "lagna", "moon_sign")


def _dates(s):
    """Every valid ISO date a printed date can mean (dd/mm and mm/dd both kept when both are valid)."""
    s, out = s.strip().lower(), set()
    nums = [int(x) for x in re.findall(r"\d+", s)]
    word = re.search(r"[a-z]{3,}", s)
    if word and word.group()[:3] in MONTHS:
        cands = [(nums[-1], MONTHS[word.group()[:3]], nums[0])]
    elif re.match(r"\d{4}-", s):
        cands = [tuple(nums)]
    else:
        cands = [(nums[2], nums[1], nums[0]), (nums[2], nums[0], nums[1])]
    for y, m, d in cands:
        try:
            out.add(dt.date(y, m, d).isoformat())
        except ValueError:
            pass
    return sorted(out)


def _time(s):
    m = re.match(r"(\d{1,2})[:.](\d{2})(?::\d{2})?\s*([ap])?\.?m?\.?", s.strip(), re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").lower()
    if ap and not 1 <= h <= 12:
        return None                  # "24:00 AM" is not a clock time
    h = h % 12 + (12 if ap == "p" else 0) if ap else h
    return f"{h:02d}:{mi:02d}" if h < 24 and mi < 60 else None


def extract_fields(text):
    """Labelled fields printed in a report; absent fields are left out. A birth field printed with a value that cannot
    be read is listed in "unparsed"; one printed more than once with different values in "repeated" (a report that
    covers two people, e.g. a compatibility report). The first readable value of each field is used."""
    pats = {"date": rf"({_DATE})", "generated": rf"({_DATE})",
            "time": r"(\d{1,2}[:.]\d{2}(?::\d{2})?\s*(?:[ap]\.?m\.?)?)", "lagna": r"([A-Za-z]+)", "moon_sign": r"([A-Za-z]+)"}
    read = {"date": _dates, "generated": _dates, "time": _time, "lagna": lambda v: _SIGN.get(v.lower()),
            "moon_sign": lambda v: _SIGN.get(v.lower())}
    out, unparsed, repeated = {}, [], []
    for key, lab in _LABEL.items():
        if key in pats:
            sep = r"\s*[:\-]\s*" if key in ("lagna", "moon_sign") else r"\s*[:\-]?\s*"
            raw = [m.group(1) for m in re.finditer(rf"(?im)^\W*(?:{lab}){sep}{pats[key]}", text)]
            vals = [read[key](r) for r in raw]
            bad = not all(vals)
            if key in ("date", "time") and not raw and re.search(rf"(?im)^\W*(?:{lab})\s*[:\-]?\s*\d", text):
                bad = True           # a value is printed but in no format this gate can read
        else:                        # same or next line (PDF tables print the value under the label)
            vals = [m.group(1).strip() for m in re.finditer(rf"(?im)^\W*(?:{lab})[ \t]*(?:[:\-][ \t]*|\n[ \t]*)(\S[^\n]*)", text)]
            bad = False
        vals = [v for v in vals if v]
        if bad and key in BIRTH:
            unparsed.append(key)
        if vals:
            out[key] = vals[0]
            if key != "generated" and len({tuple(v) if isinstance(v, list) else v for v in vals}) > 1:
                repeated.append(key)
    if unparsed:
        out["unparsed"] = unparsed
    if repeated:
        out["repeated"] = repeated
    return out


def _norm(s):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def _minutes(t):
    h, m = t.split(":")[:2]
    return int(h) * 60 + int(m)


def match(profile, fields, tolerance_min=2):
    """Verdict for `fields` (from extract_fields) against `profile` (name, date, time, place, place_aliases, lagna,
    moon_sign). Never returns the values themselves."""
    st, why = {}, []
    if "date" in fields:
        st["date"] = "match" if profile["date"] in fields["date"] else "conflict"
    if "time" in fields:
        st["time"] = "match" if abs(_minutes(fields["time"]) - _minutes(profile["time"])) <= tolerance_min else "conflict"
    if "place" in fields:
        names = [_norm(p) for p in [profile["place"], *profile.get("place_aliases", [])]]
        here = f" {_norm(fields['place'])} "          # whole words only: "Pune" is not "Punekar"
        st["place"] = "match" if any(n and f" {n} " in here for n in names) else "conflict"
    for k in ("lagna", "moon_sign"):
        if k in fields and profile.get(k):
            st[k] = "match" if fields[k] == profile[k] else "conflict"
    if "name" in fields:
        st["name"] = "match" if _norm(fields["name"]) == _norm(profile["name"]) else "conflict"
    for k in fields.get("unparsed", []):
        st.setdefault(k, "unparsed")
    for k in ("name", *BIRTH):
        st.setdefault(k, "missing")
    ambiguous = len(fields.get("date", [])) > 1
    conflicts = [k for k in BIRTH if st[k] == "conflict"]
    if conflicts:
        verdict = "REJECT"
        why.append("printed " + ", ".join(conflicts) + " differ(s) from the profile: this report is someone else's")
    elif st["date"] == "missing":
        verdict = "UNBOUND"
        why.append("no birth date printed: a name or a sign alone identifies no one")
    else:
        verdict = "BOUND"
        for k in ("time", "place"):
            if st[k] == "missing":
                verdict = "PROVISIONAL"
                why.append(f"{k} of birth not printed")
        if ambiguous and not (st["lagna"] == st["moon_sign"] == "match"):
            verdict = "PROVISIONAL"
            why.append("printed date is ambiguous (dd/mm or mm/dd) and no ascendant and Moon sign confirm it")
        for k in [k for k in BIRTH if st[k] == "unparsed"]:
            verdict = "PROVISIONAL"
            why.append(f"{k} of birth printed but unreadable")
        if fields.get("repeated"):
            verdict = "PROVISIONAL"
            why.append("report prints more than one value for " + ", ".join(fields["repeated"]) +
                       ": it may cover more than one person")
        if st["name"] == "conflict":
            verdict = "PROVISIONAL"
            why.append("name differs from the profile although the birth data match")
    return {"verdict": verdict, "fields": st, "reasons": why, "ambiguous_date": ambiguous}


def admit(result, reviewed=False):
    """May this report feed the person's profile? BOUND yes; PROVISIONAL only after an explicit owner review;
    UNBOUND and REJECT never (no flag overrides them)."""
    return result["verdict"] == "BOUND" or (result["verdict"] == "PROVISIONAL" and reviewed is True)
