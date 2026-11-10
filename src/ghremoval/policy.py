"""Kebijakan penandaan dini adaptif (docs/06, K6)."""

from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

NOT_FLAGGED = np.inf


class Calibrator:
    """Isotonic bila positif cukup, Platt bila tidak."""

    def __init__(self, scores: np.ndarray, y: np.ndarray, min_positives: int = 30) -> None:
        self.kind = "isotonic" if y.sum() >= min_positives else "platt"
        if self.kind == "isotonic":
            self.model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(scores, y)
        else:
            self.model = LogisticRegression().fit(scores.reshape(-1, 1), y)

    def __call__(self, scores: np.ndarray) -> np.ndarray:
        return self.model.predict(scores) if self.kind == "isotonic" else self.model.predict_proba(scores.reshape(-1, 1))[:, 1]


def thresholds(q: float, kappa: float, checkpoints: list[int]) -> dict[int, float]:
    return {c: min(1.0, q * (1 + kappa * (60 - c) / 60)) for c in checkpoints}


def first_cross(prob: dict[int, np.ndarray], limits: dict[int, float]) -> np.ndarray:
    """Waktu penandaan tiap akun: checkpoint pertama yang melewati ambang. NaN pada `prob` berarti akun belum memenuhi syarat."""
    checkpoints = sorted(prob)
    n = len(prob[checkpoints[0]])
    times = np.full(n, NOT_FLAGGED)
    for c in checkpoints:
        crossed = np.isfinite(prob[c]) & (prob[c] >= limits[c]) & ~np.isfinite(times)
        times[crossed] = c
    return times


def aurt(times: np.ndarray, y: np.ndarray, horizon: float) -> float:
    """Area di bawah kurva recall terhadap waktu, dinormalisasi horizon."""
    positives = int(y.sum())
    if positives == 0:
        return float("nan")
    flagged = times[(y == 1) & np.isfinite(times)]
    return float(np.sum(horizon - flagged) / (horizon * positives))


def policy_metrics(times: np.ndarray, y: np.ndarray, horizon: float) -> dict:
    flagged = np.isfinite(times)
    tp = (y == 1) & flagged
    return {"n_flagged": int(flagged.sum()), "precision": float(y[flagged].mean()) if flagged.any() else float("nan"), "recall": float(tp.sum() / max(y.sum(), 1)), "aurt": aurt(times, y, horizon),
            "median_time_tp": float(np.median(times[tp])) if tp.any() else float("nan")}


def q_grid(size: int) -> np.ndarray:
    return np.linspace(0.005, 0.995, size)


def select_q_kappa(prob: dict[int, np.ndarray], y: np.ndarray, target: float, kappas: list[float], grid: np.ndarray, horizon: float) -> dict | None:
    """Untuk tiap κ, cari q terkecil yang mencapai target precision seluruh kebijakan, lalu pilih AURT tertinggi."""
    checkpoints, best = sorted(prob), None
    for kappa in kappas:
        for q in grid:
            metrics = policy_metrics(first_cross(prob, thresholds(float(q), kappa, checkpoints)), y, horizon)
            if metrics["n_flagged"] and metrics["precision"] >= target:
                if best is None or metrics["aurt"] > best["aurt"]:
                    best = {"q": float(q), "kappa": kappa, **metrics}
                break
    return best


def select_fixed(prob: np.ndarray, y: np.ndarray, target: float, grid: np.ndarray) -> float | None:
    """q terkecil yang mencapai target precision pada satu checkpoint."""
    for q in grid:
        flagged = np.isfinite(prob) & (prob >= q)
        if flagged.any() and y[flagged].mean() >= target:
            return float(q)
    return None


def fixed_times(prob: np.ndarray, q: float | None, checkpoint: int) -> np.ndarray:
    times = np.full(len(prob), NOT_FLAGGED)
    if q is not None:
        times[np.isfinite(prob) & (prob >= q)] = checkpoint
    return times


def amoc_curve(prob: dict[int, np.ndarray], y: np.ndarray, kappa: float, grid: np.ndarray, horizon: float) -> list[dict]:
    """Rata-rata waktu penandaan pada positif terhadap false positive rate, untuk tiap q."""
    checkpoints, negatives, out = sorted(prob), max(int((y == 0).sum()), 1), []
    for q in grid:
        times = first_cross(prob, thresholds(float(q), kappa, checkpoints))
        delays = np.where(np.isfinite(times), times, horizon)[y == 1]
        out.append({"q": float(q), "false_positive_rate": float(np.isfinite(times[y == 0]).sum() / negatives), "mean_delay_positive": float(delays.mean()) if delays.size else float("nan")})
    return out
