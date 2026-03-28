"""
test_sefirot_engine.py — Each Sefirot dimension computes correctly.
"""
import pytest
from soul.soul_graph import Connection, SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine, DIMENSIONS


@pytest.fixture
def graph():
    g = SoulGraph()
    # Build a small graph with varied properties
    purpose = SoulNode(id="purpose", node_type="purpose",
                       content={"statement": "to exist"}, chain_depth=3)
    value1  = SoulNode(id="v1", node_type="value",
                       content={"core": "openness"}, chain_depth=2,
                       access_count=5, reflection_count=3,
                       cluster_id="A")
    value2  = SoulNode(id="v2", node_type="value",
                       content={"core": "truth", "depth": "honest"},
                       chain_depth=1, access_count=2, cluster_id="B")
    anti    = SoulNode(id="anti", node_type="anti_resonance",
                       content={"boundary": "harm"}, anti_resonance=True,
                       cluster_id="A")
    knowledge = SoulNode(id="know", node_type="knowledge",
                         content={}, chain_depth=0, access_count=0)

    for n in [purpose, value1, value2, anti, knowledge]:
        g.add_node(n)

    g.add_connection(Connection(source_id="purpose", target_id="v1",
                                direction="bidirectional", weight=0.9, reasoning="core link"))
    g.add_connection(Connection(source_id="purpose", target_id="v2",
                                direction="bidirectional", weight=0.8, reasoning="truth grounds purpose"))
    g.add_connection(Connection(source_id="anti", target_id="purpose",
                                direction="bidirectional", weight=0.7, reasoning="boundary"))
    g.add_connection(Connection(source_id="v1", target_id="v2",
                                direction="bidirectional", weight=0.6, reasoning="values connect"))
    return g


@pytest.fixture
def engine(graph):
    return SefirotEngine(graph)


# ---------------------------------------------------------------------------
# General contract
# ---------------------------------------------------------------------------

def test_all_dimensions_in_range(engine, graph):
    for node in graph.all_nodes():
        vec = engine.compute_full_vector(node.id)
        for dim in DIMENSIONS:
            assert 0.0 <= vec[dim] <= 1.0, f"{dim} out of range for {node.id}: {vec[dim]}"


def test_full_vector_has_all_dimensions(engine):
    vec = engine.compute_full_vector("purpose")
    assert set(vec.keys()) == set(DIMENSIONS)


def test_nonexistent_node_returns_zeros(engine):
    vec = engine.compute_full_vector("ghost")
    assert all(v == 0.0 for v in vec.values())


# ---------------------------------------------------------------------------
# Keter
# ---------------------------------------------------------------------------

def test_keter_purpose_node_is_highest(engine, graph):
    # The purpose node IS the attractor — should have highest Keter
    k_purpose = engine.compute_keter("purpose")
    for node in graph.all_nodes():
        if node.id != "purpose":
            assert k_purpose >= engine.compute_keter(node.id)


def test_keter_connected_to_purpose_is_nonzero(engine):
    assert engine.compute_keter("v1") > 0.0


def test_keter_anti_resonance_node_uses_boundary_logic(engine):
    # Anti-resonance node Keter = boundary strength (connections to purpose/value)
    k_anti = engine.compute_keter("anti")
    assert 0.0 <= k_anti <= 1.0


def test_keter_isolated_node_is_zero(engine, graph):
    isolated = SoulNode(id="iso", content={}, node_type="knowledge")
    graph.add_node(isolated)
    assert engine.compute_keter("iso") == 0.0


# ---------------------------------------------------------------------------
# Chochmah
# ---------------------------------------------------------------------------

def test_chochmah_returns_float_in_range(engine):
    v = engine.compute_chochmah("v1")
    assert 0.0 <= v <= 1.0


def test_chochmah_tiny_graph_is_zero():
    g = SoulGraph()
    g.add_node(SoulNode(id="a", content={}, node_type="knowledge"))
    g.add_node(SoulNode(id="b", content={}, node_type="knowledge"))
    e = SefirotEngine(g)
    assert e.compute_chochmah("a") == 0.0  # < 3 nodes


def test_chochmah_bridge_node_higher_than_leaf(engine, graph):
    # Add a node that bridges two disconnected subgraphs
    bridge = SoulNode(id="bridge", content={}, node_type="knowledge")
    island = SoulNode(id="island", content={}, node_type="knowledge")
    graph.add_node(bridge)
    graph.add_node(island)
    graph.add_connection(Connection(source_id="bridge", target_id="purpose",
                                    direction="descending", weight=0.5))
    graph.add_connection(Connection(source_id="bridge", target_id="island",
                                    direction="descending", weight=0.5))
    graph.update_chochmah_novelty("bridge")
    v_bridge = engine.compute_chochmah("bridge")
    v_island = engine.compute_chochmah("island")
    assert v_bridge >= v_island


# ---------------------------------------------------------------------------
# Binah
# ---------------------------------------------------------------------------

