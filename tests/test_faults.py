"""
test_faults.py — Fault checker (Gevurah anticipatory learning function).

Tests that the system correctly surfaces prior failures before attempting
the same type of operation again.
"""

import pytest

from changeling.database import open_db
from changeling.wal import WriteAheadLog
from changeling.chain_writer import append_block, ensure_genesis
from changeling.fault_checker import check, has_faults, summarise_faults


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def wal(tmp_path):
    return WriteAheadLog(tmp_path / "test.wal")


@pytest.fixture
def db(wal):
    conn = open_db(":memory:")
    ensure_genesis(conn, wal)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------

def test_check_returns_faults_for_matching_type(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r", fault="timeout")
    results = check(db, "task")
    assert len(results) == 1
    assert results[0]["fault"] == "timeout"


def test_check_ignores_faults_from_other_types(db, wal):
    append_block(db, wal, layer=1, layer_type="reflection",
                 compressed_state="s", reasoning="r", fault="loop overflow")
    results = check(db, "task")
    assert results == []


def test_check_empty_on_no_faults(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r")  # no fault
    assert check(db, "task") == []


def test_check_with_substring_filter(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r", fault="timeout error")
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s2", reasoning="r2", fault="hash mismatch")

    results = check(db, "task", fault_substring="timeout")
    assert len(results) == 1
    assert "timeout" in results[0]["fault"]


def test_check_substring_no_match(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r", fault="timeout")
    results = check(db, "task", fault_substring="nonexistent")
    assert results == []


def test_check_returns_multiple_faults(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s1", reasoning="r1", fault="error A")
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s2", reasoning="r2", fault="error B")
    results = check(db, "task")
    assert len(results) == 2


def test_check_returns_oldest_first(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s1", reasoning="r1", fault="first")
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s2", reasoning="r2", fault="second")
    results = check(db, "task")
    assert results[0]["fault"] == "first"
    assert results[1]["fault"] == "second"


# ---------------------------------------------------------------------------
# has_faults()
# ---------------------------------------------------------------------------

def test_has_faults_true(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r", fault="something broke")
    assert has_faults(db, "task") is True


def test_has_faults_false(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r")
    assert has_faults(db, "task") is False


def test_has_faults_wrong_type(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r", fault="err")
    assert has_faults(db, "reflection") is False


# ---------------------------------------------------------------------------
# summarise_faults()
# ---------------------------------------------------------------------------

def test_summarise_faults_returns_none_when_clean(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r")
    assert summarise_faults(db, "task") is None


def test_summarise_faults_returns_string_when_faults_exist(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s", reasoning="r", fault="bad input")
    summary = summarise_faults(db, "task")
    assert summary is not None
    assert "bad input" in summary
    assert "task" in summary


def test_summarise_faults_includes_all_faults(db, wal):
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s1", reasoning="r1", fault="error A")
    append_block(db, wal, layer=1, layer_type="task",
                 compressed_state="s2", reasoning="r2", fault="error B")
    summary = summarise_faults(db, "task")
    assert "error A" in summary
    assert "error B" in summary
