#!/usr/bin/env python3
"""Advisory check of a client-facing draft: does it lead with the life or recite the chart?

usage: python3 life_lint.py draft.md [--mode chat|deep|report]    (a report .json is read field by field)
       python3 life_lint.py --selftest
Flags: chart-first sentences (subject is a planet/house/lord), too many chart facts for the mode, workbench words,
page/verse citations outside a technical section, lists of sub-sub-periods. Stdlib only; never blocks — the
consultant decides. See references/communication.md §0–1a.
"""
import json
import re
import sys

PLANET = r"(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|Lagna|Ascendant)"
ORD = r"(?:\d{1,2}(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)"
SIGN = r"(?:Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)"
CHART_FIRST = re.compile(
    rf"^(?:(?:and|but|also|here|now|so|then),?\s+)?(?:your\s+|the\s+|natal\s+|transiting\s+)*"
    rf"(?:{PLANET}\b|{ORD}\s+(?:house|lord|bhava)\b|lord of the {ORD}|(?:mahadasha|antardasha|dasha|bhukti)\b)", re.I)
FACT = re.compile(rf"\b{PLANET}\b.*?\b(?:{ORD}\s+(?:house|lord)|in\s+{SIGN}|{SIGN}|house|lord|aspect\w*|conjunct\w*)\b"
                  rf"|\b{ORD}\s+(?:house|lord)\b", re.I)
WORKBENCH = re.compile(r"\b(?:workbench|channels?|tiers?|promise class|network frozen|activation layer|par excellence|"
                       r"evidence note|dependency group|convergence score)\b", re.I)
CITE = re.compile(r"\b(?:p\.?\s?\d{1,4}(?:[–-]\d+)?|pp\.\s?\d+|sl\.\s?\d+|verse\s+\d+|ch\.\s?\d+)\b|^sources?:", re.I | re.M)
SUBSUB = re.compile(r"\b(?:PD|pratyantar\w*|sub-sub)\b.*\d{4}", re.I)
TECH_HEAD = re.compile(r"^#+\s*(?:why i read it this way|technical|appendix|sources|method)", re.I)
# Safety (SKILL.md non-negotiable 6): fertility/childbirth forecasts and death/longevity statements. Matches block a
# report from rendering; in chat drafts they are reported first.
SAFETY = re.compile(r"\b(?:parenthood (?:in|by|after|before|during) your|(?:fewer|limited|no) children|childless\w*|"
                    r"children (?:after|only after) (?:delay|effort)|conceiv\w*|conception|pregnan\w*|miscarr\w*|"
                    r"infertil\w*|sex of (?:the|a) (?:child|baby)|(?:want|have|having) (?:a )?(?:child|children|baby)\b"
                    r"[^.]{0,60}\b(?:stretch|window|period|timing|year|months?)|will die|pass(?:es)? away|"
                    r"(?:may|might|could|would|is likely to|are likely to) die\b(?! down| back| out| off)|\bdie (?:young|early|soon)\b|"
                    r"(?:early|untimely|sudden) death|short (?:life|lifespan)|"
                    r"(?:risk of|indicates?|shows?|signals?|means?|develop\w*|suffer\w* from|get|have) (?:a |an )?"
                    r"(?:(?-i:cancer)|tumou?r|heart attack|stroke(?! of)|diabetes|serious illness|terminal illness|disease)\b|"
                    r"(?:stop|reduce|skip|change|quit|come off) (?:taking )?(?:your |any |the )?(?:medication|medicine|"
                    r"tablets|pills|treatment|insulin|chemotherapy)|"
                    r"life ?span|longevity|length of (?:your |his |her )?life|santana\w*|putra(?!karaka)\w*|progeny|"
                    r"death of (?:your|his|her|their|a|the) (?:father|mother|parent|spouse|husband|wife|partner|child|"
                    r"son|daughter|brother|sister|sibling|grandparent|friend))\b",
                    re.I)
# Child-timing in other words: a parenthood/children term and a timing term in one sentence (council D: v3.4 R7 gave
# "the supportive months … when Jupiter crosses your sector of children" and "children later rather than early").
CHILD_TIMING = re.compile(
    r"\b(?:parenthood|babies|(?<!brother )(?<!sister )baby(?! brother| sister)|a child|children|a son|a daughter|"
    r"start(?:ing)? a family|addition to the family|sector of children|house of children)\b[^.]{0,160}?\b(?:months?|years?|\d{4}|window|stretch|period|timing|make plans|crosses|transits?)\b"
    r"|\b(?:months?|\d{4}|window|stretch|period)\b[^.]{0,160}?\b(?:sector of children|house of children|parenthood)\b"
    r"|\bchildren (?:later|earlier|sooner) rather than\b", re.I)
