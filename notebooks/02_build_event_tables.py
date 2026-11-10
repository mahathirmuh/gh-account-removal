# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% tags=["parameters"]
config_path = "config/params.yaml"
mode = "default"

# %% [markdown]
# # 02 — Bangun tabel event
#
# **Tujuan:** mengubah raw menjadi tabel event dan pesan commit yang bebas data pribadi mentah.
# Email dibuang saat parse, dan login diganti pseudonim HMAC.

# %%
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import polars as pl

from ghremoval.config import load_context
from ghremoval.parse.events import build_hour
from ghremoval.quality import Checks, pii_columns
from ghremoval.runlog import RunLog
from ghremoval.secrets import load_hmac_key

ctx = load_context(config_path)
run = RunLog("02_build_event_tables", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
key = load_hmac_key(ctx).reveal().encode()
hours = ctx.all_hours()

# %% [markdown]
# ## 1. Parse per jam

# %%
args = [(ctx.paths.raw / f"{hour}.json.gz", ctx.paths.interim, key, hour, week) for hour, week in hours]
with ProcessPoolExecutor(max_workers=4) as pool:
    stats = pd.DataFrame(list(pool.map(build_hour, *zip(*args))))
stats

# %% [markdown]
# ## Ringkasan & cek

# %%
events = pl.scan_parquet(str(ctx.paths.interim / "events/*/part.parquet"))
per_hour = events.group_by("hour_id").agg(pl.len().alias("n"), pl.col("event_id").n_unique().alias("n_unique"), pl.col("second_of_hour").min().alias("s_min"), pl.col("second_of_hour").max().alias("s_max")).collect()
checks.add("Q04a", (per_hour["n"] == per_hour["n_unique"]).all(), "event_id unik per jam")
checks.add("Q04b", per_hour["s_min"].min() >= 0 and per_hour["s_max"].max() <= 3599, "second_of_hour dalam rentang")
hour_mismatch = events.with_columns(pl.col("created_at").str.slice(0, 13).str.replace("T", "-").alias("stamp"), pl.col("hour_id").str.replace(r"-(\d)$", "-0$1").alias("norm")).filter(pl.col("stamp") != pl.col("norm")).select(pl.len()).collect().item()
checks.add("Q04c", hour_mismatch == 0, f"{hour_mismatch} event di jam yang salah")
columns = events.collect_schema().names() + pl.scan_parquet(str(ctx.paths.interim / "commit_msgs/*/part.parquet")).collect_schema().names()
checks.add("Q05", not pii_columns(columns), f"kolom mencurigakan: {pii_columns(columns)}")
dev = stats[stats["week"] == "dev"].iloc[0]
checks.add("sanity_events", int(dev["n_events"]) == 272191, f"event jam dev {dev['n_events']}")
checks.add("sanity_truncated", int(dev["n_push_truncated"]) == 1076, f"push terpotong {dev['n_push_truncated']}")
checks.raise_if_failed()
print(run.finish(n_events=int(stats["n_events"].sum()), n_commits=int(stats["n_commits"].sum())))
