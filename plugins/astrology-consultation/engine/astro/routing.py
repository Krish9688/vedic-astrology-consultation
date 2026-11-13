"""Routing manifest: the one source for which skill reference files a question loads. `service.analyze_question` reads it;
tests/test_routing_manifest.py checks SKILL.md's workflow and topic table against it. Edition-neutral (no Lal Kitab):
edition-specific routing stays in SKILL.md."""

ALWAYS = ["SKILL.md", "references/consultation-reasoning.md", "references/inputs.md", "references/question-trees.md",
          "references/synthesis-method.md", "references/communication.md", "references/qc.md"]
TIMING = "references/timing.md"   # added when the question asks "when"
TIMING_RX = (r"\bwhen (?:will|am|is|are|do|does|did|can|should|would|might|could)\b|\bwhen\s*(?:[?.,;!]|$)|\bhow (?:long|soon)\b|next (?:\d+|two|three|four|five|ten) |next (?:week|month|year)\b|coming (?:week|month)|\bthis decade|\bwithin (?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a few) (?:days?|weeks?|months?|years?)|"
            r"\b(?:in|by|during|before|after|until) (?:19|20)\d\d\b|this (?:week|month)|this year|coming year|next year|soon|month|period|dasha|timing")
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
                            r"\bbrother|\bsister|\bchild|\bkids?\b|\bbab(?:y|ies)|\bpregnan|\bconceiv|\bson\b|"
                            r"\bdaughter|\bfamil|\bfriend",
    "travel-education-health-life": r"\babroad|\bforeign|\btravel|\brelocat|\bmov(?:e|ing)\b|\bstud(?:y|ies)|"
                                    r"\beducation|\bdegree|\buniversity|\bcollege|\bexam|\bschool|\bhealth|"
                                    r"\billness|\bill\b|\bsick|\bdisease|\bsurgery|\bwellbeing|\bspiritual|"
                                    r"\byear ahead|\bcoming year|\bnext year|\b12 months",
}


FILES = {"appearance": "references/vedic-natal.md"}   # topics that load a method file instead of references/topic-<topic>.md


def load(topics, timing):
    return ALWAYS + [FILES.get(t, f"references/topic-{t}.md") for t in topics] + ([TIMING] if timing else [])
