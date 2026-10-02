# Home, property, family, children and friendships

Load for property/home/vehicles, mother, father, siblings, children/parenthood, family life and friendships. Procedure
from [synthesis-method.md](synthesis-method.md). Other people's health, lifespan or fate are **not** read from the
native's chart as facts; describe the native's relationship with them and the themes that surround it.

## 1. Networks (Parashari)

| Matter | Houses | Lord / karaka | Relative-as-lagna (PD XV.21) | Varga |
|---|---|---|---|---|
| Home, land, vehicles, contentment | 4 (+2/11 funding, 6 loans, 8 joint title, 12 outflow/moving) | 4th lord; Mars land, Venus vehicles/comfort, Moon home | — | D4 |
| Mother | 4 | Moon | Moon's sign as lagna | D12 |
| Father | 9 (some schools 10) | Sun | Sun's sign as lagna | D12 |
| Younger siblings / courage | 3 | Mars | Mars's sign | D3 |
| Elder siblings, friends, networks | 11 | Jupiter | — | — |
| Children, creativity, students | 5 (2 family addition, 9 = 5th from 5th, 11 = 7th from 5th) | 5th lord; Jupiter | Jupiter's sign | D7 |
| Family, household, speech | 2 | 2nd lord; Jupiter | — | D2 |

**Home and property.** 4th lord with the lagna lord in a good house, or in a kendra/kona → comfort and property; 4th lord
and Venus well placed in lagna and 4th → vehicles and luxuries [HPA p52; PD XVI.13]; 4th lord in the 12th → ancestral
property at risk [HPA p52]; Rahu/Saturn with the 4th and its lord → old or dilapidated dwellings; 4th lord with an
enemy planet → property disputes [PD XVI.14]. Acquisition, renovation, moving and selling are different events;
4–12 links can describe moving or spending, not necessarily foreign property.

**Mother / father.** Triad of 4th (9th) house, its lord and the Moon (Sun), plus benefics favourably placed from the
karaka [PD XVI.10; HJH2 p187–204]. Raman: judge the 9th only after assessing the Sun, the 9th lord, their influences and
the running periods; "in no case is a literal application desirable" [HJH2 p190, p204]. Say what the chart suggests
about the native's *experience* of the parent (closeness, distance, responsibility, support), never a parent's
illness or death date. The classical texts contain many parent-death rules (e.g. PD XVI.10, HPA p44, p52) — do not
state them.

**Siblings.** 3rd house, 3rd lord and Mars for younger; 11th and its lord for elder; counts from navamsas or
Ashtakavarga are traditional and unreliable — Raman averages lagna and Moon counts and says rules must be tested
[HJH2 p383–392; PD XXIV.9]. Only discuss if asked; never infer that a sibling exists or not.

**Children / parenthood.** *Output rule:* the method notes below are for judging the theme, not for forecasting
births. Never give a window for having or conceiving a child, an age of parenthood, a number of children, "delay",
"limited progeny" or "childless" statements — even softened. Describe the relationship with children, parenting
style, mentoring or creative "offspring"; if asked *when*, say the chart cannot time conception or birth and that
fertility questions belong with a medical professional. `life_lint.py` and the report renderer block these phrasings.
- Supportive: Jupiter and the 5th lords from lagna and Moon well placed and the 5th aspected by benefics or good-house
  lords; lagna and 5th lords related [PD XII.1]; 5th lord, Jupiter and lagna lord strong [HPA p52].
- Obstructive confluence: 5th from lagna, Moon and Jupiter all afflicted with lords in dusthanas [PD XII.2]; "childless
  signs" (Leo, Virgo, Scorpio on the 5th) mean limited progeny after delay, not denial [PD XII.3].
- The sources conflict: a benefic owning or exalted in the 5th is said to cause loss of children [PD XII.3] while a
  strong 5th lord is the main sign of children elsewhere [PD XII.1, XII.9] (CR-V03). Karaka in its own house (Jupiter in
  5th) is read as bad for children by LOL [LOL p421] — contested for Venus by Raman [HJH2 p65].
- Prasna Marga grades natal obstruction: some factors present → children after effort/remedies; all present → denial
  [PM2 XVIII.38, XIX.26, XIX.32]. Use this *grading idea*, not the curse attributions.
- Timing: periods of the lagna lord, 5th lord, Jupiter, their navamsa lords, the 7th lord, and planets in/aspecting the
  5th [PM2 XIX.83]; both dasha and bhukti lords should touch the 5th, its lord or Jupiter [LOL p355]; Jupiter transits
  over the 5th lord's sign/navamsa sign from lagna, Moon or Jupiter [PM2 XIX.84].
- Adoption, step-children, students or creative "offspring" are legitimate alternative expressions of the 5th.

**Friendships and networks.** 11th (friends, gains through people), 3rd (peers, neighbours), 7th (allies/opponents),
4th (close circle). Lagna, 2nd and 11th lords friendly → gains used honourably [HJH2 p373]. Mutual friendship of
planets in a combination makes them cooperate [LOL p293].

## 2. Lal Kitab layer

- **House 4** (Moon's pakka ghar; mother, happiness, vehicles): a lone planet here gives no debilitated effect; any
  planet in 4 acts like the Moon; 4 empty with the Moon outside the kendras makes all planets good; Mars+Rahu in 6 "kill"
  the 4th [KB B3 H4]. **Matri rin**: Ketu in 4 [KB B12].
- **House 9** (Jupiter; father/ancestors, luck): after children the 5th merges into the 9th, after brothers the 3rd; a
  sleeping 9 is awakened through 2 [KB B3 H9]. **Pitri rin**: malefics or enemies in Jupiter's houses 2, 5, 9, 12;
  judged from the natal chart only; recurs across family members' charts [KB B12 p164–168].
- **House 5** (progeny): follows the Sun; progeny safe while Jupiter is good; planets in 6 and 10 are enemies of planets
  in 5 [KB B3 H5]. Author's own practice (Santan Gopal sadhana) is [AUTH], not Lal Kitab [KB B16].
- **House 3** (siblings): planets in 3 protect against the 8th; Rahu/Ketu here "worrying" [KB B3 H3].
- **House 2 and 12**: family/in-laws and expenses; "12th does justice for all, 2nd for the 12th" [KB A5 notes].
- Relatives signified by a planet protect the native while alive; after their death keep that planet's objects
  [KB B13 p199]. The scapegoat chains name relatives (maternal uncle, son, wife) — read as family *themes*, never as
  predictions about a named person [KB B7 p48–50].
- **House-building and Saturn** [KB B15; R33]: Lal Kitab ties house construction to Saturn's placement; several
  statements are deterministic ("father's death certain if native builds 3 houses") — C5, never forecast.
- Rin remedies are collective family practices; check [remedy-safety.md](remedy-safety.md) (e.g. feeding 100 dogs is
  allowed as charity; the "fast 40–43" instruction is unsafe as stated).

## 3. Alternatives and boundaries

Property purchase vs long lease vs renovation; living near parents vs caring for them from afar; a child vs adoption vs
mentoring role; a family business rather than a household event. Never confirm or rule out pregnancy, fertility, a
child's sex, a parent's death or a sibling's fate. Fertility and health questions go to medical professionals; see
[communication.md](communication.md).
