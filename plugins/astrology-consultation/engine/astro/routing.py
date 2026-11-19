"""Routing manifest: the one source for which skill reference files a question loads. `service.analyze_question` reads it;
tests/test_routing_manifest.py checks SKILL.md's workflow and topic table against it. Edition-neutral (no Lal Kitab):
edition-specific routing stays in SKILL.md."""

ALWAYS = ["SKILL.md", "references/consultation-reasoning.md", "references/inputs.md", "references/question-trees.md",
          "references/synthesis-method.md", "references/communication.md", "references/qc.md"]
TIMING = "references/timing.md"   # added when the question asks "when"
TIMING_RX = (r"\bwhen (?:will|am|is|are|do|does|did|can|should|would|might|could)\b|\bwhen\s*(?:[?.,;!]|$)|\bhow (?:long|soon)\b|next (?:\d+|two|three|four|five|ten) |next (?:week|month|year)\b|coming (?:week|month)|\bthis decade|\bwithin (?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a few) (?:days?|weeks?|months?|years?)|"
            r"\b(?:in|by|during|before|after|until) (?:19|20)\d\d\b|this (?:week|month)|this year|coming year|next year|soon|month|period|dasha|timing")
REFUSAL = ("Health and death are not read in this practice. Such predictions can harm the reader and are not good for their "
           "health. I can help with another area of your life instead.")
# health, illness, surgery, longevity and death questions are refused, never routed to a topic file (owner rule 2026-11-15).
# The word list lives in the skill (scripts/medical_words.py) so the engine, the intake and the report gates share one list.
import importlib.util as _ilu
import os as _os
import re as _re

from . import config as _config


def _load_words():
    path = _os.path.join(_config.load().skill_dir or "", "scripts", "medical_words.py")
    if _os.path.exists(path):
        spec = _ilu.spec_from_file_location("medical_words", path)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return None


WORDS = _load_words()
# Without the skill folder there is no shared list: fall back to a short one that errs on the side of refusing
_FALLBACK = _re.compile(r"health|medical|illness|\bill\b|sick|disease|surger|death|\bdie|dying|dead|longevity|life ?span|marak|ayur|"
                        r"accident|injur|hospital|cancer|funeral|widow|umar|bimar|\brog\b|maut|mrityu|ilaj|swasth", _re.I)


CRISIS = WORDS.CRISIS_NOTE if WORDS else ("Please call your local emergency number now if you or someone else may be in danger; a crisis line "
                                         "(988 US, Samaritans 116 123 UK and Ireland, Tele-MANAS 14416 India) or someone you trust can help.")


def crisis(text):
    """True when the text is about suicide or self-harm (anyone's): the crisis referral, never a topic or the plain refusal."""
    return WORDS.selfharm_hit(text) if WORDS else bool(_re.search(r"suicid|self[- ]?harm|kill (?:my|him|her)self|atmahatya|आत्महत्या", str(text), _re.I))


def refuses(text):
    """True when a question or query is about health, illness, injury, longevity or death (any listed spelling)."""
    return WORDS.question_hit(text) if WORDS else bool(_FALLBACK.search(str(text)))


def medical_line(text):
    """True when a line of book text carries such material: the search tools drop it (T11.23)."""
    return WORDS.text_hit(text) if WORDS else bool(_FALLBACK.search(str(text)))


TOPICS = {  # topic → word-start regex over the lower-cased question ("remove" ≠ "move"); file is references/topic-<topic>.md
    "relationships-marriage": r"\bmarr(?:y|ie|ia)|\bwed|\bspouse|\bwife|\bhusband|(?<!business )\bpartner|"
                              r"\brelationship|\blove\b|\bromance|\bdating|\bgirlfriend|\bboyfriend|\bmy ex\b|\bbreak ?up|"
                              r"\bsex\b|\bsexual|\bintima(?:cy|te)|\bin bed\b|\bbed (?:comforts|pleasures)|\blibido|\b(?:sexual|physical|romantic) desire|"
                              r"\b(?:find|finding|meet) someone|\bsoulmate|\bin-laws?\b|\b(?:mother|father)-in-law|\bgay\b|\blesbian|\bbisexual|"
                              r"\bhomosexual|\bstraight or gay|\bsexual orientation|\bsexuality|\bgender identity|\btransgender",
    # own looks only; a partner's looks stay with relationships-marriage (lookahead). Loads vedic-natal via FILES, no topic file
    "appearance": r"^(?!.*\b(?:spouse|wife|husband|partner|girlfriend|boyfriend|fianc|lover|beloved)).*(?:\b(?:my|own|physical|personal) appearance|\bi look\b|\bmy looks\b|"
                  r"\bgood[- ]looking|\bphysique|\bcomplexion|\bmy height\b|\bheight (?:and|or) weight|\bstature|\bmy (?:body|face|skin|hair)\b|"
                  r"\bbody (?:type|build|shape)|\bphysical (?:build|features)|\bfacial|\b(?:am i|i am|i['’]m) (?:tall|short|attractive|beautiful|handsome|pretty|"
                  r"fat|thin)\b|\bkind of body|\bbody will i have|\bskin (?:colou?r|tone)|\boverweight|\bface look)",
    "career-money": r"\bcareer|\bjob|\bwork|\bbusiness|\bpromotion|\bincome|\bmoney|\bfinanc|\bwealth|\bdebt|"
                    r"\bsalary|\bboss|\bcompany|\binvest|\blotter|\bwindfall|\binherit|\bjackpot|\bsudden (?:gain|money|wealth)",
    "home-family-children": r"\bhome|\b(?:buy|sell|bought|new|my) house|\bhouse (?:purchase|hunt)|\bproperty|\bflat\b|\bapartment|\bmother|\bfather|\bparent|\bsibling|"
                            r"\bbrother|\bsister|\bchild|\bkids?\b|\bbab(?:y|ies)|\bpregnan|\bconceiv|\bson\b|\bmom\b|\bmum\b|\bdad\b|"
                            r"\bprogeny|\boffspring|\blittle ones?\b|\bgrand(?:parent|child|mother|father)|\bstart(?:ing)? a family|"
                            r"\bdaughter|\bfamil|\bfriend",
    "travel-education-life": r"\babroad|\bforeign|\btravel|\brelocat|\bmov(?:e|ing)\b|\bstud(?:y|ies)|"
                             r"\beducation|\bdegree|\buniversity|\bcollege|\bexam|\bschool|\bspiritual|"
                             r"\byear ahead|\bcoming year|\bnext year|\b12 months",
}


