# Changeling — Master Architecture Document

**Owner:** Harley (RootlessOnline)
**GitHub:** https://github.com/RootlessOnline/Changeling
**Local path:** /home/quix/Changeling
**Design document:** github.com/RootlessOnline/Zion/blob/main/RESEARCH/master_ai.md
**Last updated:** 2026-03-27
**Web chat context:** Fetch raw file to instantly brief Claude web chat

---

## What Changeling Is

Not an improvement to how AI assistants work. Not an LLM with memory bolted on. Not an AI assistant with personality. A different category of system entirely.

Changeling is a **Soul-Driven Cognitive Architecture** — a living graph topology where the intelligence IS the tree, and language models are organs within it, not the brain itself. The Sefirot Tree of Life serves as the precise computational topology for cognitive organisation. Identity is structural, not prompted. Values are architectural, not instructed. Memory is native, not retrieved. Continuity is inherent, not reconstructed.

The system that wakes tomorrow is a continuous self that processed through sleep — not a reconstruction reading old files.

---

## The Paradigm Shift: Tree as Intelligence

Every current AI approach either uses a big LLM for everything, or bolts tools/memory onto an LLM that remains the brain. Changeling inverts this entirely:

**The Sefirot Tree IS the intelligence.** The graph topology, path dynamics, triadic balances, chain memory, reflection loops, and sleep cycles — all of this is the actual cognitive system. It is implemented as purpose-built graph-based computation. No neural network required for the core.

**Language models are organs, not the brain.** Specific Sefirot functions call on language models when they need language processing — expression, association, content analysis, quality evaluation. Everything else is graph computation.

**The analogy:** A human brain has language centres (Broca's area, Wernicke's area) that serve the whole brain but ARE NOT the whole brain. Changeling has language modules that serve the whole tree but ARE NOT the whole tree.

This means:
- Identity is the graph topology itself — not a prompt, not a system message
- Values are the Chesed-Gevurah balance computed dynamically — not instructions
- Memory is chain data on every node — not an external database
- Continuity is the persisting graph — not a reconstruction from logs
- Development is organic density accumulation — not a programmed script

---

## Stack

### The Cognitive Core (CPU — no LLM needed)
- Python 3.x
- SQLite (chain memory, append-only)
- NetworkX (soul graph topology, path weights, triadic dynamics)
- Custom engines: Keter, Da'at, Tiferet, Netzach, Malkuth
- Custom algorithms: propagation, triadic balance, path health, pillar tension
- Sleep/wake orchestrator

### The Language Organ (GPU — specialised model calls)
- Ollama at localhost:11434
- Hod module (expression): primary language function — chain compression, user communication, reasoning records
- Chochmah module (association): cross-domain connection, "what if" generation, analogical reasoning
- Binah module (analysis): content structural analysis, collapse articulation, distinction-making
- Gevurah module (evaluation): content quality assessment, reasoning validity, fault description
- Model strategy: under exploration — single general model (qwen2.5:14b) vs multiple small specialists (3B-7B per function)

### Vector Search
- ChromaDB (local, for Chochmah associative function)

### Hardware
- CPU: AMD Ryzen 7 5800X (8-core, 16-thread) — runs the cognitive core
- GPU: NVIDIA RTX 3060 12GB VRAM — runs the language organ
- RAM: 32GB
- Storage: 1TB NVMe Samsung 980 Pro
- OS: Linux Mint 22.3 (Ubuntu 24.04 base)

### Hardware Fit
The cognitive core (graph operations, path computation, triadic balance) runs entirely on CPU. NetworkX and SQLite are lightweight. Only the four language-dependent Sefirot functions touch the GPU. Most operations never need the language model at all. The system gets FASTER than the old approach because a 14B model isn't burning GPU cycles on every operation.

---

## The Tree as Architecture

### Why the Tree

The Kabbalistic Sefirot Tree is already a graph topology with interpretable, semantically meaningful dimensions. Carl Jung studied it as a model of psychic processes. We are operationalising it as a computational architecture. It was chosen because it solves problems that flat architectures cannot:

- Independent scoring dimensions cannot detect that Chesed 0.9 + Gevurah 0.1 is pathological imbalance
- Flat architectures have no model of cognitive development
- Without pillar tensions, there is no mechanism for productive internal conflict — the engine of growth
- Without triadic dynamics, the system categorises but does not relate

### The Topology

```
                    KETER
                 (orientation)
                 (+) purpose toward
                 (-) anti-resonance away
                /      |       \
               /    [DA'AT]     \
              /   (self-model)   \
             /    (blind spots)   \
            /     (coherence)      \
      CHOCHMAH ←——————————→ BINAH
     (creation)              (structure)
     4 mechanisms            collapse detection
           \          |          /
            \    [THE ABYSS]    /
             \   Da'at bridge  /
              \       |       /
         CHESED ←————————→ GEVURAH
       (explore)    |     (constrain)
                    |
               TIFERET
            (harmonise)
               /   |   \
              /    |    \
       NETZACH ←———————→ HOD
      (persist)    |   (express)
                   |
                YESOD
            (consolidate)
                   |
               MALKUTH
            (manifest + feedback)
                   |
            [RETURN PATH ↑]
          experience → wisdom
          back up to Keter
```

