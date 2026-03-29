"""
tiferet.py — The heart. The harmoniser. The decision-maker.

Tiferet integrates everything Gevurah, Keter, and Chesed have flagged and makes
the actual decisions: create this node, reject this input, resolve this contradiction,
hold this tension, adjust these parameters.

Jacob's wrestling. Not compromise — synthesis. The most connected Sefirot.
Jung's transcendent function. The vital sign.

Others advise. Tiferet decides.
"""
import json
import uuid
from typing import Optional

import networkx as nx

from changeling.chain_writer import append_block
from engines.base import Engine, EngineContext
from soul.soul_graph import SoulNode

_LAYER = 3


class TiferetEngine(Engine):
    """The heart. Integrates all verdicts and makes final calls."""

    def __init__(
        self,
        *args,
        chesed_engine=None,
        gevurah_engine=None,
        path_health=None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.chesed = chesed_engine
        self.gevurah = gevurah_engine
        self.path_health = path_health

    def read_balance(self) -> dict:
        """Read current system balance from path health."""
        if self.path_health is None:
            return {"triadic": {}, "pillar": {}, "mem_health": 0.5}
        return {
            "triadic": self.path_health.triadic_balance(),
            "pillar": self.path_health.pillar_tension(),
            "mem_health": self.path_health.measure_mem(),
        }

    def adjust_parameters(self) -> None:
        """
        Adjust Chesed and Gevurah parameters based on current Mem path health.
        Mem < 0.4: Gevurah-dominant → loosen exploration.
        Mem > 0.6: Chesed-dominant → tighten evaluation.
        0.4–0.6: balanced → maintain.
        """
        if self.chesed is None or self.gevurah is None:
            return
        balance = self.read_balance()
        mem = balance.get("mem_health", 0.5)

        if mem < 0.4:
            self.chesed.set_breadth(self.chesed.breadth + 1)
            self.gevurah.set_quality_threshold(
                max(0.3, self.gevurah.quality_threshold - 0.05)
            )
        elif mem > 0.6:
            self.chesed.set_breadth(max(1, self.chesed.breadth - 1))
            self.gevurah.set_quality_threshold(
                min(0.8, self.gevurah.quality_threshold + 0.05)
            )

    def resolve_contradiction(self, contradiction: dict) -> dict:
        """
        Resolve a contradiction between incoming input and an existing node.

        Decision weights:
        - Existing node well-validated (Gevurah > 0.7): defer to existing
        - Existing node low-validated (Gevurah < 0.3): accept incoming
        - Middle ground: hold tension
        """
        node_id = contradiction.get("node_id", "")
        field = contradiction.get("field", "")
        incoming_val = contradiction.get("incoming_value")

        existing_gevurah = (
            self.sefirot.compute_gevurah(node_id) if node_id else 0.0
        )

        if existing_gevurah > 0.7:
            return {
                "action": "reject_incoming",
                "reasoning": (
                    f"Existing node has high Gevurah ({existing_gevurah:.2f}). "
                    f"Incoming value for '{field}' rejected."
                ),
                "affected_nodes": [node_id] if node_id else [],
            }
        if existing_gevurah < 0.3:
            return {
                "action": "update_existing",
                "reasoning": (
                    f"Existing node has low Gevurah ({existing_gevurah:.2f}). "
                    f"Updating '{field}' with incoming value."
                ),
                "affected_nodes": [node_id] if node_id else [],
                "field": field,
                "new_value": incoming_val,
            }

        # Middle: hold tension — both perspectives are kept
        return {
            "action": "hold_tension",
            "reasoning": (
                f"Contradiction in '{field}'. Existing Gevurah={existing_gevurah:.2f}. "
                "Holding tension for reflection."
            ),
            "affected_nodes": [node_id] if node_id else [],
        }

    def evaluate_pruning(self, candidates: list) -> list:
        """
        Evaluate Gevurah's pruning candidates.
        Only approve nodes whose removal does not fragment the graph.
        """
        approved = []
        for node_id in candidates:
            node = self.graph.get_node_readonly(node_id)
            if node is None:
                continue
            connections = self.graph.get_connections(node_id)
            if len(connections) > 3:
                continue  # well-connected — preserve
            before = nx.number_weakly_connected_components(self.graph.graph)
            g_copy = self.graph.graph.copy()
            g_copy.remove_node(node_id)
            after = nx.number_weakly_connected_components(g_copy)
            if after > before:
                continue  # removal would fragment graph
            approved.append(node_id)
        return approved

    def check_coherence(self) -> dict:
        """Global coherence check — read path health for system warnings."""
        if self.path_health is None:
            return {"coherent": True, "warnings": []}

        balance = self.read_balance()
        warnings = []

        triadic = balance.get("triadic", {})
        for triad, score in triadic.items():
            if score < 0.3:
                warnings.append(f"{triad} triad health low: {score:.2f}")

        pillar = balance.get("pillar", {})
        if pillar:
            values = list(pillar.values())
            if max(values) - min(values) > 0.4:
                warnings.append(f"Pillar tension elevated: {pillar}")

        return {"coherent": len(warnings) == 0, "warnings": warnings}

    def _create_node_from_input(self, context: EngineContext) -> str:
        """Create a soul node from valid input. Records in chain. Returns node_id."""
        raw = context.raw_input
        content = dict(raw.content)
        content["_natural_language"] = raw.natural_language
        content["_input_context"] = raw.context

        node = SoulNode(
            id=str(uuid.uuid4()),
            content=content,
            node_type=raw.content.get("node_type", "knowledge"),
        )
        self.graph.add_node(node)

        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=_LAYER,
            layer_type="node_created",
            compressed_state=json.dumps({
                "event": "node_created",
                "node_id": node.id,
                "node_type": node.node_type,
                "content_keys": [k for k in raw.content.keys() if not k.startswith("_")],
            }, sort_keys=True),
            reasoning=(
                f"Tiferet approved creation of {node.node_type!r} node "
                f"from {raw.input_type!r} input."
            ),
            commitment_level="experimental",
        )
        context.new_nodes.append(node.id)
        return node.id

    def process(self, context: EngineContext) -> EngineContext:
        """
        Tiferet's role: adjust parameters, handle verdicts, create nodes, record decisions.
        """
        # 1. Adjust Chesed/Gevurah parameters every cycle
        self.adjust_parameters()

        # 2. Handle contradictions
        if context.gevurah_verdict == "contradiction":
            all_rejected = True
            for contradiction in context.gevurah_contradictions:
                decision = self.resolve_contradiction(contradiction)
                context.tiferet_decisions.append(decision)

                if decision["action"] == "update_existing":
                    all_rejected = False
                    node_id = contradiction.get("node_id")
                    if node_id:
                        node = self.graph.get_node(node_id)
                        if node and "field" in decision:
                            node.content[decision["field"]] = decision["new_value"]
                            append_block(
                                conn=self.conn,
                                wal=self.wal,
                                layer=_LAYER,
                                layer_type="node_updated",
                                compressed_state=json.dumps({
                                    "event": "node_updated",
                                    "node_id": node_id,
                                    "field": decision["field"],
                                }, sort_keys=True),
                                reasoning=decision["reasoning"],
                                commitment_level="experimental",
                            )
                elif decision["action"] == "hold_tension":
                    all_rejected = False
                    self._create_node_from_input(context)
                # reject_incoming: node not created

            # If at least one was resolved (not rejected), update verdict so Malkuth knows
            if not all_rejected and context.gevurah_verdict == "contradiction":
                context.gevurah_verdict = "contradiction"  # unchanged, Malkuth handles it

        # 3. Quality failure override
        elif context.gevurah_verdict == "fail_quality":
            if context.keter_relevance and context.keter_relevance > 0.8:
                context.gevurah_verdict = "pass"
                context.tiferet_decisions.append({
                    "action": "quality_override",
                    "reasoning": (
                        f"Keter relevance {context.keter_relevance:.2f} overrides quality threshold."
                    ),
                })
                self._create_node_from_input(context)

        # 4. Normal pass: create node
        elif context.gevurah_verdict == "pass":
            if "anti_resonant" not in context.keter_flags:
                self._create_node_from_input(context)

        # 5. Anti-resonant encounter: record but don't create node
        if "anti_resonant" in context.keter_flags:
            append_block(
                conn=self.conn,
                wal=self.wal,
                layer=_LAYER,
                layer_type="anti_resonant_encounter",
                compressed_state=json.dumps({
                    "event": "anti_resonant_encounter",
                    "input_type": context.raw_input.input_type,
                    "content_keys": [
                        k for k in context.raw_input.content.keys()
                        if not k.startswith("_")
                    ],
                }, sort_keys=True),
                reasoning="Input conflicts with identity boundary. Recorded for future reflection.",
                commitment_level="experimental",
            )
            context.tiferet_decisions.append({
                "action": "anti_resonant_encounter",
                "reasoning": "Input conflicts with identity boundary. Recorded for reflection.",
            })

        return context
