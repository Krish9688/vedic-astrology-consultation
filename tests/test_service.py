# The portable interfaces (service, REST, MCP, CLI) and their privacy/security guards — synthetic chart S1 only
import asyncio
import json
import sys

import pytest

from astro import cli, config, predictions, service as S

S1 = dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Every test gets its own config file and data folder; the user's real settings are never read."""
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.toml"))
    (tmp_path / "config.toml").write_text(f'data_dir = "{tmp_path / "data"}"\nreports_dir = "{tmp_path / "reports"}"\n')
    return tmp_path


def set_config(tmp_path, **kv):
    lines = [f'data_dir = "{tmp_path / "data"}"'] + [f"{k} = {json.dumps(v)}" for k, v in kv.items()]
    (tmp_path / "config.toml").write_text("\n".join(lines) + "\n")


# --- service -----------------------------------------------------------------------------------------------------
def test_service_matches_engine():
    b = S.BirthInput(**S1)
    pos = S.planet_positions(b)
    assert pos["bodies"]["Asc"]["sign"] == "Taurus" and pos["bodies"]["Mo"]["nakshatra"] == "Punarvasu"
    assert S.divisional_chart(b, 9)["signs"]["Asc"] == "Leo"
    assert S.dasha(b, S.Options(on="2026-10-02"))["running"] == ["Me", "Ra", "Ma"]


@pytest.mark.parametrize("bad", [dict(time="25:00"), dict(time="9.40"), dict(lat=91), dict(tz=15)])
def test_birth_input_validation(bad):
    with pytest.raises(ValueError):
        S.BirthInput(**(S1 | bad))


@pytest.mark.parametrize("rel", ["../../../etc/passwd", "/etc/passwd", "scripts/kg.py", "../SKILL.md"])
def test_skill_file_cannot_escape_or_read_code(rel):
    with pytest.raises(PermissionError):
        S.skill_file(rel)


def test_skill_file_reads_documents():
    assert "astrology" in S.skill_file("SKILL.md").lower()


def test_empty_root_is_refused():
    with pytest.raises(FileNotFoundError):
        S._inside("/etc/passwd", "")


def test_compare_live_refused_in_private_mode():
    with pytest.raises(PermissionError, match="hybrid"):
        S.compare_engines(S.BirthInput(**S1), live=True)


def test_compare_dir_must_be_inside_data_dir(tmp_path):
    with pytest.raises(PermissionError):
        S.compare_engines(S.BirthInput(**S1), vedastro_dir=str(tmp_path.parent))


def test_report_name_sanitized():
    with pytest.raises(ValueError):
        S.create_report({}, "../../evil")


def test_report_folder_is_owner_only(isolated_config):
    model = json.load(open(f"{config.load().skill_dir}/assets/report/example-synthetic.json"))
    res = S.create_report(model, "synthetic")
    assert res["ok"] and (isolated_config / "reports").stat().st_mode & 0o777 == 0o700


# --- predictions ---------------------------------------------------------------------------------------------------
def test_predictions_need_consent_or_synthetic(tmp_path):
    db = str(tmp_path / "p.sqlite")
    with pytest.raises(PermissionError):
        predictions.add("person-a", "career", "a change of role", db=db)
    with pytest.raises(ValueError):
        predictions.add("1992-03-14 09:40", "career", "x", synthetic=True, db=db)
    with pytest.raises(ValueError):
        predictions.add("S1", "career", "x", "2027-1", synthetic=True, db=db)
    pid = predictions.add("S1", "career", "a change of role", "2027-01", "2027-09", synthetic=True, db=db)
    assert (tmp_path / "p.sqlite").stat().st_mode & 0o777 == 0o600       # owner-only
    predictions.evaluate(pid, "role changed 2027-04", "hit", db=db)
    with pytest.raises(PermissionError):           # the first evaluation stands
        predictions.evaluate(pid, "rewritten", "miss", db=db)
    assert predictions.scorecard(db=db) == {"career / Moderate": {"hit": 1, "miss": 0, "partial": 0,
                                                                  "not evaluable": 0}}


# --- REST ------------------------------------------------------------------------------------------------------------
def test_rest_endpoints():
    from fastapi.testclient import TestClient
    from astro.rest import app
    c = TestClient(app)
    assert c.get("/api/v1/health").json() == {"ok": True}
    spec = c.get("/api/v1/openapi.json").json()
    assert {"/api/v1/chart", "/api/v1/sensitivity", "/api/v1/consultation"} <= set(spec["paths"])
    r = c.post("/api/v1/varga", json={"birth": S1, "division": 9})
    assert r.status_code == 200 and r.json()["signs"]["Asc"] == "Leo"
    assert c.post("/api/v1/varga", json={"birth": S1 | {"time": "99:00"}, "division": 9}).status_code == 422
    assert c.post("/api/v1/compare", json={"birth": S1, "live": True}).status_code == 400


