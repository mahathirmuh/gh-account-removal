"""Sampel audit manual (docs/04). Kolom anotasi tidak pernah diisi oleh kode."""

from __future__ import annotations

import json
from collections import Counter

import numpy as np
import polars as pl

from ghremoval.config import Context
from ghremoval.ingest.gharchive import iter_events
from ghremoval.parse.events import pseudo


def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's κ untuk dua anotator."""
    n = len(a)
    labels = sorted(set(a) | set(b))
    observed = sum(x == y for x, y in zip(a, b)) / n
    count_a, count_b = Counter(a), Counter(b)
    expected = sum(count_a[label] * count_b[label] for label in labels) / (n * n)
    return (observed - expected) / (1 - expected) if expected < 1 else float("nan")


def attach_pseudo(ctx: Context, frame: pl.DataFrame) -> pl.DataFrame:
    """Menambahkan pseudonim akun, dengan urutan baris tetap."""
    dim = pl.read_parquet(ctx.paths.processed / "account_dim.parquet", columns=["actor_id", "actor_pseudo"])
    return frame.join(dim, on="actor_id", how="left", maintain_order="left")


def draw_sample(frame: pl.DataFrame, score: np.ndarray, n_top: int, n_low: int, seed: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Sampel skor tinggi dan skor rendah dengan distribusi stratum sama. Mengembalikan (sampel acak, kunci kelompok)."""
    rng = np.random.default_rng(seed)
    data = frame.select("actor_id", "hour_id", "stratum", "actor_pseudo").with_columns(pl.Series("score", score))
    top = data.sort("score", descending=True).head(n_top).with_columns(pl.lit("top").alias("score_group"))
    below = data.sort("score", descending=True).slice(n_top, None).filter(pl.col("score") < pl.col("score").median().over("stratum"))
    wanted = top.group_by("stratum").len().to_dicts()
    parts = [below.filter(pl.col("stratum") == row["stratum"]).sample(n=min(row["len"], below.filter(pl.col("stratum") == row["stratum"]).height), seed=seed) for row in wanted]
    low = pl.concat(parts).with_columns(pl.lit("low").alias("score_group")).head(n_low)
    sample = pl.concat([top, low])
    sample = sample[rng.permutation(sample.height)].with_row_index("audit_id")
    return sample.select("audit_id", "actor_id", "hour_id", "stratum", "actor_pseudo"), sample.select("audit_id", "score_group", "score")


def render_summaries(ctx: Context, sample: pl.DataFrame, key: bytes) -> list[dict]:
    """Ringkasan publik tiap akun dari raw, dengan login diganti pseudonim dan tanpa email."""
    wanted = {(row["actor_id"], row["hour_id"]): row["audit_id"] for row in sample.iter_rows(named=True)}
    by_hour: dict[str, set[int]] = {}
    for (actor_id, hour) in wanted:
        by_hour.setdefault(hour, set()).add(actor_id)
    data: dict[int, dict] = {audit: {"audit_id": audit, "event_counts": Counter(), "repo_names": [], "commit_messages": [], "pr_titles": []} for audit in wanted.values()}
    for hour, actors in by_hour.items():
        for raw in iter_events(ctx.paths.raw / f"{hour}.json.gz"):
            if raw is None or raw["actor"]["id"] not in actors:
                continue
            entry = data[wanted[(raw["actor"]["id"], hour)]]
            login = raw["actor"]["login"]
            mask = lambda text: text.replace(login, pseudo(login, key)[:8])  # noqa: E731
            entry["event_counts"][raw["type"]] += 1
            name = mask(raw["repo"]["name"].split("/", 1)[-1])
            if name not in entry["repo_names"] and len(entry["repo_names"]) < 20:
                entry["repo_names"].append(name)
            payload = raw.get("payload") or {}
            for commit in payload.get("commits") or []:
                if len(entry["commit_messages"]) < 20:
                    entry["commit_messages"].append(mask((commit.get("message") or "")[:200]))
            if raw["type"] == "PullRequestEvent" and len(entry["pr_titles"]) < 10:
                entry["pr_titles"].append(mask(((payload.get("pull_request") or {}).get("title") or "")[:200]))
    return [{**entry, "event_counts": dict(entry["event_counts"])} for entry in data.values()]


def write_summaries(rows: list[dict], path) -> None:
    with open(path, "w", encoding="utf8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
