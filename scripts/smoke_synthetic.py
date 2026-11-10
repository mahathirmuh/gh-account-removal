#!/usr/bin/env python
"""Uji asap jalur analisis memakai label acak buatan.

Label sungguhan tidak dibaca. Tidak ada file yang ditulis ke results/. Skrip ini hanya memastikan
kode berjalan dari ujung ke ujung, dan angkanya tidak bermakna.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import polars as pl

import ghremoval.data as data_module
from ghremoval import analysis as A
from ghremoval.config import load_context
from ghremoval.data import xy
from ghremoval.labels import accounts_in_scope
from ghremoval.models.fit import arm_mask, load_stage, time_holdback
from ghremoval.models.tune import run_study

ctx = load_context()
ctx.p.derived["primary_id_block_width"] = 20000
hours = pl.read_parquet(ctx.paths.processed / "account_hour.parquet", columns=["actor_id", "n_events", "is_app_bot"]).filter(~pl.col("is_app_bot"))
accounts = hours.group_by("actor_id").agg(pl.col("n_events").max().alias("n"))
rng = np.random.default_rng(0)
random_gone = rng.random(accounts.height) < (0.02 + 0.3 * (accounts["n"].to_numpy() >= 20))
fake_labels = accounts.select("actor_id").with_columns(pl.Series("is_gone", random_gone), pl.lit("s1").alias("snapshot_id"), pl.when(pl.Series(random_gone)).then(pl.lit("gone")).otherwise(pl.lit("present")).alias("status"))


def fake_load(context, scope, snapshot_id="s1"):
    return fake_labels.join(accounts_in_scope(context, scope), on="actor_id", how="inner")


data_module.load_labels = fake_load
BEST = {"xgb": {"max_depth": 4, "learning_rate": 0.1, "min_child_weight": 5.0, "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0, "n_estimators": 60},
        "lr": {"C": 1.0}, "mlp": {"hidden": 64, "dropout": 0.1, "lr": 1e-3, "weight_decay": 1e-5, "batch": 512}}

for stage in sys.argv[1:] or ["dev", "final"]:
    print(f"== tahap {stage}", flush=True)
    data = load_stage(ctx, stage, 60)
    print("train", data.train.height, "test", data.test.height, "f1", data.f1.height, flush=True)
    result = A.ladder(ctx, stage, data, BEST)
    print("ladder baris", len(result["rows"]), flush=True)
    scores = {name: value[0] for name, value in result["models"].items()}
    print("gain", {k: round(v, 3) for k, v in A.bootstrap_gain(ctx, data, scores["M_behav_xgb"], scores["B2_xgb"], "F3_forward_batch_excluded", "5-19", reps=30).items() if isinstance(v, float)}, flush=True)
    print("du/name", len(A.du_name_baselines(ctx, data)), flush=True)
    print("latency", len(A.latency_table(ctx, stage, BEST)), flush=True)
    for cohort in ("fixed", "deployable"):
        behav = A.checkpoint_scores(ctx, stage, cohort, "M_behav", BEST["xgb"])
        train = load_stage(ctx, stage, 60, cohort=cohort).train
        out = A.policy_results(ctx, behav, "F3_forward_batch_excluded", train)
        keys = list(out["times"])
        print(cohort, "baris kebijakan", len(out["rows"]), "kunci", keys[:3], flush=True)
        if ("adaptive", 0.7) in out["times"] and ("best_fixed", 0.7) in out["times"]:
            print(" aurt", A.aurt_delta_bootstrap(ctx, behav, out["times"][("adaptive", 0.7)], out["times"][("best_fixed", 0.7)], out["mask"], reps=30)["delta"], flush=True)
    coord = A.coordination_ladder(ctx, stage, BEST)
    print("koordinasi", len(coord["rows"]), flush=True)
    if stage == "dev":
        X, y = xy(data.train, "M_behav")
        X_val, y_val = xy(data.test, "M_behav")
        es = time_holdback(data.train, A.hour_order(ctx))
        with tempfile.TemporaryDirectory() as folder:
            for family in ("xgb", "lr", "mlp"):
                print(family, run_study(family, 42, X, y, es, X_val, y_val, arm_mask(data.train, data.test, "F2_forward_new_accounts", ctx), Path(folder), 2)["n_trials"], flush=True)
print("uji asap selesai")
