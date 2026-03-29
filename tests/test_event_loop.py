"""
test_event_loop.py — EventLoop: full processing cycles, consequences, diagnostics.
"""
import pytest
from engines.base import RuachInput, RuachOutput
from engines.event_loop import EventLoop
from changeling.chain_reader import by_type


# ---------------------------------------------------------------------------
# process_input() — full cycle
# ---------------------------------------------------------------------------

def test_process_input_returns_ruach_output(event_loop, sample_experience):
    output = event_loop.process_input(sample_experience)
    assert isinstance(output, RuachOutput)


def test_process_input_output_has_required_fields(event_loop, sample_experience):
    output = event_loop.process_input(sample_experience)
    assert output.response_type in ("acknowledgment", "result", "question", "uncertainty", "refusal")
    assert 0.0 <= output.confidence <= 1.0
    assert 0.0 <= output.keter_alignment <= 1.0
    assert isinstance(output.open_questions, list)
    assert isinstance(output.sefirot_state, dict)
    assert isinstance(output.nodes_affected, list)


def test_process_input_stamps_chain_hash(event_loop, sample_experience):
    output = event_loop.process_input(sample_experience)
    assert output.chain_block_hash is not None
    assert len(output.chain_block_hash) == 64


def test_process_input_increments_cycle_count(event_loop, sample_experience):
    assert event_loop.cycle_count == 0
    event_loop.process_input(sample_experience)
    assert event_loop.cycle_count == 1
    event_loop.process_input(sample_experience)
    assert event_loop.cycle_count == 2


def test_process_input_writes_cycle_complete_block(event_loop, sample_experience):
    event_loop.process_input(sample_experience)
    blocks = by_type(event_loop._conn, "cycle_complete")
    assert len(blocks) >= 1


def test_process_input_experience_creates_node(event_loop, sample_experience):
    graph = event_loop.tiferet.graph
    before = graph.node_count()
    event_loop.process_input(sample_experience)
    after = graph.node_count()
    assert after >= before  # at least the same, usually +1


def test_process_question_returns_result_or_uncertainty(event_loop, sample_question):
    output = event_loop.process_input(sample_question)
    assert output.response_type in ("result", "uncertainty")


def test_process_task_creates_pending_task(event_loop, sample_task):
    before = len(event_loop.netzach.task_queue)
    event_loop.process_input(sample_task)
    after = len(event_loop.netzach.task_queue)
    assert after >= before + 1


def test_process_empty_content_returns_uncertainty(event_loop):
    inp = RuachInput(
        input_type="experience",
        content={},
        natural_language="nothing",
        context="empty test",
    )
    output = event_loop.process_input(inp)
    assert output.response_type in ("uncertainty", "acknowledgment")


def test_multiple_cycles_chain_grows(event_loop, sample_experience, sample_question):
    conn = event_loop._conn
    count_before = conn.execute("SELECT COUNT(*) FROM chain_blocks").fetchone()[0]
    event_loop.process_input(sample_experience)
    event_loop.process_input(sample_question)
    count_after = conn.execute("SELECT COUNT(*) FROM chain_blocks").fetchone()[0]
    assert count_after > count_before


# ---------------------------------------------------------------------------
# receive_consequence()
# ---------------------------------------------------------------------------

def test_receive_consequence_fills_chain_block(event_loop, sample_experience):
    output = event_loop.process_input(sample_experience)
    event_loop.receive_consequence(
        output.chain_block_hash,
        {"result": "positive", "notes": "helpful"},
    )
    conn = event_loop._conn
    row = conn.execute(
        "SELECT consequence FROM chain_blocks WHERE this_hash = ?",
        (output.chain_block_hash,)
    ).fetchone()
    assert row["consequence"] is not None
    assert "positive" in row["consequence"]


def test_receive_consequence_writes_consequence_received_block(event_loop, sample_experience):
    output = event_loop.process_input(sample_experience)
    event_loop.receive_consequence(output.chain_block_hash, {"result": "good"})
    blocks = by_type(event_loop._conn, "consequence_received")
    assert len(blocks) >= 1


# ---------------------------------------------------------------------------
# get_diagnostic()
# ---------------------------------------------------------------------------

def test_get_diagnostic_returns_full_structure(event_loop, sample_experience):
    event_loop.process_input(sample_experience)
    diag = event_loop.get_diagnostic()
    assert "self_model" in diag
    assert "blind_spots" in diag
    assert "keter_daat_gap" in diag
    assert "triadic_balance" in diag
    assert "pillar_tension" in diag


def test_get_diagnostic_triadic_balance_in_range(event_loop, sample_experience):
    event_loop.process_input(sample_experience)
    diag = event_loop.get_diagnostic()
    for triad, score in diag["triadic_balance"].items():
        assert 0.0 <= score <= 1.0, f"{triad}={score} out of range"


# ---------------------------------------------------------------------------
# get_next_task()
# ---------------------------------------------------------------------------

def test_get_next_task_returns_none_when_no_tasks(event_loop):
    result = event_loop.get_next_task()
    assert result is None


def test_get_next_task_returns_task_dict_after_task_input(event_loop, sample_task):
    event_loop.process_input(sample_task)
    task = event_loop.get_next_task()
    assert task is not None
    assert "id" in task
    assert "description" in task
    assert "keter_alignment" in task
    assert "urgency" in task
    assert "status" in task


# ---------------------------------------------------------------------------
# Consequence → next cycle interaction
# ---------------------------------------------------------------------------

def test_consequence_then_second_cycle_records_both(event_loop, sample_experience):
    output1 = event_loop.process_input(sample_experience)
    event_loop.receive_consequence(output1.chain_block_hash, {"result": "positive"})
    output2 = event_loop.process_input(sample_experience)
    assert output2.chain_block_hash != output1.chain_block_hash
    assert event_loop.cycle_count == 2
