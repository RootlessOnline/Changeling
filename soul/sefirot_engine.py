"""
sefirot_engine.py — Eleven computation functions. No LLM. CPU only.

Every dimension is a graph operation. The Sefirot vector IS the node's life
story expressed as coordinates in 11-dimensional space. It is always computed
fresh from the current state of the graph and chain — never stored, never stale.

All functions return float in [0.0, 1.0].
Zero means the node has not developed this quality yet.
One means maximum expression of this quality.
Both extremes are pathological — a healthy node lives in the middle.
"""

import math
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import networkx as nx

from soul.soul_graph import SoulGraph, SoulNode

# Sefirot dimension names in canonical order
DIMENSIONS = [
    "keter", "chochmah", "binah", "daat",
    "chesed", "gevurah", "tiferet",
    "netzach", "hod", "yesod", "malkuth",
]

_EPSILON = 1e-9


def _normalise(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clip to [0.0, 1.0] after normalisation."""
    if max_val <= min_val:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def _decay(days: float, half_life: float = 7.0) -> float:
    """Exponential decay. Returns 1.0 at 0 days, ~0.5 at half_life days."""
    return math.exp(-math.log(2) * days / half_life)


def _days_since(iso_timestamp: str) -> float:
    """Days elapsed since an ISO8601 timestamp."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        return max(0.0, delta.total_seconds() / 86400.0)
    except (ValueError, TypeError):
        return 0.0


class SefirotEngine:
    """
    Computes 11-dimensional Sefirot vectors from graph topology and chain history.

    graph: the live SoulGraph
    conn:  optional sqlite3.Connection to the chain DB (Phase 1)
           Many computations work without chain data — they return
           graph-only approximations. Chain data enriches but is not required.
    """

    def __init__(self, graph: SoulGraph, conn: Optional[sqlite3.Connection] = None) -> None:
        self.graph = graph
        self.conn = conn

    # ------------------------------------------------------------------
    # Keter — Orientation / Meta-intentionality
    # ------------------------------------------------------------------

    def compute_keter(self, node_id: str) -> float:
        """
        Distance to purpose attractor nodes. Closer = higher Keter.
        Anti-resonance nodes: Keter reflects boundary strength (how many
        purpose/value nodes they connect to — strong boundaries are well-defined).
        """
        g = self.graph.graph
        if node_id not in g:
            return 0.0

        node = self.graph.get_node_readonly(node_id)
        attractors = [n.id for n in self.graph.nodes_by_type("purpose")]

        if not attractors:
            return 0.1  # no purpose defined yet — faint orientation

        if node.anti_resonance:
            # Anti-resonance: strength = connections to purpose/value nodes
            purpose_value_ids = set(
                n.id for n in self.graph.all_nodes()
                if n.node_type in ("purpose", "value") and not n.anti_resonance
            )
            neighbours = set(
                list(g.successors(node_id)) + list(g.predecessors(node_id))
            )
            connected_pv = len(neighbours & purpose_value_ids)
            max_pv = max(len(purpose_value_ids), 1)
            return min(1.0, connected_pv / max_pv)

        # Build distance-weighted graph (high weight = close = low cost)
        min_dist = float("inf")
        for attractor_id in attractors:
            if attractor_id == node_id:
                return 1.0  # this node IS a purpose attractor
            try:
                # Convert weight to distance: high-weight edge = short distance
                dist = nx.shortest_path_length(
                    g, node_id, attractor_id,
                    weight=lambda u, v, d: 1.0 / (d.get("weight", 0.5) + _EPSILON),
                )
                min_dist = min(min_dist, dist)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        if min_dist == float("inf"):
            return 0.0
        # Normalise: distance 0 → 1.0, distance grows → approaches 0
        return 1.0 / (1.0 + min_dist)

    # ------------------------------------------------------------------
    # Chochmah — Novelty / Creative emergence
    # ------------------------------------------------------------------

    def compute_chochmah(self, node_id: str) -> float:
        """
        Betweenness centrality of the node — how much it bridges previously
        unconnected regions. Nodes that bridge = high novelty contribution.
        Also uses stored chochmah_novelty (set at connection time).
        """
        g = self.graph.graph
        if node_id not in g:
            return 0.0
        n = len(g.nodes)
        if n < 3:
            return 0.0  # can't be a bridge with < 3 nodes

        centrality = nx.betweenness_centrality(g, normalized=True)
        current = centrality.get(node_id, 0.0)

        # Blend current betweenness with stored novelty-at-insertion
        node = self.graph.get_node_readonly(node_id)
        stored = getattr(node, "chochmah_novelty", 0.0)
        combined = max(current, stored)

        # Normalise against the max in the graph
        max_centrality = max(centrality.values()) if centrality else _EPSILON
        return _normalise(combined, 0.0, max_centrality)

    # ------------------------------------------------------------------
    # Binah — Structure / Analytical depth
    # ------------------------------------------------------------------

    def compute_binah(self, node_id: str) -> float:
        """
        Two components:
        1. Chain depth: how many times this node has been through structural
           processing (chain_depth field, updated by integration layer).
        2. Reasoning ratio: connections with explicit reasoning vs total.
        """
        if node_id not in self.graph.graph:
            return 0.0

        node = self.graph.get_node_readonly(node_id)
        all_nodes = self.graph.all_nodes()

        # Component 1: chain depth normalised
        max_depth = max((n.chain_depth for n in all_nodes), default=0)
        depth_score = (node.chain_depth / max_depth) if max_depth > 0 else 0.0

        # Component 2: ratio of reasoned connections
        connections = self.graph.get_connections(node_id)
        if connections:
            reasoned = sum(1 for c in connections if c.reasoning.strip())
            reasoning_ratio = reasoned / len(connections)
        else:
            reasoning_ratio = 0.0

        return (depth_score + reasoning_ratio) / 2.0

    # ------------------------------------------------------------------
    # Da'at — Self-relevance / Self-knowledge
    # ------------------------------------------------------------------

    def compute_daat(self, node_id: str) -> float:
        """
        Normalised reflection frequency. Nodes the system returns to during
        self-examination are self-relevant — they shape the self-model.
        """
        if node_id not in self.graph.graph:
            return 0.0

        node = self.graph.get_node_readonly(node_id)
        all_nodes = self.graph.all_nodes()
        max_reflection = max((n.reflection_count for n in all_nodes), default=0)

        if max_reflection == 0:
            return 0.0
        return node.reflection_count / max_reflection

    # ------------------------------------------------------------------
    # Chesed — Reach / Exploratory expansion
    # ------------------------------------------------------------------

    def compute_chesed(self, node_id: str) -> float:
        """
        Degree centrality + bonus for cross-cluster connections.
        Broadly connected nodes that bridge clusters express Chesed fully.
        """
        g = self.graph.graph
        if node_id not in g:
            return 0.0
        n = len(g.nodes)
        if n <= 1:
            return 0.0

        node = self.graph.get_node_readonly(node_id)
        degree_centrality = nx.degree_centrality(g).get(node_id, 0.0)

        # Cross-cluster bonus
        connections = self.graph.get_connections(node_id)
        cross_cluster = sum(
            1 for c in connections
            if c.source_id != node_id or self._other_node_cluster(c, node_id) != node.cluster_id
        )
        bonus = min(0.2, 0.05 * cross_cluster)  # small bonus, capped

        return min(1.0, degree_centrality + bonus)

    def _other_node_cluster(self, connection, node_id: str) -> Optional[str]:
        other_id = connection.target_id if connection.source_id == node_id else connection.source_id
        other = self.graph.get_node_readonly(other_id)
        return other.cluster_id if other else None

    # ------------------------------------------------------------------
    # Gevurah — Validation / Fault survival
    # ------------------------------------------------------------------

    def compute_gevurah(self, node_id: str) -> float:
        """
        How well this node has survived scrutiny. Two paths:
        1. Chain: count clean (no-fault) chain blocks referencing this node.
        2. Fallback: access_count normalised (if no chain — frequently accessed
           without incident implies tacit validation).
        """
        if node_id not in self.graph.graph:
            return 0.0

        if self.conn is not None:
            return self._gevurah_from_chain(node_id)
        return self._gevurah_from_access(node_id)

    def _gevurah_from_chain(self, node_id: str) -> float:
        rows = self.conn.execute(
            "SELECT fault FROM chain_blocks WHERE compressed_state LIKE ? OR reasoning LIKE ?",
            (f"%{node_id}%", f"%{node_id}%"),
        ).fetchall()
        if not rows:
            return 0.0
        clean = sum(1 for r in rows if r[0] is None)
        total = len(rows)
        return clean / total

    def _gevurah_from_access(self, node_id: str) -> float:
        node = self.graph.get_node_readonly(node_id)
        all_nodes = self.graph.all_nodes()
        max_access = max((n.access_count for n in all_nodes), default=0)
        if max_access == 0:
            return 0.0
        return min(1.0, node.access_count / max_access)

    # ------------------------------------------------------------------
    # Tiferet — Integration / Harmonising centre
    # ------------------------------------------------------------------

    def compute_tiferet(self, node_id: str) -> float:
        """
        Two components averaged:
        1. Balance: 1.0 - |Chesed - Gevurah|. Perfect balance = 1.0.
        2. Mediation: does removing this node increase the number of
           connected components? Mediating nodes are structurally critical.
        """
        if node_id not in self.graph.graph:
            return 0.0

        chesed = self.compute_chesed(node_id)
        gevurah = self.compute_gevurah(node_id)
        balance = 1.0 - abs(chesed - gevurah)

        # Mediation score
        g = self.graph.graph
        if len(g.nodes) < 3:
            mediation = 0.0
        else:
            components_before = nx.number_weakly_connected_components(g)
            g_copy = g.copy()
            g_copy.remove_node(node_id)
            components_after = nx.number_weakly_connected_components(g_copy)
            mediation = 0.5 if components_after > components_before else 0.0

        return (balance + mediation) / (1.0 + (0.5 if mediation > 0 else 0.0))

    # ------------------------------------------------------------------
    # Netzach — Drive / Motivational persistence
    # ------------------------------------------------------------------

    def compute_netzach(self, node_id: str) -> float:
        """
        Weighted combination of recency, frequency, and unfinished-work bonus.
        Active nodes with incomplete threads have the highest drive.
        """
        if node_id not in self.graph.graph:
            return 0.0

        node = self.graph.get_node_readonly(node_id)
        all_nodes = self.graph.all_nodes()

        # Recency: exponential decay, half-life 7 days
        days = _days_since(node.last_accessed)
        recency = _decay(days, half_life=7.0)

        # Frequency: normalised access count
        max_access = max((n.access_count for n in all_nodes), default=0)
        frequency = (node.access_count / max_access) if max_access > 0 else 0.0

        # Unfinished bonus: chain blocks with experimental commitment and no consequence
        unfinished_bonus = 0.0
        if self.conn is not None:
            rows = self.conn.execute(
                """SELECT COUNT(*) FROM chain_blocks
                   WHERE commitment_level = 'experimental'
                   AND consequence IS NULL
                   AND (compressed_state LIKE ? OR reasoning LIKE ?)""",
                (f"%{node_id}%", f"%{node_id}%"),
            ).fetchone()
            if rows and rows[0] > 0:
                unfinished_bonus = min(0.2, 0.05 * rows[0])

        raw = 0.5 * recency + 0.3 * frequency + 0.2 + unfinished_bonus
        return min(1.0, raw)

    # ------------------------------------------------------------------
    # Hod — Clarity / Articulacy
    # ------------------------------------------------------------------

    def compute_hod(self, node_id: str) -> float:
        """
        Structural completeness: how fully formed is this node's content?
        In pre-verbal phase, articulacy IS structural completeness.

        Two components:
        1. Content completeness: non-null/non-empty fields in content dict.
        2. Connection typing ratio: connections with explicit path_type.
        """
        if node_id not in self.graph.graph:
            return 0.0

        node = self.graph.get_node_readonly(node_id)

        # Content completeness
        if not node.content:
            content_score = 0.0
        else:
            filled = sum(
                1 for v in node.content.values()
                if v is not None and v != "" and v != [] and v != {}
            )
            content_score = filled / len(node.content)

        # Connection typing ratio
        connections = self.graph.get_connections(node_id)
        if connections:
            typed = sum(1 for c in connections if c.path_type and c.path_type != "aleph")
            # 'aleph' is the default/untyped — typed means it's been explicitly assigned
            typing_ratio = typed / len(connections)
        else:
            typing_ratio = 0.0

        return (content_score + typing_ratio) / 2.0

    # ------------------------------------------------------------------
    # Yesod — Deployability / Reality interface
    # ------------------------------------------------------------------

    def compute_yesod(self, node_id: str) -> float:
        """
        Has this node been used in output? If yes, was the consequence positive?
        Nodes deployed with positive feedback score highest.
        """
        if node_id not in self.graph.graph:
            return 0.0

        if self.conn is not None:
            return self._yesod_from_chain(node_id)

        # Without chain: structural proxy — well-connected nodes in
        # the output path (high Chesed + high Hod) are more deployable
        chesed = self.compute_chesed(node_id)
        hod = self.compute_hod(node_id)
        return (chesed + hod) / 2.0 * 0.5  # cap at 0.5 without real deployment

    def _yesod_from_chain(self, node_id: str) -> float:
        rows = self.conn.execute(
            """SELECT consequence, commitment_level FROM chain_blocks
               WHERE layer_type IN ('task', 'output', 'response')
               AND (compressed_state LIKE ? OR reasoning LIKE ?)""",
            (f"%{node_id}%", f"%{node_id}%"),
        ).fetchall()
        if not rows:
            return 0.0
        deployed = len(rows)
        positive = sum(
            1 for r in rows
            if r[0] and any(w in str(r[0]).lower() for w in ("good","success","positive","correct","helpful"))
        )
        # Base score from deployment, bonus for positive consequences
        base = min(0.5, 0.1 * deployed)
        bonus = min(0.5, 0.15 * positive)
        return base + bonus

    # ------------------------------------------------------------------
    # Malkuth — Grounding / Consequence
    # ------------------------------------------------------------------

    def compute_malkuth(self, node_id: str) -> float:
        """
        Direct read from consequence fields in chain blocks referencing
        this node. Positive consequences raise Malkuth. No consequences = 0.0.
        Negative consequences lower the score (but learning value is tracked
        in the fault field, not here).
        """
        if node_id not in self.graph.graph:
            return 0.0

        if self.conn is None:
            return 0.0  # no chain = no grounding yet

        rows = self.conn.execute(
            """SELECT consequence FROM chain_blocks
               WHERE consequence IS NOT NULL
               AND (compressed_state LIKE ? OR reasoning LIKE ?)""",
            (f"%{node_id}%", f"%{node_id}%"),
        ).fetchall()
        if not rows:
            return 0.0

        positive_words = {"good", "success", "positive", "correct", "helpful", "done", "complete"}
        negative_words = {"fail", "error", "bad", "wrong", "incorrect", "harmful"}

        score = 0.0
        for (consequence,) in rows:
            c_lower = str(consequence).lower()
            if any(w in c_lower for w in positive_words):
                score += 1.0
            elif any(w in c_lower for w in negative_words):
                score -= 0.5  # negative consequence reduces but doesn't zero
        return max(0.0, min(1.0, score / len(rows)))

    # ------------------------------------------------------------------
    # Full vector
    # ------------------------------------------------------------------

    def compute_full_vector(self, node_id: str) -> dict:
        """
        Compute all 11 dimensions. Returns a dict keyed by dimension name.
        Always fresh — reflects current graph state.
        """
        return {
            "keter":    self.compute_keter(node_id),
            "chochmah": self.compute_chochmah(node_id),
            "binah":    self.compute_binah(node_id),
            "daat":     self.compute_daat(node_id),
            "chesed":   self.compute_chesed(node_id),
            "gevurah":  self.compute_gevurah(node_id),
            "tiferet":  self.compute_tiferet(node_id),
            "netzach":  self.compute_netzach(node_id),
            "hod":      self.compute_hod(node_id),
            "yesod":    self.compute_yesod(node_id),
            "malkuth":  self.compute_malkuth(node_id),
        }

    def sefirot_distance(self, vec_a: dict, vec_b: dict) -> float:
        """Euclidean distance between two Sefirot vectors in 11D space."""
        return math.sqrt(sum(
            (vec_a.get(d, 0.0) - vec_b.get(d, 0.0)) ** 2
            for d in DIMENSIONS
        ))
