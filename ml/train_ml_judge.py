"""Train and test the Hassouna Green ML / deep-learning judge.

Input : ml/data/training_cells.npz  (from build_training_data.py)
Output: ml/ml_judge_model.npz       (weights; the app runs them with numpy only)
        ml/ml_judge_card.json       (data, test method and measured scores)

Two models learn, for every plant taxon, which temperature regimes it is
actually found in, wild or planted (presence cells), versus the places where
other catalog plants were recorded but this one was not ("target-group
background", which cancels most of the observer bias of citizen-science data).

Inputs are the four WorldClim temperature variables only. Rainfall is left out
on purpose: in an irrigated landscape, irrigation replaces rain, and the app's
ET0 x Kc water engine already handles water demand. The models therefore
answer "does this plant tolerate this site's heat and cold?"

* Classic machine learning - one logistic regression per taxon on the four
  temperature variables and their squares (the standard species-distribution GLM).
* Deep learning - one multi-label neural network (4 -> 256 -> 256 -> 128 -> taxa)
  trained with PyTorch.

Testing: 5-fold *spatial block* cross-validation. The world is cut into 5 x 5
degree blocks and each block is predicted by models that never saw it, so the
score reflects new regions, not memorised neighbours. The metric is ROC AUC
(0.5 = coin flip, 1.0 = perfect ranking). The app's own catalog temperature
ranges are scored the same way as a baseline.

Run from the project folder:   python ml/train_ml_judge.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sqlite3
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ML_DIR = Path(__file__).resolve().parent
ROOT = ML_DIR.parent
DATA = ML_DIR / "data"
SEED, FOLDS, BLOCK_DEG = 42, 5, 5
# Temperature only (see module docstring): annual mean, seasonality, warmest-month
# maximum and coldest-month minimum.
MODEL_FEATURES = ("bio1", "bio4", "bio5", "bio6")
LOG_FEATURES = ("bio12", "bio17")           # rainfall amounts would be log-transformed if used
HIDDEN = (256, 256, 128)
MAX_NEG_GLM = 40000
QUANTILES = np.linspace(0.0, 1.0, 101)
MODEL_VERSION = "1.0"

torch.set_num_threads(max(1, os.cpu_count() or 1))


# ------------------------------------------------------------------ features
def make_transform(X, names):
    log_idx = np.array([i for i, n in enumerate(names) if n in LOG_FEATURES], dtype=int)
    F = X.astype(np.float64).copy()
    F[:, log_idx] = np.log1p(np.clip(F[:, log_idx], 0, None))
    return {"log_idx": log_idx, "mean": F.mean(0), "std": F.std(0) + 1e-9}


def transform(X, spec):
    F = X.astype(np.float64).copy()
    F[:, spec["log_idx"]] = np.log1p(np.clip(F[:, spec["log_idx"]], 0, None))
    return ((F - spec["mean"]) / spec["std"]).astype(np.float32)


def quad(Z):
    return np.hstack([Z, Z ** 2])


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60, 60)))


# ----------------------------------------------------------------- GLM (ML)
def fit_glm(Z, y, rng):
    pos = np.flatnonzero(y)
    neg = np.flatnonzero(~y)
    if len(neg) > MAX_NEG_GLM:
        neg = rng.choice(neg, MAX_NEG_GLM, replace=False)
    idx = np.concatenate([pos, neg])
    m = LogisticRegression(C=1.0, class_weight="balanced", max_iter=3000)
    m.fit(quad(Z[idx]), y[idx])
    return m.coef_[0].astype(np.float64), float(m.intercept_[0])


def fit_glms(Z, Y, seed):
    rng = np.random.default_rng(seed)
    W = np.zeros((Y.shape[1], Z.shape[1] * 2))
    b = np.zeros(Y.shape[1])
    for t in range(Y.shape[1]):
        W[t], b[t] = fit_glm(Z, Y[:, t], rng)
    return W, b


def glm_predict(Z, W, b):
    return sigmoid(quad(Z).astype(np.float64) @ W.T + b).astype(np.float32)


# ------------------------------------------------------- neural network (DL)
class Net(torch.nn.Module):
    def __init__(self, n_in, n_out):
        super().__init__()
        layers, prev = [], n_in
        for h in HIDDEN:
            layers += [torch.nn.Linear(prev, h), torch.nn.ReLU(), torch.nn.Dropout(0.2)]
            prev = h
        layers.append(torch.nn.Linear(prev, n_out))
        self.body = torch.nn.Sequential(*layers)

    def forward(self, x):
        return self.body(x)


def fit_dnn(Ztr, Ytr, seed, Zva=None, Yva=None, epochs=60, patience=6):
    torch.manual_seed(seed)
    np.random.seed(seed)
    net = Net(Ztr.shape[1], Ytr.shape[1])
    pos = Ytr.sum(0)
    pos_weight = np.clip((len(Ytr) - pos) / np.maximum(pos, 1), 1.0, 100.0)
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, dtype=torch.float32))
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-5)
    xt, yt = torch.from_numpy(Ztr), torch.from_numpy(Ytr.astype(np.float32))
    best, best_state, best_epoch, bad = np.inf, None, epochs, 0
    for epoch in range(1, epochs + 1):
        net.train()
        perm = torch.randperm(len(xt))
        for i in range(0, len(xt), 1024):
            j = perm[i:i + 1024]
            opt.zero_grad()
            loss_fn(net(xt[j]), yt[j]).backward()
            opt.step()
        if Zva is None:
            continue
        net.eval()
        with torch.no_grad():
            v = float(loss_fn(net(torch.from_numpy(Zva)), torch.from_numpy(Yva.astype(np.float32))))
        if v < best - 1e-4:
            best, best_state, best_epoch, bad = v, {k: t.clone() for k, t in net.state_dict().items()}, epoch, 0
        else:
            bad += 1
            if bad >= patience:
                break
    if best_state is not None:
        net.load_state_dict(best_state)
    net.eval()
    return net, best_epoch


def dnn_weights(net):
    lin = [m for m in net.body if isinstance(m, torch.nn.Linear)]
    return [(m.weight.detach().numpy().T.astype(np.float32), m.bias.detach().numpy().astype(np.float32)) for m in lin]


def dnn_predict_numpy(Z, weights):
    h = Z.astype(np.float32)
    for k, (W, b) in enumerate(weights):
        h = h @ W + b
        if k < len(weights) - 1:
            h = np.maximum(h, 0.0)
    return sigmoid(h).astype(np.float32)


# ------------------------------------------------------------- evaluation
def spatial_folds(cell_ids, n_cols=2160, grid=6):
    rows, cols = cell_ids // n_cols, cell_ids % n_cols
    lat, lon = 90 - (rows + 0.5) / grid, -180 + (cols + 0.5) / grid
    block = np.floor((lat + 90) / BLOCK_DEG).astype(int) * 1000 + np.floor((lon + 180) / BLOCK_DEG).astype(int)
    blocks = np.unique(block)
    np.random.default_rng(SEED).shuffle(blocks)
    fold_of = {b: i % FOLDS for i, b in enumerate(blocks)}
    return np.array([fold_of[b] for b in block]), block


def auc_per_taxon(Y, P):
    out = []
    for t in range(Y.shape[1]):
        y = Y[:, t]
        out.append(float(roc_auc_score(y, P[:, t])) if 0 < y.sum() < len(y) else float("nan"))
    return np.array(out)


def summary(a):
    a = a[np.isfinite(a)]
    return {"mean_auc": round(float(a.mean()), 3), "median_auc": round(float(np.median(a)), 3),
            "share_above_0_7": round(float((a >= 0.7).mean()), 3), "n_taxa": int(len(a))}


def catalog_rule_scores(X, names, taxon_keys):
    """Score cells with the app's own catalog temperature range for each taxon (baseline)."""
    summary_rows = list(csv.DictReader(open(DATA / "taxa_summary.csv", encoding="utf-8")))
    key_by_name = {r["scientific_name"]: int(r["taxon_key"]) for r in summary_rows if r["taxon_key"]}
    mapping = list(csv.DictReader(open(ML_DIR / "plant_scientific_names.csv", encoding="utf-8")))
    db = sqlite3.connect(ROOT / "hassouna_green.db")
    temps = {pid: (tmin, tmax) for pid, tmin, tmax in db.execute("SELECT id, temp_min_c, temp_max_c FROM plants")}
    db.close()
    range_by_key = {}
    for r in mapping:
        k = key_by_name.get(r["scientific_name"].strip())
        if k is not None and k not in range_by_key:
            range_by_key[k] = temps[int(r["plant_id"])]
    i5, i6 = list(names).index("bio5"), list(names).index("bio6")
    S = np.full((len(X), len(taxon_keys)), np.nan, dtype=np.float32)
    for t, k in enumerate(taxon_keys):
        if k in range_by_key:
            tmin, tmax = range_by_key[k]
            S[:, t] = -(np.maximum(0, X[:, i5] - tmax) + np.maximum(0, tmin - X[:, i6]))
    return S