def test_rest_bearer_token(tmp_path):
    from fastapi.testclient import TestClient
    from astro.rest import app
    set_config(tmp_path, api_token="t0ken")
    c = TestClient(app)
    assert c.get("/api/v1/health").status_code == 401
    assert c.get("/api/v1/health", headers={"Authorization": "Bearer t0ken"}).status_code == 200


@pytest.mark.parametrize("mod", ["astro.rest", "astro.mcp_server"])
def test_remote_binding_refused_without_token(mod, tmp_path):
    import importlib
    m = importlib.import_module(mod)
    kw = {"http": True} if mod.endswith("mcp_server") else {}
    with pytest.raises(SystemExit, match="refusing"):
        m.main(host="0.0.0.0", **kw)
    set_config(tmp_path, allow_remote=True)              # remote allowed but no token: still refused
    with pytest.raises(SystemExit, match="refusing"):
        m.main(host="0.0.0.0", **kw)


# --- MCP (a generic stdio client, as any MCP host would launch it) ---------------------------------------------------
def test_mcp_stdio_roundtrip(isolated_config):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        p = StdioServerParameters(command=sys.executable, args=["-m", "astro.cli", "mcp"], cwd=config.PROJECT,
                                  env={"ASTRO_CONFIG": str(isolated_config / "config.toml"), "PATH": ""})
        async with stdio_client(p) as (r, w), ClientSession(r, w) as s:
            init = await s.initialize()
            assert len(init.instructions) <= 512
            names = {t.name for t in (await s.list_tools()).tools}
            assert {"calculate_birth_chart", "prepare_consultation", "get_birth_time_sensitivity"} <= names
            res = await s.call_tool("get_divisional_chart", S1 | {"division": 9})
            assert not res.is_error and json.loads(res.content[0].text)["signs"]["Asc"] == "Leo"
            res = await s.call_tool("compare_engines", S1 | {"live": True})
            assert res.is_error and "hybrid" in res.content[0].text
            with pytest.raises(Exception):
                await s.read_resource("skill://../../etc/passwd")
    asyncio.run(run())


# --- CLI ---------------------------------------------------------------------------------------------------------
def test_setup_rejects_tampered_ephemeris(tmp_path, monkeypatch):
    """A download whose SHA-256 differs from the pinned value is deleted, not used (no network: curl is faked)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli.subprocess, "run", lambda cmd, check: open(cmd[cmd.index("-o") + 1], "wb").write(b"x"))
    with pytest.raises(SystemExit, match="checksum mismatch"):
        cli.main(["setup", "--ephemeris"])
    assert not list((tmp_path / ".local/share/astrology-consultation/ephe").iterdir())
    assert (tmp_path / "data").stat().st_mode & 0o777 == 0o700          # private data folder, owner-only



def test_cli(tmp_path, capsys):
    f = tmp_path / "s1.json"
    f.write_text(json.dumps(S1))
    cli.main(["varga", str(f), "--d", "9"])
    assert json.loads(capsys.readouterr().out)["signs"]["Asc"] == "Leo"
    cli.main(["sensitivity", str(f), "--md"])
    assert "| ascendant sign |" in capsys.readouterr().out
    cli.main(["chart", str(f), "--out", str(tmp_path / "out")])
    assert (tmp_path / "out" / "calc.json").exists()
    with pytest.raises(PermissionError):
        cli.main(["predict", "add", "--chart-id", "x", "--category", "c", "--text", "t"])
    assert cli.doctor() == 0
    out = capsys.readouterr().out
    assert "PASS     calculation engine" in out and "FAIL" not in out


def test_doctor_fails_on_tampered_ephemeris(monkeypatch, capsys):
    from astro.calc import engine
    if not engine.EPHE_DIR:
        pytest.skip("no ephemeris files in this environment")
    monkeypatch.setitem(cli.EPHE_SHA256, "sepl_18.se1", "0" * 64)
    assert cli.doctor() == 1 and "checksum mismatch: sepl_18.se1" in capsys.readouterr().out


def test_env_skill_dir_wins_and_is_not_written(tmp_path, monkeypatch):
    skill = tmp_path / "plugin" / "skills" / "astrology-consultation"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# astrology skill")
    monkeypatch.setenv("ASTRO_SKILL_DIR", str(skill))
    assert config.load().skill_dir == str(skill)
    path = config.write(config.load())
    assert not any(ln.startswith("skill_dir") for ln in open(path))   # a plugin path moves on update: never pinned
