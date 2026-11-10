"""Metode positive-unlabeled untuk RQ3 yang eksploratif (docs/06)."""

from __future__ import annotations

import numpy as np
import xgboost as xgb
from sklearn.linear_model import LogisticRegression

from ghremoval.models.fit import XGB_FIXED_SHALLOW


def _clf(X: np.ndarray, s: np.ndarray, seed: int, sample_weight: np.ndarray | None = None):
    """Classifier pohon dangkal yang sama untuk semua metode PU."""
    model = xgb.XGBClassifier(tree_method="hist", random_state=seed, n_jobs=8, eval_metric="aucpr", **{**XGB_FIXED_SHALLOW, "max_depth": 5})
    return model.fit(X, s, sample_weight=sample_weight, verbose=False)


def naive_fit(X: np.ndarray, s: np.ndarray, seed: int):
    """Model naive: unlabeled dianggap negatif."""
    return _clf(X, s, seed)


def elkan_noto_fit(X: np.ndarray, s: np.ndarray, seed: int, holdout_fraction: float = 0.2) -> tuple:
    """Elkan–Noto: `c` adalah rata-rata skor classifier pada positif yang disisihkan.

    Mengembalikan (model, c). Skor peringkat sama dengan skor model; `c` hanya mengoreksi skala.
    """
    rng = np.random.default_rng(seed)
    held = rng.random(len(s)) < holdout_fraction
    model = _clf(X[~held], s[~held], seed)
    positives = held & (s == 1)
    c = float(np.mean(model.predict_proba(X[positives])[:, 1])) if positives.any() else float("nan")
    return model, c


def pu_bagging_fit(X: np.ndarray, s: np.ndarray, seed: int, n_bags: int = 15) -> list:
    """PU bagging: positif melawan sampel acak unlabeled sebesar positif."""
    rng = np.random.default_rng(seed)
    positives, unlabeled = np.flatnonzero(s == 1), np.flatnonzero(s == 0)
    models = []
    for bag in range(n_bags):
        chosen = rng.choice(unlabeled, size=min(len(positives), len(unlabeled)), replace=False)
        index = np.concatenate([positives, chosen])
        models.append(_clf(X[index], s[index], seed + bag))
    return models


def bagging_score(models: list, X: np.ndarray) -> np.ndarray:
    return np.mean([m.predict_proba(X)[:, 1] for m in models], axis=0)


def sar_em_fit(X: np.ndarray, s: np.ndarray, propensity_features: np.ndarray, seed: int, iterations: int = 5) -> tuple:
    """SAR-EM sederhana mengikuti Bekker et al.: bergantian memperkirakan classifier dan propensity."""
    clf = _clf(X, s, seed)
    expected = np.where(s == 1, 1.0, np.clip(clf.predict_proba(X)[:, 1], 1e-3, 0.99))
    propensity = LogisticRegression(max_iter=1000)
    for _ in range(iterations):
        propensity.fit(propensity_features, s, sample_weight=expected + 1e-6)
        e = np.clip(propensity.predict_proba(propensity_features)[:, 1], 1e-3, 1.0)
        data = np.vstack([X, X])
        target = np.concatenate([np.ones(len(s)), np.zeros(len(s))])
        clf = _clf(data, target.astype(int), seed, sample_weight=np.concatenate([expected, 1 - expected]) + 1e-6)
        f = np.clip(clf.predict_proba(X)[:, 1], 1e-4, 0.9999)
        expected = np.where(s == 1, 1.0, np.clip(f * (1 - e) / (1 - f * e), 1e-4, 1.0))
    return clf, propensity


def hide_positives(s: np.ndarray, propensity_features: np.ndarray, target_hidden: float, seed: int) -> np.ndarray:
    """Mask positif yang disembunyikan. Peluang disembunyikan naik dengan atribut propensity, rata-rata `target_hidden`."""
    rng = np.random.default_rng(seed)
    features = propensity_features - propensity_features.mean(axis=0)
    span = np.abs(features).max(axis=0) + 1e-9
    logits = (features / span).sum(axis=1)
    low, high = -20.0, 20.0
    for _ in range(60):
        shift = (low + high) / 2
        hidden_rate = np.mean(1 / (1 + np.exp(-(logits[s == 1] + shift))))
        if hidden_rate > target_hidden:
            high = shift
        else:
            low = shift
    probability = 1 / (1 + np.exp(-(logits + (low + high) / 2)))
    return (s == 1) & (rng.random(len(s)) < probability)
