# Chara dasha, BPHS (Santhanam) baseline: page-checked goldens (owner, 2026-10-24; VED-F30, D-3).
# Every chart below is a published example chart (signs only, no birth data).
import pytest

from astro.calc import chara as C


def chart(s):
    """'La=Aq Me=Aq ...' -> {body: sign}."""
    return dict(kv.split("=") for kv in s.split())


def table(s):
    t = s.split()
    return dict(zip(t[::2], map(int, t[1::2])))


BPHS_EX = chart("La=Aq Me=Aq Ju=Aq Ve=Aq Ma=Ta Ra=Ge Mo=Ge Su=Cp Ke=Le Sa=Sc")       # BPHS PDF p546 (pr 555)


def test_bphs_example_follows_the_rule():
    """BPHS PDF p547 (pr 556) table: Aq 8 Pi 1 Ar 1 Ta 9 Ge 8 Cn 1 Le 7 Vi 7 Li 4 Sc 6 Sg 2 Cp 5.
    Cp 5 is a misprint for 2 (Yogardha p551 prints 4 1/2 = (2 + 7) / 2; Kendradi p553 prints 2). Sc: Mars (Ta) and Ketu
    (Le) tie on planets and sign type, so the larger count decides: 9 (Ketu). The translator's tables use 6 (Mars);
    owner decision 2026-10-24: follow the rule and record the print."""
    assert C.sign_years(BPHS_EX) == table("Aq 8 Pi 1 Ar 1 Ta 9 Ge 8 Cn 1 Le 7 Vi 7 Li 4 Sc 9 Sg 2 Cp 2")


def test_bphs_example_sequence_starts_at_the_lagna_and_runs_forward():
    """sl. 167: Libra, the 9th from the Aquarius lagna, is in an odd pada, so the dashas run forward from the lagna."""
    seq = C.dasha(BPHS_EX)
    assert [s for s, _ in seq] == ["Aq", "Pi", "Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp"]
    assert seq[0] == ("Aq", 8) and seq[1] == ("Pi", 1)


@pytest.mark.parametrize("name,positions,printed", [
    ("JSR p285 Sri Rama", "La=Cn Mo=Cn Ju=Cn Su=Ar Ve=Pi Me=Ta Ke=Ge Ma=Cp Ra=Sg Sa=Li",
     "Ar 10 Ta 11 Ge 11 Cn 12 Le 5 Vi 4 Li 6 Sc 3 Sg 8 Cp 4 Aq 5 Pi 9"),
    # JSR p286 Einstein: positions from the chart drawing (the longitude list misprints Jupiter and Venus in Taurus)
    ("JSR p286 Einstein", "La=Ge Me=Pi Ve=Pi Su=Pi Sa=Pi Ju=Aq Ra=Cp Ma=Cp Ke=Cn Mo=Sc",
     "Ar 10 Ta 11 Ge 8 Cn 7 Le 5 Vi 5 Li 6 Sc 3 Sg 2 Cp 10 Aq 11 Pi 1"),
    # PVR p247-249 Example 66 (Narayana school; its year rules agree with BPHS here); Rahu in the 2nd, PVR p241
    ("PVR Ex 66 Raman", "La=Aq Su=Cn Sa=Ta Mo=Ta Me=Le Ma=Le Ve=Le Ju=Sc Ra=Pi Ke=Vi",
     "Le 1 Cp 8 Ge 2 Sc 9 Ar 4 Vi 1 Aq 9 Cn 3 Sg 11 Ta 3 Li 10 Pi 4"),
    # CRUX p72-74 Nehru (Narayana): printed Le 10 is a misprint for 9 (Leo back to the Sun in Scorpio, 10 - 1)
    ("CRUX p74 Nehru", "La=Cn Mo=Cn Ra=Ge Sa=Le Ju=Sg Ke=Sg Su=Sc Ve=Li Me=Li Ma=Vi",
     "Cn 12 Ge 4 Ta 5 Ar 5 Pi 3 Aq 8 Cp 5 Sg 12 Sc 1 Li 12 Vi 11 Le 9"),
])
def test_printed_tables(name, positions, printed):
    assert C.sign_years(chart(positions)) == table(printed), name


