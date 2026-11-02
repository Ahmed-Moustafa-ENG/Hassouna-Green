"""Hassouna Green ML + deep-learning judge (runtime part, numpy only).

The models are trained offline by ``ml/train_ml_judge.py`` on real plant
observations (iNaturalist: wild research-grade records plus planted records
with an agreed identification) and WorldClim temperature data. This
module only loads the exported weights from ``ml/ml_judge_model.npz`` and runs
them, so the app needs no PyTorch or scikit-learn.

For each recommended plant the judge answers one question:

    "How typical are this site's temperatures of the places where this plant
     is actually found growing, wild or planted?"

Two independent models answer it:

* classic machine learning - a logistic regression per plant taxon;
* deep learning - a multi-label neural network (3 hidden layers).

Their average is converted to a *climate match*: the percentile of the site's
score among the plant's own known locations. Below the 10th percentile the
site is outside the plant's known climate range. Rainfall, soil, salinity and
irrigation are deliberately left to the rule-based engine and the ET0 water
calculation, because irrigation replaces rain in a landscape.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

MODEL_DIR = Path(__file__).resolve().parent / "ml"
MODEL_FILE = "ml_judge_model.npz"
CARD_FILE = "ml_judge_card.json"
WARMING_FEATURES = ("bio1", "bio5", "bio6")      # temperatures shifted in the warming stress test
WITHIN_RANGE_PCT = 10.0                            # 10th-percentile training-presence threshold
FULL_MARKS_PCT = 50.0                              # site as typical as the median known location
RANGE_EDGE_SCORE = 60.0                            # plant score at the edge of the known range


def plant_score(match_pct: float) -> float:
    """Map a climate-match percentile to a 0-100 plant score.

    0-10th percentile (outside the known range) -> 0-60, 10th-50th -> 60-100,
    50th and above -> 100. So 60 marks the edge of the plant's known range and
    100 means the site is as typical as the plant's median known location.
    """
    if match_pct >= FULL_MARKS_PCT:
        return 100.0
    if match_pct >= WITHIN_RANGE_PCT:
        return RANGE_EDGE_SCORE + (100.0 - RANGE_EDGE_SCORE) * (match_pct - WITHIN_RANGE_PCT) / (
            FULL_MARKS_PCT - WITHIN_RANGE_PCT)
    return RANGE_EDGE_SCORE * max(0.0, match_pct) / WITHIN_RANGE_PCT


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


class MLJudge:
    """Loads exported weights and scores plants for a location's climate."""

    def __init__(self, folder: str | Path = MODEL_DIR):
        folder = Path(folder)
        with np.load(folder / MODEL_FILE, allow_pickle=False) as d:
            self.version = str(d["model_version"])
            self.feature_names = [str(x) for x in d["feature_names"]]
            self.log_idx = d["log_idx"].astype(int)
            self.mean = d["mean"].astype(np.float64)
            self.std = d["std"].astype(np.float64)
            self.glm_W = d["glm_W"].astype(np.float64)
            self.glm_b = d["glm_b"].astype(np.float64)
            self.dnn = [(d[f"dnn_W{i}"].astype(np.float32), d[f"dnn_b{i}"].astype(np.float32))
                        for i in range(int(d["n_layers"]))]
            self.taxon_keys = d["taxon_keys"].astype(np.int64)
            self.taxon_names = [str(x) for x in d["taxon_names"]]
            self.n_cells = d["n_cells"].astype(int)
            self.quantiles = {k: d[f"q_{k}"].astype(np.float64) for k in ("glm", "dnn", "ens")}
        self.card = json.loads((folder / CARD_FILE).read_text(encoding="utf-8"))
        self.index = {int(k): i for i, k in enumerate(self.taxon_keys)}
        self._pct_axis = np.linspace(0.0, 100.0, self.quantiles["ens"].shape[1])

    @classmethod
    def load(cls, folder: str | Path = MODEL_DIR) -> "MLJudge | None":
        """Return the judge, or None when the model files are not installed."""
        folder = Path(folder)
        if not (folder / MODEL_FILE).is_file() or not (folder / CARD_FILE).is_file():
            return None
        return cls(folder)

    # ---------------------------------------------------------------- models
    def _features(self, climate: dict, warming: float) -> np.ndarray:
        x = np.array([float(climate[name]) for name in self.feature_names], dtype=np.float64)
        for name in WARMING_FEATURES:
            x[self.feature_names.index(name)] += warming
        x[self.log_idx] = np.log1p(np.clip(x[self.log_idx], 0.0, None))
        return ((x - self.mean) / self.std)[None, :]

    def raw_scores(self, climate: dict, warming: float = 0.0) -> dict[str, np.ndarray]:
        """Model outputs for every taxon: logistic regression, neural network, average."""
        z = self._features(climate, warming)
        glm = _sigmoid(np.hstack([z, z ** 2]) @ self.glm_W.T + self.glm_b)[0]
        h = z.astype(np.float32)
        for i, (W, b) in enumerate(self.dnn):
            h = h @ W + b
            if i < len(self.dnn) - 1:
                h = np.maximum(h, 0.0)
        dnn = _sigmoid(h.astype(np.float64))[0]
        return {"glm": glm, "dnn": dnn, "ens": (glm + dnn) / 2.0}

    def _percentile(self, kind: str, t: int, value: float) -> float:
        q = self.quantiles[kind][t]
        return float(np.interp(value, q, self._pct_axis, left=0.0, right=100.0))

    # ------------------------------------------------------------- judging
    def judge(self, plants: list[dict], climate: dict, warming: float = 0.0) -> dict:
        """Score plants (dicts with name, scientific_name, taxon_key) for one climate."""
        scores = self.raw_scores(climate, warming)
        rows, seen = [], set()
        for plant in plants:
            if plant["name"] in seen:
                continue
            seen.add(plant["name"])
            key = plant.get("taxon_key")
            t = None
            if key is not None and not (isinstance(key, float) and math.isnan(key)):
                t = self.index.get(int(key))
            row = {"name": plant["name"], "scientific_name": plant.get("scientific_name") or "",
                   "modeled": t is not None}
            if t is not None:
                glm_pct = self._percentile("glm", t, scores["glm"][t])
                dnn_pct = self._percentile("dnn", t, scores["dnn"][t])
                ens_pct = self._percentile("ens", t, scores["ens"][t])
                row.update(glm_pct=glm_pct, dnn_pct=dnn_pct, match_pct=ens_pct,
                           within_range=ens_pct >= WITHIN_RANGE_PCT,
                           score=plant_score(ens_pct),
                           known_cells=int(self.n_cells[t]))
            rows.append(row)
        modeled = [r for r in rows if r["modeled"]]
        return {
            "rows": rows,
            "warming": warming,
            "n_total": len(rows),
            "n_modeled": len(modeled),
            "n_within": sum(r["within_range"] for r in modeled),
            "score": round(sum(r["score"] for r in modeled) / len(modeled), 1) if modeled else None,
        }

    def stress_test(self, plants: list[dict], climate: dict, steps=(0.0, 1.0, 2.0, 3.0)) -> list[dict]:
        """Design score and plants within range under uniform warming scenarios."""
        out = []
        for w in steps:
            r = self.judge(plants, climate, warming=w)
            out.append({"warming": w, "score": r["score"], "n_within": r["n_within"], "n_modeled": r["n_modeled"],
                        "dropped": [x["name"] for x in r["rows"] if x["modeled"] and not x["within_range"]]})
        return out

    # ------------------------------------------------------------ metadata
    def metrics(self) -> dict:
        return self.card["evaluation"]

    def data_summary(self) -> dict:
        return self.card["data"]
