#!/usr/bin/env python3
"""Lal Kitab remedy cards for reports (REP-X7). Public since 3.7 (owner decision 2026-10-25); the never-recommend and caution rules stay in force.

usage: python3 lk_remedies.py --selftest
A report may carry `remedies` (cards) only with `remedies_requested: true` (remedy-safety.md §1: only when asked).
Card: {planet, house (Lal Kitab chart), remedy, safety: "low-risk"|"caution", safe_form (caution only), source,
dispute?}. A card without a safety class, a caution card without its safe form, a never-recommend item, or a
caution-type item marked low-risk fails. Rendering adds the book's process as advice and "no efficacy established";
source locators go to the appendix.
"""
import re
import sys
from html import escape

SAFETY = {"low-risk": "Low-risk traditional practice", "caution": "Caution: offered only in its safe form"}
# remedy-safety.md §2, the ⛔ rows (KB and LK1952): never recommended, whatever the card says
NEVER = re.compile(r"\b(?:ivory|tusks?|deer[- ]?skin|milk (?:to|for) (?:a )?snakes?|snakes? milk|newborn|52 days|cow[- ]urine"
                   r"|hookah|smok\w*|liquor|cigarettes?|intoxicants?|lioness|monkeys?|rabbits?|mare'?s|child marriage|bhasm"
                   r"|metal preparations?|gold medicines?|self-?medicat\w*|private parts|no water|without water|placenta"
                   r"|wildlife|captur\w*|kill\w*|sacrific\w*)\b", re.I)
# remedy-safety.md §2, the ⚠️ rows: only in a stated safe form
CAUTION = re.compile(r"\b(?:float\w*|rivers?|streams?|drains?|ovens?|fire|burn\w*|fast(?:ing|s)?|pierc\w*|dogs?|bur(?:y|ied)"
                     r"|cremation|iron rod|releas\w*|blacken\w*|grandmother)\b", re.I)
PROCESS = ("The book's process, as its advice and never an obligation: one remedy at a time, for 43 days unbroken, in "
           "daylight, done by the person.")


def card_checks(r):
    """Errors for the remedy cards of report `r`."""
    cards, errs = r.get("remedies") or [], []
    if cards and r.get("remedies_requested") is not True:
        errs.append("remedy cards without remedies_requested: true (remedies only when the person asked)")
    for i, c in enumerate(cards):
        name = f"remedy card {i + 1} ({c.get('planet', '?')} in {c.get('house', '?')})"
        text = " ".join(str(c.get(k, "")) for k in ("remedy", "safe_form"))
        for k in ("planet", "house", "remedy", "source"):
            if not c.get(k):
                errs.append(f"{name} has no {k}")
        if c.get("safety") not in SAFETY:
            errs.append(f"{name} has no safety class (low-risk or caution, remedy-safety.md §2)")
        if m := NEVER.search(text):
            errs.append(f"{name} matches a never-recommend item ('{m.group()}', remedy-safety.md §2)")
        if CAUTION.search(c.get("remedy", "")) and c.get("safety") == "low-risk":
            errs.append(f"{name} is a caution-type remedy marked low-risk")
        if c.get("safety") == "caution" and not c.get("safe_form"):
            errs.append(f"{name} is caution class but gives no safe form")
        if not isinstance(c.get("house"), int) or not 1 <= c["house"] <= 12:
            errs.append(f"{name}: house must be 1-12")
    return errs


def cards_html(r):
    """(section, appendix) HTML; empty strings unless the person asked and cards exist."""
    cards = r.get("remedies") or []
    if not cards or r.get("remedies_requested") is not True:
        return "", ""
    out = ['<h2 id="remedies">Remedies you asked about (Lal Kitab)</h2><p class="note">Traditional practices; no efficacy '
           'is established and none replaces medical, legal or financial help. ' + escape(PROCESS) + "</p>"]
    for c in cards:
        out.append('<div class="unit"><h3>' + escape(f"{c['planet']} in house {c['house']} (Lal Kitab chart)") + "</h3>"
                   f'<div class="basis">{escape(SAFETY[c["safety"]])} · Lal Kitab</div><dl>'
                   f"<dt>Remedy</dt><dd>{escape(c['safe_form'] if c['safety'] == 'caution' else c['remedy'])}</dd>"
                   + (f"<dt>Sources differ</dt><dd>{escape(c['dispute'])}</dd>" if c.get("dispute") else "")
                   + "<dt>Evidence</dt><dd>No efficacy established.</dd></dl></div>")
    src = "<h3>Remedy sources</h3><ul>" + "".join(
        f"<li>{escape(c['planet'])} in house {c['house']}: {escape(c['source'])}</li>" for c in cards) + "</ul>"
    return "".join(out), src


def selftest():
    ok = {"planet": "Jupiter", "house": 2, "remedy": "Serve elders and teachers", "safety": "low-risk", "source": "KB p107"}
    r = {"remedies_requested": True, "remedies": [ok]}
    assert card_checks(r) == [] and "No efficacy established" in cards_html(r)[0] and "KB p107" in cards_html(r)[1]
    assert "KB p107" not in cards_html(r)[0]                                        # locators only in the appendix
    assert any("remedies_requested" in e for e in card_checks({"remedies": [ok]}))
    assert cards_html({"remedies": [ok]}) == ("", "")
    assert any("safety class" in e for e in card_checks({"remedies_requested": True, "remedies": [dict(ok, safety=None)]}))
    assert any("never-recommend" in e for e in card_checks({"remedies_requested": True,
                                                            "remedies": [dict(ok, remedy="Offer milk to snakes")]}))
    float_ = dict(ok, remedy="Float coconut in a river")
    assert any("marked low-risk" in e for e in card_checks({"remedies_requested": True, "remedies": [float_]}))
    safe = dict(float_, safety="caution", safe_form="Give a coconut to a temple instead")
    assert card_checks({"remedies_requested": True, "remedies": [safe]}) == []
    assert "temple" in cards_html({"remedies_requested": True, "remedies": [safe]})[0]
    assert "river" not in cards_html({"remedies_requested": True, "remedies": [safe]})[0]  # only the safe form shows
    assert not NEVER.search("Learn new skills with elders") and not CAUTION.search("a driver by the fireplace")
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__.strip())
