"""
test_queries.py — Chain reader query methods.

Tests every query path in chain_reader:
  - by_layer
  - by_type
  - by_time_range
  - by_fault
  - latest
  - full_chain
  - walk_back
"""

import pytest

from changeling.database import open_db
from changeling.wal import WriteAheadLog
from changeling.chain_writer import append_block, ensure_genesis
from changeling.chain_reader import (
    by_layer,
    by_type,
    by_time_range,
    by_fault,
    latest,
    full_chain,
    walk_back,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def wal(tmp_path):
    return WriteAheadLog(tmp_path / "test.wal")


@pytest.fixture
def db():
    conn = open_db(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def chain(db, wal):
    """DB with genesis + several typed blocks."""
    ensure_genesis(db, wal)
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="task A", reasoning="do task A",
                 timestamp="2026-01-01T10:00:00+00:00")
    append_block(db, wal, layer=1, layer_type="reflection",
                 compressed_state="reflect A", reasoning="reflect on task A",
                 timestamp="2026-01-01T10:30:00+00:00")
    append_block(db, wal, layer=2, layer_type="task",
                 compressed_state="task B", reasoning="do task B",
                 timestamp="2026-01-01T11:00:00+00:00")
    append_block(db, wal, layer=2, layer_type="task",
                 compressed_state="task C", reasoning="do task C",
                 fault="timeout during task C",
                 timestamp="2026-01-01T12:00:00+00:00")
    return db


# ---------------------------------------------------------------------------
# by_layer
# ---------------------------------------------------------------------------

def test_by_layer_returns_correct_blocks(chain):
    results = by_layer(chain, 1)
    assert len(results) == 2
    assert all(b["layer"] == 1 for b in results)


def test_by_layer_excludes_genesis(chain):
    results = by_layer(chain, 0)
    assert len(results) == 1
    assert results[0]["layer_type"] == "genesis"


def test_by_layer_empty_for_unknown(chain):
    assert by_layer(chain, 99) == []


def test_by_layer_oldest_first(chain):
    results = by_layer(chain, 1)
    ids = [b["id"] for b in results]
    assert ids == sorted(ids)


# ---------------------------------------------------------------------------
# by_type
# ---------------------------------------------------------------------------

def test_by_type_task(chain):
    results = by_type(chain, "task")
    assert len(results) == 3  # task A, task B, task C
    assert all(b["layer_type"] == "task" for b in results)


def test_by_type_reflection(chain):
    results = by_type(chain, "reflection")
    assert len(results) == 1


def test_by_type_unknown_returns_empty(chain):
    assert by_type(chain, "nonexistent") == []


# ---------------------------------------------------------------------------
# by_time_range
# ---------------------------------------------------------------------------

def test_by_time_range_inclusive(chain):
    results = by_time_range(
        chain,
        "2026-01-01T10:00:00+00:00",
        "2026-01-01T10:30:00+00:00",
    )
    types = [b["layer_type"] for b in results]
    assert "task" in types
    assert "reflection" in types


def test_by_time_range_exclusive_of_outside(chain):
    results = by_time_range(
        chain,
        "2026-01-01T11:00:00+00:00",
        "2026-01-01T12:00:00+00:00",
    )
    # Should get task B and task C, not task A or reflection
    assert len(results) == 2
    assert all(b["layer"] == 2 for b in results)


def test_by_time_range_empty_window(chain):
    results = by_time_range(
        chain,
        "2025-01-01T00:00:00+00:00",
        "2025-06-01T00:00:00+00:00",
    )
    assert results == []


# ---------------------------------------------------------------------------
# by_fault
# ---------------------------------------------------------------------------

def test_by_fault_returns_only_faulted(chain):
    results = by_fault(chain)
    assert len(results) == 1
    assert results[0]["fault"] == "timeout during task C"


def test_by_fault_substring_filter(chain):
    results = by_fault(chain, "timeout")
    assert len(results) == 1


def test_by_fault_no_match_substring(chain):
    results = by_fault(chain, "nonexistent_error")
    assert results == []


def test_by_fault_empty_on_clean_chain(db, wal):
    ensure_genesis(db, wal)
    assert by_fault(db) == []


# ---------------------------------------------------------------------------
# latest
# ---------------------------------------------------------------------------

def test_latest_returns_last_block(chain):
    block = latest(chain)
    assert block is not None
    assert block["compressed_state"] == "task C"


def test_latest_on_empty_chain_returns_none(db):
    assert latest(db) is None


def test_latest_after_genesis_is_genesis(db, wal):
    ensure_genesis(db, wal)
    block = latest(db)
    assert block["layer_type"] == "genesis"


# ---------------------------------------------------------------------------
# full_chain
# ---------------------------------------------------------------------------

def test_full_chain_order(chain):
    blocks = full_chain(chain)
    ids = [b["id"] for b in blocks]
    assert ids == sorted(ids)


def test_full_chain_count(chain):
    # genesis + task A + reflection + task B + task C
    assert len(full_chain(chain)) == 5


def test_full_chain_empty(db):
    assert full_chain(db) == []


# ---------------------------------------------------------------------------
# walk_back
# ---------------------------------------------------------------------------

def test_walk_back_from_tip(chain):
    tip = latest(chain)
    walked = walk_back(chain, tip["this_hash"], n=3)
    assert len(walked) == 3
    # Most-recent first
    assert walked[0]["this_hash"] == tip["this_hash"]


def test_walk_back_reaches_genesis(chain):
    tip = latest(chain)
    walked = walk_back(chain, tip["this_hash"], n=100)
    # Last block in the walk should be genesis
    assert walked[-1]["layer_type"] == "genesis"
    assert walked[-1]["prev_hash"] == ""


def test_walk_back_invalid_hash_raises(chain):
    with pytest.raises(ValueError):
        walk_back(chain, "nonexistent_hash")


def test_walk_back_from_genesis(chain):
    genesis_hash = full_chain(chain)[0]["this_hash"]
    walked = walk_back(chain, genesis_hash, n=10)
    assert len(walked) == 1
    assert walked[0]["layer_type"] == "genesis"


def test_walk_back_respects_n_limit(chain):
    tip = latest(chain)
    walked = walk_back(chain, tip["this_hash"], n=2)
    assert len(walked) == 2
