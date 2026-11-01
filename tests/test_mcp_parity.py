"""T3: every MCP tool that takes birth data honours ayanamsa and calendar; span_min reaches sensitivity/applicability."""
import inspect

from astro import mcp_server as M

from test_transit import B as RAW  # noqa: E402  (synthetic chart)

KW = dict(date=RAW["date"], time=RAW["time"], zone=RAW["zone"], lat=RAW["lat"], lon=RAW["lon"])


def _birth_tools():
    return {n: f for n, f in vars(M).items() if n.startswith(("get_", "create_", "prepare_")) and callable(f)
            and {"time", "lat"} <= set(inspect.signature(f).parameters)}


def test_every_birth_tool_takes_ayanamsa_and_calendar():
    tools = _birth_tools()
    assert len(tools) >= 15
    assert {n for n, f in tools.items() if not {"ayanamsa", "calendar"} <= set(inspect.signature(f).parameters)} == set()


def test_mcp_ayanamsa_changes_the_result():
    lah = M.get_planet_positions(**KW)
    raman = M.get_planet_positions(**KW, ayanamsa="raman")
    assert raman["meta"]["ayanamsa"].startswith("Raman ") and lah["meta"]["ayanamsa"].startswith("Lahiri ")
    assert raman["bodies"]["Su"]["lon"] != lah["bodies"]["Su"]["lon"]
    assert M.get_shadbala(**KW, ayanamsa="raman")["meta"]["ayanamsa"].startswith("Raman ")


def test_mcp_julian_calendar_is_converted_on_a_non_chart_tool():
    out = M.get_planet_positions(**(KW | {"date": "1752-09-03", "zone": None, "tz": "+00:00"}), calendar="julian")
    assert out["meta"]["birth_local"].startswith("1752-09-14")


def test_span_min_passes_through():
    assert M.get_dasha_applicability(**KW, span_min=60)["window_min"] == 60
    assert M.get_birth_time_sensitivity(**KW, span_min=60) != M.get_birth_time_sensitivity(**KW)
