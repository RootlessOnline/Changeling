"""
test_chesed.py — ChesedEngine: graph search, breadth, inclusion threshold.
"""
import pytest
from engines.base import EngineContext, RuachInput
from engines.chesed import ChesedEngine
from soul.soul_graph import SoulGraph, SoulNode
from soul.sefirot_engine import SefirotEngine


# ---------------------------------------------------------------------------
# search_related()
# ---------------------------------------------------------------------------

def test_search_related_empty_graph_returns_empty(chain_with_genesis, tmp_wal, empty_graph):
    se = SefirotEngine(empty_graph, chain_with_genesis)
    chesed = ChesedEngine(empty_graph, se, chain_with_genesis, tmp_wal)
    result = chesed.search_related({"domain": "learning"})
    assert result == []


def test_search_related_finds_content_key_match(engine_stack):
    chesed = engine_stack["chesed"]
    # "domain": "learning" should match purpose-1 and know-1 in graph_with_nodes
    results = chesed.search_related({"domain": "learning"})
    node_ids = [r[0] for r in results]
    assert "purpose-1" in node_ids or "know-1" in node_ids


def test_search_related_finds_type_match(engine_stack):
    chesed = engine_stack["chesed"]
    results = chesed.search_related({"type": "knowledge"})
    node_ids = [r[0] for r in results]
    assert "know-1" in node_ids


def test_search_related_returns_tuples_with_score_and_type(engine_stack):
    chesed = engine_stack["chesed"]
    results = chesed.search_related({"domain": "learning"})
    for item in results:
        assert len(item) == 3
        node_id, score, connection_type = item
        assert isinstance(node_id, str)
        assert 0.0 <= score <= 1.0
        assert isinstance(connection_type, str)


def test_search_related_respects_breadth_limit(engine_stack):
    chesed = engine_stack["chesed"]
    results = chesed.search_related({"domain": "learning"}, breadth=1)
    # breadth=1 → limit = 1 * 2 = 2
    assert len(results) <= 2


def test_search_related_sorted_by_score_descending(engine_stack):
    chesed = engine_stack["chesed"]
    results = chesed.search_related({"domain": "learning", "type": "knowledge"})
    scores = [r[1] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_related_excludes_anti_resonance_nodes(chain_with_genesis, tmp_wal, graph_with_anti_resonance):
    se = SefirotEngine(graph_with_anti_resonance, chain_with_genesis)
    chesed = ChesedEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal)
    results = chesed.search_related({"domain": "deception"})
    node_ids = [r[0] for r in results]
    assert "ar-1" not in node_ids


def test_search_related_excludes_below_inclusion_threshold(engine_stack):
    chesed = engine_stack["chesed"]
    chesed.set_inclusion_threshold(0.99)  # very high threshold
    results = chesed.search_related({"domain": "learning"})
    # May return 0 or very few results
    for _, score, _ in results:
        assert score >= 0.99


# ---------------------------------------------------------------------------
# set_breadth() and set_inclusion_threshold()
# ---------------------------------------------------------------------------

def test_set_breadth_clamps_to_valid_range(engine_stack):
    chesed = engine_stack["chesed"]
    chesed.set_breadth(0)
    assert chesed.breadth == 1
    chesed.set_breadth(100)
    assert chesed.breadth == 10
    chesed.set_breadth(5)
    assert chesed.breadth == 5


def test_set_inclusion_threshold_clamps(engine_stack):
    chesed = engine_stack["chesed"]
    chesed.set_inclusion_threshold(0.0)
    assert chesed.inclusion_threshold == 0.1
    chesed.set_inclusion_threshold(1.0)
    assert chesed.inclusion_threshold == 0.9


# ---------------------------------------------------------------------------
# process()
# ---------------------------------------------------------------------------

def test_process_populates_related_nodes(engine_stack, sample_experience):
    chesed = engine_stack["chesed"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_flags = ["low_relevance"]
    ctx = chesed.process(ctx)
    assert isinstance(ctx.related_nodes, list)


def test_process_increases_breadth_for_high_relevance(engine_stack, sample_experience):
    chesed = engine_stack["chesed"]
    chesed.set_breadth(3)
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_flags = ["high_relevance"]
    ctx = chesed.process(ctx)
    assert ctx.chesed_breadth >= 3


def test_process_decreases_breadth_for_low_relevance(engine_stack, sample_experience):
    chesed = engine_stack["chesed"]
    chesed.set_breadth(3)
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_flags = ["low_relevance"]
    ctx = chesed.process(ctx)
    assert ctx.chesed_breadth <= 3


def test_process_records_effective_breadth(engine_stack, sample_experience):
    chesed = engine_stack["chesed"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_flags = ["low_relevance"]
    ctx = chesed.process(ctx)
    assert ctx.chesed_breadth >= 1
