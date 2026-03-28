"""
soul_graph.py — The living graph topology. Ruach's body.

SoulGraph is a NetworkX DiGraph where:
  - Nodes carry SoulNode dataclasses as attributes
  - Edges carry Connection dataclasses as attributes
  - Direction matters: descending (creation) vs ascending (wisdom)
  - Bidirectional connections create two directed edges

Sefirot vectors are NOT stored. They are always computed fresh on access
by the SefirotEngine. The vector IS the node's life expressed as coordinates —
it must reflect current graph state, not a snapshot from the past.

Every access updates last_accessed and increments access_count. This data
feeds Da'at and Netzach computations — the graph knows what it returns to.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

import networkx as nx


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SoulNode:
    """
    A node in the soul graph. Represents any unit of experience, knowledge,
    value, purpose, or identity boundary.

    sefirot_vector is deliberately absent — compute it via SefirotEngine.
    chain_depth tracks how many chain blocks have been written for this node.
    chochmah_novelty is set at insertion time: this node's betweenness
    centrality after it first connects to the graph.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: dict = field(default_factory=dict)
    node_type: str = "knowledge"   # knowledge | value | purpose | anti_resonance | self_reference
    created_at: str = field(default_factory=_now)
    last_accessed: str = field(default_factory=_now)
    access_count: int = 0
    reflection_count: int = 0
    cluster_id: Optional[str] = None
    anti_resonance: bool = False
    chain_depth: int = 0           # chain blocks written for this node
    chochmah_novelty: float = 0.0  # betweenness centrality at first connection


