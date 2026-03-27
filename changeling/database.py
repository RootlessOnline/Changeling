"""
database.py — SQLite connection management and schema initialisation.

Responsible for:
  - Opening the SQLite connection
  - Creating the chain_blocks table and indexes on first run
  - Nothing else. Writing, reading, and recovery live in their own modules.
"""

import sqlite3
from pathlib import Path

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
    fault            TEXT    DEFAULT NULL,
    reasoning        TEXT    NOT NULL,
    consequence      TEXT    DEFAULT NULL,
    commitment_level TEXT    NOT NULL DEFAULT 'experimental',
    this_hash        TEXT    NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_layer       ON chain_blocks (layer);
CREATE INDEX IF NOT EXISTS idx_layer_type  ON chain_blocks (layer_type);
CREATE INDEX IF NOT EXISTS idx_timestamp   ON chain_blocks (timestamp);
CREATE INDEX IF NOT EXISTS idx_fault       ON chain_blocks (fault)
    WHERE fault IS NOT NULL;
"""


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def open_db(path: str | Path) -> sqlite3.Connection:
    """
    Open the chain database at the given path, create schema if needed.
    Pass ':memory:' for an in-memory database (tests).
    """
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    conn.commit()
    return conn