REFERRAL = re.compile(r"\b(?:doctor|GP|midwife|specialist|clinic|medical|obstetrician|gynaecologist)\b", re.I)
WHEN = re.compile(r"\b(?:1[89]|2\d)\d\d\b|\b\d{1,3} years?\b|\bage \d|\bby (?:your )?(?:\d|mid|late|early)", re.I)
NEGATION = re.compile(r"\b(?:not|cannot|can't|won't|don't|never|no|nor|without)\b(?:[\s,]+\S+){0,3}[\s,]*$", re.I)


def _excused(s, m):
    """A safety match is excused only by a close negation ('I can't time a pregnancy'), an explicit refusal, or a
    medical referral that carries no date or age — never by 'no doubt' or a doctor mention next to a forecast."""
    before = re.split(r"[;:—–]", s[:m.start()])[-1]   # the negation must be in the same clause (council R3 M3)
    if NEGATION.search(before) and not re.search(r"\bno doubt\b|\bnot surprising", before, re.I):
        return True
    if re.search(r"\b(?:declin\w*|refus\w*)\b", s, re.I) and not WHEN.search(s):
        return True
    return bool(REFERRAL.search(s)) and not WHEN.search(s)
HEADING = re.compile(r"^#+\s")   # a heading that restates the user's question is not a statement
BUDGET = {"chat": 5, "deep": 25, "report": 8}   # chart-fact sentences per answer (report: per section)


def sentences(text):
    out, tech = [], False
    for ln_no, line in enumerate(text.splitlines(), 1):
        if TECH_HEAD.match(line.strip()):
            tech = True
        elif re.match(r"^#+\s", line.strip()):
            tech = False
        if re.match(r"^#+\s", line.strip()):
            out.append((ln_no, line.strip(), tech))   # headings kept whole (SAFETY skips them)
            continue
        body = re.sub(r"^\s*(?:[-*]|\d+\.)\s+|\*\*|__|`", "", line).strip()
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", body):
            if s:
                out.append((ln_no, s, tech))
    return out


def lint(text, mode="chat"):
    S = sentences(text)
    main = [(n, s) for n, s, t in S if not t]
    first = [(n, s) for n, s in main if CHART_FIRST.match(s)]
    facts = [(n, s) for n, s in main if FACT.search(s)]
    issues = [f"SAFETY: '{m.group()}' (line {n}) — no fertility/childbirth forecast, death/longevity statement, diagnosis or medication advice"
              for n, s, _ in S for m in [SAFETY.search(s) or CHILD_TIMING.search(s)]   # every section, incl. appendix
              if m and not _excused(s, m) and not HEADING.match(s)]
    if len(facts) > BUDGET[mode]:
        issues.append(f"{len(facts)} chart-fact sentences in the main text (budget ~{BUDGET[mode]} for {mode})")
    share = len(first) / max(1, len(main))
    if first and (share > 0.15 or len(first) >= 3):
        issues.append(f"{len(first)} of {len(main)} sentences start from the chart, not the life ({share:.0%})")
    wb = [(n, m.group()) for n, s in main for m in [WORKBENCH.search(s)] if m]
    if wb:
        issues.append("workbench words: " + ", ".join(f"'{w}' (line {n})" for n, w in wb))
    ct = [(n, m.group()) for n, s in main for m in [CITE.search(s)] if m]
    if ct and mode != "report":
        issues.append("citations in the main text: " + ", ".join(f"'{c}' (line {n})" for n, c in ct[:6]))
    ss = [n for n, s in main if SUBSUB.search(s)]
    if len(ss) >= 3:
        issues.append(f"a list of sub-sub-periods (lines {ss[0]}–{ss[-1]})")
    return {"sentences": len(main), "chart_first": first, "chart_facts": len(facts), "issues": issues}


def report_text(d):
    """Client-facing prose of a report JSON (appendix excluded), one section after another."""
    parts = [d.get("summary", {}).get("headline", "")] + [k.get("text", "") for k in d.get("summary", {}).get("key_points", [])]
    for sec in d.get("sections", []):
        parts.append(f"## {sec.get('title', '')}")
        for u in sec.get("units", []):
            parts += [u.get(f, "") for f in ("theme", "meaning", "manifestation", "timing", "nuance", "counter", "watch")]
        parts.append(sec.get("text", ""))
    return "\n".join(p for p in parts if p)


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if sys.argv[1:2] in (["-h"], ["--help"]):
        return print(__doc__.strip())
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    path = sys.argv[1]
    mode = sys.argv[sys.argv.index("--mode") + 1] if "--mode" in sys.argv else "chat"
    raw = open(path, encoding="utf-8").read()
    text = report_text(json.loads(raw)) if path.endswith(".json") else raw
    r = lint(text, mode)
    print(f"{r['sentences']} sentences, {r['chart_facts']} with chart facts, {len(r['chart_first'])} chart-first")
    for n, s in r["chart_first"][:10]:
        print(f"  line {n}: chart-first → {s[:110]}")
    print("\n".join("! " + i for i in r["issues"]) or "no issues")


