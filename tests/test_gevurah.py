"""
test_gevurah.py — GevurahEngine: quality gates, contradiction detection, fault checking.
"""
import pytest
from engines.base import EngineContext, RuachInput
from engines.gevurah import GevurahEngine


# ---------------------------------------------------------------------------
# check_quality()
# ---------------------------------------------------------------------------

def test_check_quality_passes_non_empty_content(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, issues = gevurah.check_quality({"domain": "learning", "value": "something"})
    assert passes is True
    assert issues == []


def test_check_quality_fails_empty_dict(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, issues = gevurah.check_quality({})
    assert passes is False
    assert len(issues) > 0


def test_check_quality_fails_all_null_values(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, issues = gevurah.check_quality({"a": None, "b": None})
    assert passes is False


def test_check_quality_ignores_meta_fields(engine_stack):
    gevurah = engine_stack["gevurah"]
    # Content with only meta-fields (starting with _) should fail
    passes, issues = gevurah.check_quality({"_natural_language": "hello", "_context": "test"})
    assert passes is False


def test_check_quality_passes_with_public_and_meta_mixed(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, issues = gevurah.check_quality(
        {"topic": "real", "_natural_language": "real sentence"}
    )
    assert passes is True


# ---------------------------------------------------------------------------
# check_required_fields()
# ---------------------------------------------------------------------------

def test_required_fields_task_needs_description(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, issues = gevurah.check_required_fields("task", {"description": "do something"})
    assert passes is True


def test_required_fields_task_fails_without_description(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, issues = gevurah.check_required_fields("task", {"priority": "high"})
    assert passes is False
    assert any("description" in i for i in issues)


def test_required_fields_feedback_needs_original_hash(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, _ = gevurah.check_required_fields("feedback", {})
    assert passes is False
    passes, _ = gevurah.check_required_fields("feedback", {"original_hash": "abc123"})
    assert passes is True


def test_required_fields_experience_has_no_required(engine_stack):
    gevurah = engine_stack["gevurah"]
    passes, issues = gevurah.check_required_fields("experience", {})
    assert passes is True


# ---------------------------------------------------------------------------
# detect_contradictions()
# ---------------------------------------------------------------------------

def test_detect_contradictions_empty_when_no_related(engine_stack):
    gevurah = engine_stack["gevurah"]
    contradictions = gevurah.detect_contradictions({"x": "y"}, [])
    assert contradictions == []


def test_detect_contradictions_finds_field_conflict(engine_stack):
    gevurah = engine_stack["gevurah"]
    # "know-1" has domain="learning", subject="graphs"
    # Input claims domain="mathematics" → conflict
    contradictions = gevurah.detect_contradictions(
        {"domain": "mathematics", "subject": "graphs"},
        [("know-1", 0.9, "content_match")],
    )
    domain_conflict = [c for c in contradictions if c["field"] == "domain"]
    assert len(domain_conflict) == 1
    assert domain_conflict[0]["existing_value"] == "learning"
    assert domain_conflict[0]["incoming_value"] == "mathematics"


def test_detect_contradictions_no_conflict_when_values_match(engine_stack):
    gevurah = engine_stack["gevurah"]
    # Same values → no contradiction
    contradictions = gevurah.detect_contradictions(
        {"domain": "learning"},
        [("know-1", 0.9, "content_match")],
    )
    assert contradictions == []


def test_detect_contradictions_ignores_meta_fields(engine_stack):
    gevurah = engine_stack["gevurah"]
    contradictions = gevurah.detect_contradictions(
        {"_natural_language": "something different"},
        [("know-1", 0.9, "content_match")],
    )
    assert contradictions == []


def test_detect_contradictions_ignores_null_values(engine_stack):
    gevurah = engine_stack["gevurah"]
    contradictions = gevurah.detect_contradictions(
        {"domain": None},
        [("know-1", 0.9, "content_match")],
    )
    assert contradictions == []


# ---------------------------------------------------------------------------
# check_faults()
# ---------------------------------------------------------------------------

def test_check_faults_returns_empty_when_no_faults(engine_stack):
    gevurah = engine_stack["gevurah"]
    faults = gevurah.check_faults("experience")
    assert faults == []


def test_check_faults_returns_past_faults(engine_stack):
    from changeling.chain_writer import append_block
    conn = engine_stack["conn"]
    wal = engine_stack["wal"]
    append_block(
        conn=conn, wal=wal, layer=3, layer_type="experience",
        compressed_state="failure test",
        reasoning="test fault",
        fault="something went wrong",
        commitment_level="experimental",
    )
    gevurah = engine_stack["gevurah"]
    faults = gevurah.check_faults("experience")
    assert len(faults) >= 1


# ---------------------------------------------------------------------------
# flag_for_pruning()
# ---------------------------------------------------------------------------

def test_flag_for_pruning_returns_list(engine_stack):
    gevurah = engine_stack["gevurah"]
    candidates = gevurah.flag_for_pruning()
    assert isinstance(candidates, list)


def test_flag_for_pruning_excludes_anti_resonance(chain_with_genesis, tmp_wal, graph_with_anti_resonance):
    from soul.sefirot_engine import SefirotEngine
    se = SefirotEngine(graph_with_anti_resonance, chain_with_genesis)
    gevurah = GevurahEngine(graph_with_anti_resonance, se, chain_with_genesis, tmp_wal)
    candidates = gevurah.flag_for_pruning()
    assert "ar-1" not in candidates


# ---------------------------------------------------------------------------
# set_quality_threshold()
# ---------------------------------------------------------------------------

def test_set_quality_threshold_clamps(engine_stack):
    gevurah = engine_stack["gevurah"]
    gevurah.set_quality_threshold(0.0)
    assert gevurah.quality_threshold == 0.2
    gevurah.set_quality_threshold(1.0)
    assert gevurah.quality_threshold == 0.9


# ---------------------------------------------------------------------------
# process()
# ---------------------------------------------------------------------------

def test_process_verdict_pass_for_valid_input(engine_stack, sample_experience):
    gevurah = engine_stack["gevurah"]
    ctx = EngineContext(raw_input=sample_experience)
    ctx.related_nodes = []
    ctx = gevurah.process(ctx)
    assert ctx.gevurah_verdict == "pass"


def test_process_verdict_fail_quality_for_empty_content(engine_stack):
    gevurah = engine_stack["gevurah"]
    inp = RuachInput(input_type="experience", content={}, natural_language="", context="t")
    ctx = EngineContext(raw_input=inp)
    ctx = gevurah.process(ctx)
    assert ctx.gevurah_verdict == "fail_quality"


def test_process_verdict_contradiction_when_conflict_exists(engine_stack):
    gevurah = engine_stack["gevurah"]
    inp = RuachInput(
        input_type="experience",
        content={"domain": "mathematics"},
        natural_language="mathematics",
        context="test",
    )
    ctx = EngineContext(raw_input=inp)
    ctx.related_nodes = [("know-1", 0.9, "content_match")]
    ctx = gevurah.process(ctx)
    assert ctx.gevurah_verdict == "contradiction"
    assert len(ctx.gevurah_contradictions) > 0
