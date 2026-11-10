import polars as pl
import pytest

from ghremoval.config import load_context
from ghremoval.github_client import GitHubClient
from ghremoval.labels import HoldoutLockedError, legacy_node_id, load_labels, parse_batch
from ghremoval.secrets import Secret


def test_legacy_node_id_matches_observed_value():
    assert legacy_node_id(26939949) == "MDQ6VXNlcjI2OTM5OTQ5"


def test_parse_batch_statuses():
    response = {"data": {"nodes": [{"__typename": "User", "createdAt": "2020-01-01T00:00:00Z"}, None, {"__typename": "Organization", "createdAt": "2021-01-01T00:00:00Z"}, None]},
                "errors": [{"path": ["nodes", 1], "type": "NOT_FOUND"}, {"path": ["nodes", 3], "type": "SERVICE_UNAVAILABLE"}],
                "extensions": {"warnings": [{"type": "DEPRECATION"}]}}
    rows, stats = parse_batch("s1", [1, 2, 3, 4], response, "t")
    assert [row[2] for row in rows] == ["present", "gone", "present", "error"]
    assert rows[1][4] is True and rows[3][4] is False and rows[2][3] == "Organization"
    assert stats["warn_DEPRECATION"] == 1


def test_parse_batch_without_data_is_error():
    rows, stats = parse_batch("s1", [1, 2], {"data": None, "errors": [{"message": "x"}]}, "t")
    assert all(row[2] == "error" for row in rows) and stats["no_data"] == 1


@pytest.mark.parametrize("url", ["https://evil.example/repos/x", "http://api.github.com/user/1", "https://api.github.com.evil.example/user/1"])
def test_client_rejects_non_api_urls(url):
    client = GitHubClient(Secret("rahasia"), "ua")
    with pytest.raises(ValueError):
        client.get(url)


def test_client_does_not_expose_token():
    assert "rahasia" not in repr(GitHubClient(Secret("rahasia"), "ua").__dict__["_token"])


def test_load_labels_blocks_holdout():
    ctx = load_context()
    assert ctx.p.holdout_open is False
    with pytest.raises(HoldoutLockedError):
        load_labels(ctx, "holdout")
