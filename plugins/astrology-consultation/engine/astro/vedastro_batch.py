#!/usr/bin/env python3
"""Batch cross-check calls to VedAstro through the existing vedastro-local MCP server (stdio JSON-RPC).

EXTERNAL: every call sends the birth date, time, UTC offset and coordinates to api.vedastro.org. Use only for
synthetic charts, or for a real chart with that person's consent. The place label sent is always "chart" — never a
name or city. The server loads its own API key; this script never reads it. Every request is logged
(<out>/calls.jsonl: tool, arguments, time, ok) so the external exposure is auditable.

usage: python3 tools/vedastro_batch.py --date DD/MM/YYYY --time HH:MM --tz +05:30 --lat L --lon L --out DIR
                                       [--check-date DD/MM/YYYY] [--years 100]
"""
import argparse
import datetime as dt
import json
import os
import subprocess

SERVER = os.path.expanduser("~/VedAstro/server.mjs")
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
BALA = ["PlanetSthanaBala", "PlanetDigBala", "PlanetKalaBala", "PlanetChestaBala", "PlanetNaisargikaBala",
        "PlanetDrikBala", "PlanetUchchaBala", "PlanetSaptavargajaBala", "PlanetOjayugmarasyamsaBala",
        "PlanetKendraBala", "PlanetDrekkanaBala", "PlanetNathonnathaBala", "PlanetPakshaBala", "PlanetTribhagaBala",
        "PlanetAbdaBala", "PlanetMasaBala", "PlanetVaraBala", "PlanetHoraBala", "PlanetAyanaBala", "PlanetYuddhaBala"]


class Client:
    def __init__(self, log_path):
        self.p = subprocess.Popen(["node", SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.n = 0
        self.log = open(log_path, "a")
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "astro-vedastro-batch", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")

    def _rpc(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        while True:
            msg = json.loads(self.p.stdout.readline())
            if msg.get("id") == self.n:
                return msg

    def call(self, tool, args):
        r = self._rpc("tools/call", {"name": tool, "arguments": args})
        text = "".join(c.get("text", "") for c in r.get("result", {}).get("content", []))
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"raw": text}
        ok = bool(isinstance(data, dict) and data.get("ok", "raw" not in data))
        self.log.write(json.dumps({"time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                   "tool": tool, "arguments": args, "ok": ok}) + "\n")
        self.log.flush()
        return data

    def close(self):
        self.p.terminate()


def main():
    ap = argparse.ArgumentParser()
    for k in ("date", "time", "tz", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--check-date")
    ap.add_argument("--years", type=int, default=100)
    ap.add_argument("--only-houses", action="store_true", help="fetch only the house data (one call)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    birth = {"use_profile": False, "birth_date": a.date, "birth_time": a.time, "timezone": a.tz,
             "latitude": a.lat, "longitude": a.lon, "location_name": "chart"}
    c = Client(os.path.join(a.out, "calls.jsonl"))
    save = lambda name, obj: json.dump(obj, open(os.path.join(a.out, name), "w"), indent=1)
    try:
        if a.only_houses:
            save("house_data.json", c.call("get_house_data", {**birth, "house": "All"}))
            return
        save("planet_data.json", c.call("get_planet_data", {**birth, "planet": "All"}))
        save("ascendant.json", c.call("get_ascendant", birth))
        d, m, y = (int(x) for x in a.date.split("/"))
        end = f"{d:02d}/{m:02d}/{y + a.years}"
        save("dasa_range.json", c.call("get_dasa_at_range", {**birth, "start_date": a.date, "end_date": end, "levels": 3}))
        save("shadbala.json", c.call("get_shadbala", birth))
        save("ashtakavarga.json", c.call("get_ashtakavarga", birth))
        save("house_data.json", c.call("get_house_data", {**birth, "house": "All"}))
        bala = {p: {m: c.call("vedastro_calculate", {**birth, "method": m, "planet": p}) for m in BALA} for p in PLANETS}
        save("shadbala_components.json", bala)
        if a.check_date:
            save("transits.json", c.call("get_transits", {**birth, "check_date": a.check_date, "planet": "All"}))
    finally:
        c.close()
    n = sum(1 for _ in open(os.path.join(a.out, "calls.jsonl")))
    print(f"wrote {a.out}: {n} logged calls to api.vedastro.org")


if __name__ == "__main__":
    main()
