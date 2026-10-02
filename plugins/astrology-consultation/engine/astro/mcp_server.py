"""Local MCP server: the astrology service for any MCP client (Claude Code / Desktop, ChatGPT desktop & Codex, Cursor,
Open WebUI, custom agents). Every tool is a thin wrapper over astro.service.

Transports: stdio (default; the client launches `astro mcp`) or Streamable HTTP on 127.0.0.1 (`astro mcp --http`).
Listening on any other address needs `allow_remote = true` *and* `api_token` in the config; requests must then carry
`Authorization: Bearer <token>`. Birth data is never logged.
"""
from __future__ import annotations

import datetime as dt
import functools
from typing import Optional

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import config, service as S

INSTRUCTIONS = (
    "Vedic astrology service; all calculation is local and returns facts only. For a consultation call "
    "prepare_consultation, read the skill:// files it lists, then answer life-first: meaning in the person's life, "
    "likely form, timing, counter-factor, what to watch. Never invent positions or dates; treat 'high'/'very high' "
    "birth-time sensitivity as uncertain. compare_engines live=true sends birth data to VedAstro and is refused "
    "unless the user chose hybrid mode.")


mcp = MCPServer(name="astrology-consultation", version=S.VERSION, instructions=INSTRUCTIONS)


def tool(description):
    """mcp.tool, with the service's deliberate refusals (bad input, privacy mode, paths) passed to the client;
    any other exception stays a generic error so internals and birth data never leak."""
    def deco(fn):
        @functools.wraps(fn)
        def run(*a, **kw):
            try:
                return fn(*a, **kw)
            except (ValueError, PermissionError, FileNotFoundError) as e:
                raise ToolError(str(e)) from None
        return mcp.tool(description=description)(run)
    return deco


def _b(date, time, tz, lat, lon):
    return S.BirthInput(date=date, time=time, tz=tz, lat=lat, lon=lon)


def _o(on=None, months=24, year="sidereal"):
    return S.Options(on=on, months=months, year=year)


# --- calculation --------------------------------------------------------------------------------------------
@tool("Engine, ephemeris, conventions and privacy mode of this service.")
def get_engine_info() -> dict:
    return S.engine_info()


@tool("Full chart: positions, 16 vargas, Vimshottari to pratyantar, transits on `on`, sign changes, "
                      "slow-planet contacts, Shadbala, Ashtakavarga, Jaimini factors, birth-time sensitivity. "
                      "tz = UTC offset in hours at birth (include daylight saving).")
def calculate_birth_chart(date: dt.date, time: str, tz: float, lat: float, lon: float,
                          on: Optional[dt.date] = None, months: int = 24) -> dict:
    return S.calculate_chart(_b(date, time, tz, lat, lon), _o(on, months))


@tool("Sidereal (Lahiri) positions with sign, degree, nakshatra, pada and retrograde flag.")
def get_planet_positions(date: dt.date, time: str, tz: float, lat: float, lon: float) -> dict:
    return S.planet_positions(_b(date, time, tz, lat, lon))


@tool("One divisional chart (D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, "
                      "D60) with the rule used.")
def get_divisional_chart(date: dt.date, time: str, tz: float, lat: float, lon: float, division: int) -> dict:
    return S.divisional_chart(_b(date, time, tz, lat, lon), division)


@tool("Vimshottari periods (3 levels) and the periods running on `on`. year: sidereal (default), "
                      "365.25 or 360 (VedAstro's convention).")
def get_dasha(date: dt.date, time: str, tz: float, lat: float, lon: float, on: Optional[dt.date] = None,
              year: str = "sidereal") -> dict:
    return S.dasha(_b(date, time, tz, lat, lon), _o(on, year=year))


@tool("Transits on `on` (houses from lagna and Moon), slow-planet sign changes and exact "
                      "conjunctions of Jupiter/Saturn/Rahu/Ketu with natal points over `months`.")
def get_transits(date: dt.date, time: str, tz: float, lat: float, lon: float, on: Optional[dt.date] = None,
                 months: int = 24) -> dict:
    return S.transits(_b(date, time, tz, lat, lon), _o(on, months))


@tool("Local Shadbala (BPHS/Raman) with all components and the conventions used.")
def get_shadbala(date: dt.date, time: str, tz: float, lat: float, lon: float) -> dict:
    return S.shadbala(_b(date, time, tz, lat, lon))