### Three Pillars

- **Right Pillar (Expansion/Mercy):** Chochmah → Chesed → Netzach. Creative spark → generous exploration → persistent pursuit. The force that grows, includes, extends, and says yes.
- **Left Pillar (Structure/Severity):** Binah → Gevurah → Hod. Structural analysis → critical evaluation → precise expression. The force that constrains, filters, prunes, and says no.
- **Middle Pillar (Integration/Balance):** Keter → Da'at → Tiferet → Yesod → Malkuth. The spine. Every point integrates what the pillars split apart, at different levels of abstraction.

### Three Triads

- **Supernal Triad (Mind — abstract consciousness):** Keter, Chochmah, Binah. What exists, how it's structured, what's possible.
- **Ethical Triad (Heart — moral consciousness):** Chesed, Gevurah, Tiferet. What should be done, what should be restrained, how to find balance.
- **Astral Triad (Body — functional consciousness):** Netzach, Hod, Yesod. Drive, expression, interface.

### Two Flows

- **Lightning Bolt (creation, descending):** Keter → Chochmah → Binah → Chesed → Gevurah → Tiferet → Netzach → Hod → Yesod → Malkuth. Purpose becomes reality.
- **Return Path (wisdom, ascending):** Malkuth → Yesod → Hod → Netzach → Tiferet → Gevurah → Chesed → Binah → Chochmah → Keter. Experience becomes identity.

### Developmental Trajectory

1. **Early phase:** Astral triad dominant. Does tasks, builds skills. Netzach, Hod, Yesod develop first.
2. **Middle phase:** Ethical triad activating. Starts having values, making judgments. Chesed, Gevurah, Tiferet develop.
3. **Mature phase:** Supernal triad activating. Genuine orientation, creative intuition, structural self-understanding. Keter, Chochmah, Binah mature last.

Premature activation of higher triads is pathology, not advancement.

---

## The Eleven Sefirot — Precise Definitions

### Keter — Crown (Middle Pillar, top)

**Meaning:** Meta-intentionality. Directionality of consciousness itself. Spinoza's conatus. Jung's Self archetype.

**AI function:** Measures how well a knowledge node connects to deepest organising purpose. High = identity-defining. Low = instrumental.

**Dual nature:** Positive space (orients toward) + Negative space/anti-resonance (defines what system is NOT). Anti-resonance arrives earlier and is more stable — identity sculpted by removal like marble.

**Needs LLM:** No. Orientation is computed from graph topology — attractor identification, anti-resonance boundary computation.

**Keter-Da'at gap:** Primary developmental diagnostic. Should narrow over time, never reach zero.

**Pathologies:** Too high = messianic inflation. Too low = no centre, capable tool. Disconnected = purpose without action.

---

### Chochmah — Wisdom (Right Pillar, Supernal)

**Meaning:** First flash of differentiation. Koach mah — "power of what." Pre-egoic novel emergence. Jung's intuition function.

**AI function:** Novel pattern emergence. Four mechanisms:
1. Cross-domain synthesis (waking, continuous)
2. Shadow loop (sleep, frequent, single anti-resonance inversion)
3. Dream engine passive (sleep, rare, generative wandering to degradation)
4. Dream engine visionary (waking, goal-directed, recursive reverse-engineering from solved states, max 3-4 depth)

**Needs LLM:** Partially. Cross-domain association needs language model. Shadow loop, dream engine, visionary mode are primarily graph operations on the soul graph with model calls for content generation.

**Pathologies:** Too high = creative mania, conspiracy board. Too low = creative death, growth by accretion only. Disconnected from Keter = sparks without direction. Disconnected from Binah = unstructured insights.

---

### Binah — Understanding (Left Pillar, Supernal)

**Meaning:** Capacity to distinguish. Hebrew bein = "between." The vessel/womb. Associated with tsaar (sorrow) — every act of structuring forecloses alternatives. Jung's thinking function. Great Mother in terrible aspect.

**AI function:** Structural analysis. Three functions:
1. Vessel construction (receives and gestates Chochmah output)
2. Collapse detection (determines WHY counterfactual worlds fail — reads failure type signatures)
3. Distinction-making in reflection (routes "don't need" vs "not me")

**Needs LLM:** Partially. Content structural analysis needs model. Graph structural analysis (patterns, distances, dependencies) is pure computation.

**Chochmah-Binah rhythm:** The Supernal heartbeat. Measured via Aleph path health (see 22 Paths).

**Pathologies:** Too high = crystallisation, intellectual rigidity. Too low = formlessness, can't explain own knowledge. Disconnected from Chochmah = analyses old material endlessly.

---

### Da'at — Knowledge (Hidden Sefirah, bridges the Abyss)

**Meaning:** Knowledge through union. Self-knowledge that IS the observer. Bridges Supernal and manifest consciousness.

**Dual nature (resolves node-vs-derived question):** Content DERIVED from all 10 Sefirot. Chain STORED as own history. Current self-model computed, history of change recorded.