def test_lord_at_home_and_zero_year_dasha():
    """A single lord in its own sign gives 12 (BPHS silent; Rath's rule, labelled); both Sc/Aq co-lords at home give 12
    (sl. 158); a debilitated lord one sign ahead gives 1 - 1 = 0, kept as a row (D2)."""
    pos = chart("La=Sg Su=Ar Mo=Ta Ma=Sc Ke=Sc Me=Ge Ju=Cp Ve=Li Sa=Aq Ra=Aq")
    y = C.sign_years(pos)
    assert y["Li"] == 12 and y["Sc"] == 12 and y["Aq"] == 12 and y["Sg"] == 0
    assert ("Sg", 0) in C.dasha(pos)


def test_service_returns_dated_rows_from_birth():
    from astro import service as S
    b = S.BirthInput(date="1990-05-17", time="06:30", tz=5.5, lat=19.07, lon=72.88)
    r = S.chara_dasha(b)
    rows = r["dasas"]
    assert len(rows) == 12 and rows[0]["start"].startswith("1990-05-17")
    assert sum(x["years"] for x in rows) == sum(C.sign_years(C.signs_of(S._compute(b, S.DEFAULTS, extras=False))).values())
    assert all(a["end"] == b2["start"] for a, b2 in zip(rows, rows[1:]))
    assert r["school"] == "bphs_santhanam" and "convention" in r["year_length"]


# Antardashas (owner decision 2026-10-24): BPHS ch. 51 sl. 7-12 is the default (it names the Chara dasha explicitly);
# ch. 50 sl. 90-96 gives only the start (the sign holding the dasha lord) and is shown as the alternative.
def test_ch51_antardasha_orders_follow_the_worked_lists():
    """BPHS PDF p614-615: fixed odd Aquarius -> every 6th sign forward (Santhanam's printed list omits Leo, a misprint);
    dual even Pisces -> its kendras, then the 5th's, then the 9th's, in reverse; movable odd Aries -> all 12 onward."""
    assert C.antardashas("Aq") == ["Aq", "Cn", "Sg", "Ta", "Li", "Pi", "Le", "Cp", "Ge", "Sc", "Ar", "Vi"]
    assert C.antardashas("Pi") == ["Pi", "Sg", "Vi", "Ge", "Sc", "Le", "Ta", "Aq", "Cn", "Ar", "Cp", "Li"]
    assert C.antardashas("Ar") == ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
    # fixed even: every 6th sign, in reverse
    assert C.antardashas("Ta") == ["Ta", "Sg", "Cn", "Aq", "Vi", "Ar", "Sc", "Ge", "Cp", "Le", "Pi", "Li"]


def test_ch50_alternative_start_is_the_lord_sign():
    """Ch. 50: start from the sign holding the dasha lord; for Sc/Aq the lord that furnished the years."""
    assert C.ch50_start("Ar", BPHS_EX) == "Ta"                  # Mars in Taurus
    assert C.ch50_start("Aq", BPHS_EX) == "Ge"                  # Rahu (with the Moon) beats Saturn
    assert C.ch50_start("Sc", BPHS_EX) == "Le"                  # rule: Ketu (larger count), as in the years


def test_service_rows_carry_equal_ch51_antardashas_and_the_ch50_start():
    from astro import service as S
    r = S.chara_dasha(S.BirthInput(date="1990-05-17", time="06:30", tz=5.5, lat=19.07, lon=72.88))
    for row in r["dasas"]:
        ad = row["antardashas"]
        assert len(ad) == (12 if row["years"] else 0) and (not ad or (ad[0]["start"], ad[-1]["end"]) == (row["start"], row["end"]))
        assert row["antardasha_ch50_start"] in S.engine.SIGNS
    assert "ch. 51" in r["antardasha_rule"] and "ch. 50" in r["antardasha_rule"]


def test_chara_is_exposed_through_mcp_rest_and_cli(tmp_path, capsys):
    import json
    from fastapi.testclient import TestClient
    from astro import cli, mcp_server, rest
    import datetime as dt
    m = mcp_server.get_chara_dasha(dt.date(1990, 5, 17), "06:30", 19.07, 72.88, tz=5.5)
    assert m["school"] == "bphs_santhanam" and len(m["dasas"]) == 12
    birth = {"date": "1990-05-17", "time": "06:30", "tz": 5.5, "lat": 19.07, "lon": 72.88}
    r = TestClient(rest.app).post("/api/v1/chara", json={"birth": birth})
    assert r.status_code == 200 and r.json()["school"] == "bphs_santhanam"
    f = tmp_path / "b.json"
    f.write_text(json.dumps(birth))
    cli.main(["chara", str(f)])
    assert '"school": "bphs_santhanam"' in capsys.readouterr().out
