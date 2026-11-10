"""Pelatihan model dan himpunan waktu (docs/06)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import polars as pl
import torch
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn

from ghremoval.config import Context
from ghremoval.data import BASE_COLUMNS, FEATURE_SETS, apply_age_bins, fit_age_edges, load_frame, xy
from ghremoval.splits import forward_arm

XGB_FIXED_SHALLOW = {"n_estimators": 300, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.9, "colsample_bytree": 0.9, "min_child_weight": 5.0, "reg_lambda": 1.0}


@dataclass
class StageData:
    train: pl.DataFrame
    test: pl.DataFrame  # kemunculan pertama pada himpunan test
    f1: pl.DataFrame  # semua kemunculan pada himpunan test, untuk lengan F1


def load_stage(ctx: Context, stage: str, window: int, *, with_blocks: bool = False, cohort: str = "fixed") -> StageData:
    """Tahap `dev` melatih pada w0–w1 dan menguji w2; tahap `final` melatih pada w0–w2 dan menguji w3."""
    deployable = ctx.p.locked["cohorts"]["deployable_min_events"]

    def restrict(frame: pl.DataFrame) -> pl.DataFrame:
        if cohort == "fixed":
            return frame.filter(pl.col("in_fixed_cohort"))
        return frame.filter(pl.col("n_events_w") >= deployable)

    if stage == "dev":
        pool = load_frame(ctx, window, ["train", "val"], with_blocks=with_blocks)
        weeks_train, weeks_test = ctx.weeks_of("train"), ctx.weeks_of("val")
        train, test = pool.filter(pl.col("week").is_in(weeks_train)), pool.filter(pl.col("week").is_in(weeks_test))
        f1 = load_frame(ctx, window, ["val"], first_only=False, with_blocks=with_blocks)
    elif stage == "final":
        train = load_frame(ctx, window, ["train", "val"], with_blocks=with_blocks)
        test = load_frame(ctx, window, ["holdout"], with_blocks=with_blocks)
        f1 = load_frame(ctx, window, ["holdout"], first_only=False, with_blocks=with_blocks)
    else:
        raise ValueError(stage)
    train, test, f1 = restrict(train), restrict(test), restrict(f1)
    edges = fit_age_edges(train["id_recency"].to_numpy(), ctx.p.locked["features"]["age_bins"])
    return StageData(apply_age_bins(train, edges), apply_age_bins(test, edges), apply_age_bins(f1, edges))


def time_holdback(frame: pl.DataFrame, order: dict[str, int], fraction: float = 0.2) -> np.ndarray:
    """Mask baris pada 20% jam terakhir, untuk early stopping. Tidak pernah memakai data test."""
    hours = sorted(frame["hour_id"].unique().to_list(), key=lambda h: order[h])
    tail = set(hours[-max(1, math.ceil(len(hours) * fraction)):])
    return frame["hour_id"].is_in(list(tail)).to_numpy()


def fit_xgb(params: dict, X: np.ndarray, y: np.ndarray, es_mask: np.ndarray | None, seed: int, *, n_jobs: int = 8):
    """XGBoost CPU. Early stopping memakai 20% jam terakhir bila `es_mask` diberikan."""
    args = dict(params)
    args.setdefault("n_estimators", 2000)
    if es_mask is None:
        return xgb.XGBClassifier(tree_method="hist", random_state=seed, n_jobs=n_jobs, eval_metric="aucpr", **args).fit(X, y, verbose=False)
    model = xgb.XGBClassifier(tree_method="hist", random_state=seed, n_jobs=n_jobs, eval_metric="aucpr", early_stopping_rounds=50, **args)
    return model.fit(X[~es_mask], y[~es_mask], eval_set=[(X[es_mask], y[es_mask])], verbose=False)


def fit_lr(params: dict, X: np.ndarray, y: np.ndarray, seed: int):
    """Regresi logistik pada transformasi log, tanpa menyentuh data test."""
    transformer = make_pipeline(StandardScaler(), LogisticRegression(C=params.get("C", 1.0), max_iter=4000, random_state=seed))
    return transformer.fit(np.sign(X) * np.log1p(np.abs(X)), y)


def predict(model, X: np.ndarray) -> np.ndarray:
    if hasattr(model, "predict_mlp"):
        return model.predict_mlp(X)
    data = X
    if hasattr(model, "steps"):
        data = np.sign(X) * np.log1p(np.abs(X))
    return model.predict_proba(data)[:, 1]


class _Net(nn.Module):
    def __init__(self, n_inputs: int, hidden: int, dropout: float) -> None:
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(n_inputs, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1))

    def forward(self, batch):
        return self.layers(batch).squeeze(-1)


class MlpModel:
    """MLP one-hot: dua kolom dasar di-one-hot, kolom lain dibakukan dari data latih."""

    def __init__(self, net: nn.Module, mean: np.ndarray, std: np.ndarray, levels: list[np.ndarray], n_cat: int, device: str) -> None:
        self.net, self.mean, self.std, self.levels, self.n_cat, self.device = net, mean, std, levels, n_cat, device

    def transform(self, X: np.ndarray) -> np.ndarray:
        cat = [np.column_stack([(X[:, j] == level).astype(np.float32) for level in values]) for j, values in enumerate(self.levels)]
        return np.column_stack([*cat, ((X[:, self.n_cat:] - self.mean) / self.std).astype(np.float32)])

    def predict_mlp(self, X: np.ndarray) -> np.ndarray:
        self.net.eval()
        out = []
        with torch.no_grad():
            for start in range(0, len(X), 65536):
                batch = torch.from_numpy(self.transform(X[start:start + 65536])).to(self.device)
                out.append(torch.sigmoid(self.net(batch)).cpu().numpy())
        return np.concatenate(out)


def fit_mlp(params: dict, X: np.ndarray, y: np.ndarray, es_mask: np.ndarray, seed: int, *, patience: int = 10, max_epochs: int = 80) -> MlpModel:
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    n_cat = len(BASE_COLUMNS)
    tr, es = ~es_mask, es_mask
    numeric = X[tr, n_cat:]
    mean, std = numeric.mean(axis=0), numeric.std(axis=0) + 1e-6
    levels = [np.unique(X[tr, j]) for j in range(n_cat)]
    model = MlpModel(None, mean, std, levels, n_cat, device)
    train_x, es_x = model.transform(X[tr]), model.transform(X[es])
    net = _Net(train_x.shape[1], int(params["hidden"]), float(params["dropout"])).to(device)
    optimizer = torch.optim.AdamW(net.parameters(), lr=float(params["lr"]), weight_decay=float(params["weight_decay"]))
    loss_fn = nn.BCEWithLogitsLoss()
    train_tensor, train_y = torch.from_numpy(train_x).to(device), torch.from_numpy(y[tr].astype(np.float32)).to(device)
    es_tensor, es_y = torch.from_numpy(es_x).to(device), torch.from_numpy(y[es].astype(np.float32)).to(device)
    batch_size, best, best_state, waited = int(params["batch"]), float("inf"), None, 0
    rng = np.random.default_rng(seed)
    for _ in range(max_epochs):
        net.train()
        for start in range(0, len(train_tensor), batch_size):
            indices = rng.permutation(len(train_tensor))[start:start + batch_size]
            optimizer.zero_grad()
            loss_fn(net(train_tensor[indices]), train_y[indices]).backward()
            optimizer.step()
        net.eval()
        with torch.no_grad():
            value = float(loss_fn(net(es_tensor), es_y))
        if value < best - 1e-5:
            best, best_state, waited = value, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}, 0
        else:
            waited += 1
            if waited >= patience:
                break
    net.load_state_dict(best_state)
    model.net = net
    return model


def fit_family(family: str, params: dict, X: np.ndarray, y: np.ndarray, es_mask: np.ndarray, seed: int):
    if family == "xgb":
        return fit_xgb(params, X, y, es_mask, seed)
    if family == "lr":
        return fit_lr(params, X, y, seed)
    if family == "mlp":
        return fit_mlp(params, X, y, es_mask, seed)
    raise ValueError(family)


def fit_predict(family: str, params: dict, feature_set: str, train: pl.DataFrame, tests: list[pl.DataFrame], order: dict[str, int], seeds: list[int]) -> list[np.ndarray]:
    """Latih pada `train` untuk beberapa seed, kembalikan rata-rata skor tiap frame test."""
    X, y = xy(train, feature_set)
    es = time_holdback(train, order)
    scores = [np.zeros(frame.height) for frame in tests]
    for seed in seeds:
        model = fit_family(family, params, X, y, es, seed)
        for k, frame in enumerate(tests):
            scores[k] += predict(model, xy(frame, feature_set)[0]) / len(seeds)
    return scores


def arm_mask(train: pl.DataFrame, test: pl.DataFrame, arm: str, ctx: Context) -> np.ndarray:
    return forward_arm(train, test, arm, ctx.p.derived.get("primary_id_block_width"), ctx.p.locked["splits"]["batch_exclusion"])


__all__ = ["FEATURE_SETS", "StageData", "XGB_FIXED_SHALLOW", "arm_mask", "fit_family", "fit_lr", "fit_mlp", "fit_predict", "fit_xgb", "load_stage", "predict", "time_holdback"]
