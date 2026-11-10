import numpy as np
import polars as pl
import pytest

from ghremoval.features.dense_blocks import BLOCK_COLUMNS, TENSOR_SCHEMA, block_density, block_features, build_tensor, peel_blocks


def tensor_of(rows):
    return pl.DataFrame(rows, schema=TENSOR_SCHEMA, orient="row")


def test_build_tensor_respects_cutoff_and_bots():
    events = pl.DataFrame({"actor_id": [1, 1, 2, 3], "is_app_bot": [False, False, True, False], "second_of_hour": [10, 400, 10, 299], "event_type": ["PushEvent"] * 4, "repo_id": [5, 5, 5, 6]})
    out = build_tensor(events, 5).sort("actor_id")
    assert out["actor_id"].to_list() == [1, 3] and out["minute"].to_list() == [0, 4] and out["count"].to_list() == [1, 1]


def test_block_density_and_features():
    block = tensor_of([(1, 10, "PushEvent", 0, 4), (2, 10, "PushEvent", 0, 4)])
    assert block_density(block) == pytest.approx(8 / ((2 + 1 + 1 + 1) / 4))
    tensor = pl.concat([block, tensor_of([(1, 11, "WatchEvent", 1, 2), (3, 12, "PushEvent", 5, 1)])])
    out = block_features([block], tensor, 20).sort("actor_id")
    assert out.columns == ["actor_id", *BLOCK_COLUMNS]
    assert out["in_any_block"].to_list() == [1.0, 1.0, 0.0] and out["best_block_rank"].to_list() == [1.0, 1.0, 21.0]
    assert out["share_events_in_blocks"].to_list() == pytest.approx([4 / 6, 1.0, 0.0]) and out["n_event_types_in_best_block"].to_list() == [1.0, 1.0, 0.0]


def test_block_features_without_blocks():
    out = block_features([], tensor_of([(1, 10, "PushEvent", 0, 1)]), 20)
    assert out["in_any_block"].to_list() == [0.0] and out["best_block_rank"].to_list() == [21.0]


def injected_tensor(seed=1):
    rng = np.random.default_rng(seed)
    injected = [(100 + a, 900 + r, "PushEvent", m, 5) for a in range(20) for r in range(3) for m in range(3)]
    noise = {(int(rng.integers(1000, 3000)), int(rng.integers(1000, 3000)), str(rng.choice(["WatchEvent", "ForkEvent"])), int(rng.integers(0, 60))) for _ in range(3000)}
    return tensor_of(injected + [(*row, 1) for row in noise]), {100 + a for a in range(20)}


def test_peeling_finds_injected_block_exactly():
    tensor, expected = injected_tensor()
    blocks = peel_blocks(tensor, 3)
    assert set(blocks[0]["actor_id"].to_list()) == expected
    assert blocks[0]["repo_id"].n_unique() == 3 and blocks[0]["minute"].n_unique() == 3 and blocks[0]["event_type"].n_unique() == 1
    assert block_density(blocks[0]) == pytest.approx(900 / ((20 + 3 + 1 + 3) / 4))


def test_peeling_deflates_so_blocks_do_not_overlap():
    tensor, _ = injected_tensor(2)
    blocks = peel_blocks(tensor, 4)
    seen = pl.concat(blocks).select("actor_id", "repo_id", "event_type", "minute")
    assert seen.is_duplicated().sum() == 0 and sum(b.height for b in blocks) == seen.height


def test_peeling_two_cross_type_blocks_rank_by_density():
    strong = [(1 + a, 50, t, 0, 9) for a in range(5) for t in ("PushEvent", "CreateEvent")]
    weak = [(20 + a, 60, "WatchEvent", 3, 2) for a in range(5)]
    blocks = peel_blocks(tensor_of(strong + weak), 2)
    assert set(blocks[0]["actor_id"].to_list()) == {1, 2, 3, 4, 5} and blocks[0]["event_type"].n_unique() == 2
    assert set(blocks[1]["actor_id"].to_list()) == set(range(20, 25))


def test_peeling_empty_tensor():
    assert peel_blocks(tensor_of([]), 5) == []
