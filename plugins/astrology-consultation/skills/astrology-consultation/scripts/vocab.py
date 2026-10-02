# Controlled vocabulary for the astrology knowledge graph.
# One entry per canonical entity: (id, type, label, latin_patterns, devanagari_patterns).
# Latin patterns are case-insensitive regex fragments wrapped in word boundaries; Devanagari
# fragments are wrapped in "not inside a Devanagari word" guards. Houses are handled separately
# (numbers + roles), see house_refs(). Edit this file to add synonyms; rebuild the graph after.
import re

PLANETS = [
    ("planet:sun", "Sun", [r"sun", r"surya", r"ravi", r"aditya"], ["सूर्य", "सूरज", "रवि"]),
    ("planet:moon", "Moon", [r"moon", r"chandra", r"soma"], ["चन्द्र", "चंद्र", "चन्द्रमा", "चंद्रमा"]),
    ("planet:mars", "Mars", [r"mars", r"kuja", r"mangala?", r"angaraka"], ["मंगल", "मङ्गल"]),
    ("planet:mercury", "Mercury", [r"mercury", r"budha"], ["बुध"]),
    ("planet:jupiter", "Jupiter", [r"jupiter", r"guru", r"brihaspati", r"brhaspati"], ["बृहस्पति", "वृहस्पति", "गुरु"]),
    ("planet:venus", "Venus", [r"venus", r"s[hu]u?kra"], ["शुक्र"]),
    ("planet:saturn", "Saturn", [r"saturn", r"s[h]?ani"], ["शनि", "शनिचर"]),
    ("planet:rahu", "Rahu", [r"rahu", r"dragon'?s head"], ["राहु"]),
    ("planet:ketu", "Ketu", [r"ketu", r"dragon'?s tail"], ["केतु"]),
]

SIGNS = [
    ("sign:aries", "Aries", [r"aries", r"mesha"]), ("sign:taurus", "Taurus", [r"taurus", r"vri?shabha"]),
    ("sign:gemini", "Gemini", [r"gemini", r"mithuna"]), ("sign:cancer", "Cancer", [r"cancer", r"kataka", r"karka"]),
    ("sign:leo", "Leo", [r"leo", r"simha"]), ("sign:virgo", "Virgo", [r"virgo", r"kanya"]),
    ("sign:libra", "Libra", [r"libra", r"thula", r"tula"]), ("sign:scorpio", "Scorpio", [r"scorpio", r"vri?schika"]),
    ("sign:sagittarius", "Sagittarius", [r"sagittarius", r"dhanus"]), ("sign:capricorn", "Capricorn", [r"capricorn", r"makara"]),
    ("sign:aquarius", "Aquarius", [r"aquarius", r"kumbha"]), ("sign:pisces", "Pisces", [r"pisces", r"meena"]),
]

NAKSHATRAS = [
    ("Ashwini", [r"as[h]?[vw]ini"]), ("Bharani", [r"bharani"]), ("Krittika", [r"kri?t?tika"]), ("Rohini", [r"rohini"]),
    ("Mrigashira", [r"mri?gas[h]?[ie]ra", r"mrigashirsha"]), ("Ardra", [r"ardra", r"aridra"]), ("Punarvasu", [r"punarvasu"]),
    ("Pushya", [r"pushyami?", r"pushya"]), ("Ashlesha", [r"as[h]?lesha"]), ("Magha", [r"magha"]),
    ("Purva Phalguni", [r"p[uo]o?rva ?phalguni", r"pubba"]), ("Uttara Phalguni", [r"uttara ?phalguni"]),
    ("Hasta", [r"hasta"]), ("Chitra", [r"chitra", r"chitta"]), ("Swati", [r"s[vw]ati"]),
    ("Vishakha", [r"vi?s[h]?akha"]), ("Anuradha", [r"anuradha"]), ("Jyeshtha", [r"jyesh?th?a"]),
    ("Mula", [r"m[uo]o?la(?![ -]?t?r?i?kona)"]), ("Purva Ashadha", [r"p[uo]o?rva ?a?s[h]?adha", r"poorvashadha"]),
    ("Uttara Ashadha", [r"uttara ?a?s[h]?adha"]), ("Shravana", [r"s[h]?ravana"]),
    ("Dhanishtha", [r"dhanish?th?a", r"sravishta"]), ("Shatabhisha", [r"s[h]?atabhis[h]?a[k]?"]),
    ("Purva Bhadrapada", [r"p[uo]o?rva ?bhadra(?:pada)?"]), ("Uttara Bhadrapada", [r"uttara ?bhadra(?:pada)?"]),
    ("Revati", [r"revati"]),
]

