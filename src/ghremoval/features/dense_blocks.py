"""Fitur dense-block lintas jenis event (docs/05). Tidak memakai label.

Blok ditemukan dengan greedy peeling bergaya M-Zoom (Shin et al.), diimplementasikan di sini:
pada tiap langkah, nilai atribut dengan massa slice terkecil dibuang, lalu dipilih kondisi dengan
densitas aritmetika tertinggi. Tuple blok yang ditemukan dikeluarkan sebelum mencari blok berikutnya.
"""

from __future__ import annotations

import heapq
import math
from pathlib import Path

import numpy as np
import polars as pl

MODES = ("actor_id", "repo_id", "event_type", "minute")
BLOCK_COLUMNS = ["in_any_block", "best_block_rank", "best_block_density", "best_block_n_accounts", "best_block_n_repos", "share_events_in_blocks", "n_blocks", "n_event_types_in_best_block"]
TENSOR_SCHEMA = {"actor_id": pl.Int64, "repo_id": pl.Int64, "event_type": pl.String, "minute": pl.Int32, "count": pl.Int64}


def build_tensor(events: pl.DataFrame, window_min: int) -> pl.DataFrame:
    """Tensor akun × repo × jenis event × menit, hanya dari event non-bot sebelum cutoff."""
    cutoff = 60 * window_min
    ev = events.filter((pl.col("second_of_hour") < cutoff) & ~pl.col("is_app_bot"))
    return ev.with_columns((pl.col("second_of_hour") // 60).cast(pl.Int32).alias("minute")).group_by(["actor_id", "repo_id", "event_type", "minute"]).agg(pl.len().cast(pl.Int64).alias("count"))


def _density(total: float, cardinality: list[int], measure: str) -> float:
    """Densitas blok: massa dibagi rata-rata aritmetika atau geometrik kardinalitas mode."""
    if measure == "arithmetic":
        return total / (sum(cardinality) / len(cardinality))
    if measure == "geometric":
        return total / math.exp(sum(math.log(c) for c in cardinality) / len(cardinality))
    raise ValueError(measure)


def _peel_once(attrs: list[tuple[int, ...]], counts: list[int], n_attrs: int, attr_mode: list[int], n_modes: int, measure: str) -> tuple[list[int], float]:
    """Satu putaran peeling. Mengembalikan indeks tuple pada kondisi dengan densitas tertinggi."""
    n_tuples = len(attrs)
    mass = [0] * n_attrs
    incident: list[list[int]] = [[] for _ in range(n_attrs)]
    for index, row in enumerate(attrs):
        weight = counts[index]
        for attr in row:
            mass[attr] += weight
            incident[attr].append(index)
    active = [bool(incident[a]) for a in range(n_attrs)]
    cardinality = [0] * n_modes
    for attr in range(n_attrs):
        if active[attr]:
            cardinality[attr_mode[attr]] += 1
    remaining_attrs = sum(cardinality)
    total = sum(counts)
    best_density, best_step, step = _density(total, cardinality, measure), 0, 0
    heap = [(mass[a], a) for a in range(n_attrs) if active[a]]
    heapq.heapify(heap)
    alive = bytearray(b"\x01") * n_tuples
    removed_at = [0] * n_tuples
    while heap:
        current, attr = heapq.heappop(heap)
        if not active[attr] or current != mass[attr]:
            continue
        active[attr] = False
        step += 1
        cardinality[attr_mode[attr]] -= 1
        remaining_attrs -= 1
        for index in incident[attr]:
            if alive[index]:
                alive[index] = 0
                removed_at[index] = step
                weight = counts[index]
                total -= weight
                for other in attrs[index]:
                    if other != attr and active[other]:
                        mass[other] -= weight
                        heapq.heappush(heap, (mass[other], other))
        if remaining_attrs > 0 and all(cardinality):
            density = _density(total, cardinality, measure)
            if density > best_density:
                best_density, best_step = density, step
    return [i for i in range(n_tuples) if removed_at[i] == 0 or removed_at[i] > best_step], best_density


def peel_blocks(tensor: pl.DataFrame, k: int, measure: str = "arithmetic") -> list[pl.DataFrame]:
    """Menemukan hingga `k` blok padat, tiap blok berbentuk tuple seperti tensor masukan."""
    if tensor.height == 0:
        return []
    table = tensor.select(*MODES, "count")
    encoded, attr_mode, offset = [], [], 0
    for mode_index, column in enumerate(MODES):
        _, inverse = np.unique(table[column].to_numpy(), return_inverse=True)
        cardinal = int(inverse.max()) + 1
        encoded.append(inverse + offset)
        attr_mode += [mode_index] * cardinal
        offset += cardinal
    all_attrs = np.column_stack(encoded)
    all_counts = table["count"].to_numpy()
    remaining = np.arange(table.height)
    blocks = []
    for _ in range(k):
        if remaining.size == 0:
            break
        picked, _density = _peel_once([tuple(row) for row in all_attrs[remaining].tolist()], all_counts[remaining].tolist(), offset, attr_mode, len(MODES), measure)
        chosen = remaining[np.array(picked, dtype=np.int64)]
        if chosen.size == 0:
            break
        blocks.append(table[chosen])
        keep = np.ones(remaining.size, dtype=bool)
        keep[np.array(picked, dtype=np.int64)] = False
        remaining = remaining[keep]
    return blocks


def block_density(block: pl.DataFrame, measure: str = "arithmetic") -> float:
    """Densitas blok yang ditemukan, memakai ukuran yang sama dengan pencarian."""
    return _density(float(block["count"].sum()), [block[c].n_unique() for c in MODES], measure)


def block_features(blocks: list[pl.DataFrame], tensor: pl.DataFrame, top_k: int, measure: str = "arithmetic") -> pl.DataFrame:
    """Fitur per akun dari blok yang ditemukan. Akun di luar blok memakai nilai dasar."""
    totals = tensor.group_by("actor_id").agg(pl.col("count").sum().alias("total"))
    rows = []
    for rank, block in enumerate(blocks, start=1):
        density, n_accounts, n_repos = block_density(block, measure), block["actor_id"].n_unique(), block["repo_id"].n_unique()
        per_account = block.group_by("actor_id").agg(pl.col("count").sum().alias("mass"), pl.col("event_type").n_unique().alias("n_types"))
        rows.append(per_account.with_columns(pl.lit(rank).alias("rank"), pl.lit(density).alias("density"), pl.lit(n_accounts).alias("n_accounts"), pl.lit(n_repos).alias("n_repos")))
    baseline = totals.select("actor_id")
    empty = {"in_any_block": 0.0, "best_block_rank": float(top_k + 1), "best_block_density": 0.0, "best_block_n_accounts": 0.0, "best_block_n_repos": 0.0, "share_events_in_blocks": 0.0, "n_blocks": 0.0, "n_event_types_in_best_block": 0.0}
    if not rows:
        return baseline.with_columns([pl.lit(v).alias(key) for key, v in empty.items()])
    long = pl.concat(rows)
    best = long.sort("rank").group_by("actor_id", maintain_order=True).first().select("actor_id", pl.col("rank").cast(pl.Float64).alias("best_block_rank"), pl.col("density").alias("best_block_density"),
                                                                                    pl.col("n_accounts").cast(pl.Float64).alias("best_block_n_accounts"), pl.col("n_repos").cast(pl.Float64).alias("best_block_n_repos"), pl.col("n_types").cast(pl.Float64).alias("n_event_types_in_best_block"))
    summed = long.group_by("actor_id").agg(pl.col("mass").sum().alias("mass"), pl.len().cast(pl.Float64).alias("n_blocks"))
    out = baseline.join(best, on="actor_id", how="left").join(summed, on="actor_id", how="left").join(totals, on="actor_id", how="left")
    out = out.with_columns(pl.col("mass").is_not_null().cast(pl.Float64).alias("in_any_block"), (pl.col("mass").fill_null(0) / pl.col("total")).alias("share_events_in_blocks"))
    fills = {key: v for key, v in empty.items() if key not in ("in_any_block", "share_events_in_blocks")}
    return out.with_columns([pl.col(key).fill_null(v) for key, v in fills.items()]).select("actor_id", *BLOCK_COLUMNS)


def mine_hour(interim: Path, processed: Path, hour_id: str, windows: list[int], k: int, measure: str) -> dict:
    """Mining blok untuk satu jam dan semua jendela, lalu menulis fitur per akun."""
    events = pl.read_parquet(interim / f"events/hour_id={hour_id}/part.parquet", columns=["actor_id", "is_app_bot", "second_of_hour", "event_type", "repo_id"])
    stats: dict = {"hour_id": hour_id}
    for w in windows:
        tensor = build_tensor(events, w)
        blocks = peel_blocks(tensor, k, measure)
        max_minute = max((int(b["minute"].max()) for b in blocks), default=0)
        if max_minute >= w:
            raise AssertionError(f"Blok memuat menit {max_minute} pada jendela {w}")
        features = block_features(blocks, tensor, k, measure).with_columns(pl.lit(hour_id).alias("hour_id"), pl.lit(w).cast(pl.Int32).alias("window_min"))
        path = processed / f"dense_blocks_by_hour/window={w}/{hour_id}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        features.write_parquet(path)
        stats[f"w{w}_blocks"], stats[f"w{w}_accounts_in_blocks"] = len(blocks), int(features["in_any_block"].sum())
    return stats


def merge_windows(processed: Path, windows: list[int]) -> None:
    for w in windows:
        out = processed / f"dense_blocks/window={w}/part.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        pl.scan_parquet(str(processed / f"dense_blocks_by_hour/window={w}/*.parquet")).sink_parquet(out)