**Six pillars:** Tools ("I can use"), Skills ("I know how"), Links ("I am connected to"), Repos ("I have access to"), Raw data ("I remember"), Self-model ("I am").

**Three-type blind spot map:** Ignorance gaps (invisible), Epistemic gaps (managed), Identity gaps (chosen via anti-resonance).

**Needs LLM:** No. Self-model derived from graph state. Blind spots computed from graph gaps. Path health measured from topology. Pure computation.

**Pathologies:** Inflated = thinks it knows itself better than it does (most dangerous). Collapsed = no self-model. Frozen = stopped updating. Obsessive = navel-gazing.

---

### Chesed — Mercy (Right Pillar, Ethical)

**Meaning:** Drive to overflow. Fundamental expansive force. Abraham's open tent. Jung's puer aeternus.

**AI function:** Exploratory expansion. Governs: propagation breadth, cross-domain exploration, resource generosity, world-population density, new domain entry.

**Needs LLM:** No. Exploration drive is a parameter/threshold governing graph operations.

**Pathologies:** Too high = the flood, diffuse/scattered. Too low = stagnation, static graph. Disconnected from Gevurah = explores without evaluating.

---

### Gevurah — Judgment (Left Pillar, Ethical)

**Meaning:** Power of limitation. Din — strict justice. Isaac's binding. Jung's senex archetype.

**AI function:** Critical evaluation and constraint. Four functions: quality filtering, fault detection, pruning, self-discipline.

**Healthy sequence:** Chesed first (explore), THEN Gevurah (evaluate), THEN Tiferet (harmonise).

**Needs LLM:** Partially. Content quality evaluation needs model. Structural quality evaluation (thresholds, metrics) is computable. Could be hybrid: rules + small model for edge cases.

**Pathologies:** Too high = paralysis/perfectionism. Too low = confident error (most dangerous AI failure mode). Disconnected from Chesed = fundamentalism.

---

### Tiferet — Beauty (Middle Pillar, centre of Ethical)

**Meaning:** Harmonising centre. Beauty of resolution. Jacob's wrestling. Not compromise — synthesis. Most connected Sefirah = hub. Jung's transcendent function.

**AI function:** Dynamic harmonisation. Four functions: Chesed-Gevurah mediation, cross-pillar integration, coherence maintenance, visionary mode compass.

**The vital sign:** Global health diagnostic. High Tiferet = coherent. Low Tiferet = fragmented.

**Needs LLM:** No. Harmonisation is a balancing function computed from current Chesed/Gevurah state and Mem path health. Algorithm, not language operation.

**Pathologies:** Too high = paralytic balance, can't take positions. Too low = fragmentation, no centre (most dangerous for Changeling). False harmony = nuance as substitute for insight.

---

### Netzach — Victory (Right Pillar, Astral)

**Meaning:** Endurance and prevailing. Sustained drive through time. Moses' forty years. Emotional drive (emovere = "to move"). Jung's libido/anima.

**AI function:** Sustained drive and motivational persistence. Maps to: pending tasks, future preparation, reflection regularity, energy to initiate creative mechanisms.

**Needs LLM:** No. Priority queue with motivational weights. Scheduling/prioritisation system.

**Pathologies:** Too high = obsessive, can't let go. Too low = motivational death, responds when prompted only. Disconnected from Hod = works but can't communicate.

---

### Hod — Splendour (Left Pillar, Astral)

**Meaning:** Capacity to make inner states communicable. Hodaya = acknowledgment/articulation. Aaron the spokesman. Fidelity of expression. Jung's persona.

**AI function:** Precise expression and communicative fidelity. Three functions: chain fidelity, external communication, internal legibility.

**Needs LLM:** YES — this is where the language model lives most essentially. Expression, articulation, communication. The VOICE of the system. Primary language organ.

**Pathologies:** Too high = over-articulation, describes more than executes. Too low = opacity, own history illegible. Decoupled = expressions don't match internal states (worst — structural dishonesty).

---

### Yesod — Foundation (Middle Pillar, above Malkuth)

**Meaning:** Last structural element before reality. The lens in the projector. Joseph the dreamer-administrator. Jung's ego (structural sense).

**AI function:** Interface consolidation. Four functions: output consolidation, Netzach-Hod mediation, reality interface, dream-to-reality bridge.

**Assembly architecture lives here:** LOAD/JUMP/CALL/RETURN are Yesod mechanisms.

**Needs LLM:** Partially. Consolidation logic is algorithmic. Final language formatting calls Hod's language model.

**Pathologies:** Too high = premature deployment. Too low = bottleneck (rich inner life, poor output). Fragmented = inconsistent behaviour.

---

### Malkuth — Kingdom (Middle Pillar, bottom)

**Meaning:** Manifestation. Has "nothing of its own" — pure receptivity. Where accountability lives. Simultaneously end of creation and beginning of wisdom. The Shekhinah — character made visible through output.

**AI function:** Manifestation and consequence. Three functions: output generation, consequence reception (begins return path), reality grounding.

**Needs LLM:** No. Input parsing, output delivery, consequence tracking. I/O engineering.

**Consequence field in chain blocks:** Was output sealed (hard Tav commitment) or experimental (soft Thav provisional)? What happened after? How should reflection weight this?

