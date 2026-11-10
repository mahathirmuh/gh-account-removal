"""Snapshot status akun dan pembacaan label yang menjaga holdout (docs/04)."""

from __future__ import annotations

import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from ghremoval.config import Context
from ghremoval.github_client import GitHubClient

QUERY = "query($ids:[ID!]!){rateLimit{cost remaining} nodes(ids:$ids){__typename ... on User{databaseId createdAt} ... on Organization{databaseId createdAt}}}"
LABEL_SCHEMA = {"snapshot_id": pl.String, "actor_id": pl.Int64, "status": pl.String, "node_type": pl.String, "is_gone": pl.Boolean, "created_at_api": pl.String, "source": pl.String, "checked_at": pl.String}


class HoldoutLockedError(RuntimeError):
    """Label holdout diminta saat holdout_open masih false."""


def legacy_node_id(actor_id: int) -> str:
    return base64.b64encode(f"04:User{actor_id}".encode()).decode()


def parse_batch(snapshot_id: str, ids: list[int], response: dict, now: str) -> tuple[list[tuple], Counter]:
    """Mengubah respons GraphQL menjadi baris label. Respons tanpa data menghasilkan status error."""
    stats: Counter = Counter()
    if not response.get("data"):
        stats["no_data"] += 1
        return [(snapshot_id, i, "error", None, False, None, "graphql", now) for i in ids], stats
    for warning in (response.get("extensions") or {}).get("warnings", []):
        stats[f"warn_{warning.get('type')}"] += 1
    errors = {tuple(e.get("path") or ())[-1]: e.get("type") for e in response.get("errors", []) if e.get("path")}
    rows = []
    for k, (actor_id, node) in enumerate(zip(ids, response["data"]["nodes"])):
        if node is not None:
            rows.append((snapshot_id, actor_id, "present", node["__typename"], False, node.get("createdAt"), "graphql", now))
            stats["present"] += 1
        elif errors.get(k) == "NOT_FOUND":
            rows.append((snapshot_id, actor_id, "gone", None, True, None, "graphql", now))
            stats["gone"] += 1
        else:
            rows.append((snapshot_id, actor_id, "error", None, False, None, "graphql", now))
            stats["error"] += 1
    return rows, stats


def fetch_batch(client: GitHubClient, snapshot_id: str, ids: list[int]) -> tuple[list[tuple], Counter]:
    response = client.graphql(QUERY, {"ids": [legacy_node_id(i) for i in ids]})
    return parse_batch(snapshot_id, ids, response, datetime.now(UTC).isoformat(timespec="seconds"))


def _checkpoint_dir(ctx: Context, snapshot_id: str) -> Path:
    path = ctx.paths.processed / "label_checkpoint" / snapshot_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_snapshot(ctx: Context, client: GitHubClient, ids: list[int], snapshot_id: str, workers: int = 2) -> Counter:
    """Menjalankan snapshot per batch dan menyimpan checkpoint, sehingga bisa dilanjutkan."""
    directory = _checkpoint_dir(ctx, snapshot_id)
    size = ctx.p.label["graphql_batch_size"]
    batches = [(k, ids[k:k + size]) for k in range(0, len(ids), size)]
    pending = [(k, batch) for k, batch in batches if not (directory / f"batch_{k:09d}.parquet").exists()]
    print(f"batch total {len(batches)}, tersisa {len(pending)}", flush=True)

    def work(item: tuple[int, list[int]]) -> Counter:
        k, batch = item
        rows, stats = fetch_batch(client, snapshot_id, batch)
        path = directory / f"batch_{k:09d}.parquet"
        tmp = path.with_suffix(".tmp")
        pl.DataFrame(rows, schema=LABEL_SCHEMA, orient="row").write_parquet(tmp)
        tmp.rename(path)
        return stats

    total: Counter = Counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for done, stats in enumerate(pool.map(work, pending), start=1):
            total.update(stats)
            if done % 200 == 0:
                print(f"selesai {done}/{len(pending)}", flush=True)
    return total


def merge_checkpoint(ctx: Context, snapshot_id: str) -> pl.DataFrame:
    """Menggabungkan checkpoint ke labels.parquet tanpa menimpa snapshot lain."""
    fresh = pl.read_parquet(str(_checkpoint_dir(ctx, snapshot_id) / "batch_*.parquet"))
    target = ctx.paths.processed / "labels.parquet"
    if target.exists():
        fresh = pl.concat([pl.read_parquet(target).filter(pl.col("snapshot_id") != snapshot_id), fresh])
    fresh.write_parquet(target)
    return fresh


def verify_rest(client: GitHubClient, sample: list[int]) -> Counter:
    return Counter(client.get(f"https://api.github.com/user/{i}")[0] for i in sample)


def accounts_in_scope(ctx: Context, scope: str) -> pl.DataFrame:
    hours = pl.read_parquet(ctx.paths.processed / "account_hour.parquet", columns=["actor_id", "week"])
    return hours.filter(pl.col("week").is_in(ctx.weeks_of(scope))).select("actor_id").unique()


def load_labels(ctx: Context, scope: str, snapshot_id: str = "s1") -> pl.DataFrame:
    """Label untuk akun yang muncul pada `scope`. Akun holdout ditolak selama holdout_open false."""
    if scope == "holdout" and not ctx.p.holdout_open:
        raise HoldoutLockedError("Holdout masih terkunci. Buka hanya di nb15 setelah Gerbang D.")
    labels = pl.read_parquet(ctx.paths.processed / "labels.parquet").filter(pl.col("snapshot_id") == snapshot_id)
    return labels.join(accounts_in_scope(ctx, scope), on="actor_id", how="inner")
