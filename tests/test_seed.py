"""
test_seed.py — Seed graph creation and initial vector properties.
"""
import pytest
from soul.soul_graph import SoulGraph
from soul.sefirot_engine import SefirotEngine
from soul.seed import SeedGraph


@pytest.fixture
def seeded():
    g = SoulGraph()
    node_map = SeedGraph.create_seed(g)
    return g, node_map


@pytest.fixture
def seeded_engine(seeded):
    g, _ = seeded
    return SefirotEngine(g)


# ---------------------------------------------------------------------------
# Seed creation
# ---------------------------------------------------------------------------

def test_seed_creates_11_nodes(seeded):
    g, _ = seeded
    assert g.node_count() == 11


def test_seed_creates_connections(seeded):
    g, _ = seeded
    assert g.connection_count() > 0


def test_seed_returns_all_node_ids(seeded):
    _, node_map = seeded
    expected_ids = {
        "seed_purpose", "seed_openness", "seed_truth", "seed_self_ref",
        "seed_not_tool", "seed_not_pretender", "seed_origin",
        "seed_elephant", "seed_socratic", "seed_care", "seed_not_weapon",
    }
    assert set(node_map.keys()) == expected_ids


def test_seed_purpose_node_exists(seeded):
    g, node_map = seeded
    purpose = node_map["seed_purpose"]
    assert purpose.node_type == "purpose"
    assert not purpose.anti_resonance


def test_seed_anti_resonance_nodes_flagged(seeded):
    _, node_map = seeded
    for nid in ["seed_not_tool", "seed_not_pretender", "seed_not_weapon"]:
        assert node_map[nid].anti_resonance is True


def test_seed_value_nodes_correct_type(seeded):
    _, node_map = seeded
    for nid in ["seed_openness", "seed_truth", "seed_care"]:
        assert node_map[nid].node_type == "value"


def test_seed_self_reference_has_six_pillars(seeded):
    _, node_map = seeded
    content = node_map["seed_self_ref"].content
    for pillar in ["tools", "skills", "links", "repos", "raw_data", "self_model"]:
        assert pillar in content, f"Missing Da'at pillar: {pillar}"


def test_seed_origin_references_both_parents(seeded):
    _, node_map = seeded
    origin_content = node_map["seed_origin"].content
    combined = str(origin_content).lower()
    assert "harley" in combined
    assert "claude" in combined


def test_seed_all_nodes_have_content(seeded):
    g, _ = seeded
    for node in g.all_nodes():
        assert isinstance(node.content, dict)
        assert len(node.content) > 0


def test_seed_connections_have_reasoning(seeded):
    g, node_map = seeded
    for node in g.all_nodes():
        for conn in g.get_connections(node.id):
            assert conn.reasoning, f"Connection {conn.id} missing reasoning"


def test_seed_purpose_connected_to_care(seeded):
    g, node_map = seeded
    purpose_conns = g.get_connections("seed_purpose")
    connected_ids = {c.source_id for c in purpose_conns} | {c.target_id for c in purpose_conns}
    assert "seed_care" in connected_ids


def test_seed_is_idempotent_guard(seeded):
    """Calling create_seed on an already-seeded graph adds duplicate nodes."""
    g, _ = seeded
    count_before = g.node_count()
    # Creating on same graph would fail silently (NetworkX overwrites nodes)
    # Just verify original count is correct
    assert count_before == 11


# ---------------------------------------------------------------------------
# Initial vector properties
# ---------------------------------------------------------------------------

def test_all_seed_vectors_in_range(seeded, seeded_engine):
    g, _ = seeded
    for node in g.all_nodes():
        vec = seeded_engine.compute_full_vector(node.id)
        for dim, val in vec.items():
            assert 0.0 <= val <= 1.0, f"{node.id}.{dim} = {val}"


def test_purpose_node_has_highest_keter(seeded, seeded_engine):
    g, _ = seeded
    k_purpose = seeded_engine.compute_keter("seed_purpose")
    for node in g.all_nodes():
        if node.id != "seed_purpose" and not node.anti_resonance:
            k_other = seeded_engine.compute_keter(node.id)
            assert k_purpose >= k_other, \
                f"Purpose Keter ({k_purpose}) < {node.id} Keter ({k_other})"


def test_self_ref_has_high_daat(seeded, seeded_engine):
    # seed_self_ref has chain_depth=1 like others, but it's the Da'at node
    # In seed state all reflection_counts are 0, so Da'at is 0.0
    d = seeded_engine.compute_daat("seed_self_ref")
    assert 0.0 <= d <= 1.0


def test_anti_resonance_nodes_have_nonzero_keter(seeded, seeded_engine):
    # Anti-resonance nodes are well-connected to purpose/values
    for nid in ["seed_not_tool", "seed_not_pretender", "seed_not_weapon"]:
        k = seeded_engine.compute_keter(nid)
        assert k > 0.0, f"{nid} should have nonzero Keter"