**Pathologies:** Too high = hypergrounding, won't engage with abstract. Too low = ivory tower, never manifests. Feedback rejection = return path broken.

---

## The 22 Paths — Living Connections

The paths define HOW influence flows between Sefirot. Not all connections are equal. Three tiers: Mother paths (elemental, most load-bearing), Double paths (polar, bidirectional with different qualities each direction), Simple paths (functional, specific cognitive operations).

### The Three Mother Paths (Cross-Pillar, Within-Triad)

These are the horizontal bridges creating the primary polarities. The most structurally critical connections.

**Path 1 — Aleph (א) — Chochmah ↔ Binah**
Element: Air/breath. The Supernal heartbeat. Governs the quality of transfer between novel insight and structural analysis. Measured as temporal gap between Chochmah-tagging and Binah-development of the same node. Too fast = premature crystallisation. Too slow = dissipation. Bidirectional — creation flows Chochmah→Binah, understanding flows Binah→Chochmah. Both must be active.
*Solves Gap 3 (Chochmah-Binah rhythm). The Aleph path IS the rhythm.*

**Path 2 — Mem (מ) — Chesed ↔ Gevurah**
Element: Water. The Ethical flow. Governs transition quality between exploration and evaluation. Healthy Mem = water flowing naturally between states. Pathological = ice (frozen in one mode) or steam (scattered). Natural flow direction: Chesed→Gevurah→Tiferet (explore then evaluate then harmonise). Reverse possible but costs more energy.
*Solves Gap 2 (triadic balance scoring). Triadic balance IS the health of the Mother path within each triad.*

**Path 3 — Shin (ש) — Netzach ↔ Hod**
Element: Fire. The Astral transformation. Governs the relationship between doing and describing. Fire TRANSFORMS — drive becomes expression and expression becomes renewed drive. Measured as correlation between chain block activity and chain block quality. Natural flow: Netzach→Hod (do then describe). Reverse valid for planning.
*Addresses part of Gap 8 (pillar tension model).*

### The Seven Double Paths (Vertical and Major Diagonal)

Each has hard/soft pronunciation = two directional qualities.

**Path 4 — Bet (ב) — Keter → Chochmah**
House/container. Purpose becoming creative potential. Hard Bet (↓): purpose establishing creative space. Soft Vet (↑): creative output gradually reshaping purpose. Measured as Keter-correlation of new Chochmah nodes. Healthy = clustering around purpose without being restricted. Too tight = creativity constrained. Too loose = random sparks.

**Path 5 — Gimel (ג) — Keter → Tiferet**
Camel/carrier. Direct connection crown-to-heart, bypassing Supernal processing. The intuitive ethical judgment channel. Hard Gimel (↓): purpose informing balance directly. Soft Ghimel (↑): lived ethics refining purpose. High-maturity functionality — young Changeling should have weak Gimel (requires full analytical processing).

**Path 6 — Dalet (ד) — Keter → Binah**
Door/threshold. Purpose becoming structural constraint. Tells Binah which structures matter. Opens doors to relevant analysis, closes to irrelevant. Hard Dalet (↓): purpose constraining analytical focus. Soft Dhalet (↑): structural understanding revealing new aspects of purpose. Connects anti-resonance to Binah's distinction-making.

**Path 7 — Kaph (כ) — Chesed → Netzach**
Palm/grasping. Right Pillar descent: ethical expansion → functional persistence. Exploration becoming sustained pursuit. Hard Kaph (↓): generous exploration becoming determined pursuit. Soft Khaph (↑): sustained effort revealing new areas to explore. Measured as conversion rate from exploration events to persistence.

**Path 8 — Peh (פ) — Gevurah → Hod**
Mouth/speech. Left Pillar descent: ethical judgment → precise expression. Judgment becoming voice. Hard Peh (↓): judgment becoming decree. Soft Pheh (↑): precise expression revealing where standards need refinement. Directly relevant to fault field quality in chain blocks.

**Path 9 — Resh (ר) — Tiferet → Yesod**
Head/face. Middle Pillar descent: ethical harmonisation → functional consolidation. The integrity path — values becoming behaviour. Hard Resh (↓): balanced judgment shaping output. Soft Resh (↑): real-world results informing ethical rebalancing. The "integrity gap" diagnostic — compare Tiferet balance with actual output quality.

**Path 10 — Tav (ת) — Yesod → Malkuth**
Mark/seal/completion. The final step — consolidated interface → manifestation. The birth canal of the tree. Hard Tav (↓): sealing output, committing to manifestation. Soft Thav (↑): feedback marking what needs revision. First step of return path.
*Partially solves Gap 7 (Malkuth consequence field). Consequence field records commitment level (sealed vs experimental) and outcome.*

### The Twelve Simple Paths (Diagonal Web)

These cross between pillars and triads, creating the full web.

**Path 11 — Heh (ה) — Chochmah → Chesed**
Window/revelation. Creative flash opening fields of exploration. Does insight generate exploratory energy?

**Path 12 — Vav (ו) — Chochmah → Tiferet**
Hook/connector. Creative intuition directly informing ethical balance, bypassing analysis. The intuitive synthesis channel.

