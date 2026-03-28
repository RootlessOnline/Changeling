"""
test_connection_engine.py — Path type assignment and weight computation.
"""
import pytest
from soul.soul_graph import Connection, SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine
from soul.connection_engine import ConnectionEngine, _PATH_MAP


@pytest.fixture
def graph():
    g = SoulGraph()
    for node_id, ntype in [("purpose","purpose"),("v1","value"),("v2","value"),
                            ("anti","anti_resonance"),("know","knowledge")]:
        g.add_node(SoulNode(id=node_id, node_type=ntype,
                            content={"k": "v"}, chain_depth=2, access_count=3))
    g.add_connection(Connection(source_id="purpose", target_id="v1",
                                direction="bidirectional", weight=0.8, reasoning="r"))
    g.add_connection(Connection(source_id="purpose", target_id="v2",
                                direction="bidirectional", weight=0.7, reasoning="r"))
    g.add_connection(Connection(source_id="v1", target_id="v2",
                                direction="bidirectional", weight=0.6, reasoning="r"))
    return g


@pytest.fixture
def engine(graph):
    return SefirotEngine(graph)


@pytest.fixture
def conn_engine(graph, engine):
    return ConnectionEngine(graph, engine)


# ---------------------------------------------------------------------------
# assign_path_type
# ---------------------------------------------------------------------------

def test_assign_path_type_returns_string(conn_engine):
    vec_a = {"keter": 0.9, "chochmah": 0.1}
    vec_b = {"chochmah": 0.1, "binah": 0.8}
    pt = conn_engine.assign_path_type(vec_a, vec_b)
    assert isinstance(pt, str)
    assert len(pt) > 0


def test_assign_path_type_aleph_for_chochmah_binah(conn_engine):
    vec_a = {d: 0.0 for d in ["keter","chochmah","binah","daat","chesed",
                                "gevurah","tiferet","netzach","hod","yesod","malkuth"]}
    vec_b = dict(vec_a)
    vec_a["chochmah"] = 1.0
    vec_b["binah"] = 1.0
    pt = conn_engine.assign_path_type(vec_a, vec_b)
    assert pt == "aleph"


def test_assign_path_type_mem_for_chesed_gevurah(conn_engine):
    vec_a = {d: 0.0 for d in ["keter","chochmah","binah","daat","chesed",
                                "gevurah","tiferet","netzach","hod","yesod","malkuth"]}
    vec_b = dict(vec_a)
    vec_a["chesed"] = 1.0
    vec_b["gevurah"] = 1.0
    pt = conn_engine.assign_path_type(vec_a, vec_b)
    assert pt == "mem"


def test_assign_path_type_shin_for_netzach_hod(conn_engine):
    vec_a = {d: 0.0 for d in ["keter","chochmah","binah","daat","chesed",
                                "gevurah","tiferet","netzach","hod","yesod","malkuth"]}
    vec_b = dict(vec_a)
    vec_a["netzach"] = 1.0
    vec_b["hod"] = 1.0
    pt = conn_engine.assign_path_type(vec_a, vec_b)
    assert pt == "shin"


def test_assign_path_type_defaults_to_aleph_for_no_match(conn_engine):
    # daat has no entries in _PATH_MAP, so no cross-pair match is possible.
    # Same-dim supernal fallback fires and returns "aleph".
    daat_vec = {d: 0.0 for d in ["keter","chochmah","binah","daat","chesed",
                                   "gevurah","tiferet","netzach","hod","yesod","malkuth"]}
    daat_vec["daat"] = 1.0
    pt = conn_engine.assign_path_type(daat_vec, daat_vec)
    assert pt == "aleph"


def test_assign_path_type_recognises_all_defined_pairs(conn_engine):
    """Every entry in _PATH_MAP should be discoverable."""
    dims = ["keter","chochmah","binah","daat","chesed",
            "gevurah","tiferet","netzach","hod","yesod","malkuth"]
    for pair, expected_path in _PATH_MAP.items():
        pair_list = list(pair)
        if len(pair_list) < 2:
            continue
        vec_a = {d: 0.0 for d in dims}
        vec_b = {d: 0.0 for d in dims}
        vec_a[pair_list[0]] = 1.0
        vec_b[pair_list[1]] = 1.0
        pt = conn_engine.assign_path_type(vec_a, vec_b)
        assert pt == expected_path, f"Expected {expected_path} for {pair}, got {pt}"


# ---------------------------------------------------------------------------
# compute_connection_weight
# ---------------------------------------------------------------------------

def test_weight_identical_vectors_is_max(conn_engine):
    vec = {"keter": 0.5, "chesed": 0.5}
    w = conn_engine.compute_connection_weight(vec, vec)
    assert w == pytest.approx(1.0)


def test_weight_opposite_vectors_is_low(conn_engine):
    dims = ["keter","chochmah","binah","daat","chesed",
            "gevurah","tiferet","netzach","hod","yesod","malkuth"]
    vec_a = {d: 1.0 for d in dims}
    vec_b = {d: 0.0 for d in dims}
    w = conn_engine.compute_connection_weight(vec_a, vec_b)
    assert w < 0.1


def test_weight_in_range(conn_engine):
    import random
    dims = ["keter","chochmah","binah","daat","chesed",
            "gevurah","tiferet","netzach","hod","yesod","malkuth"]
    for _ in range(10):
        va = {d: random.random() for d in dims}
        vb = {d: random.random() for d in dims}
        w = conn_engine.compute_connection_weight(va, vb)
        assert 0.0 <= w <= 1.0


# ---------------------------------------------------------------------------
# find_connections
# ---------------------------------------------------------------------------

def test_find_connections_returns_list(conn_engine):
    # Add an unconnected node
    conn_engine.graph.add_node(
        SoulNode(id="new", node_type="knowledge", content={"k": "v"},
                 chain_depth=1, access_count=2)
    )
    results = conn_engine.find_connections("new", max_connections=3)
    assert isinstance(results, list)


def test_find_connections_max_respected(conn_engine):
    conn_engine.graph.add_node(
        SoulNode(id="new2", node_type="knowledge", content={"k": "v"},
                 chain_depth=2, access_count=4)
    )
    results = conn_engine.find_connections("new2", max_connections=2)
    assert len(results) <= 2


def test_find_connections_does_not_connect_to_self(conn_engine):
    conn_engine.graph.add_node(
        SoulNode(id="new3", node_type="knowledge", content={"k": "v"})
    )
    results = conn_engine.find_connections("new3")
    for c in results:
        assert c.source_id != c.target_id


def test_find_connections_nonexistent_node_returns_empty(conn_engine):
    assert conn_engine.find_connections("ghost") == []


# ---------------------------------------------------------------------------
# sefirot_distance
# ---------------------------------------------------------------------------

def test_sefirot_distance_symmetric(conn_engine):
    dims = ["keter","chochmah","binah","daat","chesed",
            "gevurah","tiferet","netzach","hod","yesod","malkuth"]
    va = {d: 0.3 for d in dims}
    vb = {d: 0.7 for d in dims}
    assert conn_engine.sefirot_distance(va, vb) == pytest.approx(conn_engine.sefirot_distance(vb, va))


def test_sefirot_distance_zero_for_equal(conn_engine):
    v = {"keter": 0.5, "chesed": 0.5}
    assert conn_engine.sefirot_distance(v, v) == pytest.approx(0.0)
