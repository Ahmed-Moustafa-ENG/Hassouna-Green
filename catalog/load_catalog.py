"""Load the edible plant catalog into hassouna_green.db.

Reads ``catalog/edible_plants.csv`` and writes:

* the two new use categories (``خضروات`` vegetables and ``فواكه`` fruits)
  with their provisional landscape Kc and their plant-filter group;
* the plants themselves, with their temperature range, water class, beauty,
  carbon rating and acceptable soils;
* a ``crop_details`` row per plant: crop type, life cycle, planting spacing,
  sowing months, days to harvest and the crop's own Kc;
* the scientific names into ``ml/plant_scientific_names.csv``, so the machine
  learning judge can be retrained over the new species.

The script is idempotent: running it twice leaves the database in the same
state. Plants whose species already exist in the catalog (the olive, the fig,
the pomegranate, the carob, the tamarind and the two date palms) are moved
into the fruit group instead of being inserted a second time.

    python catalog/load_catalog.py
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import hassouna_db  # noqa: E402

CATALOG_CSV = ROOT / "catalog" / "edible_plants.csv"
NAMES_CSV = ROOT / "ml" / "plant_scientific_names.csv"

VEGETABLE = "خضروات"
FRUIT = "فواكه"

# Provisional planning Kc of the two new groups (FAO-56 style values for a
# planted bed and for a fruit tree). Individual crops override this with their
# own coefficient in crop_details.
USE_CATEGORIES = [
    (VEGETABLE, "Vegetables", 0.65, "vegetable"),
    (FRUIT, "Fruits", 0.75, "fruit"),
]

# Species that are already in the catalog as landscape plants. They are moved
# into the fruit group instead of being added a second time.
EXISTING_FRUIT_SPECIES = {
    "Olea europaea",
    "Ficus carica",
    "Punica granatum",
    "Ceratonia siliqua",
    "Tamarindus indica",
    "Phoenix dactylifera",
}

# Plants that join the fruit group and are renamed with it.
RENAMED = {
    "Punica granatum": ("رمان", "Pomegranate"),
}


def migrate(conn: sqlite3.Connection) -> None:
    """Create the new table and add the new columns, if they are missing."""
    conn.executescript(hassouna_db.SCHEMA_SQL)
    columns = {r["name"] for r in conn.execute("PRAGMA table_info(plant_use_categories)")}
    if "group_ar" not in columns:
        conn.execute(
            "ALTER TABLE plant_use_categories ADD COLUMN group_ar TEXT NOT NULL DEFAULT 'ornamental'"
        )
    crop_columns = {r["name"] for r in conn.execute("PRAGMA table_info(crop_details)")}
    if "soil_strict" not in crop_columns:
        conn.execute(
            "ALTER TABLE crop_details ADD COLUMN soil_strict INTEGER NOT NULL DEFAULT 0"
        )
    # Every use category that is not a vegetable or a fruit group stays ornamental.
    conn.execute(
        "UPDATE plant_use_categories SET group_ar = 'ornamental' WHERE group_ar IS NULL OR group_ar = ''"
    )


def read_catalog() -> list[dict]:
    with CATALOG_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def update_names_csv(rows: list[dict], plant_ids: dict[str, int]) -> int:
    """Add the new scientific names to the ML judge's name mapping."""
    with NAMES_CSV.open(newline="", encoding="utf-8") as fh:
        existing = list(csv.DictReader(fh))
    known = {row["name_en"] for row in existing}
    added = 0
    for row in rows:
        if row["name_en"] in known:
            continue
        existing.append({
            "plant_id": str(plant_ids[row["name_en"]]),
            "name_en": row["name_en"],
            "scientific_name": row["scientific_name"],
            "note": f"edible catalog - {row['use']}",
        })
        known.add(row["name_en"])
        added += 1
    with NAMES_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["plant_id", "name_en", "scientific_name", "note"])
        writer.writeheader()
        writer.writerows(existing)
    return added


