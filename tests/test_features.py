import math

import polars as pl
import pytest

from ghremoval.features.behaviour import BEHAVIOUR_COLUMNS, PROXY_COLUMNS, TYPES, account_behaviour, window_features


def events(rows):
    defaults = {"is_app_bot": False, "event_type": "PushEvent", "repo_id": 1, "repo_owner_is_actor": True, "has_org": False, "repo_short_len": 4, "repo_short_has_digit": False,
                "repo_short_hash": "a", "ref_type": None, "push_size": 1, "push_distinct_size": 1, "pr_author_none": None}
    schema = {"actor_id": pl.Int64, "is_app_bot": pl.Boolean, "second_of_hour": pl.Int32, "event_type": pl.String, "repo_id": pl.Int64, "repo_owner_is_actor": pl.Boolean, "has_org": pl.Boolean,
              "repo_short_len": pl.Int32, "repo_short_has_digit": pl.Boolean, "repo_short_hash": pl.String, "ref_type": pl.String, "push_size": pl.Int32, "push_distinct_size": pl.Int32, "pr_author_none": pl.Boolean}
    return pl.DataFrame([{**defaults, **r} for r in rows], schema=schema)


def commits(rows):
    schema = {"actor_id": pl.Int64, "second_of_hour": pl.Int32, "msg_hash": pl.String, "msg_len": pl.Int32}
    return pl.DataFrame(rows, schema=schema) if rows else pl.DataFrame(schema=schema)


def feature(values, name):
    return values[BEHAVIOUR_COLUMNS.index(name)]


def test_single_event_account_uses_zero_gap():
    v = account_behaviour([10], ["PushEvent"], [1], [True], [False], [4], [False], ["a"], [None], [2], [2], [None], [])
    assert len(v) == 48 == len(BEHAVIOUR_COLUMNS)
    assert feature(v, "gap_mean") == 0 and feature(v, "share_zero_gap") == 1 and feature(v, "share_modal_gap") == 1 and feature(v, "pr_author_none_ratio") == -1


def test_known_values_two_repos():
    seconds = [0, 10, 10, 70]
    types = ["PushEvent", "PushEvent", "CreateEvent", "PullRequestEvent"]
    v = account_behaviour(seconds, types, [1, 1, 2, 2], [True, True, False, False], [True, False, False, False], [2, 4, 6, 8], [True, False, False, False], ["a", "a", "b", "c"],
                          [None, None, "branch", None], [3, 1, None, None], [3, 0, None, None], [None, None, None, True], [("h", 4), ("h", 2), ("k", 6)])
    assert feature(v, f"share_{TYPES[0]}") == 0.5 and feature(v, "n_event_types") == 3
    assert feature(v, "n_active_minutes") == 2 and feature(v, "max_events_per_minute") == 3 and feature(v, "span_seconds") == 70
    assert feature(v, "gap_mean") == pytest.approx(70 / 3) and feature(v, "gap_min") == 0 and feature(v, "share_zero_gap") == pytest.approx(1 / 3)
    assert feature(v, "n_repos") == 2 and feature(v, "repo_entropy") == pytest.approx(math.log(2)) and feature(v, "share_own_repo") == 0.5 and feature(v, "share_org_events") == 0.25
    assert feature(v, "push_size_sum") == 4 and feature(v, "push_size_max") == 3 and feature(v, "push_distinct_ratio") == pytest.approx(0.75)
    assert feature(v, "n_commit_msgs") == 3 and feature(v, "msg_unique_ratio") == pytest.approx(2 / 3) and feature(v, "msg_len_mean") == 4 and feature(v, "msg_top_share") == pytest.approx(2 / 3)
    assert feature(v, "n_new_branches") == 1 and feature(v, "pr_author_none_ratio") == 1
    assert feature(v, "repo_short_len_mean") == 5 and feature(v, "repo_short_digit_share") == 0.25 and feature(v, "repo_short_unique_per_event") == 0.75


def test_events_after_cutoff_do_not_change_window_features():
    base = [{"actor_id": 1, "second_of_hour": 10}, {"actor_id": 2, "second_of_hour": 20, "repo_id": 1}]
    later = base + [{"actor_id": 1, "second_of_hour": 400, "repo_id": 9}, {"actor_id": 3, "second_of_hour": 500, "repo_id": 1}]
    cm_base = [{"actor_id": 1, "second_of_hour": 10, "msg_hash": "m", "msg_len": 2}]
    cm_later = cm_base + [{"actor_id": 3, "second_of_hour": 500, "msg_hash": "m", "msg_len": 2}]
    a = window_features(events(base), commits(cm_base), 5).sort("actor_id")
    b = window_features(events(later), commits(cm_later), 5).sort("actor_id")
    assert a.equals(b)


def test_proxies_count_other_accounts_within_window():
    ev = events([{"actor_id": 1, "second_of_hour": 1}, {"actor_id": 2, "second_of_hour": 2}, {"actor_id": 3, "second_of_hour": 3, "repo_id": 2, "repo_short_hash": "z"}])
    cm = commits([{"actor_id": 1, "second_of_hour": 1, "msg_hash": "m", "msg_len": 1}, {"actor_id": 2, "second_of_hour": 2, "msg_hash": "m", "msg_len": 1}])
    out = window_features(ev, cm, 5).sort("actor_id")
    assert out["msg_others_max"].to_list() == [1.0, 1.0, -1.0] and out["repo_others_max"].to_list() == [1.0, 1.0, 0.0]
    assert out["repo_any_shared"].to_list() == [1.0, 1.0, 0.0] and out["msg_share_1_50"].to_list() == [1.0, 1.0, -1.0]
    assert all(c in out.columns for c in PROXY_COLUMNS)


def test_bots_excluded_from_features_and_proxies():
    ev = events([{"actor_id": 1, "second_of_hour": 1}, {"actor_id": 9, "second_of_hour": 2, "is_app_bot": True}])
    out = window_features(ev, commits([]), 5)
    assert out["actor_id"].to_list() == [1] and out["repo_others_max"].to_list() == [0.0]


def test_labels_are_not_an_input():
    import inspect
    assert not any("label" in name or name == "y" for name in inspect.signature(window_features).parameters)
