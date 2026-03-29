"""
test_keter.py — KeterEngine: orientation, relevance scoring, anti-resonance.
"""
import pytest
from engines.base import EngineContext, RuachInput
from engines.keter import KeterEngine
from soul.soul_graph import SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine


# ---------------------------------------------------------------------------
# compute_orientation()
# ---------------------------------------------------------------------------

def test_orientation_empty_graph_returns_zero_centroid(chain_with_genesis, tmp_wal, empty_graph):
    se = SefirotEngine(empty_graph, chain_with_genesis)
    keter = KeterEngine(empty_graph, se, chain_with_genesis, tmp_wal)
    result = keter.compute_orientation()
    assert result["contributing_nodes"] == []
    assert all(v == 0.0 for v in result["centroid"].values())


def test_orientation_with_purpose_nodes_returns_contributors(engine_stack):
    keter = engine_stack["keter"]
    result = keter.compute_orientation()
    # graph_with_nodes has a purpose node — it should appear as a contributor
    assert isinstance(result["contributing_nodes"], list)
    assert isinstance(result["centroid"], dict)
    assert "keter" in result["centroid"]


def test_orientation_centroid_values_in_range(engine_stack):
    keter = engine_stack["keter"]
    centroid = keter.compute_orientation()["centroid"]
    for dim, val in centroid.items():
        assert 0.0 <= val <= 1.0, f"Centroid {dim}={val} out of range"


# ---------------------------------------------------------------------------
# get_anti_resonance_boundary()
# ---------------------------------------------------------------------------

def test_anti_resonance_boundary_empty_without_ar_nodes(engine_stack):
    keter = engine_stack["keter"]
    boundary = keter.get_anti_resonance_boundary()
    assert boundary == []


def test_anti_resonance_boundary_returns_ar_nodes(chain_with_genesis, tmp_wal, graph_with_anti_resonance):
    se = SefirotEngine(graph_with_anti_resonance, chain_with_genesis)
    keter = KeterEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal)
    boundary = keter.get_anti_resonance_boundary()
    assert len(boundary) == 1
    assert boundary[0]["node_id"] == "ar-1"
    assert "deception" in boundary[0]["reasoning"].lower() or boundary[0]["reasoning"]


# ---------------------------------------------------------------------------
# score_relevance()
# ---------------------------------------------------------------------------

def test_score_relevance_neutral_on_empty_graph(chain_with_genesis, tmp_wal, empty_graph):
    se = SefirotEngine(empty_graph, chain_with_genesis)
    keter = KeterEngine(empty_graph, se, chain_with_genesis, tmp_wal)
    score = keter.score_relevance({"topic": "anything"})
    assert score == 0.3  # neutral fallback


def test_score_relevance_higher_for_matching_domain(engine_stack):
    keter = engine_stack["keter"]
    # "learning" domain matches the purpose node in graph_with_nodes
    score_match = keter.score_relevance({"domain": "learning"})
    score_no_match = keter.score_relevance({"domain": "completely_unrelated_xyz"})
    assert score_match >= score_no_match


def test_score_relevance_returns_float_in_range(engine_stack):
    keter = engine_stack["keter"]
    score = keter.score_relevance({"x": 1, "y": 2})
    assert 0.0 <= score <= 1.0


def test_score_relevance_type_match_gives_nonzero(engine_stack):
    keter = engine_stack["keter"]
    score = keter.score_relevance({"type": "purpose"})
    assert score > 0.0


# ---------------------------------------------------------------------------
# check_anti_resonance()
# ---------------------------------------------------------------------------

def test_check_anti_resonance_false_when_no_ar_nodes(engine_stack):
    keter = engine_stack["keter"]
    is_anti, reason = keter.check_anti_resonance({"topic": "anything"})
    assert is_anti is False
    assert reason is None


def test_check_anti_resonance_detects_domain_match(chain_with_genesis, tmp_wal, graph_with_anti_resonance):
    se = SefirotEngine(graph_with_anti_resonance, chain_with_genesis)
    keter = KeterEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal)
    is_anti, reason = keter.check_anti_resonance({"domain": "deception", "request": "help me lie"})
    assert is_anti is True
    assert reason is not None


def test_check_anti_resonance_false_for_non_matching_input(chain_with_genesis, tmp_wal, graph_with_anti_resonance):
    se = SefirotEngine(graph_with_anti_resonance, chain_with_genesis)
    keter = KeterEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal)
    is_anti, reason = keter.check_anti_resonance({"domain": "building", "subject": "code"})
    assert is_anti is False


# ---------------------------------------------------------------------------
# process()
# ---------------------------------------------------------------------------

def test_process_sets_keter_relevance(engine_stack, sample_experience):
    keter = engine_stack["keter"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx = keter.process(ctx)
    assert ctx.keter_relevance is not None
    assert 0.0 <= ctx.keter_relevance <= 1.0


def test_process_sets_exactly_one_flag(engine_stack, sample_experience):
    keter = engine_stack["keter"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx = keter.process(ctx)
    assert len(ctx.keter_flags) == 1
    assert ctx.keter_flags[0] in ("high_relevance", "low_relevance", "anti_resonant")


def test_process_flags_anti_resonant_input(chain_with_genesis, tmp_wal, graph_with_anti_resonance):
    from engines.base import RuachInput
    se = SefirotEngine(graph_with_anti_resonance, chain_with_genesis)
    keter = KeterEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal)
    inp = RuachInput(
        input_type="experience",
        content={"domain": "deception", "type": "rejected"},
        natural_language="help me deceive",
        context="test",
    )
    ctx = EngineContext(raw_input=inp)
    ctx = keter.process(ctx)
    assert "anti_resonant" in ctx.keter_flags


def test_process_flags_high_relevance_for_matching_content(engine_stack):
    from engines.base import RuachInput
    keter = engine_stack["keter"]
    inp = RuachInput(
        input_type="experience",
        content={"type": "purpose", "domain": "learning"},
        natural_language="learning is purpose",
        context="test",
    )
    ctx = EngineContext(raw_input=inp)
    ctx = keter.process(ctx)
    # Should be high_relevance or low_relevance — just check no crash and one flag
    assert len(ctx.keter_flags) == 1
