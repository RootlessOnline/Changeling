"""
path_health.py — The 22 path monitoring system. Da'at's diagnostic eye.

Paths are living connections. Their health tells stories:
  - All Mother paths healthy = triads internally balanced
  - Right-column Doubles strong / Left weak = growth without quality
  - Ascending weaker than descending = creates but doesn't learn
  - Descending weaker than ascending = reflects beautifully but can't create

Da'at reads flow topology, not individual numbers.

Three tiers of paths:
  Mother  (3): elemental, most load-bearing — Aleph, Mem, Shin
  Double  (7): polar, bidirectional with different directional qualities
  Simple (12): functional, specific cognitive operations

Triadic balance IS the Mother path health.
Pillar tension IS the aggregate path health per pillar.
"""

import sqlite3
import statistics
from typing import Optional

from soul.soul_graph import SoulGraph
from soul.sefirot_engine import SefirotEngine, DIMENSIONS

# ---------------------------------------------------------------------------
# Path topology constants
# ---------------------------------------------------------------------------

# Which Sefirot each path connects (for aggregate computations)
PILLAR_PATHS = {
    "right":  ["bet", "kaph", "heh", "yod"],          # Expansion pillar paths
    "left":   ["dalet", "peh", "zayin"],               # Severity pillar paths
    "middle": ["gimel", "resh", "tav"],                # Balance pillar paths
}

# Sefirot aligned per pillar (for identifying which nodes contribute to which pillar)
PILLAR_SEFIROT = {
    "right":  ["chochmah", "chesed", "netzach"],
    "left":   ["binah", "gevurah", "hod"],
    "middle": ["keter", "daat", "tiferet", "yesod", "malkuth"],
}


