# Hassouna Green — Sustainable Land Planning

**Created by Ahmed Moustafa & Abdelrahman Khaled.**

A bilingual (Arabic / English) Streamlit app that designs a planting plan for a piece of land in Egypt, the UAE or Qatar. It picks plants from a database of the plant catalog, estimates irrigation water with the FAO-56 method (ET₀ × crop coefficient), draws a layout, and scores the design.

The design is checked by three separate judges:

- a rule-based score (water, soil, diversity, beauty);
- a machine-learning judge (logistic regression and a small neural network) trained on real iNaturalist plant observations and WorldClim climate data, with its accuracy measured by spatial cross-validation (see `ml/README.md`);
- an optional AI planner and reviewer through OpenRouter (needs an API key).

## Run it on your computer

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run 22_updated.py
```

## The reference data

Everything the app knows about places, soils and plants lives in `hassouna_green.db`
(next to the app), not in the code. Edit the database, not the Python files:

| Table | What it holds |
|---|---|
| `locations`, `regions`, `countries` | Governorates, emirates and municipalities, with coordinates and monthly temperature normals |
| `soil_types`, `soil_traits` | The soil names and the short descriptions shown in the land step |
| `soil_compatibility` | Which plants each soil accepts |
| `soil_properties` | Each soil's character (family, salinity, drainage) and the planning rules that follow from it: the image-suitability penalty, whether the soil advice asks for organic matter, and whether the soil is clay-like for the sodium check |
| `plants`, `plant_soils`, `plant_use_categories` | The plant catalog, the soils each plant accepts, and the provisional landscape Kc of each use group |
| `crop_details` | The farming details of the edible crops: crop type, life cycle, planting spacing, sowing months, days to harvest and the crop's own Kc |
| `plant_taxa`, `location_climate` | Scientific names and WorldClim normals, used by the machine-learning judge |

The app reads the soil rules from the database, so a rule never depends on a soil
name being written in the code. A database written before `soil_properties` existed
still loads; those soils then use the neutral default rules.

## Vegetables and fruits

The catalog holds the landscape plants and, next to them, **233 edible crops**:
143 vegetables and 90 fruit trees, chosen for what actually grows in Egypt and
the Gulf. They are not a separate section — they are plants in the same catalog,
so they get the same treatment: the same temperature filter, the same soil and
water rules, the same machine-learning climate judge and the same map.

The **plant filter** on the results page is what selects them:

| Filter | What it shows |
|---|---|
| All Types | The whole catalog, as before |
| Vegetables | 143 vegetables, selected for the site |
| Fruits | 90 fruit trees, selected for the site |
| Ornamental plants | The landscape plants |
| any single use category | That category only |

Whatever the filter selects is what the design consists of, so the cards, the
layout map, the water estimate and the two judges all follow the selection.

Each crop also carries its farming data: the months it is sown, how long it
takes to harvest, the spacing between the plants and between the rows, and its
own crop coefficient. The results page turns that into a **planting calendar**
for the design month, and the cards show the spacing and the coefficient next
to the plant.

The source of truth is `catalog/edible_plants.csv`. To change it, edit the CSV
and run:

```
.venv\Scripts\python.exe catalog\load_catalog.py     # writes the crops into the database
.venv\Scripts\python.exe catalog\check_catalog.py     # checks the CSV against the database
```

`load_catalog.py` is idempotent, and it also adds the new scientific names to
`ml/plant_scientific_names.csv`, so the machine-learning judge can be retrained
over the new species.

## Optional AI section

Put your OpenRouter key in `.streamlit/secrets.toml` (this file is ignored by Git):

```
OPENROUTER_API_KEY = "sk-or-v1-..."
```

On Streamlit Community Cloud, paste the same line into the app's **Secrets** setting instead.

## Phones and tablets

The layout adapts to the screen: the plant cards reflow from 4 columns to 3, 2 and 1, the layout figure can be swiped sideways on phones, and buttons and inputs are sized for touch.
