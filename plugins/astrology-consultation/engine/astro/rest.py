"""Local REST API (FastAPI) over astro.service — for apps and assistants that do not speak MCP.
OpenAPI document at /api/v1/openapi.json, interactive docs at /api/v1/docs. Binds to 127.0.0.1 by default;
anything else needs `allow_remote = true` and `api_token` (bearer auth on every request). Birth data is not logged.
"""
from __future__ import annotations

import datetime as dt
import hmac
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from . import config, service as S


class ChartRequest(BaseModel):
    birth: S.BirthInput
    options: S.Options = S.Options()


class VargaRequest(ChartRequest):
    division: int = Field(ge=1, le=60)


class ConsultationRequest(ChartRequest):
    question: str = Field(min_length=3, max_length=1000)


class ReportRequest(BaseModel):
    model: dict
    name: str = "report"


def _auth(request: Request, authorization: Optional[str] = Header(default=None)):
    if request.url.path == "/api/v1/source":   # AGPL section 13: the source offer is visible without a token
        return
    token = config.load().api_token
    if token and not hmac.compare_digest((authorization or "").encode(), f"Bearer {token}".encode()):
        raise HTTPException(status_code=401, detail="unauthorized")


app = FastAPI(title="astrology-consultation", version=S.VERSION, docs_url="/api/v1/docs",
              openapi_url="/api/v1/openapi.json", dependencies=[Depends(_auth)],
              description="Local Vedic astrology calculation, knowledge lookup and report rendering. Reasoning is "
                          "done by the calling AI with the skill's method (see /api/v1/consultation).")


def _wrap(fn):
    try:
        return fn()
    except (ValueError, PermissionError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/v1/health")
def health():
    return {"ok": True}


@app.get("/api/v1/source")
def source():
    return {"version": S.VERSION, **S.source_offer()}


@app.get("/api/v1/version")
def version():
    return S.engine_info()


@app.get("/api/v1/panchang")
def panchang(date: str, lat: float, lon: float, tz: str | None = None, zone: str | None = None):
    return _wrap(lambda: S.panchang(date, lat, lon, tz, zone))


@app.get("/api/v1/place")
def place(name: str, country: str | None = None):
    return _wrap(lambda: S.find_place(name, country))


@app.post("/api/v1/chart")
def chart(r: ChartRequest):
    return _wrap(lambda: S.calculate_chart(r.birth, r.options))


@app.post("/api/v1/positions")
def positions(r: ChartRequest):
    return _wrap(lambda: S.planet_positions(r.birth))


@app.post("/api/v1/varga")
def varga(r: VargaRequest):
    return _wrap(lambda: S.divisional_chart(r.birth, r.division))


class OutlookRequest(ChartRequest):
    period: str = "month"
    start: dt.date | None = None


@app.post("/api/v1/gochara")
def gochara(r: ChartRequest):
    return _wrap(lambda: S.gochara(r.birth, r.options))


@app.post("/api/v1/outlook")
def outlook(r: OutlookRequest):
    return _wrap(lambda: S.outlook(r.birth, r.period, r.start, r.options))


class TajikaRequest(ChartRequest):
    year: int | None = None


@app.post("/api/v1/tajika")
def tajika(r: TajikaRequest):
    return _wrap(lambda: S.tajika(r.birth, r.year, r.options))


class CompatibilityRequest(BaseModel):
    girl: S.BirthInput
    boy: S.BirthInput
    options: S.Options = S.Options()


@app.post("/api/v1/compatibility")
def compatibility(r: CompatibilityRequest):
    return _wrap(lambda: S.compatibility(r.girl, r.boy, r.options))


@app.post("/api/v1/yogini")
def yogini(r: ChartRequest):
    return _wrap(lambda: S.yogini_dasha(r.birth, r.options))


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
    import sys
    import uvicorn
    if host not in ("127.0.0.1", "localhost", "::1"):
        S.REMOTE = True
        print(S.SOURCE_NOTICE + " Source: " + S.source_offer()["source"], file=sys.stderr)
    served = app
    if host in ("127.0.0.1", "localhost", "::1"):   # DNS-rebinding guard: a web page cannot reach us under its own name
        from starlette.middleware.trustedhost import TrustedHostMiddleware
        served = TrustedHostMiddleware(app, allowed_hosts=["127.0.0.1", "localhost", "::1", "[::1]", "host.docker.internal"])
    uvicorn.run(served, host=host, port=port, log_level="warning", access_log=False)