YOGAS = [
    ("Gajakesari yoga", [r"gaja ?kesari"]), ("Raja yoga", [r"raja ?yoga", r"rajayoga"]), ("Dhana yoga", [r"dhana ?yoga"]),
    ("Viparita raja yoga", [r"viparita"]), ("Neechabhanga", [r"neecha ?bhanga", r"nichabhanga"]),
    ("Budhaditya yoga", [r"budha ?aditya", r"budhaditya"]), ("Kemadruma yoga", [r"kemadruma"]),
    ("Sunapha yoga", [r"sunapha"]), ("Anapha yoga", [r"anapha"]), ("Durudhura yoga", [r"durudh?ura"]),
    ("Ruchaka yoga", [r"ruchaka"]), ("Bhadra yoga", [r"bhadra yoga"]), ("Hamsa yoga", [r"hamsa"]),
    ("Malavya yoga", [r"malavya"]), ("Sasa yoga", [r"sasa yoga", r"shasha yoga"]),
    ("Pancha Mahapurusha yoga", [r"pancha ?mahapurusha", r"mahapurusha"]), ("Adhi yoga", [r"adhi ?yoga"]),
    ("Amala yoga", [r"amala yoga"]), ("Parivartana yoga", [r"parivartana", r"exchange of (?:signs|houses)"]),
    ("Chandra-Mangala yoga", [r"chandra[ -]?mangala"]), ("Lakshmi yoga", [r"lakshmi yoga"]),
    ("Saraswati yoga", [r"saras[w]?ati yoga"]), ("Kalasarpa yoga", [r"kala ?sarpa"]), ("Sakata yoga", [r"s[h]?akata"]),
    ("Vasumati yoga", [r"vasumati"]), ("Vesi yoga", [r"vesi"]), ("Vasi yoga", [r"vasi yoga"]), ("Ubhayachari yoga", [r"ubhayachari", r"obhayachari"]),
    ("Harsha yoga", [r"harsha yoga"]), ("Sarala yoga", [r"sarala yoga"]), ("Vimala yoga", [r"vimala yoga"]),
    ("Guru-Chandala yoga", [r"guru ?chandala"]), ("Nabhasa yogas", [r"nabhasa"]), ("Sanyasa yoga", [r"sa[nm]yasa yoga", r"pravrajya"]),
    ("Kuja dosha", [r"kuja ?dosha", r"manglik", r"mangalik"]),
]

VARGAS = [
    ("D1", "Rasi (D1)", [r"rasi chart", r"\bD-?1\b"]), ("D2", "Hora (D2)", [r"hora chart", r"hora division", r"\bD-?2\b"]),
    ("D3", "Drekkana (D3)", [r"dre[sk]kana", r"drekana", r"\bD-?3\b"]), ("D4", "Chaturthamsa (D4)", [r"chaturthamsa", r"\bD-?4\b"]),
    ("D7", "Saptamsa (D7)", [r"saptamsa", r"\bD-?7\b"]), ("D9", "Navamsa (D9)", [r"navamsa", r"navamsha", r"\bD-?9\b"]),
    ("D10", "Dasamsa (D10)", [r"das[h]?amsa", r"\bD-?10\b"]), ("D12", "Dwadasamsa (D12)", [r"d[vw]adasamsa", r"\bD-?12\b"]),
    ("D16", "Shodasamsa (D16)", [r"s[h]?odasamsa", r"\bD-?16\b"]), ("D20", "Vimsamsa (D20)", [r"vimsamsa", r"\bD-?20\b"]),
    ("D24", "Siddhamsa (D24)", [r"siddhamsa", r"chaturvimsamsa", r"\bD-?24\b"]), ("D27", "Bhamsa (D27)", [r"bhamsa", r"saptavimsamsa", r"\bD-?27\b"]),
    ("D30", "Trimsamsa (D30)", [r"trims[h]?amsa", r"\bD-?30\b"]), ("D40", "Khavedamsa (D40)", [r"khavedamsa", r"\bD-?40\b"]),
    ("D45", "Akshavedamsa (D45)", [r"akshavedamsa", r"\bD-?45\b"]), ("D60", "Shashtiamsa (D60)", [r"shas[h]?t[iy]amsa", r"\bD-?60\b"]),
]

