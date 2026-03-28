"""
test_integration.py — Chain blocks created on graph mutations.

ChainGraphIntegration bridges Phase 1 (chain memory) and Phase 2 (soul graph).
Every significant graph event writes a verifiable chain block.
"""
import json
import pytest
from soul.soul_graph import Connection, SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine
from soul.integration import ChainGraphIntegration
from changeling.database import open_db
from changeling.chain_writer import ensure_genesis
from changeling.chain_reader import by_type, full_chain, latest
from changeling.wal import WriteAheadLog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def chain_env(tmp_path):
    """Initialised chain DB + WAL ready for integration use."""
    db_path  = tmp_path / "chain.db"
    wal_path = tmp_path / "wal.jsonl"
    conn = open_db(db_path)
    wal  = WriteAheadLog(wal_path)
    ensure_genesis(conn, wal)
    return conn, wal


@pytest.fixture
def graph():
    g = SoulGraph()
    g.add_node(SoulNode(id="purpose", node_type="purpose",
                        content={"statement": "to exist"}, chain_depth=0))
    g.add_node(SoulNode(id="val", node_type="value",
                        content={"core": "truth"}, chain_depth=0))
    return g


@pytest.fixture
def integration(graph, chain_env):
    conn, wal = chain_env
    engine = SefirotEngine(graph)
    return ChainGraphIntegration(graph, conn, wal, engine)


@pytest.fixture
def integration_no_engine(graph, chain_env):
    conn, wal = chain_env
    return ChainGraphIntegration(graph, conn, wal, engine=None)


# ---------------------------------------------------------------------------
# node_added
# ---------------------------------------------------------------------------

