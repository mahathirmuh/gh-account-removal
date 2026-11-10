import numpy as np
import polars as pl
import pytest

from ghremoval.audit import cohen_kappa, draw_sample
from ghremoval.models.fit import time_holdback
from ghremoval.policy import aurt, first_cross, fixed_times, policy_metrics, q_grid, select_fixed, select_q_kappa, thresholds
from ghremoval.pu import elkan_noto_fit, hide_positives, pu_bagging_fit, bagging_score, sar_em_fit, naive_fit


def test_first_cross_flags_at_earliest_checkpoint_and_never_before_visible():
    prob = {5: np.array([0.9, np.nan, 0.1]), 10: np.array([0.1, 0.8, 0.2]), 60: np.array([0.95, 0.9, 0.1])}
    times = first_cross(prob, {5: 0.5, 10: 0.5, 60: 0.5})
    assert times.tolist() == [5.0, 10.0, np.inf]


def test_aurt_matches_fixed_window_formula():
    y = np.array([1, 1, 0, 1])
    times = fixed_times(np.array([0.9, 0.2, 0.9, 0.9]), 0.5, 15)
    assert aurt(times, y, 75) == pytest.approx((2 / 3) * (75 - 15) / 75)


def test_thresholds_grow_with_kappa_for_early_checkpoints():
    low, high = thresholds(0.4, 0.0, [5, 60]), thresholds(0.4, 0.5, [5, 60])
    assert high[5] > low[5] and high[60] == low[60]
    assert thresholds(0.9, 0.5, [5])[5] == 1.0


def test_select_q_kappa_rejects_unreachable_target():
    y = np.array([0, 0, 1, 0])
    prob = {5: np.array([0.9, 0.9, 0.1, 0.9]), 60: np.array([0.9, 0.9, 0.1, 0.9])}
    assert select_q_kappa(prob, y, 0.9, [0.0, 0.5], q_grid(99), 75) is None


def test_select_q_kappa_prefers_earlier_flags():
    y = np.array([1, 1, 0, 0])
    prob = {5: np.array([0.9, 0.2, 0.1, 0.1]), 60: np.array([0.9, 0.9, 0.1, 0.1])}
    best = select_q_kappa(prob, y, 0.9, [0.0, 0.5], q_grid(99), 75)
    assert best["precision"] == 1.0 and best["recall"] == 1.0


def test_select_fixed_finds_smallest_valid_threshold():
    y = np.array([1, 1, 0])
    assert select_fixed(np.array([0.9, 0.8, 0.3]), y, 0.9, np.array([0.1, 0.5, 0.85])) == 0.5
    assert policy_metrics(np.array([5.0, np.inf, np.inf]), y, 75)["n_flagged"] == 1


def test_time_holdback_takes_last_hours():
    frame = pl.DataFrame({"hour_id": ["a"] * 2 + ["b"] * 2 + ["c"] * 2})
    assert time_holdback(frame, {"a": 0, "b": 1, "c": 2}, 0.3).tolist() == [False, False, False, False, True, True]


def synthetic_pu(seed=0, n=3000):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 4))
    y = (X[:, 0] + X[:, 1] > 0.8).astype(int)
    labeled = rng.random(n) < 0.5
    return X, y, (y == 1) & labeled


def test_elkan_noto_recovers_label_frequency():
    X, _, s = synthetic_pu()
    _, c = elkan_noto_fit(X, s.astype(int), 0)
    assert 0.3 < c < 0.75


def test_pu_methods_rank_hidden_positives_above_chance():
    from sklearn.metrics import roc_auc_score
    X, y, s = synthetic_pu(1)
    s_int = s.astype(int)
    hidden = (y == 1) & ~s
    unlabeled = ~s
    scores = {"naive": naive_fit(X, s_int, 0).predict_proba(X)[:, 1], "bag": bagging_score(pu_bagging_fit(X, s_int, 0, n_bags=5), X), "sar": sar_em_fit(X, s_int, X[:, [0]], 0, iterations=2)[0].predict_proba(X)[:, 1]}
    for name, score in scores.items():
        assert roc_auc_score(hidden[unlabeled], score[unlabeled]) > 0.85, name


def test_hide_positives_hits_target_and_is_deterministic():
    rng = np.random.default_rng(0)
    s = (rng.random(4000) < 0.4).astype(int)
    features = rng.normal(size=(4000, 2))
    a, b = hide_positives(s, features, 0.5, 7), hide_positives(s, features, 0.5, 7)
    assert (a == b).all() and abs(a.sum() / s.sum() - 0.5) < 0.06 and not a[s == 0].any()


def test_cohen_kappa_manual():
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "a", "b", "b"]) == 1.0
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == pytest.approx(0.0)


def test_draw_sample_is_deterministic_and_balanced():
    frame = pl.DataFrame({"actor_id": list(range(100)), "hour_id": ["h"] * 100, "stratum": ["5-19"] * 60 + ["20+"] * 40, "actor_pseudo": [str(i) for i in range(100)]})
    score = np.arange(100.0)
    a = draw_sample(frame, score, 10, 10, 3)
    b = draw_sample(frame, score, 10, 10, 3)
    assert a[0].equals(b[0]) and a[1]["score_group"].value_counts().height == 2
