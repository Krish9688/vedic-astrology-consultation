"""Local REST API (FastAPI) over astro.service — for apps and assistants that do not speak MCP.
OpenAPI document at /api/v1/openapi.json, interactive docs at /api/v1/docs. Binds to 127.0.0.1 by default;
anything else needs `allow_remote = true` and `api_token` (bearer auth on every request). Birth data is not logged.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import config, service as S


class ChartRequest(BaseModel):
    birth: S.BirthInput
    options: S.Options = S.Options()


class VargaRequest(ChartRequest):
    division: int = Field(ge=1, le=60)


class CompareRequest(ChartRequest):
    vedastro_dir: Optional[str] = None
    live: bool = False


class ConsultationRequest(ChartRequest):
    question: str = Field(min_length=3, max_length=1000)


class ReportRequest(BaseModel):
    model: dict
    name: str = "report"


def _auth(authorization: Optional[str] = Header(default=None)):
    token = config.load().api_token
    if token and authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="unauthorized")


app = FastAPI(title="astrology-consultation", version=S.VERSION, docs_url="/api/v1/docs",
              openapi_url="/api/v1/openapi.json", dependencies=[Depends(_auth)],
              description="Local Vedic astrology calculation, knowledge lookup and report rendering. Reasoning is "
                          "done by the calling AI with the skill's method (see /api/v1/consultation).")


def _wrap(fn):
    try:
        return fn()
    except (ValueError, PermissionError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.get("/api/v1/health")
def health():
    return {"ok": True}


@app.get("/api/v1/version")
def version():
    return S.engine_info()


@app.post("/api/v1/chart")
def chart(r: ChartRequest):
    return _wrap(lambda: S.calculate_chart(r.birth, r.options))


@app.post("/api/v1/positions")
def positions(r: ChartRequest):
    return _wrap(lambda: S.planet_positions(r.birth))


@app.post("/api/v1/varga")
def varga(r: VargaRequest):
    return _wrap(lambda: S.divisional_chart(r.birth, r.division))


@app.post("/api/v1/dasha")
def dasha(r: ChartRequest):
    return _wrap(lambda: S.dasha(r.birth, r.options))


@app.post("/api/v1/transits")
def transits(r: ChartRequest):
    return _wrap(lambda: S.transits(r.birth, r.options))


@app.post("/api/v1/shadbala")
def shadbala(r: ChartRequest):
    return _wrap(lambda: S.shadbala(r.birth))


@app.post("/api/v1/ashtakavarga")
def ashtakavarga(r: ChartRequest):
    return _wrap(lambda: S.ashtakavarga(r.birth))


@app.post("/api/v1/jaimini")
def jaimini(r: ChartRequest):
    return _wrap(lambda: S.jaimini_factors(r.birth))


@app.post("/api/v1/sensitivity")
def sensitivity(r: ChartRequest):
    return _wrap(lambda: S.birth_time_sensitivity(r.birth, r.options))


@app.post("/api/v1/compare")
def compare(r: CompareRequest):
    return _wrap(lambda: S.compare_engines(r.birth, r.vedastro_dir, r.live))


@app.post("/api/v1/consultation")
def consultation(r: ConsultationRequest):
    return _wrap(lambda: S.consultation_context(r.question, r.birth, r.options))


@app.post("/api/v1/report")
def report(r: ReportRequest):
    return _wrap(lambda: S.create_report(r.model, r.name))


def main(host: str = "127.0.0.1", port: int = 8766):
    s = config.load()
    if host not in ("127.0.0.1", "localhost", "::1") and not (s.allow_remote and s.api_token):
        raise SystemExit("refusing to listen beyond localhost: set allow_remote = true and api_token in the config")
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)