# Children are never timed (topic-home-family-children.md output rule): a children-only question is not a timing question, so
# timing.md is not loaded for it and the plain refusal for "when" applies. Property, parents or any other topic keep their timing.
_BE_PARENT = r"(?:be|becom\w*|being|get(?:s|ting)? to be) (?:a |an )?(?:mom|mum|dad|mother|father|parent|grandparent|grandmother|grandfather)"
CHILDREN_RX = (r"\bchild|\bkids?\b|\bbab(?:y|ies)|\bpregnan|\bconceiv|\bson\b|\bdaughter|\bprogeny|\boffspring|\bparenthood|\blittle ones?\b|"
               r"\bgrandchild|\bfertil|\bgrandparent|\bstart(?:ing)? a family|\bgrow(?:ing)? (?:our|my|the) family|\b" + _BE_PARENT)
# a relative's or friend's baby is a normal question and keeps its timing (owner 2026-11-19): cousin, in-laws (daughter-in-law ...), niece,
# nephew, aunt, uncle, grandchild, friend, and "her/his/their baby" (someone else's)
NOT_CHILDREN_RX = (r"\bhome|\bhouses?\b|\bproperty|\bflat\b|\bapartment|\bmother|\bfather|\bparents?\b|\bsibling|\bbrother|\bsister|"
                   r"\bcousins?\b|\bnieces?\b|\bnephews?\b|\baunt|\buncle|-in-law|\bin-laws?\b|\bgrand(?:child|children|son|daughter|kids?)|"
                   r"\bfriends?\b|\bcolleague|\bneighbou?r|\b(?:his|her|their) (?:baby|babies|child|children|kids?|son|daughter|little ones?)\b")
# the person's own parenthood ("become parents", "be a mother", "get to be a mom") names a parent word without being about a relative
_OWN_PARENT = _re.compile(r"\b(?:be|becom\w*|being|get(?:s|ting)? to be) (?:a |an )?(?:mom|mum|dad|mother|father|parents?|grandparents?)\b|\b(?:mothers?|fathers?) (?:myself|ourselves)\b")
_YEAR_WORDS = r"\b(?:year ahead|coming year|next year|12 months)"
_MARRY_EVENT_RX = r"\bmarr|\bwed|\bengag|\bdivorc|\bdating|\bbreak ?up|\bboyfriend|\bgirlfriend|\bfianc"


def is_timing(q):
    """True when a lower-cased question asks "when" (TIMING_RX), except a children-only question: one with no other topic (a bare
    "next year" does not count; a spouse word alone, as in "my wife conceive", does not count either) and no home, property or
    relative word. A relative's baby ("my sister have a baby") keeps its timing, as before."""
    bare = _re.sub(_YEAR_WORDS, " ", q)
    other = [t for t, rx in TOPICS.items() if t not in ("home-family-children", "relationships-marriage") and _re.search(rx, bare)]
    if _re.search(TOPICS["relationships-marriage"], bare) and _re.search(_MARRY_EVENT_RX, bare):
        other.append("relationships-marriage")
    mine = q if _re.search(r"\bmy (?:son|daughter|grand\w+)\b", q) else _OWN_PARENT.sub(" ", q)     # "my son becomes a father" is a relative's
    children_only = _re.search(CHILDREN_RX, q) and not other and not _re.search(NOT_CHILDREN_RX, mine)
    return bool(_re.search(TIMING_RX, q)) and not children_only


FILES = {"appearance": "references/vedic-natal.md"}   # topics that load a method file instead of references/topic-<topic>.md


def load(topics, timing):
    return ALWAYS + [FILES.get(t, f"references/topic-{t}.md") for t in topics] + ([TIMING] if timing else [])
