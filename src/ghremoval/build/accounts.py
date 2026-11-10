"""Dimensi akun dan tabel akun-jam (docs/03)."""

from __future__ import annotations

import polars as pl

from ghremoval.config import Context


def stratum_expr(column: str, strata: list[list]) -> pl.Expr:
    expr = None
    for low, high in strata:
        label = str(low) if low == high else (f"{low}+" if high is None else f"{low}-{high}")
        condition = pl.col(column).is_between(low, high if high is not None else 10**12)
        expr = pl.when(condition).then(pl.lit(label)) if expr is None else expr.when(condition).then(pl.lit(label))
    return expr.otherwise(None).alias("stratum")


def assign_stratum(n: int, strata: list[list]) -> str | None:
    for low, high in strata:
        if n >= low and (high is None or n <= high):
            return str(low) if low == high else (f"{low}+" if high is None else f"{low}-{high}")
    return None


def period_expr() -> pl.Expr:
    return pl.when(pl.col("week") == "dev").then(pl.lit("dev")).when(pl.col("week") == "w3").then(pl.lit("w3")).otherwise(pl.lit("w0_w2")).alias("period")


def mark_first_in_period(df: pl.DataFrame, order: dict[str, int]) -> pl.DataFrame:
    """Menandai baris kemunculan pertama akun pada tiap periode, menurut urutan jam."""
    ranked = df.with_columns(pl.col("hour_id").replace_strict(order, return_dtype=pl.Int32).alias("_rank"), period_expr())
    return ranked.with_columns((pl.col("_rank") == pl.col("_rank").min().over(["actor_id", "period"])).alias("is_first_in_period")).drop("_rank", "period")


def build_account_hour(ctx: Context) -> pl.DataFrame:
    locked = ctx.p.locked["cohorts"]
    events = pl.scan_parquet(str(ctx.paths.interim / "events/*/part.parquet"))
    base = (events.group_by(["actor_id", "hour_id", "week"]).agg(pl.len().cast(pl.Int32).alias("n_events"), pl.col("second_of_hour").min().alias("first_second"),
                                                                pl.col("second_of_hour").max().alias("last_second"), pl.col("is_app_bot").first()).collect())
    order = {hour: i for i, (hour, _) in enumerate(ctx.all_hours())}
    out = base.with_columns(stratum_expr("n_events", locked["strata"]), ((pl.col("n_events") >= locked["fixed_min_events"]) & ~pl.col("is_app_bot")).alias("in_fixed_cohort"),
                            pl.col("actor_id").max().over("hour_id").alias("max_id_in_hour")).with_columns((pl.col("max_id_in_hour") - pl.col("actor_id")).alias("id_recency"))
    return mark_first_in_period(out, order).sort(["hour_id", "actor_id"])


def build_account_dim(ctx: Context, account_hour: pl.DataFrame) -> pl.DataFrame:
    actors = pl.scan_parquet(str(ctx.paths.interim / "actor_login_features/*/part.parquet")).unique(subset=["actor_id"], keep="first").collect()
    order = {hour: i for i, (hour, _) in enumerate(ctx.all_hours())}
    seen = (account_hour.with_columns(pl.col("hour_id").replace_strict(order, return_dtype=pl.Int32).alias("_rank")).sort("_rank")
            .group_by("actor_id", maintain_order=True).agg(pl.col("hour_id").first().alias("first_hour_id"), pl.len().cast(pl.Int32).alias("n_hours_seen")))
    return actors.join(seen, on="actor_id", how="inner").sort("actor_id")