def test_node_added_writes_chain_block(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    count_before = len(by_type(conn, "node_event"))
    integration.node_added(node)
    assert len(by_type(conn, "node_event")) == count_before + 1


def test_node_added_block_has_correct_layer_type(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    block = latest(conn)
    assert block["layer_type"] == "node_event"


def test_node_added_block_layer_is_2(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    block = latest(conn)
    assert block["layer"] == 2


def test_node_added_block_commitment_sealed(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    block = latest(conn)
    assert block["commitment_level"] == "sealed"


def test_node_added_state_contains_event_field(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["event"] == "added"


def test_node_added_state_contains_node_id(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["node_id"] == "purpose"


def test_node_added_increments_chain_depth(integration, graph):
    node = graph.get_node_readonly("purpose")
    depth_before = node.chain_depth
    integration.node_added(node)
    assert node.chain_depth == depth_before + 1


def test_node_added_state_has_content_keys(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert "content_keys" in state
    assert isinstance(state["content_keys"], list)


# ---------------------------------------------------------------------------
# node_updated
# ---------------------------------------------------------------------------

def test_node_updated_writes_chain_block(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("val")
    count_before = len(by_type(conn, "node_event"))
    integration.node_updated(node, "added new association")
    assert len(by_type(conn, "node_event")) == count_before + 1


def test_node_updated_commitment_is_experimental(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("val")
    integration.node_updated(node, "refined content")
    block = latest(conn)
    assert block["commitment_level"] == "experimental"


def test_node_updated_state_contains_event_updated(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("val")
    integration.node_updated(node, "test change")
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["event"] == "updated"


def test_node_updated_state_has_change_field(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("val")
    integration.node_updated(node, "content expanded")
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["change"] == "content expanded"


def test_node_updated_increments_chain_depth(integration, graph):
    node = graph.get_node_readonly("val")
    depth_before = node.chain_depth
    integration.node_updated(node, "some change")
    assert node.chain_depth == depth_before + 1


# ---------------------------------------------------------------------------
# node_accessed
# ---------------------------------------------------------------------------

def test_node_accessed_no_block_below_10(integration, graph, chain_env):
    conn, _ = chain_env
    # access_count starts at 0; at 0 no block should be written
    count_before = len(full_chain(conn))
    integration.node_accessed("purpose")
    assert len(full_chain(conn)) == count_before


def test_node_accessed_nonexistent_node_is_silent(integration, chain_env):
    conn, _ = chain_env
    count_before = len(full_chain(conn))
    integration.node_accessed("does_not_exist")
    assert len(full_chain(conn)) == count_before


def test_node_accessed_writes_block_at_multiple_of_10(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    # Manually set access_count to exactly 10 (simulating 10 prior accesses)
    node.access_count = 10
    count_before = len(full_chain(conn))
    integration.node_accessed("purpose")
    assert len(full_chain(conn)) == count_before + 1


def test_node_accessed_block_has_node_event_type(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    node.access_count = 10
    integration.node_accessed("purpose")
    block = latest(conn)
    assert block["layer_type"] == "node_event"


def test_node_accessed_state_event_is_accessed(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    node.access_count = 20
    integration.node_accessed("purpose")
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["event"] == "accessed"


# ---------------------------------------------------------------------------
# node_reflected
# ---------------------------------------------------------------------------

def test_node_reflected_writes_chain_block(integration, graph, chain_env):
    conn, _ = chain_env
    count_before = len(by_type(conn, "node_event"))
    integration.node_reflected("purpose")
    assert len(by_type(conn, "node_event")) == count_before + 1


def test_node_reflected_increments_reflection_count(integration, graph):
    node = graph.get_node_readonly("purpose")
    count_before = node.reflection_count
    integration.node_reflected("purpose")
    assert node.reflection_count == count_before + 1


def test_node_reflected_state_contains_reflection_count(integration, graph, chain_env):
    conn, _ = chain_env
    integration.node_reflected("purpose")
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["event"] == "reflected"
    assert state["reflection_count"] >= 1


def test_node_reflected_nonexistent_node_is_silent(integration, chain_env):
    conn, _ = chain_env
    count_before = len(full_chain(conn))
    integration.node_reflected("ghost")
    assert len(full_chain(conn)) == count_before


def test_node_reflected_multiple_increments_accumulate(integration, graph):
    node = graph.get_node_readonly("val")
    integration.node_reflected("val")
    integration.node_reflected("val")
    integration.node_reflected("val")
    assert node.reflection_count == 3


# ---------------------------------------------------------------------------
# connection_added
# ---------------------------------------------------------------------------

def test_connection_added_writes_chain_block(integration, chain_env):
    conn, _ = chain_env
    c = Connection(source_id="purpose", target_id="val",
                   path_type="aleph", weight=0.8,
                   direction="bidirectional", reasoning="test link")
    count_before = len(by_type(conn, "connection_event"))
    integration.connection_added(c)
    assert len(by_type(conn, "connection_event")) == count_before + 1


def test_connection_added_layer_type_is_connection_event(integration, chain_env):
    conn, _ = chain_env
    c = Connection(source_id="purpose", target_id="val",
                   path_type="mem", weight=0.7,
                   direction="descending", reasoning="test")
    integration.connection_added(c)
    block = latest(conn)
    assert block["layer_type"] == "connection_event"


def test_connection_added_commitment_is_sealed(integration, chain_env):
    conn, _ = chain_env
    c = Connection(source_id="purpose", target_id="val",
                   path_type="shin", weight=0.6,
                   direction="ascending", reasoning="test")
    integration.connection_added(c)
    block = latest(conn)
    assert block["commitment_level"] == "sealed"


def test_connection_added_state_has_source_and_target(integration, chain_env):
    conn, _ = chain_env
    c = Connection(source_id="purpose", target_id="val",
                   path_type="gimel", weight=0.5,
                   direction="bidirectional", reasoning="structural link")
    integration.connection_added(c)
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["source_id"] == "purpose"
    assert state["target_id"] == "val"


def test_connection_added_state_has_path_type(integration, chain_env):
    conn, _ = chain_env
    c = Connection(source_id="purpose", target_id="val",
                   path_type="dalet", weight=0.5,
                   direction="descending", reasoning="test")
    integration.connection_added(c)
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["path_type"] == "dalet"


def test_connection_added_state_has_weight(integration, chain_env):
    conn, _ = chain_env
    c = Connection(source_id="purpose", target_id="val",
                   weight=0.75, reasoning="test")
    integration.connection_added(c)
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["weight"] == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# sefirot_snapshot
# ---------------------------------------------------------------------------

def test_sefirot_snapshot_returns_vector(integration):
    vec = integration.sefirot_snapshot("purpose")
    assert vec is not None
    assert isinstance(vec, dict)
    assert len(vec) == 11


def test_sefirot_snapshot_writes_chain_block(integration, chain_env):
    conn, _ = chain_env
    count_before = len(by_type(conn, "sefirot_snapshot"))
    integration.sefirot_snapshot("purpose")
    assert len(by_type(conn, "sefirot_snapshot")) == count_before + 1


def test_sefirot_snapshot_layer_type(integration, chain_env):
    conn, _ = chain_env
    integration.sefirot_snapshot("purpose")
    block = latest(conn)
    assert block["layer_type"] == "sefirot_snapshot"


def test_sefirot_snapshot_state_contains_vector(integration, chain_env):
    conn, _ = chain_env
    integration.sefirot_snapshot("val")
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["event"] == "sefirot_snapshot"
    assert "vector" in state
    assert "keter" in state["vector"]


def test_sefirot_snapshot_state_contains_node_id(integration, chain_env):
    conn, _ = chain_env
    integration.sefirot_snapshot("val")
    block = latest(conn)
    state = json.loads(block["compressed_state"])
    assert state["node_id"] == "val"


def test_sefirot_snapshot_without_engine_returns_none(integration_no_engine):
    result = integration_no_engine.sefirot_snapshot("purpose")
    assert result is None


def test_sefirot_snapshot_without_engine_writes_no_block(integration_no_engine, chain_env):
    conn, _ = chain_env
    count_before = len(by_type(conn, "sefirot_snapshot"))
    integration_no_engine.sefirot_snapshot("purpose")
    assert len(by_type(conn, "sefirot_snapshot")) == count_before


def test_sefirot_snapshot_vector_values_in_range(integration):
    vec = integration.sefirot_snapshot("purpose")
    for dim, val in vec.items():
        assert 0.0 <= val <= 1.0, f"{dim} = {val} out of range"


# ---------------------------------------------------------------------------
# Chain integrity across multiple events
# ---------------------------------------------------------------------------

def test_multiple_events_produce_valid_chain(integration, graph, chain_env):
    conn, _ = chain_env
    from changeling.chain_writer import verify_chain
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    integration.node_updated(node, "refined")
    integration.node_reflected("purpose")
    c = Connection(source_id="purpose", target_id="val",
                   weight=0.8, reasoning="multi-event test")
    integration.connection_added(c)
    integration.sefirot_snapshot("purpose")
    valid, err = verify_chain(conn)
    assert valid, f"Chain integrity failed: {err}"


def test_event_blocks_are_at_layer_2(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("val")
    integration.node_added(node)
    c = Connection(source_id="purpose", target_id="val",
                   weight=0.5, reasoning="layer test")
    integration.connection_added(c)
    blocks = [b for b in full_chain(conn) if b["layer_type"] != "genesis"]
    for b in blocks:
        assert b["layer"] == 2


def test_events_ordered_by_insertion(integration, graph, chain_env):
    conn, _ = chain_env
    node = graph.get_node_readonly("purpose")
    integration.node_added(node)
    integration.node_reflected("val")
    chain = full_chain(conn)
    non_genesis = [b for b in chain if b["layer_type"] != "genesis"]
    assert non_genesis[0]["layer_type"] == "node_event"
    assert non_genesis[1]["layer_type"] == "node_event"
