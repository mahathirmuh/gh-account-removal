"""Baseline literatur yang bisa dihitung dari stream event (docs/05)."""

from __future__ import annotations

from pathlib import Path

import polars as pl

DU_COLUMNS = ["interval_le_60", "interval_le_120", "interval_le_180", "interval_le_3600", "n_watch", "n_fork", "n_push", "n_comment"]
NAME_COLUMNS = ["login_len", "login_digit_ratio", "login_hyphen_count"]


def du_interval_features(interim: Path, hours: list[str], window_min: int) -> pl.DataFrame:
    """Hitungan interval antar-operasi 1, 2, 3 menit dan 1 jam, serta jumlah operasi, mengikuti Du et al."""
    paths = [str(interim / f"events/hour_id={hour}/part.parquet") for hour in hours]
    cutoff = 60 * window_min
    events = pl.scan_parquet(paths).filter((pl.col("second_of_hour") < cutoff) & ~pl.col("is_app_bot")).select("actor_id", "hour_id", "second_of_hour", "event_type")
    gaps = events.sort(["actor_id", "hour_id", "second_of_hour"]).with_columns(pl.col("second_of_hour").diff().over(["actor_id", "hour_id"]).alias("gap"))
    out = gaps.group_by(["actor_id", "hour_id"]).agg((pl.col("gap") <= 60).sum().alias("interval_le_60"), (pl.col("gap") <= 120).sum().alias("interval_le_120"), (pl.col("gap") <= 180).sum().alias("interval_le_180"),
                                                     (pl.col("gap") <= 3600).sum().alias("interval_le_3600"), (pl.col("event_type") == "WatchEvent").sum().alias("n_watch"), (pl.col("event_type") == "ForkEvent").sum().alias("n_fork"),
                                                     (pl.col("event_type") == "PushEvent").sum().alias("n_push"), pl.col("event_type").is_in(["IssueCommentEvent", "PullRequestReviewCommentEvent", "CommitCommentEvent"]).sum().alias("n_comment"))
    return out.collect().with_columns(pl.col(DU_COLUMNS).cast(pl.Float64))