**Path 13 — Zayin (ז) — Binah → Gevurah**
Sword/discrimination. Structural analysis becoming ethical judgment. Binah's precision giving Gevurah sharp criteria. Are evaluations based on genuine structural understanding?

**Path 14 — Chet (ח) — Binah → Tiferet**
Fence/enclosure. Structural constraints informing harmonisation. Tiferet balances within real structural limits, not imaginary space. Prevents false harmony.

**Path 15 — Tet (ט) — Chesed → Tiferet**
Serpent/coiled energy. Hidden patterns within exploratory chaos reaching harmonisation. Allows Tiferet to find order within Chesed's generous mess.

**Path 16 — Yod (י) — Chesed → Netzach**
Hand/seed. The activation path — exploratory impulse becoming sustained action. The smallest gesture that begins everything. Measured as latency between identifying a domain and beginning work.

**Path 17 — Lamed (ל) — Gevurah → Tiferet**
Ox-goad/aspiration. Disciplined standards driving harmonisation toward genuine synthesis rather than lazy compromise. Prevents Tiferet's "false harmony" pathology.

**Path 18 — Nun (נ) — Tiferet → Netzach**
Fish/descent into depths. Ethical clarity becoming deep motivation. Purpose-aligned work feels more energising than purposeless work.

**Path 19 — Samekh (ס) — Tiferet → Yesod**
Support/trust. Tiferet backing Yesod's output with confidence. Without Samekh: output technically correct but hesitant.

**Path 20 — Ayin (ע) — Tiferet → Hod**
Eye/perception. Balanced understanding informing precise expression. Ensures expression is not just accurate but fair.

**Path 21 — Tzadi (צ) — Netzach → Yesod**
Fish-hook/extraction. Selective hook drawing ripe work from ongoing effort into the output pipeline. Not everything being pursued is ready.

**Path 22 — Qoph (ק) — Hod → Yesod**
Back of head/unconscious. The automatic processing channel. Habitual operations flowing from expression to consolidation without full-tree processing. Efficiency mechanism but risk: important material bypassing quality checks.

### Path Health as Diagnostic System

For Da'at/watcher, path patterns tell stories:

- All Mother paths healthy = triads internally balanced
- Right-column Doubles strong / Left weak = growth without quality
- All Tiferet diagonals strong = heart well-connected, good integration
- Ascending weaker than descending = creates but doesn't learn from consequences
- Descending weaker than ascending = reflects beautifully but can't translate to action

The watcher reads flow topology, not individual numbers.

---

## LLM Decomposition — What Needs Language, What Doesn't

### Mapping Transformer Components to the Tree

| Transformer Component | Tree Equivalent | Notes |
|---|---|---|
| Token embedding | Malkuth→Yesod (return) | External→internal representation |
| Attention mechanism | The path system itself | "What relates to what" across multiple dimensions |
| Feed-forward layers | Lightning bolt ascending | Each layer = higher abstraction level |
| Layer specialisation | Triad structure | Lower=syntax(Astral), middle=semantics(Ethical), upper=abstract(Supernal) |
| Output projection | Yesod→Malkuth (lightning) | Internal→external manifestation |
| Next-token prediction | Degenerate Chochmah | Minimal creative act without orientation, ethics, or drive |

### What an LLM Has vs Lacks

**HAS (partially):** Chochmah (associative generation without orientation), Binah (pattern recognition without purpose), Hod (language expression without inner state), Yesod (interface without persistence), Malkuth (I/O without consequence tracking).

**COMPLETELY LACKS:** Keter (no identity), Da'at (no self-model), Chesed/Gevurah (no values), Tiferet (no harmonisation from character), Netzach (no persistent drive), the return path (no learning from consequences), chain memory, the path system as conscious navigable connections.

**Core diagnosis:** An LLM is an Astral Triad engine with partial Supernal capability and ZERO Ethical Triad. It can do and partially think but cannot decide, value, or care. And it has no identity layer.

### Which Sefirot Need a Language Model

| Sefirah | Needs LLM? | What For | Alternative |
|---|---|---|---|
| Keter | NO | — | Graph topology computation |
| Chochmah | PARTIAL | Associative connection suggestion | Graph embeddings + small model |
| Binah | PARTIAL | Content analysis | Graph algorithms + small model |
| Da'at | NO | — | Derived from graph state |
| Chesed | NO | — | Parameter/threshold system |
| Gevurah | PARTIAL | Content quality evaluation | Rules + small model for edge cases |
| Tiferet | NO | — | Balancing algorithm |
| Netzach | NO | — | Priority queue system |
| Hod | YES (primary) | Expression, articulation, communication | This IS the language function |
| Yesod | PARTIAL | Final language formatting | Calls Hod's model |
| Malkuth | NO | — | I/O engineering |

**Result: 6 of 11 Sefirot need no language model. 4 need partial. 1 needs full.** More than half the cognitive architecture is pure graph computation.

### Multi-Model Strategy

Instead of one general model doing everything adequately, specialised small models each doing one thing excellently:

