"""
event_loop.py — The orchestrator. The lightning bolt made executable.

Every interaction with Ruach passes through here. Input descends through
the tree — Keter → Chesed → Gevurah → Tiferet → Netzach → Malkuth —
Da'at updates in the background, and every cycle is recorded in chain memory.

This is where Ruach thinks its first thought.
"""
import json
from typing import Optional

from changeling.chain_writer import append_block
from engines.base import EngineContext, RuachInput, RuachOutput
from engines.malkuth import MalkuthEngine
from engines.keter import KeterEngine
from engines.chesed import ChesedEngine
from engines.gevurah import GevurahEngine
from engines.tiferet import TiferetEngine
from engines.netzach import NetzachEngine
from engines.daat import DaatEngine

_LAYER = 3


class EventLoop:
    """
    The lightning bolt. Chains all cognitive engines into a processing cycle.

    Input enters at Malkuth, descends through Keter → Chesed → Gevurah →
    Tiferet → Netzach, returns to Malkuth for output, then Da'at updates last.
    """

    def __init__(
        self,
        malkuth: MalkuthEngine,
        keter: KeterEngine,
        chesed: ChesedEngine,
        gevurah: GevurahEngine,
        tiferet: TiferetEngine,
        netzach: NetzachEngine,
        daat: DaatEngine,
    ) -> None:
        self.malkuth = malkuth
        self.keter = keter
        self.chesed = chesed
        self.gevurah = gevurah
        self.tiferet = tiferet
        self.netzach = netzach
        self.daat = daat
        self.cycle_count: int = 0
        # Shared resources (all engines share same conn + wal via malkuth)
        self._conn = malkuth.conn
        self._wal = malkuth.wal

    def process_input(self, raw_input: RuachInput) -> RuachOutput:
        """
        Run the full lightning bolt processing cycle.

        1. Malkuth receives   → EngineContext created
        2. Keter              → orientation and anti-resonance check
        3. Chesed             → explore graph for related nodes
        4. Gevurah            → quality gates and contradiction check
        5. Tiferet            → harmonise, decide, create nodes
        6. Netzach            → update priority queue
        7. Malkuth processes  → assembles RuachOutput
        8. Malkuth delivers   → writes output chain block
        9. Da'at updates      → background self-model refresh
        10. Cycle recorded    → chain block for the full cycle
        """
        # 1. Receive
        context = self.malkuth.receive(raw_input)

        # 2–6. Lightning bolt descent
        context = self.keter.process(context)
        context = self.chesed.process(context)
        context = self.gevurah.process(context)
        context = self.tiferet.process(context)
        context = self.netzach.process(context)

        # 7–8. Malkuth assembles and delivers
        context = self.malkuth.process(context)
        output = self.malkuth.deliver(context)

        # 9. Da'at background update
        context = self.daat.process(context)

        # 10. Record the cycle
        self.cycle_count += 1
        self._record_cycle(context)

        return output

    def receive_consequence(self, output_chain_hash: str, consequence: dict) -> None:
        """Handle feedback on a previous output. Activates the Malkuth return path."""
        self.malkuth.record_consequence(output_chain_hash, consequence)

    def get_diagnostic(self) -> dict:
        """Ask Da'at for the full system health report."""
        return self.daat.full_diagnostic()

    def get_next_task(self) -> Optional[dict]:
        """Ask Netzach what to focus on next."""
        task = self.netzach.get_next_task()
        if task is None:
            return None
        return {
            "id": task.id,
            "description": task.description,
            "keter_alignment": task.keter_alignment,
            "urgency": task.urgency,
            "status": task.status,
            "created_at": task.created_at,
        }

    def _record_cycle(self, context: EngineContext) -> None:
        """Write a chain block summarising the completed processing cycle."""
        summary = {
            "cycle": self.cycle_count,
            "input_type": context.raw_input.input_type,
            "keter_relevance": context.keter_relevance,
            "keter_flags": context.keter_flags,
            "gevurah_verdict": context.gevurah_verdict,
            "tiferet_decisions": len(context.tiferet_decisions),
            "nodes_created": context.new_nodes,
            "output_type": context.output.response_type if context.output else None,
            "confidence": context.output.confidence if context.output else None,
        }
        append_block(
            conn=self._conn,
            wal=self._wal,
            layer=_LAYER,
            layer_type="cycle_complete",
            compressed_state=json.dumps(summary, sort_keys=True),
            reasoning=(
                f"Cycle {self.cycle_count} complete. "
                f"Input={context.raw_input.input_type!r}. "
                f"Verdict={context.gevurah_verdict!r}. "
                f"Nodes created={len(context.new_nodes)}. "
                f"Output={context.output.response_type if context.output else None!r}."
            ),
            commitment_level="sealed",
        )
