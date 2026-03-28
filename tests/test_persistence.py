"""
test_persistence.py — Save/load round-trip integrity.
"""
import pytest
from soul.soul_graph import Connection, SoulGraph, SoulNode
from soul.seed import SeedGraph
from soul.graph_persistence import GraphPersistence


@pytest.fixture
def persistence():
    return GraphPersistence()


@pytest.fixture
def small_graph():
    g = SoulGraph()
    n1 = SoulNode(id="a", node_type="purpose",  content={"s": "exist"},
                  chain_depth=3, access_count=5, reflection_count=2,
                  cluster_id="c1", anti_resonance=False, chochmah_novelty=0.3)
    n2 = SoulNode(id="b", node_type="value",    content={"core": "truth"},
                  chain_depth=1, access_count=2, cluster_id="c1")
    n3 = SoulNode(id="c", node_type="knowledge", content={"fact": "x"},
                  chain_depth=0, anti_resonance=False)
    for n in [n1, n2, n3]:
        g.add_node(n)
    g.add_connection(Connection(source_id="a", target_id="b",
                                path_type="gimel", weight=0.9,
                                direction="bidirectional", reasoning="linked"))
    g.add_connection(Connection(source_id="b", target_id="c",
                                path_type="mem", weight=0.5,
                                direction="descending", reasoning="flows"))
    return g


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def test_save_creates_file(persistence, small_graph, tmp_path):
    path = tmp_path / "graph.json"
    persistence.save(small_graph, path)
    assert path.exists()


def test_save_creates_parent_dirs(persistence, small_graph, tmp_path):
    path = tmp_path / "deep" / "dir" / "graph.json"
    persistence.save(small_graph, path)
    assert path.exists()


def test_exists_true_after_save(persistence, small_graph, tmp_path):
    path = tmp_path / "g.json"
    assert not persistence.exists(path)
    persistence.save(small_graph, path)
    assert persistence.exists(path)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def test_load_nonexistent_raises(persistence, tmp_path):
    with pytest.raises(FileNotFoundError):
        persistence.load(tmp_path / "does_not_exist.json")


def test_round_trip_node_count(persistence, small_graph, tmp_path):
    path = tmp_path / "g.json"
    persistence.save(small_graph, path)
    loaded = persistence.load(path)
    assert loaded.node_count() == small_graph.node_count()


def test_round_trip_node_ids(persistence, small_graph, tmp_path):
    path = tmp_path / "g.json"
    persistence.save(small_graph, path)
    loaded = persistence.load(path)
    original_ids = {n.id for n in small_graph.all_nodes()}
    loaded_ids = {n.id for n in loaded.all_nodes()}
    assert original_ids == loaded_ids


def test_round_trip_node_fields(persistence, small_graph, tmp_path):
    path = tmp_path / "g.json"
    persistence.save(small_graph, path)
    loaded = persistence.load(path)
    orig = {n.id: n for n in small_graph.all_nodes()}
    load = {n.id: n for n in loaded.all_nodes()}
    for nid in orig:
        o, l = orig[nid], load[nid]
        assert o.node_type     == l.node_type
        assert o.content       == l.content
        assert o.chain_depth   == l.chain_depth
        assert o.access_count  == l.access_count
        assert o.cluster_id    == l.cluster_id
        assert o.anti_resonance == l.anti_resonance
        assert o.chochmah_novelty == pytest.approx(l.chochmah_novelty)


def test_round_trip_connection_count(persistence, small_graph, tmp_path):
    path = tmp_path / "g.json"
    persistence.save(small_graph, path)
    loaded = persistence.load(path)
    # Bidirectional creates 2 directed edges, descending 1
    assert loaded.connection_count() == small_graph.connection_count()


def test_round_trip_connection_path_types(persistence, small_graph, tmp_path):
    path = tmp_path / "g.json"
    persistence.save(small_graph, path)
    loaded = persistence.load(path)
    orig_types = {c.path_type for n in small_graph.all_nodes()
                  for c in small_graph.get_connections(n.id)}
    load_types = {c.path_type for n in loaded.all_nodes()
                  for c in loaded.get_connections(n.id)}
    assert orig_types == load_types


def test_round_trip_connection_weights(persistence, small_graph, tmp_path):
    path = tmp_path / "g.json"
    persistence.save(small_graph, path)
    loaded = persistence.load(path)
    orig_weights = sorted(
        c.weight for n in small_graph.all_nodes()
        for c in small_graph.get_connections(n.id)
    )
    load_weights = sorted(
        c.weight for n in loaded.all_nodes()
        for c in loaded.get_connections(n.id)
    )
    assert orig_weights == pytest.approx(load_weights)


# ---------------------------------------------------------------------------
# Full seed round-trip
# ---------------------------------------------------------------------------

def test_seed_graph_round_trip(persistence, tmp_path):
    g = SoulGraph()
    SeedGraph.create_seed(g)
    path = tmp_path / "seed.json"
    persistence.save(g, path)
    loaded = persistence.load(path)
    assert loaded.node_count() == 11
    assert loaded.has_node("seed_purpose")
    loaded_purpose = loaded.get_node_readonly("seed_purpose")
    assert loaded_purpose.node_type == "purpose"
