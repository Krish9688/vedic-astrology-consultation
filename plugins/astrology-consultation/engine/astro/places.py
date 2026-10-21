"""Birthplace → coordinates and IANA time zone, offline, from the GeoNames gazetteer (cities with 15,000+ people,
CC-BY 4.0, geonames.org). `astro setup --places` downloads it once into the private data folder; nothing is looked up
online afterwards and no place name ever leaves the machine. A name that matches several places returns all of them:
the caller chooses, the engine never guesses."""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import os
import unicodedata
import urllib.request
import zipfile

SOURCE = "GeoNames cities15000 (CC-BY 4.0, https://www.geonames.org)"
URLS = {"cities15000.txt": "https://download.geonames.org/export/dump/cities15000.zip",
        "admin1CodesASCII.txt": "https://download.geonames.org/export/dump/admin1CodesASCII.txt"}


def folder(data_dir):
    return os.path.join(data_dir, "places")


def install(data_dir):
    """Download the gazetteer (HTTPS) into <data_dir>/places and record date and checksums for reproducibility."""
    d = folder(data_dir)
    os.makedirs(d, mode=0o700, exist_ok=True)
    meta = {"source": SOURCE, "downloaded": dt.date.today().isoformat(), "sha256": {}}
    for name, url in URLS.items():
        with urllib.request.urlopen(url, timeout=120) as r:
            raw = r.read()
        data = zipfile.ZipFile(io.BytesIO(raw)).read(name) if url.endswith(".zip") else raw
        part = os.path.join(d, name + ".part")
        with open(part, "wb") as f:
            f.write(data)
        os.replace(part, os.path.join(d, name))
        meta["sha256"][name] = hashlib.sha256(data).hexdigest()
    with open(os.path.join(d, "places.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return d


def _norm(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.casefold()) if not unicodedata.combining(c)).strip()


def info(data_dir):
    p = os.path.join(folder(data_dir), "places.json")
    return json.load(open(p)) if os.path.exists(p) else None


def search(query, data_dir, country=None, limit=10):
    """Places whose name or alternate name equals the query (then: starts with it), largest population first.
    Returns {"query", "matches": [...], "ambiguous": bool, "source"}. Raises FileNotFoundError without the gazetteer."""
    d = folder(data_dir)
    path = os.path.join(d, "cities15000.txt")
    if not os.path.exists(path):
        raise FileNotFoundError("no place gazetteer installed: run `astro setup --places` once (downloads GeoNames, "
                                "CC-BY 4.0), or give coordinates and a time zone yourself")
    q, cc = _norm(query), (country or "").upper()
    if not q:
        raise ValueError("empty place name")
    admin = {}
    ap = os.path.join(d, "admin1CodesASCII.txt")
    if os.path.exists(ap):
        with open(ap, encoding="utf-8") as f:
            for line in f:
                k, name, *_ = line.rstrip("\n").split("\t")
                admin[k] = name
    found = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) < 18 or (cc and c[8] != cc):
                continue
            names = {_norm(c[1]), _norm(c[2])} | {_norm(a) for a in c[3].split(",") if a}
            rank = 0 if q in names else 1 if any(n.startswith(q) for n in names) else None
            if rank is None:
                continue
            found.append((rank, -int(c[14] or 0), {
                "name": c[1], "region": admin.get(f"{c[8]}.{c[10]}", c[10]), "country": c[8],
                "lat": float(c[4]), "lon": float(c[5]), "zone": c[17], "population": int(c[14] or 0),
                "geonameid": int(c[0])}))
    found.sort(key=lambda x: x[:2])
    best = [m for r, _, m in found if r == found[0][0]] if found else []
    matches = [m for *_, m in found][:limit]
    places = {(round(m["lat"], 1), round(m["lon"], 1)) for m in best}
    return {"query": query, "matches": matches, "ambiguous": len(places) > 1, "source": SOURCE,
            "gazetteer": info(data_dir)}
