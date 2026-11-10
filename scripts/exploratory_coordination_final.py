#!/usr/bin/env python
"""Analisis eksploratif setelah holdout: dari mana tambahan AP fitur koordinasi berasal.

Tidak mengubah keputusan hipotesis di nb15. Keluaran hanya agregat, tanpa login, nama repo, atau hash.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import polars as pl
from sklearn.metrics import average_precision_score

from ghremoval.analysis import checkpoint_scores, coordination_ladder, fixed_shallow_scores, policy_results
from ghremoval.config import load_context
from ghremoval.models.fit import arm_mask, load_stage
from ghremoval.policy import aurt
from ghremoval.report import save_table

ctx = load_context()
if not (ctx.paths.results / "holdout_opened.json").exists():
    raise RuntimeError("Skrip ini hanya boleh dijalankan setelah nb15 membuka holdout.")

best = json.loads((ctx.paths.results / "best_params.json").read_text())
out = coordination_ladder(ctx, "final", best)
data, scores, y = out["data"], out["scores"], out["y"]
scores = {"B2": fixed_shallow_scores("B2", data.train, [data.test], ctx)[0], **scores}
test = data.test
hours = test["hour_id"].to_numpy()
key = arm_mask(data.train, test, "F3_forward_batch_excluded", ctx) & (test["stratum"].to_numpy() == "5-19")


def row(view: str, label: str, mask: np.ndarray) -> dict:
    base = {"view": view, "label": label, "n": int(mask.sum()), "n_pos": int(y[mask].sum()), "base_rate": float(y[mask].mean()) if mask.any() else float("nan")}
    return base | {f"ap_{name}": float(average_precision_score(y[mask], scores[name][mask])) if y[mask].sum() else float("nan") for name in ("B2", "M_behav", "M_proxy", "M_coord")}


rows = [row("all", "F3_5-19", key)]
for hour in sorted(set(hours[key])):
    rows.append(row("per_hour", hour, key & (hours == hour)))
    rows.append(row("without_hour", hour, key & (hours != hour)))
by_hour = pd.DataFrame(rows)
by_hour["gain_behav"] = by_hour["ap_M_behav"] - by_hour["ap_B2"]
by_hour["gain_proxy"] = by_hour["ap_M_proxy"] - by_hour["ap_M_behav"]
by_hour["gain_block_over_proxy"] = by_hour["ap_M_coord"] - by_hour["ap_M_proxy"]
save_table(by_hour, "tab_exploratory_coordination_final", "Exploratory: coordination gain by holdout hour, F3, 5-19 events (observed label)")
print(by_hour.round(4).to_string())

frame = pl.concat([data.train, data.test]).filter(pl.col("stratum") == "5-19")
shared = []
for feature in ("msg_any_shared", "repo_any_shared", "short_any_shared"):
    table = frame.group_by("week", pl.col(feature).cast(pl.Int8).alias("shared")).agg(pl.len().alias("n"), pl.col("is_gone").sum().alias("n_gone"), pl.col("is_gone").mean().alias("rate")).sort("week", "shared")
    shared += [{"feature": feature, **r} for r in table.to_dicts()]
shared_table = pd.DataFrame(shared)
save_table(shared_table, "tab_exploratory_shared_by_week", "Exploratory: disappearance rate by shared-artifact flag and week, 5-19 events (observed label)")
print(shared_table.round(4).to_string())

gone = test.filter(pl.Series(key & (y == 1))).select("actor_id", "hour_id")
holdout_hours = sorted(set(hours))
commits = pl.scan_parquet([str(ctx.paths.interim / f"commit_msgs/hour_id={h}/part.parquet") for h in holdout_hours]).select("actor_id", "hour_id", "msg_hash").unique().collect()
groups = commits.join(gone, on=["actor_id", "hour_id"], how="inner").group_by("msg_hash").agg(pl.col("actor_id").n_unique().alias("n_gone_accounts")).sort("n_gone_accounts", descending=True)
sizes = groups["n_gone_accounts"].to_list()
covered = commits.join(gone, on=["actor_id", "hour_id"], how="inner").select("actor_id", "hour_id").unique().height
print("positif F3 5-19:", gone.height, "punya pesan commit:", covered, "ukuran grup pesan terbesar:", sizes[:8], "grup berukuran >= 5:", sum(s >= 5 for s in sizes))

primary, horizon = ctx.p.locked["policy"]["primary_target_precision"], ctx.p.locked["policy"]["aurt_horizon_minutes"]
behav = checkpoint_scores(ctx, "final", "fixed", "M_behav", best["xgb"])
policy = policy_results(ctx, behav, "F3_forward_batch_excluded", load_stage(ctx, "final", 60, cohort="fixed").train)
arm, label_y = policy["mask"], behav["test_y"]
adaptive, fixed = policy["times"][("adaptive", primary)], policy["times"][("best_fixed", primary)]
policy_hours = behav["test_frame"]["hour_id"].to_numpy()


def policy_row(view: str, label: str, mask: np.ndarray) -> dict:
    a, b = aurt(adaptive[mask], label_y[mask], horizon), aurt(fixed[mask], label_y[mask], horizon)
    return {"view": view, "label": label, "n": int(mask.sum()), "n_pos": int(label_y[mask].sum()), "n_flagged_adaptive": int(np.isfinite(adaptive[mask]).sum()), "n_tp_adaptive": int(((label_y[mask] == 1) & np.isfinite(adaptive[mask])).sum()), "aurt_adaptive": a, "aurt_best_fixed": b, "delta": a - b}


policy_rows = [policy_row("all", "F3_fixed_cohort", arm)]
for hour in sorted(set(policy_hours[arm])):
    policy_rows.append(policy_row("per_hour", hour, arm & (policy_hours == hour)))
    policy_rows.append(policy_row("without_hour", hour, arm & (policy_hours != hour)))
policy_table = pd.DataFrame(policy_rows)
save_table(policy_table, "tab_exploratory_policy_by_hour", "Exploratory: adaptive policy against selected fixed window by holdout hour (observed label)")
print(policy_table.round(4).to_string())
