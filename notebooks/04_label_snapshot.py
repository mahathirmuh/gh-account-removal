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
mode = "s1"

# %% [markdown]
# # 04 — Snapshot status akun
#
# **Tujuan:** mengambil status semua akun target satu kali, sesuai `docs/04`.
# Tingkat hilang per minggu tidak ditampilkan di sini.

# %%
from datetime import UTC, date, datetime

import numpy as np
import polars as pl

from ghremoval.config import load_context, update_params
from ghremoval.github_client import GitHubClient
from ghremoval.labels import HoldoutLockedError, load_labels, merge_checkpoint, run_snapshot, verify_rest
from ghremoval.quality import Checks
from ghremoval.runlog import RunLog
from ghremoval.secrets import load_token

ctx = load_context(config_path)
run = RunLog(f"04_label_snapshot_{mode}", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
client = GitHubClient(load_token(ctx), ctx.p.project["user_agent"])

# %% [markdown]
# ## 1. Daftar akun target

# %%
hours = pl.read_parquet(ctx.paths.processed / "account_hour.parquet")
ids = sorted(hours.filter(~pl.col("is_app_bot") & (pl.col("n_events") >= ctx.p.label["min_events_to_label"]))["actor_id"].unique().to_list())
if mode == "s2":
    previous = pl.read_parquet(ctx.paths.processed / "labels.parquet").filter((pl.col("snapshot_id") == "s1") & (pl.col("status") == "present"))
    ids = sorted(previous["actor_id"].to_list())
print("akun target:", len(ids), "query:", len(ids) // ctx.p.label["graphql_batch_size"] + 1)

# %% [markdown]
# ## 2. Snapshot, dengan checkpoint per batch

# %%
if mode == "s1" and ctx.p.label["snapshot_date"] is None:
    update_params(ctx, "label.snapshot_date", date.today().isoformat())
    ctx = load_context(config_path)
print("snapshot_date:", ctx.p.label["snapshot_date"])
started = datetime.now(UTC)
stats = run_snapshot(ctx, client, ids, mode)
print({k: v for k, v in stats.items() if k in ("present", "gone", "error", "no_data") or k.startswith("warn_")})
print("menit:", round((datetime.now(UTC) - started).total_seconds() / 60, 1))

# %% [markdown]
# ## 3. Gabungkan dan verifikasi

# %%
labels = merge_checkpoint(ctx, mode).filter(pl.col("snapshot_id") == mode)
rng = np.random.default_rng(ctx.p.project["seed"])
gone_ids = labels.filter(pl.col("is_gone"))["actor_id"].to_numpy()
sample = rng.choice(gone_ids, min(2000, len(gone_ids)), replace=False).tolist()
rest = verify_rest(client, sample)
mismatch = 1 - rest.get(404, 0) / max(len(sample), 1)
print("verifikasi REST:", dict(rest), "ketidakcocokan:", round(mismatch, 4))

# %% [markdown]
# ## Ringkasan & cek

# %%
overall = labels.group_by("status").len().sort("status")
print(overall)
error_rate = labels.filter(pl.col("status") == "error").height / labels.height
checks.add("Q08a", labels["actor_id"].n_unique() == len(ids) == labels.height, "satu baris per akun")
checks.add("Q08b", error_rate < 0.001, f"error {error_rate:.5f}")
checks.add("Q09", mismatch <= 0.01, f"ketidakcocokan REST {mismatch:.4f}")
try:
    load_labels(ctx, "holdout")
    locked = False
except HoldoutLockedError:
    locked = True
checks.add("Q10", locked, "holdout terkunci")
if mode == "s1":
    dev = load_labels(ctx, "dev")
    print("jam dev:", dev.group_by("status").len().sort("status").to_dicts())
checks.raise_if_failed()
print(run.finish(n_accounts=labels.height, n_error=labels.filter(pl.col("status") == "error").height))
