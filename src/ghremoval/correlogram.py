"""Korelogram residual terhadap jarak ID dan pemilihan lebar blok (docs/06)."""

from __future__ import annotations

import numpy as np


def residual_correlogram(ids: np.ndarray, residuals: np.ndarray, *, max_pairs_per_bin: int = 300_000, seed: int = 0, edges: np.ndarray | None = None) -> list[dict]:
    """Korelasi residual pasangan akun yang berjarak ID dalam bin log.

    Pasangan diambil dengan offset peringkat pada ID terurut, supaya jarak pendek terwakili.
    """
    order = np.argsort(ids)
    x, r = ids[order].astype(float), residuals[order] - residuals.mean()
    bins = edges if edges is not None else np.logspace(2, 8, 25)
    rng = np.random.default_rng(seed)
    variance = float(np.mean(r**2))
    pairs_a, pairs_b = [], []
    n = len(x)
    for offset in np.unique(np.logspace(0, np.log10(max(n - 1, 2)), 400).astype(int)):
        take = min(n - offset, 20_000)
        start = rng.choice(n - offset, take, replace=False) if take < n - offset else np.arange(n - offset)
        pairs_a.append(start)
        pairs_b.append(start + offset)
    a, b = np.concatenate(pairs_a), np.concatenate(pairs_b)
    distance = x[b] - x[a]
    out = []
    for low, high in zip(bins[:-1], bins[1:]):
        mask = (distance >= low) & (distance < high)
        count = int(mask.sum())
        if count < 50:
            continue
        chosen = np.flatnonzero(mask)
        if count > max_pairs_per_bin:
            chosen = rng.choice(chosen, max_pairs_per_bin, replace=False)
        out.append({"low": float(low), "high": float(high), "mid": float(np.sqrt(low * high)), "n_pairs": count, "corr": float(np.mean(r[a[chosen]] * r[b[chosen]]) / variance)})
    return out


def autocorrelation_range(correlogram: list[dict], threshold: float = 0.05) -> float:
    """Batas bawah bin pertama yang korelasinya di bawah ambang. Tak terhingga bila tidak ada."""
    for row in correlogram:
        if row["corr"] < threshold:
            return row["low"]
    return float("inf")


def choose_block_width(widths: list[int], autocorr_range: float) -> int:
    """Lebar terkecil yang tidak lebih pendek dari jarak autokorelasi; jika tidak ada, lebar terbesar."""
    for width in sorted(widths):
        if autocorr_range <= width:
            return width
    return max(widths)
