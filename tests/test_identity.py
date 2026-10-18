# Report identity gate (council 6, P1-1): a report enters a person's profile only when its birth data matches.
# Invented people only; no real person's data.
import pytest

from astro import identity as I

ME = dict(name="Zed Q Testperson", date="1971-02-17", time="04:52", place="Northtown", place_aliases=["Old Northtown"],
          lagna="Capricorn", moon_sign="Leo")
REPORT = """Premium Report
Name : Zed Q Testperson
Date of Birth : 17/02/1971
Time of Birth : 04:52 AM
Place of Birth : Old Northtown, Somestate
Ascendant : Makara
Moon Sign : Simha
Report generated on 13/03/2026
"""


def fields(text=REPORT, **drop):
    f = I.extract_fields(text)
    for k in drop:
        f.pop(k, None)
    return f


def test_extracts_labelled_fields():
    f = I.extract_fields(REPORT)
    assert f["name"] == "Zed Q Testperson" and f["date"] == ["1971-02-17"] and f["time"] == "04:52"
    assert f["place"].startswith("Old Northtown") and f["lagna"] == "Capricorn" and f["moon_sign"] == "Leo"
    assert f["generated"] == ["2026-03-13"]


def test_twelve_hour_clock_and_ambiguous_dates():
    f = I.extract_fields("DOB: 05/07/1971\nTOB: 11:20 PM\n")
    assert f["time"] == "23:20" and sorted(f["date"]) == ["1971-05-07", "1971-07-05"]


def test_full_match_is_bound():
    r = I.match(ME, fields())
    assert r["verdict"] == "BOUND" and I.admit(r)


def test_conflicting_birth_date_is_rejected():
    r = I.match(ME, fields(REPORT.replace("17/02/1971", "18/02/1971")))
    assert r["verdict"] == "REJECT" and r["fields"]["date"] == "conflict" and not I.admit(r, reviewed=True)


@pytest.mark.parametrize("old,new,field", [("04:52 AM", "05:30 AM", "time"), ("Makara", "Kumbha", "lagna"),
                                           ("Simha", "Kanya", "moon_sign"), ("Old Northtown", "Southville", "place")])
def test_any_conflict_rejects(old, new, field):
    r = I.match(ME, fields(REPORT.replace(old, new)))
    assert r["verdict"] == "REJECT" and r["fields"][field] == "conflict"


def test_missing_place_is_provisional_and_needs_review():
    r = I.match(ME, fields(place=1))
    assert r["verdict"] == "PROVISIONAL" and r["fields"]["place"] == "missing"
    assert not I.admit(r) and I.admit(r, reviewed=True)


def test_matching_name_alone_proves_nothing():
    r = I.match(ME, I.extract_fields("Name: Zed Q Testperson\nYour Gemini forecast for 2026\n"))
    assert r["verdict"] == "UNBOUND" and not I.admit(r, reviewed=True)


def test_no_birth_data_is_unbound():
    assert I.match(ME, I.extract_fields("Your Leo Moon-sign forecast for 2026"))["verdict"] == "UNBOUND"


def test_different_name_with_matching_data_needs_review():
    r = I.match(ME, fields(REPORT.replace("Zed Q Testperson", "Zed Testperson-Q")))
    assert r["verdict"] == "PROVISIONAL" and r["fields"]["name"] == "conflict"


def test_ambiguous_date_alone_is_capped_and_chart_facts_settle_it():
    amb = REPORT.replace("17/02/1971", "02/05/1971")
    me = ME | dict(date="1971-05-02")
    assert I.match(me, fields(amb))["verdict"] == "BOUND"                       # time, place, lagna and Moon agree
    assert I.match(me, fields(amb, lagna=1, moon_sign=1))["verdict"] == "PROVISIONAL"


def test_result_never_carries_the_values():
    r = I.match(ME, fields(REPORT.replace("17/02/1971", "18/02/1971")))
    assert not any(s in repr(r) for s in ("1971", "Testperson", "Northtown", "04:52"))


def test_reject_cannot_be_admitted_by_review_flag():
    for v in ("REJECT", "UNBOUND"):
        assert not I.admit({"verdict": v}, reviewed=True)


def test_label_and_value_on_separate_lines():
    """Commercial PDFs often print a table: the label on one line, the value on the next, no colon."""
    f = I.extract_fields("NAME\nZed Q Testperson\nBIRTH DATE\n17/02/1971\nBIRTH TIME\n04:52\nBIRTH PLACE\nOld Northtown,\n")
    assert I.match(ME, f)["verdict"] == "BOUND" and I.match(ME, f)["fields"]["place"] == "match"
    assert f["name"] == "Zed Q Testperson"


# Independent review (council 6): confirmed identity-gate findings
def test_two_different_birth_dates_never_bind():
    r = I.match(ME, fields(REPORT + "Date of Birth : 18/02/1980\n"))
    assert r["verdict"] == "PROVISIONAL" and "more than one" in " ".join(r["reasons"])


def test_place_matches_whole_words_only():
    assert I.match(ME | dict(place="North", place_aliases=[]), fields())["fields"]["place"] == "conflict"


@pytest.mark.parametrize("bad", ["Time of Birth : 24:00 AM", "Time of Birth : 25:10"])
def test_unparsed_birth_field_caps_the_verdict(bad):
    r = I.match(ME, fields(REPORT.replace("Time of Birth : 04:52 AM", bad)))
    assert r["verdict"] == "PROVISIONAL" and r["fields"]["time"] == "unparsed"


def test_twelve_oclock_edges():
    assert I.extract_fields("TOB: 12:30 AM")["time"] == "00:30" and I.extract_fields("TOB: 12:30 PM")["time"] == "12:30"
