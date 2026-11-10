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

for stage in ([s for s in sys.argv[1:] if s != "none"] if sys.argv[1:] else ["dev", "final"]):
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

# Bagian yang dipakai nb09, nb11, dan nb14, tetap dengan label acak dan tanpa menulis file.
from ghremoval.audit import attach_pseudo, draw_sample, render_summaries  # noqa: E402
from ghremoval.correlogram import autocorrelation_range, choose_block_width, residual_correlogram  # noqa: E402
from ghremoval.data import load_frame  # noqa: E402
from ghremoval.models.fit import predict  # noqa: E402
from ghremoval.models.pilot import pilot_model  # noqa: E402
from ghremoval.pu import bagging_score, elkan_noto_fit, hide_positives, naive_fit, pu_bagging_fit, sar_em_fit  # noqa: E402
from ghremoval.secrets import load_hmac_key  # noqa: E402
from ghremoval.splits import artifact_groups, artifact_links, diagnose, signature_groups, stratified_group_folds  # noqa: E402

frame = load_frame(ctx, 60, ["train", "val"]).filter(pl.col("in_fixed_cohort"))
y_all = frame["is_gone"].to_numpy().astype(int)
hours_used = frame["hour_id"].unique().to_list()
events = pl.scan_parquet([str(ctx.paths.interim / f"events/hour_id={h}/part.parquet") for h in hours_used])
commits = pl.scan_parquet([str(ctx.paths.interim / f"commit_msgs/hour_id={h}/part.parquet") for h in hours_used])
groups = artifact_groups(frame.height, artifact_links(frame, events, commits, ctx.p.locked["splits"]["artifact_max_accounts"]))
print("artefak", diagnose(groups, y_all, stratified_group_folds(groups, y_all, 5, 42), 0.25), flush=True)
sig = signature_groups(frame["n_events"].to_numpy(), frame["n_repos"].to_numpy(), frame["n_active_minutes"].to_numpy(), 10)
print("signature", diagnose(sig, y_all, stratified_group_folds(sig, y_all, 5, 42), 0.25), flush=True)
sample_idx = np.flatnonzero(frame["week"].is_in(["w0", "w1"]).to_numpy())
X_all = frame.select("n_events_w", "id_recency").to_numpy().astype(np.float32)
residual = y_all[sample_idx] - pilot_model(42).fit(X_all[sample_idx], y_all[sample_idx]).predict_proba(X_all[sample_idx])[:, 1]
table = residual_correlogram(frame["actor_id"].to_numpy()[sample_idx], residual)
print("korelogram", len(table), "lebar", choose_block_width([5000, 20000, 100000], autocorrelation_range(table)), flush=True)

data = load_stage(ctx, "dev", 60)
X, s = xy(data.train, "M_behav")
prop = data.train.select("n_events_coarse", "age_bin12").to_numpy()
hidden = hide_positives(s, prop, 0.5, 1)
s_hidden = s & ~hidden
print("pu", predict(naive_fit(X, s_hidden, 1), X).shape, elkan_noto_fit(X, s_hidden, 1)[1], bagging_score(pu_bagging_fit(X, s_hidden, 1, n_bags=3), X).shape, predict(sar_em_fit(X, s_hidden, prop, 1, iterations=2)[0], X).shape, flush=True)
sample, key = draw_sample(attach_pseudo(ctx, data.test), np.random.default_rng(0).random(data.test.height), 100, 100, 1)
rows = render_summaries(ctx, sample, load_hmac_key(ctx).reveal().encode())
print("audit", sample.height, key["score_group"].value_counts().sort("score_group").to_dicts(), len(rows), flush=True)
print("uji asap selesai")
