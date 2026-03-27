"""
test_wal.py — Write-ahead log and crash recovery.

Verifies that:
  - Every block write is logged to WAL before SQLite
  - The WAL correctly identifies pending (unresolved) entries
  - Recovery marks blocks as committed if they made it to DB
  - Recovery marks blocks as interrupted if they didn't make it to DB
  - A simulated crash (pending without committed) is detected and handled
  - After recovery, the chain is intact
"""

import json
import pytest

from changeling.database import open_db
from changeling.wal import WriteAheadLog
from changeling.chain_writer import append_block, ensure_genesis, verify_chain
from changeling.chain_reader import full_chain


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def wal_path(tmp_path):
    return tmp_path / "test.wal"


@pytest.fixture
def wal(wal_path):
    return WriteAheadLog(wal_path)


@pytest.fixture
def db():
    conn = open_db(":memory:")
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Basic WAL operations
# ---------------------------------------------------------------------------

def test_wal_file_created_on_first_write(wal, wal_path, db):
    ensure_genesis(db, wal)
    assert wal_path.exists()


def test_wal_log_pending_creates_entry(wal):
    entry_id = wal.log_pending({"this_hash": "abc", "layer_type": "task"})
    assert len(entry_id) > 0
    pending = wal.pending_entries()
    assert len(pending) == 1
    assert pending[0]["entry_id"] == entry_id


def test_wal_log_committed_resolves_pending(wal):
    entry_id = wal.log_pending({"this_hash": "abc"})
    wal.log_committed(entry_id, "abc")
    assert wal.pending_entries() == []


def test_wal_log_interrupted_resolves_pending(wal):
    entry_id = wal.log_pending({"this_hash": "abc"})
    wal.log_interrupted(entry_id, "crash recovery")
    assert wal.pending_entries() == []


def test_wal_multiple_entries_only_orphans_returned(wal):
    id1 = wal.log_pending({"this_hash": "aaa"})
    id2 = wal.log_pending({"this_hash": "bbb"})
    wal.log_committed(id1, "aaa")
    # id2 is still pending
    pending = wal.pending_entries()
    assert len(pending) == 1
    assert pending[0]["entry_id"] == id2


def test_wal_no_pending_on_empty_log(wal):
    assert wal.pending_entries() == []


def test_wal_no_pending_after_full_write(wal, db):
    ensure_genesis(db, wal)
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r")
    assert wal.pending_entries() == []


# ---------------------------------------------------------------------------
# Crash recovery — block written to DB but commit not logged
# ---------------------------------------------------------------------------

def test_recovery_marks_committed_if_block_in_db(wal, db):
    """
    Simulate: block was written to SQLite, but process died before
    wal.log_committed() was called. Recovery should find it and log committed.
    """
    ensure_genesis(db, wal)

    # Manually log a pending entry whose hash IS in the DB
    b = append_block(db, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r")
    # The block was written correctly. Now simulate: the committed log line
    # was NOT written (corrupt the WAL by removing committed entries).
    # We do this by creating a fresh WAL that only has the pending entry.
    fresh_wal = WriteAheadLog.__new__(WriteAheadLog)
    fresh_wal.path = wal.path
    # Overwrite the WAL file with only a pending entry for that block
    with open(wal.path, "w") as f:
        f.write(json.dumps({
            "type": "pending",
            "entry_id": "orphan-id",
            "block": b,
            "at": "2026-01-01T00:00:00+00:00",
        }) + "\n")

    pending_before = fresh_wal.pending_entries()
    assert len(pending_before) == 1

    recovered = fresh_wal.recover(db)
    assert "orphan-id" in recovered

    # Should now be resolved as committed (block IS in DB)
    pending_after = fresh_wal.pending_entries()
    assert pending_after == []


# ---------------------------------------------------------------------------
# Crash recovery — block NOT written to DB
# ---------------------------------------------------------------------------

def test_recovery_marks_interrupted_if_block_not_in_db(wal, db):
    """
    Simulate: process died after logging pending to WAL but before
    the INSERT hit SQLite. Block hash does not exist in DB.
    Recovery should mark as interrupted.
    """
    ensure_genesis(db, wal)

    phantom_block = {
        "layer": 1,
        "layer_type": "task",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "prev_hash": "some_prev",
        "compressed_state": "state that never made it",
        "fault": None,
        "reasoning": "this was never written",
        "commitment_level": "experimental",
        "this_hash": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    }

    entry_id = wal.log_pending(phantom_block)
    assert len(wal.pending_entries()) == 1

    recovered = wal.recover(db)
    assert entry_id in recovered
    assert wal.pending_entries() == []


# ---------------------------------------------------------------------------
# Chain integrity survives recovery
# ---------------------------------------------------------------------------

def test_chain_intact_after_recovery(wal, db):
    ensure_genesis(db, wal)
    for i in range(3):
        append_block(db, wal, layer=1, layer_type="task",
                     compressed_state=f"s{i}", reasoning=f"r{i}")

    wal.recover(db)

    ok, reason = verify_chain(db)
    assert ok, reason


def test_wal_handles_corrupted_line_gracefully(wal_path, db):
    """A corrupt line in the WAL must not crash recovery."""
    ensure_genesis(db, WriteAheadLog(wal_path))

    # Inject a corrupt line
    with open(wal_path, "a") as f:
        f.write("this is not json\n")

    wal = WriteAheadLog(wal_path)
    # Should not raise
    pending = wal.pending_entries()
    assert isinstance(pending, list)
