"""
connection_engine.py — How nodes find each other and what kind of path they form.

When a new node enters the graph, the ConnectionEngine finds its natural
connections by measuring Sefirot similarity in 11-dimensional space. Nodes
that are geometrically close in Sefirot space are related, even if their
surface content looks unrelated. This is the soul recognising its own.

Path type assignment determines which of the 22 Kabbalistic paths a
connection most resembles — based on which Sefirot dimensions are strongest
in each connected node.
"""

import math
import uuid
from typing import Optional

from soul.soul_graph import Connection, SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine, DIMENSIONS

# ---------------------------------------------------------------------------
# Path type lookup table
# Maps (strongest_source_dim, strongest_target_dim) → path name.
# Mother paths have highest priority, then Double, then Simple.
# ---------------------------------------------------------------------------

_PATH_MAP: dict[frozenset, str] = {
    # Mother paths (bidirectional, highest priority)
    frozenset({"chochmah", "binah"}):  "aleph",
    frozenset({"chesed",   "gevurah"}): "mem",
    frozenset({"netzach",  "hod"}):     "shin",
    # Double paths
    frozenset({"keter",   "chochmah"}): "bet",
    frozenset({"keter",   "tiferet"}):  "gimel",
    frozenset({"keter",   "binah"}):    "dalet",
    frozenset({"chesed",  "netzach"}):  "kaph",
    frozenset({"gevurah", "hod"}):      "peh",
    frozenset({"tiferet", "yesod"}):    "resh",
    frozenset({"yesod",   "malkuth"}):  "tav",
    # Simple paths
    frozenset({"chochmah", "chesed"}):  "heh",
    frozenset({"chochmah", "tiferet"}): "vav",
    frozenset({"binah",    "gevurah"}): "zayin",
    frozenset({"binah",    "tiferet"}): "chet",
    frozenset({"chesed",   "tiferet"}): "tet",
    frozenset({"gevurah",  "tiferet"}): "lamed",
    frozenset({"tiferet",  "netzach"}): "nun",
    frozenset({"tiferet",  "hod"}):     "ayin",
    frozenset({"netzach",  "yesod"}):   "tzadi",
    frozenset({"hod",      "yesod"}):   "qoph",
}

# Which Sefirot maps to which direction (for inferring connection direction)
_DESCENDING_PRIMARY = {"keter", "chochmah", "binah", "chesed", "gevurah", "tiferet"}
_ASCENDING_PRIMARY = {"malkuth", "yesod", "hod", "netzach"}