TECHNIQUES = [
    ("Vimshottari dasha", [r"vims[h]?ottari", r"\bdasa\b", r"\bdasha\b", r"mahadasa", r"mahadasha"], ["दशा", "महादशा"]),
    ("Antardasha (bhukti)", [r"bhukti", r"antardas[h]?a", r"apahara"], ["अंतर्दशा", "अन्तर्दशा"]),
    ("Pratyantardasha", [r"pratyantar", r"\bantara\b"], []),
    ("Chara dasha", [r"chara das[h]?a"], []),
    ("Narayana dasha", [r"narayana das[h]?a"], []),
    ("Yogini dasha", [r"yogini das[h]?a"], []),
    ("Ashtottari dasha", [r"ashtottari"], []),
    ("Kalachakra dasha", [r"kala ?chakra"], []),
    ("Sookshma dasha", [r"s[uo]o?kshma"], []),
    ("Kakshya", [r"kak[s]?hya"], []),
    ("Vimsopaka strength", [r"vims[h]?opaka"], []),
    ("Sudarshana chakra", [r"sudar[s]?hana"], []),
    ("Karakamsa", [r"karakamsa", r"karakamsha"], []),
    ("Transit (gochara)", [r"transit\w*", r"gochara"], ["गोचर"]),
    ("Ashtakavarga", [r"ashtaka ?varga", r"bindus?"], []),
    ("Shadbala", [r"shad ?bala", r"ishta ?phala", r"kashta ?phala", r"rupas"], []),
    ("Arudha", [r"arudha", r"upapada"], []),
    ("Chara karaka", [r"chara ?karaka", r"atma ?karaka", r"amatya ?karaka", r"dara ?karaka"], []),
    ("Argala", [r"argala"], []),
    ("Jaimini", [r"jaimini"], []),
    ("Tajika / Varshaphala (Parashari annual)", [r"tajik", r"varsha ?phala", r"muntha", r"saham"], []),
    ("Lal Kitab Varshaphal", [r"varshaphal\b", r"annual chart"], ["वर्षफल", "वर्ष फल"]),
    ("Sade sati", [r"sade ?sati", r"elarata", r"ashtama shani"], ["साढ़ेसाती", "साढ़े साती"]),
    ("Vedha", [r"vedha"], []),
    ("Vargottama", [r"vargottama"], []),
    ("Combustion", [r"combust\w*", r"asta(?:ngata)?\b"], []),
    ("Retrogression", [r"retrograde\w*", r"vakra"], ["वक्री"]),
    ("Dignity: exaltation", [r"exalt\w*", r"uchcha"], ["उच्च"]),
    ("Dignity: debilitation", [r"debilitat\w*", r"neecha"], ["नीच"]),
    ("Moolatrikona", [r"m[uo]o?la ?t?rikona"], []),
    ("Functional benefic/malefic", [r"functional (?:benefic|malefic)", r"yoga ?karaka", r"yogakaraka"], []),
    ("Maraka", [r"maraka"], []),
    ("Badhaka", [r"badhaka"], []),
    ("Aspect (drishti)", [r"aspect\w*", r"drishti"], ["दृष्टि"]),
    ("Conjunction", [r"conjunct\w*", r"conjoin\w*", r"association"], []),
    ("Dispositor", [r"dispositor"], []),
    ("Avastha", [r"avastha"], []),
    ("Bhava chalit / cusps", [r"chalit", r"bhava ?madhya", r"cusp"], []),
    ("Prashna (horary)", [r"pras[h]?na", r"horary", r"query"], []),
    ("Muhurta", [r"muhurta", r"electional"], []),
    ("Longevity (ayurdaya)", [r"longevity", r"ayurdaya"], []),
    ("Moon chart (Chandra lagna)", [r"chandra ?lagna", r"from the moon"], []),
    ("Karaka (significator)", [r"\bkaraka\b", r"significator"], []),
]

LAL_KITAB = [
    ("Pakka ghar", [r"pakka ?ghar", r"permanent house"], ["पक्का घर", "पक्के घर"]),
    ("Sleeping planet/house", [r"sleeping", r"so(?:ya|ta) hua"], ["सोया हुआ", "सोए हुए", "सोया"]),
    ("Rin (ancestral debt)", [r"\brin\b", r"ancestral debt", r"pitri ?rin"], ["ऋण"]),
    ("Masnui (artificial) planet", [r"masnui", r"artificial planet"], ["मसनूई"]),
    ("Dharmi planet", [r"dharmi"], ["धर्मी"]),
    ("Blind horoscope", [r"blind (?:horoscope|chart)", r"andha teva"], ["अंधा टेवा", "अन्धा टेवा"]),
    ("35-year cycle", [r"35[- ]year cycle", r"35 years? cycle"], []),
    ("Lal Kitab remedy (upay)", [r"\bupay", r"remed(?:y|ies)"], ["उपाय"]),
    ("Grah-phal / Rashi-phal", [r"grah[a]?[ -]?phal", r"rash[i]?[ -]?phal"], ["ग्रह फल", "राशि फल"]),
    ("Kalpurush (fixed Aries) chart", [r"kal ?purush", r"kalapurusha"], ["काल पुरुष"]),
]

