"""Routing manifest: the one source for which skill reference files a question loads. `service.analyze_question` reads it;
tests/test_routing_manifest.py checks SKILL.md's workflow and topic table against it. Edition-neutral (no Lal Kitab):
edition-specific routing stays in SKILL.md."""

ALWAYS = ["SKILL.md", "references/consultation-reasoning.md", "references/inputs.md", "references/question-trees.md",
          "references/synthesis-method.md", "references/communication.md", "references/qc.md"]
TIMING = "references/timing.md"   # added when the question asks "when"
TIMING_RX = r"\bwhen (?:will|am|is|are|do|does|did|can|should|would|might|could)\b|next (?:\d+|two|three|four|five|ten) |this year|coming year|next year|soon|month|period|dasha|timing"
TOPICS = {  # topic → word-start regex over the lower-cased question ("remove" ≠ "move"); file is references/topic-<topic>.md
    "relationships-marriage": r"\bmarr(?:y|ie|ia)|\bwed|\bspouse|\bwife|\bhusband|(?<!business )\bpartner|"
                              r"\brelationship|\blove\b|\bromance|\bdating|\bgirlfriend|\bboyfriend|\bmy ex\b|\bbreak ?up",
    "career-money": r"\bcareer|\bjob|\bwork|\bbusiness|\bpromotion|\bincome|\bmoney|\bfinanc|\bwealth|\bdebt|"
                    r"\bsalary|\bboss|\bcompany|\binvest",
    "home-family-children": r"\bhome|\b(?:buy|sell|bought|new|my) house|\bhouse (?:purchase|hunt)|\bproperty|\bflat\b|\bapartment|\bmother|\bfather|\bparent|\bsibling|"
                            r"\bbrother|\bsister|\bchild|\bkids?\b|\bbab(?:y|ies)|\bpregnan|\bconceiv|\bson\b|"
                            r"\bdaughter|\bfamil|\bfriend",
    "travel-education-health-life": r"\babroad|\bforeign|\btravel|\brelocat|\bmov(?:e|ing)\b|\bstud(?:y|ies)|"
                                    r"\beducation|\bdegree|\buniversity|\bcollege|\bexam|\bschool|\bhealth|"
                                    r"\billness|\bill\b|\bsick|\bdisease|\bsurgery|\bwellbeing|\bspiritual|"
                                    r"\byear ahead|\bcoming year|\bnext year|\b12 months",
}


def load(topics, timing):
    return ALWAYS + [f"references/topic-{t}.md" for t in topics] + ([TIMING] if timing else [])
