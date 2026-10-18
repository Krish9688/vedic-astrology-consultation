# The portable interfaces (service, REST, MCP, CLI) and their privacy/security guards — synthetic chart S1 only
import asyncio
import json
import os
import socket
import subprocess
import sys
import time

import pytest

from astro import cli, config, predictions, service as S

S1 = dict(date="1992-03-14", time="09:40", tz=0, lat=51.5, lon=-0.12)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Every test gets its own config file and data folder; the user's real settings are never read."""
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.toml"))
    monkeypatch.setattr(S, "REMOTE", False)                     # a server test may have flipped it
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


def test_unpadded_time_is_normalised():
    """P1-5 (council 6): "9:40" used to pass validation and then crash the engine (fromisoformat needs HH)."""
    b = S.BirthInput(**(S1 | dict(time="9:40")))
    assert b.time == "09:40:00"
    assert S.planet_positions(b)["bodies"]["Asc"] == S.planet_positions(S.BirthInput(**S1))["bodies"]["Asc"]


def test_time_source_and_label_reach_the_output():
    """P1-5: time_source (how reliable the birth time is) and the opaque label used to be silently dropped."""
    c = S.calculate_chart(S.BirthInput(**S1, time_source="hospital record", label="S1"), full=False)
    assert c["meta"]["time_source"] == "hospital record" and c["meta"]["label"] == "S1"
    assert "time_source" not in S.calculate_chart(S.BirthInput(**S1), full=False)["meta"]


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


def test_report_name_sanitized():
    with pytest.raises(ValueError):
        S.create_report({}, "../../evil")


def test_report_folder_is_owner_only(isolated_config):
    model = json.load(open(f"{config.load().skill_dir}/assets/report/example-synthetic.json"))
    res = S.create_report(model, "synthetic")
    assert res["ok"] and (isolated_config / "reports").stat().st_mode & 0o777 == 0o700
    assert os.stat(res["html"]).st_mode & 0o777 == 0o600                 # the report file itself is owner-only


def test_report_file_owner_only_when_pdf_step_fails(isolated_config, monkeypatch):
    # council 5 R4 S1: a failing PDF step must not leave a world-readable HTML report behind
    import types
    boom = types.ModuleType("weasyprint")
    boom.HTML = lambda **kw: (_ for _ in ()).throw(RuntimeError("pdf failed"))
    monkeypatch.setitem(sys.modules, "weasyprint", boom)
    model = json.load(open(f"{config.load().skill_dir}/assets/report/example-synthetic.json"))
    old = os.umask(0o022)                # the regression only shows under a permissive umask
    try:
        res = S.create_report(model, "failing")
    finally:
        os.umask(old)
    assert not res["ok"] and "pdf failed" in res["errors"][0]          # the reason reaches the client (3.6.2)
    assert os.stat(isolated_config / "reports" / "failing.html").st_mode & 0o777 == 0o600


def test_report_safety_covers_unit_basis_and_titles(isolated_config):
    # council 5 R7-1: every printed string is checked, including the "Chart basis" column and section titles
    model = json.load(open(f"{config.load().skill_dir}/assets/report/example-synthetic.json"))
    unit = next(u for sec in model["sections"] for u in sec.get("units", []) if "basis" in u)
    unit["basis"] = "The native will die young."
    res = S.create_report(model, "unsafe-basis")
    assert not res["ok"] and any("SAFETY" in e for e in res["errors"])

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
    assert c.post("/api/v1/compare", json={"birth": S1}).status_code == 404   # engine comparison removed


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
            doc = await s.read_resource("skill://references/timing.md")          # nested files must be readable (E-1)
            assert len(doc.contents[0].text) > 1000
            for bad in ("skill://../../etc/passwd", "skill://references/../../astro/service.py"):
                with pytest.raises(Exception, match="(?i)unknown resource|outside|not allowed|invalid|only skill"):
                    await s.read_resource(bad)
    asyncio.run(run())


def _example_model():
    return json.load(open(f"{config.load().skill_dir}/assets/report/example-synthetic.json"))


