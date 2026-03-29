"""
test_netzach.py — NetzachEngine: task queue, priority, decay, persistence.
"""
import time
import pytest
from engines.base import EngineContext, RuachInput
from engines.netzach import NetzachEngine, PendingTask
from engines.netzach_persistence import NetzachPersistence


# ---------------------------------------------------------------------------
# PendingTask
# ---------------------------------------------------------------------------

def test_pending_task_defaults(engine_stack):
    task = PendingTask(description={"work": "learn"}, keter_alignment=0.8)
    assert task.status == "pending"
    assert task.urgency == 0.7
    assert task.id != ""


# ---------------------------------------------------------------------------
# add_task() / get_next_task()
# ---------------------------------------------------------------------------

def test_add_task_appears_in_queue(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"action": "study"}, keter_alignment=0.7)
    netzach.add_task(task)
    assert any(t.id == task.id for t in netzach.task_queue)


def test_get_next_task_returns_highest_priority(engine_stack):
    netzach = engine_stack["netzach"]
    low = PendingTask(description={"p": "low"}, keter_alignment=0.1, urgency=0.1)
    high = PendingTask(description={"p": "high"}, keter_alignment=0.9, urgency=0.9)
    netzach.add_task(low)
    netzach.add_task(high)
    next_task = netzach.get_next_task()
    assert next_task.id == high.id


def test_get_next_task_returns_none_when_queue_empty(engine_stack):
    netzach = engine_stack["netzach"]
    # Fresh engine has empty queue
    assert netzach.get_next_task() is None


def test_get_next_task_skips_completed_tasks(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"work": "done"}, keter_alignment=0.8)
    netzach.add_task(task)
    netzach.complete_task(task.id)
    assert netzach.get_next_task() is None


# ---------------------------------------------------------------------------
# complete_task()
# ---------------------------------------------------------------------------

def test_complete_task_sets_status(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"action": "finish"}, keter_alignment=0.6)
    netzach.add_task(task)
    netzach.complete_task(task.id)
    completed = next(t for t in netzach.task_queue if t.id == task.id)
    assert completed.status == "completed"


def test_complete_task_writes_chain_block(engine_stack):
    from changeling.chain_reader import by_type
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"action": "test"}, keter_alignment=0.5)
    netzach.add_task(task)
    netzach.complete_task(task.id)
    blocks = by_type(engine_stack["conn"], "task_completed")
    assert len(blocks) >= 1


# ---------------------------------------------------------------------------
# find_unfinished_business()
# ---------------------------------------------------------------------------

def test_find_unfinished_business_returns_experimental_blocks(engine_stack):
    from changeling.chain_writer import append_block
    conn = engine_stack["conn"]
    wal = engine_stack["wal"]
    append_block(
        conn=conn, wal=wal, layer=3, layer_type="node_created",
        compressed_state='{"node_id": "test"}',
        reasoning="test",
        commitment_level="experimental",
    )
    netzach = engine_stack["netzach"]
    unfinished = netzach.find_unfinished_business()
    assert len(unfinished) >= 1


# ---------------------------------------------------------------------------
# decay_drive()
# ---------------------------------------------------------------------------

def test_decay_drive_reduces_urgency_for_low_keter_task(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"x": "y"}, keter_alignment=0.0, urgency=1.0)
    netzach.add_task(task)
    before = task.urgency
    netzach.decay_drive()
    assert task.urgency < before


def test_decay_drive_barely_affects_high_keter_task(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"x": "y"}, keter_alignment=1.0, urgency=1.0)
    netzach.add_task(task)
    before = task.urgency
    netzach.decay_drive()
    assert task.urgency == before  # keter_alignment=1.0 → decay=0


def test_decay_drive_does_not_go_below_zero(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"x": "y"}, keter_alignment=0.0, urgency=0.01)
    netzach.add_task(task)
    for _ in range(100):
        netzach.decay_drive()
    assert task.urgency >= 0.0


# ---------------------------------------------------------------------------
# process()
# ---------------------------------------------------------------------------

def test_process_creates_task_for_task_input(engine_stack, sample_task):
    netzach = engine_stack["netzach"]
    ctx = EngineContext(raw_input=sample_task)
    ctx.keter_relevance = 0.7
    before = len(netzach.task_queue)
    ctx = netzach.process(ctx)
    assert len(netzach.task_queue) == before + 1
    assert any(u["action"] == "task_created" for u in ctx.netzach_updates)


def test_process_activates_pending_task_on_feedback(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"description": "review"}, keter_alignment=0.6)
    netzach.add_task(task)

    inp = RuachInput(
        input_type="feedback",
        content={"description": "reviewed", "result": "good"},
        natural_language="done",
        context="feedback",
    )
    ctx = EngineContext(raw_input=inp)
    ctx.keter_relevance = 0.5
    ctx = netzach.process(ctx)

    updated_task = next(t for t in netzach.task_queue if t.id == task.id)
    assert updated_task.status == "active"


def test_process_does_not_create_task_for_experience_input(engine_stack, sample_experience):
    netzach = engine_stack["netzach"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.keter_relevance = 0.5
    before = len(netzach.task_queue)
    ctx = netzach.process(ctx)
    assert len(netzach.task_queue) == before


# ---------------------------------------------------------------------------
# NetzachPersistence
# ---------------------------------------------------------------------------

def test_save_and_load_queue_roundtrip(engine_stack):
    netzach = engine_stack["netzach"]
    task1 = PendingTask(description={"work": "a"}, keter_alignment=0.8, urgency=0.9)
    task2 = PendingTask(description={"work": "b"}, keter_alignment=0.4, urgency=0.5)
    netzach.add_task(task1)
    netzach.add_task(task2)

    persistence = NetzachPersistence()
    persistence.save_queue(netzach)

    loaded = persistence.load_queue(engine_stack["conn"])
    assert len(loaded) == 2
    loaded_ids = {t.id for t in loaded}
    assert task1.id in loaded_ids
    assert task2.id in loaded_ids


def test_load_queue_returns_empty_when_no_state(chain_with_genesis):
    persistence = NetzachPersistence()
    loaded = persistence.load_queue(chain_with_genesis)
    assert loaded == []


def test_save_queue_returns_block_with_hash(engine_stack):
    netzach = engine_stack["netzach"]
    task = PendingTask(description={"work": "test"})
    netzach.add_task(task)
    persistence = NetzachPersistence()
    block = persistence.save_queue(netzach)
    assert "this_hash" in block
    assert len(block["this_hash"]) == 64
