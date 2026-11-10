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
# # 09 — Audit desain split
#
# **Tujuan:** mengukur seberapa besar desain split mengubah performa terukur (RQ2), memakai data `w0–w2`.
# Holdout `w3` tidak disentuh. Semua metrik dihitung terhadap label teramati `s`.

# %%
import json

import numpy as np
import pandas as pd
import polars as pl
from sklearn.metrics import average_precision_score

from ghremoval.analysis import FORWARD_ARMS, pilot_scores, score_row
from ghremoval.config import load_context, update_params
from ghremoval.correlogram import autocorrelation_range, choose_block_width, residual_correlogram
from ghremoval.data import FEATURE_SETS, apply_age_bins, fit_age_edges, load_frame
from ghremoval.evaluate import paired_cluster_bootstrap
from ghremoval.models.fit import arm_mask, load_stage
from ghremoval.models.pilot import pilot_model
from ghremoval.quality import Checks
from ghremoval.report import save_table, write_numbers
from ghremoval.runlog import RunLog
from ghremoval.splits import artifact_groups, artifact_links, diagnose, id_block_groups, signature_groups, stratified_group_folds
from ghremoval.viz import new_figure, save_figure

ctx = load_context(config_path)
run = RunLog("09_split_audit", ctx.paths.run_log, ctx.paths.root)
checks = Checks()
cfg = ctx.p.locked["splits"]
reps = ctx.p.locked["decision"]["bootstrap_reps"]
frame = load_frame(ctx, 60, ["train", "val"]).filter(pl.col("in_fixed_cohort"))
y = frame["is_gone"].to_numpy().astype(int)
ids = frame["actor_id"].to_numpy()
strata = frame["stratum"].to_numpy()
recency = frame["id_recency"].to_numpy()
is_dev_train = frame["week"].is_in(ctx.weeks_of("train")).to_numpy()
print("akun:", frame.height, "positif:", int(y.sum()))
assert "w3" not in frame["week"].unique().to_list()

# %% [markdown]
# ## 1. Grup tiap lengan dan diagnostiknya

# %%
hours = frame["hour_id"].unique().to_list()
events = pl.scan_parquet([str(ctx.paths.interim / f"events/hour_id={h}/part.parquet") for h in hours])
commits = pl.scan_parquet([str(ctx.paths.interim / f"commit_msgs/hour_id={h}/part.parquet") for h in hours])
groups = {"A1_random": np.arange(frame.height), "A2_artifact": artifact_groups(frame.height, artifact_links(frame, events, commits, cfg["artifact_max_accounts"]))}
for width in cfg["id_block_widths"]:
    groups[f"A3_idblock_{width}"] = id_block_groups(ids, width)
groups["A3s_signature"] = signature_groups(frame["n_events"].to_numpy(), frame["n_repos"].to_numpy(), frame["n_active_minutes"].to_numpy(), cfg["signature_min_events"])
folds = {arm: {seed: stratified_group_folds(g, y, cfg["n_folds"], seed) for seed in cfg["cv_seeds"]} for arm, g in groups.items()}
diagnostics = pd.DataFrame([{"arm": arm, **diagnose(g, y, folds[arm][cfg["cv_seeds"][0]], cfg["max_group_pos_share"])} for arm, g in groups.items()])
save_table(diagnostics, "tab_group_diagnostics", "Group structure and positive concentration per split arm")
valid_arms = diagnostics.loc[~diagnostics["is_degenerate"], "arm"].tolist()
diagnostics

# %% [markdown]
# ## 2. Korelogram residual dan lebar blok
#
# Residual dari baseline `B2` pada `w0–w1`, split acak. Aturan pemilihan dikunci di `docs/06`.

# %%


