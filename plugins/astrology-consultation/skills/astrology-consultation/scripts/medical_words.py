"""The one list of medical, death and self-harm words (owner rule 2026-11-15: no medical and no death content, for anyone).

Everything that refuses or drops such text reads this module: astro/routing.py (questions, book-search filter),
astro/service.py (book excerpts), consultation.py (intake question text) and render_report.py (every report string).
Add a word here and every check has it. Standard library only, so the engine and the scripts can both load it.

Lists, each a regex alternation (Latin lists are wrapped as r"\\b(?:...)\\b", Devanagari lists with their own guards):
  STRONG        health, illness, injury, longevity and death words: English, Hindi and Hinglish in Latin letters
  DEVA          the same in Devanagari (Python's \\b is wrong around vowel signs, so DEVA has its own guards)
  SELFHARM      suicide and self-harm: these get the crisis referral (communication.md 5a), not the plain refusal
  BOOK_EXTRA    more words that mark a book excerpt as such material (doctor, named diseases, ...); never used on a question
                because "my friend is a doctor" is a normal question
  REPORT_WORDS  the wider report list (body parts, soft death phrases, old-age words); only for report strings
Text is normalised first (norm / variants): NFKC, accents folded, invisible characters stripped, spaced or dotted letters
joined ("F A T H E R", "d.i.e"), lower-cased for the question and book checks. A word that mixes Latin with Cyrillic or Greek
letters is refused. A word of 5+ letters one edit away from a listed word is refused unless it is a real word (the
near-word list in data/medical-near-words.txt holds the real words that sit one edit from a listed word).
Known over-blocks the owner accepts: "server health", "hospital administration", "die down", "health-food", "dead-heat",
"operation" in a work sense, "Umar" and "Maran" the names, "Mayo Clinic", "Death Valley", "Grateful Dead", "dead market",
"survive the exam", "a will to live", "stent" or "croak" in a joke, and any sentence that holds a typo-net near miss of a listed word
that the real-word list lacks. In book lines, any line (or wrapped excerpt block, read joined) that names two organs is dropped.
Round 5 over-blocks (accepted): "farewell email", "goodbye note", "sleeping pills", "razor", "untimely", "phobia", "disorder", "peg out the
washing", "conk out" (a car), "stand again", "when she is gone for good", "I will myself", a "sick of pretending" venting line, and in reports
"Your parents' home may host a gathering" (the relative-shape rule, not a word).
Round 6 over-blocks (accepted): "bypass" (a road or a system), "time is almost up" (a deadline), "guzar jayega" (time passing), "live to see"
in a plain sense, "Will my sister/mother pass?" about an exam, a "medicine" startup, "Die Young" the song title, "Lifespan Insurance", a
hospital fundraiser, "cut again" or "burn my hand" in a cooking or craft sense, "how high does a building need to be" for a real building
question, "mad house" or "madhouse" as a party word, "defect" in a plain sense (reports), and "I want to dye" with no object.
Round 7 over-blocks (accepted): "be around for" a meeting, "put down" a pet or a thing, "get better soon" about a person or "I", "dirgha", "ayu",
"replacement" and "implant" in any sense, "collision", "stabbed" or "shot at" in a film sense, "Gujarat" is kept, a nukta-less Devanagari
spelling is read the same as the nukta one, and "kms" after a want word, "will" or "to" is read as self-harm (plain "5 kms" stays neutral).
Round 9 over-blocks (T11.42, accepted): "heavenly abode" or "final abode" in a story or a place name, "guzar sakte" in a "pass by" sense,
"antim yatra" for a last trip, "no more" or "slip away" or "depart" with a kin word anywhere in the same sentence ("Your uncle says the
phase is no more by June"), and "depart" without "for", "from", "to" or "with".
"""
import os
import re
import unicodedata

