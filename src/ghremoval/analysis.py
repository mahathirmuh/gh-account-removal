"""Analisis bersama untuk tahap pengembangan dan holdout (docs/06)."""

from __future__ import annotations

import numpy as np
import polars as pl

from ghremoval.baselines import DU_COLUMNS, NAME_COLUMNS, du_interval_features
from ghremoval.config import Context
from ghremoval.data import FEATURE_SETS, xy
from ghremoval.evaluate import ap_by_stratum, delta_ap_metric, paired_cluster_bootstrap, precision_at_k, recall_at_k, within_cell_auc
from ghremoval.models.fit import XGB_FIXED_SHALLOW, StageData, arm_mask, fit_predict, fit_xgb, load_stage, predict, time_holdback
from ghremoval.models.pilot import pilot_model
from ghremoval.policy import Calibrator, NOT_FLAGGED, amoc_curve, aurt, first_cross, fixed_times, matched_precision, policy_metrics, q_grid, select_fixed, select_q_kappa, thresholds
from ghremoval.splits import forward_arm, id_block_groups

FORWARD_ARMS = ["F1_forward", "F2_forward_new_accounts", "F3_forward_batch_excluded"]
REPORT_STRATA = ["all", "5-19", "20+"]


def hour_order(ctx: Context) -> dict[str, int]:
    return {hour: i for i, (hour, _) in enumerate(ctx.all_hours())}


def seeds(ctx: Context) -> list[int]:
    return list(ctx.p.locked["models"]["final_model_seeds"])


def block_width(ctx: Context) -> int:
    width = ctx.p.derived.get("primary_id_block_width")
    if not width:
        raise RuntimeError("primary_id_block_width belum diisi nb09")
    return int(width)


def fixed_shallow_scores(feature_set: str, train: pl.DataFrame, tests: list[pl.DataFrame], ctx: Context) -> list[np.ndarray]:
    X, y = xy(train, feature_set)
    scores = [np.zeros(frame.height) for frame in tests]
    for seed in seeds(ctx):
        model = fit_xgb(dict(XGB_FIXED_SHALLOW), X, y, None, seed)
        for k, frame in enumerate(tests):
            scores[k] += predict(model, xy(frame, feature_set)[0]) / len(seeds(ctx))
    return scores


def pilot_scores(feature_set: str, train: pl.DataFrame, tests: list[pl.DataFrame], ctx: Context) -> list[np.ndarray]:
    X, y = xy(train, feature_set)
    scores = [np.zeros(frame.height) for frame in tests]
    for seed in ctx.p.locked["splits"]["cv_seeds"]:
        model = pilot_model(seed).fit(X, y)
        for k, frame in enumerate(tests):
            scores[k] += model.predict_proba(xy(frame, feature_set)[0])[:, 1] / len(ctx.p.locked["splits"]["cv_seeds"])
    return scores


def score_row(y: np.ndarray, score: np.ndarray, strata: np.ndarray, mask: np.ndarray, cells: np.ndarray | None = None) -> dict:
    """AP per stratum dan metrik top-k pada lengan `mask`. Semua dihitung terhadap label teramati."""
    ap = ap_by_stratum(y[mask], score[mask], strata[mask])
    row = {f"ap_{name}": ap.get(name, float("nan")) for name in REPORT_STRATA}
    row.update({f"base_{name}": float(y[mask if name == "all" else mask & (strata == name)].mean()) if (mask if name == "all" else mask & (strata == name)).any() else float("nan") for name in REPORT_STRATA})
    row.update({"n": int(mask.sum()), "n_pos": int(y[mask].sum())})
    for k in (50, 100, 500):
        row[f"p_at_{k}"], row[f"r_at_{k}"] = precision_at_k(y[mask], score[mask], k), recall_at_k(y[mask], score[mask], k)
    if cells is not None:
        row["within_cell_auc"] = within_cell_auc(y[mask], score[mask], cells[mask])
    return row


def cells_of(frame: pl.DataFrame) -> np.ndarray:
    return (frame["n_events_coarse"].cast(pl.Int32).cast(pl.String) + "_" + frame["age_bin12"].cast(pl.Int32).cast(pl.String)).to_numpy()


