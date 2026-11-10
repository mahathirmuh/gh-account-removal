import gzip
import json

import polars as pl
import pytest

from ghremoval.build.accounts import assign_stratum, mark_first_in_period
from ghremoval.config import load_context
from ghremoval.ingest.gharchive import hour_quality, iter_events
from ghremoval.parse.events import hash_msg, normalize_short, parse_event, pseudo
from ghremoval.quality import pii_columns
from ghremoval.secrets import Secret

KEY = b"kunci-uji"
BASE = {"id": "1", "public": True, "created_at": "2024-04-09T03:12:34Z", "actor": {"id": 7, "login": "Alice"}, "repo": {"id": 9, "name": "Alice/repo42"}}


def event(event_type, payload, **extra):
    return {**BASE, "type": event_type, "payload": payload, **extra}


def parse(raw):
    return parse_event(raw, KEY, "2024-04-09-3", "w0", {})


def test_iter_events_and_quality_count_bad_lines(tmp_path):
    path = tmp_path / "x.json.gz"
    with gzip.open(path, "wb") as handle:
        handle.write(json.dumps({"created_at": "2024-04-09T03:00:01Z"}).encode() + b"\n")
        handle.write(b"{rusak\n")
        handle.write(json.dumps({"created_at": "2024-04-09T03:59:59Z"}).encode() + b"\n")
    assert sum(1 for e in iter_events(path) if e is None) == 1
    quality = hour_quality(path)
    assert quality["n_lines"] == 3 and quality["n_bad"] == 1 and quality["n_minutes"] == 2


def test_parse_push_drops_pii_and_hashes_message():
    raw = event("PushEvent", {"size": 25, "distinct_size": 24, "commits": [{"message": "  fix  ", "author": {"email": "a@users.noreply.github.com"}, "distinct": True}]})
    row, commits, actor = parse(raw)
    flat = json.dumps([row, commits, actor])
    assert "noreply.github.com" not in flat and "Alice" not in flat
    assert row[4] == 12 * 60 + 34 and row[12] is True and row[18] == 25
    assert commits[0][4] == hash_msg("fix") and commits[0][5] == 3 and commits[0][6] is True


def test_parse_pull_request_author_none_only_on_opened():
    opened = event("PullRequestEvent", {"action": "opened", "pull_request": {"author_association": "NONE"}})
    closed = event("PullRequestEvent", {"action": "closed", "pull_request": {"author_association": "NONE"}})
    assert parse(opened)[0][20] is True and parse(closed)[0][20] is None


@pytest.mark.parametrize("etype,payload,idx,expected", [("CreateEvent", {"ref_type": "branch"}, 17, "branch"), ("WatchEvent", {"action": "started"}, 6, "started"), ("ForkEvent", {}, 5, "ForkEvent"), ("PublicEvent", {}, 5, "PublicEvent")])
def test_parse_other_event_types(etype, payload, idx, expected):
    assert parse(event(etype, payload))[0][idx] == expected


def test_bot_flag_org_flag_and_login_features():
    raw = event("WatchEvent", {}, actor={"id": 1, "login": "dep-a1[bot]"}, org={"id": 3})
    row, _, actor = parse(raw)
    assert row[9] is True and row[16] is True
    assert actor[3] == len("dep-a1[bot]") and actor[5] == 1


def test_normalize_short_and_pseudo():
    assert normalize_short("ReaDme2") == "readme2"
    assert pseudo("alice", KEY) != pseudo("bob", KEY) and len(pseudo("alice", KEY)) == 16


def test_assign_stratum_boundaries():
    strata = [[1, 1], [2, 4], [5, 19], [20, None]]
    assert [assign_stratum(n, strata) for n in (1, 2, 4, 5, 19, 20, 900)] == ["1", "2-4", "2-4", "5-19", "5-19", "20+", "20+"]


def test_mark_first_in_period():
    df = pl.DataFrame({"actor_id": [1, 1, 1, 1], "hour_id": ["h0", "h1", "h2", "h3"], "week": ["dev", "w0", "w1", "w3"]})
    out = mark_first_in_period(df, {"h0": 0, "h1": 1, "h2": 2, "h3": 3})
    assert out["is_first_in_period"].to_list() == [True, True, False, True]


def test_pii_columns_and_secret_repr():
    assert pii_columns(["actor_login", "msg_hash", "login_len"]) == ["actor_login"]
    assert "abc" not in repr(Secret("abc")) and "abc" not in str(Secret("abc"))


def test_config_loads():
    ctx = load_context()
    assert len(ctx.all_hours()) == 25 and ctx.weeks_of("train") == ["w0", "w1"]