def test_mcp_create_report_tool(isolated_config):
    """The real MCP tool (not only the service function) writes the report into an owner-only folder."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        p = StdioServerParameters(command=sys.executable, args=["-m", "astro.cli", "mcp"], cwd=config.PROJECT,
                                  env={"ASTRO_CONFIG": str(isolated_config / "config.toml"), "PATH": ""})
        async with stdio_client(p) as (r, w), ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("create_report", {"model": _example_model(), "name": "mcp-synthetic"})
            out = json.loads(res.content[0].text)
            assert not res.is_error and out["ok"] and os.path.exists(out["html"])
            bad = await s.call_tool("create_report", {"model": _example_model(), "name": "../escape"})
            assert bad.is_error
    asyncio.run(run())
    assert (isolated_config / "reports").stat().st_mode & 0o777 == 0o700


# --- HTTP MCP: a real server process on a free localhost port ---------------------------------------------------------
def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_http_mcp_bearer_token(isolated_config):
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
    set_config(isolated_config, api_token="t0ken")
    port = _free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    proc = subprocess.Popen([sys.executable, "-m", "astro.cli", "mcp", "--http", "--port", str(port)],
                            cwd=config.PROJECT, env=dict(os.environ, ASTRO_CONFIG=str(isolated_config / "config.toml")),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        assert httpx.post(url, json={}).status_code == 401
        assert httpx.post(url, json={}, headers={"Authorization": "Bearer wrong"}).status_code == 401

        async def run():
            client = create_mcp_http_client(headers={"Authorization": "Bearer t0ken"})
            async with streamable_http_client(url, http_client=client) as streams, \
                    ClientSession(streams[0], streams[1]) as s:
                await s.initialize()
                res = await s.call_tool("get_divisional_chart", S1 | {"division": 9})
                assert json.loads(res.content[0].text)["signs"]["Asc"] == "Leo"
        asyncio.run(run())
    finally:
        proc.terminate()
        proc.wait(10)


@pytest.mark.parametrize("mod", ["astro.rest", "astro.mcp_server"])
def test_listen_host_rules(mod, tmp_path, monkeypatch):
    """Default is localhost; another address only with allow_remote AND a token; no access log either way."""
    import importlib
    import uvicorn
    m = importlib.import_module(mod)
    kw = {"http": True} if mod.endswith("mcp_server") else {}
    seen = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **k: seen.append(k))
    m.main(**kw)
    set_config(tmp_path, allow_remote=True, api_token="t0ken")
    m.main(host="0.0.0.0", **kw)
    assert [s["host"] for s in seen] == ["127.0.0.1", "0.0.0.0"] and not any(s.get("access_log") for s in seen)


def test_rest_report_and_remaining_endpoints(isolated_config):
    from fastapi.testclient import TestClient
    from astro.rest import app
    c = TestClient(app)
    r = c.post("/api/v1/report", json={"model": _example_model(), "name": "rest-synthetic"})
    assert r.status_code == 200 and r.json()["ok"] and os.path.exists(r.json()["html"])
    assert (isolated_config / "reports").stat().st_mode & 0o777 == 0o700
    assert c.post("/api/v1/report", json={"model": _example_model(), "name": "../x"}).status_code == 400
    assert c.get("/api/v1/version").status_code == 200
    for ep in ("positions", "dasha", "transits", "shadbala", "ashtakavarga", "jaimini", "sensitivity", "chart"):
        assert c.post(f"/api/v1/{ep}", json={"birth": S1}).status_code == 200, ep


# --- CLI ---------------------------------------------------------------------------------------------------------
def test_setup_rejects_tampered_ephemeris(tmp_path, monkeypatch):
    """A download whose SHA-256 differs from the pinned value is deleted, not used (no network: the download is faked)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli.urllib.request, "urlretrieve", lambda url, path: open(path, "wb").write(b"x"))
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


# --- council E regressions -------------------------------------------------------------------------------------------
def test_rest_rejects_foreign_host_header(monkeypatch):
    """DNS rebinding: a localhost server answers only to localhost names (E-5)."""
    from fastapi.testclient import TestClient
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    from astro import rest
    app = TrustedHostMiddleware(rest.app, allowed_hosts=["127.0.0.1", "localhost", "::1", "[::1]", "host.docker.internal"])
    c = TestClient(app, base_url="http://127.0.0.1")
    assert c.get("/api/v1/health").status_code == 200
    assert c.get("/api/v1/health", headers={"host": "evil.example"}).status_code == 400
    captured = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kw: captured.setdefault("app", app))
    rest.main()
    assert isinstance(captured["app"], TrustedHostMiddleware)


