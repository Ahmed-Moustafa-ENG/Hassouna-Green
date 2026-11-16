# Hassouna Green — Machine-learning & deep-learning judge

The judge answers one question for every recommended plant:

> **Does this plant tolerate this site's heat and cold?** More precisely: how typical are the site's temperatures of the places where this plant is actually found growing, wild or planted?

It sits on the results page next to the rule-based score. The rule-based score checks water, soil, diversity and beauty with programmed weights. The ML judge is a separate check, learned from real data.

## What it learned from

| Item | Detail |
|---|---|
| Plant records | 528,839 iNaturalist observations since 1950: 291,969 wild (research grade) and 236,870 planted ones, counted only when other users agree with the identification (`captive=true, identifications=most_agree`) |
| Plants | 398 distinct scientific names in `plant_scientific_names.csv`, of which 397 matched an iNaturalist taxon and 372 were modelled, covering 417 of the 427 catalog plants (the 10 generic entries such as "Ornamental Palm" have no scientific name and are not judged) |
| Climate | WorldClim 2.1 normals (1970–2000) at 10 arc-minutes (~18 km): annual mean temperature, temperature seasonality, warmest-month maximum, coldest-month minimum |
| Training grid | 53,991 land cells that contain at least one record |

**Why planted records are included:** in Egypt and the Gulf almost every landscape plant is planted and irrigated. Wild records alone gave 0 Bougainvillea records in Egypt and the Gulf, against 584 planted ones. With wild records only, the judge rated every plant in a typical Dubai design as unsuitable.

**Why rainfall is left out:** in a landscape, irrigation replaces rain, and the app's ET₀ × Kc water engine already handles water demand.

**How a crop variety is handled:** iNaturalist records a cultivar under its
species, so "Brassica oleracea var. capitata" (cabbage) is not a taxon there.
`species_fallbacks.csv` maps 26 names to the taxon iNaturalist actually uses -
either the parent species or the accepted name (`Raphanus sativus` →
`Raphanus raphanistrum sativus`, `Sechium edule` → `Sicyos edulis`,
`Actinidia deliciosa` → `Actinidia chinensis`, `Feronia limonia` →
`Limonia acidissima`). The crops therefore share their species' climate
niche, which is what the observations actually describe. Only grapefruit
(`Citrus paradisi`) has no taxon in iNaturalist and stays unjudged.

## The two models

1. **Classic machine learning:** one logistic regression per plant on the 4 temperature variables and their squares (8 terms). This is the standard model in species-distribution research.
2. **Deep learning:** one PyTorch neural network, 4 → 256 → 256 → 128 → 372 outputs, predicting all plants at once.

The app averages the two. It then reports a **climate match**: the site's percentile among the plant's own known locations.
- Below the 10th percentile, the site is *outside the known range* (the standard 10%-omission threshold in species-distribution modelling).
- The plant score maps 0–10th percentile → 0–60, 10th–50th → 60–100, and 50th or higher → 100. So **60 = edge of the known range** and **100 = as typical as the plant's median location**. The design score is the average over the judged plants.

Background (non-presence) cells are places where *other catalog plants* were recorded but this one was not. This is called a target-group background, and it cancels most of the bias from people recording more in some regions than others.

## How it was tested and the measured results

**5-fold spatial block cross-validation.** The world is cut into 5° × 5° blocks, and every block is scored by models trained *without* that block. This tests prediction in new regions; a random split would leak information between nearby cells and inflate the score. The metric is ROC AUC: 0.5 = random guessing, 1.0 = perfect.

| Method | Mean AUC | Median AUC | Plants with AUC ≥ 0.7 |
|---|---|---|---|
| Logistic regression (ML) | 0.799 | 0.812 | 84.1% |
| Deep neural network (DL) | 0.809 | 0.821 | 88.7% |
| Both combined (used in the app) | 0.809 | 0.822 | 88.2% |
| App catalog temperature ranges (baseline) | 0.612 | 0.629 | 34.7% |