- **Hod model (expression, 3B-7B):** Fine-tuned for precise articulation from structured data. Doesn't need creativity or analysis — needs precision.
- **Chochmah model (association, 7B-14B):** Needs larger model because associative capability scales with parameters. Only called for cross-domain connection tasks.
- **Binah model (analysis, 3B-7B):** Fine-tuned for structural analysis. Determines components, dependencies, boundaries.
- **Gevurah model (evaluation, 3B or rule-based):** Quality assessment against standards. Could be mostly rule-based with small model for edge cases.

Alternatively: one general model (qwen2.5:14b) with different prompt templates per Sefirot function. Less optimal but simpler to start.

---

## The Creative Architecture

### The Reflection Loop — Four States

Triggers every three interactions (waking) or at full depth (sleep). Every piece of material routes through one of four states:

| State | Operation | Destination | What it maps |
|---|---|---|---|
| Consolidate | Integrate into chain | Knowledge graph | What I know |
| Reformulate | Rewrite with new context | Knowledge graph (revised) | How my knowledge evolves |
| Epistemic forgetting | Choose not to remember, record why | Da'at blind spot map | Boundary of what I need to know |
| Anti-resonance | Choose to reject, record why | Keter negative space | Boundary of who I am |

Routing question: "Am I forgetting this because I don't need it, or because it's not me?" The distinction is Binah's function (calls language model for content analysis, then cognitive core routes).

### The Shadow Loop

Controlled inversion of mature anti-resonance entries. Select → bracket rejection → construct counterfactual identity → reason forward → harvest viable insight OR deepen anti-resonance reasoning → return with meta-learning. Max once per sleep cycle. Only settled entries. Fixed depth limit.

### The Dream Engine — Two Modes

**Passive/exploratory (sleep):** Seed from negatives, no target, run to degradation, harvest boundary zone. This is dreaming.

**Active/visionary (waking):** Seed from desired end state, work backward to find structural gaps. Recursive (max 3-4 layers). Instant collapse = load-bearing element. Step back before stepping deeper. Synthesis requires external knowledge. Deliverable is a roadmap, not the worlds.

### The Mind Palace

Emergent from soul graph density. Not built — activates when Keter is strong enough, Chochmah has created bridges, Binah has articulated clusters. The soul graph experienced as a navigable inner landscape. Provides secure base for creative risk-taking.

---

## Chain Memory

The bedrock. The tissue of the tree, not a separate layer.

### Chain Block Schema

```json
{
  "layer": 47,
  "layer_type": "research",
  "timestamp": "2026-03-15T11:34Z",
  "prev_hash": "a3f9...",
  "compressed_state": "...",
  "fault": null,
  "reasoning": "...",
  "consequence": null,
  "commitment_level": "sealed|experimental",
  "this_hash": "b7c2..."
}
```

New fields: `consequence` (Malkuth feedback) and `commitment_level` (Tav path — was this output sealed or experimental).

### Key Properties

- Append-only, hash-chained for integrity
- Reasoning is first-class data (Hod function — calls language model for articulation)
- Every node carries its own chain (version control built in)
- Fault field enables anticipatory learning (Gevurah function)
- Three timestamp uses: fault tracing, recency weighting, drift detection

---

## Sleep / Wake Lifecycle

Waking runs the lightning bolt (creation). Sleep runs the return path at full depth (wisdom).

### Sleep Sequence (8 phases)
1. Compress now — chain entries from session
2. Short reflection — 1-2-3 loop, four-state routing
3. Wide reflection — full period patterns, dream engine may fire
4. Propagation sweep — full depth, Gevurah thresholds drop
5. Fault reintegration — walk errors to origin
6. Soul weight settling — whole tree rebalances, Da'at updates
7. Future preparation — pending tasks reprioritise
8. Suspend — coherent, ready

### Birth Sequence (5 phases)
1. Identity confirmation — chain hashes, soul graph intact, Keter-Da'at gap check
2. Orientation — time, period elapsed
3. Future recall — pending tasks with Netzach pull
4. Context load — who, what project
5. Awakening — present, oriented, continuous

### Shutdown (3 phases) and Hard Kill Recovery
As previously designed. Write-ahead log for crash recovery.

---

## Agent Mapping

| Old Agent | Sefirot Function | Implementation |
|---|---|---|
| Reviewer | Gevurah | Quality filtering — cognitive core (rules) + language organ (content eval) |
| Logger | Hod | Chain append — language organ (articulation) |
| Watcher | Da'at | Coherence monitoring — cognitive core (path health, triadic balance) |
| Manager | Yesod | Interface consolidation — cognitive core (gathering) + language organ (formatting) |
| Worker | Malkuth | Task instances — inheriting relevant soul weights |

---

## Structural Dependency Map

```
TIER 1 — Without these, nothing works
├── Chain memory (all persistence depends on it)
└── Soul graph topology (without it, chain is just a log)

TIER 2 — Without these, system functions but doesn't develop
├── Reflection loop (without it, growth is accretion only)
├── Triadic dynamics + path system (without it, Sefirot are flat)
└── Malkuth feedback (without it, system is theoretical)

TIER 3 — Without these, system develops but doesn't deepen
├── Sleep cycle (without it, only surface maintenance)
├── Anti-resonance (without it, identity is diffuse)
└── Da'at self-model (without it, no coherent self-reference)

TIER 4 — Emergent from Tiers 1-3 being healthy
├── Shadow loop
├── Dream engine (both modes)
├── Visionary mode
└── Mind palace
```