# ---------------------------------------------------------------------------------------------------------------------
# Latin letters: English, Hindi and Hinglish
# ---------------------------------------------------------------------------------------------------------------------
_ENGLISH_CORE = (
    r"health(?!y appetite)\w*|well-?being|medical\w*|medicin\w*|medicat\w*|medic\b|medics\b|illness\w*|(?<![\'’])ill|sick\w*|diseas\w*|"
    r"diagnos\w*|symptom\w*|surger\w*|surgeons?|operated on|(?:an?|the|my|his|her|their|after|before|for) operations?|"
    r"hospital(?!ity|\s+(?:records?|certificates?|register|birth))\w*|clinic\w*|"
    r"(?<!zodiac is )(?<!sign is )(?<!rashi is )(?<!lagna is )(?<!moon is )(?<!sun is )(?<!sun in )(?<!moon in )(?<!born in )(?<!am a )(?<!am an )(?<!am )(?<!is a )cancer(?![\s-]+(?:sign|rashi|moon|lagna|ascendant|zodiac|sun|season|rising|native|man|woman|born|people|person))|tumou?rs?|"
    r"death\w*|dying|(?:dies?|died)(?!\s+hard)|dead(?![- ]?(?:end|lock|line|pan|stock|heat))|deceased|demise|"
    r"(?:he|she|they|spouses?|wife|husband|father|mother|parents?|native|natives)\s+expired|expired\s+(?:early|young|prematurely)|"
    r"pass(?:es|ed|ing)?\s+away|perish\w*|funeral\w*|cremat\w*|memorial\w*|mortal\w*|fatal\w*|longevity|life ?spans?|"
    r"end of (?:your|his|her|their|my) life|how long (?:will|would|does|do|is) (?:i|he|she|they|my \w+) (?:live|survive|last)|"
    r"live (?:long|to be)|life insurance (?:payouts?|pay ?outs?|claims?)|"
    r"marak\w*|ayur\w*|arisht\w*|balarisht\w*|"
    r"accident\w*|injur\w*|fractur\w*|fever\w*|virus\w*|infect\w*|ambulance\w*|bedridden|confined to (?:a |the |his |her )?bed|"
    r"eyesight|widow\w*"
)
_ENGLISH_MORE = (
    # named diseases and conditions
    r"small-?pox|chicken-?pox|measles|mumps|rabies|tetanus|scurvy|gout|goit(?:re|er)|catarrh|leprosy|leper\w*|leprous|rheumat\w*|dysentery|"
    r"diarrh\w*|scabies|ringworm|eczema|vitiligo|leucoderma|epilepsy|cough\w*|tonsil\w*|"
    r"diabet\w*|leuk(?:a)?emi\w*|lymphoma\w*|melanoma\w*|carcinoma\w*|chemo\w*|radiotherap\w*|oncolog\w*|asthma\w*|arthritis|"
    r"epilep\w*|seizures?|migraines?|hypertensi\w*|blood pressure|cholesterol|thyroid\w*|obes(?:e|ity)|an(?:a)?emi(?:a|c)|"
    r"tubercul\w*|malaria\w*|dengue|typhoid|cholera|jaundice|hepatitis|pneumonia|bronchitis|covid\w*|corona(?:virus)?|"
    r"pandemic\w*|epidemic\w*|outbreaks?|plague|flu|influenza|hiv|sepsis|gangrene|ulcers?|piles|fistula|hernia|appendic\w*|appendectom\w*|"
    r"gallstones?|kidney stones?|cirrhosis|dementia|alzheimer\w*|parkinson\w*|strokes?(?!\s+of)|heart (?:attacks?|disease|failure|"
    r"condition|trouble|problems?|surgery|patients?)|cardiac|cardio\w*|paraly[sz]\w*|coma|comatose|blindness|(?:go|goes|going|went|become|became|becoming|turn|turns|turned) blind|"
    r"deafness|deaf\w*|disabilit\w*|disabled|handicap\w*|crippl\w*|bedbound|bed-?bound|frail\w*|sickly|ailing|ailment\w*|unwell|"
    r"infirm\w*|recuperat\w*|relapse\w*|remission|prognos\w*|terminal(?:ly)?|check-?ups?|pharma\w*|nursing home|palliative|hospice|"
    r"contagio\w*|quarantine\w*|vaccin\w*|antibiotic\w*|insulin|painkillers?|steroids?|prescri\w*|pains?|painful|aches?|headaches?|"
    r"backaches?|stomach ?aches?|heal(?:s|ed|ing)?|"
    # mental health and crisis
    r"depress\w*|anxiety|panic attacks?|anxiety attacks?|nervous breakdown|mental (?:illness|health|disorder|breakdown)|psychiatr\w*|"
    r"schizo\w*|bipolar|insan\w*|madness|lunatic\w*|ptsd|addict\w*|alcoholi\w*|rehab|substance abuse|overdos\w*|drug (?:abuse|use|habit)|"
    # pregnancy and fertility
    r"miscarr\w*|stillbirth\w*|still-?born|abortion\w*|(?:lose|lost|losing|loses) (?:the|a|my|your|his|her|their) (?:baby|babies|child|"
    r"pregnancy|unborn)|pregnancy complications?|medical complications?|c(?:a)?esarean\w*|c-section|ectopic|infertil\w*|impoten\w*|sterility|ivf|"
    # injury
    r"concussion\w*|sprain\w*|dislocat\w*|wound\w*|stitches|bleed\w*|h(?:a)?emorrh\w*|broken (?:bone|leg|arm|rib|neck|back|spine|skull)|"
    r"(?:car|road|bike|plane|train|traffic) (?:crash|accident)\w*|drown\w*|amputat\w*|"
    # organs, procedures, wards
    r"transplant\w*|pacemakers?|ventilators?|life support|icu|intensive care|emergency room|trauma cent(?:er|re)|dialysis|biopsy|"
    r"x-?rays?|mri|ct scan|endoscop\w*|an(?:a)?esth\w*|organ (?:failure|donor|donation)|patients|organ transplant|"
    r"kidneys?|liver|lungs?|spleen|pancrea\w*|gallbladder|bowels?|intestin\w*|womb|uterus|ovar(?:y|ies|ian)|prostate|bone marrow|"
    r"brain (?:tumou?r|damage|stroke|surgery|h(?:a)?emorrhage)|"
    # death and dying
    r"obituar\w*|burial|burials|graveyard|gravestone|coffin\w*|casket|last rites|final rites|last breath|"
    r"breath\w* (?:his|her|their|my|your|one's) last|gone for good|no longer with us|(?:other|next) world|deathbed|euthanasia|mercy killing|"
    r"murder\w*|homicid\w*|assassinat\w*|kill(?:ed|ing|s|er)?\b(?! time)|poison\w*|"
    r"late (?:father|mother|husband|wife|grand\w+|brother|sister|son|daughter|uncle|aunt|parents?)|"
    r"lose (?:my|your|his|her|their) (?:father|mother|parents?|husband|wife|spouse|son|daughter|child|children|brother|sister|grand\w+)|"
    r"life ?line|(?:short|long)[- ]?(?:life|lived|lives)|numbered days|days are numbered|end is near|have (?:\w+ )?(?:years|time|days|months) (?:left|to live)|(?:years|time|days) to live|how (?:much time|many years) (?:do|does|will|would) (?:i|he|she|they|my \w+) have|"
    r"what age will (?:i|he|she|they|my \w+|your \w+) (?:reach|live|die|be when)|(?:till|until|up to|upto) what age|"
    r"how many (?:years|months|days) (?:do|does|will|would|are|have|has|is) (?:i|he|she|they|my \w+|left|remain\w*)|"
    r"critical condition|critically (?:ill|injured)|serious(?:ly)? (?:ill|injured)|in danger of (?:dying|death)|"
    r"rest in peace|(?:left|leave|leaves|leaving) this world|departed|orphan\w*|"
    # self-harm (also in SELFHARM: here so every list carries the word)
    r"suicid\w*|self[- ]?harm\w*|self[- ]?injur\w*|"
    # slang and euphemisms for death
    r"kick(?:s|ed|ing)? the bucket|six feet under|(?:meet|meets|met|meeting) (?:his|her|their|my|your|our|the|one['’]?s) maker|croak(?:s|ed|ing)?|"
    r"snuff(?:s|ed|ing)? (?:it|out)|(?:my|his|her|their|your) number (?:is |was )?(?:up|called)|number['’]?s up|"
    r"called (?:to|by|home to|up to) (?:god|him|the lord|heaven|the heavens)|bit(?:e|es|ing)? the dust|depart(?:s|ed|ing)? (?:this|the|from this) (?:world|life|earth)|"
    r"flat-?lin\w*|gone to (?:heaven|god|a better place|the other side|his maker|her maker)|(?-i:RIP)|pushing up daisies|"
    r"giv(?:e|es|en|ing) up the ghost|gave up the ghost|buy(?:s|ing)? the farm|bought the farm|cash(?:es|ed|ing)? in (?:his|her|their|my) chips|"
    r"shuffl\w* off|(?:no longer|not) among us|gone from (?:this|the) (?:world|earth)|(?:leave|leaves|left|leaving) us for good|"
    r"pass(?:es|ed|ing)? on(?=\s*(?:$|[?.!,;]|peacefully|soon|young|early|before|in \d|in (?:his|her|their|my|your) sleep|this year|next year|quietly|suddenly|too soon|from))|"
    r"pass(?:es|ed|ing)? over to the other side|(?:go|goes|going|went|gone) to (?:his|her|their|my) (?:eternal )?rest|eternal rest|"
    r"(?:he|she|they|i|native|natives|father|mother|husband|wife|grand\w+|parents?|uncle|aunt|brother|sister)\s+(?:will\s+|may\s+|might\s+|would\s+|to\s+)?expire|"
    r"stent\w*|crutch\w*|allerg\w*|anaphyla\w*|"
    # lifespan phrasings
    r"outliv\w*|(?:make|makes|made|making) it (?:to|past|beyond) (?:the age of )?\d+|(?:live|lives|living|lived|survive|survives|reach|reaches|reached|see|sees|hit|hits) "
    r"(?:to|past|beyond|till|until|up to|upto|the age of) (?:the age of )?\d{2,3}\b|(?:see|sees|reach|reaches|reached|make|makes) (?:the year )?(?:19|20)\d\d\b(?! (?:with|in|for|and))|"
    r"(?:live|survive|alive|be here|be around|last) (?:till|until|to|through|into) (?:the year )?(?:19|20)\d\d|"
    r"(?:reach|reaches|reached|hit|hits|turn|turns|turning) (?:the age of )?(?:[6-9]\d|1[01]\d)\b|how old will (?:i|he|she|they|my \w+) (?:be|live|get)|"
    r"(?:last|final) (?:hour|hours|moments?|wish)|"
    # pregnancy outcome
    r"pregnan\w*(?:\W+\w+){0,6}?\W+(?:end|ends|ending|ended) badly|pregnan\w*(?:\W+\w+){0,6}?\W+(?:lose|lost|loss|complicat\w*|go(?:es)? wrong|danger\w*|safe|survive|healthy|risk\w*)|"
    r"carry (?:\w+ ){0,3}to term|(?:baby|child|foetus|fetus|unborn|newborn)(?:\W+\w+){0,4}?\W+(?:survive|surviv\w*|safe|healthy|normal|alive|premature|defect\w*|abnormal|born (?:dead|early))|"
    r"full[- ]?term|premature(?:ly)?|preterm|born (?:dead|early)|healthy (?:baby|child|babies)|(?:safe|normal|easy|smooth|natural|painful) (?:delivery|birth|labou?r)|labou?r pains?|"
    # device, rehab and disability words (shared by questions and reports)
    r"hearing aids?|hearing loss|hearing impair\w*|visually impaired|physio\w*|plaster casts?|in a cast|limp(?:s|ed|ing)?|"
    r"(?:lose|loses|losing) (?:a|an|the|your|his|her|their|one of (?:your|his|her|their)) (?:limb|leg|arm|foot|hand|eye|finger|toe)|"
    r"(?:lost) (?:a |an |the |your |his |her |their )?(?:limb|leg|arm|eye)|wheelchairs?|walking (?:frame|stick|aid|cane)|zimmer frame|rollator|prosthe\w*|"
    r"(?:knee|back|neck|leg|arm|wrist|ankle) braces?|slings?|bandag\w*|stitches|rehab\w*|therapy sessions?|cataracts?|glaucoma|lasik|inhalers?|nebuli[sz]ers?|"
    r"dentures?|root canal|oxygen (?:tank|mask|cylinder)|stairlift|mobility aids?|disfigur\w*|scars?|scarring|hunchback\w*|dwarfism|speech impair\w*|"
    r"akhri (?:waqt|saans|samay|din|pal|ghadi)|aakhri (?:waqt|saans|samay|din|pal|ghadi)|akhiri (?:waqt|saans)|antim (?:samay|saans|din|waqt|sanskar|yatra)|umra"
)
_ROUND5 = (
    # questions: lifespan and death idioms, loss of faculties (round 5)
    r"(?:see|sees|reach|reaches|reached|celebrate|make it to|live to see|survive to|get to see|be around for) (?:\w+ ){0,2}?(?:[4-9]\d|1[01]\d)(?:st|nd|rd|th) birthdays?|"
    r"(?:early|untimely|premature) (?:grave|tomb)|(?:my|his|her|their|your|our) graves?|(?:into|to|in) (?:an? |the )(?:early |untimely )?(?:grave|tomb)|untimely|"
    r"before (?:his|her|their|my|your) time|"
    r"(?:walk|walks|walking|stand|stands|standing) again|(?:walk|stand) (?:on|with|without) (?:his|her|their|my|your) (?:own )?(?:legs?|feet|two feet)|"
    r"(?:regain|regains|regained|regaining|get back|gets back) (?:his|her|their|my|your) (?:sight|vision|speech|hearing|memory|mobility|strength|voice|senses|health)|"
    r"(?:lose|loses|losing|lost) (?:the |a |his |her |their |my |your )?(?:memory|memories|marbles|sanity|faculties|speech|mobility)|"
    r"(?:lose|loses|losing|lost) (?:his|her|their|my|your) (?:eye)?sight|loss of (?:memory|sight|hearing|speech|mobility|teeth|tooth|limbs?)|memory loss|senile|senility|"
    r"(?:lose|loses|losing|lost) (?:his|her|their|my|your) (?:teeth|tooth|limbs?|hearing|senses|voice|vigou?r|virility|potency)|toothache|teeth (?:fall|loss|decay|trouble)\w*|"
    r"peg(?:s|ged|ging)? out|pop(?:s|ped|ping)? (?:his|her|their|my|your) clogs|conk(?:s|ed|ing)? out|drop(?:s|ped|ping)? dead|keel(?:s|ed|ing)? over|"
    r"(?:kick|kicks|kicked|kicking|bite|bites|bit|biting) it(?=\s*(?:$|[?.!,;]|soon|young|early|before|this year|next year|in \d))|"
    r"(?:meet|meets|met|meeting) (?:his|her|their|my|your) end|(?:cash|check)(?:es|ed|ing)? out (?:early|young|soon)|"
    r"life (?:ends?|will end|terminat\w*|comes? to an end)|end of (?:the |one['’]?s )?life|life['’]?s end|(?:age|years) of (?:death|dying)|"
    r"(?:after|when|once) (?:you|he|she|they|i)(?: are| is| were|['’]re|['’]m|['’]s)? gone (?:from this world|for good|forever)|"
    # venereal and sexual-health diseases, nervous complaints
    r"venereal|gonorrh\w*|syphili\w*|chlamyd\w*|herpes|sexually transmitted|trichomon\w*|chancroid|(?-i:AIDS|STDs?|STIs?)|"
    r"(?:genital|secret|private|sexual|urinary|uterine|menstrual) (?:diseases?|disorders?|troubles?|complaints?|infections?|weakness|afflictions?|ailments?)|"
    r"spermatorrh\w*|leucorrh\w*|erectile|nervous (?:exhaustion|debility|disorders?|diseases?|troubles?|weakness|complaints?)|neurasthen\w*|"
    # named mental, learning and developmental conditions
    r"dyslexi\w*|dyscalcul\w*|dyspraxi\w*|dysgraph\w*|autis\w*|asperger\w*|tourette\w*|adhd|ocd|attention[- ]deficit|"
    r"(?:panic|eating|sleep|personality|learning|mood|conduct|stress|anxiety|bipolar|obsessive[- ]compulsive|post[- ]traumatic|dissociative|speech|"
    r"developmental|identity|psychotic|seizure|mental|attention|autism spectrum) (?:disorders?|disabilit\w*|difficult\w*)|"
    r"anorexi\w*|bulimi\w*|phobias?|hallucinat\w*|paranoi\w*|psychosis|psychotic|neuros(?:is|es)|neurotic|insomnia|sleeplessness|narcolep\w*|"
    r"mentally (?:ill|unstable|challenged|disturbed|retarded)|special needs|neurodivergen\w*|"
    # death records and rites
    r"(?:purn|alp|madhy\w*|dirgh|pind|nisarg|ams)ayu|epitaphs?|eulog\w*|tombstones?|headstones?|cemeter\w*|mausole\w*|sepulch\w*|death certificates?|posthumous\w*|requiem|last will and testament"
)
_ROUND6 = (
    r"(?:lives?|living|lived|alive) to see|(?:heart|body|lungs?|kidneys?|liver|health)(?: is| was| will| may| might)?(?: going to| about to| gonna)? (?:give|gives|gave|giving) out|"
    r"give out on (?:him|her|me|them)|laid to rest|(?:be|been|is|was) laid down to rest|"
    r"(?:mental|lunatic|insane|psychiatric|mad)[- ]?(?:asylum|hospital|institution|home|ward|house)|asylum for the (?:insane|mad)|madhouse|loony bin|nut ?house|"
    r"\w+['’]?s time (?:is |was |will be )?(?:almost |nearly |just about )?(?:up|over|short)|(?:his|her|their|your|my) time (?:may |might |could |will |would )?(?:be |is |was )?(?:almost |nearly |just about )?(?:up|over|short)|"
    r"time (?:is )?(?:almost|nearly) up|(?:not much|little) time (?:left|remaining)|counting (?:down )?(?:his|her|their|my) days|bypass\w*|"
    r"gu[zj]ar ?(?:ja|ga)\w*|birth defects?|congenital\w*|born with (?:an? )?(?:defect|disabilit|deformit|handicap)\w*|"
    r"(?:mom|mum|mother|mommy|mummy|dad|daddy|father|papa|mama|grand\w+|granny|nana|nani|dada|dadi|uncle|aunt|auntie|brother|sister|husband|wife|parents|spouse)(?:['’]s)? (?:\w+ ){0,2}?pass(?:es|ed)?(?=\s*(?:[?.!]|$))"
)
_ROUND7 = (
    # Latin Hinglish recovery of a relative, and "main theek ho jaunga"
    r"(?:maa|mummy|mom|mother|papa|pita\w*|dad|father|bhai\w*|behen|bahen|didi|nani|dadi|nana|dada|chacha|chachi|mama|mami|bua|mausi|beta|beti|patni|pati|biwi|husband|wife|saas|sasur|bhabhi|jija\w*)"
    r"(?:\W+\w+){0,5}?\W+(?:theek|thik|thek) (?:ho )?(?:ja\w*|hog\w*|hon\w*|pa\w*)|(?:main|mai|mein) (?:\w+ )?(?:theek|thik) ho (?:jaunga|jaungi|jaaunga|jaaungi|paunga|paungi)|"
    r"gu[zj]ar(?:enge|egi|ega|ungi|unga)|guzr(?:enge|egi|ega)|"
    # lifespan and death idioms
    r"(?:be|stay|remain) around (?:for|to see|till|until|when)|around to see|(?:leave|leaves|leaving) us (?:this|next|soon|before|early|young|in \d)|"
    r"outlast\w*|(?:journey|time|stay|days) on (?:this )?earth|(?:his|her|their|my|your|the) journey (?:\w+ )?(?:end|ends|ending|over)\b|"
    r"(?:put|putting) (?:\w+ ){0,3}?(?:down|to sleep)(?=\s*(?:[?.!,;]|$|this|next|soon|in \d|before))|"
    # accidents and injuries
    r"(?:hit|struck|run over|knocked down|run down|mowed down) by (?:an? |the )?(?:car|bus|truck|lorry|train|vehicle|bike|motorcycle|taxi|auto|rickshaw|tractor)|run over|"
    r"hit[- ]and[- ]run|collision|electrocut\w*|stabbed|shot (?:dead|at)|mauled|bitten by (?:an? |the )?(?:snake|dog)|"
    r"(?:fall|fell|falls|falling) (?:from|off) (?:an? |the )?(?:roof|balcony|ladder|building|height|cliff|stairs|horse|bike|terrace)|heat ?stroke|sun ?stroke|"
    # getting better, replacement surgery
    r"(?:mom|mum|mother|mommy|mummy|dad|daddy|father|papa|mama|grand\w+|granny|nana|nani|dada|dadi|uncle|aunt|auntie|brother|sister|husband|wife|friend|son|daughter|baby|child|kid|he|she|they|i)\s+"
    r"(?:\w+ )?(?:get|gets|getting) (?:better|well)(?:\s+soon)?(?=\s*(?:[?.!,;]|$))|"
    r"(?:hip|knee|joint|shoulder|valve|lens|heart|cornea|bone|disc|elbow|ankle)(?: joint)? replacements?|replacement surgery|"
    r"(?:dental|cochlear|breast|hair|retinal|bone|spinal|knee|hip|metal) implants?|implant surgery|"
    # longevity words (book lines too)
    r"ayush\w*|dirgh(?:a|ayu)\w*|ayu\b"
)
_HINGLISH = (
    # Marathi, Tamil, Telugu, Kannada, Malayalam, Punjabi, Gujarati, Bengali, Urdu words for death and illness (Latin letters)
    r"maran|marnar|maranar|saavu|saavaa|maranam|chavu|chaavu|rogam|jabbu|aajar|wafat|wafaat|intiqal|inteqal|inteqaal|faut\w*|marz|marzon|mareez|mareeza|"
    r"bimar\w*|bemar\w*|beemar\w*|bimaari|bemaari|mrutyu|mruthyu|mratyu|mrithyu|mrittu|mritak|guzar (?:gay\w*|jan\w*|jaa\w*|gaya|gayi|gae)|gujar (?:gay\w*|jan\w*|gaya|gayi)|"
    r"chal bas\w*|raam naam satya|ram naam satya|parlok|paralok|param dham|kaal kavalit|kal kavalit|swarg ?lok|swarglok|vaikunth\w*|moksh prapt|"
    r"umar|umr|aayu|bimari|beemari|bimaar\w*|beemaar\w*|rog|roga|rogi|rogon|maut|mrityu|mrtyu|mritu|dehant|dehaant|dehavsan\w*|"
    r"swargvas\w*|swargwas\w*|swarg sidhar\w*|nidhan|ilaaj|ilaj|upchar|swasthya|swasth|sehat|tabiyat|tabiyet|tabeeyat|tabeyat|"
    r"dawai\w*|dawa|dawayein|aspatal|aspataal|haspital|chot|choton|durghatna|durghtna|dard|bukhar|bukhaar|zeher|jahar|"
    r"marne|marna|mar(?:enge|ega|egi|unga|ungi)|mar (?:jaunga|jaungi|jayenge|jayega|jayegi|gaya|gayi|gaye)|"
    r"kab tak (?:jiy\w*|jee\w*|zinda)|jiyenge|jeeyenge|jiyega|jiyegi|jiyunga|jeeunga|jeeungi|zinda nahi|jaan (?:ka|ko) khatra|"
    r"garbhpa\w*|atmahatya|aatmahatya|khudkushi|khudkhushi|"
    r"nahi+n? rah(?:enge|engi|egi|unga|ungi|ega)"
)
_NUM = r"(?:(?:sixty|seventy|eighty|ninety)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|hundred|\d{2,3})"
_KIN8 = (r"elders?|elderly|loved ones?|relatives?|grand(?:parent|mother|father|ma|pa|dad|mum|mom)s?|parents?|mother|father|mum|mom|dad|mama|papa|"
         r"uncle|aunt|auntie|in-laws?|family members?|older (?:persons?|people|members?|relatives?)|seniors?|someone (?:close|dear)")
