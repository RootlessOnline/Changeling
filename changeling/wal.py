"""
wal.py — Write-Ahead Log for crash safety.

Every block write is logged here BEFORE it touches the SQLite database.
On startup, check for pending entries that were never committed — this means
the last session died mid-write. Recover by either confirming the block made
it into the DB or marking the attempt as interrupted.

File format: newline-delimited JSON.
  {"type": "pending",     "entry_id": "...", "block": {...}, "at": "ISO8601"}
  {"type": "committed",   "entry_id": "...", "hash":  "...", "at": "ISO8601"}
  {"type": "interrupted", "entry_id": "...", "reason":"...", "at": "ISO8601"}

Read right-to-left logic: scan all lines, build set of resolved entry_ids,
anything pending and not resolved is an orphan needing recovery.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class WriteAheadLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def log_pending(self, block: dict) -> str:
        """
        Record a block as a pending write before touching SQLite.
        Returns the entry_id used to later mark it committed or interrupted.
        """
        entry_id = str(uuid.uuid4())
        self._append({
            "type": "pending",
            "entry_id": entry_id,
            "block": block,
            "at": _now(),
        })
        return entry_id

    def log_committed(self, entry_id: str, this_hash: str) -> None:
        """Record that the pending entry was successfully written to SQLite."""
        self._append({
            "type": "committed",
            "entry_id": entry_id,
            "hash": this_hash,
            "at": _now(),
        })

    def log_interrupted(self, entry_id: str, reason: str) -> None:
        """Record that a pending entry was never completed (crash recovery)."""
        self._append({
            "type": "interrupted",
            "entry_id": entry_id,
            "reason": reason,
            "at": _now(),
        })

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def pending_entries(self) -> list[dict]:
        """
        Return all pending entries that have no committed or interrupted
        follow-up — these are orphans from a crashed session.
        """
        if not self.path.exists():
            return []

        pending: dict[str, dict] = {}   # entry_id -> block
        resolved: set[str] = set()

        for record in self._read_all():
            eid = record.get("entry_id", "")
            t = record.get("type", "")
            if t == "pending":
                pending[eid] = record.get("block", {})
            elif t in ("committed", "interrupted"):
                resolved.add(eid)

        return [
            {"entry_id": eid, "block": blk}
            for eid, blk in pending.items()
            if eid not in resolved
        ]

    def recover(self, conn: sqlite3.Connection) -> list[str]:
        """
        Called at startup. For each orphaned pending entry:
          - If the block's hash exists in the DB: it was written but the
            commit log was never appended. Mark committed.
          - Otherwise: the block was never written. Mark interrupted.
        Returns list of entry_ids that were processed.
        """
        processed = []
        for entry in self.pending_entries():
            entry_id = entry["entry_id"]
            block = entry["block"]
            this_hash = block.get("this_hash", "")

            if this_hash:
                row = conn.execute(
                    "SELECT 1 FROM chain_blocks WHERE this_hash = ?",
                    (this_hash,),
                ).fetchone()
                if row:
                    self.log_committed(entry_id, this_hash)
                    processed.append(entry_id)
                    continue

            self.log_interrupted(
                entry_id,
                "crash recovery: block not found in database",
            )
            processed.append(entry_id)

        return processed

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _append(self, record: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=True) + "\n")

    def _read_all(self) -> list[dict]:
        records = []
        if not self.path.exists():
            return records
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # corrupted line — skip, don't crash
        return records


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