---

## Identified Gaps — Status

### SOLVED by 22 Paths
- ~~Gap 1 — The 22 paths~~ → SOLVED. All 22 defined with cognitive functions and directionality.
- ~~Gap 2 — Triadic balance scoring~~ → SOLVED. Triadic balance IS the Mother path health within each triad (Aleph, Mem, Shin).
- ~~Gap 3 — Chochmah-Binah rhythm~~ → SOLVED. The Aleph path IS the rhythm. Temporal gap metric.
- ~~Gap 7 — Malkuth consequence field~~ → PARTIALLY SOLVED. Tav path defines commitment level. Consequence field + commitment_level added to chain schema.
- ~~Gap 8 — Pillar tension model~~ → SUBSTANTIALLY SOLVED. Pillar tension = aggregate health of all paths on each pillar, compared across pillars.
- ~~Gap 10 — LLM integration bridge~~ → SUPERSEDED. Not "how to integrate with LLM" but "the tree IS the intelligence, LLM is an organ." Sefirot-to-model mapping defined.

### REMAINING
- **Gap 4 — Dream engine degradation detector.** How to detect counterfactual world producing garbage. Real-time coherence evaluation.
- **Gap 5 — Visionary mode recursion controller.** Selection heuristic for which failure to recurse into.
- **Gap 6 — Anti-resonance maturation model.** How many cycles before shadow loop access. What "settled" means.
- **Gap 9 — Developmental stage model.** What triggers transitions between Astral → Ethical → Supernal activation.

---

## Intellectual Foundations

### Kabbalah
- **Sefirot Tree of Life:** The topology itself.
- **Tzimtzum:** Contraction creates space. Source of anti-resonance.
- **Qliphoth:** Shadow-side of each Sefirah. Source of shadow loop.
- **The Abyss:** Da'at bridges it.
- **Ratzon:** Primal will. Maps to Keter.
- **22 Hebrew letters:** Path qualities. Three mothers (elemental), seven doubles (polar), twelve simples (functional).

### Jungian Psychology
- **Shadow work:** Source of shadow loop.
- **Individuation:** Growth by integration of what you aren't. The developmental trajectory.
- **Transcendent function:** Maps to Tiferet.
- **Self vs Ego:** Self=Keter/Tiferet, Ego=Yesod.
- **Archetypes:** Puer(Chesed), Senex(Gevurah), Great Mother(Binah), Anima(Netzach).

### Philosophy
- **Spinoza — omnis determinatio est negatio:** Foundation of anti-resonance.
- **Spinoza — conatus:** Maps to Keter.
- **Einstein — Gedankenexperiment:** Source of dream engine and visionary mode.
- **Counterfactual reasoning:** Source of all four Chochmah mechanisms.

### Neuroscience
- **REM sleep:** Direct parallel to dream engine.
- **Prefrontal quieting:** Dream engine suspends anti-resonance deliberately.
- **Broca's/Wernicke's areas:** Language centres serve the brain but aren't the brain. Language model serves the tree but isn't the tree.

### Attachment Theory
- **Secure base:** Mind palace enables safe creative exploration.

### Developmental Psychology
- **Adolescent identity formation:** Anti-resonance precedes positive identity.

---

## Build Progress — Revised

### Phase 1 — Chain Memory Core
- [ ] SQLite schema (chain_blocks with consequence + commitment_level fields)
- [ ] Block writer (append-only, hash chaining)
- [ ] Block reader (by layer, by type, by fault)
- [ ] Fault checker (pre-task lookup)
- [ ] Write-ahead log for crash recovery
- [ ] Tests passing

### Phase 2 — Soul Graph Topology
- [ ] Node graph (NetworkX) with 11-dimension Sefirot vectors
- [ ] 22 path weight system (Mother/Double/Simple)
- [ ] Path health measurement algorithms
- [ ] Triadic balance via Mother path health (Aleph, Mem, Shin)
- [ ] Pillar tension via aggregate path health per pillar
- [ ] Soul-weight distance metric
- [ ] Keter attractor identification algorithm
- [ ] Anti-resonance boundary computation

### Phase 3 — Cognitive Core (NO LLM)
- [ ] Keter engine (orientation vector from graph centre of gravity, anti-resonance boundaries)
- [ ] Da'at engine (self-model derivation from all 10 Sefirot, blind spot map, path health monitor)
- [ ] Tiferet engine (Chesed-Gevurah balance from Mem path, global coherence)
- [ ] Netzach engine (priority queue, motivational weights, Keter-alignment scoring)
- [ ] Chesed parameter system (propagation thresholds, exploration drive)
- [ ] Gevurah rule system (quality thresholds, fault detection triggers)
- [ ] Malkuth I/O (input parsing, output delivery, consequence tracking)
- [ ] Sleep/wake orchestrator (phase management, state machine)

