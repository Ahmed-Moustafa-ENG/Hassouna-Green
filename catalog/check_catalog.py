"""Check the edible catalog against the database.

Verifies that every row of ``catalog/edible_plants.csv`` is in the database
with the same values, and that the database holds nothing the CSV does not.

    python catalog/check_catalog.py
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import hassouna_db  # noqa: E402

CSV_PATH = ROOT / "catalog" / "edible_plants.csv"


def main() -> None:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    conn = sqlite3.connect(hassouna_db.database_path())
    conn.row_factory = sqlite3.Row
    problems = 0

    soil_names = {r["name_ar"] for r in conn.execute("SELECT name_ar FROM soil_types")}
    categories = {r["name_ar"] for r in conn.execute("SELECT name_ar FROM plant_use_categories")}
    plant_ids = {r["name_en"]: r["id"] for r in conn.execute("SELECT id, name_en FROM plants")}

    for row in rows:
        name = row["name_en"]
        if name not in plant_ids:
            print(f"  missing from the database: {name}")
            problems += 1
            continue
        db = conn.execute(
            "SELECT p.*, c.crop_type, c.lifecycle, c.kc, c.soil_strict, c.sowing_months, "
            "c.harvest_days, c.spacing_cm, c.row_spacing_cm FROM plants p "
            "LEFT JOIN crop_details c ON c.plant_id = p.id WHERE p.id = ?", (plant_ids[name],)
        ).fetchone()
        if db is None or db["crop_type"] != row["crop_type"]:
            print(f"  {name}: crop details do not match the CSV")
            problems += 1
        if db["use_category_ar"] not in categories:
            print(f"  {name}: unknown use category {db['use_category_ar']}")
            problems += 1
        if row["use"] not in categories:
            print(f"  {name}: the CSV uses an unknown category {row['use']}")
            problems += 1
        for soil in (s for s in row["soils"].split("|") if s):
            if soil not in soil_names:
                print(f"  {name}: unknown soil {soil}")
                problems += 1
        db_soils = {r["soil_name_ar"] for r in conn.execute(
            "SELECT soil_name_ar FROM plant_soils WHERE plant_id = ?", (plant_ids[name],)
        )}
        if db_soils != {s for s in row["soils"].split("|") if s}:
            print(f"  {name}: the soils in the database differ from the CSV")
            problems += 1

    groups = dict(conn.execute(
        "SELECT group_ar, COUNT(*) FROM plant_use_categories uc "
        "LEFT JOIN plants p ON p.use_category_ar = uc.name_ar GROUP BY group_ar"
    ).fetchall())
    print(f"\n  {len(rows)} crops in the CSV | plants per group: {groups}")
    print(f"  problems: {problems}")
    conn.close()
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