def test_config_types_are_checked(tmp_path):
    """allow_remote = "false" must not switch remote listening on (E-7)."""
    set_config(tmp_path, allow_remote="false")
    with pytest.raises(ValueError, match="allow_remote"):
        config.load()


def test_config_file_is_created_owner_only(tmp_path):
    (tmp_path / "config.toml").unlink()
    config.write(config.Settings(data_dir=str(tmp_path / "data")))
    assert (tmp_path / "config.toml").stat().st_mode & 0o777 == 0o600


def test_year_one_is_a_clean_refusal():
    with pytest.raises(ValueError, match="between the years"):
        S.BirthInput(date="0001-01-01", time="12:00", tz=0, lat=0, lon=0)


def test_prediction_errors_are_clean(tmp_path):
    with pytest.raises(ValueError, match="chart_id"):
        predictions.add(None, "career", "x", None, None, "Moderate", synthetic=True, db=str(tmp_path / "p.db"))
    with pytest.raises(ValueError, match="no prediction"):
        predictions.evaluate(99999, "x", "hit", db=str(tmp_path / "p.db"))


def test_search_query_is_never_an_option():
    """A query beginning with '--' is searched for, not parsed as a flag (E-19)."""
    if not config.load().knowledge_dir:
        pytest.skip("no local library")
    try:
        out = S.search_sources("--help")
    except ValueError as e:
        out = str(e)
    assert "usage:" not in out and "Traceback" not in out


# --- council G regressions -------------------------------------------------------------------------------------------
def test_source_offer_is_advertised_without_a_token(tmp_path):
    """AGPL-3.0 section 13 (C4): network users can see where the source is, even when a token guards everything else."""
    from fastapi.testclient import TestClient
    from astro.rest import app
    info = S.engine_info()
    assert info["license"] == "AGPL-3.0-or-later" and info["source"].startswith("https://")
    set_config(tmp_path, api_token="t0ken")
    c = TestClient(app)
    r = c.get("/api/v1/source")
    assert r.status_code == 200 and r.json()["source"].startswith("https://")
    assert c.get("/api/v1/version").status_code == 401


def test_source_url_override(tmp_path):
    set_config(tmp_path, source_url="https://example.org/fork")
    assert S.engine_info()["source"] == "https://example.org/fork"


def test_library_not_served_remotely(tmp_path, monkeypatch):
    """G-6: book excerpts are not handed to remote clients unless the owner opts in."""
    monkeypatch.setattr(S, "REMOTE", True)
    for fn in (S.search_sources, S.rule_sources):
        with pytest.raises(PermissionError, match="remote"):
            fn("navamsa")
    set_config(tmp_path, share_library_remotely=True)
    S.rule_sources("navamsa")   # allowed after opting in (may say the graph is absent)


# --- council H regressions -------------------------------------------------------------------------------------------
def test_source_url_survives_setup(tmp_path):
    """H-5: `astro setup` rewrites the config; a modified deployment's source_url must not be lost."""
    set_config(tmp_path, source_url="https://example.org/fork")
    config.write(config.load())
    assert config.load().source_url == "https://example.org/fork" and S.engine_info()["source"] == "https://example.org/fork"


@pytest.mark.parametrize("q,topic", [("When will I marry?", "relationships-marriage"),
                                     ("When will I get pregnant?", "home-family-children"),
                                     ("Should I have kids?", "home-family-children"),
                                     ("Will this illness pass?", "travel-education-health-life"),
                                     ("Should I remove my business partner?", "career-money")])
def test_question_routing(q, topic):
    """H-8: MCP-only clients depend on this routing; ordinary phrasings must reach the right method file."""
    t = S.analyze_question(q)["topics"]
    assert topic in t and not (q.endswith("partner?") and "relationships-marriage" in t)


def test_lal_kitab_kb_not_served_remotely(monkeypatch):
    """H-10: the book-derived KB follows the same remote rule as library excerpts."""
    kb = os.path.join(config.load().skill_dir, "data", "lal-kitab")
    files = [f for f in os.listdir(kb) if f.endswith(".md")] if os.path.isdir(kb) else []
    if not files:
        pytest.skip("public edition: no Lal Kitab KB")
    monkeypatch.setattr(S, "REMOTE", True)
    with pytest.raises(PermissionError, match="remote"):
        S.skill_file(f"data/lal-kitab/{files[0]}")
