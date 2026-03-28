"""
test_soul_graph.py — SoulGraph node/connection CRUD and NetworkX integration.
"""
import pytest
from soul.soul_graph import Connection, SoulGraph, SoulNode


@pytest.fixture
def graph():
    return SoulGraph()


@pytest.fixture
def populated(graph):
    n1 = SoulNode(id="n1", content={"k": "v"}, node_type="purpose")
    n2 = SoulNode(id="n2", content={"k": "v"}, node_type="value")
    n3 = SoulNode(id="n3", content={"k": "v"}, node_type="knowledge")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    c = Connection(source_id="n1", target_id="n2", weight=0.8, direction="bidirectional", reasoning="test")
    graph.add_connection(c)
    return graph


# ---------------------------------------------------------------------------
# Node operations
# ---------------------------------------------------------------------------

def test_add_node_stores_in_graph(graph):
    node = SoulNode(id="x", node_type="knowledge", content={"a": 1})
    graph.add_node(node)
    assert graph.has_node("x")
    assert graph.node_count() == 1


def test_get_node_returns_node(populated):
    node = populated.get_node("n1")
    assert node is not None
    assert node.id == "n1"


def test_get_node_updates_access_metadata(graph):
    node = SoulNode(id="a", content={}, node_type="knowledge")
    graph.add_node(node)
    assert node.access_count == 0
    retrieved = graph.get_node("a")
    assert retrieved.access_count == 1


def test_get_node_returns_none_for_missing(graph):
    assert graph.get_node("nonexistent") is None


def test_get_node_readonly_does_not_increment_access(graph):
    node = SoulNode(id="b", content={}, node_type="knowledge")
    graph.add_node(node)
    graph.get_node_readonly("b")
    graph.get_node_readonly("b")
    assert node.access_count == 0


def test_node_count(populated):
    assert populated.node_count() == 3


def test_all_nodes_returns_all(populated):
    nodes = populated.all_nodes()
    ids = {n.id for n in nodes}
    assert ids == {"n1", "n2", "n3"}


def test_nodes_by_type(populated):
    purpose_nodes = populated.nodes_by_type("purpose")
    assert len(purpose_nodes) == 1
    assert purpose_nodes[0].id == "n1"


# ---------------------------------------------------------------------------
# Connection operations
# ---------------------------------------------------------------------------

def test_add_connection_creates_edge(populated):
    assert populated.connection_count() >= 1


def test_bidirectional_connection_creates_two_edges(graph):
    a = SoulNode(id="a", content={}, node_type="knowledge")
    b = SoulNode(id="b", content={}, node_type="value")
    graph.add_node(a)
    graph.add_node(b)
    conn = Connection(source_id="a", target_id="b", direction="bidirectional")
    graph.add_connection(conn)
    # Both directions should exist in the directed graph
    assert graph.graph.has_edge("a", "b")
    assert graph.graph.has_edge("b", "a")


def test_add_connection_missing_node_raises(graph):
    graph.add_node(SoulNode(id="x", content={}, node_type="knowledge"))
    with pytest.raises(ValueError):
        graph.add_connection(Connection(source_id="x", target_id="missing"))


def test_get_connections_returns_incident_edges(populated):
    conns = populated.get_connections("n1")
    assert len(conns) >= 1


def test_get_connections_deduplicates(populated):
    conns = populated.get_connections("n1")
    ids = [c.id for c in conns]
    assert len(ids) == len(set(ids))


def test_connection_count(populated):
    # bidirectional = 2 directed edges
    assert populated.connection_count() == 2


# ---------------------------------------------------------------------------
# Traversal
# ---------------------------------------------------------------------------

def test_get_neighbours_depth_1(populated):
    # n1 connects to n2, n3 has no connections
    neighbours = populated.get_neighbours("n1", depth=1)
    ids = {n.id for n in neighbours}
    assert "n2" in ids
    assert "n1" not in ids


def test_get_neighbours_depth_2(populated):
    # Add another connection: n2 → n3
    populated.add_connection(Connection(source_id="n2", target_id="n3",
                                        direction="descending", weight=0.5))
    depth2 = populated.get_neighbours("n1", depth=2)
    ids = {n.id for n in depth2}
    assert "n3" in ids


def test_get_neighbours_isolated_node(graph):
    graph.add_node(SoulNode(id="isolated", content={}, node_type="knowledge"))
    assert graph.get_neighbours("isolated") == []


def test_get_cluster_returns_matching(graph):
    a = SoulNode(id="a", content={}, node_type="knowledge", cluster_id="cluster1")
    b = SoulNode(id="b", content={}, node_type="knowledge", cluster_id="cluster1")
    c = SoulNode(id="c", content={}, node_type="knowledge", cluster_id="cluster2")
    graph.add_node(a)
    graph.add_node(b)
    graph.add_node(c)
    cluster = graph.get_cluster("cluster1")
    ids = {n.id for n in cluster}
    assert ids == {"a", "b"}


# ---------------------------------------------------------------------------
# find_similar
# ---------------------------------------------------------------------------

def test_find_similar_without_engine_returns_empty(populated):
    vec = {"keter": 1.0, "chesed": 0.8}
    assert populated.find_similar(vec, threshold=10.0) == []


def test_find_similar_with_engine_finds_nodes(populated):
    from soul.sefirot_engine import SefirotEngine
    engine = SefirotEngine(populated)
    vec = engine.compute_full_vector("n1")
    results = populated.find_similar(vec, threshold=2.0,
                                     compute_vector_fn=engine.compute_full_vector)
    ids = {n.id for n in results}
    # n1 itself should be within distance 0
    assert "n1" in ids


# ---------------------------------------------------------------------------
# NetworkX integration
# ---------------------------------------------------------------------------

def test_networkx_centrality_accessible(populated):
    import networkx as nx
    centrality = nx.degree_centrality(populated.graph)
    assert "n1" in centrality


def test_graph_is_directed(graph):
    import networkx as nx
    assert isinstance(graph.graph, nx.DiGraph)
