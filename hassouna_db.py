"""SQLite data layer for Hassouna Green.

The app's reference data lives in ``hassouna_green.db``, stored next to this
file by default. Every text record is stored in both Arabic (``*_ar``) and
English (``*_en``):

* countries and their locations (governorates, emirates, municipalities)
* location descriptions and regions
* monthly average-temperature normals for each location
* soil types, their short trait descriptions, location soil options and
  each region's default soil
* soil-compatibility rules used by the recommendation engine
* the plant catalog and each plant's suitable soils
* plant-use categories with provisional landscape Kc planning values
* each plant's scientific name and taxon id (``plant_taxa``) and each
  location's WorldClim climate normals (``location_climate``), used by the
  machine-learning judge in ``ml_judge.py``

The Arabic names are the app's internal identifiers (for example, a selected
soil is stored as its Arabic name); the English columns are display labels.

To use a different database file, set the ``HASSOUNA_DB`` environment
variable to its path. Only Python's built-in ``sqlite3`` module is required.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

SCHEMA_VERSION = 3
DB_FILENAME = "hassouna_green.db"
DEFAULT_DB_PATH = Path(__file__).resolve().with_name(DB_FILENAME)
CLIMATE_FEATURES = ("bio1", "bio4", "bio5", "bio6", "bio12", "bio15", "bio17")

REQUIRED_TABLES = (
    "meta",
    "countries",
    "soil_types",
    "soil_traits",
    "soil_compatibility",
    "locations",
    "location_monthly_temperatures",
    "location_soil_types",
    "regions",
    "plant_use_categories",
    "plants",
    "plant_soils",
    "plant_taxa",
    "location_climate",
)

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS countries (
    id         INTEGER PRIMARY KEY,
    name_ar    TEXT NOT NULL UNIQUE CHECK (length(trim(name_ar)) > 0),
    name_en    TEXT NOT NULL UNIQUE CHECK (length(trim(name_en)) > 0),
    sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS soil_types (
    id         INTEGER PRIMARY KEY,
    name_ar    TEXT NOT NULL UNIQUE CHECK (length(trim(name_ar)) > 0),
    name_en    TEXT NOT NULL UNIQUE CHECK (length(trim(name_en)) > 0),
    sort_order INTEGER NOT NULL
);

-- Short soil descriptions shown in the land-data step.
CREATE TABLE IF NOT EXISTS soil_traits (
    soil_name_ar TEXT NOT NULL REFERENCES soil_types(name_ar) ON UPDATE CASCADE ON DELETE CASCADE,
    sort_order   INTEGER NOT NULL,
    trait_ar     TEXT NOT NULL CHECK (length(trim(trait_ar)) > 0),
    trait_en     TEXT NOT NULL CHECK (length(trim(trait_en)) > 0),
    PRIMARY KEY (soil_name_ar, sort_order)
);

-- compatible_soil is a soil_types.name_ar value or the wildcard 'any'.
CREATE TABLE IF NOT EXISTS soil_compatibility (
    soil_name_ar    TEXT NOT NULL REFERENCES soil_types(name_ar) ON UPDATE CASCADE ON DELETE CASCADE,
    compatible_soil TEXT NOT NULL,
    sort_order      INTEGER NOT NULL,
    PRIMARY KEY (soil_name_ar, compatible_soil)
);

CREATE TABLE IF NOT EXISTS locations (
    id         INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    name_ar    TEXT NOT NULL UNIQUE CHECK (length(trim(name_ar)) > 0),
    name_en    TEXT NOT NULL UNIQUE CHECK (length(trim(name_en)) > 0),
    latitude   REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude  REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    desc_ar    TEXT NOT NULL CHECK (length(trim(desc_ar)) > 0),
    desc_en    TEXT NOT NULL CHECK (length(trim(desc_en)) > 0),
    sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS location_monthly_temperatures (
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    month       INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    avg_temp_c  NUMERIC NOT NULL,
    PRIMARY KEY (location_id, month)
);

CREATE TABLE IF NOT EXISTS location_soil_types (
    location_id  INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    soil_name_ar TEXT NOT NULL REFERENCES soil_types(name_ar) ON UPDATE CASCADE,
    sort_order   INTEGER NOT NULL,
    PRIMARY KEY (location_id, soil_name_ar)
);

CREATE TABLE IF NOT EXISTS regions (
    id              INTEGER PRIMARY KEY,
    location_id     INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    name_ar         TEXT NOT NULL CHECK (length(trim(name_ar)) > 0),
    name_en         TEXT NOT NULL CHECK (length(trim(name_en)) > 0),
    default_soil_ar TEXT NOT NULL REFERENCES soil_types(name_ar) ON UPDATE CASCADE,
    sort_order      INTEGER NOT NULL,
    UNIQUE (location_id, name_ar),
    UNIQUE (location_id, name_en)
);

CREATE TABLE IF NOT EXISTS plant_use_categories (
    name_ar     TEXT PRIMARY KEY CHECK (length(trim(name_ar)) > 0),
    name_en     TEXT NOT NULL UNIQUE CHECK (length(trim(name_en)) > 0),
    planning_kc REAL NOT NULL CHECK (planning_kc > 0 AND planning_kc <= 1.5),
    kc_note_ar  TEXT NOT NULL DEFAULT '',
    kc_note_en  TEXT NOT NULL DEFAULT ''
);

-- water_class is the app's ordinal catalog filter (1 = low, 3 = high); it is
-- not a measured water requirement.
CREATE TABLE IF NOT EXISTS plants (
    id              INTEGER PRIMARY KEY,
    name_ar         TEXT NOT NULL CHECK (length(trim(name_ar)) > 0),
    name_en         TEXT NOT NULL UNIQUE CHECK (length(trim(name_en)) > 0),
    water_class     INTEGER NOT NULL CHECK (water_class BETWEEN 1 AND 3),
    temp_min_c      NUMERIC NOT NULL,
    temp_max_c      NUMERIC NOT NULL,
    use_category_ar TEXT NOT NULL REFERENCES plant_use_categories(name_ar) ON UPDATE CASCADE,
    beauty          INTEGER NOT NULL CHECK (beauty BETWEEN 1 AND 5),
    co2_kg_year     NUMERIC NOT NULL CHECK (co2_kg_year >= 0),
    catalog         TEXT NOT NULL CHECK (catalog IN ('egypt', 'gulf')),
    sort_order      INTEGER NOT NULL,
    CHECK (temp_min_c <= temp_max_c)
);

-- soil_name_ar is a soil_types.name_ar value or the wildcard 'any'.
CREATE TABLE IF NOT EXISTS plant_soils (
    plant_id     INTEGER NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    soil_name_ar TEXT NOT NULL,
    sort_order   INTEGER NOT NULL,
    PRIMARY KEY (plant_id, soil_name_ar)
);

-- Scientific name of each plant for the ML judge. Plants with a generic or
-- unidentified catalog name have no row. taxon_key is the id in taxon_source
-- (NULL when the name was not found there).
CREATE TABLE IF NOT EXISTS plant_taxa (
    plant_id        INTEGER PRIMARY KEY REFERENCES plants(id) ON DELETE CASCADE,
    scientific_name TEXT NOT NULL CHECK (length(trim(scientific_name)) > 0),
    taxon_source    TEXT NOT NULL CHECK (taxon_source IN ('inat', 'gbif')),
    taxon_key       INTEGER,
    taxon_rank      TEXT NOT NULL DEFAULT '',
    note            TEXT NOT NULL DEFAULT ''
);

-- WorldClim 2.1 climate normals (1970-2000) at the nearest 10-arc-minute land
-- cell to each location: bio1 annual mean temperature (C), bio4 temperature
-- seasonality, bio5 / bio6 warmest-month max / coldest-month min (C), bio12
-- annual rainfall (mm), bio15 rainfall seasonality, bio17 driest-quarter rain (mm).
CREATE TABLE IF NOT EXISTS location_climate (
    location_id INTEGER PRIMARY KEY REFERENCES locations(id) ON DELETE CASCADE,
    bio1        REAL NOT NULL,
    bio4        REAL NOT NULL,
    bio5        REAL NOT NULL,
    bio6        REAL NOT NULL,
    bio12       REAL NOT NULL CHECK (bio12 >= 0),
    bio15       REAL NOT NULL,
    bio17       REAL NOT NULL CHECK (bio17 >= 0),
    cell_lat    REAL NOT NULL,
    cell_lon    REAL NOT NULL,
    source      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_locations_country ON locations(country_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_regions_location ON regions(location_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_plants_order ON plants(sort_order);
"""


