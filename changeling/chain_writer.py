"""
chain_writer.py — Append-only block writer.

The chain only grows. This is philosophically important, not just technical.
History cannot be rewritten. Mistakes are recorded, not erased.

Every write goes through the WAL first:
  1. Compute block (hash, prev_hash, timestamp)
  2. Log to WAL as pending
  3. Insert into SQLite
  4. Log to WAL as committed
  5. Return the written block

The hash covers: layer, layer_type, timestamp, prev_hash, compressed_state,
fault, reasoning, commitment_level. The consequence field is deliberately
excluded — it is filled later by Malkuth feedback and must not alter the
block's identity hash.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from changeling.wal import WriteAheadLog


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def compute_hash(
    layer: int,
    layer_type: str,
    timestamp: str,
    prev_hash: str,
    compressed_state: str,
    fault: Optional[str],
    reasoning: str,
    commitment_level: str,
) -> str:
    """
    Deterministic SHA-256 over the block's immutable fields.
    consequence is NOT included — it is mutable Malkuth feedback.
    """
    canonical = json.dumps(
        {
            "layer": layer,
            "layer_type": layer_type,
            "timestamp": timestamp,
            "prev_hash": prev_hash,
            "compressed_state": compressed_state,
            "fault": fault,
            "reasoning": reasoning,
            "commitment_level": commitment_level,
        },
        sort_keys=True,
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Genesis
# ---------------------------------------------------------------------------

def ensure_genesis(conn: sqlite3.Connection, wal: WriteAheadLog) -> None:
    """
    Create the genesis block if the chain is empty.
    The genesis block anchors the chain — every block's prev_hash traces
    back to it. prev_hash is "" because there is nothing before the beginning.
    """
    count = conn.execute("SELECT COUNT(*) FROM chain_blocks").fetchone()[0]
    if count == 0:
        append_block(
            conn=conn,
            wal=wal,
            layer=0,
            layer_type="genesis",
            compressed_state="Chain memory initialised.",
            reasoning="Chain memory initialised.",
            commitment_level="sealed",
        )


# ---------------------------------------------------------------------------
# Block writer
# ---------------------------------------------------------------------------

def append_block(
    conn: sqlite3.Connection,
    wal: WriteAheadLog,
    layer: int,
    layer_type: str,
    compressed_state: str,
    reasoning: str,
    fault: Optional[str] = None,
    commitment_level: str = "experimental",
    timestamp: Optional[str] = None,
) -> dict:
    """
    Append a new block to the chain. Returns the full block as a dict.

    Raises:
      ValueError  if commitment_level is not 'sealed' or 'experimental'.
      RuntimeError if the chain tip's hash doesn't match the stored prev_hash
                   (chain corruption detected before write).
    """
    if commitment_level not in ("sealed", "experimental"):
        raise ValueError(
            f"commitment_level must be 'sealed' or 'experimental', got {commitment_level!r}"
        )

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    # Fetch the chain tip — its hash becomes our prev_hash.
    tip_row = conn.execute(
        "SELECT this_hash FROM chain_blocks ORDER BY id DESC LIMIT 1"
    ).fetchone()
    prev_hash = tip_row["this_hash"] if tip_row else ""

    this_hash = compute_hash(
        layer, layer_type, timestamp, prev_hash,
        compressed_state, fault, reasoning, commitment_level,
    )

    block = {
        "layer": layer,
        "layer_type": layer_type,
        "timestamp": timestamp,
        "prev_hash": prev_hash,
        "compressed_state": compressed_state,
        "fault": fault,
        "reasoning": reasoning,
        "consequence": None,
        "commitment_level": commitment_level,
        "this_hash": this_hash,
    }

    # WAL: record pending BEFORE touching SQLite.
    entry_id = wal.log_pending(block)

    conn.execute(
        """
        INSERT INTO chain_blocks
            (layer, layer_type, timestamp, prev_hash, compressed_state,
             fault, reasoning, consequence, commitment_level, this_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            layer, layer_type, timestamp, prev_hash, compressed_state,
            fault, reasoning, None, commitment_level, this_hash,
        ),
    )
    conn.commit()

    # WAL: record committed AFTER SQLite commit.
    wal.log_committed(entry_id, this_hash)

    return block


# ---------------------------------------------------------------------------
# Consequence update (Malkuth feedback — the only permitted mutation)
# ---------------------------------------------------------------------------

def record_consequence(
    conn: sqlite3.Connection,
    this_hash: str,
    consequence: str,
) -> None:
    """
    Fill in the consequence field for an existing block.

    This is the ONLY permitted mutation on the chain. The consequence field
    was deliberately left out of the hash precisely so Malkuth feedback can
    be recorded without breaking the chain's integrity.

    Raises ValueError if no block with the given hash is found.
    """
    rows = conn.execute(
        "SELECT id FROM chain_blocks WHERE this_hash = ?", (this_hash,)
    ).fetchone()
    if not rows:
        raise ValueError(f"No block found with hash {this_hash!r}")

    conn.execute(
        "UPDATE chain_blocks SET consequence = ? WHERE this_hash = ?",
        (consequence, this_hash),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Chain integrity verifier
# ---------------------------------------------------------------------------

def verify_chain(conn: sqlite3.Connection) -> tuple[bool, Optional[str]]:
    """
    Walk every block in order and verify:
      1. prev_hash matches the previous block's this_hash (or "" for genesis).
      2. this_hash matches the recomputed hash of the block's immutable fields.

    Returns (True, None) if intact, (False, reason_string) on first failure.
    """
    rows = conn.execute(
        "SELECT * FROM chain_blocks ORDER BY id ASC"
    ).fetchall()

    expected_prev = ""

    for row in rows:
        b = dict(row)

        if b["prev_hash"] != expected_prev:
            return False, (
                f"Block id={b['id']}: prev_hash mismatch "
                f"(expected {expected_prev!r}, got {b['prev_hash']!r})"
            )

        recomputed = compute_hash(
            b["layer"], b["layer_type"], b["timestamp"], b["prev_hash"],
            b["compressed_state"], b["fault"], b["reasoning"],
            b["commitment_level"],
        )
        if recomputed != b["this_hash"]:
            return False, (
                f"Block id={b['id']}: this_hash mismatch "
                f"(stored {b['this_hash']!r}, recomputed {recomputed!r})"
            )

        expected_prev = b["this_hash"]

    return True, None