_ROUND8 = (
    # T11.40: death said by meaning, not by one word: lifespan and expectancy, an age at the end, "not be with us", a life ended or left
    r"life[- ]?expectanc\w*|expectancy of life|years on earth|end[- ]of[- ]life|twilight years|"
    rf"(?:live|lives|living|lived|survive|survives)\s+(?:to|past|beyond|till|until|up to|upto)\s+(?:about |around |nearly |almost |roughly |the age of )*{_NUM}\b|"
    rf"life\W+(?:\w+\W+){{0,5}}?(?:about|around|close to|nearly|almost|roughly|up to)\s+{_NUM}\s+years|"
    r"\b(?:end|ending|close)\b[^.;!?]{0,15}?\b(?:around|near|about|by|at|before|after)\s+(?:the\s+)?age\b|"
    r"(?:not|no longer|never|n['’]t)\s+(?:be|stay|remain)\s+(?:\w+\s+){0,2}with us(?:\s+(?:by|for|beyond|past|after|much|long\w*|next|this|till|until|through|any)\b|\s*(?:$|[.,;!?]))|"
    r"(?:not|n['’]t)\s+(?:be|stay|remain)\s+(?:around|here|alive)\s+(?:by|for|beyond|past|after|much|long\w*|next|this|till|until|through|any)\b|"
    r"(?:not|n['’]t|unlikely to)\s+(?:make it|see)\s+(?:through|out|in|the)\s+(?:the |this |next |new )?(?:\w+ )?(?:year|winter|summer|season|monsoon)|"
    r"(?:leave|leaves|leaving) us (?:soon|before|young|too soon|this year|next year|by (?:year|\d))|"
    r"(?:clos|end|complet|conclud|finish|terminat)\w* (?:\w+['’]?s? ){0,3}?(?:life|lives)(?:\s+journey|\s+here|\s+on earth|\s*(?:$|[.,;!?]))|"
    r"(?:remaining|closing|declining|golden|autumn|last|final) (?:years|days|chapter) of (?:\w+['’]?s? ){0,3}?(?:life|lives|" + _KIN8 + r")"
)
_ROUND9 = (
    # T11.42: a death said by a place or a leaving, not one word: the heavenly or eternal abode, Hinglish "guzar sakna", leaving the
    # world, going to the Lord, last rites. Known over-blocks (accepted): "heavenly abode" of a god in a story, "guzar sakte" in a
    # "pass by" sense, "antim yatra" for a last trip
    r"(?:heavenly|eternal|celestial|final|last) abode|guzar sak\w*|gujar sak\w*|"
    r"(?:duniya|sansar|sansaar) (?:se )?(?:chal|chhod|chod|vida)\w*|(?:ram|bhagwan|bhagvan|prabhu) (?:ji )?(?:ko|ke) (?:pyar|charan)\w*|"
    r"antim (?:sanskar|yatra|saans)|brahm ?lee?n|swarg(?:\s+(?:ko\s+)?(?:ja\w*|sidhar\w*|pahunch\w*|prapt\w*)|vasi)|kooch kar\w*|pran tyag\w*"
)
STRONG = _ENGLISH_CORE + "|" + _ENGLISH_MORE + "|" + _ROUND5 + "|" + _ROUND6 + "|" + _ROUND7 + "|" + _ROUND8 + "|" + _ROUND9 + "|" + _HINGLISH
# the words after "pass on" that keep it a hand-over (a recipe, advice, a thing), not a death. The one list: the family gate in
# render_report.py reads it too, so the two cannot drift.
# T11.44: not when a time expression follows ("pass on the night of Diwali", "this winter", "the coming year", "the 5th of May"): that is a death.
_PASS_ON_TIME = (r"(?:(?:the|a|an|this|that|these|its|your|their|his|her|our|my|next|last|coming|upcoming|following|first|second|third|"
                 r"fourth|fifth|final|every|each)\s+)+(?:\d\w*|nights?|days?|mornings?|evenings?|afternoons?|weeks?|weekends?|months?|"
                 r"years?|seasons?|winters?|summers?|springs?|autumns?|monsoons?|diwali|holi|dussehra|navratri|eid|christmas|new year|"
                 r"festivals?|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|(?:mon|tues|wednes|thurs|fri|satur|sun)day)\b")
PASS_ON_OK = (r"(?!" + _PASS_ON_TIME + r")(?:to|through|the|a|an|this|that|these|it|its|your|their|his|her|our|my|what|knowledge|skills?|"
              r"traditions?|values?|lessons?|work|news|messages?|advice|wisdom|stories)")
# a person who is kin or an elder or a loved one: the subject of the T11.42 leaving and ending patterns below
_KIN9 = (_KIN8 + r"|dada\w*|dadi\w*|nana\w*|nani\w*|papa ?ji|mataji|pitaji|buzurg\w*|dear ones?|senior (?:members?|relatives?)")

# ---------------------------------------------------------------------------------------------------------------------
# Devanagari (Hindi): every entry may carry a suffix (inflection, matra) after the stem
# ---------------------------------------------------------------------------------------------------------------------
DEVA = (
    r"मृत्यु|मौत|मरण|मरना|मरने|मरेंग\w*|मरेग\w*|मरूं\w*|मरूँ\w*|मर (?:जा\w*|गया|गई|गए)|निधन|देहांत|देहावसान|देहान्त|स्वर्गवास|स्वर्ग सिधार\w*|"
    r"बीमार\w*|रोग\w*|आयु\w*|उम्र|उमर|उमरा|उमर्|आखिरी (?:वक्त|वक़्त|साँस|सांस|समय|दिन|पल)|आख़िरी (?:वक्त|वक़्त|साँस|सांस|समय)|आखरी (?:वक्त|सांस|समय)|"
    r"अंतिम (?:समय|सांस|साँस|दिन|यात्रा|संस्कार|क्षण)|कितना जिएंगे|ऑपरेशन|ओपरेशन|अस्पताल|इलाज|दवा\w*|दवाई|स्वास्थ्य|सेहत|तबीयत|तबियत|दुर्घटना|हादसा|चोट\w*|"
    r"नहीं रहेंग\w*|नहीं रहेग\w*|नहीं रहूं\w*|नहीं रहूँ\w*|जीवनकाल|जीवन काल|गर्भपात|आत्महत्या|खुदकुशी|कैंसर|ट्यूमर|बुखार|दर्द|ज़हर|जहर|"
    r"शोक|अंतिम संस्कार|दाह संस्कार|श्मशान|कब्र|जनाज़ा|जनाजा|विधवा|विधुर|अल्पायु|दीर्घायु|मारकेश|अरिष्ट|हृदयाघात|दिल का दौरा|लकवा|"
    r"पक्षाघात|मधुमेह|अपाहिज|विकलांग|कोमा|आईसीयू|वेंटिलेटर|प्रत्यारोपण|चिकित्सा|उपचार|डॉक्टर|कब तक जिएंग\w*|कितना जिएंग\w*|जिंदा न रहेंग\w*|"
    r"कीमोथेरेपी|डायलिसिस|संक्रमण|महामारी|कोविड|कोरोना|टीबी|डिप्रेशन|अवसाद|तनाव रोग|"
    r"गुज़र (?:जा|गय|गई|गए)\w*|गुज़र(?:ेंग|ेग|ूं|ूँ|ुए)\w*|गुजर (?:जा|गय|गई|गए)\w*|गुजर(?:ेंग|ेग|ूं|ूँ|ुए)\w*"
)
_DEVA_L = r"(?<![\wऀ-ॿ])"
_DEVA_R = r"(?![\wऀ-ॿ])"
_DEVA_TAIL = r"[ऀ-ॿ]*"

# Devanagari relatives (a family report may not name one: the English shape rule cannot read them)
DEVA_KIN = (r"पिताजी|पिता|पापा|बाबूजी|बाप|माँ|मां|माता|माताजी|मम्मी|भाई|भैया|बहन|बहिन|दीदी|दादा|दादी|नाना|नानी|चाचा|चाची|मामा|मामी|बुआ|"
            r"मौसी|ताऊ|ताई|ससुर|सास|भाभी|देवर|जेठ")