def oof_by_arm(feature_set: str, arm_folds: dict[int, np.ndarray], subset: np.ndarray | None = None) -> np.ndarray:
    """Skor out-of-fold. Batas bin usia dihitung ulang dari data latih tiap lipatan."""
    index = np.arange(frame.height) if subset is None else np.flatnonzero(subset)
    columns = [c for c in FEATURE_SETS[feature_set] if c != "age_bin12"]
    base = frame.select(columns).to_numpy().astype(np.float32)[index]
    local_y, local_recency, runs = y[index], recency[index], []
    for seed, fold_values in arm_folds.items():
        local_folds, score = fold_values[index], np.zeros(len(index))
        for fold in np.unique(local_folds):
            test = local_folds == fold
            edges = fit_age_edges(local_recency[~test], ctx.p.locked["features"]["age_bins"])
            X = np.column_stack([base, np.digitize(local_recency, edges).astype(np.float32)])
            score[test] = pilot_model(seed).fit(X[~test], local_y[~test]).predict_proba(X[test])[:, 1]
        runs.append(score)
    return np.mean(runs, axis=0)


baseline_oof = oof_by_arm("B2", folds["A1_random"], subset=is_dev_train)
residuals = y[is_dev_train] - baseline_oof
correlogram = residual_correlogram(ids[is_dev_train], residuals, seed=ctx.p.project["seed"])
autocorr_range = autocorrelation_range(correlogram)
primary = choose_block_width(cfg["id_block_widths"], autocorr_range)
if ctx.p.derived["primary_id_block_width"] is None:
    update_params(ctx, "derived.primary_id_block_width", primary)
    ctx = load_context(config_path)
print("jarak autokorelasi:", autocorr_range, "lebar terpilih:", primary, "tersimpan:", ctx.p.derived["primary_id_block_width"])
fig, ax = new_figure()
ax.semilogx([r["mid"] for r in correlogram], [r["corr"] for r in correlogram], marker="o", ms=2.5, lw=1, color="#0072B2")
ax.axhline(0.05, color="#D55E00", lw=0.8, ls="--"); ax.axvline(primary, color="#6E6E6E", lw=0.8, ls=":")
ax.set_xlabel("Distance between numeric IDs"); ax.set_ylabel("Residual correlation")
save_figure(fig, "fig_correlogram")

# %% [markdown]
# ## 3. Performa per lengan validasi silang

# %%
scores = {arm: {fs: oof_by_arm(fs, folds[arm]) for fs in ("B2", "M_behav")} for arm in valid_arms}
all_mask = np.ones(frame.height, bool)
rows = []
for arm in valid_arms:
    for fs in ("B2", "M_behav"):
        rows.append({"arm": arm, "model": fs, **score_row(y, scores[arm][fs], strata, all_mask)})
cv_table = pd.DataFrame(rows)
primary_arm = f"A3_idblock_{ctx.p.derived['primary_id_block_width']}"
cv_table.loc[:, ["arm", "model", "n", "n_pos", "ap_all", "ap_5-19", "ap_20+", "base_5-19"]]

# %% [markdown]
# ## 4. Tambahan AP fitur perilaku dan H2a
#
# H2a: rasio tambahan AP (A1 / A3 primer) pada stratum 5–19.

# %%
mask_519 = strata == "5-19"
clusters = id_block_groups(ids, ctx.p.derived["primary_id_block_width"])


def gain(arm: str, idx: np.ndarray) -> float:
    return average_precision_score(y[idx], scores[arm]["M_behav"][idx]) - average_precision_score(y[idx], scores[arm]["B2"][idx])


def ratio_metric(idx: np.ndarray) -> float:
    kept = idx[mask_519[idx]]
    if y[kept].sum() == 0:
        return float("nan")
    denominator = gain(primary_arm, kept)
    return float("nan") if denominator <= 0 else gain("A1_random", kept) / denominator