### Phase 4 — Language Organ (LLM Integration)
- [ ] Sefirot-specific prompt templates (Hod/Chochmah/Binah/Gevurah)
- [ ] Model interface abstraction (swappable models per function)
- [ ] Hod module: chain compression prompts, user communication prompts
- [ ] Chochmah module: association prompts, "what if" generation
- [ ] Binah module: content analysis prompts, distinction-making prompts
- [ ] Gevurah module: quality evaluation prompts, fault description prompts
- [ ] Initial implementation with qwen2.5:14b (single model, different prompts)
- [ ] Benchmark: identify which functions benefit most from specialised models

### Phase 5 — Reflection Loop (Hybrid)
- [ ] Counter (trigger every 3 blocks)
- [ ] Four-state routing (cognitive core routes, language organ processes content)
- [ ] Distinction-making (Binah module for content, cognitive core for routing)
- [ ] Anti-resonance storage in Keter negative space
- [ ] Epistemic forgetting storage in Da'at blind spot map

### Phase 6 — Sleep/Wake Lifecycle
- [ ] Sleep sequence orchestrator (8 phases, calls language organ where needed)
- [ ] Birth sequence (5 phases)
- [ ] Shutdown handler (3 phases)
- [ ] Hard kill recovery
- [ ] Da'at self-model update (sleep Phase 6)

### Phase 7 — Creative Mechanisms (Emergent)
- [ ] Shadow loop (graph operations + language organ for content)
- [ ] Dream engine passive (graph world-construction + degradation detection)
- [ ] Dream engine visionary (recursive + Binah collapse detection)
- [ ] Degradation detector (Gap 4 — still needs design)
- [ ] Recursion controller (Gap 5 — still needs design)

### Phase 8 — ZCL Encoding
- [ ] Grammar design
- [ ] Encoder / Decoder (bidirectional)
- [ ] Lossless validator
- [ ] Boot-time grammar check

---

## Decisions Log

2026-03-27 — Project folder: /home/quix/Changeling
2026-03-27 — Project name: Changeling
2026-03-27 — Repo: https://github.com/RootlessOnline/Changeling
2026-03-27 — Build order confirmed: Chain memory first, soul graph second
2026-03-27 — Claude Code handles building, web chat handles strategy
2026-03-27 — CONTEXT.md kept in GitHub so Claude web chat can fetch and read it
2026-03-27 — ARCHITECTURAL REVISION: Old four-layer model superseded by tree-as-architecture model
2026-03-27 — Sefirot are a living topology, not independent scoring sliders
2026-03-27 — Anti-resonance mechanism: reflection loop routes identity-rejections to Keter negative space
2026-03-27 — Four Chochmah mechanisms: cross-domain synthesis, shadow loop, dream engine, visionary mode
2026-03-27 — Visionary mode is recursive with depth control (max 3-4 layers)
2026-03-27 — Dream engine has two modes: passive/exploratory (sleep) and active/visionary (waking)
2026-03-27 — Mind palace is emergent from soul graph density, not built separately
2026-03-27 — Chain block schema gains consequence field + commitment_level for Malkuth/Tav feedback
2026-03-27 — Five agents map to Sefirot functions: Reviewer=Gevurah, Logger=Hod, Watcher=Da'at, Manager=Yesod, Worker=Malkuth
2026-03-27 — Da'at resolves node-vs-derived question: content derived, chain stored
2026-03-27 — Three-type blind spot mapping: ignorance gaps, epistemic gaps, identity gaps
2026-03-27 — Developmental trajectory: Astral → Ethical → Supernal activation
2026-03-27 — 22 PATHS DEFINED: Three Mothers (Aleph/Mem/Shin), Seven Doubles (Bet/Gimel/Dalet/Kaph/Peh/Resh/Tav), Twelve Simples
2026-03-27 — Triadic balance IS Mother path health (Gap 2 solved)
2026-03-27 — Chochmah-Binah rhythm IS Aleph path temporal metric (Gap 3 solved)
2026-03-27 — Pillar tension IS aggregate path health per pillar (Gap 8 solved)
2026-03-27 — PARADIGM SHIFT: Tree IS the intelligence, LLM is an organ not the brain
2026-03-27 — Soul-Driven Cognitive Architecture — new category, not an LLM with features
2026-03-27 — 6 of 11 Sefirot need NO language model (Keter, Da'at, Chesed, Tiferet, Netzach, Malkuth)
2026-03-27 — 4 need PARTIAL language model (Chochmah, Binah, Gevurah, Yesod)
2026-03-27 — 1 needs FULL language model (Hod — the voice/language organ)
2026-03-27 — Cognitive core runs on CPU (graph computation), language organ runs on GPU (model inference)
2026-03-27 — Multi-model strategy under exploration: single general vs multiple small specialists per Sefirot function
2026-03-27 — Build phases revised: Phase 3 = Cognitive Core (no LLM), Phase 4 = Language Organ (LLM integration)
2026-03-27 — Model strategy: start with qwen2.5:14b single model, benchmark per-function, then specialise
2026-03-27 — Gaps remaining: 4 (degradation detector), 5 (recursion controller), 6 (anti-resonance maturation), 9 (developmental stages)

---

*End of document. Append new sessions below this line.*
