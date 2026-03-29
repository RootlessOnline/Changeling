"""
gevurah.py — Quality gates, fault detection, contradiction detection.

Gevurah is the judge. It does not halt processing — it flags. Tiferet
makes the final call. Every flag is recorded reasoning, not a shutdown command.

Isaac's binding. Strict justice. Four functions:
1. Quality check: does the input have the structural minimum?
2. Required fields check: does this input_type have its mandatory fields?
3. Fault check: have we failed on inputs like this before?
4. Contradiction check: does this conflict with existing validated knowledge?
"""
import json
from typing import Tuple

from changeling.fault_checker import check as fault_check
from engines.base import Engine, EngineContext

# Required fields per input_type
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "experience": [],
    "question": [],
    "feedback": ["original_hash"],
    "task": ["description"],
    "correction": [],
}


class GevurahEngine(Engine):
    """The judge. Quality gates, fault memory, contradiction detection."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.quality_threshold: float = 0.5

    def check_quality(self, input_content: dict) -> Tuple[bool, list]:
        """Does this input meet minimum quality standards?"""
        issues = []
        # Exclude internal meta-fields when checking emptiness
        public = {k: v for k, v in input_content.items() if not str(k).startswith("_")}
        if not public:
            issues.append("content is empty")
            return False, issues
        non_empty = [
            v for v in public.values()
            if v is not None and v != "" and v != [] and v != {}
        ]
        if not non_empty:
            issues.append("all content fields are empty or null")
            return False, issues
        return True, issues

    def check_required_fields(self, input_type: str, input_content: dict) -> Tuple[bool, list]:
        """Check type-specific required fields."""
        required = _REQUIRED_FIELDS.get(input_type, [])
        missing = [
            f for f in required
            if f not in input_content or input_content[f] is None
        ]
        if missing:
            return False, [f"Missing required field(s) for {input_type!r}: {missing}"]
        return True, []

    def detect_contradictions(self, input_content: dict, related_nodes: list) -> list:
        """
        Does this input contradict existing validated nodes?
        Compares matching content fields for direct value conflicts.
        Ignores internal meta-fields (prefixed with _).
        """
        contradictions = []
        # Filter to public fields only
        public_input = {
            k: v for k, v in input_content.items()
            if not str(k).startswith("_")
        }

        for item in related_nodes:
            node_id = item[0] if isinstance(item, tuple) else item
            node = self.graph.get_node_readonly(node_id)
            if node is None:
                continue
            for key in public_input:
                if key not in node.content:
                    continue
                incoming_str = str(public_input[key]).lower().strip()
                existing_str = str(node.content[key]).lower().strip()
                # Only flag substantive conflicts
                if (
                    incoming_str != existing_str
                    and incoming_str not in ("none", "null", "")
                    and existing_str not in ("none", "null", "")
                    and len(incoming_str) > 1
                    and len(existing_str) > 1
                ):
                    contradictions.append({
                        "node_id": node_id,
                        "field": key,
                        "existing_value": node.content[key],
                        "incoming_value": public_input[key],
                    })
        return contradictions

    def check_faults(self, layer_type: str) -> list:
        """Check for past faults of this operation type via Phase 1 fault_checker."""
        return fault_check(self.conn, layer_type)

    def flag_for_pruning(self) -> list:
        """
        Find nodes with low scores across Gevurah, Netzach, and Malkuth.
        Returns candidate node IDs — Tiferet evaluates whether to approve.
        """
        candidates = []
        for node in self.graph.all_nodes():
            if node.anti_resonance:
                continue
            if (
                self.sefirot.compute_gevurah(node.id) < 0.2
                and self.sefirot.compute_netzach(node.id) < 0.2
                and self.sefirot.compute_malkuth(node.id) < 0.1
            ):
                candidates.append(node.id)
        return candidates

    def set_quality_threshold(self, threshold: float) -> None:
        """Tiferet adjusts this based on current system balance."""
        self.quality_threshold = max(0.2, min(threshold, 0.9))

    def process(self, context: EngineContext) -> EngineContext:
        """Gevurah's role in the event loop."""
        # Fault check — anticipatory learning
        context.gevurah_faults = self.check_faults(context.raw_input.input_type)

        # Quality + required fields check
        passes_quality, quality_issues = self.check_quality(context.raw_input.content)
        passes_required, required_issues = self.check_required_fields(
            context.raw_input.input_type, context.raw_input.content
        )

        if not passes_quality or not passes_required:
            context.gevurah_verdict = "fail_quality"
            return context  # Don't halt — Tiferet may override

        # Contradiction check against related nodes
        if context.related_nodes:
            contradictions = self.detect_contradictions(
                context.raw_input.content,
                context.related_nodes,
            )
            if contradictions:
                context.gevurah_verdict = "contradiction"
                context.gevurah_contradictions = contradictions
                return context

        context.gevurah_verdict = "pass"
        return context