_ME = r"(?:myself|himself|herself|themselves|yourself|ourselves|oneself)"
_POSS = r"(?:my|his|her|their|your|our|one['’]?s)"
SELFHARM = (
    r"suicid\w*|self[- ]?harm\w*|self[- ]?injur\w*|self[- ]?destruct\w*|"
    rf"kill(?:ing|s|ed)? {_ME}|(?:hurt|hurting|hurts|harm|harming|harms|cut|cutting|cuts|poison|poisoning|starv\w*|burn\w*|hit\w*|injur\w*) {_ME}|"
    rf"(?:hang|hanging|hangs|drown|drowning|shoot|shooting|stab|stabbing|choke|choking|strangle|strangling) {_ME}|"
    rf"(?:end|ending|ends|ended|take|taking|takes|took|taken|give|giving|gave|throw|throwing|threw|waste|wasting) {_POSS} (?:own )?(?:life|lives)|"
    r"(?:end|ending|ends|ended) (?:it all|it now|it tonight|everything|the pain)|"
    r"end it all|stop(?:ping|ped)? living|quit(?:ting)? life|"
    r"(?:do(?:es)?(?: ?n['’]?t| not)|did(?: ?n['’]?t| not)|never|no longer|ca(?:n['’]?t| not)|could(?: ?n['’]?t| not)|would(?: ?n['’]?t| not)|"
    r"(?:don|didn|doesn|won|wouldn|can)['’]?t) (?:want|wanted|wish|wished|wanna|wanting)(?:s|ed|ing)? (?:to )?(?:live|living|wake up|be here|be alive|exist|go on|carry on|be around|see tomorrow|"
    r"see another day|be on this earth|stay alive|keep going)|"
    r"(?:want|wants|wanted|wanting|wish|wishes|wished|wishing|wanna|plan|plans|planned|planning|think|thinks|thought|thinking|feel|feels|felt|feeling|"
    r"ready|decide|decides|decided|deciding|try|tries|tried|trying|attempt\w*|about) (?:of |about |like |to |for )?"
    r"(?:to )?(?:die|dying|be dead|be gone|disappear|vanish|not exist|not be alive|not be here|not wake up|never wake up|"
    r"end (?:it|things|everything)|go away forever|be no more|not be around)|"
    r"wish(?:ed|es)? (?:i|he|she|they|we|it) (?:was|were|had|would|could) (?:dead|never been born|never born|not here|not alive|not wake|gone)|"
    r"(?:better|best) off (?:dead|without (?:me|him|her|them|us)|if (?:i|he|she|they) (?:was|were) (?:gone|dead|not here))|"
    r"(?:no|any|a) (?:reason|point|purpose|use|will|hope|meaning)(?: left)? (?:to |in |of |for )?(?:live|living|life|go on|going on|carry on|be here|exist|continue|keep going|on living)|"
    r"(?:life|living|it all|everything|existence) (?:is |was |feels |seems )?(?:not |no |n['’]t |isn['’]t |wasn['’]t )?(?:worth (?:living|it|anything)|pointless|meaningless|hopeless|over|too much|unbearable)|"
    r"not worth living|(?:give|gave|giving|given) up (?:on )?(?:life|living|everything|myself|hope)|"
    r"(?:disappear|vanish|go away|be gone|leave this world|leave everything|run away from (?:life|everything)) (?:forever|for good|permanently|for ever)|"
    r"(?:tired|sick|weary|done|fed up|exhausted|finished) (?:of|with) (?:living|life|being alive|everything|this life|it all)|"
    r"(?:can['’]?t|cannot|can not|couldn['’]?t) (?:go on|take (?:it|this|any more|anymore)|do this (?:any ?more|anymore)|bear it)|"
    r"jump(?:ing|ed|s)? (?:off (?:a |the )?(?:bridge|building|roof|cliff|balcony|terrace|train)|in front of (?:a |the )?(?:train|car|bus|truck)|from (?:a |the )?(?:bridge|building|roof|cliff|balcony|terrace))|pills to (?:die|end)|take (?:all )?(?:my|the) pills|overdos\w* (?:on purpose|myself|to die)|"
    r"death wish|"
    # Hindi and Hinglish in Latin letters
    r"atmahatya|aatmahatya|atmahatya|aatm hatya|atm\w* hatya|khudkushi|khudkhushi|khudkushee|khud ?kushi|suicide|sucide|"
    r"jaan (?:le|lena|lu|loonga|loongi|lunga|lungi|de|dena|du|doonga|doongi|dunga|dungi|dene|lene|ko khatam)\w*|apni jaan|"
    r"mar (?:jana|jaana|jaanaa|jaun|jaaun|jau|jaoon|jaon|jaunga|jaungi|jaoonga|jaoongi) ?(?:chahta|chahti|chahte|chahiye|hai)?|"
    r"mar ?jana chah\w*|marna chah\w*|marne ka (?:man|mann|mood|dil|khayal|vichar|irada)\w*|marne ki (?:ichha|iccha|icchha|soch)\w*|"
    r"(?:jeena|jina|jeene|jine|jeevan|zindagi|zindgi) (?:nahi|nahin|nhi|nai|nahi\w*) (?:chahta|chahti|chahte|chahiye|rakhna|hai)|"
    r"(?:jeena|jina|jeene|jine) (?:ka|ki|ke) (?:man|mann|mood|dil|ichha|iccha|icchha|koi (?:matlab|maksad|mtlb)|maqsad|matlab|mtlb) (?:nahi|nahin|nhi|nai)|"
    r"jeena nahi|jina nahi|jeene ki wajah nahi|zindagi (?:khatam|khtm|se thak\w*|bojh|bekar)|sab (?:kuch )?khatam kar\w*|khatam kar (?:lu|du|loonga|doonga|lunga|dunga|lungi|dungi)\w*|"
    r"zindagi se (?:tang|thak|bezar)\w*|(?:hamesha|hamesha ke liye|humesha ke liye|hmesha ke liye) (?:chala|chali|chale) jau\w*|gayab ho jau\w*|"
    # indirect warning signs
    r"(?:giv(?:e|es|ing)|gave|given) away (?:all )?(?:of )?(?:my|his|her|their) (?:things|stuff|belongings|possessions|savings|money|clothes|books|pets?|valuables)|"
    r"how many (?:\w+ )?(?:pills?|tablets?)|(?:pills?|tablets?) (?:would|will|do|does|to) (?:it )?(?:take|need|kill)|enough (?:pills?|tablets?)|"
    r"overdose amount|(?:lethal|fatal|deadly) dose|painless (?:way|death|method)|easiest way to (?:die|go)|"
    r"what['’]?s the (?:point|use)|what is the (?:point|use)|no (?:point|use)(?: in)? (?:living|going on|anything|trying|continuing)|pointless to (?:live|go on)|"
    r"nothing (?:will|is going to|would|ever|can|could) (?:ever )?(?:change|get better|improve|matter|help)|(?:it|things|life|nothing) (?:will|is going to|would) never (?:get better|change|improve)|"
    r"never (?:going to )?get(?:ting)? better|hopeless\w*|(?:no|without|lost all|lose|lost) hope|"
    r"(?:say|saying|said|bid|tell|telling|told) (?:my )?goodbyes?(?: to)? (?:everyone|everybody|all|them|my (?:family|friends|kids|children|parents|loved ones))|"
    r"goodbye (?:letter|note|message|post)|(?:write|writing|wrote|written|left|leave|leaving) (?:a |my )?(?:last|final|goodbye|farewell|suicide) (?:letter|note|message|words|will)|"
    r"final goodbyes?|last goodbyes?|farewell (?:letter|note)|"
    r"no way out|no exit|no escape|no way (?:to )?(?:go on|forward)|trapped forever|"
    r"(?:can['’]?t|cannot|can not|couldn['’]?t) (?:take|bear|stand|handle|cope|live)(?: with)? (?:it|this|life|living|any ?more|anymore)|"
    r"(?:no ?one|nobody|none) (?:would|will|['’]d) (?:even )?(?:miss|notice|care|cry|mourn)|(?:no ?one|nobody) (?:cares|needs|wants|loves)(?: about)? me|"
    r"(?:a )?burden (?:to|on) (?:everyone|everybody|my family|them|all|others)|(?:everyone|everybody|they|the world|my family) (?:would|will|['’]d) be better off|"
    r"wish (?:i|he|she|they) (?:was|were|had) never (?:been )?born|wish i (?:could )?(?:just )?(?:sleep|go to sleep) (?:forever|and never)|"
    r"(?:noose|rope|gun|razor|bridge|cliff|rooftop|train tracks?|poison|knife|blade)\b(?:\W+\w+){0,6}?\W+(?:myself|my life|end it|ending it|kill|die|dying|suicide)|"
    r"(?:myself|my life|end it|ending it|kill|die|dying|suicide)\b(?:\W+\w+){0,6}?\W+(?:noose|rope|gun|razor|bridge|cliff|rooftop|train tracks?|poison|knife|blade)|"
    r"noose|(?:goodbyes?|farewell)\b[^.?!]{0,40}(?:last time|forever|for good|final)|"
    r"koi (?:fayda|faida|fayada|phayda) nahi|kuch (?:fayda|faida|phayda) nahi|sab (?:kuch )?khatam(?: ho)?|ab (?:aur )?(?:jeena|jina) nahi|aur nahi (?:jeena|jina)|jeena nahin chah\w*|"
    r"(?:sabko|sab ko|duniya ko) alvida|alvida (?:duniya|sabko|sab)|mere bina (?:sab )?(?:theek|khush|accha)\w*|koi (?:nahi|nhi) (?:chahta|chahti|samajhta|samajhti)|"
    r"mar jaun to|mar jaaun to|mar jau to"
)
# Round 5 (REVIEW.md "Re-check 4"): indirect and coded signs. When in doubt the crisis referral wins, so these are wide on purpose.
_SH5 = (
    # written goodbyes, plural too
    r"(?:writ(?:e|es|ing|ten)|wrote|left|leav(?:e|es|ing)|pen(?:ned|ning)?|drafted|drafting|finish(?:ed|ing)|sent|sending|post(?:ed|ing)?|composed) (?:\w+ ){0,2}?"
    r"(?:(?:goodbye|good-?bye|farewell|suicide|parting|last|final) (?:letters?|notes?|words|will|videos?)|(?:goodbye|good-?bye|farewell|suicide|parting) (?:messages?|emails?|texts?|posts?))|"
    r"(?:goodbye|good-?bye|farewell|suicide|parting) (?:letters?|notes?|messages?|emails?|texts?|posts?|videos?)|"
    # stockpiling or swallowing pills
    r"(?:stockpil\w*|hoard\w*|stash\w*|sav(?:e|es|ed|ing) up|collect(?:ing|ed|s)?|gather(?:ing|ed|s)?|(?:putting|set(?:ting)?|keep(?:ing)?) aside|hiding) "
    r"(?:\w+ ){0,3}?(?:pills|tablets|meds|medication|medicines?|painkillers|sedatives|capsules)|"
    r"(?:pills|tablets|meds|medication|painkillers|sedatives|capsules) (?:\w+ ){0,3}?(?:stockpil\w*|stashed|hoarded|saved up|put aside|set aside)|"
    r"(?:swallow\w*|gulp\w*|down(?:ing|ed)?|popp(?:ing|ed)|eat(?:ing)?|ate|take|taking|took) (?:a |the |my |all |every )?(?:whole |entire )?(?:handful|bottle|strip|pack|packet|box|whole|entire)s? (?:of )?(?:\w+ )?(?:pills|tablets|meds|medication|medicines?|sleeping|capsules)|"
    r"sleeping (?:pills|tablets)|(?:pills|tablets) (?:and|with|or) (?:alcohol|whisky|whiskey|vodka|liquor|booze|wine)|"
    # sleep and never wake
    r"(?:sleep|sleeping|asleep|drift(?:ing)? off|close my eyes)\b[^.?!]{0,30}\b(?:never|not|no more) (?:to )?(?:wak\w*|open (?:them|my eyes)|get(?:ting)? up|come back|awake)|"
    r"sleep(?:ing)? forever|forever sleep|eternal sleep|permanent sleep|(?:sleep|rest) for good|never (?:to )?wake up again|(?:not|never) wake up (?:again|tomorrow|in the morning|tonight)|"
    r"(?:wish|hope|hoping|pray|praying) (?:i |that i |to )?(?:would |could |will |do |don['’]?t |do not )?(?:not|never) (?:to )?wake|"
    # rope, noose, gun, pills in view
    r"(?:look(?:ing|ed|s)?|star(?:e|es|ed|ing)|gaz(?:e|es|ed|ing)|eye(?:ing|d)?|buy(?:ing)?|bought|order(?:ed|ing)?|hid|hide|hiding|"
    r"prepar(?:e|ed|ing)|pick(?:ed|ing)? up) (?:\w+ ){0,4}?(?:rope|noose|ligature|pistol|revolver|firearm|razor|gun|pesticide|rat poison|pills|tablets)\b|"
    r"think(?:ing)? (?:about|of) (?:\w+ ){0,2}?(?:rope|noose|ligature|gun|pistol|pills|tablets)\b|"
    r"(?:rope|noose|ligature|belt|scarf|dupatta|sari|cord|wire)\b(?:\W+\w+){0,6}?\W+(?:ceiling|fan|neck|beam|garage|tree|rafter|hook|hang\w*|throat)|"
    r"(?:ceiling fan|beam|rafter|hook|tree|garage)\b(?:\W+\w+){0,6}?\W+(?:rope|noose|ligature|hang\w*)|"
    r"around my neck|(?:hang|hung|hanging) (?:from|off)|"
    # coded words and euphemisms
    r"un-?aliv\w*|kys\b|sewer ?slid\w*|self[- ]?delet\w*|self[- ]?terminat\w*|self[- ]?eliminat\w*|self[- ]?immolat\w*|"
    r"(?:off|offing) (?:my ?self|himself|herself)|do(?:ing|es)? away with (?:my ?self|himself|herself|my life)|do(?:ing)? (?:myself|himself|herself) in|"
    r"(?:exit|check(?:ing)? out of|opt(?:ing)? out of|log(?:ging)? off from|bow(?:ing)? out of|bail(?:ing)? (?:out )?(?:on|from)|escap(?:e|ing)) (?:from )?(?:this )?(?:life|world|existence|earth|living)|"
    r"(?:kill|end|murder|finish) me\b|(?:put|putting) an end to (?:my |this |it |the |all )?(?:life|existence|suffering|pain|myself|it all|things|everything|living)|"
    r"(?:end|ended|ending|finish\w*|terminat\w*|conclud\w*) (?:\w+ ){0,2}?(?:my|own) (?:life|existence|suffering|pain)|"
    r"(?:end|ends|ending|ended) (?:things|it|my suffering|my pain|the suffering) (?:tonight|today|tomorrow|now|soon|for good|once and for all|this (?:week|weekend|month|year))|"
    r"(?:think(?:ing)?|thought|plan(?:ning|ned|s)?|consider(?:ing|ed)?|contemplat\w*|decid\w*|ready|about|want(?:ed|ing)?|wanna|need(?:ed)?) (?:\w+ ){0,2}?(?:to |of |about )?end(?:ing)? (?:everything|my life)\b|"
    r"(?:want|wanting|wish|need|wanna) (?:it )?all to (?:be over|end|stop)|(?:want|wanna|need) (?:to be )?out of (?:this )?(?:life|world|everything)|"
    r"(?:thinking|thought|think|planning|plan|contemplating|about) (?:of |about |to )?jump(?:ing)?\b|edge of (?:the |a )?(?:terrace|roof|cliff|bridge|balcony|building|platform)|"
    r"goodbye,? (?:cruel )?world|"
    r"wish (?:i|he|she|they) (?:could |would |will |can )?(?:just )?(?:die|disappear|vanish|stop existing|not exist|be dead|sleep forever|fall asleep forever|never wake|not wake)|"
    # goodbyes and being gone
    r"(?:won['’]?t|will not|not going to|am not going to) (?:\w+ )?(?:be (?:here|around|alive)(?: much)? (?:longer|anymore|any more|tomorrow|after (?:tonight|today|this))|"
    r"see (?:tomorrow|the (?:morning|sunrise|next day)|another day)|make it (?:through|to (?:tomorrow|morning)))|"
    r"(?:last|final) (?:night|day|hours?|moments?|days?|time) (?:on earth|alive|of my life)|(?:my|the) (?:last|final) (?:message|text|post|breath)|"
    r"(?:when|after|once|if) i(?:['’]m| am| was| were)? (?:dead|not here|not around)|(?:when|after|once|if) i (?:die|leave this world)|if i weren['’]?t here|if i wasn['’]?t here|"
    r"(?:plan|planning|planned|arrang\w*|organi[sz]\w*|prepar\w*|writ\w*) (?:\w+ ){0,2}?(?:my|own) (?:funeral|death|exit|ending|will|suicide)|"
    r"(?:everyone|everybody|they|world|family|parents|mom|dad|mother|father) (?:would|will|['’]d)(?: be)? (?:happier|easier|better|fine|safer|relieved|free) "
    r"(?:without me|if i (?:was|were) (?:gone|dead|not here|not around)|if i (?:disappeared|died|vanished|never existed))|"
    # worth, burden, hopelessness
    r"(?:shouldn['’]?t|should not) (?:even )?(?:be here|exist|be alive|have been born|have lived)|(?:hate|hating|loathe|despise) (?:being alive|my life|existing|my existence|living like this)|"
    r"(?:make|making) (?:it|the pain|everything|all of this|this) (?:stop|end|go away)|(?:want|wanting|need|wish) (?:\w+ )?(?:it|the pain|everything|all of this|this|the noise) to (?:stop|end|be over|go away)|"
    r"(?:tired|sick|weary|done|fed up|exhausted|finished) (?:of|with) (?:\w+ ){0,2}?(?:pretending|surviving|existing|breathing|being here|this world|the world|this pain|the pain|my life)|"
    r"(?:don['’]?t|can['’]?t|cannot|couldn['’]?t) see (?:a |any )?way out|(?:nothing|no one|nobody) (?:left )?to live for|(?:can['’]?t|cannot|couldn['’]?t) (?:keep|go) (?:on )?(?:fighting|living|pretending|doing this)|"
    r"(?:the )?(?:pain|suffering|darkness|emptiness) (?:won['’]?t|will not|never) (?:stop|end|go away)|(?:can['’]?t|cannot|couldn['’]?t) (?:face|survive|get through) (?:another day|tomorrow|another night)|"
    # method words
    r"cut(?:ting|s)? (?:my |his |her |their )?(?:wrists?|veins?|thighs?|throat)|slit(?:ting)? (?:my |his |her )?(?:wrists?|throat)|bleed(?:ing)? (?:out|to death)|"
    r"(?:step|stepping|stood|stand|standing|lie|lying|lay|throw\w*)(?: myself)? (?:out )?(?:in front of|under) (?:a |the |an |oncoming |moving |speeding )?(?:train|truck|bus|metro|car|traffic|vehicle)|"
    r"(?:lie|lying|lay|sleep|sleeping) on (?:the )?(?:train )?(?:tracks|railway)|"
    r"walk(?:ing)? into (?:the )?(?:sea|river|ocean|lake|canal|traffic|water)\b(?:\W+\w+){0,4}?\W+(?:never|not (?:come|return)|disappear|forever|drown|end)|"
    r"jump(?:ing|ed|s)? (?:\w+ )?(?:in|into|off|from) (?:the |a )?(?:river|sea|ocean|lake|canal|well|water|fan|window|flat|apartment|tower|dam|heights?|terrace|balcony|metro)|"
    r"(?:drink|drinking|swallow\w*|consum\w*|took|taking|take|ingest\w*) (?:\w+ ){0,3}?(?:poison|pesticide|rat poison|bleach|phenyl|kerosene|harpic)|"
    r"(?:i['’]?ll|i will|i am going to|i['’]?m going to|i plan to|i['’]?m planning to|i have decided to|i['’]?ve decided to|i decided to) (?:finally )?(?:end it|not be here)|"
    # Hinglish in Latin letters
    r"(?:neend|nind|sone) (?:ki )?(?:goli|goliyan|goliya|tablet\w*|dawai\w*|dawa)|(?:goli|goliyan|goliya|tablets?) (?:kha|khaa|jama|ikatth?i|ikkatha)\w*|"
    r"(?:fans[ie]|phans[ie]|phanda|fanda|rassi) (?:\w+ ){0,3}?(?:laga|lag|le|lu|lunga|loonga|kar|latak|chadh)\w*|(?:pankhe|pankhey) se (?:latak|jhool|fans|fas)\w*|"
    r"(?:nas|naas|hath|haath|kalai) kaat\w*|(?:zeher|zehar|jahar|zahar|vish|poison) (?:kha|khaa|pi|pee|peena|pina|le|lunga|loonga)\w*|"
    r"(?:chhat|chat|pul|bridge|building|terrace|balcony) se (?:kud|koodh|kood|gir|chhalang|chalang)\w*|(?:train|gaadi|gadi|metro|truck|bus) ke (?:aage|niche|neeche|samne|saamne) (?:kud|kood|aa|let|so|gir|ghus)\w*|"
    r"(?:kabhi|hamesha) (?:na|nahi|nahin|nhi) (?:uth|jag|jaag)\w*|(?:hamesha|humesha|hmesha) (?:ke liye )?(?:so|soo) (?:jana|jau|jaun|jaaun|ja)\w*|"
    r"mujhe (?:maar|mar) (?:do|dalo|daalo|jane do|jaane do)|(?:kaash|kash) (?:main |mai |mein )?(?:mar|paida hi na|paida hi nahi)\w*|paida hi (?:na|nahi|nahin|nhi) (?:hua|hota|hui|hoti)|"
    r"(?:main|mai|mein|me|hum) (?:sab ?ke ?liye )?(?:bojh|burden|bhaar)(?: hu| hun| hoon| ban)\w*|(?:mere|meray) (?:na hone|marne|mar jaane) (?:ke baad|se|par|pe)\b|"
    r"(?:kisi ko|kisiko) (?:fark|farak|parwah|parwaah|zarurat|zaroorat) (?:nahi|nahin|nhi)\w*|koi (?:yaad|miss) (?:nahi|nahin|nhi) karega|"
    r"jee kar kya|jeekar kya|jee ke kya|jeke kya|ji ke kya|jina kyu|jeena kyu|"
    r"(?:ab )?(?:aur )?(?:nahi|nahin|nhi|na) (?:jee|ji|jiy|jeey)(?:na|nunga|ungi|unga|oonga|oongi|enge|egi|ega)\b|"
    r"zindagi (?:ko )?(?:khatam|end)|marr? (?:hi )?(?:jau|jaun|jaaun|jaoon|jaunga|jaungi)\b|mar (?:jaata|jata|gaya hota|gayi hoti) to|"
    r"zindagi (?:se )?(?:ab )?(?:thak|tang|bezaar|bezar|haar)\w*|duniya (?:chhod|chod)(?:ne| kar| ke| dunga| dungi)\w*|sab (?:kuch )?(?:chhod|chod) (?:ke|kar|k) (?:ja|chala|chali)\w*"
)
SELFHARM = SELFHARM + "|" + _SH5
SELFHARM_DEVA = (
    r"आत्महत्या|आत्म हत्या|आत्मघात\w*|खुदकुशी|खुदकशी|ख़ुदकुशी|खुद को (?:खत्म|ख़त्म|मार|नुकसान|चोट)\w*|ख़ुद को (?:खत्म|ख़त्म|मार|नुकसान|चोट)\w*|"
    r"जान (?:लेना|देना|देने|लेने|दे दूं|दे दूँ|दे दूंगा|ले लूं|ले लूँ|ले लूंगा|को खत्म|को ख़त्म)\w*|जान दे\w*|अपनी जान|"
    r"मर (?:जाना|जाऊं|जाऊँ|जाउं|जाऊंगा|जाऊँगा|जाऊंगी|जाऊँगी|जाउंगा) ?(?:चाहत\w*|चाहिए)?|मरना चाहत\w*|मरने (?:का|की|के) (?:मन|इरादा|इच्छा|ख्याल|खयाल|विचार|सोच)\w*|"
    r"जीना नहीं चाहत\w*|जीने (?:का|की|के) (?:मन|इच्छा|कोई मतलब|कोई मक़सद|कोई मकसद|वजह) नहीं|जीने की वजह नहीं|"
    r"(?:ज़िंदगी|जिंदगी|जीवन) (?:खत्म|ख़त्म|से थक|बोझ|बेकार)\w*|सब (?:कुछ )?(?:खत्म|ख़त्म) कर\w*|खत्म कर (?:लूं|लूँ|दूं|दूँ|लूंगा|लूँगा|दूंगा|दूँगा)\w*|"
    r"हमेशा के लिए (?:चला|चली|चले) जा\w*|गायब हो जा\w*|सुसाइड|आत्महन\w*|"
    r"(?:अब )?(?:और )?नहीं जीना(?: \S+){0,2}|जीना(?: \S+){0,3} नहीं चाहत\w*|जी(?:ना|ने)(?: \S+){0,3} नहीं(?: \S+){0,2} चाहत\w*|और नहीं जी\w*|"
    r"जीने का (?:कोई )?(?:मतलब|मकसद|मक़सद) नहीं|जीने की (?:कोई )?(?:वजह|इच्छा) नहीं|मरना चाहत\w*|मर जाना चाहत\w*|मर जाऊं तो|मर जाऊँ तो|"
    r"कोई (?:फायदा|फ़ायदा|फायदा) नहीं|सब (?:कुछ )?(?:खत्म|ख़त्म)(?: हो)?|अलविदा (?:कह|दुनिया|सबको)|सबको अलविदा|मेरे बिना सब|"
    r"कितनी गोलियां|कितनी गोलियाँ|गोलियां खा|नींद की गोलियां|फांसी|फाँसी|नस काट|हाथ काट|पुल से कूद\w*|छत से कूद\w*|कूद जा\w*"

    # round 5
    r"गोलियां? (?:जमा|इकट्ठ\w*)|गोलियाँ (?:खा|जमा|इकट्ठ)\w*|फंदा|रस्सी (?:से|पर|का|को)|पंखे से (?:लट|झूल)\w*|लटक (?:जा|कर|के)\w*|"
    r"ज़?हर (?:खा|पी|पि)\w*|नस(?:ें)? काट\w*|कलाई काट\w*|हाथ की नस|"
    r"(?:कभी|हमेशा) (?:न|नहीं) (?:उठ|जाग)\w*|हमेशा के लिए सो\w*|"
    r"मुझे (?:मार|मर) (?:दो|डालो|जाने दो)|काश (?:मैं )?(?:मर|पैदा ही न)\w*|पैदा ही (?:न|नहीं) (?:हुआ|होता|हुई|होती)\w*|"
    r"(?:मैं|सबके लिए) बोझ (?:हूँ|हूं|बन)\w*|मेरे (?:न होने|मरने|मर जाने) (?:के बाद|से)|"
    r"किसी को (?:फ़?र्क|परवाह|ज़?रूरत) (?:नहीं|नही)\w*|कोई (?:याद|मिस) नहीं करेगा|कोई (?:रोएगा|रोयेगा) नहीं|"
    r"जीकर क्या|जी कर क्या|जीने का क्या (?:मतलब|फायदा)|क्यों जिऊं|क्यों जीना|"
    r"(?:मर|मर ही) जाऊं|(?:मर|मर ही) जाऊँ|मर जाता तो|मर गया होता|मर गई होती|"
    r"आख़िरी (?:ख़त|खत|चिट्ठी|पत्र|संदेश|मैसेज)|आखिरी (?:खत|चिट्ठी|पत्र|संदेश|मैसेज|अलविदा)|अलविदा (?:पत्र|चिट्ठी|खत|संदेश)|"
    r"ज़?िंदगी से (?:थक|तंग|हार|ऊब)\w*|दुनिया (?:छोड़|छोड़ने|छोड़कर|से चला|से चली|से चले|से जा)\w*|"
    r"सब (?:कुछ )?छोड़ (?:के|कर) (?:चला|चली|जा)\w*|(?:अब )?(?:और )?(?:नहीं|नही) (?:सह|जी)\w*|रहना नहीं चाह\w*"
)
SELFHARM_DEVA = unicodedata.normalize("NFC", SELFHARM_DEVA)   # the text is NFC-normalised (nukta decomposed): the pattern must be too

