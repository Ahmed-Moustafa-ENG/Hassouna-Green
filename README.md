# Hassouna Green — Sustainable Land Planning

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

## Optional AI section

Put your OpenRouter key in `.streamlit/secrets.toml` (this file is ignored by Git):

```
OPENROUTER_API_KEY = "sk-or-v1-..."
```

On Streamlit Community Cloud, paste the same line into the app's **Secrets** setting instead.
