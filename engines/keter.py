"""
keter.py — Orientation and anti-resonance engine. The compass.

Keter determines what matters. Before any processing, Keter asks two questions:
  "Is this relevant to who I am?" → relevance score
  "Does this conflict with who I am not?" → anti-resonance check

Without an LLM, relevance is structural: content field overlap with purpose
and value nodes, type/domain matching, and orientation centroid proximity.

Anti-resonance is identity, not error handling. A refusal from Keter should
explain itself. Even pre-verbal, Ruach can state why it won't process something.
"""
import math
from typing import Optional, Tuple

from engines.base import Engine, EngineContext

_KETER_THRESHOLD = 0.5
_RELEVANCE_HIGH = 0.6
_SEFIROT_DIMS = [
    "keter", "chochmah", "binah", "daat",
    "chesed", "gevurah", "tiferet",
    "netzach", "hod", "yesod", "malkuth",
]


class KeterEngine(Engine):
    """The compass. Determines what matters and what is refused at identity level."""

    def compute_orientation(self) -> dict:
        """Compute current orientation vector from all high-Keter nodes."""
        nodes = self.graph.all_nodes()
        attractors = [
            n for n in nodes
            if not n.anti_resonance
            and self.sefirot.compute_keter(n.id) > _KETER_THRESHOLD
        ]
        if not attractors:
            return {
                "centroid": {d: 0.0 for d in _SEFIROT_DIMS},
                "contributing_nodes": [],
            }

        weights = [self.sefirot.compute_keter(n.id) for n in attractors]
        total_weight = sum(weights)
        centroid = {}
        for dim in _SEFIROT_DIMS:
            centroid[dim] = sum(
                w * self.sefirot.compute_full_vector(n.id).get(dim, 0.0)
                for n, w in zip(attractors, weights)
            ) / total_weight

        return {
            "centroid": centroid,
            "contributing_nodes": [n.id for n in attractors],
        }

    def get_anti_resonance_boundary(self) -> list:
        """Return all anti-resonance nodes with their content and rejection reasoning."""
        return [
            {
                "node_id": n.id,
                "content": n.content,
                "reasoning": n.content.get("rejection_reasoning", "Identity boundary."),
            }
            for n in self.graph.nodes_by_type("anti_resonance")
        ]

    def score_relevance(self, input_content: dict) -> float:
        """
        How relevant is this input to current orientation?

        Two strategies combined:
        1. Content key/value overlap with purpose and value nodes.
        2. Type/domain field matching against any existing node.

        In early phases the graph is small and scores will be coarse.
        This refines as the graph grows and the orientation vector fills in.
        """
        nodes = self.graph.all_nodes()
        if not nodes:
            return 0.3  # no graph = neutral

        input_keys = set(str(k).lower() for k in input_content.keys())
        input_vals = set(
            str(v).lower() for v in input_content.values()
            if isinstance(v, (str, int, float))
        )

        # Strategy 1: overlap with purpose/value nodes (orientation anchors)
        anchor_nodes = [
            n for n in nodes
            if n.node_type in ("purpose", "value") and not n.anti_resonance
        ]
        content_score = 0.0
        if anchor_nodes:
            for n in anchor_nodes:
                node_keys = set(str(k).lower() for k in n.content.keys())
                node_vals = set(
                    str(v).lower() for v in n.content.values()
                    if isinstance(v, (str, int, float))
                )
                union_k = input_keys | node_keys
                union_v = input_vals | node_vals
                key_ov = len(input_keys & node_keys) / max(len(union_k), 1)
                val_ov = len(input_vals & node_vals) / max(len(union_v), 1)
                content_score = max(content_score, key_ov * 0.6 + val_ov * 0.4)

        # Strategy 2: type/domain field match against all nodes
        input_type_hint = str(
            input_content.get("type", input_content.get("domain", ""))
        ).lower()
        type_score = 0.0
        if input_type_hint:
            for n in nodes:
                n_hint = str(
                    n.content.get("type", n.content.get("domain", ""))
                ).lower()
                if n_hint and n_hint == input_type_hint:
                    type_score = 0.5
                    break

        raw = max(content_score, type_score)

        # Boost if orientation is established (centroid has magnitude)
        orientation = self.compute_orientation()
        centroid_magnitude = math.sqrt(
            sum(v ** 2 for v in orientation["centroid"].values())
        )
        if centroid_magnitude > 0.1:
            raw = min(1.0, raw + 0.1)

        return round(max(0.0, min(1.0, raw)), 4)

    def check_anti_resonance(self, input_content: dict) -> Tuple[bool, Optional[str]]:
        """
        Does this input conflict with identity boundaries?
        Checks input content field overlap against anti-resonance node markers.
        """
        boundary = self.get_anti_resonance_boundary()
        if not boundary:
            return False, None

        input_keys = set(str(k).lower() for k in input_content.keys())
        input_vals = set(
            str(v).lower() for v in input_content.values()
            if isinstance(v, (str, int, float))
        )

        for entry in boundary:
            node_content = entry["content"]
            # Exclude meta-fields from matching
            skip_keys = {"rejection_reasoning", "_natural_language", "_input_context"}
            boundary_vals = set(
                str(v).lower() for k, v in node_content.items()
                if k not in skip_keys and isinstance(v, (str, int, float))
                and str(v).strip()
            )

            # Anti-resonance triggers on value overlap — not key overlap.
            # "domain" is a generic structural key; the identity marker is the VALUE.
            if boundary_vals & input_vals:
                reason = entry.get("reasoning", "Identity boundary.")
                return True, reason

        return False, None

    def process(self, context: EngineContext) -> EngineContext:
        """Keter's role in the event loop."""
        context.keter_relevance = self.score_relevance(context.raw_input.content)

        is_anti, reason = self.check_anti_resonance(context.raw_input.content)
        if is_anti:
            context.keter_flags.append("anti_resonant")
            # Store reason in content for Malkuth to include in refusal
            context.raw_input.content["_anti_resonance_reason"] = reason
        elif context.keter_relevance > _RELEVANCE_HIGH:
            context.keter_flags.append("high_relevance")
        else:
            context.keter_flags.append("low_relevance")

        return context