whole = np.flatnonzero(mask_519)
gains = {arm: gain(arm, whole) for arm in valid_arms}
ratio = gains["A1_random"] / gains[primary_arm] if primary_arm in gains and gains[primary_arm] > 0 else float("nan")
ratio_ci = paired_cluster_bootstrap(lambda idx: ratio_metric(idx) - 1.0, clusters, reps, ctx.p.project["seed"])
print("tambahan AP per lengan (5-19):", {k: round(v, 4) for k, v in gains.items()})
print("rasio A1/A3:", round(ratio, 3), "CI rasio:", round(ratio_ci["low"] + 1, 3), round(ratio_ci["high"] + 1, 3), "p:", round(ratio_ci["p_one_sided"], 4))

# %% [markdown]
# ## 5. Lengan forward tahap pengembangan
#
# Train `w0–w1`, test `w2`. Model memakai konfigurasi pilot supaya audit tidak bergantung pada tuning.

# %%
data = load_stage(ctx, "dev", 60)
forward = {fs: pilot_scores(fs, data.train, [data.test, data.f1], ctx) for fs in ("B2", "M_behav")}
forward_rows = []
for arm in FORWARD_ARMS:
    test_frame, index = (data.f1, 1) if arm == "F1_forward" else (data.test, 0)
    fy, mask = test_frame["is_gone"].to_numpy().astype(int), arm_mask(data.train, test_frame, arm, ctx)
    for fs in ("B2", "M_behav"):
        forward_rows.append({"arm": arm, "model": fs, **score_row(fy, forward[fs][index], test_frame["stratum"].to_numpy(), mask)})
forward_table = pd.DataFrame(forward_rows)
audit = pd.concat([cv_table, forward_table], ignore_index=True)
save_table(audit, "tab_split_audit", "Measured performance per split arm, development stage (observed label)")
forward_table[["arm", "model", "n", "n_pos", "ap_all", "ap_5-19", "ap_20+", "base_5-19"]]

# %%
ref = forward_table.set_index(["arm", "model"]).loc[("F2_forward_new_accounts", "M_behav"), "ap_5-19"]
distance = {arm: float(cv_table[(cv_table.arm == arm) & (cv_table.model == "M_behav")]["ap_5-19"].iloc[0] - ref) for arm in valid_arms}
print("selisih AP 5-19 tiap lengan CV terhadap F2 pengembangan:", {k: round(v, 4) for k, v in distance.items()})
fig, ax = new_figure(height=2.6)
names = list(gains)
ax.barh(names, [gains[n] for n in names], color="#0072B2")
ax.set_xlabel("AP gain of behaviour features over baseline, 5-19 events")
save_figure(fig, "fig_split_bias")
summary = {"gains_5_19": gains, "ratio_a1_a3": ratio, "ratio_ci": [ratio_ci["low"] + 1, ratio_ci["high"] + 1], "ratio_p": ratio_ci["p_one_sided"], "distance_to_f2_dev": distance, "primary_width": ctx.p.derived["primary_id_block_width"], "autocorrelation_range": autocorr_range, "valid_arms": valid_arms, "cv_ap_5_19": {arm: float(cv_table[(cv_table.arm == arm) & (cv_table.model == "M_behav")]["ap_5-19"].iloc[0]) for arm in valid_arms}}
(ctx.paths.results / "split_audit_dev.json").write_text(json.dumps(summary, indent=2) + "\n")

# %% [markdown]
# ## Ringkasan & cek

# %%
reported = set(cv_table["arm"])
degenerate = set(diagnostics.loc[diagnostics["is_degenerate"], "arm"])
checks.add("Q15", not (reported & degenerate), f"lengan degeneratif: {sorted(degenerate)}")
checks.add("Q16", ctx.p.derived["primary_id_block_width"] in cfg["id_block_widths"], str(ctx.p.derived["primary_id_block_width"]))
checks.add("Q17", "w3" not in frame["week"].unique().to_list(), "tanpa w3")
checks.raise_if_failed()
write_numbers({"primary_id_block_width": ctx.p.derived["primary_id_block_width"], "ratio_h2a": ratio})
print(run.finish(n_rows=frame.height, n_pos=int(y.sum())))