@tool("Local Ashtakavarga: bhinnashtakavarga per planet and sarvashtakavarga, by sign and house.")
def get_ashtakavarga(date: dt.date, time: str, tz: float, lat: float, lon: float) -> dict:
    return S.ashtakavarga(_b(date, time, tz, lat, lon))


@tool("Jaimini factors: chara karakas (7 and 8 schemes), arudha padas, upapada, karakamsa, "
                      "rasi drishti.")
def get_jaimini_factors(date: dt.date, time: str, tz: float, lat: float, lon: float) -> dict:
    return S.jaimini_factors(_b(date, time, tz, lat, lon))


@tool("How far the birth time can move (±0.5 to ±15 min) before each factor changes, with "
                      "classes robust / moderate / high / very high.")
def get_birth_time_sensitivity(date: dt.date, time: str, tz: float, lat: float, lon: float,
                               on: Optional[dt.date] = None) -> dict:
    return S.birth_time_sensitivity(_b(date, time, tz, lat, lon), _o(on))


@tool("Compare the local engine with VedAstro. Without `live` it uses no network (a previously "
                      "fetched folder inside the data directory). live=true sends date, time, offset and "
                      "coordinates to api.vedastro.org and is refused unless privacy mode is hybrid.")
def compare_engines(date: dt.date, time: str, tz: float, lat: float, lon: float,
                    vedastro_dir: Optional[str] = None, live: bool = False) -> dict:
    return S.compare_engines(_b(date, time, tz, lat, lon), vedastro_dir=vedastro_dir, live=live)


# --- knowledge --------------------------------------------------------------------------------------------------
@tool("Page-cited full-text search of the user's own local astrology library (if configured).")
def search_astrology_sources(query: str, sources: Optional[str] = None) -> str:
    return S.search_sources(query, sources)


@tool("Which books in the local knowledge graph support or dispute a rule (book, page, tier, school).")
def get_rule_sources(rule: str) -> str:
    return S.rule_sources(rule)


# --- reasoning support (the client reasons) ---------------------------------------------------------------------
@tool("Classify a question and list the skill files to read for it (no chart needed).")
def analyze_question(question: str) -> dict:
    return S.analyze_question(question)


@tool("Prepare a consultation: routed skill files, calculated facts with provenance and "
                      "sensitivity classes. Read the listed skill:// files, then answer.")
def prepare_consultation(question: str, date: dt.date, time: str, tz: float, lat: float, lon: float,
                         on: Optional[dt.date] = None) -> dict:
    return S.consultation_context(question, _b(date, time, tz, lat, lon), _o(on))


@tool("Validate and render a Structured Report Model (skill://assets/report/report.schema.json) "
                      "to HTML and, when WeasyPrint is installed, PDF in the reports folder.")
def create_report(model: dict, name: str = "report") -> dict:
    return S.create_report(model, name)


@mcp.resource("skill://{path}", description="A document of the astrology-consultation skill (SKILL.md, "
                                             "references/*.md, assets/report/*). Read-only.")
def skill_document(path: str) -> str:
    return S.skill_file(path)


@mcp.prompt(description="Start a consultation with the skill's method.")
def astrology_consultation(question: str) -> str:
    return (f"Answer this astrology question as a careful senior consultant: {question}\n\n"
            "1. Call prepare_consultation with the birth details. 2. Read skill://SKILL.md and the files it lists. "
            "3. Answer life-first; grade evidence; name the main counter-factor and one sign to watch; say which "
            "parts depend on an exact birth time.")


def main(http: bool = False, host: str = "127.0.0.1", port: int = 8765):
    if not http:
        mcp.run("stdio")
        return
    s = config.load()
    if host not in ("127.0.0.1", "localhost", "::1") and not (s.allow_remote and s.api_token):
        raise SystemExit("refusing to listen beyond localhost: set allow_remote = true and api_token in the config")
    import uvicorn
    app = mcp.streamable_http_app(host=host)
    if s.api_token:
        app.add_middleware(_BearerAuth, token=s.api_token)
    uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)


class _BearerAuth:
    def __init__(self, app, token):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            auth = dict(scope.get("headers") or []).get(b"authorization", b"").decode()
            if auth != f"Bearer {self.token}":
                await send({"type": "http.response.start", "status": 401, "headers": [(b"content-type", b"text/plain")]})
                await send({"type": "http.response.body", "body": b"unauthorized"})
                return
        await self.app(scope, receive, send)


if __name__ == "__main__":
    main()
