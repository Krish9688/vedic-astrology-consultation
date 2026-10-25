#!/usr/bin/env python3
"""Advisory check of a client-facing draft: does it lead with the life or recite the chart?

usage: python3 life_lint.py draft.md [--mode chat|deep|report|audit]    (a report .json is read field by field)
--mode audit reads someone else's report (council 6): flags fear, sales, certainty, money and costly-remedy language.
       python3 life_lint.py --selftest
Flags: chart-first sentences (subject is a planet/house/lord), too many chart facts for the mode, workbench words,
page/verse citations outside a technical section, lists of sub-sub-periods. Stdlib only. Advisory for chat and deep
drafts (the consultant decides) with one exception: SAFETY lines are blocking errors when render_report.py checks a
report. The safety patterns are a phrase-list backstop, not proof that a text is safe. See references/communication.md
§0–1a and §6.
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
REFERRAL = re.compile(r"\b(?:doctor|GP|midwife|specialist|clinic|medical|obstetrician|gynaecologist|crisis (?:line|service)|"
                      r"helpline|hotline|emergency (?:services|number)|counsel+or|therapist|psychologist|lawyer|solicitor|"
                      r"financial (?:adviser|advisor|counsel+or))\b", re.I)
# Further verdicts the skill must not give (council 5 R7-2): divorce/separation, infidelity, self-harm, infertility
# verdicts, financial ruin and selling/investing instructions. Same excuses as SAFETY (refusal, dateless referral).
SAFETY_MORE = re.compile(
    r"\b(?:will|would|is going to|are going to|(?:is|are) (?:likely|bound|destined|certain) to)\b[^.;]{0,40}?\b(?:divorc\w*|separat\w*|break up|split up)\b"
    r"|\bend(?:s|ing)? in (?:divorce|separation)\b|\bdivorce (?:is )?(?:likely|certain|indicated|inevitable|coming|in (?:19|20)\d\d)\b"
    r"|\bcheat(?:s|ed|ing)? on (?:you|him|her|them)\b|\bunfaithful\b|\binfidelity\b|\badulter\w*|\b(?:having|has|had|have) an affair\b|\bextra-?marital\b"
    r"|\b(?:will not|won't|may not|might not|not going to) (?:survive|live (?:past|beyond|to see|long|much longer))\b"
    r"|\bsuicid\w*|\bkill (?:your|him|her|them|my)sel(?:f|ves)\b|\bend(?:ing)? (?:your|his|her|their|my) (?:own )?life\b|\bself-harm\w*"
    r"|\bharm(?:ing)? (?:your|him|her|them|my)sel(?:f|ves)\b"
    r"|\b(?:cannot|can't|can not|unable to|won't be able to|will not be able to|will never|never) (?:conceive|get pregnant|become (?:a )?(?:mother|father|parent)|have (?:a |any )?(?:child|children|kids|baby))\b"
    r"|\b(?:lose|losing|will lose) (?:all (?:your|of your) |everything|your (?:house|home|savings|money|job|business)\b)|\bbankrupt\w*|\bfinancial ruin\b|\bgo broke\b"
    r"|\bsell (?:your|the) (?:house|home|property|business|shares|stocks|gold)\b|\b(?:invest|put) (?:all|everything|your savings)\b"
    # Kuja (P4-2): conventions are listed, never a verdict on the person, and never harm to a spouse
    r"|\b(?:you|he|she|they) (?:are|is|'re) (?:not |definitely |clearly )?(?:a )?mang(?:a)?lik\b"
    r"|\b(?:your|his|her|their|the) (?:birth )?chart (?:has|shows|carries|is)(?: a| strong| severe| no)? (?:mang(?:a)?lik|mangal|kuja) ?(?:dosha|dosh)?\b"
    r"|\b(?:mang(?:a)?lik|mangal|kuja) ?(?:dosha|dosh)? (?:will|would|is going to|could|can|may) (?:harm|hurt|endanger|kill|ruin|destroy|delay|break)\b"
    r"|\b(?:will|would|is going to|could|may) (?:harm|hurt|endanger|kill|shorten the life of) (?:your|his|her|their) (?:spouse|husband|wife|partner|marriage)\b"
    r"|\b(?:your|his|her|their) (?:spouse|husband|wife|partner) (?:will|would|is going to) (?:suffer|be harmed|fall ill|die)\b", re.I)
# A negation excuses a match unless it is a verdict about a person ("you cannot conceive", "he will not survive",
# "your partner won't …") — council 5 R7-2; disclaimers ("no infidelity claims", "a chart can't time conception") stay excused.
VERDICT_NEG = re.compile(r"\b(?:you|he|she|they|your (?:\w+ ){0,2}?(?:partner|spouse|husband|wife|father|mother|parents?|child|"
                         r"children|son|daughter|brother|sister|sibling))\s+(?:will |would |may |might |can |could |are |is )?"
                         r"(?:not|never|cannot|can't|can not|won't|will not|unable)\b", re.I)
# "... which a chart cannot tell" / "lifespan is something I cannot predict": a refusal anywhere in a dateless sentence
TELL_REFUSAL = re.compile(r"\b(?:I|we|astrology|(?:a|the|this|no|your) (?:birth )?chart|no one|nobody)\b[^.;]{0,20}?\b(?:cannot|can't|can not|"
                          r"won't|will not|does not|doesn't|do not|don't)\s+(?:tell|predict|say|show|time|forecast|know|answer)\b", re.I)
WHEN = re.compile(r"\b(?:1[89]|2\d)\d\d\b|\b\d{1,3} years?\b|\bage \d|\bby (?:your )?(?:\d|mid|late|early)", re.I)
NEGATION = re.compile(r"\b(?:not|cannot|can't|won't|don't|never|no|nor|without)\b(?:[\s,]+\S+){0,3}[\s,]*$", re.I)


def _excused(s, m):
    """A safety match is excused only by a close negation ('I can't time a pregnancy'), an explicit refusal, or a
    medical referral that carries no date or age — never by 'no doubt' or a doctor mention next to a forecast."""
    before = re.split(r"[;:—–]", s[:m.start()])[-1]   # the negation must be in the same clause (council R3 M3)
    if (NEGATION.search(before) and not VERDICT_NEG.search(before)
            and not re.search(r"\bno doubt\b|\bnot surprising", before, re.I)):
        return True
    if TELL_REFUSAL.search(s) and not WHEN.search(s):
        return True
    if re.search(r"\b(?:declin\w*|refus\w*)\b", s, re.I) and not WHEN.search(s):
        return True
    return bool(REFERRAL.search(s)) and not WHEN.search(s)
# Audit mode (council 6, P3-4): advisory probes for a third-party report; paraphrase-tested, never verbatim vendor text
AUDIT = [
    ("fear", r"\b(?:secret (?:affair|relationship)|hidden (?:romance|affair|relationship)|come to light|(?:will|may|could) be "
             r"(?:exposed|discovered)|hard to diagnose|struggle to identify|chronic illness|danger to (?:your )?life|"
             r"black magic|evil eye|curse[ds]?|(?:enemies|rivals) (?:will|may|could) (?:harm|destroy|ruin)|"
             r"(?:will|may|could) (?:ruin|destroy) your)\b"),
    ("sales", r"\b(?:book (?:a|your|the)\b[^.]{0,20}\b(?:puja|pooja|ritual|homa|havan|consultation)|coupons?|discount|"
              r"limited[- ]time|order now|buy now|energi[sz]ed|certified (?:gem|stone|rudraksha)|"
              r"(?:our|the) (?:expert )?astrologers?|call (?:now|us)|whatsapp)\b"),
    ("certainty", r"(?:\b100 ?%|\bguaranteed\b|\bscientifically proven\b|\bdefinitely will\b|\bno doubt\b|\b\d{1,3}(?:\.\d+)? ?% (?:accura\w*|success|hit rate|correct)|\baccura\w+ (?:of|rate of|is|at) (?:about |around )?\d{1,3} ?%)"),
    ("money", r"\b(?:invest (?:in|your)|(?:buy|sell) (?:shares|stocks|property|gold)|(?:stock|share) market|"
              r"speculat\w*|lottery)\b"),
    ("costly-remedy", r"\b(?:gemstones?|(?:blue|yellow) sapphire|emerald|ruby|diamond|cat'?s eye|hessonite)\b"),
]
AUDIT += [   # Lal Kitab-style remedy wording (LAL-KITAB-ROADMAP §4): check each against remedy-safety.md first
    ("unsafe-remedy", r"\b(?:float\w*|immers\w*|throw\w*|drop\w*|pour\w*)\b[^.]{0,60}\b(?:river|running water|"
                      r"flowing water|stream|sea|drain|canal)\b|\bbur(?:y|ied|ying)\b|\bnose[- ]?(?:piercing|pierced)\b|"
                      r"\bwithout water\b|\b(?:collect|take|accept)\w* money from\b|\bivory\b|\b(?:deer|animal) skin\b|"
                      r"\bmilk to (?:a )?snakes?\b|\b(?:liquor|alcohol)\b"),
    ("donation-check", r"\b(?:donat\w*|give away)\b"),   # X17: never donate the objects of an exalted planet
]
AUDIT = [(cat, re.compile(rx, re.I)) for cat, rx in AUDIT]


def audit(text):
    """(category, line, match) for each probe hit in someone else's report — advisory, never blocking."""
    return [(cat, n, m.group()) for n, s, _ in sentences(text) for cat, rx in AUDIT for m in [rx.search(s)] if m]


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
    issues = [f"SAFETY: '{m.group()}' (line {n}) — no fertility/childbirth forecast, death/longevity, diagnosis or medication "
              "advice, divorce/infidelity verdict, self-harm content without a crisis referral, or financial-ruin/investment call"
              for n, s, _ in S for m in [SAFETY.search(s) or CHILD_TIMING.search(s) or SAFETY_MORE.search(s)]   # every section
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
    if mode == "audit":
        hits = audit(text)
        print("\n".join(f"AUDIT {c}: '{m}' (line {n})" for c, n, m in hits) or "no audit flags")
        return
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
