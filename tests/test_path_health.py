"""
test_path_health.py — Mother paths, Double paths, and diagnostics.
"""
import pytest
from soul.soul_graph import Connection, SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine
from soul.path_health import PathHealth


@pytest.fixture
def full_graph():
    """Graph with enough variety to exercise path health computations."""
    g = SoulGraph()
    nodes = [
        SoulNode(id="purpose", node_type="purpose", content={"s": "exist"},
                 chain_depth=3, access_count=10, reflection_count=5),
        SoulNode(id="v_open",  node_type="value",   content={"core": "open"},
                 chain_depth=2, access_count=7, reflection_count=3),
        SoulNode(id="v_truth", node_type="value",   content={"core": "truth", "depth": "honest"},
                 chain_depth=2, access_count=5, reflection_count=2),
        SoulNode(id="anti",    node_type="anti_resonance", content={"boundary": "harm"},
                 anti_resonance=True, chain_depth=1, access_count=3),
        SoulNode(id="know1",   node_type="knowledge", content={"fact": "a"},
                 chain_depth=1, access_count=2, reflection_count=1),
        SoulNode(id="know2",   node_type="knowledge", content={"fact": "b", "source": "x"},
                 chain_depth=0, access_count=1),
    ]
    for n in nodes:
        g.add_node(n)
    conns = [
        Connection(source_id="purpose", target_id="v_open",  direction="bidirectional", weight=0.9, reasoning="core"),
        Connection(source_id="purpose", target_id="v_truth", direction="bidirectional", weight=0.8, reasoning="truth"),
        Connection(source_id="v_open",  target_id="v_truth", direction="bidirectional", weight=0.7, reasoning="values"),
        Connection(source_id="anti",    target_id="purpose", direction="bidirectional", weight=0.6, reasoning="boundary"),
        Connection(source_id="know1",   target_id="v_open",  direction="descending",   weight=0.5, reasoning="links"),
        Connection(source_id="know2",   target_id="v_truth", direction="descending",   weight=0.4, reasoning="supports"),
    ]
    for c in conns:
        g.add_connection(c)
    return g


@pytest.fixture
def engine(full_graph):
    return SefirotEngine(full_graph)


@pytest.fixture
def path_health(full_graph, engine):
    return PathHealth(full_graph, engine)


@pytest.fixture
def empty_path_health():
    g = SoulGraph()
    e = SefirotEngine(g)
    return PathHealth(g, e)


# ---------------------------------------------------------------------------
# Mother paths
# ---------------------------------------------------------------------------

def test_aleph_returns_float_in_range(path_health):
    v = path_health.measure_aleph()
    assert 0.0 <= v <= 1.0


def test_aleph_empty_graph_returns_neutral(empty_path_health):
    assert empty_path_health.measure_aleph() == pytest.approx(0.5)


def test_mem_returns_float_in_range(path_health):
    v = path_health.measure_mem()
    assert 0.0 <= v <= 1.0


def test_mem_empty_graph_returns_neutral(empty_path_health):
    assert empty_path_health.measure_mem() == pytest.approx(0.5)


def test_shin_returns_float_in_range(path_health):
    v = path_health.measure_shin()
    assert 0.0 <= v <= 1.0


def test_shin_too_few_nodes_returns_neutral(empty_path_health):
    assert empty_path_health.measure_shin() == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Double paths
# ---------------------------------------------------------------------------

def test_double_path_returns_dict_with_two_directions(path_health):
    for measure in [path_health.measure_bet, path_health.measure_gimel,
                    path_health.measure_dalet, path_health.measure_kaph,
                    path_health.measure_peh, path_health.measure_resh,
                    path_health.measure_tav]:
        result = measure()
        assert "descending" in result
        assert "ascending" in result
        assert 0.0 <= result["descending"] <= 1.0
        assert 0.0 <= result["ascending"] <= 1.0


def test_double_path_empty_returns_defaults(empty_path_health):
    r = empty_path_health.measure_bet()
    assert r["descending"] == pytest.approx(0.5)
    assert r["ascending"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Simple paths
# ---------------------------------------------------------------------------

def test_all_simple_paths_return_float_in_range(path_health):
    for name in ["heh","vav","zayin","chet","tet","yod",
                 "lamed","nun","samekh","ayin","tzadi","qoph"]:
        v = path_health.measure_simple_path(name)
        assert 0.0 <= v <= 1.0, f"Path {name} out of range: {v}"


def test_unknown_simple_path_returns_neutral(path_health):
    assert path_health.measure_simple_path("unknown") == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Triadic balance
# ---------------------------------------------------------------------------

def test_triadic_balance_has_three_keys(path_health):
    balance = path_health.triadic_balance()
    assert set(balance.keys()) == {"supernal", "ethical", "astral"}


def test_triadic_balance_values_in_range(path_health):
    balance = path_health.triadic_balance()
    for v in balance.values():
        assert 0.0 <= v <= 1.0


def test_triadic_balance_equals_mother_path_scores(path_health):
    balance = path_health.triadic_balance()
    assert balance["supernal"] == pytest.approx(path_health.measure_aleph())
    assert balance["ethical"]  == pytest.approx(path_health.measure_mem())
    assert balance["astral"]   == pytest.approx(path_health.measure_shin())


# ---------------------------------------------------------------------------
# Pillar tension
# ---------------------------------------------------------------------------

def test_pillar_tension_has_three_pillars(path_health):
    tension = path_health.pillar_tension()
    assert set(tension.keys()) == {"right", "left", "middle"}


def test_pillar_tension_values_in_range(path_health):
    tension = path_health.pillar_tension()
    for v in tension.values():
        assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# Full diagnostic
# ---------------------------------------------------------------------------

def test_full_diagnostic_has_22_paths_plus_aggregates(path_health):
    diag = path_health.full_diagnostic()
    path_names = {"aleph","mem","shin","bet","gimel","dalet","kaph","peh","resh","tav",
                  "heh","vav","zayin","chet","tet","yod","lamed","nun","samekh","ayin","tzadi","qoph"}
    for name in path_names:
        assert name in diag, f"Missing path: {name}"
    assert "triadic_balance" in diag
    assert "pillar_tension" in diag


def test_full_diagnostic_all_scalars_in_range(path_health):
    diag = path_health.full_diagnostic()
    for key, val in diag.items():
        if isinstance(val, float):
            assert 0.0 <= val <= 1.0, f"{key} out of range"
        elif isinstance(val, dict):
            for sub_k, sub_v in val.items():
                if isinstance(sub_v, float):
                    assert 0.0 <= sub_v <= 1.0, f"{key}.{sub_k} out of range"