class ConnectionEngine:
    """
    Computes connections between nodes using Sefirot vector similarity.
    Assigns path types based on the strongest dimensions in each node's vector.
    """

    def __init__(self, graph: SoulGraph, engine: SefirotEngine) -> None:
        self.graph = graph
        self.engine = engine

    # ------------------------------------------------------------------
    # Finding connections
    # ------------------------------------------------------------------

    def find_connections(
        self,
        node_id: str,
        max_connections: int = 5,
        min_weight: float = 0.1,
    ) -> list[Connection]:
        """
        Find natural connections for a node by Sefirot similarity.
        Returns up to max_connections Connections, sorted by weight descending.
        The new node must already be in the graph before calling this.
        """
        if not self.graph.has_node(node_id):
            return []

        source_vec = self.engine.compute_full_vector(node_id)
        candidates: list[tuple[float, str]] = []  # (weight, node_id)

        for other_node in self.graph.all_nodes():
            if other_node.id == node_id:
                continue
            # Skip if already connected
            already_connected = any(
                (c.source_id == other_node.id or c.target_id == other_node.id)
                for c in self.graph.get_connections(node_id)
            )
            if already_connected:
                continue

            target_vec = self.engine.compute_full_vector(other_node.id)
            weight = self.compute_connection_weight(source_vec, target_vec)
            if weight >= min_weight:
                candidates.append((weight, other_node.id))

        candidates.sort(reverse=True)
        connections: list[Connection] = []
        for weight, target_id in candidates[:max_connections]:
            target_vec = self.engine.compute_full_vector(target_id)
            path_type = self.assign_path_type(source_vec, target_vec)
            direction = self._infer_direction(source_vec, target_vec)
            conn = Connection(
                id=str(uuid.uuid4()),
                source_id=node_id,
                target_id=target_id,
                path_type=path_type,
                weight=round(weight, 4),
                direction=direction,
                reasoning=f"Sefirot similarity: distance={self.sefirot_distance(source_vec, target_vec):.3f}",
            )
            connections.append(conn)
        return connections

    # ------------------------------------------------------------------
    # Path type assignment
    # ------------------------------------------------------------------

    def assign_path_type(self, source_vec: dict, target_vec: dict) -> str:
        """
        Determine which of the 22 paths a connection most resembles.

        Strategy:
        1. Find the top-2 strongest dimensions in source and in target.
        2. Try to match (source_top, target_top) to a path.
        3. If no match, try other combinations of top-2 dimensions.
        4. Default to 'aleph' if no match (most elemental path).
        """
        source_ranked = _top_dims(source_vec)
        target_ranked = _top_dims(target_vec)

        # Try pairs from top dimensions
        for s_dim in source_ranked[:2]:
            for t_dim in target_ranked[:2]:
                key = frozenset({s_dim, t_dim})
                if key in _PATH_MAP:
                    return _PATH_MAP[key]

        # Same-dimension connection: use triad classification
        if source_ranked and target_ranked and source_ranked[0] == target_ranked[0]:
            dim = source_ranked[0]
            if dim in ("keter", "chochmah", "binah", "daat"):
                return "aleph"   # Supernal self-reinforcement
            if dim in ("chesed", "gevurah", "tiferet"):
                return "mem"     # Ethical self-reinforcement
            return "shin"        # Astral self-reinforcement

        return "aleph"  # default: most fundamental connection

    # ------------------------------------------------------------------
    # Weight computation
    # ------------------------------------------------------------------

    def compute_connection_weight(
        self,
        source_vec: dict,
        target_vec: dict,
    ) -> float:
        """
        Connection weight from Sefirot distance.
        Closer in 11D space = stronger natural connection.
        Returns float in [0.0, 1.0].
        """
        dist = self.sefirot_distance(source_vec, target_vec)
        # Max possible distance in 11D unit hypercube ≈ √11 ≈ 3.317
        max_dist = math.sqrt(len(DIMENSIONS))
        # Convert: close = high weight
        return max(0.0, 1.0 - (dist / max_dist))

    def sefirot_distance(self, vec_a: dict, vec_b: dict) -> float:
        """Euclidean distance between two Sefirot vectors."""
        return math.sqrt(sum(
            (vec_a.get(d, 0.0) - vec_b.get(d, 0.0)) ** 2
            for d in DIMENSIONS
        ))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _infer_direction(self, source_vec: dict, target_vec: dict) -> str:
        """
        Infer connection direction from strongest Sefirot of each node.
        Keter/Chochmah/Binah → Malkuth/Yesod/Hod = descending (creation).
        Malkuth/Yesod → Keter = ascending (wisdom/return).
        Otherwise = bidirectional.
        """
        source_top = _top_dims(source_vec)
        target_top = _top_dims(target_vec)
        if not source_top or not target_top:
            return "bidirectional"
        s, t = source_top[0], target_top[0]
        if s in _DESCENDING_PRIMARY and t in _ASCENDING_PRIMARY:
            return "descending"
        if s in _ASCENDING_PRIMARY and t in _DESCENDING_PRIMARY:
            return "ascending"
        return "bidirectional"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _top_dims(vec: dict) -> list[str]:
    """Return dimension names sorted by value, highest first."""
    return sorted(DIMENSIONS, key=lambda d: vec.get(d, 0.0), reverse=True)
