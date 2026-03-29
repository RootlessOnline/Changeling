"""
netzach.py — Drive and priority engine. Ruach's persistence and motivation.

Netzach asks: "What have I committed to? What pulls at me? What needs finishing?"
It manages the priority queue, decays urgency over time, and detects when
inputs complete or create tasks.

Moses' forty years. Emovere — to move. The motivational current.
High Keter-alignment tasks decay slower because purpose sustains drive.
"""
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from changeling.chain_writer import append_block
from engines.base import Engine, EngineContext

_LAYER = 3


@dataclass
class PendingTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: dict = field(default_factory=dict)
    keter_alignment: float = 0.5
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_touched: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    urgency: float = 0.7
    source_node_id: Optional[str] = None
    status: str = "pending"   # 'pending' | 'active' | 'completed' | 'abandoned'


class NetzachEngine(Engine):
    """Drive engine. Priority queue, persistence, unfinished business tracking."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.task_queue: list[PendingTask] = []
        self.drive_decay_rate: float = 0.05

    def add_task(self, task: PendingTask) -> None:
        """Add a task to the priority queue and resort."""
        self.task_queue.append(task)
        self._sort_queue()

    def complete_task(self, task_id: str) -> None:
        """Mark task as completed and record in chain."""
        for task in self.task_queue:
            if task.id == task_id:
                task.status = "completed"
                task.last_touched = datetime.now(timezone.utc).isoformat()
                append_block(
                    conn=self.conn,
                    wal=self.wal,
                    layer=_LAYER,
                    layer_type="task_completed",
                    compressed_state=json.dumps({
                        "event": "task_completed",
                        "task_id": task_id,
                        "description_keys": list(task.description.keys()),
                        "keter_alignment": task.keter_alignment,
                    }, sort_keys=True),
                    reasoning=f"Netzach: task {task_id} completed.",
                    commitment_level="sealed",
                )
                return

    def get_next_task(self) -> Optional[PendingTask]:
        """Return highest-priority pending task."""
        self._sort_queue()
        for task in self.task_queue:
            if task.status == "pending":
                return task
        return None

    def find_unfinished_business(self) -> list:
        """Find chain blocks with experimental commitment and no consequence recorded."""
        rows = self.conn.execute(
            """SELECT this_hash, compressed_state, reasoning, timestamp
               FROM chain_blocks
               WHERE commitment_level = 'experimental' AND consequence IS NULL
               ORDER BY id DESC LIMIT 20"""
        ).fetchall()
        return [dict(r) for r in rows]

    def decay_drive(self) -> None:
        """
        Decay urgency on pending tasks each cycle.
        High Keter-alignment tasks decay slower — purpose sustains drive.
        """
        for task in self.task_queue:
            if task.status == "pending":
                decay = self.drive_decay_rate * (1.0 - task.keter_alignment)
                task.urgency = max(0.0, task.urgency - decay)

    def _sort_queue(self) -> None:
        """Sort by composite priority: keter_alignment * urgency * recency."""
        now = datetime.now(timezone.utc)
        for task in self.task_queue:
            try:
                last = datetime.fromisoformat(task.last_touched)
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                seconds_ago = (now - last).total_seconds()
                recency = 1.0 / (1.0 + seconds_ago / 86400)
            except (ValueError, TypeError):
                recency = 0.5
            task._priority = task.keter_alignment * task.urgency * recency
        self.task_queue.sort(key=lambda t: getattr(t, "_priority", 0.0), reverse=True)

    def process(self, context: EngineContext) -> EngineContext:
        """Netzach's role: manage priorities, detect completion, create tasks."""
        # Check if this input activates or satisfies pending tasks
        for task in self.task_queue:
            if task.status != "pending":
                continue
            task_keys = set(str(k).lower() for k in task.description.keys())
            input_keys = set(str(k).lower() for k in context.raw_input.content.keys()
                             if not str(k).startswith("_"))
            if task_keys & input_keys and context.raw_input.input_type in (
                "feedback", "correction", "experience"
            ):
                task.status = "active"
                task.last_touched = context.raw_input.timestamp
                context.netzach_updates.append({
                    "action": "task_activated",
                    "task_id": task.id,
                })

        # Create a new task if input_type is 'task'
        if context.raw_input.input_type == "task":
            new_task = PendingTask(
                id=str(uuid.uuid4()),
                description=dict(context.raw_input.content),
                keter_alignment=(
                    context.keter_relevance
                    if context.keter_relevance is not None
                    else 0.5
                ),
                created_at=context.raw_input.timestamp,
                last_touched=context.raw_input.timestamp,
                urgency=0.7,
                source_node_id=context.new_nodes[0] if context.new_nodes else None,
                status="pending",
            )
            self.add_task(new_task)
            context.netzach_updates.append({
                "action": "task_created",
                "task_id": new_task.id,
            })

        self.decay_drive()
        return context
