"""
Phase 1 — Chain memory core.

Append-only SQLite chain. Each block is hash-linked to the previous,
making the chain tamper-evident. Reasoning is first-class data.

Block structure:
  id             — autoincrement rowid
  layer          — int (which architectural layer wrote this block)
  layer_type     — str (e.g. "task", "reflection", "sleep", "fault")
  timestamp      — ISO8601 UTC
  prev_hash      — SHA-256 of the previous block's this_hash (or "GENESIS")
  compressed_state — str (state snapshot / compressed payload)
  fault          — str or NULL (fault description if this block records one)
  reasoning      — str (first-class reasoning, not a comment)
  this_hash      — SHA-256 of the canonical fields of this block
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS chain_blocks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    layer            INTEGER NOT NULL,
    layer_type       TEXT    NOT NULL,
    timestamp        TEXT    NOT NULL,
    prev_hash        TEXT    NOT NULL,
    compressed_state TEXT    NOT NULL,
    fault            TEXT,
    reasoning        TEXT    NOT NULL,
    this_hash        TEXT    NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_layer_type ON chain_blocks (layer_type);
CREATE INDEX IF NOT EXISTS idx_fault      ON chain_blocks (fault)
    WHERE fault IS NOT NULL;
"""


def init_db(path: str | Path) -> sqlite3.Connection:
    """Open (or create) the chain DB and ensure the schema exists."""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def _compute_hash(
    layer: int,
    layer_type: str,
    timestamp: str,
    prev_hash: str,
    compressed_state: str,
    fault: Optional[str],
    reasoning: str,
) -> str:
    """Deterministic SHA-256 over the block's canonical fields."""
    canonical = json.dumps(
        {
            "layer": layer,
            "layer_type": layer_type,
            "timestamp": timestamp,
            "prev_hash": prev_hash,
            "compressed_state": compressed_state,
            "fault": fault,
            "reasoning": reasoning,
        },
        sort_keys=True,
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Block writer
# ---------------------------------------------------------------------------

def append_block(
    conn: sqlite3.Connection,
    layer: int,
    layer_type: str,
    compressed_state: str,
    reasoning: str,
    fault: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> dict:
    """
    Append a new block to the chain and return the full block as a dict.
    Raises ValueError if the computed hash collides (should never happen).
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    # Fetch the hash of the most recent block (the chain tip).
    row = conn.execute(
        "SELECT this_hash FROM chain_blocks ORDER BY id DESC LIMIT 1"
    ).fetchone()
    prev_hash = row["this_hash"] if row else "GENESIS"

    this_hash = _compute_hash(
        layer, layer_type, timestamp, prev_hash, compressed_state, fault, reasoning
    )

    conn.execute(
        """
        INSERT INTO chain_blocks
            (layer, layer_type, timestamp, prev_hash,
             compressed_state, fault, reasoning, this_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (layer, layer_type, timestamp, prev_hash,
         compressed_state, fault, reasoning, this_hash),
    )
    conn.commit()

    return {
        "layer": layer,
        "layer_type": layer_type,
        "timestamp": timestamp,
        "prev_hash": prev_hash,
        "compressed_state": compressed_state,
        "fault": fault,
        "reasoning": reasoning,
        "this_hash": this_hash,
    }


# ---------------------------------------------------------------------------
# Block reader
# ---------------------------------------------------------------------------

def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def read_by_layer(conn: sqlite3.Connection, layer: int) -> list[dict]:
    """Return all blocks for a given layer, oldest first."""
    rows = conn.execute(
        "SELECT * FROM chain_blocks WHERE layer = ? ORDER BY id ASC", (layer,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def read_by_type(conn: sqlite3.Connection, layer_type: str) -> list[dict]:
    """Return all blocks of a given layer_type, oldest first."""
    rows = conn.execute(
        "SELECT * FROM chain_blocks WHERE layer_type = ? ORDER BY id ASC",
        (layer_type,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def read_by_fault(conn: sqlite3.Connection, fault_substring: Optional[str] = None) -> list[dict]:
    """
    Return all blocks that have a non-null fault field.
    If fault_substring is given, filter to blocks whose fault contains it.
    """
    if fault_substring:
        rows = conn.execute(
            "SELECT * FROM chain_blocks WHERE fault LIKE ? ORDER BY id ASC",
            (f"%{fault_substring}%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM chain_blocks WHERE fault IS NOT NULL ORDER BY id ASC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def read_recent(conn: sqlite3.Connection, n: int = 3) -> list[dict]:
    """Return the n most recent blocks, returned oldest-first."""
    rows = conn.execute(
        "SELECT * FROM chain_blocks ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    return [_row_to_dict(r) for r in reversed(rows)]


def read_all(conn: sqlite3.Connection) -> list[dict]:
    """Return all blocks, oldest first."""
    rows = conn.execute(
        "SELECT * FROM chain_blocks ORDER BY id ASC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Fault checker
# ---------------------------------------------------------------------------

def check_faults(conn: sqlite3.Connection, layer_type: str) -> list[dict]:
    """
    Pre-task lookup: return all past fault blocks for a given layer_type.
    Call this before starting a task to surface prior failures of the same type.
    """
    return read_by_fault(conn) if not layer_type else [
        b for b in read_by_fault(conn) if b["layer_type"] == layer_type
    ]


# ---------------------------------------------------------------------------
# Chain integrity verifier
# ---------------------------------------------------------------------------

def verify_chain(conn: sqlite3.Connection) -> tuple[bool, Optional[str]]:
    """
    Walk every block in order and verify:
      1. this_hash matches recomputed hash of fields.
      2. prev_hash matches the previous block's this_hash.

    Returns (True, None) if intact, (False, reason) on first failure.
    """
    blocks = read_all(conn)
    expected_prev = "GENESIS"

    for b in blocks:
        if b["prev_hash"] != expected_prev:
            return False, (
                f"Block id={b['id']}: prev_hash mismatch "
                f"(expected {expected_prev!r}, got {b['prev_hash']!r})"
            )

        recomputed = _compute_hash(
            b["layer"], b["layer_type"], b["timestamp"],
            b["prev_hash"], b["compressed_state"], b["fault"], b["reasoning"],
        )
        if recomputed != b["this_hash"]:
            return False, (
                f"Block id={b['id']}: this_hash mismatch "
                f"(stored {b['this_hash']!r}, recomputed {recomputed!r})"
            )

        expected_prev = b["this_hash"]

    return True, None