@dataclass
class Connection:
    """
    A directed edge between two nodes. The path_type assigns which of the
    22 Kabbalistic paths this connection most resembles, computed from the
    Sefirot profiles of both nodes at connection time.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    path_type: str = "aleph"
    weight: float = 0.5
    direction: str = "bidirectional"   # descending | ascending | bidirectional
    created_at: str = field(default_factory=_now)
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Soul Graph
# ---------------------------------------------------------------------------

class SoulGraph:
    """
    The living graph. The body of Ruach.

    Uses NetworkX DiGraph for the topology so all NetworkX algorithms
    (centrality, shortest path, clustering, connected components) are
    immediately available for Sefirot computation.
    """

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, node: SoulNode) -> SoulNode:
        """
        Add a node to the graph. Computes initial chochmah_novelty
        from betweenness centrality before insertion (captures how much
        this node bridges existing structure — the novelty of its arrival).
        """
        # Capture betweenness state before this node arrives
        pre_centrality: dict[str, float] = {}
        if len(self.graph.nodes) >= 2:
            pre_centrality = nx.betweenness_centrality(self.graph, normalized=True)

        self.graph.add_node(node.id, data=node)

        # chochmah_novelty will be updated when connections are added
        # (betweenness is 0 until the node bridges paths)
        # Store the pre-insertion average so the engine can compare later
        node._pre_insertion_avg_centrality = (
            sum(pre_centrality.values()) / len(pre_centrality)
            if pre_centrality else 0.0
        )
        return node

    def get_node(self, node_id: str) -> Optional[SoulNode]:
        """
        Retrieve a node and update access metadata.
        Every access is a Netzach event — recency and frequency both matter.
        """
        if node_id not in self.graph.nodes:
            return None
        node: SoulNode = self.graph.nodes[node_id]["data"]
        node.last_accessed = _now()
        node.access_count += 1
        return node

    def get_node_readonly(self, node_id: str) -> Optional[SoulNode]:
        """Retrieve a node without updating access metadata. For internal computations."""
        if node_id not in self.graph.nodes:
            return None
        return self.graph.nodes[node_id]["data"]

    def update_chochmah_novelty(self, node_id: str) -> None:
        """
        Recompute and store chochmah_novelty after connections have been made.
        Call this after connecting a new node to the graph.
        """
        if node_id not in self.graph.nodes:
            return
        node = self.graph.nodes[node_id]["data"]
        if len(self.graph.nodes) < 3:
            node.chochmah_novelty = 0.0
            return
        centrality = nx.betweenness_centrality(self.graph, normalized=True)
        node.chochmah_novelty = centrality.get(node_id, 0.0)

    # ------------------------------------------------------------------
    # Connection operations
    # ------------------------------------------------------------------

    def add_connection(self, connection: Connection) -> Connection:
        """
        Add a directed edge. For bidirectional connections, also add the
        reverse edge as a new Connection with direction='ascending'.
        """
        if connection.source_id not in self.graph or connection.target_id not in self.graph:
            raise ValueError(
                f"Both nodes must exist before connecting: "
                f"{connection.source_id!r} → {connection.target_id!r}"
            )
        self.graph.add_edge(
            connection.source_id,
            connection.target_id,
            data=connection,
            weight=connection.weight,
        )
        if connection.direction == "bidirectional":
            reverse = Connection(
                id=str(uuid.uuid4()),
                source_id=connection.target_id,
                target_id=connection.source_id,
                path_type=connection.path_type,
                weight=connection.weight,
                direction="ascending",
                created_at=connection.created_at,
                reasoning=f"[reverse] {connection.reasoning}",
            )
            self.graph.add_edge(
                connection.target_id,
                connection.source_id,
                data=reverse,
                weight=reverse.weight,
            )
        return connection

    def get_connections(self, node_id: str) -> list[Connection]:
        """
        Return all connections incident to this node (both out-edges and
        in-edges), deduplicated by connection id.
        """
        seen: set[str] = set()
        connections: list[Connection] = []
        for _, __, edata in self.graph.out_edges(node_id, data=True):
            c: Connection = edata.get("data")
            if c and c.id not in seen:
                seen.add(c.id)
                connections.append(c)
        for _, __, edata in self.graph.in_edges(node_id, data=True):
            c: Connection = edata.get("data")
            if c and c.id not in seen:
                seen.add(c.id)
                connections.append(c)
        return connections

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def get_neighbours(self, node_id: str, depth: int = 1) -> list[SoulNode]:
        """BFS outward from node_id to the given depth. Does not include node_id itself."""
        if node_id not in self.graph:
            return []
        visited: set[str] = {node_id}
        current: set[str] = {node_id}
        for _ in range(depth):
            nxt: set[str] = set()
            for nid in current:
                nxt.update(self.graph.successors(nid))
                nxt.update(self.graph.predecessors(nid))
            nxt -= visited
            visited.update(nxt)
            current = nxt
        visited.discard(node_id)
        return [self.graph.nodes[nid]["data"] for nid in visited if nid in self.graph.nodes]

    def get_cluster(self, cluster_id: str) -> list[SoulNode]:
        """Return all nodes assigned to a cluster."""
        return [
            self.graph.nodes[nid]["data"]
            for nid in self.graph.nodes
            if self.graph.nodes[nid]["data"].cluster_id == cluster_id
        ]

    def find_similar(
        self,
        sefirot_vector: dict,
        threshold: float,
        compute_vector_fn: Optional[Callable[[str], dict]] = None,
    ) -> list[SoulNode]:
        """
        Find nodes whose Sefirot vector is within `threshold` Euclidean
        distance of the given vector.

        Requires compute_vector_fn — a callable that takes a node_id and
        returns its Sefirot vector dict. This is typically
        SefirotEngine.compute_full_vector. Without it, returns empty list.
        """
        if compute_vector_fn is None:
            return []
        DIMS = ["keter","chochmah","binah","daat","chesed","gevurah",
                "tiferet","netzach","hod","yesod","malkuth"]
        result = []
        for nid in self.graph.nodes:
            other_vec = compute_vector_fn(nid)
            dist = sum(
                (sefirot_vector.get(d, 0.0) - other_vec.get(d, 0.0)) ** 2
                for d in DIMS
            ) ** 0.5
            if dist <= threshold:
                result.append(self.graph.nodes[nid]["data"])
        return result

    # ------------------------------------------------------------------
    # Bulk access
    # ------------------------------------------------------------------

    def all_nodes(self) -> list[SoulNode]:
        return [self.graph.nodes[nid]["data"] for nid in self.graph.nodes]

    def nodes_by_type(self, node_type: str) -> list[SoulNode]:
        return [n for n in self.all_nodes() if n.node_type == node_type]

    def node_count(self) -> int:
        return len(self.graph.nodes)

    def connection_count(self) -> int:
        return len(self.graph.edges)

    def has_node(self, node_id: str) -> bool:
        return node_id in self.graph.nodes