TOPICS = [
    ("Marriage & spouse", [r"marriage", r"marital\w*", r"spouse", r"wife", r"husband", r"kalatra"], ["विवाह", "शादी", "स्त्री", "पत्नी"]),
    ("Romance & relationships", [r"romance", r"love affair", r"lover", r"relationship"], []),
    ("Children & progeny", [r"children", r"progeny", r"putra", r"issue\b", r"sons?\b", r"daughters?"], ["संतान", "सन्तान", "औलाद", "लड़का", "लड़के"]),
    ("Career & profession", [r"career", r"profession", r"occupation", r"employment", r"karma ?bhava", r"job"], ["नौकरी", "रोज़गार", "रोजगार"]),
    ("Wealth & finance", [r"wealth", r"money", r"finance", r"riches", r"dhana\b", r"income", r"gains?"], ["धन", "दौलत", "माया"]),
    ("Health & disease (symbolic)", [r"health", r"disease", r"illness", r"sickness", r"roga"], ["बीमारी", "रोग"]),
    ("Longevity & death (doctrine, never forecast)", [r"death", r"longevity", r"early demise"], ["मौत", "मृत्यु"]),
    ("Education & learning", [r"education", r"learning", r"vidya", r"studies"], ["विद्या", "पढ़ाई"]),
    ("Foreign travel & relocation", [r"foreign", r"abroad", r"travel", r"journey", r"residence", r"relocat\w*"], ["विदेश", "सफर", "सफ़र", "यात्रा"]),
    ("Property, home & vehicles", [r"property", r"house property", r"landed", r"vehicle", r"conveyance"], ["मकान", "जायदाद"]),
    ("Siblings", [r"siblings?", r"brothers?", r"sisters?"], ["भाई", "बहन"]),
    ("Mother", [r"mother"], ["माता", "माँ"]),
    ("Father", [r"father"], ["पिता", "बाप"]),
    ("Spirituality & moksha", [r"spiritual\w*", r"moksha", r"renunciation", r"liberation", r"religio\w*"], ["धर्म"]),
    ("Litigation & enemies", [r"litigation", r"enem(?:y|ies)", r"court", r"lawsuit"], ["दुश्मन", "मुकदमा"]),
    ("Fame & status", [r"fame", r"status", r"reputation", r"honou?r"], ["इज्जत", "इज़्ज़त"]),
]


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def entities():
    """Yield (id, type, label, latin, deva)."""
    for i, l, lat, dev in PLANETS:
        yield i, "Planet", l, lat, dev
    for i, l, lat in SIGNS:
        yield i, "Sign", l, lat, []
    for l, lat in NAKSHATRAS:
        yield "nakshatra:" + _slug(l), "Nakshatra", l, lat, []
    for l, lat in YOGAS:
        yield "yoga:" + _slug(l), "Yoga", l, lat, []
    for d, l, lat in VARGAS:
        yield "varga:" + d.lower(), "DivisionalChart", l, lat, []
    for l, lat, dev in TECHNIQUES:
        yield "technique:" + _slug(l), "Technique", l, lat, dev
    for l, lat, dev in LAL_KITAB:
        yield "lk:" + _slug(l), "LalKitabConcept", l, lat, dev
    for l, lat, dev in TOPICS:
        yield "topic:" + _slug(l), "Topic", l, lat, dev


_DEVA = r"ऀ-ॿ"
_COMPILED = None


def _compiled():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = []
        for eid, typ, label, lat, dev in entities():
            parts = []
            if lat:
                parts.append(r"(?<![A-Za-z])(?:" + "|".join(lat) + r")(?:'?s|es)?(?![A-Za-z])" if typ != "DivisionalChart"
                             else "(?:" + "|".join(lat) + ")")
            if dev:
                parts.append(rf"(?<![{_DEVA}])(?:" + "|".join(map(re.escape, dev)) + rf")(?![{_DEVA}])")
            _COMPILED.append((eid, typ, label, re.compile("|".join(parts), re.I)))
    return _COMPILED


ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
       "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12}
