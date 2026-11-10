import numpy as np
import polars as pl

from ghremoval.analysis import _align, cells_of, score_row


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