# ------------------------------------------------------------------- main
def main():
    t0 = time.time()
    d = np.load(DATA / "training_cells.npz")
    X, cell_ids = d["X"], d["cell_ids"]
    T = int(d["n_taxa"])
    Y = np.unpackbits(d["Y"], axis=0)[: len(X), :T].astype(bool)
    all_names, keys, taxon_names = list(d["feature_names"]), d["taxon_keys"], d["taxon_names"]
    X = X[:, [all_names.index(f) for f in MODEL_FEATURES]]
    names = list(MODEL_FEATURES)
    meta = json.loads((DATA / "training_meta.json").read_text())
    print(f"{len(X):,} grid cells, {T} taxa, {Y.sum():,} presence cells")

    spec = make_transform(X, names)
    Z = transform(X, spec)
    fold, block = spatial_folds(cell_ids)

    oof_glm = np.zeros(Y.shape, dtype=np.float32)
    oof_dnn = np.zeros(Y.shape, dtype=np.float32)
    best_epochs = []
    for k in range(FOLDS):
        tr, te = fold != k, fold == k
        # inner validation blocks (for early stopping) taken from the training side only
        tr_blocks = np.unique(block[tr])
        va_blocks = np.random.default_rng(SEED + k).choice(tr_blocks, max(1, len(tr_blocks) // 10), replace=False)
        va = tr & np.isin(block, va_blocks)
        fit = tr & ~va
        W, b = fit_glms(Z[tr], Y[tr], SEED + k)
        oof_glm[te] = glm_predict(Z[te], W, b)
        net, ep = fit_dnn(Z[fit], Y[fit], SEED + k, Z[va], Y[va])
        best_epochs.append(ep)
        oof_dnn[te] = dnn_predict_numpy(Z[te], dnn_weights(net))
        print(f"  fold {k + 1}/{FOLDS}: {te.sum():,} test cells, DNN stopped at epoch {ep} ({time.time() - t0:.0f}s)", flush=True)

    oof_ens = (oof_glm + oof_dnn) / 2
    auc_glm, auc_dnn, auc_ens = auc_per_taxon(Y, oof_glm), auc_per_taxon(Y, oof_dnn), auc_per_taxon(Y, oof_ens)
    R = catalog_rule_scores(X, names, keys)
    has_rule = np.isfinite(R[0])
    auc_rule = np.full(T, np.nan)
    auc_rule[has_rule] = auc_per_taxon(Y[:, has_rule], R[:, has_rule])
    evaluation = {
        "method": f"{FOLDS}-fold spatial block cross-validation ({BLOCK_DEG}x{BLOCK_DEG} degree blocks); "
                  "every cell is scored by models trained without its block",
        "metric": "ROC AUC: presence cells vs target-group background cells (0.5 = random, 1.0 = perfect)",
        "logistic_regression": summary(auc_glm), "deep_neural_network": summary(auc_dnn),
        "ensemble": summary(auc_ens), "catalog_temperature_rule": summary(auc_rule),
        "same_taxa_comparison": {
            "n_taxa": int(has_rule.sum()),
            "ensemble_mean_auc": round(float(np.nanmean(auc_ens[has_rule])), 3),
            "catalog_rule_mean_auc": round(float(np.nanmean(auc_rule[has_rule])), 3),
        },
    }
    print(json.dumps(evaluation, indent=2))

    # Final models on all data.
    W, b = fit_glms(Z, Y, SEED)
    final_epochs = int(np.median(best_epochs))
    net, _ = fit_dnn(Z, Y, SEED, epochs=final_epochs)
    weights = dnn_weights(net)
    with torch.no_grad():
        torch_out = torch.sigmoid(net(torch.from_numpy(Z[:2000]))).numpy()
    assert np.abs(torch_out - dnn_predict_numpy(Z[:2000], weights)).max() < 1e-4, "numpy DNN != torch"

    P_glm, P_dnn = glm_predict(Z, W, b), dnn_predict_numpy(Z, weights)
    P_ens = (P_glm + P_dnn) / 2
    q = {name: np.stack([np.quantile(P[Y[:, t], t], QUANTILES) for t in range(T)]).astype(np.float32)
         for name, P in (("glm", P_glm), ("dnn", P_dnn), ("ens", P_ens))}

    arrays = {
        "model_version": np.array(MODEL_VERSION), "feature_names": np.array(names),
        "log_idx": spec["log_idx"], "mean": spec["mean"], "std": spec["std"],
        "glm_W": W.astype(np.float32), "glm_b": b.astype(np.float32),
        "taxon_keys": keys, "taxon_names": taxon_names, "n_cells": Y.sum(0).astype(np.int32),
        "q_glm": q["glm"], "q_dnn": q["dnn"], "q_ens": q["ens"], "n_layers": np.array(len(weights)),
    }
    for i, (Wl, bl) in enumerate(weights):
        arrays[f"dnn_W{i}"], arrays[f"dnn_b{i}"] = Wl, bl
    np.savez_compressed(ML_DIR / "ml_judge_model.npz", **arrays)

    per_taxon = [{"taxon_key": int(keys[t]), "name": str(taxon_names[t]), "cells": int(Y[:, t].sum()),
                  "auc_logistic_regression": round(float(auc_glm[t]), 3),
                  "auc_deep_neural_network": round(float(auc_dnn[t]), 3),
                  "auc_ensemble": round(float(auc_ens[t]), 3),
                  "auc_catalog_rule": None if not np.isfinite(auc_rule[t]) else round(float(auc_rule[t]), 3)}
                 for t in range(T)]
    card = {
        "model_version": MODEL_VERSION,
        "trained_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "data": meta,
        "features": [f"{n}" for n in names],
        "models": {
            "logistic_regression": f"One L2-regularised logistic regression per taxon on {len(names)} standardised "
                                   "temperature variables and their squares (classic species-distribution GLM), "
                                   "class-balanced.",
            "deep_neural_network": f"Multi-label MLP {len(names)} -> {' -> '.join(map(str, HIDDEN))} -> {T} "
                                   "(ReLU, dropout 0.2), "
                                   f"PyTorch, Adam, class-weighted BCE, {final_epochs} epochs (median early-stopping "
                                   "epoch from cross-validation).",
            "ensemble": "Average of the two models' probabilities.",
            "climate_match": "Percentile of the site's score among the taxon's own known-presence cells; "
                             "below the 10th percentile = outside its known climate range (standard SDM threshold).",
            "plant_score": "0-10th percentile -> 0-60, 10th-50th -> 60-100, 50th+ -> 100: 60 marks the edge of the "
                           "known range, 100 = as typical as the plant's median known location. Design score = "
                           "average over the judged plants.",
        },
        "architecture": {"n_features": len(names), "glm_terms": 2 * len(names),
                         "dnn_hidden": list(HIDDEN), "dnn_outputs": T, "dnn_epochs": final_epochs,
                         "dnn_parameters": int(sum(p.numel() for p in net.parameters()))},
        "evaluation": evaluation,
        "per_taxon": per_taxon,
        "limitations": [
            {"en": "Records show where a plant has been seen growing, wild or planted; a region with no records may "
                   "simply be unrecorded rather than unsuitable.",
             "ar": "السجلات تبيّن أين شوهد النبات ينمو، برياً أو مزروعاً؛ غياب السجلات عن منطقة قد يعني أنها "
                   "لم تُسجَّل، لا أنها غير مناسبة."},
            {"en": "Temperature only: rainfall is left out because irrigation replaces rain in a landscape; soil, "
                   "salinity and water demand are judged by the rule-based score and the ET0 water engine.",
             "ar": "الحرارة فقط: استُبعدت الأمطار لأن الري يحل محلها في تنسيق الحدائق؛ التربة والملوحة واحتياج "
                   "المياه يقيّمها التقييم القاعدي وحساب المياه ET0."},
            {"en": "Some cultivated records may be indoor or greenhouse plants, which can make a plant look more "
                   "cold-tolerant than it is.",
             "ar": "بعض السجلات المزروعة قد تكون لنباتات داخلية أو في صوب، مما قد يُظهر النبات أكثر تحملاً للبرد "
                   "مما هو عليه."},
            {"en": "Climate normals are 1970-2000 at ~18 km resolution; city microclimates are not resolved.",
             "ar": "متوسطات المناخ للفترة 1970-2000 بدقة ~18 كم؛ لا تظهر المناخات المحلية داخل المدن."},
            {"en": "Citizen-science records are densest in Europe and North America; the target-group background "
                   "reduces but does not remove this bias.",
             "ar": "مشاهدات العلم التشاركي أكثف في أوروبا وأمريكا الشمالية؛ أسلوب الخلفية من نفس المجموعة يقلّل "
                   "هذا الانحياز ولا يلغيه."},
            {"en": "The model uses year-round climate, so cool-season bedding plants (e.g. pansy) grown only in "
                   "winter may be judged unfairly.",
             "ar": "يستخدم النموذج مناخ العام كله، لذلك قد تُقيَّم نباتات الأحواض الموسمية التي تُزرع شتاءً فقط "
                   "(مثل البانسيه) بشكل غير منصف."},
            {"en": "Genus-level catalog entries (e.g. Bougainvillea) are modeled at genus level.",
             "ar": "النباتات المسجّلة في الكتالوج على مستوى الجنس (مثل البوغنفيل) تُقيَّم على مستوى الجنس."},
        ],
    }
    (ML_DIR / "ml_judge_card.json").write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved model ({(ML_DIR / 'ml_judge_model.npz').stat().st_size / 1e3:.0f} kB) and card in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
