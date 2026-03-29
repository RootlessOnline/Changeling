"""
test_tiferet.py — TiferetEngine: balance adjustment, contradiction resolution, node creation.
"""
import pytest
from engines.base import EngineContext, RuachInput
from engines.tiferet import TiferetEngine


# ---------------------------------------------------------------------------
# read_balance()
# ---------------------------------------------------------------------------

def test_read_balance_returns_triadic_and_pillar(engine_stack):
    tiferet = engine_stack["tiferet"]
    balance = tiferet.read_balance()
    assert "triadic" in balance
    assert "pillar" in balance
    assert "mem_health" in balance


def test_read_balance_mem_in_range(engine_stack):
    tiferet = engine_stack["tiferet"]
    balance = tiferet.read_balance()
    assert 0.0 <= balance["mem_health"] <= 1.0


def test_read_balance_without_path_health_returns_defaults(chain_with_genesis, tmp_wal, graph_with_nodes):
    from soul.sefirot_engine import SefirotEngine
    se = SefirotEngine(graph_with_nodes, chain_with_genesis)
    tiferet = TiferetEngine(graph_with_nodes, se, chain_with_genesis, tmp_wal)
    balance = tiferet.read_balance()
    assert balance["mem_health"] == 0.5


# ---------------------------------------------------------------------------
# adjust_parameters()
# ---------------------------------------------------------------------------

def test_adjust_parameters_no_crash_without_chesed_gevurah(chain_with_genesis, tmp_wal, graph_with_nodes):
    from soul.sefirot_engine import SefirotEngine
    se = SefirotEngine(graph_with_nodes, chain_with_genesis)
    tiferet = TiferetEngine(graph_with_nodes, se, chain_with_genesis, tmp_wal)
    tiferet.adjust_parameters()  # should not raise


def test_adjust_parameters_increases_chesed_when_gevurah_dominant(engine_stack):
    tiferet = engine_stack["tiferet"]
    chesed = engine_stack["chesed"]
    # Force low Mem health by patching path_health
    original_mem = tiferet.path_health.measure_mem
    tiferet.path_health.measure_mem = lambda: 0.2  # Gevurah-dominant
    original_breadth = chesed.breadth
    tiferet.adjust_parameters()
    assert chesed.breadth >= original_breadth
    tiferet.path_health.measure_mem = original_mem


def test_adjust_parameters_decreases_chesed_when_chesed_dominant(engine_stack):
    tiferet = engine_stack["tiferet"]
    chesed = engine_stack["chesed"]
    chesed.set_breadth(5)
    original_mem = tiferet.path_health.measure_mem
    tiferet.path_health.measure_mem = lambda: 0.8  # Chesed-dominant
    tiferet.adjust_parameters()
    assert chesed.breadth <= 5
    tiferet.path_health.measure_mem = original_mem


# ---------------------------------------------------------------------------
# resolve_contradiction()
# ---------------------------------------------------------------------------

def test_resolve_contradiction_rejects_incoming_for_high_gevurah_node(engine_stack):
    tiferet = engine_stack["tiferet"]
    # Mock high Gevurah
    original = tiferet.sefirot.compute_gevurah
    tiferet.sefirot.compute_gevurah = lambda nid: 0.9
    decision = tiferet.resolve_contradiction({
        "node_id": "know-1",
        "field": "domain",
        "existing_value": "learning",
        "incoming_value": "mathematics",
    })
    assert decision["action"] == "reject_incoming"
    tiferet.sefirot.compute_gevurah = original


def test_resolve_contradiction_updates_existing_for_low_gevurah_node(engine_stack):
    tiferet = engine_stack["tiferet"]
    original = tiferet.sefirot.compute_gevurah
    tiferet.sefirot.compute_gevurah = lambda nid: 0.1
    decision = tiferet.resolve_contradiction({
        "node_id": "know-1",
        "field": "domain",
        "existing_value": "learning",
        "incoming_value": "mathematics",
    })
    assert decision["action"] == "update_existing"
    assert decision["field"] == "domain"
    assert decision["new_value"] == "mathematics"
    tiferet.sefirot.compute_gevurah = original


