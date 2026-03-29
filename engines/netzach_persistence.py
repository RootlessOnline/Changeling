"""
netzach_persistence.py — Persist and restore Netzach's task queue via chain memory.

Netzach's drive must survive restarts. On sleep, the task queue is written to
chain as a netzach_state block. On wake, it is loaded and the queue restored.

The chain is the source of truth. Netzach's queue is ephemeral state;
the chain record is permanent.
"""
import json
from datetime import datetime, timezone

from changeling.chain_reader import by_type
from changeling.chain_writer import append_block
from engines.netzach import NetzachEngine, PendingTask


class NetzachPersistence:
    """Save and restore Netzach's task queue through chain memory."""

    def save_queue(self, netzach: NetzachEngine) -> dict:
        """
        Persist current task queue to chain as a netzach_state block.
        Returns the written block.
        """
        tasks_data = [
            {
                "id": task.id,
                "description": task.description,
                "keter_alignment": task.keter_alignment,
                "created_at": task.created_at,
                "last_touched": task.last_touched,
                "urgency": task.urgency,
                "source_node_id": task.source_node_id,
                "status": task.status,
            }
            for task in netzach.task_queue
        ]
        pending_count = sum(1 for t in netzach.task_queue if t.status == "pending")
        block = append_block(
            conn=netzach.conn,
            wal=netzach.wal,
            layer=3,
            layer_type="netzach_state",
            compressed_state=json.dumps({"tasks": tasks_data}, sort_keys=True),
            reasoning=(
                f"Netzach queue persisted: {len(tasks_data)} total task(s), "
                f"{pending_count} pending."
            ),
            commitment_level="sealed",
        )
        return block

    def load_queue(self, conn) -> list[PendingTask]:
        """
        Load task queue from the most recent netzach_state chain block.
        Returns empty list if no netzach_state blocks exist.
        """
        blocks = by_type(conn, "netzach_state")
        if not blocks:
            return []

        latest = blocks[-1]  # most recent is last in oldest-first order
        try:
            data = json.loads(latest["compressed_state"])
            tasks_data = data.get("tasks", [])
        except (json.JSONDecodeError, KeyError):
            return []

        tasks = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for t in tasks_data:
            task = PendingTask(
                id=t.get("id", ""),
                description=t.get("description", {}),
                keter_alignment=float(t.get("keter_alignment", 0.5)),
                created_at=t.get("created_at", now_iso),
                last_touched=t.get("last_touched", now_iso),
                urgency=float(t.get("urgency", 0.5)),
                source_node_id=t.get("source_node_id"),
                status=t.get("status", "pending"),
            )
            tasks.append(task)
        return tasks
