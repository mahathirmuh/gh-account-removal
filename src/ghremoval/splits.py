"""Grup validasi silang, diagnostik, dan himpunan forward (docs/06)."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.model_selection import StratifiedGroupKFold


def id_block_groups(ids: np.ndarray, width: int) -> np.ndarray:
    """Blok ID lebar tetap. Sengaja tanpa perantaian."""
    return (ids // width).astype(np.int64)


def signature_groups(n_events: np.ndarray, n_repos: np.ndarray, n_minutes: np.ndarray, min_events: int) -> np.ndarray:
    """Akun dengan signature aktivitas identik berada dalam satu grup; akun di bawah ambang tunggal."""
    n = len(n_events)
    keys = np.char.add(np.char.add(n_events.astype(int).astype(str), "_"), np.char.add(np.char.add(n_repos.astype(int).astype(str), "_"), n_minutes.astype(int).astype(str)))
    unique, inverse = np.unique(keys, return_inverse=True)
    singles = n_events < min_events
    out = inverse.astype(np.int64)
    out[singles] = len(unique) + np.arange(singles.sum())
    if n == 0:
        return out
    return out


def artifact_groups(n_accounts: int, links: list[np.ndarray]) -> np.ndarray:
    """Komponen terhubung dari akun yang berbagi artefak. `links` berisi array indeks akun per artefak."""
    rows, cols = [], []
    for members in links:
        rows.append(members[:-1])
        cols.append(members[1:])
    if not rows:
        return np.arange(n_accounts)
    r, c = np.concatenate(rows), np.concatenate(cols)
    return connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n_accounts, n_accounts)), directed=False)[1]


def artifact_links(frame: pl.DataFrame, interim_events: pl.LazyFrame, interim_commits: pl.LazyFrame, max_accounts: int) -> list[np.ndarray]:
    """Akun dalam `frame` yang berbagi repo atau pesan commit pada jam yang sama, untuk artefak yang dipakai 2 sampai `max_accounts` akun.

    Tautan dibatasi per jam supaya komponen tidak merantai antarjam menjadi satu grup raksasa.
    """
    index = pl.DataFrame({"actor_id": frame["actor_id"], "hour_id": frame["hour_id"], "idx": np.arange(frame.height)}).lazy()
    links: list[np.ndarray] = []
    for source, key in ((interim_events.select("actor_id", "hour_id", "repo_id"), "repo_id"), (interim_commits.select("actor_id", "hour_id", "msg_hash"), "msg_hash")):
        grouped = (source.join(index, on=["actor_id", "hour_id"], how="inner").select("hour_id", key, "idx").unique().group_by("hour_id", key).agg(pl.col("idx"), pl.len().alias("size")).filter(pl.col("size").is_between(2, max_accounts)).collect())
        links += [np.array(members, dtype=np.int64) for members in grouped["idx"].to_list()]
    return links


def stratified_group_folds(groups: np.ndarray, y: np.ndarray, n_folds: int, seed: int) -> np.ndarray:
    folds = np.zeros(len(y), dtype=np.int32)
    for fold, (_, test) in enumerate(StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed).split(np.zeros(len(y)), y, groups)):
        folds[test] = fold
    return folds


def diagnose(groups: np.ndarray, y: np.ndarray, folds: np.ndarray | None, max_share: float) -> dict:
    """Ukuran grup dan porsi positif. Lengan degeneratif bila satu grup memuat terlalu banyak positif."""
    _, inverse = np.unique(groups, return_inverse=True)
    sizes, positives = np.bincount(inverse), np.bincount(inverse, weights=y)
    largest = int(np.argmax(sizes))
    total = max(float(y.sum()), 1.0)
    fold_share = float(np.bincount(folds, weights=y).max() / total) if folds is not None else float("nan")
    worst_positive_group = float(positives.max() / total)
    return {"n_groups": int(len(sizes)), "largest_group": int(sizes[largest]), "largest_group_pos_share": float(positives[largest] / total), "max_group_pos_share": worst_positive_group,
            "max_fold_pos_share": fold_share, "groups_with_pos": int((positives > 0).sum()), "is_degenerate": worst_positive_group > max_share}


def batch_excluded_ids(test_ids: np.ndarray, train_ids: np.ndarray, train_y: np.ndarray, width: int, mode: str = "train_positive_block") -> np.ndarray:
    """Mask akun test yang berada di blok ID train terlarang."""
    source = train_ids[train_y == 1] if mode == "train_positive_block" else train_ids
    return np.isin(test_ids // width, np.unique(source // width))


def forward_arm(train: pl.DataFrame, test: pl.DataFrame, arm: str, width: int | None, mode: str = "train_positive_block") -> np.ndarray:
    """Mask baris `test` untuk lengan forward. F1 semua, F2 akun baru, F3 akun baru tanpa blok positif train."""
    mask = np.ones(test.height, dtype=bool)
    if arm == "F1_forward":
        return mask
    mask &= ~np.isin(test["actor_id"].to_numpy(), train["actor_id"].to_numpy())
    if arm == "F2_forward_new_accounts":
        return mask
    if arm == "F3_forward_batch_excluded":
        return mask & ~batch_excluded_ids(test["actor_id"].to_numpy(), train["actor_id"].to_numpy(), train["is_gone"].to_numpy().astype(int), width, mode)
    raise ValueError(arm)
