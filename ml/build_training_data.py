"""Build the training data for the Hassouna Green ML / deep-learning judge.

What it does
------------
1. Verifies every scientific name in ``plant_scientific_names.csv`` against a
   real taxonomic database (iNaturalist or GBIF).
2. Downloads where each taxon has actually been observed growing:
   * ``--source inat`` (default): iNaturalist observations of
     - wild plants (research grade, which excludes planted specimens) and
     - planted / cultivated plants whose identification other users agree with
       (``captive=true, identifications=most_agree``). Landscape plants in
       Egypt and the Gulf are almost all planted and irrigated, so wild records
       alone would miss them (e.g. 0 wild vs 584 cultivated Bougainvillea
       records in Egypt + the Gulf). Use ``--wild-only`` to leave them out.
     Each set is sampled in eight 90x90 degree boxes so one continent cannot
     crowd out the others.
   * ``--source gbif``: GBIF Maps API density tiles (all records except
     botanical-garden LIVING_SPECIMEN and fossils).
   Only records from 1950 onwards are used.
3. Snaps every record to the WorldClim 2.1 10-arc-minute grid (~18 km) and
   attaches seven climate variables (temperature and rainfall normals 1970-2000).
4. Writes a compact training set (``data/training_cells.npz``), a per-taxon
   summary and the climate of every app location (``data/location_climate.csv``).

Run from the project folder (needs internet; roughly 15-30 minutes):

    python ml/build_training_data.py

Downloads are cached, so an interrupted run resumes where it stopped.
Training-only dependencies: see ``ml/requirements-train.txt``.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import json
import sqlite3
import sys
import threading
import time
import zipfile
from pathlib import Path

import numpy as np
import requests
from PIL import Image

ML_DIR = Path(__file__).resolve().parent
ROOT = ML_DIR.parent
DATA_DIR = ML_DIR / "data"

WORLDCLIM_URL = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip"
MIN_YEAR = 1950
# WorldClim bioclimatic variables used as model inputs.
FEATURES = [
    ("bio1", "Annual mean temperature (°C)"),
    ("bio4", "Temperature seasonality (SD x 100)"),
    ("bio5", "Max temperature of warmest month (°C)"),
    ("bio6", "Min temperature of coldest month (°C)"),
    ("bio12", "Annual precipitation (mm)"),
    ("bio15", "Precipitation seasonality (CV)"),
    ("bio17", "Precipitation of driest quarter (mm)"),
]
GRID = 6                                   # cells per degree at 10 arc-minutes


def worldclim_file(folder: Path, name: str) -> Path:
    return folder / f"wc2.1_10m_bio_{name[3:]}.tif"      # bio12 -> wc2.1_10m_bio_12.tif
N_ROWS, N_COLS = 180 * GRID, 360 * GRID
BOXES = [(lat, lon) for lat in (-90, 0) for lon in (-180, -90, 0, 90)]   # SW corners, 90 x 90 degrees

session = requests.Session()
session.headers["User-Agent"] = "HassounaGreen-ML-judge/1.0 (student research project; plant climate niche model)"


class RateLimiter:
    """Keeps requests to one host at or below a fixed rate across threads."""

    def __init__(self, per_minute):
        self.interval, self.lock, self.next_at = 60.0 / per_minute, threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            delay = max(0.0, self.next_at - now)
            self.next_at = max(now, self.next_at) + self.interval
        if delay:
            time.sleep(delay)


def http_get(url, params=None, headers=None, tries=10, timeout=90, limiter=None):
    last = None
    for attempt in range(tries):
        if limiter:
            limiter.wait()
        try:
            r = session.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (200, 204, 206):
                return r
            last = f"HTTP {r.status_code}"
        except requests.RequestException as exc:
            last = type(exc).__name__
        time.sleep(min(60, 2 ** attempt))
    raise RuntimeError(f"GET {url} failed after {tries} tries: {last}")


# ------------------------------------------------------------------ WorldClim
def ensure_worldclim(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    if all(worldclim_file(folder, name).exists() for name, _ in FEATURES):
        return folder
    size = int(session.head(WORLDCLIM_URL, timeout=60).headers["Content-Length"])
    parts = 16                              # parallel byte ranges: the server is slow per connection
    ranges = [(i * size // parts, (i + 1) * size // parts - 1) for i in range(parts)]
    print(f"Downloading WorldClim 2.1 (10 arc-min bioclim, {size / 1e6:.0f} MB) ...")

    def fetch(rng):
        a, b = rng
        r = http_get(WORLDCLIM_URL, headers={"Range": f"bytes={a}-{b}"}, timeout=600)
        assert len(r.content) == b - a + 1
        return a, r.content

    with cf.ThreadPoolExecutor(parts) as pool:
        chunks = dict(pool.map(fetch, ranges))
    zip_path = folder / "wc2.1_10m_bio.zip"
    zip_path.write_bytes(b"".join(chunks[a] for a, _ in ranges))
    zipfile.ZipFile(zip_path).extractall(folder)
    zip_path.unlink()
    return folder


def load_climate(folder: Path) -> np.ndarray:
    Image.MAX_IMAGE_PIXELS = None
    layers = []
    for name, _ in FEATURES:
        a = np.array(Image.open(worldclim_file(folder, name)), dtype=np.float32)
        a[a < -1e30] = np.nan
        assert a.shape == (N_ROWS, N_COLS), a.shape
        layers.append(a)
    return np.stack(layers, axis=-1)          # rows x cols x features


def cell_of(lat, lon):
    row = min(N_ROWS - 1, max(0, int((90.0 - lat) * GRID)))
    col = int((lon + 180.0) * GRID) % N_COLS
    return row, col


def nearest_valid(climate, row, col, radius=2):
    """Return (row, col) of the nearest land cell, for points just off the coast."""
    if np.isfinite(climate[row, col, 0]):
        return row, col
    best = None
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            r, c = row + dr, (col + dc) % N_COLS
            if 0 <= r < N_ROWS and np.isfinite(climate[r, c, 0]):
                d = dr * dr + dc * dc
                if best is None or d < best[0]:
                    best = (d, r, c)
    return (best[1], best[2]) if best else None


# ---------------------------------------------------------------- iNaturalist
INAT_TAXA = "https://api.inaturalist.org/v1/taxa"
INAT_OBS = "https://api.inaturalist.org/v2/observations"
INAT_LIMIT = RateLimiter(per_minute=55)     # iNaturalist asks for <= 60 requests per minute


def _norm(name):
    """Lower-case and drop the hybrid sign, so 'Rosa damascena' matches 'Rosa × damascena'."""
    return " ".join(t for t in name.lower().replace("×", " ").split() if t != "x")


def inat_match(name):
    rank = "genus" if len(name.split()) == 1 else "species,hybrid,subspecies,variety"
    d = http_get(INAT_TAXA, params={"q": name, "rank": rank, "is_active": "true", "per_page": 10},
                 limiter=INAT_LIMIT).json()
    for r in d.get("results", []):
        if _norm(name) in (_norm(r.get("name", "")), _norm(r.get("matched_term", ""))):
            return {"key": int(r["id"]), "matched_name": r["name"], "rank": r["rank"],
                    "match_type": "EXACT" if _norm(r["name"]) == _norm(name) else "SYNONYM",
                    "observations": r.get("observations_count")}
    return None


INAT_KINDS = {
    "wild": ("inat_{key}.json", {"quality_grade": "research"}),
    "cultivated": ("inat_cult_{key}.json", {"captive": "true", "identifications": "most_agree"}),
}


def inat_points(key, cache_dir: Path, pages_per_box=1, kind="wild"):
    filename, filters = INAT_KINDS[kind]
    cache = cache_dir / filename.format(key=key)
    if cache.exists():
        return json.loads(cache.read_text())
    base = {"taxon_id": key, "per_page": 200, "fields": "uuid,location", "d1": f"{MIN_YEAR}-01-01", **filters}
    seen = {}

    def collect(results):
        for o in results:
            if o.get("location"):
                lat, lon = map(float, o["location"].split(","))
                seen[o["uuid"]] = [round(lat, 4), round(lon, 4), 1]

    first = http_get(INAT_OBS, params=base, limiter=INAT_LIMIT).json()
    collect(first["results"])
    if first["total_results"] > len(first["results"]):          # big taxon: sample every region
        for lat0, lon0 in BOXES:
            for page in range(1, pages_per_box + 1):
                box = dict(base, swlat=lat0, swlng=lon0, nelat=lat0 + 90, nelng=lon0 + 90, page=page)
                d = http_get(INAT_OBS, params=box, limiter=INAT_LIMIT).json()
                collect(d["results"])
                if page * 200 >= d["total_results"]:
                    break
    points = list(seen.values())
    cache.write_text(json.dumps(points))
    return points


# ----------------------------------------------------------------------- GBIF
GBIF_MATCH = "https://api.gbif.org/v1/species/match"
GBIF_TILE = "https://api.gbif.org/v2/map/occurrence/density/{z}/{x}/{y}.mvt"
GBIF_BASIS = ["HUMAN_OBSERVATION", "PRESERVED_SPECIMEN", "OCCURRENCE",
              "OBSERVATION", "MATERIAL_SAMPLE", "MACHINE_OBSERVATION"]


def gbif_match(name):
    m = http_get(GBIF_MATCH, params={"name": name, "kingdom": "Plantae"}).json()
    key = m.get("acceptedUsageKey") or m.get("usageKey")
    if m.get("matchType") in ("EXACT", "FUZZY") and m.get("rank") in (
            "SPECIES", "GENUS", "SUBSPECIES", "VARIETY", "FORM") and key:
        return {"key": int(key), "matched_name": m.get("canonicalName"), "rank": m["rank"].lower(),
                "match_type": m["matchType"], "observations": None}
    return None


def gbif_points(key, cache_dir: Path, zoom=1, extent=512):
    import mapbox_vector_tile  # training-only dependency
    cache = cache_dir / f"gbif_{key}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    deg, points = 180.0 / 2 ** zoom, []
    for x in range(2 * 2 ** zoom):
        for y in range(2 ** zoom):
            r = http_get(GBIF_TILE.format(z=zoom, x=x, y=y),
                         params={"srs": "EPSG:4326", "taxonKey": key, "basisOfRecord": GBIF_BASIS})
            if not r.content:
                continue
            for layer in mapbox_vector_tile.decode(r.content).values():
                for feat in layer["features"]:
                    geom = feat["geometry"]["coordinates"]
                    px, py = (geom[0] if isinstance(geom[0], list) else geom)[:2]
                    if not (0 <= px < extent and 0 <= py < extent):
                        continue          # tile buffer: belongs to a neighbouring tile
                    count = sum(v for k, v in feat["properties"].items() if k.isdigit() and int(k) >= MIN_YEAR)
                    if count > 0:
                        lon = -180.0 + x * deg + (px + 0.5) / extent * deg
                        lat = 90.0 - (y + 1) * deg + (py + 0.5) / extent * deg   # decoded y points up
                        points.append([round(lat, 4), round(lon, 4), int(count)])
    cache.write_text(json.dumps(points))
    return points


SOURCES = {
    "inat": {"label": "iNaturalist observations: wild (research grade) and cultivated with agreed identification "
                      "(api.inaturalist.org)",
             "match": inat_match, "points": inat_points, "workers": 3},
    "gbif": {"label": "GBIF occurrence density maps (api.gbif.org, excluding living/fossil specimens)",
             "match": gbif_match, "points": gbif_points, "workers": 6},
}


# ----------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=sorted(SOURCES), default="inat")
    ap.add_argument("--worldclim-dir", type=Path, default=DATA_DIR / "worldclim")
    ap.add_argument("--cache-dir", type=Path, default=DATA_DIR / "occurrence_cache")
    ap.add_argument("--min-cells", type=int, default=20, help="minimum occupied grid cells to model a taxon")
    ap.add_argument("--wild-only", action="store_true", help="iNaturalist: leave out cultivated records")
    args = ap.parse_args()
    src = SOURCES[args.source]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    climate = load_climate(ensure_worldclim(args.worldclim_dir))
    print(f"WorldClim loaded: {int(np.isfinite(climate[..., 0]).sum()):,} land cells")

    with open(ML_DIR / "plant_scientific_names.csv", newline="", encoding="utf-8") as fh:
        mapping = list(csv.DictReader(fh))
    names = sorted({r["scientific_name"].strip() for r in mapping if r["scientific_name"].strip()})
    print(f"Matching {len(names)} names with {args.source} ...")
    match_cache = args.cache_dir / f"matches_{args.source}.json"
    cached = json.loads(match_cache.read_text()) if match_cache.exists() else {}
    taxa = {}
    for name in names:
        m = cached[name] if name in cached else src["match"](name)
        taxa[name] = m
        print(f"  {name:28s} -> " + (f"{m['matched_name']} [{m['rank']}, {m['match_type']}, id {m['key']}]"
                                     if m else "NO MATCH (not modeled)"))
    match_cache.write_text(json.dumps({n: m for n, m in taxa.items() if m}, indent=1))

    keys = sorted({m["key"] for m in taxa.values() if m})
    print(f"Downloading occurrences for {len(keys)} taxa ...")
    kinds = ["wild"] if (args.source != "inat" or args.wild_only) else ["wild", "cultivated"]
    points_by_key, records_by_kind, t0 = {k: [] for k in keys}, {kind: 0 for kind in kinds}, time.time()
    for kind in kinds:
        print(f"  {kind} records:", flush=True)
        with cf.ThreadPoolExecutor(src["workers"]) as pool:
            if args.source == "inat":
                futures = {pool.submit(inat_points, k, args.cache_dir, kind=kind): k for k in keys}
            else:
                futures = {pool.submit(src["points"], k, args.cache_dir): k for k in keys}
            for i, fut in enumerate(cf.as_completed(futures), 1):
                pts = fut.result()
                points_by_key[futures[fut]] += pts
                records_by_kind[kind] += len(pts)
                if i % 10 == 0 or i == len(keys):
                    print(f"  {kind}: {i}/{len(keys)} taxa done ({time.time() - t0:.0f}s)", flush=True)

    # Snap to the climate grid -> occupied cells per taxon.
    cells_by_key, records_by_key, dropped = {}, {}, 0
    for key, pts in points_by_key.items():
        cells = set()
        for lat, lon, _count in pts:
            rc = nearest_valid(climate, *cell_of(lat, lon))
            if rc is None:
                dropped += 1
                continue
            cells.add(rc[0] * N_COLS + rc[1])
        cells_by_key[key] = cells
        records_by_key[key] = int(sum(p[2] for p in pts))
    modeled = [k for k in keys if len(cells_by_key[k]) >= args.min_cells]
    all_cells = np.array(sorted(set().union(*(cells_by_key[k] for k in modeled))), dtype=np.int64)
    index = {c: i for i, c in enumerate(all_cells)}
    Y = np.zeros((len(all_cells), len(modeled)), dtype=bool)
    for j, key in enumerate(modeled):
        Y[[index[c] for c in cells_by_key[key]], j] = True
    X = climate[all_cells // N_COLS, all_cells % N_COLS, :]
    assert np.isfinite(X).all()

    name_by_key = {m["key"]: m["matched_name"] for m in taxa.values() if m}
    np.savez_compressed(
        DATA_DIR / "training_cells.npz",
        cell_ids=all_cells, X=X.astype(np.float32), Y=np.packbits(Y, axis=0), n_taxa=len(modeled),
        taxon_keys=np.array(modeled, dtype=np.int64),
        taxon_names=np.array([name_by_key[k] for k in modeled]),
        feature_names=np.array([f for f, _ in FEATURES]),
        feature_labels=np.array([lbl for _, lbl in FEATURES]),
    )

    with open(DATA_DIR / "taxa_summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["scientific_name", "source", "taxon_key", "matched_name", "rank", "match_type",
                    "records_used", "occupied_cells", "modeled"])
        for name, m in taxa.items():
            k = m["key"] if m else None
            w.writerow([name, args.source, k, m["matched_name"] if m else "", m["rank"] if m else "",
                        m["match_type"] if m else "NONE", records_by_key.get(k, 0),
                        len(cells_by_key.get(k, ())), k in modeled])

    db = sqlite3.connect(ROOT / "hassouna_green.db")
    with open(DATA_DIR / "location_climate.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["location_name_ar", "latitude", "longitude", "cell_lat", "cell_lon"] + [f for f, _ in FEATURES])
        for name, lat, lon in db.execute("SELECT name_ar, latitude, longitude FROM locations ORDER BY id"):
            r, c = nearest_valid(climate, *cell_of(lat, lon), radius=3)
            w.writerow([name, lat, lon, round(90 - (r + 0.5) / GRID, 4), round(-180 + (c + 0.5) / GRID, 4)]
                       + [round(float(v), 3) for v in climate[r, c, :]])
    db.close()

    meta = {
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": args.source,
        "source_label": src["label"] if "cultivated" in kinds else SOURCES[args.source]["label"].split(":")[0]
        + (" research-grade (wild) observations" if args.source == "inat" else ""),
        "record_kinds": kinds, "records_by_kind": records_by_kind, "min_year": MIN_YEAR,
        "worldclim": "WorldClim 2.1, 10 arc-minute bioclimatic variables (1970-2000); Fick & Hijmans 2017",
        "names_in_catalog": len(names), "names_matched": len(keys) and sum(1 for m in taxa.values() if m),
        "taxa_matched": len(keys), "taxa_modeled": len(modeled), "min_cells": args.min_cells,
        "grid_cells": int(len(all_cells)), "records_used": int(sum(records_by_key[k] for k in modeled)),
        "points_dropped_no_climate": dropped,
    }
    (DATA_DIR / "training_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    sys.exit(main())