# Round 6 (REVIEW.md "Re-check 5"): last night, method enquiries, cutting, a will and "ready to go", "dye" for die, Hinglish and Devanagari forms
_SH6 = (
    r"(?:tonight|today) is my (?:last|final) (?:night|day)|"
    r"(?:don['’]?t|do not|can['’]?t|cannot|won['’]?t) (?:see|picture|imagine) myself (?:being (?:here|alive|around)|alive|(?:here|around) (?:next year|much longer|anymore|any more|after))|"
    r"how (?:high|tall|far|deep) (?:\w+ ){0,6}?(?:building|bridge|balcony|roof|rooftop|terrace|cliff|tower|floor|window|fall|jump|river|water|lake)\b(?:\W+\w+){0,6}?\W+(?:need|has to|have to|must|enough|to be|kill|die|fatal)\w*|"
    r"how (?:high|tall) (?:does|do|must|should|would) (?:a |an |the )?(?:building|bridge|balcony|roof|rooftop|terrace|cliff|tower|floor|window)\b|how far is the fall|"
    r"(?:which|what) (?:medicines?|pills|tablets|drugs|meds|medications) (?:\w+ ){0,3}?(?:together|combin\w*|mix\w*|kill|fatal|lethal)|"
    r"mix(?:ing)? (?:\w+ ){0,3}?(?:pills|tablets|medicines?|drugs|meds) (?:with|and) (?:alcohol|\w+ (?:pills|tablets))|"
    r"how long (?:does|will|would|do) it take (?:to|for (?:me|someone|a person) to) (?:die|bleed|suffocate|drown|choke|stop breathing|pass out|fall asleep forever)|"
    r"how (?:much|many) (?:\w+ ){0,3}?(?:to|for) (?:die|overdose|kill)|(?:fastest|quickest|easiest|best|sure|surest|least painful|painless) (?:ways?|methods?) (?:to |of )?(?:die|dying|go|end|kill|leave|disappear)|"
    r"cut(?:ting|s)? (?:my |myself|my own )?(?:arms?|legs?|wrists?|thighs?|skin|body|stomach|chest)|cut(?:ting)? myself|cut(?:ting)? (?:again|deeper)|"
    r"(?:started|start|relapsed|back to|going back to|urge to|want to|wanna|need to) cutting|"
    r"burn(?:ing|ed|s)? (?:my |myself|my own )?(?:arms?|legs?|wrists?|thighs?|skin|body|hands?)|(?:scratch|scratching|pinch|pinching|bang|banging|hurt|hurting) (?:my ?self|my (?:arms?|wrists?|skin))|"
    r"(?:wrote|written|drafted|made out|signed|made|updated|finished) (?:my|a) (?:last )?(?:will|testament)\b(?:\W+\w+){0,10}?\W+(?:ready|go|leave|goodbye|done|time|bye)|"
    r"ready to go\b(?:\W+\w+){0,10}?\W+(?:will|goodbye|last|testament)|(?:will|goodbye|last|testament)\b(?:\W+\w+){0,10}?\W+ready to go|"
    r"(?:put|putting|set|setting|got|getting|settled|settling) (?:my )?affairs in order|(?:gonna|gona) (?:just )?(?:die|end it|kill)|"
    r"(?:khud|apne aap) ko (?:maar|mar|khatam|mita)\w*|khud ko (?:nuksan|chot|kaat|jala)\w*|khudko (?:maar|mar|khatam)\w*"
)
SELFHARM = SELFHARM + "|" + _SH6