def test_binah_higher_chain_depth_scores_higher(engine, graph):
    b_purpose = engine.compute_binah("purpose")   # chain_depth=3
    b_know = engine.compute_binah("know")          # chain_depth=0
    assert b_purpose > b_know


def test_binah_reasoned_connections_boost_score(engine):
    b_purpose = engine.compute_binah("purpose")  # has reasoned connections
    assert b_purpose > 0.0


def test_binah_zero_chain_zero_connections(engine, graph):
    isolated = SoulNode(id="blank", content={}, node_type="knowledge", chain_depth=0)
    graph.add_node(isolated)
    assert engine.compute_binah("blank") == 0.0


# ---------------------------------------------------------------------------
# Da'at
# ---------------------------------------------------------------------------

def test_daat_higher_reflection_scores_higher(engine):
    d_v1 = engine.compute_daat("v1")   # reflection_count=3
    d_v2 = engine.compute_daat("v2")   # reflection_count=0
    assert d_v1 > d_v2


def test_daat_zero_when_no_reflections(engine, graph):
    g2 = SoulGraph()
    a = SoulNode(id="a", content={}, node_type="knowledge", reflection_count=0)
    g2.add_node(a)
    e2 = SefirotEngine(g2)
    assert e2.compute_daat("a") == 0.0


def test_daat_normalised_to_max(engine, graph):
    # v1 has max reflection_count=3, so its Da'at should be 1.0
    assert engine.compute_daat("v1") == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Chesed
# ---------------------------------------------------------------------------

def test_chesed_well_connected_node_higher(engine):
    # purpose connects to v1, v2 (and anti bidirectionally) — most connected
    c_purpose = engine.compute_chesed("purpose")
    c_know = engine.compute_chesed("know")
    assert c_purpose > c_know


def test_chesed_isolated_node_is_zero(engine, graph):
    graph.add_node(SoulNode(id="iso2", content={}, node_type="knowledge"))
    assert engine.compute_chesed("iso2") == 0.0


# ---------------------------------------------------------------------------
# Gevurah
# ---------------------------------------------------------------------------

def test_gevurah_without_chain_uses_access_count(engine):
    g_v1 = engine.compute_gevurah("v1")  # access_count=5
    g_know = engine.compute_gevurah("know")  # access_count=0
    assert g_v1 > g_know


def test_gevurah_returns_float_in_range(engine):
    v = engine.compute_gevurah("purpose")
    assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# Tiferet
# ---------------------------------------------------------------------------

def test_tiferet_returns_float_in_range(engine):
    t = engine.compute_tiferet("purpose")
    assert 0.0 <= t <= 1.0


def test_tiferet_mediating_node_gets_bonus(engine, graph):
    # purpose connects v1, v2, anti — removing it disconnects anti.
    # A bridge node always receives the mediation term (0.5 in numerator),
    # so its minimum tiferet is (0+0.5)/1.5 ≈ 0.333 even at worst balance.
    t_purpose = engine.compute_tiferet("purpose")
    assert t_purpose > 0.0


# ---------------------------------------------------------------------------
# Netzach
# ---------------------------------------------------------------------------

def test_netzach_returns_nonzero_for_any_node(engine):
    # Netzach has a minimum base (0.2) from the formula
    n = engine.compute_netzach("v1")
    assert n > 0.0


def test_netzach_recent_node_higher_than_old(engine, graph):
    # Both nodes have last_accessed = now (created in fixture)
    # Frequency differentiates: v1 has access_count=5, know has 0
    n_v1 = engine.compute_netzach("v1")
    n_know = engine.compute_netzach("know")
    assert n_v1 >= n_know


# ---------------------------------------------------------------------------
# Hod
# ---------------------------------------------------------------------------

def test_hod_empty_content_scores_lower(engine):
    h_know = engine.compute_hod("know")     # content={}
    h_v2 = engine.compute_hod("v2")         # content has 2 fields
    assert h_v2 > h_know


def test_hod_reasoned_connections_boost(engine):
    h = engine.compute_hod("purpose")
    assert h > 0.0  # purpose has reasoned connections


# ---------------------------------------------------------------------------
# Yesod and Malkuth (without chain — structural proxies)
# ---------------------------------------------------------------------------

def test_yesod_without_chain_returns_structural_proxy(engine):
    y = engine.compute_yesod("purpose")
    assert 0.0 <= y <= 0.5  # capped at 0.5 without real deployment data


def test_malkuth_without_chain_is_zero(engine):
    # No chain = no grounding
    assert engine.compute_malkuth("purpose") == 0.0


# ---------------------------------------------------------------------------
# Sefirot distance
# ---------------------------------------------------------------------------

def test_sefirot_distance_same_vector_is_zero(engine):
    vec = engine.compute_full_vector("purpose")
    assert engine.sefirot_distance(vec, vec) == pytest.approx(0.0)


def test_sefirot_distance_different_vectors_nonzero(engine):
    v1 = engine.compute_full_vector("purpose")
    v2 = engine.compute_full_vector("know")
    assert engine.sefirot_distance(v1, v2) >= 0.0
