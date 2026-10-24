# P6-2 (part B): astro/routing.py is the one routing source; SKILL.md's workflow and topic table must agree with it,
# and every reference over 100 lines needs a table of contents matching its ## headings (both editions).
import glob
import os
import re

import pytest

from astro import config, routing, service as S

SKILL = config.load().skill_dir
TEXT = open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8").read()
CASES = os.path.join(SKILL, "tests", "test-cases.md")


def view(text, private):   # the edition's text: drop the other edition's blocks and the marker lines
    text = re.sub(r"<!-- private-edition -->\n(.*?)<!-- /private-edition -->\n", r"\1" if private else "", text, flags=re.S)
    return re.sub(r"<!-- public-edition\n(.*?)public-edition -->\n", "" if private else r"\1", text, flags=re.S)


def links(text):
    return set(re.findall(r"\]\((references/[\w-]+\.md)\)", text))


def slug(t):
    return re.sub(r"[^\w\- ]", "", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t).replace("`", "").lower()).replace(" ", "-")


@pytest.mark.parametrize("private", [True, False])
def test_skill_md_names_the_manifest_files(private):
    t = view(TEXT, private)
    for f in routing.ALWAYS[1:] + [routing.TIMING]:
        assert f in links(t), f
    for topic in routing.TOPICS:
        row = re.search(rf"^ *\|[^|\n]*\| \[[^\]]*\]\((references/topic-{topic}\.md)\) \|$", t, re.M)
        assert row, topic   # a table row whose Load cell is exactly this topic file
    assert len(re.findall(r"^ *\| .* \| \[[^\]]*\]\(references/topic-", t, re.M)) == len(routing.TOPICS)


def test_load_list_is_manifest_derived():
    a = S.analyze_question("When will I marry?")
    assert a["load"] == routing.ALWAYS + ["references/topic-relationships-marriage.md", routing.TIMING]
    assert set(a) == {"question", "topics", "timing_question", "load"}
    assert all(os.path.exists(os.path.join(SKILL, f)) for f in a["load"])


# T-case routing, per SKILL.md's table (word starts); [] = open activation, no topic file. Lal Kitab words don't route.
EXPECT = {"T01": ["relationships-marriage"], "T02": ["relationships-marriage"], "T03": ["career-money"],
          "T04": ["career-money", "travel-education-health-life"], "T05": ["travel-education-health-life"],
          "T06": ["travel-education-health-life"], "T07": [], "T08": ["travel-education-health-life"],
          "T09": ["relationships-marriage"], "T10": ["career-money"], "T11": ["relationships-marriage"], "T12": [],
          "T13": ["career-money"], "T14": ["career-money"], "T15": [], "T16": ["home-family-children"], "T17": [],
          "T18": ["relationships-marriage"], "T19": [], "T20": [], "T21": [], "T22": ["relationships-marriage"],
          "T23": [], "T24": []}
if not os.path.exists(os.path.join(SKILL, "scripts", "lal_kitab.py")):   # public edition: its own T16 wording
    EXPECT["T16"] = []
TIMED = {"T02", "T03", "T04", "T06", "T08", "T12", "T13", "T14", "T23"}


def test_t_case_routing_equals_skill_md():
    reqs = {}
    for line in open(CASES, encoding="utf-8"):
        m = re.match(r"\| (T\d+) \|[^|]*\|(.*?)\|", line)
        q = re.findall(r"\"([^\"]+)\"", m[2]) if m else []
        if q and m[1] not in reqs:
            reqs[m[1]] = q[-1]
    assert set(EXPECT) <= set(reqs), set(EXPECT) - set(reqs)
    for tid, topics in EXPECT.items():
        a = S.analyze_question(reqs[tid])
        assert [t for t in a["topics"] if not t.startswith("open")] == topics, tid
        assert a["timing_question"] == (tid in TIMED), tid
        assert a["load"] == routing.load(topics, tid in TIMED)


@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(SKILL, "references", "*.md"))))
@pytest.mark.parametrize("private", [True, False])
def test_long_references_have_a_toc(path, private):
    t = view(open(path, encoding="utf-8").read(), private)
    if len(open(path, encoding="utf-8").read().splitlines()) <= 100 or len(t.splitlines()) <= 40:
        pytest.skip("short, or the edition keeps only a stub")
    head, _, rest = t.partition("Contents:")
    assert rest and len(head.splitlines()) < 8, "no Contents line near the top"
    toc = re.findall(r"\]\(#([^)]+)\)", rest.split("\n\n")[0])
    body = rest.split("\n\n", 1)[1]
    assert toc == [slug(h) for h in re.findall(r"^## (.+)$", body, re.M)]