All numbers are computed by `train_ml_judge.py` and stored in `ml_judge_card.json` (with a per-plant table); none are typed in by hand. A wild-records-only, 7-variable version scored higher (combined AUC 0.861) but answered the wrong question for irrigated landscapes, as explained above.

The earlier model, trained on 173 landscape plants only, scored 0.803 combined. Doubling the catalog to 372 taxa - mostly crops - did not cost accuracy.

## Limitations (also shown in the app)

- Records show where a plant has been seen growing; a region with no records may be unrecorded rather than unsuitable.
- Temperature only. Soil, salinity and water are judged by the rule-based score and the water engine.
- Climate normals are 1970–2000 at ~18 km, so city microclimates are not resolved.
- Some planted records may be indoor or greenhouse plants, which can make a plant look more cold-tolerant than it is.
- Year-round climate is used, so cool-season bedding plants (e.g. pansy) grown only in winter may be judged unfairly. The same applies to winter vegetables: the judge compares the site with the places the crop is recorded in all year.
- Citizen-science records are densest in Europe and North America; the target-group background reduces this bias but does not remove it.
- Genus-level entries (e.g. Bougainvillea, Cassia) are modelled at genus level.
- Crops that share a species share a climate niche, so cabbage and cauliflower get the same score.
- The warming slider adds +1/+2/+3 °C to all temperatures. It is a sensitivity test, not a climate projection.

## Files

| File | Needed to run the app? | Purpose |
|---|---|---|
| `../ml_judge.py` | yes | Runs the exported weights with numpy only (no PyTorch needed) |
| `ml_judge_model.npz` | yes | Weights of both models plus percentile tables (~970 kB) |
| `ml_judge_card.json` | yes | Data summary, test method, measured scores, per-plant AUCs, limitations |
| `../hassouna_green.db` | yes | Schema v3: adds `plant_taxa` (scientific names and iNaturalist ids) and `location_climate` |
| `plant_scientific_names.csv` | no | Editable mapping from catalog plant id to scientific name |
| `species_fallbacks.csv` | no | Names iNaturalist does not list as they are, and the name it uses instead |
| `build_training_data.py` | no | Downloads records and climate and builds `data/` |
| `train_ml_judge.py` | no | Trains, cross-validates and exports the models |
| `update_database.py` | no | Writes `plant_taxa` and `location_climate` into the database |
| `data/` | no | Built training set (`training_cells.npz`), per-plant summary, location climates |
| `requirements-train.txt` | no | Extra libraries for rebuilding or retraining only |

## Retraining (optional, Windows PowerShell, from the project folder)

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r ml\requirements-train.txt
.\.venv\Scripts\python.exe ml\build_training_data.py     # ~1 hour: iNaturalist allows ~60 requests/minute; resumes if interrupted
.\.venv\Scripts\python.exe ml\train_ml_judge.py          # ~3 minutes
.\.venv\Scripts\python.exe ml\update_database.py
```

You only need to retrain after adding plants to the catalog: add their scientific names to `plant_scientific_names.csv` first. To retrain from the included `data/training_cells.npz` without downloading anything, run only the last two commands.

## Data credits

- iNaturalist (api.inaturalist.org). Observations are contributed by the iNaturalist community under the licences chosen by each observer. **The raw observations are not redistributed here**: `build_training_data.py` downloads them and keeps them in `ml/data/occurrence_cache/`, which is outside the repository. What is published is the derived model (`ml_judge_model.npz`) and a per-taxon summary (`data/taxa_summary.csv`).
- Fick, S.E. & Hijmans, R.J. (2017). WorldClim 2: new 1-km spatial resolution climate surfaces for global land areas. *International Journal of Climatology* 37: 4302–4315. The climate surfaces are also downloaded at build time and not redistributed; only the nearest-cell normals for each app location are published.

The project's own copyright and the terms of this material are described in
[LICENSE](../LICENSE) and in the third-party notices of the main
[README](../README.md).
