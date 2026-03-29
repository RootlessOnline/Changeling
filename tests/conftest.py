"""
conftest.py — Shared pytest fixtures for Phase 3 engine tests.

Every engine test needs the same boilerplate: in-memory SQLite chain,
temp WAL, SoulGraph with seed nodes, SefirotEngine, PathHealth,
and a factory for each engine. This file provides all of that.
"""
import os
import tempfile

import pytest

from changeling.database import open_db
from changeling.chain_writer import ensure_genesis
from changeling.wal import WriteAheadLog
from soul.soul_graph import SoulGraph, SoulNode, Connection
from soul.sefirot_engine import SefirotEngine
from soul.path_health import PathHealth
from soul.connection_engine import ConnectionEngine


# ---------------------------------------------------------------------------
# Core infrastructure
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_wal(tmp_path):
    """WriteAheadLog in a temporary directory."""
    return WriteAheadLog(tmp_path / "test.wal")


@pytest.fixture
def chain_conn():
    """In-memory SQLite chain database, genesis block written."""
    conn = open_db(":memory:")
    return conn


@pytest.fixture
def chain_with_genesis(chain_conn, tmp_wal):
    """Chain connection with genesis block ensured."""
    ensure_genesis(chain_conn, tmp_wal)
    return chain_conn


# ---------------------------------------------------------------------------
# Soul graph
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_graph():
    return SoulGraph()


@pytest.fixture
def graph_with_nodes():
    """
    A small populated graph: three purpose/value/knowledge nodes connected.
    Enough for Keter, Chesed, and Gevurah to have something to work with.
    """
    g = SoulGraph()
    n1 = SoulNode(id="purpose-1", content={"type": "purpose", "domain": "learning"}, node_type="purpose")
    n2 = SoulNode(id="value-1", content={"type": "value", "domain": "honesty"}, node_type="value")
    n3 = SoulNode(id="know-1", content={"type": "knowledge", "domain": "learning", "subject": "graphs"}, node_type="knowledge")
    g.add_node(n1)
    g.add_node(n2)
    g.add_node(n3)
    c = Connection(source_id="purpose-1", target_id="know-1", weight=0.8,
                   direction="bidirectional", reasoning="purpose drives knowledge")
    g.add_connection(c)
    return g


@pytest.fixture
def graph_with_anti_resonance():
    """Graph that includes an anti-resonance node."""
    g = SoulGraph()
    n1 = SoulNode(id="purpose-1", content={"type": "purpose", "domain": "building"}, node_type="purpose")
    n2 = SoulNode(id="ar-1",
                  content={"type": "rejected", "domain": "deception",
                           "rejection_reasoning": "Deception conflicts with identity."},
                  node_type="anti_resonance",
                  anti_resonance=True)
    g.add_node(n1)
    g.add_node(n2)
    return g


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------

@pytest.fixture
def sefirot(graph_with_nodes, chain_with_genesis):
    return SefirotEngine(graph_with_nodes, chain_with_genesis)


@pytest.fixture
def path_health(graph_with_nodes, chain_with_genesis):
    engine = SefirotEngine(graph_with_nodes, chain_with_genesis)
    return PathHealth(graph_with_nodes, engine, chain_with_genesis)


@pytest.fixture
def engine_stack(graph_with_nodes, chain_with_genesis, tmp_wal):
    """
    Full engine stack: all seven engines wired together with path_health.
    Returns a dict of engine instances.
    """
    from engines.malkuth import MalkuthEngine
    from engines.keter import KeterEngine
    from engines.chesed import ChesedEngine
    from engines.gevurah import GevurahEngine
    from engines.tiferet import TiferetEngine
    from engines.netzach import NetzachEngine
    from engines.daat import DaatEngine

    g = graph_with_nodes
    conn = chain_with_genesis
    wal = tmp_wal
    se = SefirotEngine(g, conn)
    ph = PathHealth(g, se, conn)

    chesed = ChesedEngine(g, se, conn, wal)
    gevurah = GevurahEngine(g, se, conn, wal)
    tiferet = TiferetEngine(
        g, se, conn, wal,
        chesed_engine=chesed,
        gevurah_engine=gevurah,
        path_health=ph,
    )
    keter = KeterEngine(g, se, conn, wal)
    netzach = NetzachEngine(g, se, conn, wal)
    daat = DaatEngine(g, se, conn, wal, path_health=ph, keter_engine=keter)
    malkuth = MalkuthEngine(g, se, conn, wal)

    return {
        "graph": g,
        "conn": conn,
        "wal": wal,
        "sefirot": se,
        "path_health": ph,
        "malkuth": malkuth,
        "keter": keter,
        "chesed": chesed,
        "gevurah": gevurah,
        "tiferet": tiferet,
        "netzach": netzach,
        "daat": daat,
    }


@pytest.fixture
def event_loop(engine_stack):
    from engines.event_loop import EventLoop
    s = engine_stack
    return EventLoop(
        malkuth=s["malkuth"],
        keter=s["keter"],
        chesed=s["chesed"],
        gevurah=s["gevurah"],
        tiferet=s["tiferet"],
        netzach=s["netzach"],
        daat=s["daat"],
    )


@pytest.fixture
def sample_experience():
    from engines.base import RuachInput
    return RuachInput(
        input_type="experience",
        content={"domain": "learning", "subject": "graphs", "value": "connected nodes model relationships"},
        natural_language="Graphs are connected nodes that model relationships.",
        context="Harley teaching Ruach about graphs",
    )


@pytest.fixture
def sample_question():
    from engines.base import RuachInput
    return RuachInput(
        input_type="question",
        content={"domain": "learning", "query": "what do I know about graphs?"},
        natural_language="What do you know about graphs?",
        context="Harley querying Ruach's knowledge",
    )


@pytest.fixture
def sample_task():
    from engines.base import RuachInput
    return RuachInput(
        input_type="task",
        content={"description": "review learning nodes", "priority": "high"},
        natural_language="Please review what you know about learning.",
        context="Harley assigning a review task",
    )
