"""P8-3c / CALC-X4: a small explicit ayanamsa set. Lahiri stays the default and byte-identical; each mode carries its
own label; modes never leak between calls or threads."""
import json
import threading

import pytest
import swisseph as swe

from astro import cli
from astro import service as S
from astro.calc import engine as E

from test_transit import B as RAW  # noqa: E402  (the synthetic chart of the transit tests)

B = S.BirthInput(**RAW)
# Swiss Ephemeris 2.10.03 at J2000 (SE regression values, not truth; CALC-X4, CALC-X6 item 3)
J2000 = {"lahiri": 23.85709, "true_chitra": 23.84002, "lahiri_icrc": 23.85679, "lahiri_1940": 23.84232,
         "kp": 23.76024, "raman": 22.41079}
LABEL = {"lahiri": "Lahiri ", "true_chitra": "True Citra ", "lahiri_icrc": "Lahiri ICRC ", "lahiri_1940": "Lahiri 1940 ",
         "kp": "Krishnamurti ", "raman": "Raman "}


def strip(c):
    c = json.loads(json.dumps(c))
    c["meta"].pop("computed_at_utc", None)
    return c


@pytest.mark.parametrize("mode", list(J2000))
def test_each_mode_has_its_j2000_value_and_label(mode):
    with E.using(mode):
        E._sid()
        assert round(swe.get_ayanamsa_ut(2451545.0), 5) == J2000[mode]
    c = S.calculate_chart(B, S.Options(on="2026-01-15", ayanamsa=mode), full=False)      # Options alone selects it
    assert c["meta"]["ayanamsa"].startswith(LABEL[mode])
    assert set(J2000) == set(E.AYANAMSAS)


def test_default_is_unchanged_and_modes_do_not_leak():
    before = strip(S.calculate_chart(B, S.Options(on="2026-01-15"), full=False))
    raman = S.calculate_chart(B, S.Options(on="2026-01-15", ayanamsa="raman"), full=False)
    after = strip(S.calculate_chart(B, S.Options(on="2026-01-15"), full=False))
    assert before == after and after["meta"]["ayanamsa"].startswith("Lahiri ")
    shift = raman["bodies"]["Su"]["lon"] - before["bodies"]["Su"]["lon"]
    assert 1.43 < shift < 1.46                # Raman's ayanamsa is ~1.45 deg smaller, so longitudes are larger


def test_one_call_uses_one_mode_for_natal_and_transit_figures():
    dt = __import__("datetime")
    o = S.outlook(B, "month", "2026-01-15", S.Options(ayanamsa="raman"))
    lah = S.outlook(B, "month", "2026-01-15")
    assert o["meta"]["ayanamsa"].startswith("Raman ")
    ing = lambda out: {(f["planet"], f["when"]) for f in out["factors"] if f["kind"] == "ingress"}
    with E.using("raman"):                     # the outlook's sign changes are the Raman sky's, not Lahiri's
        sky = E.sky(dt.datetime(2026, 1, 14, 18, 30), dt.datetime(2026, 2, 13, 18, 30), "mean", 5.5)
    assert ing(o) == {(c["planet"], c["date"]) for c in sky["sign_changes"]} and ing(o) != ing(lah)


def test_unknown_modes_are_refused():
    with pytest.raises(ValueError):
        S.Options(ayanamsa="fagan")
    with pytest.raises(ValueError):
        with E.using("user-defined"):
            pass


def test_a_second_call_waits_for_the_first_to_finish():
    # deterministic lock check (review: a timing race test passes without the lock)
    inside, release, order = threading.Event(), threading.Event(), []

    def first():
        with E.using("raman"):
            inside.set()
            release.wait(5)
            order.append("first done")

    def second():
        inside.wait(5)
        with E.using("lahiri"):
            order.append("second ran")
    t1, t2 = threading.Thread(target=first), threading.Thread(target=second)
    t1.start()
    t2.start()
    inside.wait(5)
    t2.join(0.3)
    assert t2.is_alive() and order == []            # blocked while the Raman call holds the lock
    release.set()
    t1.join(5)
    t2.join(5)
    assert order == ["first done", "second ran"]


def test_chart_key_keeps_the_default_and_separates_other_modes():
    d = S.calculate_chart(B, S.Options(on="2026-01-15"), full=False)
    r = S.calculate_chart(B, S.Options(on="2026-01-15", ayanamsa="raman"), full=False)
    i = S.calculate_chart(B, S.Options(on="2026-01-15", ayanamsa="lahiri_icrc"), full=False)
    m = d["meta"]
    old = "sha256:" + __import__("hashlib").sha256(json.dumps([m["birth_local"], m["lat"], m["lon"], m["nodes"]]).encode()).hexdigest()[:16]
    assert S._chart_key(d) == old and len({S._chart_key(x) for x in (d, r, i)}) == 3


def test_cli_flag_reaches_commands_without_options(tmp_path, capsys):
    f = tmp_path / "b.json"
    f.write_text(json.dumps(RAW))
    cli.main(["positions", str(f), "--ayanamsa", "raman"])
    assert json.loads(capsys.readouterr().out)["meta"]["ayanamsa"].startswith("Raman ")
    cli.main(["positions", str(f)])
    assert json.loads(capsys.readouterr().out)["meta"]["ayanamsa"].startswith("Lahiri ")


def test_rest_endpoints_without_options_honour_the_ayanamsa():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from astro import rest
    body = {"birth": RAW, "options": {"ayanamsa": "kp"}}
    for path in ("/api/v1/positions", "/api/v1/varga"):
        r = TestClient(rest.app).post(path, json=body | ({"division": 9} if path.endswith("varga") else {}))
        assert r.status_code == 200 and r.json()["meta"]["ayanamsa"].startswith("Krishnamurti "), (path, r.text[:200])
