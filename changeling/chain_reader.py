"""
chain_reader.py — Query the chain. Read-only.

All queries return dicts (not sqlite3.Row objects) so callers don't need
to know about the database layer.

Query surface:
  - by_layer(layer)           — all blocks at a given layer number
  - by_type(layer_type)       — all blocks of a given type
  - by_time_range(start, end) — all blocks within an ISO8601 time window
  - by_fault(substring)       — all blocks with a non-null fault field
  - latest()                  — the most recent block
  - full_chain()              — all blocks, oldest first
  - walk_back(this_hash, n)   — walk the chain backwards from a block
"""

import sqlite3
from typing import Optional


def _row(row: sqlite3.Row) -> dict:
    return dict(row)


def _rows(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def by_layer(conn: sqlite3.Connection, layer: int) -> list[dict]:
    """All blocks at the given layer number, oldest first."""
    return _rows(conn.execute(
        "SELECT * FROM chain_blocks WHERE layer = ? ORDER BY id ASC",
        (layer,),
    ).fetchall())


def by_type(conn: sqlite3.Connection, layer_type: str) -> list[dict]:
    """All blocks of the given layer_type, oldest first."""
    return _rows(conn.execute(
        "SELECT * FROM chain_blocks WHERE layer_type = ? ORDER BY id ASC",
        (layer_type,),
    ).fetchall())


def by_time_range(
    conn: sqlite3.Connection,
    start: str,
    end: str,
) -> list[dict]:
    """
    All blocks whose timestamp falls within [start, end] (ISO8601 strings,
    inclusive), oldest first. Relies on ISO8601 lexicographic ordering.
    """
    return _rows(conn.execute(
        "SELECT * FROM chain_blocks WHERE timestamp >= ? AND timestamp <= ? ORDER BY id ASC",
        (start, end),
    ).fetchall())


def by_fault(
    conn: sqlite3.Connection,
    substring: Optional[str] = None,
) -> list[dict]:
    """
    All blocks that have a non-null fault field, oldest first.
    If substring is given, further filters to blocks whose fault contains it.
    """
    if substring:
        return _rows(conn.execute(
            "SELECT * FROM chain_blocks WHERE fault LIKE ? ORDER BY id ASC",
            (f"%{substring}%",),
        ).fetchall())
    return _rows(conn.execute(
        "SELECT * FROM chain_blocks WHERE fault IS NOT NULL ORDER BY id ASC"
    ).fetchall())


def latest(conn: sqlite3.Connection) -> Optional[dict]:
    """The most recently appended block, or None if the chain is empty."""
    row = conn.execute(
        "SELECT * FROM chain_blocks ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return _row(row) if row else None


def full_chain(conn: sqlite3.Connection) -> list[dict]:
    """All blocks, oldest first (canonical chain order)."""
    return _rows(conn.execute(
        "SELECT * FROM chain_blocks ORDER BY id ASC"
    ).fetchall())


def walk_back(
    conn: sqlite3.Connection,
    this_hash: str,
    n: int = 10,
) -> list[dict]:
    """
    Walk the chain backwards from the block with the given hash, following
    prev_hash links. Returns up to n blocks, most-recent first.
    Stops at genesis (prev_hash == "").

    Raises ValueError if the starting hash is not found.
    """
    start = conn.execute(
        "SELECT * FROM chain_blocks WHERE this_hash = ?", (this_hash,)
    ).fetchone()
    if start is None:
        raise ValueError(f"No block found with hash {this_hash!r}")

    chain: list[dict] = []
    current = dict(start)

    while len(chain) < n:
        chain.append(current)
        if not current["prev_hash"]:
            break  # reached genesis
        parent = conn.execute(
            "SELECT * FROM chain_blocks WHERE this_hash = ?",
            (current["prev_hash"],),
        ).fetchone()
        if parent is None:
            break  # orphaned — shouldn't happen in a valid chain
        current = dict(parent)

    return chain
