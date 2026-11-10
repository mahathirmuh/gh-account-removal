from types import SimpleNamespace

import numpy as np
import polars as pl
import pytest

from ghremoval.analysis import _align, cells_of, f3_sensitivity, policy_sensitivity, rates_by_week, score_row


def policy_ctx():
    return SimpleNamespace(p=SimpleNamespace(locked={"policy": {"aurt_horizon_sensitivity": [65, 90], "target_precisions": [0.5], "q_grid_size": 5, "aurt_horizon_minutes": 75}}))


def test_policy_sensitivity_recomputes_aurt_for_other_horizons():
    times = {("adaptive", 0.5): np.array([5.0, np.inf, 60.0]), ("best_fixed", 0.5): np.array([60.0, np.inf, 60.0])}
    out = {"rows": [{"policy": "adaptive", "target": 0.5, "status": "ok", "kappa": 0.0}], "times": times, "mask": np.ones(3, dtype=bool)}
    scores = {"test_y": np.array([1, 0, 1]), "test_prob": {5: np.array([0.9, 0.1, 0.1]), 60: np.array([0.9, 0.1, 0.8])}}
    rows = policy_sensitivity(policy_ctx(), scores, out, 0.5)
    horizon = [r for r in rows if r["analysis"] == "horizon"]
    assert [r["horizon"] for r in horizon] == [65, 90] and horizon[0]["delta"] == pytest.approx(55 / 130)
    assert {r["analysis"] for r in rows} == {"horizon", "matched_precision"}


def test_policy_sensitivity_reports_missing_target():
    out = {"rows": [], "times": {}, "mask": np.ones(1, dtype=bool)}
    assert policy_sensitivity(policy_ctx(), {}, out, 0.5)[0]["status"].startswith("target precision")


def test_f3_sensitivity_drops_blocks_with_any_training_account():
    ctx = SimpleNamespace(p=SimpleNamespace(derived={"primary_id_block_width": 5000}))
    train = pl.DataFrame({"actor_id": [1], "is_gone": [False]})
    test = pl.DataFrame({"actor_id": [3, 5003, 5004, 5005], "is_gone": [True, True, False, False], "stratum": ["5-19"] * 4})
    rows = f3_sensitivity(ctx, SimpleNamespace(train=train, test=test), {"m": np.array([0.9, 0.8, 0.2, 0.1])})
    assert rows[0]["n"] == 3 and rows[0]["n_pos"] == 1 and rows[0]["ap_5-19"] == pytest.approx(1.0)
    only_near = SimpleNamespace(train=train, test=test.head(1))
    assert f3_sensitivity(ctx, only_near, {"m": np.array([0.9])}) == [{"arm": "F3_train_any_block", "model": "m", "n": 0, "n_pos": 0}]


def test_rates_by_week_groups_week_and_stratum():
    train = pl.DataFrame({"week": ["w0", "w0"], "stratum": ["5-19", "5-19"], "is_gone": [True, False], "extra": [1, 2]})
    test = pl.DataFrame({"week": ["w3"], "stratum": ["20+"], "is_gone": [True]})
    rows = rates_by_week(SimpleNamespace(train=train, test=test))
    assert rows == [{"week": "w0", "stratum": "5-19", "n": 2, "n_gone": 1, "rate": 0.5}, {"week": "w3", "stratum": "20+", "n": 1, "n_gone": 1, "rate": 1.0}]


def test_align_marks_unseen_accounts_nan():
    out = _align(np.array([1, 2, 3]), np.array([3, 1]), np.array([0.3, 0.1]))
    assert out[0] == 0.1 and np.isnan(out[1]) and out[2] == 0.3


def test_cells_of_combines_activity_and_age():
    frame = pl.DataFrame({"n_events_coarse": [2.0, 3.0], "age_bin12": [1.0, 0.0]})
    assert cells_of(frame).tolist() == ["2_1", "3_0"]


def test_score_row_respects_mask_and_reports_base_rate():
    y = np.array([1, 0, 1, 0, 1])
    score = np.array([0.9, 0.1, 0.8, 0.7, 0.2])
    strata = np.array(["5-19", "5-19", "20+", "20+", "5-19"])
    mask = np.array([True, True, True, True, False])
    row = score_row(y, score, strata, mask)
    assert row["n"] == 4 and row["n_pos"] == 2 and row["base_all"] == 0.5 and row["base_5-19"] == 0.5 and row["ap_5-19"] == 1.0
