"""Write the ML judge's reference data into hassouna_green.db (schema v3).

Fills two tables from the files produced by build_training_data.py:

* plant_taxa       <- ml/plant_scientific_names.csv + ml/data/taxa_summary.csv
* location_climate <- ml/data/location_climate.csv

Upgrades a schema-v2 database in place. Safe to rerun after retraining.

    python ml/update_database.py
"""
from __future__ import annotations

import csv
import datetime as dt
import sqlite3
import sys
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
ROOT = ML_DIR.parent
sys.path.insert(0, str(ROOT))
import hassouna_db  # noqa: E402

DATA = ML_DIR / "data"


def main():
    db_path = hassouna_db.database_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    version = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    if version is None or version[0] not in ("2", "3"):
        raise SystemExit(f"Expected a schema v2 or v3 database, found {version}")

    mapping = list(csv.DictReader(open(ML_DIR / "plant_scientific_names.csv", encoding="utf-8")))
    summary = {r["scientific_name"]: r for r in csv.DictReader(open(DATA / "taxa_summary.csv", encoding="utf-8"))}
    climate = list(csv.DictReader(open(DATA / "location_climate.csv", encoding="utf-8")))
    source = next(iter(summary.values()))["source"]
    plant_ids = {row[0] for row in conn.execute("SELECT id FROM plants")}
    location_ids = {name: lid for lid, name in conn.execute("SELECT id, name_ar FROM locations")}

    with conn:
        conn.executescript(hassouna_db.SCHEMA_SQL)          # adds the v3 tables; existing tables untouched
        conn.execute("DELETE FROM plant_taxa")
        conn.execute("DELETE FROM location_climate")
        n_taxa = 0
        for r in mapping:
            pid, name = int(r["plant_id"]), r["scientific_name"].strip()
            if pid not in plant_ids:
                raise SystemExit(f"plant_id {pid} in plant_scientific_names.csv is not in the plants table")
            if not name:
                continue                                   # generic / unidentified catalog entry
            s = summary.get(name, {})
            key = int(s["taxon_key"]) if s.get("taxon_key") else None
            conn.execute(
                "INSERT INTO plant_taxa(plant_id, scientific_name, taxon_source, taxon_key, taxon_rank, note) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (pid, name, source, key, s.get("rank", ""), r.get("note", "")))
            n_taxa += 1
        for r in climate:
            lid = location_ids.get(r["location_name_ar"])
            if lid is None:
                raise SystemExit(f"Location {r['location_name_ar']} not found in the database")
            conn.execute(
                "INSERT INTO location_climate(location_id, bio1, bio4, bio5, bio6, bio12, bio15, bio17, "
                "cell_lat, cell_lon, source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (lid, *(float(r[f]) for f in hassouna_db.CLIMATE_FEATURES), float(r["cell_lat"]),
                 float(r["cell_lon"]), "WorldClim 2.1 bioclim, 10 arc-min, 1970-2000"))
        missing = set(location_ids.values()) - {row[0] for row in conn.execute("SELECT location_id FROM location_climate")}
        if missing:
            raise SystemExit(f"{len(missing)} locations have no climate row")
        conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
                     (str(hassouna_db.SCHEMA_VERSION),))
        conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('ml_data_updated_at_utc', ?)",
                     (dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),))
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.execute("VACUUM")
    conn.close()
    hassouna_db.load_reference_data(db_path)                # full validation through the app's loader
    print(f"{db_path.name}: schema v{hassouna_db.SCHEMA_VERSION}, {n_taxa} plant_taxa rows, "
          f"{len(climate)} location_climate rows")


if __name__ == "__main__":
    main()