def main() -> None:
    rows = read_catalog()
    db_path = hassouna_db.database_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    with conn:
        migrate(conn)

        # ── the two new use categories ─────────────────────────────────────
        for name_ar, name_en, kc, group in USE_CATEGORIES:
            conn.execute(
                "INSERT INTO plant_use_categories(name_ar, name_en, planning_kc, kc_note_ar, "
                "kc_note_en, group_ar) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(name_ar) DO UPDATE SET name_en = excluded.name_en, "
                "planning_kc = excluded.planning_kc, group_ar = excluded.group_ar",
                (name_ar, name_en, kc,
                 "معامل تخطيطي مؤقت لمجموعة المحاصيل الخضرية",
                 "provisional planning Kc for the vegetable crop group",
                 group),
            )
        # The old fruit-tree category joins the fruit group as well.
        conn.execute(
            "UPDATE plant_use_categories SET group_ar = 'fruit' WHERE name_ar = 'شجرة مثمرة'"
        )

        # ── move the existing edible fruit trees into the fruit group ─────
        moved = 0
        for scientific_name in EXISTING_FRUIT_SPECIES:
            ids = [r["plant_id"] for r in conn.execute(
                "SELECT plant_id FROM plant_taxa WHERE scientific_name = ?", (scientific_name,)
            )]
            for plant_id in ids:
                conn.execute(
                    "UPDATE plants SET use_category_ar = ? WHERE id = ?", (FRUIT, plant_id)
                )
                if scientific_name in RENAMED:
                    name_ar, name_en = RENAMED[scientific_name]
                    conn.execute(
                        "UPDATE plants SET name_ar = ?, name_en = ? WHERE id = ?",
                        (name_ar, name_en, plant_id),
                    )
                moved += 1

        # ── the new plants ────────────────────────────────────────────────
        next_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM plants").fetchone()[0] + 1
        next_sort = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) FROM plants"
        ).fetchone()[0] + 1
        plant_ids: dict[str, int] = {}
        inserted = 0
        for row in rows:
            existing = conn.execute(
                "SELECT id FROM plants WHERE name_en = ?", (row["name_en"],)
            ).fetchone()
            if existing:
                plant_id = existing["id"]
            else:
                plant_id = next_id
                next_id += 1
                conn.execute(
                    "INSERT INTO plants(name_ar, name_en, water_class, temp_min_c, temp_max_c, "
                    "use_category_ar, beauty, co2_kg_year, catalog, sort_order) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (row["name_ar"], row["name_en"], int(row["water_class"]),
                     float(row["temp_min_c"]), float(row["temp_max_c"]), row["use"],
                     int(row["beauty"]), float(row["co2_kg_year"]), row["catalog"], next_sort),
                )
                next_sort += 1
                inserted += 1
            plant_ids[row["name_en"]] = plant_id

            # soils
            conn.execute("DELETE FROM plant_soils WHERE plant_id = ?", (plant_id,))
            for order, soil in enumerate(s for s in row["soils"].split("|") if s):
                conn.execute(
                    "INSERT INTO plant_soils(plant_id, soil_name_ar, sort_order) VALUES (?, ?, ?)",
                    (plant_id, soil, order),
                )

            # farming details
            conn.execute("DELETE FROM crop_details WHERE plant_id = ?", (plant_id,))
            conn.execute(
                "INSERT INTO crop_details(plant_id, crop_type, lifecycle, spacing_cm, "
                "row_spacing_cm, sowing_months, harvest_days, kc, soil_strict) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (plant_id, row["crop_type"], row["lifecycle"], float(row["spacing_cm"]),
                 float(row["row_spacing_cm"]), row["sowing_months"], int(row["harvest_days"]),
                 float(row["kc"]), int(row.get("soil_strict", 0))),
            )

        added_names = update_names_csv(rows, plant_ids)

    print(f"{db_path.name}: {inserted} new plants, {moved} existing plants moved to the fruit group")
    print(f"  {added_names} scientific names added to {NAMES_CSV.relative_to(ROOT)}")
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    reference = hassouna_db.load_reference_data(db_path)
    plants = reference["plants"]
    print(f"  catalog now holds {len(plants)} plants; "
          f"{len(reference['soil_properties'])} soil rules; "
          f"groups: {sorted(set(reference['use_groups'].values()))}")
    edible = plants[plants["group"] != "ornamental"]
    print(f"  edible plants: {len(edible)} "
          f"(vegetables {int((edible['group'] == 'vegetable').sum())}, "
          f"fruits {int((edible['group'] == 'fruit').sum())})")


if __name__ == "__main__":
    main()
