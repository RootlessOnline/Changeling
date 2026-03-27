"""
test_chain.py — Chain integrity, append-only guarantee, genesis block.

These tests verify the foundational guarantees of chain memory:
  - The chain starts with a genesis block
  - Each block correctly links to the previous via prev_hash
  - Hashes are recomputed correctly
  - Tampering is detected
  - The chain is truly append-only (existing blocks cannot be changed
    without breaking integrity)
  - consequence field can be updated (the sole permitted mutation)
"""

import pytest
import sqlite3

from changeling.database import open_db
from changeling.wal import WriteAheadLog
from changeling.chain_writer import (
    append_block,
    ensure_genesis,
    verify_chain,
    record_consequence,
    compute_hash,
)
from changeling.chain_reader import full_chain, latest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def wal(tmp_path):
    return WriteAheadLog(tmp_path / "test.wal")


@pytest.fixture
def db():
    """Fresh in-memory chain DB per test."""
    conn = open_db(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def db_with_genesis(db, wal):
    ensure_genesis(db, wal)
    return db


# ---------------------------------------------------------------------------
# Genesis block
# ---------------------------------------------------------------------------

def test_genesis_created_on_empty_chain(db, wal):
    ensure_genesis(db, wal)
    blocks = full_chain(db)
    assert len(blocks) == 1
    g = blocks[0]
    assert g["layer"] == 0
    assert g["layer_type"] == "genesis"
    assert g["prev_hash"] == ""
    assert g["reasoning"] == "Chain memory initialised."
    assert g["commitment_level"] == "sealed"


def test_genesis_not_duplicated(db, wal):
    ensure_genesis(db, wal)
    ensure_genesis(db, wal)  # second call must be a no-op
    assert len(full_chain(db)) == 1


def test_genesis_hash_is_valid(db, wal):
    ensure_genesis(db, wal)
    g = full_chain(db)[0]
    expected = compute_hash(
        g["layer"], g["layer_type"], g["timestamp"], g["prev_hash"],
        g["compressed_state"], g["fault"], g["reasoning"], g["commitment_level"],
    )
    assert g["this_hash"] == expected


# ---------------------------------------------------------------------------
# Block chaining
# ---------------------------------------------------------------------------

def test_first_non_genesis_block_links_to_genesis(db_with_genesis, wal):
    genesis = full_chain(db_with_genesis)[0]
    b = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r")
    assert b["prev_hash"] == genesis["this_hash"]


def test_blocks_chain_sequentially(db_with_genesis, wal):
    b1 = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                      compressed_state="s1", reasoning="r1")
    b2 = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                      compressed_state="s2", reasoning="r2")
    assert b2["prev_hash"] == b1["this_hash"]


def test_each_block_has_unique_hash(db_with_genesis, wal):
    b1 = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                      compressed_state="s1", reasoning="r1",
                      timestamp="2026-01-01T00:00:00+00:00")
    b2 = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                      compressed_state="s2", reasoning="r2",
                      timestamp="2026-01-01T00:00:01+00:00")
    assert b1["this_hash"] != b2["this_hash"]


def test_consequence_defaults_to_none(db_with_genesis, wal):
    b = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r")
    assert b["consequence"] is None


def test_commitment_level_sealed(db_with_genesis, wal):
    b = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r",
                     commitment_level="sealed")
    assert b["commitment_level"] == "sealed"


def test_commitment_level_default_is_experimental(db_with_genesis, wal):
    b = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r")
    assert b["commitment_level"] == "experimental"


def test_invalid_commitment_level_raises(db_with_genesis, wal):
    with pytest.raises(ValueError):
        append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r",
                     commitment_level="maybe")


# ---------------------------------------------------------------------------
# Chain integrity
# ---------------------------------------------------------------------------

def test_verify_clean_chain(db_with_genesis, wal):
    for i in range(4):
        append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state=f"s{i}", reasoning=f"r{i}")
    ok, reason = verify_chain(db_with_genesis)
    assert ok
    assert reason is None


def test_verify_empty_chain(db):
    ok, reason = verify_chain(db)
    assert ok
    assert reason is None


def test_verify_detects_content_tampering(db_with_genesis, wal):
    append_block(db_with_genesis, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r")
    db_with_genesis.execute(
        "UPDATE chain_blocks SET reasoning = 'tampered' WHERE layer_type = 'task'"
    )
    ok, reason = verify_chain(db_with_genesis)
    assert not ok
    assert reason is not None


def test_verify_detects_hash_tampering(db_with_genesis, wal):
    append_block(db_with_genesis, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r")
    db_with_genesis.execute(
        "UPDATE chain_blocks SET this_hash = 'deadbeef' WHERE layer_type = 'task'"
    )
    ok, reason = verify_chain(db_with_genesis)
    assert not ok


def test_verify_detects_prev_hash_break(db_with_genesis, wal):
    append_block(db_with_genesis, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r")
    db_with_genesis.execute(
        "UPDATE chain_blocks SET prev_hash = 'broken' WHERE layer_type = 'task'"
    )
    ok, reason = verify_chain(db_with_genesis)
    assert not ok


# ---------------------------------------------------------------------------
# Append-only guarantee
# ---------------------------------------------------------------------------

def test_consequence_is_the_only_permitted_mutation(db_with_genesis, wal):
    """
    Updating consequence must not break chain integrity because consequence
    is excluded from the hash. All other mutations break the chain.
    """
    b = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r")
    record_consequence(db_with_genesis, b["this_hash"], "output was good")
    ok, reason = verify_chain(db_with_genesis)
    assert ok, reason


def test_consequence_update_on_missing_hash_raises(db_with_genesis):
    with pytest.raises(ValueError):
        record_consequence(db_with_genesis, "nonexistent_hash", "irrelevant")


def test_cannot_insert_duplicate_hash(db_with_genesis, wal):
    b = append_block(db_with_genesis, wal, layer=1, layer_type="task",
                     compressed_state="s", reasoning="r",
                     timestamp="2026-01-01T00:00:00+00:00")
    with pytest.raises(sqlite3.IntegrityError):
        db_with_genesis.execute(
            """INSERT INTO chain_blocks
               (layer, layer_type, timestamp, prev_hash, compressed_state,
                reasoning, commitment_level, this_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (b["layer"], b["layer_type"], b["timestamp"], b["prev_hash"],
             b["compressed_state"], b["reasoning"], b["commitment_level"],
             b["this_hash"]),
        )
