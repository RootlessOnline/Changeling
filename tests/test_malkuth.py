"""
test_malkuth.py — MalkuthEngine: I/O, consequence tracking, output assembly.
"""
import pytest
from engines.base import EngineContext, RuachInput
from engines.malkuth import MalkuthEngine
from changeling.chain_reader import by_type, latest


# ---------------------------------------------------------------------------
# receive()
# ---------------------------------------------------------------------------

def test_receive_returns_engine_context(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    assert isinstance(ctx, EngineContext)
    assert ctx.raw_input is sample_experience


def test_receive_writes_input_received_chain_block(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    malkuth.receive(sample_experience)
    blocks = by_type(engine_stack["conn"], "input_received")
    assert len(blocks) >= 1
    assert "input_received" in blocks[-1]["compressed_state"]


def test_receive_context_starts_empty(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    assert ctx.keter_relevance is None
    assert ctx.keter_flags == []
    assert ctx.related_nodes == []
    assert ctx.output is None


# ---------------------------------------------------------------------------
# process() — assembles RuachOutput
# ---------------------------------------------------------------------------

def test_process_assembles_acknowledgment_for_experience(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    assert ctx.output is not None
    assert ctx.output.response_type == "acknowledgment"


def test_process_assembles_refusal_for_anti_resonant(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_flags = ["anti_resonant"]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    assert ctx.output.response_type == "refusal"
    assert ctx.output.confidence >= 0.8


def test_process_assembles_uncertainty_for_fail_quality(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "fail_quality"
    ctx = malkuth.process(ctx)
    assert ctx.output.response_type == "uncertainty"
    assert ctx.output.confidence <= 0.5


def test_process_assembles_result_for_question_with_related_nodes(engine_stack):
    from engines.base import RuachInput
    malkuth = engine_stack["malkuth"]
    q = RuachInput(
        input_type="question",
        content={"query": "something"},
        natural_language="?",
        context="test",
    )
    ctx = malkuth.receive(q)
    ctx.keter_flags = ["high_relevance"]
    ctx.keter_relevance = 0.8
    ctx.related_nodes = [("node-1", 0.9, "content_match"), ("node-2", 0.7, "type_match")]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    assert ctx.output.response_type == "result"


def test_process_confidence_scales_with_related_nodes(engine_stack):
    from engines.base import RuachInput
    malkuth = engine_stack["malkuth"]
    q = RuachInput(input_type="question", content={"q": "x"}, natural_language="x", context="t")
    ctx = malkuth.receive(q)
    ctx.keter_flags = ["low_relevance"]
    ctx.keter_relevance = 0.3
    ctx.related_nodes = [("n1", 0.5, "proximity")] * 5
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    assert ctx.output.confidence > 0.3


def test_process_nodes_affected_includes_new_and_related(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_flags = ["low_relevance"]
    ctx.keter_relevance = 0.4
    ctx.gevurah_verdict = "pass"
    ctx.new_nodes = ["new-1"]
    ctx.related_nodes = [("rel-1", 0.5, "content_match")]
    ctx = malkuth.process(ctx)
    assert "new-1" in ctx.output.nodes_affected
    assert "rel-1" in ctx.output.nodes_affected


def test_process_reasoning_is_non_empty(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    assert len(ctx.output.reasoning) > 0


# ---------------------------------------------------------------------------
# deliver()
# ---------------------------------------------------------------------------

def test_deliver_stamps_chain_block_hash(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    output = malkuth.deliver(ctx)
    assert output.chain_block_hash is not None
    assert len(output.chain_block_hash) == 64  # SHA-256 hex


def test_deliver_writes_output_delivered_block(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    malkuth.deliver(ctx)
    blocks = by_type(engine_stack["conn"], "output_delivered")
    assert len(blocks) >= 1


def test_deliver_raises_if_output_not_assembled(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    with pytest.raises(RuntimeError):
        malkuth.deliver(ctx)


# ---------------------------------------------------------------------------
# record_consequence()
# ---------------------------------------------------------------------------

def test_record_consequence_fills_chain_block(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    output = malkuth.deliver(ctx)

    malkuth.record_consequence(output.chain_block_hash, {"result": "positive", "notes": "good"})

    conn = engine_stack["conn"]
    row = conn.execute(
        "SELECT consequence FROM chain_blocks WHERE this_hash = ?",
        (output.chain_block_hash,)
    ).fetchone()
    assert row is not None
    assert row["consequence"] is not None
    assert "positive" in row["consequence"]


def test_record_consequence_writes_return_path_block(engine_stack, sample_experience):
    malkuth = engine_stack["malkuth"]
    ctx = malkuth.receive(sample_experience)
    ctx.keter_relevance = 0.5
    ctx.keter_flags = ["low_relevance"]
    ctx.gevurah_verdict = "pass"
    ctx = malkuth.process(ctx)
    output = malkuth.deliver(ctx)
    malkuth.record_consequence(output.chain_block_hash, {"result": "good"})
    blocks = by_type(engine_stack["conn"], "consequence_received")
    assert len(blocks) >= 1