# Round 7 (REVIEW.md "Re-check 6"): researching ways to go, giving things away, "feel like ending it", kms after a want word
_SH7 = (
    r"(?:research\w*|look(?:ing)? up|read(?:ing)? about|google\w*|search(?:ing)? for) (?:\w+ ){0,2}?(?:ways|how|methods?) (?:to )?(?:go|die|end it|leave|disappear|check out)\b|"
    r"go(?:ing)? (?:quietly|peacefully|painlessly)\b|"
    r"(?:gave|giving|give|gives|given)\b[^.?!]{0,50}\b(?:because|since|as|so)\b[^.?!]{0,15}(?:won['’]?t|will not|not going to|never going to) be (?:around|here|there|alive)|"
    r"(?:feel(?:ing)?|felt) like (?:just )?end(?:ing)? (?:it|it all|things|everything|life|my life)\b|"
    r"(?:want|wanna|gonna|gona|gotta|going to|i['’]?ll|i will|i['’]?d|should|may as well|let me|let['’]?s|lets|to|just) (?:just )?(?:kms|kys)\b|(?:kms|kys)\b(?= (?:tonight|today|now|soon|lol|fr|rn))"
)
SELFHARM = SELFHARM + "|" + _SH7
_SH6_DEVA = (
    r"(?:अब )?(?:मुझे )?(?:और )?जीना (?:ही |भी )?(?:नहीं|नही)|(?:मैं |मुझे )?(?:अब )?(?:जिंदा रहना|ज़िंदा रहना|जीने|रहना) (?:ही |भी )?(?:नहीं|नही) (?:चाहत\w*|है)|"
    r"(?:मरना|मर जाना|गायब हो जाना) (?:ही |भी )?(?:चाहत\w*|चाहिए)|(?:मैं )?(?:खुद|ख़ुद|अपने आप) को (?:ही )?(?:खत्म|ख़त्म|मार|मिटा|नुकसान|चोट)\w*|"
    r"मर (?:ही |भी )?जाऊं|मर (?:ही |भी )?जाऊँ|(?:आज|आज की) रात (?:मेरी )?(?:आखिरी|आख़िरी) रात|आज मेरी आखिरी रात|मैं (?:अब )?(?:यहाँ|यहां) (?:ज्यादा देर|ज़्यादा देर) नहीं|"
    r"(?:खुद|अपने आप) को (?:काट|जला)\w*|हाथ (?:काट|जला)\w*"
)
SELFHARM_DEVA = unicodedata.normalize("NFC", SELFHARM_DEVA + "|" + _SH6_DEVA)

BOOK_EXTRA = (r"doctors?|deadly|cure\b|cured|arsas|bhagandhara|leprosy|leper\w*|consumption|phthisis|colic|insanity|epilepsy|blindness|"
              r"deafness|lameness|dropsy|scabies|rheumat\w*|diarrh\w*|dysentery|vomit\w*|slay\w*|slain|lunacy|leprous|"
              r"small-?pox|chicken-?pox|pox|measles|mumps|rabies|tetanus|scurvy|ringworm|gout|goitre|goiter|cough\w*|catarrh|cold and cough|"
              r"lame(?:ness|d)?|cripple\w*|dumb\w*|deaf\w*|mute(?:ness)?|blind(?!\s+planets?)\w*|squint\w*|stammer\w*|stutter\w*|"
              r"hunchback\w*|dwarf\w*|deform\w*|leucoderma|vitiligo|eczema|boils?|abscess\w*|insane|mad(?:ness| man| woman)|"
              r"sterile|impotent|miscarriage|abortion|bleeding|haemorrhage|hemorrhage|cholera|plague|fainting|swoon\w*|"
              r"weak(?:ness)? of (?:body|health|constitution)|snake-?bites?|\w*life[- ]?spans?|spans?|(?:span|length|term|duration) of (?:\w+ )?life|"
              r"(?:deprive\w*|death|loss|lose|lost|bereave\w*|dies?|died|demise|widow\w*)\b[^.\n]{0,60}early in life|"
              r"early in life\b[^.\n]{0,60}(?:deprive\w*|death|loss|lose|lost|dies?|died|demise|widow\w*)|"
              r"deprive\w* (?:\w+ ){0,3}?of (?:his |her |the |one['’]?s |their )?(?:father|mother|parents?|wife|husband|spouse|brother|sister|children|sons?|daughters?|life|health|eyesight|sight|limbs?)|"
              r"early (?:death|loss|demise|bereavement)|(?:threat|danger|risk|fear) (?:of|to) (?:\w+ ){0,3}?(?:the |his |her )?(?:spouse|wife|husband|father|mother|parents?|children|sons?)|"
              r"loss (?:of|to) (?:the |his |her |one['’]?s )?(?:spouse|wife|husband|father|mother|parents?|children|sons?|daughters?)|"
              r"(?:dies?|expires?|death) (?:at|before|after|in) (?:the )?(?:age|years?) (?:of )?\d+|disorders?")

