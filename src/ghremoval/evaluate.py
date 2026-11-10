"""Metrik dan bootstrap klaster (docs/06)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

STRATA = ["1", "2-4", "5-19", "20+"]


def safe_ap(y: np.ndarray, score: np.ndarray) -> float:
    return float(average_precision_score(y, score)) if y.sum() > 0 else float("nan")


def tie_broken(score: np.ndarray, seed: int = 0) -> np.ndarray:
    """Pemecah seri deterministik, untuk metrik berbasis peringkat pada skor sama."""
    rng = np.random.default_rng(seed)
    span = max(float(np.ptp(score)), 1.0)
    return score + rng.random(len(score)) * 1e-9 * span


def ap_by_stratum(y: np.ndarray, score: np.ndarray, strata: np.ndarray) -> dict[str, float]:
    out = {"all": safe_ap(y, score)}
    for stratum in STRATA:
        mask = strata == stratum
        if mask.any():
            out[stratum] = safe_ap(y[mask], score[mask])
    return out


def base_rate_by_stratum(y: np.ndarray, strata: np.ndarray) -> dict[str, float]:
    out = {"all": float(y.mean())}
    for stratum in STRATA:
        mask = strata == stratum
        if mask.any():
            out[stratum] = float(y[mask].mean())
    return out


def precision_at_k(y: np.ndarray, score: np.ndarray, k: int, seed: int = 0) -> float:
    return float(y[np.argsort(-tie_broken(score, seed), kind="stable")[:k]].mean())


def recall_at_k(y: np.ndarray, score: np.ndarray, k: int, seed: int = 0) -> float:
    return float(y[np.argsort(-tie_broken(score, seed), kind="stable")[:k]].sum() / max(y.sum(), 1))


def within_cell_auc(y: np.ndarray, score: np.ndarray, cells: np.ndarray) -> float:
    """AUC di dalam sel, dibobot jumlah positif, hanya sel yang memuat positif dan negatif."""
    total = weighted = 0.0
    for cell in np.unique(cells):
        mask = cells == cell
        positives = int(y[mask].sum())
        if 0 < positives < mask.sum():
            weighted += positives * roc_auc_score(y[mask], score[mask])
            total += positives
    return weighted / total if total else float("nan")


def cluster_indices(clusters: np.ndarray) -> list[np.ndarray]:
    order = np.argsort(clusters, kind="stable")
    _, starts = np.unique(clusters[order], return_index=True)
    return np.split(order, starts[1:])


def paired_cluster_bootstrap(metric: Callable[[np.ndarray], float], clusters: np.ndarray, reps: int, seed: int, ci: float = 0.95) -> dict:
    """Bootstrap klaster untuk statistik selisih berpasangan.

    `metric` menerima array indeks baris dan mengembalikan statistik pada sampel ulang itu.
    Klaster disampel ulang dengan pengembalian dan semua akun di dalamnya dipertahankan.
    """
    groups = cluster_indices(clusters)
    rng = np.random.default_rng(seed)
    n = len(groups)
    values = []
    for _ in range(reps):
        picks = rng.integers(0, n, n)
        idx = np.concatenate([groups[i] for i in picks])
        value = metric(idx)
        if not np.isnan(value):
            values.append(value)
    array = np.array(values)
    if array.size == 0:
        return {"low": float("nan"), "high": float("nan"), "p_one_sided": float("nan"), "n_reps": 0}
    alpha = (1 - ci) / 2
    return {"low": float(np.quantile(array, alpha)), "high": float(np.quantile(array, 1 - alpha)), "p_one_sided": float(np.mean(array <= 0)), "n_reps": int(array.size)}


def delta_ap_metric(y: np.ndarray, score_a: np.ndarray, score_b: np.ndarray, mask: np.ndarray) -> Callable[[np.ndarray], float]:
    """Selisih AP(a) − AP(b) pada sampel ulang, dibatasi `mask`."""
    def metric(idx: np.ndarray) -> float:
        kept = idx[mask[idx]]
        if y[kept].sum() == 0:
            return float("nan")
        return average_precision_score(y[kept], score_a[kept]) - average_precision_score(y[kept], score_b[kept])
    return metric


def holm(p_values: dict[str, float]) -> dict[str, float]:
    """Koreksi Holm. Nilai NaN dilewati dan tetap NaN."""
    valid = sorted((p, name) for name, p in p_values.items() if not np.isnan(p))
    m, running, out = len(valid), 0.0, {name: float("nan") for name in p_values}
    for rank, (p, name) in enumerate(valid):
        running = max(running, min((m - rank) * p, 1.0))
        out[name] = running
    return out
