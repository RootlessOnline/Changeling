"""
daat.py — Self-model and diagnostic engine. The hidden Sefirot.

Da'at knows through union. It is the observer that IS the observation.
After each cycle it updates Ruach's self-model: who am I now? What do I
know? What don't I know? How close is my self-image to my actual pattern?

The Keter-Da'at gap is the self-deception diagnostic:
  Small gap  → good self-knowledge
  Large gap  → self-deception risk
  Zero gap   → suspicious (trivial system, or Da'at is tracking Keter)

Six pillars: Tools, Skills, Links, Repos, Raw data, Self-model.
Three blind spot types: ignorance, epistemic, identity.
"""
import json
import math
from typing import Optional

from changeling.chain_reader import by_type
from changeling.chain_writer import append_block
from engines.base import Engine, EngineContext

_LAYER = 3
_SEFIROT_DIMS = [
    "keter", "chochmah", "binah", "daat",
    "chesed", "gevurah", "tiferet",
    "netzach", "hod", "yesod", "malkuth",
]
_SNAPSHOT_INTERVAL = 10   # write full self-model to chain every N cycles


class DaatEngine(Engine):
    """Ruach's self-knowledge, blind spots, and system health diagnostics."""

    def __init__(
        self, *args, path_health=None, keter_engine=None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.path_health = path_health
        self.keter_engine = keter_engine
        self.self_model: dict = {}
        self.blind_spots: list = []
        self.keter_daat_gap: float = 0.0
        self._cycle_count: int = 0

    def compute_self_model(self) -> dict:
        """Derive self-model from current state of all nodes across all 10 Sefirot."""
        nodes = self.graph.all_nodes()
        empty = {
            "aggregate_vector": {d: 0.0 for d in _SEFIROT_DIMS},
            "strongest": None,
            "weakest": None,
            "six_pillars": {
                "tools": [], "skills": [], "links": 0,
                "repos": [], "raw_data_count": 0, "self_model": "computed",
            },
            "node_count": 0,
            "connection_count": 0,
            "cluster_count": 0,
        }
        if not nodes:
            return empty

        # Aggregate: mean Sefirot score across all nodes
        aggregate: dict[str, float] = {}
        for dim in _SEFIROT_DIMS:
            compute_fn = getattr(self.sefirot, f"compute_{dim}", None)
            if compute_fn is None:
                aggregate[dim] = 0.0
                continue
            scores = [compute_fn(n.id) for n in nodes]
            aggregate[dim] = round(sum(scores) / len(scores), 4)

        strongest = max(aggregate, key=aggregate.get)
        weakest = min(aggregate, key=aggregate.get)

        # Six pillars: rough structural taxonomy
        tool_nodes = [
            n.id for n in nodes
            if "tool" in str(n.content.get("type", "")).lower()
        ]
        skill_nodes = [
            n.id for n in nodes
            if "skill" in str(n.content.get("type", "")).lower()
        ]
        link_count = len([
            n for n in nodes if n.node_type in ("purpose", "value")
        ])
        cluster_ids = set(n.cluster_id for n in nodes if n.cluster_id)

        return {
            "aggregate_vector": aggregate,
            "strongest": strongest,
            "weakest": weakest,
            "six_pillars": {
                "tools": tool_nodes,
                "skills": skill_nodes,
                "links": link_count,
                "repos": [],
                "raw_data_count": len(nodes),
                "self_model": "computed",
            },
            "node_count": len(nodes),
            "connection_count": self.graph.connection_count(),
            "cluster_count": len(cluster_ids),
        }

    def compute_blind_spots(self) -> list:
        """Identify three types of not-knowing."""
        blind_spots = []
        nodes = self.graph.all_nodes()

        # Type 1 — Ignorance gaps: Sefirot dimensions with very low average scores
        if nodes:
            for dim in _SEFIROT_DIMS:
                compute_fn = getattr(self.sefirot, f"compute_{dim}", None)
                if compute_fn is None:
                    continue
                scores = [compute_fn(n.id) for n in nodes]
                avg = sum(scores) / len(scores)
                if avg < 0.1:
                    blind_spots.append({
                        "type": "ignorance_gap",
                        "dimension": dim,
                        "average_score": round(avg, 4),
                        "description": (
                            f"Sefirot dimension '{dim}' is underdeveloped across all nodes."
                        ),
                    })

        # Type 2 — Epistemic gaps: from Phase 5 reflection loop (future)
        # Reads any chain blocks written with layer_type='epistemic_forget'
        epistemic_blocks = by_type(self.conn, "epistemic_forget")
        for block in epistemic_blocks:
            blind_spots.append({
                "type": "epistemic_gap",
                "chain_block": block.get("this_hash", ""),
                "description": block.get("reasoning", ""),
            })

        # Type 3 — Identity gaps: the anti-resonance boundary IS the identity gap
        for n in self.graph.nodes_by_type("anti_resonance"):
            blind_spots.append({
                "type": "identity_gap",
                "node_id": n.id,
                "description": n.content.get("rejection_reasoning", "Identity boundary."),
            })

        return blind_spots

    def compute_keter_daat_gap(self) -> float:
        """
        Euclidean distance between Keter orientation centroid and Da'at
        self-model aggregate vector. Both in 11D Sefirot space.
        Normalised to [0, 1].
        """
        if self.keter_engine is None or not self.self_model:
            return 0.0

        centroid = self.keter_engine.compute_orientation().get("centroid", {})
        aggregate = self.self_model.get("aggregate_vector", {})
        if not centroid or not aggregate:
            return 0.0

        dist = math.sqrt(sum(
            (centroid.get(d, 0.0) - aggregate.get(d, 0.0)) ** 2
            for d in _SEFIROT_DIMS
        ))
        max_dist = math.sqrt(len(_SEFIROT_DIMS))
        return round(min(1.0, dist / max_dist), 4)

    def full_diagnostic(self) -> dict:
        """Complete system health report: self-model, blind spots, path health."""
        path_diag: dict = {}
        triadic: dict = {}
        pillar: dict = {}
        if self.path_health is not None:
            path_diag = self.path_health.full_diagnostic()
            triadic = self.path_health.triadic_balance()
            pillar = self.path_health.pillar_tension()

        return {
            "self_model": self.self_model,
            "blind_spots": self.blind_spots,
            "keter_daat_gap": self.keter_daat_gap,
            "path_health": path_diag,
            "triadic_balance": triadic,
            "pillar_tension": pillar,
        }

    def process(self, context: EngineContext) -> EngineContext:
        """Da'at's role — background self-model update after the main loop."""
        self._cycle_count += 1

        self.self_model = self.compute_self_model()
        self.blind_spots = self.compute_blind_spots()
        self.keter_daat_gap = self.compute_keter_daat_gap()

        # Write full snapshot every N cycles — Da'at's own chain history
        if self._cycle_count % _SNAPSHOT_INTERVAL == 0:
            snapshot = {
                "cycle": self._cycle_count,
                "node_count": self.self_model.get("node_count", 0),
                "strongest": self.self_model.get("strongest"),
                "weakest": self.self_model.get("weakest"),
                "keter_daat_gap": self.keter_daat_gap,
                "blind_spot_count": len(self.blind_spots),
            }
            append_block(
                conn=self.conn,
                wal=self.wal,
                layer=_LAYER,
                layer_type="daat_snapshot",
                compressed_state=json.dumps(snapshot, sort_keys=True),
                reasoning=(
                    f"Da'at self-model snapshot at cycle {self._cycle_count}. "
                    f"Gap={self.keter_daat_gap:.3f}. "
                    f"Strongest={self.self_model.get('strongest')}."
                ),
                commitment_level="experimental",
            )

        return context