class PathHealth:
    """
    Monitors all 22 paths of the Tree of Life.

    Uses the SefirotEngine to compute current Sefirot vectors across the
    graph, then measures path health from the aggregate flow quality between
    relevant nodes.
    """

    def __init__(
        self,
        graph: SoulGraph,
        engine: SefirotEngine,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        self.graph = graph
        self.engine = engine
        self.conn = conn

    # ------------------------------------------------------------------
    # Mother Paths — most load-bearing
    # ------------------------------------------------------------------

    def measure_aleph(self) -> float:
        """
        Aleph (א) — Chochmah ↔ Binah. Air. The Supernal heartbeat.

        Healthy: high-Chochmah nodes are complemented by high-Binah nodes
        in the graph. Measures the balance between emergence and structure.

        With chain data: measures temporal gap between node creation (Chochmah
        event) and first structural revision (Binah processing). Healthy gap
        = 1-10 cycles. 0 = premature crystallisation. Never = dissipation.
        Without chain: measures the ratio of Chochmah vs Binah scores across
        all nodes — a balanced graph has both.
        """
        if self.conn is not None:
            return self._aleph_from_chain()
        return self._aleph_from_graph()

    def _aleph_from_graph(self) -> float:
        nodes = self.graph.all_nodes()
        if not nodes:
            return 0.5
        chochmah_scores = [self.engine.compute_chochmah(n.id) for n in nodes]
        binah_scores = [self.engine.compute_binah(n.id) for n in nodes]
        avg_c = sum(chochmah_scores) / len(chochmah_scores)
        avg_b = sum(binah_scores) / len(binah_scores)
        # Balance: both should be non-zero and similar
        if avg_c + avg_b == 0:
            return 0.5
        balance = 1.0 - abs(avg_c - avg_b) / (avg_c + avg_b)
        presence = min(1.0, (avg_c + avg_b))
        return (balance + presence) / 2.0

    def _aleph_from_chain(self) -> float:
        """Temporal gap between node_added and first node_updated events."""
        try:
            added = self.conn.execute(
                "SELECT compressed_state, timestamp FROM chain_blocks WHERE layer_type='node_event' ORDER BY id ASC"
            ).fetchall()
        except Exception:
            return self._aleph_from_graph()

        import json
        creation_times: dict[str, str] = {}
        update_times: dict[str, str] = {}
        for row in added:
            try:
                data = json.loads(row[0])
                nid = data.get("node_id", "")
                event = data.get("event", "")
                if event == "added" and nid not in creation_times:
                    creation_times[nid] = row[1]
                elif event == "updated" and nid not in update_times:
                    update_times[nid] = row[1]
            except (json.JSONDecodeError, AttributeError):
                continue

        gaps = []
        for nid, created in creation_times.items():
            if nid in update_times:
                from soul.sefirot_engine import _days_since
                created_days = _days_since(created)
                updated_days = _days_since(update_times[nid])
                gap = abs(created_days - updated_days)
                gaps.append(gap)

        if not gaps:
            return self._aleph_from_graph()

        avg_gap = sum(gaps) / len(gaps)
        # Healthy gap: ~1-10 cycles (days). Normalise.
        if avg_gap < 0.001:
            return 0.3   # premature crystallisation
        if avg_gap > 30:
            return 0.3   # dissipation
        return min(1.0, 0.5 + (avg_gap / 10.0) * 0.5)

    def measure_mem(self) -> float:
        """
        Mem (מ) — Chesed ↔ Gevurah. Water. The Ethical flow.

        Healthy: the graph oscillates between exploration (Chesed events =
        node additions) and evaluation (Gevurah events = fault checks, pruning).
        Stuck in one mode = pathological (ice or steam).
        Measures variance of the Chesed/Gevurah ratio over time.
        """
        nodes = self.graph.all_nodes()
        if not nodes:
            return 0.5
        chesed_scores = [self.engine.compute_chesed(n.id) for n in nodes]
        gevurah_scores = [self.engine.compute_gevurah(n.id) for n in nodes]
        avg_c = sum(chesed_scores) / len(chesed_scores)
        avg_g = sum(gevurah_scores) / len(gevurah_scores)
        if avg_c + avg_g == 0:
            return 0.5
        # Both present + balanced = healthy flow
        balance = 1.0 - abs(avg_c - avg_g) / (avg_c + avg_g)
        presence = min(1.0, avg_c + avg_g)
        return (balance * 0.6 + presence * 0.4)

    def measure_shin(self) -> float:
        """
        Shin (ש) — Netzach ↔ Hod. Fire. The Astral transformation.

        Healthy: drive and expression are correlated. Active nodes should
        also be articulate. Measures Pearson correlation between Netzach
        and Hod scores across all nodes.
        """
        nodes = self.graph.all_nodes()
        if len(nodes) < 2:
            return 0.5
        netzach_scores = [self.engine.compute_netzach(n.id) for n in nodes]
        hod_scores = [self.engine.compute_hod(n.id) for n in nodes]

        try:
            corr = statistics.correlation(netzach_scores, hod_scores)
            # Correlation in [-1, 1] → normalise to [0, 1]
            return (corr + 1.0) / 2.0
        except statistics.StatisticsError:
            return 0.5

    # ------------------------------------------------------------------
    # Double Paths — bidirectional, directional quality matters
    # ------------------------------------------------------------------

    def measure_bet(self) -> dict:
        """Bet (ב) — Keter → Chochmah. Purpose establishing creative space."""
        return self._double_path("keter", "chochmah")

    def measure_gimel(self) -> dict:
        """Gimel (ג) — Keter → Tiferet. Intuitive ethical judgment channel."""
        return self._double_path("keter", "tiferet")

    def measure_dalet(self) -> dict:
        """Dalet (ד) — Keter → Binah. Purpose constraining analytical focus."""
        return self._double_path("keter", "binah")

    def measure_kaph(self) -> dict:
        """Kaph (כ) — Chesed → Netzach. Exploration becoming sustained pursuit."""
        return self._double_path("chesed", "netzach")

    def measure_peh(self) -> dict:
        """Peh (פ) — Gevurah → Hod. Judgment becoming precise expression."""
        return self._double_path("gevurah", "hod")

    def measure_resh(self) -> dict:
        """Resh (ר) — Tiferet → Yesod. Integrity path — values becoming behaviour."""
        return self._double_path("tiferet", "yesod")

    def measure_tav(self) -> dict:
        """Tav (ת) — Yesod → Malkuth. Final step: consolidation to manifestation."""
        return self._double_path("yesod", "malkuth")

    def _double_path(self, source_dim: str, target_dim: str) -> dict:
        """
        Measure a Double path bidirectionally.
        Descending (source→target): source dimension average → target average.
        Ascending (target→source): return influence.
        """
        nodes = self.graph.all_nodes()
        if not nodes:
            return {"descending": 0.5, "ascending": 0.5}

        source_scores = [self._dimension_score(n.id, source_dim) for n in nodes]
        target_scores = [self._dimension_score(n.id, target_dim) for n in nodes]

        avg_s = sum(source_scores) / len(source_scores)
        avg_t = sum(target_scores) / len(target_scores)

        # Descending: does source dimension support target dimension?
        # Measured as: when source is high, is target also present?
        high_source_nodes = [n for n in nodes if self._dimension_score(n.id, source_dim) > 0.4]
        if high_source_nodes:
            desc = sum(self._dimension_score(n.id, target_dim) for n in high_source_nodes) / len(high_source_nodes)
        else:
            desc = avg_t * 0.5

        # Ascending: does target dimension feed back to source?
        high_target_nodes = [n for n in nodes if self._dimension_score(n.id, target_dim) > 0.4]
        if high_target_nodes:
            asc = sum(self._dimension_score(n.id, source_dim) for n in high_target_nodes) / len(high_target_nodes)
        else:
            asc = avg_s * 0.5

        return {"descending": round(desc, 4), "ascending": round(asc, 4)}

    def _dimension_score(self, node_id: str, dim: str) -> float:
        method = getattr(self.engine, f"compute_{dim}", None)
        if method is None:
            return 0.0
        return method(node_id)

    # ------------------------------------------------------------------
    # Simple Paths — diagonal web
    # ------------------------------------------------------------------

    def measure_simple_path(self, path_name: str) -> float:
        """
        Generic measurement for Simple paths. Measures the density of
        connections of this path type and the health of nodes at both ends.
        """
        _SIMPLE_PATH_DIMS = {
            "heh":    ("chochmah", "chesed"),
            "vav":    ("chochmah", "tiferet"),
            "zayin":  ("binah",    "gevurah"),
            "chet":   ("binah",    "tiferet"),
            "tet":    ("chesed",   "tiferet"),
            "yod":    ("chesed",   "netzach"),
            "lamed":  ("gevurah",  "tiferet"),
            "nun":    ("tiferet",  "netzach"),
            "samekh": ("tiferet",  "yesod"),
            "ayin":   ("tiferet",  "hod"),
            "tzadi":  ("netzach",  "yesod"),
            "qoph":   ("hod",      "yesod"),
        }
        dims = _SIMPLE_PATH_DIMS.get(path_name)
        if dims is None:
            return 0.5
        result = self._double_path(dims[0], dims[1])
        return (result["descending"] + result["ascending"]) / 2.0

    # ------------------------------------------------------------------
    # Aggregate diagnostics
    # ------------------------------------------------------------------

    def triadic_balance(self) -> dict:
        """
        Triadic balance IS the Mother path health.
        Returns the three Mother path scores keyed by triad name.
        """
        return {
            "supernal": self.measure_aleph(),   # Chochmah-Binah
            "ethical":  self.measure_mem(),     # Chesed-Gevurah
            "astral":   self.measure_shin(),    # Netzach-Hod
        }

    def pillar_tension(self) -> dict:
        """
        Pillar tension = aggregate health of paths on each pillar, compared.
        Large imbalances between pillars indicate developmental strain.
        """
        right_scores = [
            self.measure_bet()["descending"],
            self.measure_kaph()["descending"],
            self.measure_simple_path("heh"),
            self.measure_simple_path("yod"),
        ]
        left_scores = [
            self.measure_dalet()["descending"],
            self.measure_peh()["descending"],
            self.measure_simple_path("zayin"),
        ]
        middle_scores = [
            self.measure_gimel()["descending"],
            self.measure_resh()["descending"],
            self.measure_tav()["descending"],
        ]
        return {
            "right":  round(sum(right_scores) / len(right_scores), 4),
            "left":   round(sum(left_scores) / len(left_scores), 4),
            "middle": round(sum(middle_scores) / len(middle_scores), 4),
        }

    def full_diagnostic(self) -> dict:
        """All 22 paths + triadic balance + pillar tension in one call."""
        return {
            # Mother paths
            "aleph":   self.measure_aleph(),
            "mem":     self.measure_mem(),
            "shin":    self.measure_shin(),
            # Double paths
            "bet":     self.measure_bet(),
            "gimel":   self.measure_gimel(),
            "dalet":   self.measure_dalet(),
            "kaph":    self.measure_kaph(),
            "peh":     self.measure_peh(),
            "resh":    self.measure_resh(),
            "tav":     self.measure_tav(),
            # Simple paths
            "heh":     self.measure_simple_path("heh"),
            "vav":     self.measure_simple_path("vav"),
            "zayin":   self.measure_simple_path("zayin"),
            "chet":    self.measure_simple_path("chet"),
            "tet":     self.measure_simple_path("tet"),
            "yod":     self.measure_simple_path("yod"),
            "lamed":   self.measure_simple_path("lamed"),
            "nun":     self.measure_simple_path("nun"),
            "samekh":  self.measure_simple_path("samekh"),
            "ayin":    self.measure_simple_path("ayin"),
            "tzadi":   self.measure_simple_path("tzadi"),
            "qoph":    self.measure_simple_path("qoph"),
            # Aggregates
            "triadic_balance": self.triadic_balance(),
            "pillar_tension":  self.pillar_tension(),
        }