def ladder(ctx: Context, stage: str, data: StageData, best_params: dict) -> dict:
    """Tangga model pada lengan F1–F3. Mengembalikan baris tabel dan skor untuk bootstrap."""
    order = hour_order(ctx)
    tests = [data.test, data.f1]
    models: dict[str, list[np.ndarray]] = {"B0_rank_events": [data.test["n_events"].to_numpy().astype(float), data.f1["n_events"].to_numpy().astype(float)]}
    models["B1_age"] = fixed_shallow_scores("B1", data.train, tests, ctx)
    models["B2_xgb"] = fixed_shallow_scores("B2", data.train, tests, ctx)
    models["B2_lr"] = fit_predict("lr", {"C": 1.0}, "B2", data.train, tests, order, seeds(ctx))
    for family in ("xgb", "lr", "mlp"):
        models[f"M_behav_{family}"] = fit_predict(family, best_params[family], "M_behav", data.train, tests, order, seeds(ctx))
    models["M_robust_xgb"] = fit_predict("xgb", best_params["xgb"], "M_robust", data.train, tests, order, seeds(ctx))
    y_test, y_f1 = data.test["is_gone"].to_numpy().astype(int), data.f1["is_gone"].to_numpy().astype(int)
    rows = []
    for name, (score_test, score_f1) in models.items():
        for arm in FORWARD_ARMS:
            frame, y, score = (data.f1, y_f1, score_f1) if arm == "F1_forward" else (data.test, y_test, score_test)
            mask = arm_mask(data.train, frame, arm, ctx)
            rows.append({"model": name, "arm": arm, **score_row(y, score, frame["stratum"].to_numpy(), mask, cells_of(frame))})
    return {"rows": rows, "models": models, "y_test": y_test}


def bootstrap_gain(ctx: Context, data: StageData, score_a: np.ndarray, score_b: np.ndarray, arm: str, stratum: str | None, reps: int | None = None) -> dict:
    """Paired cluster bootstrap untuk AP(a) − AP(b) pada lengan dan stratum tertentu."""
    frame = data.test
    mask = arm_mask(data.train, frame, arm, ctx)
    if stratum:
        mask &= frame["stratum"].to_numpy() == stratum
    y = frame["is_gone"].to_numpy().astype(int)
    clusters = id_block_groups(frame["actor_id"].to_numpy(), block_width(ctx))
    observed = delta_ap_metric(y, score_a, score_b, mask)(np.arange(len(y)))
    result = paired_cluster_bootstrap(delta_ap_metric(y, score_a, score_b, mask), clusters, reps or ctx.p.locked["decision"]["bootstrap_reps"], ctx.p.project["seed"])
    largest = np.bincount(np.unique(clusters[mask], return_inverse=True)[1]).argmax()
    largest_cluster = np.unique(clusters[mask])[largest]
    without = mask & (clusters != largest_cluster)
    return {"delta": float(observed), **result, "n_clusters_with_pos": int(np.unique(clusters[mask & (y == 1)]).size), "delta_without_largest_cluster": float(delta_ap_metric(y, score_a, score_b, without)(np.arange(len(y))))}


def du_name_baselines(ctx: Context, data: StageData) -> list[dict]:
    """Baseline B3: interval ala Du et al. dan heuristik nama."""
    hours = sorted(set(data.train["hour_id"].to_list()) | set(data.test["hour_id"].to_list()), key=hour_order(ctx).get)
    intervals = du_interval_features(ctx.paths.interim, hours, 60)
    dim = pl.read_parquet(ctx.paths.processed / "account_dim.parquet", columns=["actor_id", *NAME_COLUMNS])
    train, test = data.train.join(intervals, on=["actor_id", "hour_id"], how="left").join(dim, on="actor_id", how="left"), data.test.join(intervals, on=["actor_id", "hour_id"], how="left").join(dim, on="actor_id", how="left")
    out = []
    for name, columns in {"B3_du_intervals": DU_COLUMNS, "B3_name_heuristic": NAME_COLUMNS}.items():
        X_train, X_test = train.select(columns).fill_null(0).to_numpy().astype(np.float32), test.select(columns).fill_null(0).to_numpy().astype(np.float32)
        y_train, y_test = train["is_gone"].to_numpy().astype(int), test["is_gone"].to_numpy().astype(int)
        score = np.mean([predict(fit_xgb(dict(XGB_FIXED_SHALLOW), X_train, y_train, None, seed), X_test) for seed in seeds(ctx)], axis=0)
        for arm in FORWARD_ARMS[1:]:
            out.append({"model": name, "arm": arm, **score_row(y_test, score, test["stratum"].to_numpy(), arm_mask(data.train, test, arm, ctx))})
    return out


