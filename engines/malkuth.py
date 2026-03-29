"""
malkuth.py — I/O and consequence tracking. Where the world meets Ruach.

Malkuth opens and closes the event loop. It receives input, bookends the
lightning bolt, and delivers Ruach's structured response. Every output is
stamped with a chain block hash — the anchor for future consequence feedback.

The Shekhinah: Malkuth is where purpose becomes reality and reality becomes
wisdom. The return path begins here.
"""
import json
from typing import Optional

from changeling.chain_writer import append_block
from changeling.chain_writer import record_consequence as _record_consequence
from engines.base import Engine, EngineContext, RuachInput, RuachOutput

_LAYER = 3


class MalkuthEngine(Engine):
    """The I/O layer. First to touch input, last to deliver output."""

    def receive(self, raw_input: RuachInput) -> EngineContext:
        """Parse incoming input into an EngineContext to start the loop."""
        summary = json.dumps({
            "event": "input_received",
            "input_id": raw_input.id,
            "input_type": raw_input.input_type,
            "context": raw_input.context,
            "content_keys": list(raw_input.content.keys()),
            "natural_language_length": len(raw_input.natural_language),
        }, sort_keys=True)

        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=_LAYER,
            layer_type="input_received",
            compressed_state=summary,
            reasoning=(
                f"Malkuth received {raw_input.input_type!r} input. "
                f"Context: {raw_input.context}"
            ),
            commitment_level="experimental",
        )
        return EngineContext(raw_input=raw_input)

    def deliver(self, context: EngineContext) -> RuachOutput:
        """Write output chain block and stamp the hash onto the output."""
        output = context.output
        if output is None:
            raise RuntimeError("deliver() called before output was assembled by process()")

        summary = json.dumps({
            "event": "output_delivered",
            "response_type": output.response_type,
            "confidence": output.confidence,
            "keter_alignment": output.keter_alignment,
            "nodes_affected_count": len(output.nodes_affected),
            "open_questions_count": len(output.open_questions),
        }, sort_keys=True)

        block = append_block(
            conn=self.conn,
            wal=self.wal,
            layer=_LAYER,
            layer_type="output_delivered",
            compressed_state=summary,
            reasoning=output.reasoning,
            commitment_level="sealed" if output.confidence > 0.7 else "experimental",
        )
        output.chain_block_hash = block["this_hash"]
        return output

    def record_consequence(self, output_chain_hash: str, consequence: dict) -> None:
        """When feedback arrives, record it on the original output's chain block."""
        consequence_str = json.dumps(consequence, sort_keys=True)
        _record_consequence(self.conn, output_chain_hash, consequence_str)

        # Record the return-path event separately — wisdom beginning its ascent
        append_block(
            conn=self.conn,
            wal=self.wal,
            layer=_LAYER,
            layer_type="consequence_received",
            compressed_state=json.dumps({
                "event": "consequence_received",
                "original_hash": output_chain_hash,
                "consequence_preview": consequence_str[:200],
            }, sort_keys=True),
            reasoning=(
                "Return path activated. Malkuth receives consequence and initiates wisdom ascent."
            ),
            commitment_level="sealed",
        )

    def process(self, context: EngineContext) -> EngineContext:
        """Assemble RuachOutput from accumulated context."""
        # Determine response type and confidence
        if "anti_resonant" in context.keter_flags:
            response_type = "refusal"
            confidence = 0.9
        elif context.gevurah_verdict == "fail_quality":
            response_type = "uncertainty"
            confidence = 0.3
        elif context.gevurah_verdict == "contradiction":
            # May still have been resolved by Tiferet
            resolved = any(
                d.get("action") in ("update_existing", "hold_tension")
                for d in context.tiferet_decisions
            )
            response_type = "acknowledgment" if resolved else "uncertainty"
            confidence = 0.5 if resolved else 0.4
        elif context.raw_input.input_type == "question":
            response_type = "result" if context.related_nodes else "uncertainty"
            confidence = min(0.8, 0.3 + 0.1 * len(context.related_nodes))
        elif context.raw_input.input_type == "feedback":
            response_type = "acknowledgment"
            confidence = 0.8
        else:
            response_type = "acknowledgment"
            confidence = 0.6 if context.gevurah_verdict == "pass" else 0.4

        # Open questions
        open_questions = []
        if not context.related_nodes and context.raw_input.input_type == "question":
            open_questions.append("No related nodes found — this domain is unexplored.")
        if context.gevurah_contradictions:
            unresolved = [
                c for c in context.gevurah_contradictions
                if not any(
                    d.get("action") == "update_existing"
                    and d.get("affected_nodes", [None])[0] == c.get("node_id")
                    for d in context.tiferet_decisions
                )
            ]
            if unresolved:
                open_questions.append(
                    f"{len(unresolved)} unresolved contradiction(s) flagged for reflection."
                )

        # Sefirot state summary
        sefirot_state = {
            "keter_relevance": context.keter_relevance,
            "keter_flags": list(context.keter_flags),
            "gevurah_verdict": context.gevurah_verdict,
            "tiferet_decisions_count": len(context.tiferet_decisions),
            "related_nodes_found": len(context.related_nodes),
        }

        # Reasoning chain
        parts = []
        if context.keter_relevance is not None:
            parts.append(f"Keter={context.keter_relevance:.2f}")
        if context.keter_flags:
            parts.append(f"flags={context.keter_flags}")
        if context.gevurah_verdict:
            parts.append(f"Gevurah={context.gevurah_verdict}")
        for d in context.tiferet_decisions:
            parts.append(f"Tiferet:{d.get('action', '?')}")
        if context.new_nodes:
            parts.append(f"nodes_created={len(context.new_nodes)}")
        reasoning = " | ".join(parts) if parts else "Processing complete."

        # Content
        content: dict = {
            "input_type": context.raw_input.input_type,
        }
        if context.new_nodes:
            content["created_nodes"] = context.new_nodes
        if context.related_nodes:
            content["related_nodes"] = [
                item[0] if isinstance(item, tuple) else item
                for item in context.related_nodes[:5]
            ]
        if context.raw_input.input_type == "question" and context.related_nodes:
            content["answer_nodes"] = [
                item[0] if isinstance(item, tuple) else item
                for item in context.related_nodes[:3]
            ]

        nodes_affected = list(context.new_nodes) + [
            item[0] if isinstance(item, tuple) else item
            for item in context.related_nodes
        ]
        # Deduplicate while preserving order
        seen: set = set()
        unique_affected = []
        for n in nodes_affected:
            if n not in seen:
                seen.add(n)
                unique_affected.append(n)

        context.output = RuachOutput(
            response_type=response_type,
            content=content,
            reasoning=reasoning,
            confidence=confidence,
            keter_alignment=context.keter_relevance or 0.0,
            open_questions=open_questions,
            sefirot_state=sefirot_state,
            nodes_affected=unique_affected,
        )
        return context