_ORDN = r"(1[0-2]|[1-9])(?:st|nd|rd|th)"
_ORDW = r"(" + "|".join(ORD) + r")"
_HOUSE_RX = [
    (re.compile(rf"\b(?:{_ORDN}|{_ORDW})\s+(lord|lords|house|bhava|from)\b", re.I), None),
    (re.compile(rf"\blord of the (?:{_ORDN}|{_ORDW})\b", re.I), "lord"),
    (re.compile(r"\b(?:house|H)\s?(1[0-2]|[1-9])\b"), "house"),
    (re.compile(rf"\b(?:in|to|into|occupies|occupying) (?:the )?(?:{_ORDN}|{_ORDW})(?![\w-])(?!\s+(?:lord|house|bhava|from))", re.I), "in"),
    (re.compile(r"\b(lagna|ascendant)(\s+lord)?\b", re.I), "lagna"),
    (re.compile(r"(?:खाना|खाने|घर)\s*(?:नंबर|नम्बर|नं\.?|न०)?\s*([0-9०-९]{1,2})"), "deva"),
]
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def house_spans(text):
    """[(house_number, role, start_offset)] for every house reference; role is 'house' or 'lord'."""
    out = []
    for rx, kind in _HOUSE_RX:
        for m in rx.finditer(text):
            if kind == "lagna":
                out.append((1, "lord" if m.group(2) else "house", m.start()))
            elif kind == "deva":
                n = int(m.group(1).translate(_DEVA_DIGITS))
                if 1 <= n <= 12:
                    out.append((n, "house", m.start()))
            elif kind == "house":
                out.append((int(m.group(1)), "house", m.start()))
            else:  # ordinal forms: "7th lord", "lord of the seventh", "in the 7th"
                n = int(m.group(1)) if m.group(1) else ORD[m.group(2).lower()]
                role = "lord" if kind == "lord" or (kind is None and m.group(3).lower().startswith("lord")) else "house"
                out.append((n, role, m.start()))
    return out


def house_refs(text):
    """{(house_number, role)} mentioned in text."""
    return {(n, r) for n, r, _ in house_spans(text)}


def entity_spans(text, eid):
    """Start offsets of every match of one vocabulary entity."""
    for i, _, _, rx in _compiled():
        if i == eid:
            return [m.start() for m in rx.finditer(text)]
    return []


def find_entities(text):
    """Return {entity_id: count} for vocabulary entities mentioned in text (houses excluded).
    A match lying inside a longer match of another entity is not counted ("chara karaka" is not "karaka")."""
    spans = []
    for eid, _, _, rx in _compiled():
        spans += [(m.start(), m.end(), eid) for m in rx.finditer(text) if m.end() > m.start()]
    found = {}
    for s0, e0, eid in spans:
        if any(s1 <= s0 and e0 <= e1 and (e1 - s1) > (e0 - s0) and other != eid for s1, e1, other in spans):
            continue
        found[eid] = found.get(eid, 0) + 1
    return found


def all_entities():
    """(id, type, label) for every canonical node, houses included."""
    out = [(eid, typ, label) for eid, typ, label, _, _ in entities()]
    out += [(f"house:{n}", "House", f"House {n}") for n in range(1, 13)]
    return out


if __name__ == "__main__":
    t = "Guru in the 7th house aspecting the lord of the tenth; Navamsa and D10 confirm. Moolatrikona, mula trikona. बृहस्पति खाना नंबर 7, शनिवार"
    f = find_entities(t)
    assert "planet:jupiter" in f and "varga:d9" in f and "varga:d10" in f, f
    assert "technique:moolatrikona" in f and "nakshatra:mula" not in f, f
    assert "planet:saturn" not in f, f  # शनिवार (Saturday) must not match Saturn
    assert house_refs(t) == {(7, "house"), (10, "lord")}, house_refs(t)
    assert set(find_entities("chara karaka scheme")) == {"technique:chara-karaka"}
    assert house_refs("lagna lord in the 6th from the Moon") == {(1, "lord"), (6, "house")}
    assert house_refs("Venus in the 7th, Mars in 8th; 10th lord") == {(7, "house"), (8, "house"), (10, "lord")}
    g = find_entities("Jupiter aspected the exalted Moon; transits; combustion; Sunday")
    assert {"technique:aspect-drishti", "technique:dignity-exaltation", "technique:transit-gochara",
            "technique:combustion"} <= set(g) and "planet:sun" not in g, g
    print("vocab ok:", len(all_entities()), "entities")
