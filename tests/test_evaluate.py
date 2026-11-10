import numpy as np
import polars as pl
import pytest

from ghremoval.data import apply_age_bins, cohort_mask, fit_age_edges
from ghremoval.evaluate import ap_by_stratum, cluster_indices, delta_ap_metric, holm, paired_cluster_bootstrap, precision_at_k, recall_at_k, within_cell_auc


def test_ap_by_stratum_handles_strata():
    y, score = np.array([1, 0, 1, 0]), np.array([0.9, 0.1, 0.8, 0.2])
    out = ap_by_stratum(y, score, np.array(["5-19", "5-19", "20+", "20+"]))
    assert out["all"] == 1.0 and out["5-19"] == 1.0 and "1" not in out


def test_within_cell_auc_manual():
    y = np.array([1, 0, 1, 0, 1, 1])
    score = np.array([0.9, 0.1, 0.2, 0.8, 0.5, 0.4])
    cells = np.array(["a", "a", "b", "b", "c", "c"])
    # sel a AUC 1 (1 positif), sel b AUC 0 (1 positif), sel c hanya positif sehingga dilewati
    assert within_cell_auc(y, score, cells) == pytest.approx(0.5)


def test_precision_and_recall_at_k_deterministic_on_ties():
    y, score = np.array([1, 0, 0, 1]), np.ones(4)
    assert precision_at_k(y, score, 2, seed=3) == precision_at_k(y, score, 2, seed=3)
    assert recall_at_k(y, np.array([4.0, 3.0, 2.0, 1.0]), 1) == 0.5


def test_cluster_bootstrap_keeps_whole_clusters():
    clusters = np.array([1, 1, 2, 2, 2, 3])
    assert sorted(len(g) for g in cluster_indices(clusters)) == [1, 2, 3]
    seen = []

    def metric(idx):
        seen.append(np.bincount(clusters[idx], minlength=4))
        return 1.0

    result = paired_cluster_bootstrap(metric, clusters, 25, seed=1)
    assert result["n_reps"] == 25 and result["low"] == 1.0 and result["p_one_sided"] == 0.0
    assert all(c[1] % 2 == 0 and c[2] % 3 == 0 for c in seen)


def test_delta_ap_metric_is_zero_for_identical_scores():
    y, score = np.array([1, 0, 1, 0]), np.array([0.9, 0.1, 0.2, 0.8])
    assert delta_ap_metric(y, score, score, np.ones(4, bool))(np.arange(4)) == 0.0


def test_holm_manual():
    out = holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": float("nan")})
    assert out["a"] == pytest.approx(0.03) and out["c"] == pytest.approx(0.06) and out["b"] == pytest.approx(0.06) and np.isnan(out["d"])


def test_age_edges_come_only_from_training_frame():
    train = pl.DataFrame({"id_recency": list(range(100))})
    edges = fit_age_edges(train["id_recency"].to_numpy(), 4)
    test = apply_age_bins(pl.DataFrame({"id_recency": [0, 99, 10000]}), edges)
    assert test["age_bin12"].to_list() == [0.0, 3.0, 3.0]


def test_cohort_mask():
    frame = pl.DataFrame({"in_fixed_cohort": [True, False], "n_events_w": [2, 3]})
    assert cohort_mask(frame, "fixed", 3).tolist() == [True, False] and cohort_mask(frame, "deployable", 3).tolist() == [False, True]