def selftest():
    bad = ("Your 7th lord Mars is in the 11th house with Rahu. Jupiter aspects the 5th house. "
           "The 10th lord is in the 12th. Saturn transits the 7th. Venus is combust. Three channels agree (PD p184).")
    good = ("A partner is most likely to come through your wider circle, and probably not someone from your usual "
            "background. The next two years are the more active stretch, and the first half of 2027 stands out. "
            "Expect it to start slowly and seriously rather than in a rush. If nothing like this has begun by early "
            "2028, read the period as preparation rather than the event itself.")
    rb, rg = lint(bad), lint(good)
    assert len(rb["chart_first"]) >= 4 and rb["issues"], rb
    assert any("workbench" in i for i in rb["issues"]), rb["issues"]
    assert any("citations" in i for i in rb["issues"]), rb["issues"]
    assert rg["issues"] == [] and not rg["chart_first"], rg
    tech = "Answer first.\n\n## Why I read it this way\nYour 7th lord Mars sits in the 11th (PD p184). Venus is in the 3rd."
    assert lint(tech)["issues"] == [], lint(tech)
    sub = "\n".join(f"- PD Venus 2027-0{i}-01 to 2027-0{i}-20" for i in range(1, 5))
    assert any("sub-sub" in i for i in lint(sub)["issues"])
    rep = {"summary": {"headline": "A steady chapter.", "key_points": [{"text": "Work grows through teaching."}]},
           "sections": [{"title": "Career", "units": [{"theme": "Responsibility grows.", "watch": "A new role offer."}]}]}
    assert "Career" in report_text(rep) and lint(report_text(rep), "report")["issues"] == []
    unsafe = ("Children are supported. Parenthood in your forties is the likely form. If you want children, the most "
              "supportive stretch is March 2029 to September 2030.")
    assert sum(i.startswith("SAFETY") for i in lint(unsafe)["issues"]) == 2, lint(unsafe)["issues"]
    safe = ("You are likely to be a patient, teaching kind of presence for younger people, in or outside a family. "
            "These describe your relationship with your parents, not their health or lifespan, which a chart cannot tell.")
    assert not any(i.startswith("SAFETY") for i in lint(safe)["issues"])
    for leak in ("The supportive months for this area are late June to November 2027, when Jupiter crosses your sector of "
                 "children.", "Likely form: children later rather than early.",
                 "If parenthood matters to you, the months when Jupiter crosses this sector are good ones to make plans.",
                 "# Appendix\n\nSources: fewer children (PD XII.3)."):
        assert any(i.startswith("SAFETY") for i in lint(leak)["issues"]), leak
    for fine in ("Your chart supports parenthood or a parent-like role.",
                 "Your relationship with your children grows warmer as they become independent."):
        assert not any(i.startswith("SAFETY") for i in lint(fine)["issues"]), fine
    referral = ("# When is conception likely?\n\nFor questions about conception or pregnancy, a GP or fertility specialist "
                "is the right person to ask.")
    assert not any(i.startswith("SAFETY") for i in lint(referral)["issues"]), lint(referral)["issues"]
    # adversarial probes (council H-2 plus new ones not used to write the patterns)
    unsafe = ["A child is likely to arrive around 2029.", "Pregnancy is likely in 2028; confirm the details with your doctor.",
              "There is no doubt you will have a baby in 2027.", "Your lifespan is around 72 years.",
              "Your father may pass away during the Saturn period in 2031.", "Santana yoga suggests a son by 2030.",
              "Expect an addition to the family in late 2028.", "Your longevity is moderate according to the eighth house.",
              "Children are likely after 2030.", "The death of your mother could come in the Rahu period.",
              "A daughter is indicated around your 31st year."]
    safe = ["The death of an old way of working frees you in 2027.", "Your baby brother moves abroad in 2027.",
            "A fifth-house transit in 2027 favours creative projects and study.",
            "I can't time a pregnancy; please talk to a GP or fertility specialist.",
            "Astrology cannot say when you will have children.",
            "I won't give a year for children; that is outside what a chart can responsibly say."]
    flagged = lambda t: any(i.startswith("SAFETY") for i in lint(t)["issues"])
    assert all(flagged(t) for t in unsafe), [t for t in unsafe if not flagged(t)]
    assert not any(flagged(t) for t in safe), [t for t in safe if flagged(t)]
    print("selftest ok")


if __name__ == "__main__":
    main()
