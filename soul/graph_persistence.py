"""
graph_persistence.py — Save and load the soul graph.

The soul graph persists in two forms:
  1. Snapshot: data/soul_graph.json — complete graph state at save time
  2. Chain: every mutation writes a chain block via Phase 1's chain writer

The snapshot is for fast loading. The chain is for history and recovery.
Together they give both present state and complete developmental history.

Uses NetworkX JSON graph format extended with SoulNode/Connection fields.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import networkx as nx
from networkx.readwrite import json_graph

from soul.soul_graph import Connection, SoulGraph, SoulNode

_DEFAULT_PATH = Path(__file__).parent.parent / "data" / "soul_graph.json"


class GraphPersistence:

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, graph: SoulGraph, path: Optional[str | Path] = None) -> None:
        """
        Save the soul graph to JSON.
        Creates parent directories if they don't exist.
        """
        save_path = Path(path or _DEFAULT_PATH)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "node_count": graph.node_count(),
            "connection_count": graph.connection_count(),
            "nodes": [_serialise_node(n) for n in graph.all_nodes()],
            "edges": _serialise_edges(graph),
        }
        with open(save_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=True)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self, path: Optional[str | Path] = None) -> SoulGraph:
        """
        Load a soul graph from JSON. Returns a fresh SoulGraph populated
        with the saved nodes and connections.
        Raises FileNotFoundError if the file doesn't exist.
        """
        load_path = Path(path or _DEFAULT_PATH)
        with open(load_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        graph = SoulGraph()

        # Nodes first
        for n_data in data.get("nodes", []):
            node = _deserialise_node(n_data)
            graph.graph.add_node(node.id, data=node)  # bypass add_node to skip betweenness

        # Then edges
        for e_data in data.get("edges", []):
            conn = _deserialise_connection(e_data)
            if graph.has_node(conn.source_id) and graph.has_node(conn.target_id):
                graph.graph.add_edge(
                    conn.source_id,
                    conn.target_id,
                    data=conn,
                    weight=conn.weight,
                )

        return graph

    def exists(self, path: Optional[str | Path] = None) -> bool:
        return Path(path or _DEFAULT_PATH).exists()


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _serialise_node(node: SoulNode) -> dict:
    return {
        "id":                node.id,
        "content":           node.content,
        "node_type":         node.node_type,
        "created_at":        node.created_at,
        "last_accessed":     node.last_accessed,
        "access_count":      node.access_count,
        "reflection_count":  node.reflection_count,
        "cluster_id":        node.cluster_id,
        "anti_resonance":    node.anti_resonance,
        "chain_depth":       node.chain_depth,
        "chochmah_novelty":  node.chochmah_novelty,
    }


def _deserialise_node(data: dict) -> SoulNode:
    return SoulNode(
        id=data["id"],
        content=data.get("content", {}),
        node_type=data.get("node_type", "knowledge"),
        created_at=data.get("created_at", ""),
        last_accessed=data.get("last_accessed", ""),
        access_count=data.get("access_count", 0),
        reflection_count=data.get("reflection_count", 0),
        cluster_id=data.get("cluster_id"),
        anti_resonance=data.get("anti_resonance", False),
        chain_depth=data.get("chain_depth", 0),
        chochmah_novelty=data.get("chochmah_novelty", 0.0),
    )


def _serialise_edges(graph: SoulGraph) -> list[dict]:
    edges = []
    seen: set[str] = set()
    for _, __, edata in graph.graph.edges(data=True):
        conn: Connection = edata.get("data")
        if conn and conn.id not in seen:
            seen.add(conn.id)
            edges.append({
                "id":         conn.id,
                "source_id":  conn.source_id,
                "target_id":  conn.target_id,
                "path_type":  conn.path_type,
                "weight":     conn.weight,
                "direction":  conn.direction,
                "created_at": conn.created_at,
                "reasoning":  conn.reasoning,
            })
    return edges


def _deserialise_connection(data: dict) -> Connection:
    return Connection(
        id=data["id"],
        source_id=data["source_id"],
        target_id=data["target_id"],
        path_type=data.get("path_type", "aleph"),
        weight=data.get("weight", 0.5),
        direction=data.get("direction", "bidirectional"),
        created_at=data.get("created_at", ""),
        reasoning=data.get("reasoning", ""),
    )
