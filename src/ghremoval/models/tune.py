"""Tuning Optuna TPE dengan penyimpanan SQLite (docs/06)."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import optuna

from ghremoval.evaluate import safe_ap
from ghremoval.models.fit import fit_family, predict


def suggest(trial: optuna.Trial, family: str) -> dict:
    if family == "lr":
        return {"C": trial.suggest_float("C", 1e-3, 10.0, log=True)}
    if family == "xgb":
        return {"max_depth": trial.suggest_int("max_depth", 3, 8), "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True), "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 20.0, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0), "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0), "reg_lambda": trial.suggest_float("reg_lambda", 0.1, 10.0, log=True)}
    if family == "mlp":
        return {"hidden": trial.suggest_categorical("hidden", [64, 128, 256, 512]), "dropout": trial.suggest_float("dropout", 0.0, 0.5), "lr": trial.suggest_float("lr", 1e-4, 3e-3, log=True),
                "weight_decay": trial.suggest_float("weight_decay", 1e-6, 1e-2, log=True), "batch": trial.suggest_categorical("batch", [256, 512])}
    raise ValueError(family)


def run_study(family: str, sampler_seed: int, X: np.ndarray, y: np.ndarray, es_mask: np.ndarray, X_val: np.ndarray, y_val: np.ndarray, val_mask: np.ndarray, storage_dir: Path, n_trials: int) -> dict:
    """Memaksimalkan AP pada `val_mask` (stratum 5–19 lengan F2). Hasil trial tersimpan di SQLite."""
    storage_dir.mkdir(parents=True, exist_ok=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=sampler_seed, n_startup_trials=8), storage=f"sqlite:///{storage_dir}/{family}.sqlite3",
                                study_name=f"{family}_{sampler_seed}", load_if_exists=True)
    remaining = n_trials - len(study.trials)

    def objective(trial: optuna.Trial) -> float:
        params = suggest(trial, family)
        started = time.time()
        model = fit_family(family, params, X, y, es_mask, 42)
        value = safe_ap(y_val[val_mask], predict(model, X_val[val_mask]))
        trial.set_user_attr("seconds", time.time() - started)
        return value

    if remaining > 0:
        study.optimize(objective, n_trials=remaining)
    return {"family": family, "sampler_seed": sampler_seed, "best_value": study.best_value, "best_params": study.best_params, "n_trials": len(study.trials), "seconds": sum(t.user_attrs.get("seconds", 0.0) for t in study.trials)}
