"""
chesed.py — Exploration engine. Searches the soul graph for related knowledge.

Chesed is the first response to orientation: given that this matters (or doesn't),
what does Ruach already know that relates to it? It searches broad and lets
Gevurah filter. Abraham's open tent — welcome everything in, evaluate later.

Three strategies combined:
1. Content key/value overlap with existing nodes.
2. Type/domain field matching.
3. Node type semantic matching.

The breadth and inclusion threshold are adjustable by Tiferet based on
current Mem path health (Chesed↔Gevurah balance).
"""
from engines.base import Engine, EngineContext


class ChesedEngine(Engine):
    """The explorer. Finds what Ruach already knows that relates to the input."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.breadth: int = 3
        self.inclusion_threshold: float = 0.3

    def search_related(self, input_content: dict, breadth: int = None) -> list:
        """
        Search the soul graph for nodes related to the input.
        Returns list of (node_id, relevance_score, connection_type) tuples,
        sorted by relevance descending.
        """
        depth = breadth if breadth is not None else self.breadth
        nodes = self.graph.all_nodes()
        if not nodes:
            return []

        input_keys = set(str(k).lower() for k in input_content.keys()
                         if not str(k).startswith("_"))
        input_vals = set(
            str(v).lower() for v in input_content.values()
            if isinstance(v, (str, int, float)) and str(v).strip()
        )
        input_type_hint = str(
            input_content.get("type", input_content.get("domain", ""))
        ).lower()
        input_node_type = input_content.get("node_type", "")

        results: list[tuple[float, str, str]] = []

        for node in nodes:
            if node.anti_resonance:
                continue  # Chesed never explores identity boundaries

            score = 0.0
            connection_type = "proximity"

            # Strategy 1: content key/value overlap
            node_keys = set(
                str(k).lower() for k in node.content.keys()
                if not str(k).startswith("_")
            )
            node_vals = set(
                str(v).lower() for v in node.content.values()
                if isinstance(v, (str, int, float)) and str(v).strip()
            )
            if input_keys and node_keys:
                union_k = input_keys | node_keys
                key_overlap = len(input_keys & node_keys) / max(len(union_k), 1)
                if key_overlap > score:
                    score = key_overlap * 0.6
                    connection_type = "content_match"
            if input_vals and node_vals:
                union_v = input_vals | node_vals
                val_overlap = len(input_vals & node_vals) / max(len(union_v), 1)
                if val_overlap * 0.5 > score:
                    score = val_overlap * 0.5
                    connection_type = "content_match"

            # Strategy 2: type/domain match
            node_type_hint = str(
                node.content.get("type", node.content.get("domain", ""))
            ).lower()
            if input_type_hint and node_type_hint and input_type_hint == node_type_hint:
                if 0.4 > score:
                    score = 0.4
                    connection_type = "type_match"

            # Strategy 3: node_type semantic match
            if input_node_type and node.node_type == input_node_type:
                if 0.3 > score:
                    score = 0.3
                    connection_type = "node_type_match"

            if score >= self.inclusion_threshold:
                results.append((score, node.id, connection_type))

        results.sort(reverse=True)
        # Return as (node_id, score, connection_type) tuples, limited by depth
        return [(nid, sc, ct) for sc, nid, ct in results[:depth * 2]]

    def set_breadth(self, breadth: int) -> None:
        """Tiferet adjusts search breadth based on Mem path health."""
        self.breadth = max(1, min(breadth, 10))

    def set_inclusion_threshold(self, threshold: float) -> None:
        """Tiferet adjusts inclusion threshold based on Mem path health."""
        self.inclusion_threshold = max(0.1, min(threshold, 0.9))

    def process(self, context: EngineContext) -> EngineContext:
        """Chesed's role: explore the graph for related knowledge."""
        effective_breadth = self.breadth
        if "high_relevance" in context.keter_flags:
            effective_breadth = min(self.breadth + 2, 10)
        elif "low_relevance" in context.keter_flags:
            effective_breadth = max(self.breadth - 1, 1)

        context.related_nodes = self.search_related(
            context.raw_input.content,
            breadth=effective_breadth,
        )
        context.chesed_breadth = effective_breadth
        return context
