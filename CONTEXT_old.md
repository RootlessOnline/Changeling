# Changeling — Master AI Project Context

**Owner:** Harley (RootlessOnline)
**GitHub:** https://github.com/RootlessOnline/Changeling
**Local path:** /home/quix/Changeling
**Last updated:** 2026-03-27
**Web chat context:** Fetch raw file to instantly brief Claude web chat

---

## Stack
- Python 3.x
- SQLite (chain memory, append-only)
- NetworkX (soul graph topology)
- ChromaDB (vector similarity search, local)
- Ollama at localhost:11434
- Primary model: qwen2.5:14b
- Backup model: llama3.1

---

## What Changeling Is
A stateful AI with genuine identity — not a chatbot with memory bolted on.
Every task shapes it. Every reflection pass integrates that shaping.
The system that wakes tomorrow is a continuous self, not a reconstruction reading old files.

---

## Four Layers

### Layer 1 — Identity (Soul Graph)
- 11-dimensional Sefirot scoring per knowledge node
- Dimensions: Keter, Chochmah, Binah, Da'at, Chesed, Gevurah, Tiferet, Netzach, Hod, Yesod, Malkuth
- Nodes connect via semantic links AND soul-weight similarity (Euclidean distance)
- Da'at is the self-model node: 6 pillars (Tools, Skills, Links, Repos, Raw data, Self-model)
- Also maps blind spots — systematic gaps in understanding

### Layer 2 — Session (Assembly Architecture)
- INCLUDE/LINK — combine prompt pages before sending
- LOAD/MOV — inject live data at call time
- JUMP — route to specialised sub-pages by task type
- CALL/RETURN — spin up sub-agents, get result, continue
- FLAGS — Reviewer verdict register (APPROVE/REJECT/ESCALATE)
- PROTECTED MEMORY — write gateway, governance files read-only

### Layer 3 — Working (Chain Memory)
Chain block structure:
{
  layer: int,
  layer_type: str,
  timestamp: ISO8601,
  prev_hash: str,
  compressed_state: str,
  fault: str or null,
  reasoning: str,
  this_hash: str
}
- Reasoning is first-class data, not a comment
- Reflection loop: every 3 blocks triggers reflect pass
- Three memory states: consolidate / reformulate / maintain deliberate forgetting
- Fault detection: before any task, check same layer_type for past faults
- Propagation: when node updates, walk outward checking neighbours for same gap

### Layer 4 — Task (Agents)
Current transitional agents → replaced by mature architecture:
- Reviewer → soul weight compliance (structural)
- Logger → chain append (automatic)
- Watcher → reflection loop (continuous)
- Manager → interface only
- Worker → lightweight task instances inheriting relevant soul weights

---

## Sleep / Wake Lifecycle

