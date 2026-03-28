"""
integration.py — Bridge between chain memory (Phase 1) and soul graph (Phase 2).

Every graph mutation writes a chain block. The graph is both a live topology
AND a recorded history. Chain memory is not a log of the graph — it IS the
tissue of the tree. Every node carries its own history through chain depth.

Chain block conventions:
  layer_type='node_event'        — node added, updated, accessed
  layer_type='connection_event'  — connection added
  layer_type='sefirot_snapshot'  — Sefirot vector recorded for history

The compressed_state field carries JSON with event details. This enables
the SefirotEngine and PathHealth to query the chain for computational context.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from changeling.chain_writer import append_block
from changeling.wal import WriteAheadLog
from soul.soul_graph import Connection, SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChainGraphIntegration:
    """
    Writes chain blocks for every significant soul graph event.

    graph:  the live SoulGraph
    conn:   sqlite3 connection to the chain DB (Phase 1)
    wal:    WriteAheadLog instance (Phase 1)
    engine: SefirotEngine for snapshot operations (optional)
    """

    def __init__(
        self,
        graph: SoulGraph,
        conn: sqlite3.Connection,
        wal: WriteAheadLog,
        engine: Optional[SefirotEngine] = None,
    ) -> None:
        self.graph = graph
        self.conn = conn
        self.wal = wal
        self.engine = engine

    # ------------------------------------------------------------------
    # Node events
    # ------------------------------------------------------------------

    def node_added(self, node: SoulNode) -> None:
        """
        Write a chain block recording that a node was added.
        Increments node.chain_depth.
        """
        state = json.dumps({
            "event": "added",
            "node_id": node.id,
            "node_type": node.node_type,
            "anti_resonance": node.anti_resonance,
            "content_keys": list(node.content.keys()),
        })
        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=2,
            layer_type="node_event",
            compressed_state=state,
            reasoning=f"Node '{node.id}' ({node.node_type}) added to soul graph.",
            commitment_level="sealed",
        )
        node.chain_depth += 1

    def node_updated(self, node: SoulNode, change_description: str) -> None:
        """
        Write a chain block recording a structural update to a node.
        Increments node.chain_depth (more chain history = higher Binah).
        """
        state = json.dumps({
            "event": "updated",
            "node_id": node.id,
            "node_type": node.node_type,
            "change": change_description,
            "chain_depth": node.chain_depth,
        })
        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=2,
            layer_type="node_event",
            compressed_state=state,
            reasoning=f"Node '{node.id}' updated: {change_description}",
            commitment_level="experimental",
        )
        node.chain_depth += 1

    def node_accessed(self, node_id: str) -> None:
        """
        Update access metadata. Writes a chain block only for significant
        accesses (every 10th access) to avoid bloating the chain.
        """
        node = self.graph.get_node_readonly(node_id)
        if node is None:
            return
        if node.access_count % 10 == 0 and node.access_count > 0:
            state = json.dumps({
                "event": "accessed",
                "node_id": node_id,
                "access_count": node.access_count,
            })
            append_block(
                conn=self.conn,
                wal=self.wal,
                layer=2,
                layer_type="node_event",
                compressed_state=state,
                reasoning=f"Node '{node_id}' accessed {node.access_count} times.",
                commitment_level="experimental",
            )

    def node_reflected(self, node_id: str) -> None:
        """
        Record that a reflection cycle touched this node.
        Increments reflection_count — feeds Da'at computation.
        """
        node = self.graph.get_node_readonly(node_id)
        if node is None:
            return
        node.reflection_count += 1
        state = json.dumps({
            "event": "reflected",
            "node_id": node_id,
            "reflection_count": node.reflection_count,
        })
        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=2,
            layer_type="node_event",
            compressed_state=state,
            reasoning=f"Node '{node_id}' touched by reflection cycle #{node.reflection_count}.",
            commitment_level="experimental",
        )

    # ------------------------------------------------------------------
    # Connection events
    # ------------------------------------------------------------------

    def connection_added(self, connection: Connection) -> None:
        """
        Write a chain block recording that a connection was made.
        Connections are always sealed — they represent a structural commitment.
        """
        state = json.dumps({
            "event": "added",
            "connection_id": connection.id,
            "source_id": connection.source_id,
            "target_id": connection.target_id,
            "path_type": connection.path_type,
            "weight": connection.weight,
            "direction": connection.direction,
        })
        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=2,
            layer_type="connection_event",
            compressed_state=state,
            reasoning=(
                f"Connection '{connection.path_type}' established: "
                f"{connection.source_id} → {connection.target_id}. "
                f"{connection.reasoning}"
            ),
            commitment_level="sealed",
        )

    # ------------------------------------------------------------------
    # Sefirot snapshot
    # ------------------------------------------------------------------

    def sefirot_snapshot(self, node_id: str) -> Optional[dict]:
        """
        Write current computed Sefirot vector to chain for historical tracking.
        Returns the vector that was snapshotted, or None if engine not available.

        Use this at significant moments: after reflection cycles, after major
        graph mutations, at sleep boundaries. Not every access.
        """
        if self.engine is None:
            return None

        vector = self.engine.compute_full_vector(node_id)
        state = json.dumps({
            "event": "sefirot_snapshot",
            "node_id": node_id,
            "vector": {k: round(v, 4) for k, v in vector.items()},
        })
        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=2,
            layer_type="sefirot_snapshot",
            compressed_state=state,
            reasoning=(
                f"Sefirot snapshot for node '{node_id}'. "
                f"Keter={vector['keter']:.3f} Tiferet={vector['tiferet']:.3f} "
                f"Da'at={vector['daat']:.3f}"
            ),
            commitment_level="experimental",
        )
        return vector
