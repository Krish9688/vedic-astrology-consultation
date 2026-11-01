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
# The same regex runs over all client text of a report, so the verbs kill/sacrifice/capture count only next to an animal word.
_ANIMAL = (r"(?:animals?|birds?|snakes?|wildlife|creatures?|cows?|dogs?|fish|owls?|tortoises?|goats?|chickens?|hens?|cocks?"
           r"|roosters?|pigeons?|doves?|crows?|sheep|rams?|buffal\w+|cobras?|cats?|ox|oxen|deer|monkeys?|rats?(?! race)|mice)")
_SNAKE = r"(?:snakes?|serpents?|cobras?)"
_GAP = r"\W+(?:\w+\W+){0,3}"          # up to three words between two terms
NEVER = re.compile(
    r"\b(?:ivory|tusks?|deer[- ]?skin|snakes? milk|cow'?s?[- ]urine|urine of (?:a |the )?cow|gomutra"
    r"|(?:52|fifty[- ]?two) days|hookah|smok\w*|liquor|cigarettes?|intoxicants?|lioness|monkeys?|rabbits?|mare'?s"
    r"|child[- ]marriages?|bhasm|metal preparations?|gold medicines?|self-?(?:medicat|dos)\w*|private parts|intimate parts"
    r"|no water|without water|placenta|wildlife|chirayata|chiretta|elephants?'?s? milk"
    rf"|milk{_GAP}{_SNAKE}|{_SNAKE}{_GAP}milk|milk (?:of|from) (?:an? |the )?(?:elephant|lion|mare|animals?)"
    rf"|mare{_GAP}milk|milk{_GAP}mango|mango{_GAP}milk"
    rf"|(?:newborn|baby|infant)'?s? face|newborn[^.]{{0,60}}\b(?:days?|avoid|away|not see)\b|\b(?:avoid|away|not see)\b[^.]{{0,60}}newborn"
    r"|(?:avoid|abstain\w* from|refrain\w* from|go without|forgo|not drink\w*|stop drinking) (?:\w+ ){0,2}water[^.]{0,30}days?"
    r"|(?:give|giving) up (?:eating )?meat[^.]{0,60}(?:life|longer|extend)|(?:extend|lengthen)\w* (?:your |the )?life[^.]{0,40}meat"
    rf"|(?:sex\w*|libido|potency){_GAP}(?:medicines?|tonics?|potions?|pills?|cure)"
    r"|wash\w*\W+(?:\w+\W+){0,3}curd|doctors? fill\w* (?:the )?graveyards?"
    r"|(?:avoid|stop|skip|shun|abandon|quit) (?:\w+ ){0,2}(?:doctors?|medical (?:care|treatment|advice))"
    rf"|(?:kill\w*|sacrific\w*|captur\w*|harm\w*|hurt\w*|trap\w*|cag\w+|beat\w*|beating){_GAP}{_ANIMAL}|{_ANIMAL}{_GAP}(?:killed|sacrificed|captured|caged|trapped|harmed|hurt|beaten)"
    r"|protected (?:birds?|animals?|species)|cat'?s? (?:navel|placenta)|marr\w+ (?:off )?(?:a |your )?(?:minor|underage))\b",
    re.I)
# remedy-safety.md §2, the ⚠️ rows: only in a stated safe form
CAUTION = re.compile(r"\b(?:float\w*|rivers?|streams?|drains?|ovens?|fire|burn\w*|fast(?:ing|s)?|pierc\w*|dogs?|bur(?:y|ied)"
                     r"|cremation|iron rod|releas\w*|blacken\w*|grandmother)\b", re.I)
PROCESS = ("The book's process, as its advice and never an obligation: one remedy at a time, for 43 days unbroken, in "
           "daylight, done by the person.")


def never_hits(strings):
    """Never-recommend matches in any client text, not only remedy cards; [] when clean."""
    return sorted({m.group() for t in strings if isinstance(t, str) for m in NEVER.finditer(t)})


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
    assert never_hits(["Offer milk to a serpent", "a calm word"]) == ["milk to a serpent"]
    assert not NEVER.search("A newborn arrives; killing time; capture attention; sacrifice a holiday; Learn new skills with elders") and not CAUTION.search("a driver by the fireplace")
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__.strip())