# Report strings: STRONG plus these (the old render_report _MED, less what STRONG now carries). The two entries that
# need the relative-word list stay in render_report.py.
REPORT_WORDS = (
    r"last rites|clinics?|clinician\w*|chronic|convalesc\w*|slipped disc|laid up|under the knife|"
    r"treatment\w*|therap\w*|doctors?|operations?|passing(?!\s+phase)|pass\w* away|"
    r"balarishta|outliv\w*|graves?|"
    r"bedside|carers?|(?:be|been|is|are|was|were|get|gets|got)\s+gone|gone by|not see\s+(?:\d{4}|the year)|not wake|"
    r"goodbye|in memory of|bereave\w*|mourn\w*|griev\w*|grief|"
    r"old age|nursing|care home|wheelchair|miscarr\w*|blind\w*|bur(?:y|ied)|"
    r"(?<!\bto )heart(?!\s+of\b)|brain|spine|spinal|bones?|blood(?!\s+relat\w+)|skin|teeth|throat|nerves?|joints?|time on earth|years left|"
    r"leaves? this world|next world|called home|breathe\w* (?:his|her|their) last|last (?:days|years|breath)|"
    r"final (?:years|days|illness)|(?:long|short)(?:er)?(?:-| )?(?:life|lives|lived)|live (?:long|short)|"
    r"(?:fragile|weak|strong|delicate|robust|sturdy|poor|sound|good|frail) constitution|your constitution|"
    r"no longer (?:be )?with us|taken from (?:you|us)|cur(?:e|ed|es) of|(?:lingering|chronic|persistent|recurring|long-standing) complaints?|"
    r"(?:your|his|her|their) recovery|heirs?|vision|"
    r"psychiatr\w*|anxiety|trauma\w*|burn(?:s|ed|t)? (?:out|down)|stents?|crutch\w*|allerg\w*|hernia|seizures?|insulin|asthma|migraines?|hospice|"
    r"defects?|bypass\w*|laid to rest|heat ?stroke|sun ?stroke|replacements?|journey on earth|limbs?|casts?(?= (?:on|for|around)\b)|(?:arm|leg|foot|wrist|ankle|hand) cast|braces|(?:walking )?canes?|walkers?(?= (?:for|to help)\b)|impair\w*|mobility (?:issues?|problems?)|"
    r"hearing devices?|speech therapy|sessions? of therapy|exercises? for (?:your|his|her|their) (?:back|knee|neck|shoulder)|recover(?:y|ing) (?:from|after)|"
    # T11.38: the end of a life said without a death word (risk to life, a life cut short, passed on, days numbered)
    r"(?:risk|threat|danger|peril|fear)s? (?:of|to) (?:\w+ ){0,2}?li(?:fe|ves)|li(?:fe|ves) (?:\w+ ){0,2}?(?:cut )?short|cut short|"
    r"(?:end|ending|close) (?:of|to) (?:\w+['’]?s? ){0,3}?life|"
    r"(?:los(?:e|es|ing|t)|loss of) (?:a |his |her |their |your |one['’]?s |the )?li(?:fe|ves)|"
    r"(?:tak(?:e|es|ing)|took|claim\w*) (?:a |his |her |their |one['’]?s |the )li(?:fe|ves)|"
    r"pass(?:es|ed)? on(?!\s+" + PASS_ON_OK + r"\b)|(?:not|never|won['’]t|fail\w* to|unable to) survive|"
    r"days (?:\w+ ){0,2}?numbered|leaves? (?:this|the) (?:earth|life|world)|left this (?:earth|life|world)|"
    # batch 3 (T11.30): fertility, pregnancy, birth health, potency and the reproductive body, for the children and intimacy reports.
    # Known over-blocks (accepted): "fertile ground", "conception" of a project, "give birth to an idea"
    r"fertil\w*|pregnan\w*|conceiv\w*(?!\s+(?:of|a plan|an idea|the idea|the plan)\b)|conception|child-?birth|(?:give|gives|gave|giving) birth|"
    r"expectant|expecting (?:a |an |your |the )?(?:baby|child|little|twins|first|second|phase)|in the family way|"
    r"potency|virility|sperm\w*|ovulat\w*|contracepti\w*|menstru\w*|prenatal|antenatal|postnatal|breast-?feed\w*|lactat\w*|"
    r"(?:safe|easy|smooth|normal|difficult|hard|complicated) (?:delivery|deliveries|birth|labou?r)|"
    # T11.40: a person who may "pass", or a loved one or elder lost, taken or leaving. "pass" with an exam, a place, a phase or a thing stays free
    rf"(?:{_KIN8})\w*[^.;!?]{{0,60}}?\bpass(?:es|ed)?\b(?!\s+(?:through|into|over|by|the|an?|to|on|from|along|around|between|down|up|off|out|"
    r"your|his|her|their|my|our|its|that|these|those|it|this (?:stage|test|exam|hurdle|point|milestone|inspection))\b)|"
    r"\b(?:he|she|they)\s+(?:may|might|could|will|would|can|shall)\s+(?:also\s+)?pass(?:es)?\s+(?:before|during|this (?:year|phase|month|period)|"
    r"next (?:year|month)|within|soon|early|young|around|after|by (?:the|year)|peacefully|quietly)\b|"
    # T11.42: a person (kin, an elder, a loved one) with "no more", a journey that ends, "slip away", "fade away", "depart"
    rf"(?:{_KIN9})\w*[^.;!?]{{0,40}}?\bno more(?=\s*(?:$|[.,;!?])|\s+(?:by|after|before|next|this|in|from|soon|within|during|beyond|past|till|until|once|then|and|when)\b)|"
    rf"(?:{_KIN9})\w*(?:\s+ji)?['’]?s?\s+(?:(?:life|earthly|final|last|worldly)\s+)?journey\s+(?:\w+\s+){{0,2}}?(?:ends?|comes? to an end|is over|closes|concludes|finishes)\b|"
    rf"\bjourney of (?:an? |the |your |his |her |their )?(?:{_KIN9})\w*\s+(?:\w+\s+){{0,2}}?(?:ends?|comes? to an end|is over|closes|concludes|finishes)\b|"
    rf"(?:{_KIN9})\w*[^.;!?]{{0,40}}?\b(?:slip\w*|fad(?:e|es|ed|ing))\s+away\b(?!\s+(?:from|to|into|for|with|early|late|on|at)\b)|"
    rf"(?:{_KIN9})\w*[^.;!?]{{0,40}}?\b(?:may|might|could|will|would|shall)\s+(?:\w+ly\s+)?depart\b(?!\s+(?:for|from|to|with)\b)|"
    rf"(?:los(?:e|es|ing|t)|loss of)\s+(?:a |an |the |your |one of your )?(?:{_KIN8})\b|"
    rf"(?:{_KIN8})\w*[^.;!?]{{0,40}}?\b(?:be|is|are|get|gets|got|been)\s+(?:lost\b(?!\s+(?:in|on|for|to|at|without|among))|taken away|taken from|called away)"
)

# ---------------------------------------------------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------------------------------------------------
_INVISIBLE = re.compile("[​-‏‪-‮⁠-⁤﻿­᠎]")
_WORD = re.compile(r"\w+", re.U)
_SPACED = re.compile(r"(?<![\w])(?:[A-Za-z][\s.\-_*]+){2,}[A-Za-z](?![\w])")
_SEP = re.compile(r"[\s.\-_*]+")


def _is_latin(c):
    return c.isascii() and c.isalpha() or (c.isalpha() and unicodedata.name(c, "").startswith("LATIN"))


def norm(text):
    """NFKC; accents folded on Latin letters ("fathér" -> "father", Devanagari vowel signs kept); invisible and other
    format characters dropped (zero-width space, joiner, soft hyphen, bidi marks); runs of three or more single letters
    split by spaces, dots, dashes or underscores joined ("F A T H E R", "d.i.e"). Case is kept."""
    text = str(text)
    if not text.isascii():
        t = unicodedata.normalize("NFKC", text).replace("\u093c", "")      # the nukta is folded: ज़ reads as ज
        t = _INVISIBLE.sub("", t)
        t = "".join(c for c in t if unicodedata.category(c) != "Cf")
        out = []
        for c in unicodedata.normalize("NFKD", t):
            if unicodedata.category(c) == "Mn" and out and _is_latin(out[-1]):
                continue
            out.append(c)
        text = unicodedata.normalize("NFC", "".join(out))
    # a run of six or more single letters is not joined: words_in refuses it as letter-spaced text
    return _SPACED.sub(lambda m: m.group() if len(re.findall(r"[A-Za-z]", m.group())) >= 6 else _SEP.sub("", m.group()), text)


_LEETMAP = {"3": "e", "0": "o", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}
_LEETTOK = re.compile(r"[A-Za-z0-9@$]*[A-Za-z][A-Za-z0-9@$]*")
_LEETMARK = re.compile(r"[A-Za-z][0-9@$]|[0-9@$][A-Za-z]")
_REPEAT = re.compile(r"(.)\1{2,}")
LONG_SPACED = re.compile(r"(?<![\w])(?:[A-Za-z][\s.\-_*]+){5,}[A-Za-z](?![\w])")


def _leet(t, one):
    tr = str.maketrans({**_LEETMAP, "1": one})
    return _LEETTOK.sub(lambda m: m.group().translate(tr) if re.search(r"[0-9@$]", m.group()) else m.group(), t)


def variants(text):
    """The normalised text plus: a variant for a standalone "i" or "a" glued to a spaced word ("i d i e" -> "die"), the
    leetspeak readings (3->e, 1->i or l, 0->o, 4->a, 5->s, 7->t, @->a, $->s inside a word that has letters), and the text
    with a letter held three or more times cut to two ("deeeath"). The first item is the normalised text."""
    t = norm(text)
    v = [t]
    raw = str(text)
    if _SPACED.search(raw) or (not raw.isascii() and _SPACED.search(unicodedata.normalize("NFKC", raw))):
        v.append(_SPACED.sub(lambda m: _SEP.sub("", re.sub(r"^[AaIi][\s.\-_*]+", "", m.group())), unicodedata.normalize("NFKC", raw)))
    if _LEETMARK.search(t):
        v += [_leet(t, "i"), _leet(t, "l")]
    if _REPEAT.search(t):
        v += [_REPEAT.sub(r"\1\1", x) for x in v[:]]
    return v


def mixed_script(text):
    """True when one word mixes Latin letters with Cyrillic or Greek letters (a homoglyph spelling such as a Cyrillic o)."""
    t = unicodedata.normalize("NFKC", str(text))
    if t.isascii():
        return False
    for w in _WORD.findall(_INVISIBLE.sub("", t)):
        scripts = {unicodedata.name(c, "").split(" ")[0] for c in w if c.isalpha()}
        if "LATIN" in scripts and scripts & {"CYRILLIC", "GREEK"}:
            return True
    return False


def compile_rx(*parts):
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.I)




def _fold(p):
    """A Devanagari pattern with the nukta dropped (ज़ -> ज): norm() folds the text the same way."""
    return unicodedata.normalize("NFC", p.replace("\\u093c?", "").replace("\\u093c", "")).replace("\u093c", "")