class DatabaseError(RuntimeError):
    """Raised when the reference database is missing, outdated or invalid."""


def database_path() -> Path:
    """Return the database path from ``HASSOUNA_DB`` or the default location."""
    configured = os.environ.get("HASSOUNA_DB")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DB_PATH


def database_signature(path: str | Path | None = None) -> tuple[str, int | None, int | None]:
    """Return a cache key that changes when the database file is edited."""
    db_path = Path(path).expanduser().resolve() if path else database_path()
    try:
        stat = db_path.stat()
    except FileNotFoundError:
        return str(db_path), None, None
    return str(db_path), stat.st_mtime_ns, stat.st_size


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes in an open SQLite connection."""
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    """Open an existing Hassouna Green database without creating a new file."""
    db_path = Path(path).expanduser().resolve() if path else database_path()
    if not db_path.is_file():
        raise DatabaseError(
            f"Database file not found: {db_path}. Put {DB_FILENAME} in the same "
            "folder as 22_updated.py and hassouna_db.py, or set HASSOUNA_DB to its path."
        )
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _check_schema(conn: sqlite3.Connection) -> None:
    present = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    missing = [name for name in REQUIRED_TABLES if name not in present]
    if missing:
        raise DatabaseError(f"Database is missing required table(s): {', '.join(missing)}")
    row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    if row is None or row["value"] != str(SCHEMA_VERSION):
        found = row["value"] if row else "none"
        raise DatabaseError(
            f"Unsupported database schema version {found}; expected {SCHEMA_VERSION}. "
            f"Download the matching {DB_FILENAME} together with hassouna_db.py."
        )


def _grouped(rows, key: str, value: str) -> dict:
    grouped: dict = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row[value])
    return grouped


def load_reference_data(path: str | Path | None = None) -> dict:
    """Load and validate all reference data used by the app.

    Returns a dictionary with the structures the Streamlit app uses:
    ``locations`` (keyed by Arabic name, each with ``name_en`` and
    ``region_names_en``), ``country_location_keys``, ``countries``,
    ``country_labels_en``, ``soil_types``, ``soil_labels_en``, ``soil_traits``,
    ``soil_compatibility``, ``use_kc``, ``use_labels_en`` and ``plants``
    (a pandas DataFrame).
    """
    with closing(connect(path)) as conn:
        _check_schema(conn)

        countries = conn.execute(
            "SELECT id, name_ar, name_en FROM countries ORDER BY sort_order, id"
        ).fetchall()
        if not countries:
            raise DatabaseError("The countries table is empty.")
        country_by_id = {row["id"]: row["name_ar"] for row in countries}

        soil_rows = conn.execute(
            "SELECT name_ar, name_en FROM soil_types ORDER BY sort_order, id"
        ).fetchall()
        soil_traits: dict[str, list[dict]] = {}
        for row in conn.execute(
            "SELECT soil_name_ar, trait_ar, trait_en FROM soil_traits ORDER BY soil_name_ar, sort_order"
        ):
            soil_traits.setdefault(row["soil_name_ar"], []).append(
                {"ar": row["trait_ar"], "en": row["trait_en"]}
            )
        soil_compatibility = _grouped(
            conn.execute(
                "SELECT soil_name_ar, compatible_soil FROM soil_compatibility "
                "ORDER BY soil_name_ar, sort_order"
            ),
            "soil_name_ar",
            "compatible_soil",
        )

        location_rows = conn.execute(
            "SELECT l.id, l.country_id, l.name_ar, l.name_en, l.latitude, l.longitude, "
            "l.desc_ar, l.desc_en "
            "FROM locations l JOIN countries c ON c.id = l.country_id "
            "ORDER BY c.sort_order, l.sort_order, l.id"
        ).fetchall()
        if not location_rows:
            raise DatabaseError("The locations table is empty.")

        temps: dict[int, dict[int, float]] = {}
        for row in conn.execute(
            "SELECT location_id, month, avg_temp_c FROM location_monthly_temperatures"
        ):
            temps.setdefault(row["location_id"], {})[row["month"]] = row["avg_temp_c"]
        location_soils = _grouped(
            conn.execute(
                "SELECT location_id, soil_name_ar FROM location_soil_types "
                "ORDER BY location_id, sort_order"
            ),
            "location_id",
            "soil_name_ar",
        )
        region_rows: dict[int, list] = {}
        for row in conn.execute(
            "SELECT location_id, name_ar, name_en, default_soil_ar FROM regions "
            "ORDER BY location_id, sort_order, id"
        ):
            region_rows.setdefault(row["location_id"], []).append(row)
        climate_by_location = {
            row["location_id"]: {name: float(row[name]) for name in CLIMATE_FEATURES}
            for row in conn.execute("SELECT * FROM location_climate")
        }

        locations: dict[str, dict] = {}
        country_location_keys = {row["name_ar"]: [] for row in countries}
        for row in location_rows:
            location_id = row["id"]
            month_values = temps.get(location_id, {})
            if sorted(month_values) != list(range(1, 13)):
                raise DatabaseError(
                    f"Location '{row['name_ar']}' must have temperatures for months 1-12."
                )
            regions = region_rows.get(location_id, [])
            if not regions:
                raise DatabaseError(f"Location '{row['name_ar']}' has no regions.")
            soils = location_soils.get(location_id, [])
            if not soils:
                raise DatabaseError(f"Location '{row['name_ar']}' has no soil types.")
            country = country_by_id[row["country_id"]]
            locations[row["name_ar"]] = {
                "country": country,
                "name_ar": row["name_ar"],
                "name_en": row["name_en"],
                "regions": [region["name_ar"] for region in regions],
                "region_names_en": {region["name_ar"]: region["name_en"] for region in regions},
                "monthly_temp": [month_values[month] for month in range(1, 13)],
                "soil_types": soils,
                "region_soils": {region["name_ar"]: region["default_soil_ar"] for region in regions},
                "lat": row["latitude"],
                "lon": row["longitude"],
                "desc_ar": row["desc_ar"],
                "desc_en": row["desc_en"],
                "climate": climate_by_location.get(location_id),
            }
            country_location_keys[country].append(row["name_ar"])

        use_rows = conn.execute(
            "SELECT name_ar, name_en, planning_kc FROM plant_use_categories ORDER BY name_ar"
        ).fetchall()

        plant_soils = _grouped(
            conn.execute(
                "SELECT plant_id, soil_name_ar FROM plant_soils ORDER BY plant_id, sort_order"
            ),
            "plant_id",
            "soil_name_ar",
        )
        taxa = {
            row["plant_id"]: row
            for row in conn.execute(
                "SELECT plant_id, scientific_name, taxon_source, taxon_key, taxon_rank FROM plant_taxa"
            )
        }
        plant_rows = conn.execute(
            "SELECT id, name_ar, name_en, water_class, temp_min_c, temp_max_c, "
            "use_category_ar, beauty, co2_kg_year, catalog "
            "FROM plants ORDER BY sort_order, id"
        ).fetchall()
        if not plant_rows:
            raise DatabaseError("The plants table is empty.")
        plants = []
        for row in plant_rows:
            soils = plant_soils.get(row["id"], [])
            if not soils:
                raise DatabaseError(f"Plant '{row['name_en']}' has no soil entries.")
            taxon = taxa.get(row["id"])
            plants.append(
                {
                    "name": row["name_ar"],
                    "name_en": row["name_en"],
                    "water": row["water_class"],
                    "soil": soils,
                    "temp_min": row["temp_min_c"],
                    "temp_max": row["temp_max_c"],
                    "use": row["use_category_ar"],
                    "beauty": row["beauty"],
                    "co2": row["co2_kg_year"],
                    "catalog": row["catalog"],
                    "scientific_name": taxon["scientific_name"] if taxon else "",
                    "taxon_source": taxon["taxon_source"] if taxon else "",
                    "taxon_key": taxon["taxon_key"] if taxon else None,
                }
            )

    return {
        "locations": locations,
        "country_location_keys": country_location_keys,
        "countries": [row["name_ar"] for row in countries],
        "country_labels_en": {row["name_ar"]: row["name_en"] for row in countries},
        "soil_types": [row["name_ar"] for row in soil_rows],
        "soil_labels_en": {row["name_ar"]: row["name_en"] for row in soil_rows},
        "soil_traits": soil_traits,
        "soil_compatibility": soil_compatibility,
        "use_kc": {row["name_ar"]: float(row["planning_kc"]) for row in use_rows},
        "use_labels_en": {row["name_ar"]: row["name_en"] for row in use_rows},
        "plants": pd.DataFrame(plants),
    }
