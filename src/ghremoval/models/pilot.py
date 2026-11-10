"""Konfigurasi gradient boosting pilot, dipakai untuk replikasi dan audit split (docs/07)."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier


def pilot_model(seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=7, l2_regularization=5.0, min_samples_leaf=30, early_stopping=False, random_state=seed)


def oof_scores(X: np.ndarray, y: np.ndarray, folds_by_seed: dict[int, np.ndarray]) -> np.ndarray:
    """Rata-rata skor out-of-fold atas beberapa seed lipatan."""
    runs = []
    for seed, folds in folds_by_seed.items():
        score = np.zeros(len(y))
        for fold in np.unique(folds):
            test = folds == fold
            score[test] = pilot_model(seed).fit(X[~test], y[~test]).predict_proba(X[test])[:, 1]
        runs.append(score)
    return np.mean(runs, axis=0)