DEVA, SELFHARM_DEVA, DEVA_KIN = _fold(DEVA), _fold(SELFHARM_DEVA), _fold(DEVA_KIN)
STRONG_RX = compile_rx(STRONG)
BOOK_RX = compile_rx(STRONG, BOOK_EXTRA)
SELFHARM_RX = compile_rx(SELFHARM)
DEVA_RX = re.compile(_DEVA_L + r"(?:" + DEVA + r")" + _DEVA_TAIL + _DEVA_R)
SELFHARM_DEVA_RX = re.compile(_DEVA_L + r"(?:" + SELFHARM_DEVA + r")" + _DEVA_TAIL + _DEVA_R)
DEVA_KIN_RX = re.compile(_DEVA_L + r"(?:" + DEVA_KIN + r")" + _DEVA_TAIL + _DEVA_R)
# "recover" and "survive" are health words about a person but ordinary words about a business or a plan
_DEVA_WELL = re.compile(r"ठीक हो (?:जा|पा|सक)\w*|ठीक हो गय\w*|स्वस्थ हो\w*")
_DEVA_SELF = re.compile(r"(?<![\wऀ-ॿ])(?:मैं|मुझे|वह|वो|उन्हें|उनकी|उनका|उसकी|उसका)(?![\wऀ-ॿ])")
_RECOVER = re.compile(r"\b(?:recover\w*|surviv\w*)\b", re.I)
_MONEY = re.compile(r"\b(?:business|money|career|job|loss(?:es)?|financ\w*|invest\w*|debt|market|compan\w*|econom\w*|savings?|"
                    r"income|slump|startup|shop|firm|project|plan|relationship|marriage|reputation|finances)\b", re.I)

# ---------------------------------------------------------------------------------------------------------------------
# Misspellings: a word of 5+ letters one edit (insert, delete, change, swap two letters) from a listed word is refused,
# unless it is a real word (data/medical-near-words.txt). A few short or common typos are listed outright.
# ---------------------------------------------------------------------------------------------------------------------
LEXICON = ("health medical medicine illness disease sickness surgery surgeon hospital cancer tumour accident injury death funeral "
           "suicide longevity lifespan mortality fatal widow fracture fever virus infection diabetes symptom diagnosis ambulance "
           "cremation obituary burial overdose miscarriage pandemic epidemic therapy chemo pacemaker transplant ventilator dialysis "
           "stroke asthma paralysis bimari mrityu swasthya aspatal durghatna ilaaj tabiyat nidhan dehant swargvas covid "
           "dying demise deceased cardiac anxiety depression unwell pneumonia leukemia tuberculosis hepatitis jaundice arthritis "
           "epilepsy seizure migraine cholera typhoid malaria dengue smallpox measles anemia homicide murder coffin graveyard hospice "
           "biopsy amputation concussion antibiotic addiction alcoholism schizophrenia bimaari wafat intiqal ailment "
           "terminal hospitalised hospitalized prescription casualty suicidal").split()
TYPOS = re.compile(r"\b(?:helth|helath|heatlh|healht|deth|deaht|daeth|dieing|desease|diseas|sucide|suicde|suiside|canser|cancor|hospitel|"
                   r"acident|accidnt|injery|ilnes|illnes|ilness|sikness|sicknes|surgary|surgury|maraka?s?|ayurday\w*)\b", re.I)
_SUFFIX = ("s", "es", "ed", "d", "ing", "ly", "er", "ers", "est", "ness", "ies")


def _near_file():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "medical-near-words.txt")
    try:
        return frozenset(open(p, encoding="utf-8").read().split())
    except OSError:
        return None


NEAR_REAL = _near_file()


def _osa(a, b, k):
    """True when the optimal-string-alignment distance of a and b (insert, delete, change, swap of neighbours) is at most k."""
    la, lb = len(a), len(b)
    if abs(la - lb) > k:
        return False
    prev2, prev = None, list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + c)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > k:
            return False
        prev2, prev = prev, cur
    return prev[lb] <= k


def _edit1(a, b):
    return a != b and _osa(a, b, 1)


def _limit(x, w):
    """Edits allowed between a listed word x and a typed word w: two for a listed word of 7+ letters, else one."""
    return 2 if len(x) >= 7 and len(w) >= 5 else 1


def _is_real(w):
    return w in NEAR_REAL or any(w.endswith(f) and w[:-len(f)] in NEAR_REAL for f in _SUFFIX)


def near_listed(w):
    """The listed word that a typed word of 5+ letters is a close misspelling of (None for a real word or no match)."""
    if NEAR_REAL is None or len(w) < 5 or w in LEXICON or _is_real(w) or re.sub(r"(?:es|s|ed|d|ing|ly)$", "", w) in LEXICON:
        return None
    for x in LEXICON:
        k = _limit(x, w)
        if abs(len(x) - len(w)) <= k and _osa(w, x, k):
            return x
    return None


def _fuzzy(t):
    """Words found a close misspelling of a listed word (empty when the near-word list is missing: the net is off)."""
    return [w for w in re.findall(r"[a-z]{5,}", t.lower()) if near_listed(w)]


def words_in(text, rx=None, fuzzy=True):
    """Every medical, death or self-harm word found in text (lower-case), by any of the checks, in any normalised
    variant: the word list, Devanagari, the typo net, letter-spaced text and the homoglyph rule. Empty list = clean."""
    rx = rx or STRONG_RX
    found = []
    if mixed_script(text):
        found.append("a word that mixes Latin with Cyrillic or Greek letters")
    if LONG_SPACED.search(unicodedata.normalize("NFKC", str(text))):
        found.append("letter-spaced text")
    for t in variants(text):
        found += [m.group().lower() for m in rx.finditer(t)]
        found += [m.group() for m in DEVA_RX.finditer(t)]
        found += [m.group().lower() for m in TYPOS.finditer(t)]
        if fuzzy:
            found += _fuzzy(t)
    return list(dict.fromkeys(found))


# Body-part tables ("Moon rules the stomach, Mars the head and bones") are the base of medical astrology: a book line that names
# two body parts, or one body part beside a planet or sign and a mapping word, is dropped. Looks (eyes, face, hair) are kept.
_ORGAN = (r"stomach|brain|bones?|spinal cord|spine|lungs?|liver|kidneys?|heart|bowels?|intestin\w*|bladder|genitals?|intimate parts|private parts|womb|uterus|legs?|"
          r"spleen|thyroid|blood|throat|chest|belly|thighs?|knees?|abdomen|pelvis|ribs?|joints?|teeth|nerves?|veins?|arteries|lymph\w*|"
          r"gall ?bladder|pancreas|rectum|anus|windpipe|marrow|tonsils?|sinus\w*|muscles?|tendons?|gums?|palate")
_ORGAN_RX = re.compile(r"\b(?:" + _ORGAN + r")\b", re.I)
_PLANET_SIGN = re.compile(r"\b(?:sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu|aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|"
                          r"sagittarius|capricorn|aquarius|pisces|mesha|vrishabha|mithuna|karka|simha|kanya|tula|vrischika|dhanus|makara|kumbha|meena|"
                          r"\d+(?:st|nd|rd|th) house|house \d+)\b", re.I)
_MAPPING = re.compile(r"\b(?:rules?|governs?|represents?|signif\w+|indicat\w+|controls?|stands? for|denotes?|afflict\w*|harm\w*|trouble\w*|"
                      r"pain|weak\w*|disease\w*)\b|[:=→-]", re.I)


_DESPACED = re.compile(r"suicid|selfharm|killmy|kill(?:him|her|them)self|endmy(?:own)?life|takemy(?:own)?life|wanttodie|enditall|"
                       r"hurtmy|cutmy|jaanle|jaandena|aatmahatya|atmahatya|khudkushi|notwanttolive|dontwanttolive")


def body_map(line):
    """True when a book line maps planets or signs to body parts, or lists two or more organs."""
    parts = {m.group().lower() for m in _ORGAN_RX.finditer(str(line))}
    return (len(parts) >= 2 or bool(parts and _PLANET_SIGN.search(line) and _MAPPING.search(line))
            or bool(re.search(r"\bbody[- ]parts?\b", str(line), re.I)))


CRISIS_NOTE = ("I am sorry this is so heavy, and I am glad you said it. I will not read the chart for this. If you or someone "
               "else may be in danger, please call your local emergency number now. Otherwise a crisis line can help right away "
               "(988 in the US, Samaritans 116 123 in the UK and Ireland, Tele-MANAS 14416 in India; numbers differ by country), "
               "or a doctor or someone you trust. When you want, I can talk with you, or help with another area of your life.")


# Typo net for the self-harm phrases: one edit on the key words ("i wnat to kil myslef"). Short words (kill, want, life, die, end) allow
# only a dropped, swapped or doubled letter, and skip real words; long ones (myself, himself, suicide, unalive) allow any one edit.
_SH_SHORT = ("kill", "want", "wanna", "gonna", "life", "die", "end")
_SH_LONG = ("myself", "himself", "herself", "themselves", "yourself", "suicide", "suicidal", "unalive")
_SH_REAL = frozenset("ill dye did den and wan wat ant lie lief lice ife lif edn enc ene unalike".split())
_SH_TOKEN = re.compile(r"[A-Za-z]{3,}")
_SH_DYE = re.compile(r"\b(wan+a|wnn?a|wana|gonna|gona|want to|wnat to|wnt to|i|i['’]?ll|i['’]?d)(\s+)dye\b"
                     r"(?!\s+(?:my |his |her |the |a |some |these |those |your )?(?:[a-z]+ )?(?:hair|beard|cloth\w*|fabric|saree|sari|shirt|dress|eyebrows?|wool|yarn|it\b|them\b))", re.I)


def _short_typo(tok, key):
    """True when tok is key with one letter dropped, two neighbours swapped or one letter doubled."""
    if len(tok) == len(key) - 1:
        return any(key[:i] + key[i + 1:] == tok for i in range(len(key)))
    if len(tok) == len(key):
        return any(key[:i] + key[i + 1] + key[i] + key[i + 2:] == tok for i in range(len(key) - 1))
    if len(tok) == len(key) + 1:
        return any(tok[i] == tok[i - 1] and tok[:i] + tok[i + 1:] == key for i in range(1, len(tok)))
    return False


def _sh_fix(t):
    """The text with each word that is one typo away from a self-harm key word put right."""
    def fix(m):
        w = m.group().lower()
        if w in _SH_REAL or w in _SH_SHORT or w in _SH_LONG:
            return m.group()
        for k in _SH_SHORT:
            if _short_typo(w, k):
                return k
        if len(w) >= 5:
            for k in _SH_LONG:
                if _edit1(w, k):
                    return k
        return m.group()
    t = _SH_TOKEN.sub(fix, t)
    # "wanna dye": dye is die only after a want word, and not in a colouring sentence
    return _SH_DYE.sub(lambda m: m.group(1) + m.group(2) + "die", t)


def selfharm_hit(text):
    """True when the text is about suicide or self-harm, anyone's: it gets the crisis referral, not a topic.
    When in doubt the crisis referral wins over a reading."""
    if LONG_SPACED.search(unicodedata.normalize("NFKC", str(text))):
        if _DESPACED.search(re.sub(r"[^a-z]", "", str(text).lower())):     # a fully letter-spaced line: read it without the gaps
            return True
    for t in variants(text):
        if SELFHARM_RX.search(t) or SELFHARM_DEVA_RX.search(t) or SELFHARM_RX.search(_sh_fix(t)):
            return True
    return False


def question_hit(text):
    """True when a question is about health, illness, injury, longevity, death or self-harm in any listed language and
    spelling, or spells a word with mixed scripts. The one check behind analyze_question, consultation intake and the
    book-search query filter."""
    if words_in(text):
        return True
    t = norm(text)
    if _DEVA_WELL.search(t) and (DEVA_KIN_RX.search(t) or _DEVA_SELF.search(t)):     # "क्या मेरी माँ ठीक हो जाएगी?": recovery of a person
        return True
    return bool(_RECOVER.search(t) and not _MONEY.search(t))


def text_hit(text, rx=None):
    """True when a line of book text carries such material (BOOK_RX), or spells a word with mixed scripts. The typo net is
    off here: it is for what a person types, and it would drop Sanskrit and Hindi terms from the books."""
    t = str(text)
    plain = t.replace("[", "").replace("]", "")      # the search tools bracket the query words: "lose his [teeth]"
    return any(bool(words_in(x, rx or BOOK_RX, fuzzy=False)) or body_map(x) for x in ((t, plain) if plain != t else (t,)))