def policy_stage(ctx: Context, stage: str, window: int, cohort: str, with_score: bool = False) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """(fit, kalibrasi, test). Tahap dev: w0, w1, w2. Tahap final: w0–w1, w2, w3."""
    data_dev = load_stage(ctx, "dev", window, cohort=cohort)
    if stage == "dev":
        fit = data_dev.train.filter(pl.col("week").is_in(["w0"]))
        return fit, data_dev.train.filter(pl.col("week").is_in(["w1"])), data_dev.test
    data = load_stage(ctx, "final", window, cohort=cohort)
    fit = data.train.filter(pl.col("week").is_in(["w0", "w1"]))
    return fit, data.train.filter(pl.col("week").is_in(["w2"])), data.test


def _align(population: np.ndarray, ids: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Menyelaraskan skor ke populasi; akun yang belum memenuhi syarat bernilai NaN."""
    out = np.full(len(population), np.nan)
    positions = {a: i for i, a in enumerate(ids.tolist())}
    for k, actor in enumerate(population.tolist()):
        if actor in positions:
            out[k] = values[positions[actor]]
    return out


def checkpoint_scores(ctx: Context, stage: str, cohort: str, feature_set: str, params: dict | None) -> dict:
    """Melatih model per checkpoint dan mengembalikan probabilitas terkalibrasi pada set kalibrasi dan test."""
    windows = ctx.p.locked["windows_minutes"]
    order = hour_order(ctx)
    calib_prob, test_prob, final = {}, {}, {}
    for c in windows:
        fit, calib, test = policy_stage(ctx, stage, c, cohort)
        X_fit, y_fit = xy(fit, feature_set)
        if params is None:
            models = [fit_xgb(dict(XGB_FIXED_SHALLOW), X_fit, y_fit, None, seed) for seed in seeds(ctx)]
        else:
            es = time_holdback(fit, order)
            models = [fit_xgb(dict(params), X_fit, y_fit, es, seed) for seed in seeds(ctx)]
        score = lambda frame: np.mean([predict(model, xy(frame, feature_set)[0]) for model in models], axis=0)  # noqa: E731
        calib_score = score(calib)
        calibrator = Calibrator(calib_score, calib["is_gone"].to_numpy().astype(int))
        final[c] = (calib["actor_id"].to_numpy(), calibrator(calib_score), test["actor_id"].to_numpy(), calibrator(score(test)))
        if c == max(windows):
            population = {"calib": calib["actor_id"].to_numpy(), "calib_y": calib["is_gone"].to_numpy().astype(int), "test": test["actor_id"].to_numpy(), "test_y": test["is_gone"].to_numpy().astype(int), "test_frame": test, "fit_last": fit}
    for c, (calib_ids, calib_values, test_ids, test_values) in final.items():
        calib_prob[c], test_prob[c] = _align(population["calib"], calib_ids, calib_values), _align(population["test"], test_ids, test_values)
    return {"calib_prob": calib_prob, "test_prob": test_prob, **population}


def policy_results(ctx: Context, scores: dict, arm: str, train_for_arm: pl.DataFrame) -> dict:
    """Memilih parameter pada kalibrasi dan mengevaluasi pada lengan test."""
    cfg = ctx.p.locked["policy"]
    grid, horizon, windows = q_grid(cfg["q_grid_size"]), cfg["aurt_horizon_minutes"], ctx.p.locked["windows_minutes"]
    calib_y, test_y = scores["calib_y"], scores["test_y"]
    mask = arm_mask(train_for_arm, scores["test_frame"], arm, ctx)
    out = {"rows": [], "best_fixed": {}, "times": {}}
    for target in cfg["target_precisions"]:
        chosen = select_q_kappa(scores["calib_prob"], calib_y, target, cfg["kappa_grid"], grid, horizon)
        if chosen is None:
            out["rows"].append({"policy": "adaptive", "target": target, "status": "target tidak tercapai pada kalibrasi"})
            continue
        times = first_cross(scores["test_prob"], thresholds(chosen["q"], chosen["kappa"], windows))
        out["rows"].append({"policy": "adaptive", "target": target, "status": "ok", "q": chosen["q"], "kappa": chosen["kappa"], "calib_aurt": chosen["aurt"], **policy_metrics(times[mask], test_y[mask], horizon)})
        out["times"][("adaptive", target)] = times
        fixed_rows = {}
        for c in windows:
            q = select_fixed(scores["calib_prob"][c], calib_y, target, grid)
            if q is None:
                continue
            fixed = fixed_times(scores["test_prob"][c], q, c)
            metrics = policy_metrics(fixed[mask], test_y[mask], horizon)
            calib_fixed = fixed_times(scores["calib_prob"][c], q, c)
            calib_aurt = aurt(calib_fixed, calib_y, horizon)
            out["rows"].append({"policy": f"fixed_{c}", "target": target, "status": "ok", "q": q, "kappa": 0.0, "calib_aurt": calib_aurt, **metrics})
            fixed_rows[c] = (calib_aurt, fixed)
        if fixed_rows:
            best_c = max(fixed_rows, key=lambda c: fixed_rows[c][0])
            out["best_fixed"][target] = best_c
            out["times"][("best_fixed", target)] = fixed_rows[best_c][1]
    out["mask"] = mask
    return out


def aurt_delta_bootstrap(ctx: Context, scores: dict, times_a: np.ndarray, times_b: np.ndarray, mask: np.ndarray, reps: int | None = None) -> dict:
    """Selisih AURT berpasangan, klaster per blok ID."""
    horizon = ctx.p.locked["policy"]["aurt_horizon_minutes"]
    y = scores["test_y"]
    clusters = id_block_groups(scores["test"], block_width(ctx))

    def metric(idx: np.ndarray) -> float:
        kept = idx[mask[idx]]
        if y[kept].sum() == 0:
            return float("nan")
        return aurt(times_a[kept], y[kept], horizon) - aurt(times_b[kept], y[kept], horizon)

    observed = metric(np.arange(len(y)))
    return {"delta": float(observed), **paired_cluster_bootstrap(metric, clusters, reps or ctx.p.locked["decision"]["bootstrap_reps"], ctx.p.project["seed"])}


def policy_sensitivity(ctx: Context, scores: dict, out: dict, target: float) -> list[dict]:
    """Sensitivitas kebijakan (docs/06): horizon lain dan precision teramati yang disamakan. Eksploratif."""
    cfg = ctx.p.locked["policy"]
    chosen = next((r for r in out["rows"] if r["policy"] == "adaptive" and r["target"] == target and r["status"] == "ok"), None)
    if chosen is None or ("best_fixed", target) not in out["times"]:
        return [{"analysis": "all", "target": target, "status": "target precision tidak tercapai pada kalibrasi"}]
    mask, y = out["mask"], scores["test_y"][out["mask"]]
    adaptive, fixed = out["times"][("adaptive", target)][mask], out["times"][("best_fixed", target)][mask]
    rows = []
    for horizon in cfg["aurt_horizon_sensitivity"]:
        a, b = aurt(adaptive, y, horizon), aurt(fixed, y, horizon)
        rows.append({"analysis": "horizon", "target": target, "status": "ok", "horizon": horizon, "aurt_adaptive": a, "aurt_best_fixed": b, "delta": a - b})
    prob = {c: values[mask] for c, values in scores["test_prob"].items()}
    matched = matched_precision(prob, y, chosen["kappa"], cfg["target_precisions"], q_grid(cfg["q_grid_size"]), cfg["aurt_horizon_minutes"])
    return rows + [{"analysis": "matched_precision", "target": target, **row} for row in matched]


def f3_sensitivity(ctx: Context, data: StageData, scores: dict[str, np.ndarray]) -> list[dict]:
    """Lengan F3 yang mengecualikan blok ID berisi akun train apa pun, yaitu bagian test yang tidak bertetangga dengan train (docs/06)."""
    arm = "F3_train_any_block"
    mask = forward_arm(data.train, data.test, "F3_forward_batch_excluded", block_width(ctx), "train_any_block")
    if not mask.any():
        return [{"arm": arm, "model": name, "n": 0, "n_pos": 0} for name in scores]
    y, strata = data.test["is_gone"].to_numpy().astype(int), data.test["stratum"].to_numpy()
    return [{"arm": arm, "model": name, **score_row(y, score, strata, mask)} for name, score in scores.items()]


def rates_by_week(data: StageData) -> list[dict]:
    """Tingkat hilang per minggu dan stratum, untuk sensitivitas selisih masa tunggu (docs/01)."""
    columns = ["week", "stratum", "is_gone"]
    frame = pl.concat([data.train.select(columns), data.test.select(columns)])
    return frame.group_by("week", "stratum").agg(pl.len().alias("n"), pl.col("is_gone").sum().alias("n_gone"), pl.col("is_gone").mean().alias("rate")).sort("week", "stratum").to_dicts()


def latency_table(ctx: Context, stage: str, best_params: dict) -> list[dict]:
    """AP per jendela pada kohort tetap dan deployable. Lengan F2."""
    windows, order, rows = ctx.p.locked["windows_minutes"], hour_order(ctx), []
    for cohort in ("fixed", "deployable"):
        reference = load_stage(ctx, stage, 60, cohort=cohort)
        for w in windows:
            data = load_stage(ctx, stage, w, cohort=cohort)
            for name, feature_set, params in (("B2", "B2", None), ("M_behav", "M_behav", best_params["xgb"])):
                score = fixed_shallow_scores(feature_set, data.train, [data.test], ctx)[0] if params is None else fit_predict("xgb", params, feature_set, data.train, [data.test], order, seeds(ctx))[0]
                if cohort == "fixed":
                    test_frame = reference.test
                    aligned = _align(test_frame["actor_id"].to_numpy(), data.test["actor_id"].to_numpy(), score)
                    aligned = np.where(np.isnan(aligned), np.nanmin(score) - 1.0, aligned)
                    frame, values = test_frame, aligned
                else:
                    frame, values = data.test, score
                y = frame["is_gone"].to_numpy().astype(int)
                mask = arm_mask(reference.train, frame, "F2_forward_new_accounts", ctx)
                rows.append({"cohort": cohort, "window": w, "model": name, **score_row(y, values, frame["stratum"].to_numpy(), mask)})
    return rows


def coordination_ladder(ctx: Context, stage: str, best_params: dict) -> dict:
    """Ablasi M_behav, M_proxy, M_coord pada akun dan lengan yang sama."""
    order = hour_order(ctx)
    data = load_stage(ctx, stage, 60, with_blocks=True)
    scores = {name: fit_predict("xgb", best_params["xgb"], name, data.train, [data.test], order, seeds(ctx))[0] for name in ("M_behav", "M_proxy", "M_coord")}
    y = data.test["is_gone"].to_numpy().astype(int)
    rows = []
    for arm in FORWARD_ARMS[1:]:
        mask = arm_mask(data.train, data.test, arm, ctx)
        for name, score in scores.items():
            rows.append({"model": name, "arm": arm, **score_row(y, score, data.test["stratum"].to_numpy(), mask), "n_pos_in_blocks": int(y[mask & (data.test["in_any_block"].to_numpy() == 1)].sum())})
    return {"rows": rows, "scores": scores, "data": data, "y": y}


__all__ = ["FEATURE_SETS", "FORWARD_ARMS", "NOT_FLAGGED", "REPORT_STRATA", "amoc_curve", "aurt_delta_bootstrap", "block_width", "bootstrap_gain", "cells_of", "checkpoint_scores", "coordination_ladder", "du_name_baselines", "hour_order", "ladder", "latency_table", "pilot_scores", "policy_results", "score_row", "seeds"]
