"""
test_daat.py — DaatEngine: self-model, blind spots, Keter-Da'at gap, diagnostics.
"""
import pytest
from engines.base import EngineContext
from engines.daat import DaatEngine


# ---------------------------------------------------------------------------
# compute_self_model()
# ---------------------------------------------------------------------------

def test_self_model_empty_graph_returns_zeros(chain_with_genesis, tmp_wal, empty_graph):
    from soul.sefirot_engine import SefirotEngine
    from engines.keter import KeterEngine
    se = SefirotEngine(empty_graph, chain_with_genesis)
    keter = KeterEngine(empty_graph, se, chain_with_genesis, tmp_wal)
    daat = DaatEngine(empty_graph, se, chain_with_genesis, tmp_wal, keter_engine=keter)
    model = daat.compute_self_model()
    assert model["node_count"] == 0
    assert model["connection_count"] == 0
    assert all(v == 0.0 for v in model["aggregate_vector"].values())


def test_self_model_populated_graph_has_counts(engine_stack):
    daat = engine_stack["daat"]
    model = daat.compute_self_model()
    assert model["node_count"] == 3  # graph_with_nodes has 3 nodes
    assert "aggregate_vector" in model
    assert "strongest" in model
    assert "weakest" in model


def test_self_model_aggregate_vector_in_range(engine_stack):
    daat = engine_stack["daat"]
    model = daat.compute_self_model()
    for dim, val in model["aggregate_vector"].items():
        assert 0.0 <= val <= 1.0, f"{dim}={val} out of range"


def test_self_model_six_pillars_present(engine_stack):
    daat = engine_stack["daat"]
    model = daat.compute_self_model()
    pillars = model["six_pillars"]
    assert "tools" in pillars
    assert "skills" in pillars
    assert "raw_data_count" in pillars
    assert pillars["raw_data_count"] == 3


def test_self_model_strongest_weakest_are_sefirot_dims(engine_stack):
    daat = engine_stack["daat"]
    model = daat.compute_self_model()
    valid_dims = {
        "keter", "chochmah", "binah", "daat",
        "chesed", "gevurah", "tiferet",
        "netzach", "hod", "yesod", "malkuth",
    }
    assert model["strongest"] in valid_dims
    assert model["weakest"] in valid_dims


# ---------------------------------------------------------------------------
# compute_blind_spots()
# ---------------------------------------------------------------------------

def test_blind_spots_returns_list(engine_stack):
    daat = engine_stack["daat"]
    spots = daat.compute_blind_spots()
    assert isinstance(spots, list)


def test_blind_spots_includes_ignorance_gaps_for_underdeveloped_dims(chain_with_genesis, tmp_wal, empty_graph):
    from soul.sefirot_engine import SefirotEngine
    from soul.soul_graph import SoulNode
    from engines.keter import KeterEngine
    # Single node with near-zero scores → all dims will be underdeveloped
    g = empty_graph
    n = SoulNode(id="n1", content={"x": "y"}, node_type="knowledge")
    g.add_node(n)
    se = SefirotEngine(g, chain_with_genesis)
    keter = KeterEngine(g, se, chain_with_genesis, tmp_wal)
    daat = DaatEngine(g, se, chain_with_genesis, tmp_wal, keter_engine=keter)
    spots = daat.compute_blind_spots()
    ignorance_gaps = [s for s in spots if s["type"] == "ignorance_gap"]
    # With a single isolated node, many dimensions should be near 0
    assert len(ignorance_gaps) >= 1


def test_blind_spots_includes_identity_gaps_for_ar_nodes(chain_with_genesis, tmp_wal, graph_with_anti_resonance):
    from soul.sefirot_engine import SefirotEngine
    from engines.keter import KeterEngine
    se = SefirotEngine(graph_with_anti_resonance, chain_with_genesis)
    keter = KeterEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal)
    daat = DaatEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal, keter_engine=keter)
    spots = daat.compute_blind_spots()
    identity_gaps = [s for s in spots if s["type"] == "identity_gap"]
    assert len(identity_gaps) == 1
    assert identity_gaps[0]["node_id"] == "ar-1"


def test_blind_spots_includes_epistemic_gaps_from_chain(engine_stack):
    from changeling.chain_writer import append_block
    append_block(
        conn=engine_stack["conn"],
        wal=engine_stack["wal"],
        layer=3,
        layer_type="epistemic_forget",
        compressed_state="forgotten domain",
        reasoning="This domain is out of scope.",
        commitment_level="sealed",
    )
    daat = engine_stack["daat"]
    spots = daat.compute_blind_spots()
    epistemic = [s for s in spots if s["type"] == "epistemic_gap"]
    assert len(epistemic) >= 1


# ---------------------------------------------------------------------------
# compute_keter_daat_gap()
# ---------------------------------------------------------------------------

def test_keter_daat_gap_returns_zero_when_no_keter_engine(chain_with_genesis, tmp_wal, graph_with_nodes):
    from soul.sefirot_engine import SefirotEngine
    se = SefirotEngine(graph_with_nodes, chain_with_genesis)
    daat = DaatEngine(graph_with_nodes, se, chain_with_genesis, tmp_wal)
    assert daat.compute_keter_daat_gap() == 0.0


def test_keter_daat_gap_in_valid_range(engine_stack):
    daat = engine_stack["daat"]
    daat.self_model = daat.compute_self_model()
    gap = daat.compute_keter_daat_gap()
    assert 0.0 <= gap <= 1.0


# ---------------------------------------------------------------------------
# full_diagnostic()
# ---------------------------------------------------------------------------

def test_full_diagnostic_has_all_keys(engine_stack):
    daat = engine_stack["daat"]
    diag = daat.full_diagnostic()
    assert "self_model" in diag
    assert "blind_spots" in diag
    assert "keter_daat_gap" in diag
    assert "path_health" in diag
    assert "triadic_balance" in diag
    assert "pillar_tension" in diag


def test_full_diagnostic_triadic_has_three_triads(engine_stack):
    daat = engine_stack["daat"]
    diag = daat.full_diagnostic()
    triadic = diag["triadic_balance"]
    assert "supernal" in triadic
    assert "ethical" in triadic
    assert "astral" in triadic


# ---------------------------------------------------------------------------
# process()
# ---------------------------------------------------------------------------

def test_process_updates_self_model(engine_stack, sample_experience):
    daat = engine_stack["daat"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx = daat.process(ctx)
    assert daat.self_model != {}
    assert daat.self_model["node_count"] >= 0


def test_process_returns_context_unchanged(engine_stack, sample_experience):
    daat = engine_stack["daat"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_relevance = 0.5
    result = daat.process(ctx)
    assert result.keter_relevance == 0.5


def test_process_writes_snapshot_at_interval(engine_stack, sample_experience):
    from changeling.chain_reader import by_type
    from engines.daat import _SNAPSHOT_INTERVAL
    daat = engine_stack["daat"]
    ctx = EngineContext(raw_input=sample_experience)
    # Run enough cycles to trigger a snapshot
    daat._cycle_count = _SNAPSHOT_INTERVAL - 1
    daat.process(ctx)
    blocks = by_type(engine_stack["conn"], "daat_snapshot")
    assert len(blocks) >= 1


def test_process_does_not_write_snapshot_before_interval(engine_stack, sample_experience):
    from changeling.chain_reader import by_type
    daat = engine_stack["daat"]
    ctx = EngineContext(raw_input=sample_experience)
    daat._cycle_count = 0  # reset
    daat.process(ctx)  # cycle 1 — no snapshot
    blocks = by_type(engine_stack["conn"], "daat_snapshot")
    assert len(blocks) == 0
