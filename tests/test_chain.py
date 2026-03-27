"""
Phase 1 tests — chain memory core.
Uses an in-memory SQLite database so no files are created on disk.
"""

import pytest
import sqlite3
from core.chain_memory import (
    init_db,
    append_block,
    read_by_layer,
    read_by_type,
    read_by_fault,
    read_recent,
    read_all,
    check_faults,
    verify_chain,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """Fresh in-memory chain DB for each test."""
    conn = init_db(":memory:")
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def test_init_creates_table(db):
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chain_blocks'"
    ).fetchone()
    assert row is not None


# ---------------------------------------------------------------------------
# Block writer
# ---------------------------------------------------------------------------

def test_append_single_block(db):
    block = append_block(db, layer=1, layer_type="task",
                         compressed_state="state_a", reasoning="reason_a")
    assert block["prev_hash"] == "GENESIS"
    assert block["this_hash"] and len(block["this_hash"]) == 64
    assert block["fault"] is None


def test_append_chains_prev_hash(db):
    b1 = append_block(db, layer=1, layer_type="task",
                      compressed_state="s1", reasoning="r1")
    b2 = append_block(db, layer=1, layer_type="task",
                      compressed_state="s2", reasoning="r2")
    assert b2["prev_hash"] == b1["this_hash"]


def test_append_with_fault(db):
    block = append_block(db, layer=2, layer_type="reflection",
                         compressed_state="s", reasoning="r",
                         fault="null_pointer in module X")
    assert block["fault"] == "null_pointer in module X"


def test_append_is_append_only(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    # Attempting a direct UPDATE should not affect the chain reader
    db.execute("UPDATE chain_blocks SET compressed_state='tampered' WHERE id=1")
    ok, reason = verify_chain(db)
    assert not ok  # tamper detected


def test_unique_hashes(db):
    b1 = append_block(db, layer=1, layer_type="task",
                      compressed_state="s1", reasoning="r1",
                      timestamp="2026-01-01T00:00:00+00:00")
    b2 = append_block(db, layer=1, layer_type="task",
                      compressed_state="s2", reasoning="r2",
                      timestamp="2026-01-01T00:00:01+00:00")
    assert b1["this_hash"] != b2["this_hash"]


# ---------------------------------------------------------------------------
# Block reader — by layer
# ---------------------------------------------------------------------------

def test_read_by_layer(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    append_block(db, layer=2, layer_type="task", compressed_state="s", reasoning="r")
    append_block(db, layer=1, layer_type="task", compressed_state="s2", reasoning="r2")

    layer1 = read_by_layer(db, 1)
    assert len(layer1) == 2
    assert all(b["layer"] == 1 for b in layer1)


def test_read_by_layer_empty(db):
    assert read_by_layer(db, 99) == []


# ---------------------------------------------------------------------------
# Block reader — by type
# ---------------------------------------------------------------------------

def test_read_by_type(db):
    append_block(db, layer=1, layer_type="task",       compressed_state="s", reasoning="r")
    append_block(db, layer=1, layer_type="reflection", compressed_state="s", reasoning="r")
    append_block(db, layer=1, layer_type="task",       compressed_state="s", reasoning="r")

    tasks = read_by_type(db, "task")
    assert len(tasks) == 2
    assert all(b["layer_type"] == "task" for b in tasks)


# ---------------------------------------------------------------------------
# Block reader — by fault
# ---------------------------------------------------------------------------

def test_read_by_fault_all(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r",
                 fault="timeout error")
    append_block(db, layer=2, layer_type="sleep", compressed_state="s", reasoning="r",
                 fault="hash mismatch")

    faults = read_by_fault(db)
    assert len(faults) == 2


def test_read_by_fault_substring(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r",
                 fault="timeout error")
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r",
                 fault="hash mismatch")

    results = read_by_fault(db, "timeout")
    assert len(results) == 1
    assert "timeout" in results[0]["fault"]


def test_read_by_fault_none_when_clean(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    assert read_by_fault(db) == []


# ---------------------------------------------------------------------------
# Block reader — recent
# ---------------------------------------------------------------------------

def test_read_recent(db):
    for i in range(5):
        append_block(db, layer=1, layer_type="task",
                     compressed_state=f"s{i}", reasoning=f"r{i}")
    recent = read_recent(db, 3)
    assert len(recent) == 3
    # Oldest-first ordering within the returned window
    assert recent[0]["compressed_state"] == "s2"
    assert recent[2]["compressed_state"] == "s4"


def test_read_recent_fewer_than_n(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    assert len(read_recent(db, 10)) == 1


# ---------------------------------------------------------------------------
# Fault checker (pre-task lookup)
# ---------------------------------------------------------------------------

def test_check_faults_finds_matching_type(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r",
                 fault="bad input")
    append_block(db, layer=1, layer_type="reflection", compressed_state="s", reasoning="r",
                 fault="loop overflow")

    task_faults = check_faults(db, "task")
    assert len(task_faults) == 1
    assert task_faults[0]["layer_type"] == "task"


def test_check_faults_empty_for_clean_type(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    assert check_faults(db, "task") == []


def test_check_faults_no_type_returns_all(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r",
                 fault="err1")
    append_block(db, layer=2, layer_type="sleep", compressed_state="s", reasoning="r",
                 fault="err2")
    all_faults = check_faults(db, "")
    assert len(all_faults) == 2


# ---------------------------------------------------------------------------
# Chain integrity verifier
# ---------------------------------------------------------------------------

def test_verify_clean_chain(db):
    for i in range(4):
        append_block(db, layer=1, layer_type="task",
                     compressed_state=f"s{i}", reasoning=f"r{i}")
    ok, reason = verify_chain(db)
    assert ok
    assert reason is None


def test_verify_detects_hash_tampering(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    db.execute("UPDATE chain_blocks SET this_hash='deadbeef' WHERE id=1")
    ok, reason = verify_chain(db)
    assert not ok
    assert reason is not None


def test_verify_detects_content_tampering(db):
    append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    db.execute("UPDATE chain_blocks SET reasoning='altered' WHERE id=1")
    ok, reason = verify_chain(db)
    assert not ok


def test_verify_empty_chain(db):
    ok, reason = verify_chain(db)
    assert ok
    assert reason is None


def test_genesis_block_has_no_prev(db):
    b = append_block(db, layer=1, layer_type="task", compressed_state="s", reasoning="r")
    assert b["prev_hash"] == "GENESIS"


# ---------------------------------------------------------------------------
# Read all
# ---------------------------------------------------------------------------

def test_read_all_order(db):
    for i in range(3):
        append_block(db, layer=1, layer_type="task",
                     compressed_state=f"s{i}", reasoning=f"r{i}")
    blocks = read_all(db)
    ids = [b["id"] for b in blocks]
    assert ids == sorted(ids)
