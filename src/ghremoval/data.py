"""Menyusun tabel pemodelan dari fitur, kohort, dan label."""

from __future__ import annotations

import numpy as np
import polars as pl

from ghremoval.config import Context
from ghremoval.features.behaviour import BEHAVIOUR_COLUMNS, FAMILIES, PROXY_COLUMNS
from ghremoval.features.dense_blocks import BLOCK_COLUMNS
from ghremoval.labels import load_labels

BASE_COLUMNS = ["n_events_coarse", "age_bin12"]
ROBUST_DROP = {"temporal", "repo", "repo_names"}
ROBUST_COLUMNS = [c for family, cols in FAMILIES.items() if family not in ROBUST_DROP for c in cols]
FEATURE_SETS = {
    "B1": ["age_bin12"],
    "B2": BASE_COLUMNS,
    "M_behav": BASE_COLUMNS + BEHAVIOUR_COLUMNS,
    "M_robust": BASE_COLUMNS + ROBUST_COLUMNS,
    "M_proxy": BASE_COLUMNS + BEHAVIOUR_COLUMNS + PROXY_COLUMNS,
    "M_coord": BASE_COLUMNS + BEHAVIOUR_COLUMNS + PROXY_COLUMNS + BLOCK_COLUMNS,
}


def load_frame(ctx: Context, window: int, scopes: list[str], *, first_only: bool = True, with_blocks: bool = False, snapshot: str = "s1") -> pl.DataFrame:
    """Baris akun-jam dengan fitur jendela `window` dan label. Akun status error dibuang."""
    weeks = [week for scope in scopes for week in ctx.weeks_of(scope)]
    labels = pl.concat([load_labels(ctx, scope, snapshot) for scope in scopes]).unique("actor_id")
    hours = pl.read_parquet(ctx.paths.processed / "account_hour.parquet").filter(pl.col("week").is_in(weeks) & ~pl.col("is_app_bot"))
    if first_only:
        hours = hours.filter(pl.col("is_first_in_period"))
    features = pl.read_parquet(ctx.paths.processed / f"features/window={window}/part.parquet").filter(pl.col("hour_id").is_in(hours["hour_id"].unique().implode()))
    frame = hours.join(features, on=["actor_id", "hour_id"], how="inner").join(labels.filter(pl.col("status") != "error").select("actor_id", "is_gone"), on="actor_id", how="inner")
    if with_blocks:
        blocks = pl.read_parquet(ctx.paths.processed / f"dense_blocks/window={window}/part.parquet").select("actor_id", "hour_id", *BLOCK_COLUMNS)
        frame = frame.join(blocks, on=["actor_id", "hour_id"], how="left").with_columns([pl.col(c).fill_null(0.0) for c in BLOCK_COLUMNS])
    return frame.with_columns((pl.col("n_events_w").cast(pl.Float64).log(2).floor()).alias("n_events_coarse"))


def fit_age_edges(recency: np.ndarray, bins: int = 12) -> np.ndarray:
    """Batas kuantil `id_recency`, dihitung hanya dari data latih."""
    return np.quantile(recency, np.linspace(0, 1, bins + 1)[1:-1])


def apply_age_bins(frame: pl.DataFrame, edges: np.ndarray) -> pl.DataFrame:
    return frame.with_columns(pl.Series("age_bin12", np.digitize(frame["id_recency"].to_numpy(), edges).astype(float)))


def cohort_mask(frame: pl.DataFrame, cohort: str, deployable_min: int) -> np.ndarray:
    if cohort == "fixed":
        return frame["in_fixed_cohort"].to_numpy()
    if cohort == "deployable":
        return (frame["n_events_w"] >= deployable_min).to_numpy()
    if cohort == "all":
        return np.ones(frame.height, dtype=bool)
    raise ValueError(cohort)


def xy(frame: pl.DataFrame, feature_set: str) -> tuple[np.ndarray, np.ndarray]:
    return frame.select(FEATURE_SETS[feature_set]).to_numpy().astype(np.float32), frame["is_gone"].to_numpy().astype(int)
