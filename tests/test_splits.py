import numpy as np
import polars as pl

from ghremoval.correlogram import autocorrelation_range, choose_block_width, residual_correlogram
from ghremoval.splits import artifact_groups, batch_excluded_ids, diagnose, forward_arm, id_block_groups, signature_groups, stratified_group_folds


def test_id_blocks_do_not_chain():
    ids = np.array([100, 4999, 5000, 9999, 10000])
    assert id_block_groups(ids, 5000).tolist() == [0, 0, 1, 1, 2]


def test_artifact_groups_union_only_shared_members():
    groups = artifact_groups(5, [np.array([0, 1]), np.array([1, 2])])
    assert groups[0] == groups[1] == groups[2] and groups[3] != groups[0] and groups[3] != groups[4]


def test_signature_groups_are_singletons_below_threshold():
    groups = signature_groups(np.array([12, 12, 3, 3]), np.array([2, 2, 1, 1]), np.array([4, 4, 1, 1]), 10)
    assert groups[0] == groups[1] and groups[2] != groups[3]


def test_diagnose_flags_giant_positive_group():
    groups = np.array([0] * 8 + [1, 2])
    y = np.array([1] * 8 + [0, 1])
    folds = np.array([0] * 8 + [1, 2])
    result = diagnose(groups, y, folds, 0.25)
    assert result["is_degenerate"] is True and result["largest_group"] == 8 and abs(result["max_fold_pos_share"] - 8 / 9) < 1e-9
    assert diagnose(np.arange(10), y, None, 0.25)["is_degenerate"] is False


def test_folds_are_deterministic_and_keep_groups_together():
    rng = np.random.default_rng(0)
    groups = rng.integers(0, 50, 500)
    y = rng.integers(0, 2, 500)
    a, b = stratified_group_folds(groups, y, 5, 42), stratified_group_folds(groups, y, 5, 42)
    assert (a == b).all()
    assert all(len(set(a[groups == g])) == 1 for g in np.unique(groups))


def test_batch_exclusion_uses_only_training_positives():
    mask = batch_excluded_ids(np.array([100, 5100, 10100]), np.array([200, 5200]), np.array([1, 0]), 5000)
    assert mask.tolist() == [True, False, False]
    assert batch_excluded_ids(np.array([5100]), np.array([200, 5200]), np.array([1, 0]), 5000, "train_any_block").tolist() == [True]


def test_forward_arms():
    train = pl.DataFrame({"actor_id": [1, 2], "is_gone": [True, False]})
    test = pl.DataFrame({"actor_id": [1, 3, 5003, 12000]})
    assert forward_arm(train, test, "F1_forward", None).all()
    assert forward_arm(train, test, "F2_forward_new_accounts", None).tolist() == [False, True, True, True]
    assert forward_arm(train, test, "F3_forward_batch_excluded", 5000).tolist() == [False, False, True, True]


def test_block_width_rule():
    assert choose_block_width([5000, 20000, 100000], 12000) == 20000
    assert choose_block_width([5000, 20000, 100000], 300000) == 100000
    assert choose_block_width([5000, 20000, 100000], float("inf")) == 100000
    assert autocorrelation_range([{"low": 100, "corr": 0.2}, {"low": 1000, "corr": 0.01}]) == 1000


def test_correlogram_detects_short_range_structure():
    rng = np.random.default_rng(3)
    ids = np.sort(rng.choice(10_000_000, 20_000, replace=False))
    blocks = ids // 2000
    effect = rng.normal(size=blocks.max() + 1)[blocks]
    residuals = effect + rng.normal(scale=0.5, size=len(ids))
    table = residual_correlogram(ids, residuals)
    near = [row["corr"] for row in table if row["high"] <= 1000]
    far = [row["corr"] for row in table if row["low"] >= 50000]
    assert np.mean(near) > 0.3 and abs(np.mean(far)) < 0.1
