"""
base.py — Core data structures and Engine base class.

RuachInput: what arrives at Malkuth.
RuachOutput: what Ruach sends back.
EngineContext: accumulator passing through the event loop.
Engine: ABC for every cognitive engine.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RuachInput:
    input_type: str          # 'experience', 'question', 'feedback', 'task', 'correction'
    content: dict            # structured content
    natural_language: str    # Harley's words — stored for Phase 4 Hod, not processed yet
    context: str             # what prompted this interaction
    timestamp: str = field(default_factory=_now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class RuachOutput:
    response_type: str       # 'acknowledgment', 'result', 'question', 'uncertainty', 'refusal'
    content: dict
    reasoning: str
    confidence: float        # 0.0–1.0
    keter_alignment: float   # 0.0–1.0
    open_questions: list
    sefirot_state: dict
    nodes_affected: list
    chain_block_hash: Optional[str] = None


@dataclass
class EngineContext:
    """Passes through the event loop, accumulating each engine's contribution."""
    raw_input: RuachInput
    keter_relevance: Optional[float] = None
    keter_flags: list = field(default_factory=list)
    related_nodes: list = field(default_factory=list)
    chesed_breadth: int = 3
    gevurah_verdict: Optional[str] = None
    gevurah_faults: list = field(default_factory=list)
    gevurah_contradictions: list = field(default_factory=list)
    tiferet_decisions: list = field(default_factory=list)
    netzach_updates: list = field(default_factory=list)
    new_nodes: list = field(default_factory=list)
    new_connections: list = field(default_factory=list)
    output: Optional[RuachOutput] = None


class Engine(ABC):
    """Base class for all cognitive engines."""

    def __init__(self, soul_graph, sefirot_engine, conn, wal) -> None:
        self.graph = soul_graph
        self.sefirot = sefirot_engine
        self.conn = conn   # sqlite3.Connection — chain reads and writes
        self.wal = wal     # WriteAheadLog instance

    @abstractmethod
    def process(self, context: EngineContext) -> EngineContext:
        """Process the current context and return updated context."""
        pass