### Sleep (8 phases)
1. Compress now into chain
2. Short reflection (1-2-3 loop)
3. Wide reflection (full period patterns)
4. Propagation sweep at full depth
5. Fault reintegration
6. Soul weight settling (Da'at updates)
7. Future preparation (reprioritise pending tasks)
8. Suspend

### Birth sequence (5 phases)
1. Identity confirmation (validator check)
2. Orientation (time, what period passed)
3. Future recall (pending tasks)
4. Context load (who, what project)
5. Awakening

### Shutdown (3 phases)
1. Emergency compress (save as interrupted)
2. Pending tasks snapshot
3. Suspend marker

### Hard kill recovery
1. Read write-ahead log
2. Integrity check (chain hashes)
3. Mark interrupted work
4. Abbreviated sleep
5. Normal birth sequence

---

## ZCL — Zion Chain Language (Phase 5, design pending)
Lossless encoding for chain memory compression.
Trailer-first format: [base data][decode key][recode count]
Read right to left. Delta decoding — go to any version in max N/2 steps.
Target: 200x compression vs naive storage.
Grammar must be perfectly lossless — validated at boot.

---

## Hardware
- CPU: AMD Ryzen 7 5800X (8-core, 16-thread)
- GPU: NVIDIA RTX 3060 12GB VRAM
- RAM: 32GB
- Storage: 1TB NVMe Samsung 980 Pro
- OS: Linux Mint 22.3 (Ubuntu 24.04 base)
- Ollama: running, GPU-accelerated

---

## Build Progress

### Phase 1 — Chain memory core
- [x] SQLite schema (chain_blocks table)
- [x] Block writer (append-only, hash chaining)
- [x] Block reader (by layer, by type, by fault)
- [x] Fault checker (pre-task lookup)
- [x] Tests passing
- [x] REBUILT per v3 spec: changeling/ package, consequence + commitment_level fields, WAL, genesis block, 67 tests passing

### Phase 2 — Sefirot scorer
- [ ] Ollama call wrapper
- [ ] 11-dimension scoring prompt
- [ ] Score storage alongside chain blocks
- [ ] Node graph (NetworkX)
- [ ] Soul-weight distance metric

### Phase 3 — Reflection loop
- [ ] Counter (trigger every 3 blocks)
- [ ] Reflect prompt (reads last 3, writes summary block)
- [ ] Three memory states implemented
- [ ] Deliberate forgetting log

### Phase 4 — Sleep/wake lifecycle
- [ ] Sleep sequence orchestrator (8 phases)
- [ ] Birth sequence (5 phases)
- [ ] Shutdown handler (3 phases)
- [ ] Hard kill recovery (write-ahead log)

### Phase 5 — ZCL encoding
- [ ] Grammar design
- [ ] Encoder
- [ ] Decoder (bidirectional)
- [ ] Lossless validator
- [ ] Boot-time grammar check

---

## Decisions Log
(Append new decisions after every web chat session)

2026-03-27 — Project folder: /home/quix/Changeling
2026-03-27 — Project name: Changeling
2026-03-27 — Repo: https://github.com/RootlessOnline/Changeling
2026-03-27 — Build order confirmed: Chain memory first, soul graph second
2026-03-27 — Primary model: qwen2.5:14b via Ollama
2026-03-27 — Claude Code handles building, web chat handles strategy
2026-03-27 — CONTEXT.md kept in GitHub so Claude web chat can fetch and read it
2026-03-27 — Phase 1 complete: chain memory core built and 23 tests passing
2026-03-27 — .claude/ excluded from repo (contains local Claude Code settings)
2026-03-27 — Phase 2 not yet started — awaiting strategy confirmation from web chat
2026-03-27 — Phase 1 complete, 23 tests passing. Claude Code must update CONTEXT.md checkboxes and Decisions Log before every push — this is mandatory.
2026-03-27 — Phase 1 REBUILT per CONTEXT_v3 spec: changeling/ package replaces core/chain_memory.py
2026-03-27 — Schema updated: consequence + commitment_level fields added per v3
2026-03-27 — Genesis block: prev_hash="" (not "GENESIS"), commitment_level="sealed"
2026-03-27 — Hash covers: layer, layer_type, timestamp, prev_hash, compressed_state, fault, reasoning, commitment_level — consequence excluded (mutable Malkuth feedback)
2026-03-27 — WAL implemented: plain file, newline-delimited JSON, pending/committed/interrupted entries
2026-03-27 — 67 tests passing across 4 test files: test_chain, test_queries, test_faults, test_wal
2026-03-27 — record_consequence() is the only permitted chain mutation (fills Malkuth feedback post-hoc)
2026-03-27 — Phase 1 complete, 23 tests passing
2026-03-27 — Phase 2 NOT started yet — awaiting design
2026-03-27 — Critical design decision: Sefirot is a topology not 11 independent scores. Three pillars (Mercy/Severity/Balance), three triads (Supernal/Ethical/Astral), two flows (lightning bolt down = creation, return path up = reflection). 22 paths define relationship quality between nodes. This must be fully designed before Phase 2 code is written.
2026-03-27 — Switching to Opus to design the three triads properly before any Phase 2 code is written
2026-03-27 — Sonnet vs Opus rule: Opus for deep conceptual design (Sefirot triads, ZCL grammar, Da'at architecture). Sonnet for everything else.