def test_resolve_contradiction_holds_tension_for_mid_gevurah(engine_stack):
    tiferet = engine_stack["tiferet"]
    original = tiferet.sefirot.compute_gevurah
    tiferet.sefirot.compute_gevurah = lambda nid: 0.5
    decision = tiferet.resolve_contradiction({
        "node_id": "know-1",
        "field": "subject",
        "existing_value": "old",
        "incoming_value": "new",
    })
    assert decision["action"] == "hold_tension"
    tiferet.sefirot.compute_gevurah = original


def test_resolve_contradiction_includes_reasoning(engine_stack):
    tiferet = engine_stack["tiferet"]
    decision = tiferet.resolve_contradiction({
        "node_id": "know-1",
        "field": "domain",
        "existing_value": "a",
        "incoming_value": "b",
    })
    assert "reasoning" in decision
    assert len(decision["reasoning"]) > 0


# ---------------------------------------------------------------------------
# check_coherence()
# ---------------------------------------------------------------------------

def test_check_coherence_returns_dict_with_coherent_and_warnings(engine_stack):
    tiferet = engine_stack["tiferet"]
    result = tiferet.check_coherence()
    assert "coherent" in result
    assert "warnings" in result
    assert isinstance(result["warnings"], list)


# ---------------------------------------------------------------------------
# evaluate_pruning()
# ---------------------------------------------------------------------------

def test_evaluate_pruning_returns_subset_of_candidates(engine_stack):
    tiferet = engine_stack["tiferet"]
    candidates = ["know-1", "purpose-1", "nonexistent-node"]
    approved = tiferet.evaluate_pruning(candidates)
    assert isinstance(approved, list)
    for node_id in approved:
        assert node_id in candidates


# ---------------------------------------------------------------------------
# process() — node creation and decision recording
# ---------------------------------------------------------------------------

def test_process_creates_node_for_valid_pass(engine_stack, sample_experience):
    tiferet = engine_stack["tiferet"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx.related_nodes = []
    before = engine_stack["graph"].node_count()
    ctx = tiferet.process(ctx)
    after = engine_stack["graph"].node_count()
    assert after == before + 1
    assert len(ctx.new_nodes) == 1


def test_process_does_not_create_node_for_anti_resonant(engine_stack, sample_experience):
    tiferet = engine_stack["tiferet"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_flags = ["anti_resonant"]
    ctx.gevurah_verdict = "pass"
    before = engine_stack["graph"].node_count()
    ctx = tiferet.process(ctx)
    assert engine_stack["graph"].node_count() == before
    assert any(d["action"] == "anti_resonant_encounter" for d in ctx.tiferet_decisions)


def test_process_records_anti_resonant_in_chain(engine_stack, sample_experience):
    from changeling.chain_reader import by_type
    tiferet = engine_stack["tiferet"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_flags = ["anti_resonant"]
    ctx.gevurah_verdict = "pass"
    tiferet.process(ctx)
    blocks = by_type(engine_stack["conn"], "anti_resonant_encounter")
    assert len(blocks) >= 1


def test_process_quality_override_creates_node_for_high_keter(engine_stack, sample_experience):
    tiferet = engine_stack["tiferet"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_relevance = 0.9
    ctx.keter_flags = ["high_relevance"]
    ctx.gevurah_verdict = "fail_quality"
    before = engine_stack["graph"].node_count()
    ctx = tiferet.process(ctx)
    assert engine_stack["graph"].node_count() == before + 1
    assert any(d["action"] == "quality_override" for d in ctx.tiferet_decisions)


def test_process_quality_no_override_for_low_keter(engine_stack, sample_experience):
    tiferet = engine_stack["tiferet"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_relevance = 0.4
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "fail_quality"
    before = engine_stack["graph"].node_count()
    ctx = tiferet.process(ctx)
    assert engine_stack["graph"].node_count() == before


def test_process_node_carries_natural_language(engine_stack, sample_experience):
    tiferet = engine_stack["tiferet"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx = tiferet.process(ctx)
    node_id = ctx.new_nodes[0]
    node = engine_stack["graph"].get_node(node_id)
    assert "_natural_language" in node.content
    assert node.content["_natural_language"] == sample_experience.natural_language
