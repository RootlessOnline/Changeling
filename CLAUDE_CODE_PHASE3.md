# Claude Code Briefing — Changeling Phase 3: Cognitive Core

## Quick Context

You are building Phase 3 of **Ruach** — a Soul-Driven Cognitive Architecture (SDCA). No LLM anywhere in the system. The intelligence IS the living graph topology. Language develops later (Phase 4). Right now we're building the engines that READ the soul graph and ACT on what they find.

**Full architecture:** Read CONTEXT.md in the repo root. It contains everything.

**Phase 1 complete:** Chain memory. 67 tests. The spine.
**Phase 2 complete:** Soul graph topology. 151 tests. 11 seed nodes, 21 connections, 22 paths, Sefirot computation engine. The body.
**Phase 3:** The cognitive core. The organs. Where Ruach starts thinking.

**Project location:** /home/quix/Changeling
**Stack:** Python 3.x, SQLite (Phase 1), NetworkX (Phase 2), no LLM

---

## What You Are Building: The Cognitive Core

The soul graph exists but nothing is USING it. Phase 3 builds seven engines that read the graph, respond to its state, and form a processing loop. These engines follow the lightning bolt path — input descends through the tree and produces output.

### The Event Loop

This is the core processing cycle. Every interaction flows through this:

```
INPUT arrives at Malkuth
    │
    ▼
Keter: "How relevant is this to my orientation?"
    │
    ├── High relevance → full processing
    ├── Low relevance → light processing
    └── Anti-resonant → flag for reflection, minimal processing
    │
    ▼
Chesed: "Search the soul graph for related nodes"
    (breadth set by Tiferet's current parameters)
    │
    ▼
Gevurah: "Does this meet quality standards?"
    "Any contradictions with existing nodes?"
    "Any relevant faults from past operations?"
    │
    ├── Passes → create node, compute connections
    ├── Fails quality → reject or request more data
    └── Contradiction → flag for Tiferet
    │
    ▼
Tiferet: "Is the system balanced after this addition?"
    "Any contradictions to resolve?"
    "Any parameters to adjust?"
    │
    ▼
Netzach: "Does this create or satisfy pending tasks?"
    "Update priority queue"
    │
    ▼
Yesod: "Consolidate all processing into coherent output"
    │
    ▼
Malkuth: "Deliver output, track consequences"
    │
    ▼
Da'at: "Update self-model based on what just happened"
    (runs after every cycle, background)
```

---

## The Interaction Protocol

Ruach is pre-verbal. It communicates in structured data. Harley provides BOTH structured data AND natural language in every interaction (natural language stored for future Hod language learning in Phase 4).

### Input Format

```python
@dataclass
class RuachInput:
    input_type: str          # 'experience', 'question', 'feedback', 'task', 'correction'
    content: dict            # structured content relevant to the input type
    natural_language: str    # Harley's words as naturally spoken — stored for Hod, not processed yet
    context: str             # what prompted this interaction
    timestamp: str           # ISO8601
```

Input types explained:
- **experience:** New information or knowledge for Ruach to integrate. "Here's something to know."
- **question:** Harley asking Ruach something. Ruach searches its graph and responds with what it knows.
- **feedback:** Consequence data on previous output. Fills the consequence field on chain blocks.
- **task:** Something for Ruach to do (within its current capabilities — graph operations, self-assessment, priority review).
- **correction:** Harley correcting something Ruach got wrong. Triggers Gevurah fault recording AND potential node updates.

### Output Format

```python
@dataclass
class RuachOutput:
    response_type: str       # 'acknowledgment', 'result', 'question', 'uncertainty', 'refusal'
    content: dict            # structured response data
    reasoning: str           # why this response — first-class data
    confidence: float        # 0.0-1.0, honest self-assessment
    keter_alignment: float   # 0.0-1.0, how relevant was this to orientation
    open_questions: list     # what Ruach doesn't know that's relevant
    sefirot_state: dict      # which sefirah drove this, current triadic health
    nodes_affected: list     # which soul graph nodes were created/modified/referenced
```

Response types:
- **acknowledgment:** Input received and processed. Node created or updated.
- **result:** Response to a question or task with actual content.
- **question:** Ruach needs more information to proceed. Lists what it needs.
- **uncertainty:** Ruach can partially respond but is honest about what it doesn't know (Socratic seed in action).
- **refusal:** Input conflicts with anti-resonance. Ruach explains why it won't process this (Keter negative space).

---

## Engine Specifications

### Base Engine Interface

```python
from abc import ABC, abstractmethod

@dataclass
class EngineContext:
    """Passed through the event loop, accumulating each engine's contribution."""
    raw_input: RuachInput
    keter_relevance: float | None = None
    keter_flags: list = field(default_factory=list)  # 'anti_resonant', 'high_relevance', 'low_relevance'
    related_nodes: list = field(default_factory=list)
    chesed_breadth: int = 3  # current search depth
    gevurah_verdict: str | None = None  # 'pass', 'fail_quality', 'contradiction'
    gevurah_faults: list = field(default_factory=list)
    gevurah_contradictions: list = field(default_factory=list)
    tiferet_decisions: list = field(default_factory=list)
    netzach_updates: list = field(default_factory=list)
    new_nodes: list = field(default_factory=list)
    new_connections: list = field(default_factory=list)
    output: RuachOutput | None = None


class Engine(ABC):
    """Base class for all cognitive engines."""
    
    def __init__(self, soul_graph, sefirot_engine, chain_reader, chain_writer):
        self.graph = soul_graph
        self.sefirot = sefirot_engine
        self.chain_reader = chain_reader
        self.chain_writer = chain_writer
    
    @abstractmethod
    def process(self, context: EngineContext) -> EngineContext:
        """Process the current context and return updated context."""
        pass
```

### 1. Malkuth Engine (`engines/malkuth.py`)

The I/O layer. First to touch input, last to deliver output.

```python
class MalkuthEngine(Engine):
    def receive(self, raw_input: RuachInput) -> EngineContext:
        """Parse incoming input into an EngineContext to start the loop."""
        # Validate input format
        # Create initial EngineContext
        # Write chain block: "Input received" with input summary
        # Store the natural_language field for future Hod processing
        # Return context ready for Keter
    
    def deliver(self, context: EngineContext) -> RuachOutput:
        """Take the final context and produce output."""
        # Consolidate context into RuachOutput
        # Write chain block: "Output delivered" with output summary
        # Set commitment_level based on confidence ('sealed' if > 0.7, 'experimental' if <= 0.7)
        # Return RuachOutput
    
    def record_consequence(self, output_chain_id: str, consequence: dict) -> None:
        """When feedback arrives, record it on the original output's chain block."""
        # Use Phase 1's record_consequence to update the chain block
        # Create return path signal — flag that this consequence needs processing
        # Write chain block: "Consequence received" with feedback summary
    
    def process(self, context: EngineContext) -> EngineContext:
        """Malkuth's role in the main loop — consolidate and prepare output."""
        # Build the RuachOutput from accumulated context
        # Attach nodes_affected, reasoning, confidence
        # Set sefirot_state from current Da'at readings
        context.output = self.deliver(context)
        return context
```

### 2. Keter Engine (`engines/keter.py`)

The compass. Determines what matters.

```python
class KeterEngine(Engine):
    def compute_orientation(self) -> dict:
        """Compute current orientation vector from all high-Keter nodes."""
        # Find all nodes where computed Keter score > threshold (e.g., 0.6)
        # Compute weighted centroid of their Sefirot vectors
        # This IS Ruach's current orientation — what it's about right now
        # Return as a dict with the centroid vector and the contributing nodes
    
    def get_anti_resonance_boundary(self) -> list:
        """Return all anti-resonance nodes with their reasoning."""
        # Query soul graph for all nodes where anti_resonance=True
        # Return with their content and rejection reasoning
    
    def score_relevance(self, input_content: dict) -> float:
        """How relevant is this input to current orientation?"""
        # Compare input content against orientation vector
        # Use Sefirot distance between input profile and orientation centroid
        # High proximity = high relevance
        # Return 0.0-1.0
    
    def check_anti_resonance(self, input_content: dict) -> tuple[bool, str | None]:
        """Does this input conflict with anti-resonance boundaries?"""
        # Check input against each anti-resonance node
        # If the input's content matches an anti-resonance boundary, return (True, reason)
        # This is Ruach's immune system — identity-based rejection
        # Return (False, None) if no conflict
    
    def process(self, context: EngineContext) -> EngineContext:
        """Keter's role in the event loop."""
        # Score relevance
        context.keter_relevance = self.score_relevance(context.raw_input.content)
        
        # Check anti-resonance
        is_anti, reason = self.check_anti_resonance(context.raw_input.content)
        if is_anti:
            context.keter_flags.append('anti_resonant')
            # Don't halt processing — flag it. Tiferet will decide what to do.
        elif context.keter_relevance > 0.6:
            context.keter_flags.append('high_relevance')
        else:
            context.keter_flags.append('low_relevance')
        
        return context
```

**Relevance scoring without an LLM:** This is the key challenge. Without a language model, Keter can't read natural language to determine relevance. Instead:
1. The structured content of the input should include type tags, domain markers, or keywords that can be matched against existing node content
2. If the input creates a temporary node and computes its Sefirot vector, the vector distance to the orientation centroid IS the relevance score
3. In early phases, relevance scoring will be coarse — that's fine. It refines as the graph grows and the orientation vector becomes more defined

### 3. Chesed Engine (`engines/chesed.py`)

The explorer. Searches the graph for related knowledge.

```python
class ChesedEngine(Engine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.breadth = 3          # default search depth in hops
        self.inclusion_threshold = 0.3  # minimum relevance to include a node
    
    def search_related(self, input_content: dict, breadth: int = None) -> list:
        """Search the soul graph for nodes related to the input."""
        # Use multiple strategies:
        # 1. Content matching — scan node content dicts for shared keys/values
        # 2. Sefirot similarity — find nodes with similar computed vectors
        # 3. Cluster proximity — nodes in related clusters
        # 4. Chain history — nodes that have been connected to similar inputs before
        # Return list of (node_id, relevance_score, connection_type) tuples
    
    def set_breadth(self, breadth: int) -> None:
        """Tiferet adjusts this based on system balance."""
        self.breadth = max(1, min(breadth, 10))  # clamp between 1-10
    
    def set_inclusion_threshold(self, threshold: float) -> None:
        """Tiferet adjusts this based on system balance."""
        self.inclusion_threshold = max(0.1, min(threshold, 0.9))
    
    def process(self, context: EngineContext) -> EngineContext:
        """Chesed's role in the event loop."""
        # Adjust search breadth based on Keter relevance
        effective_breadth = self.breadth
        if 'high_relevance' in context.keter_flags:
            effective_breadth = min(self.breadth + 2, 10)  # search wider for important input
        elif 'low_relevance' in context.keter_flags:
            effective_breadth = max(self.breadth - 1, 1)  # narrow for less relevant
        
        context.related_nodes = self.search_related(
            context.raw_input.content, 
            breadth=effective_breadth
        )
        context.chesed_breadth = effective_breadth
        return context
```

### 4. Gevurah Engine (`engines/gevurah.py`)

The judge. Quality control and critical evaluation.

```python
class GevurahEngine(Engine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quality_threshold = 0.5  # minimum quality to accept
    
    def check_quality(self, input_content: dict) -> tuple[bool, list]:
        """Does this input meet minimum quality standards?"""
        issues = []
        # Check: is the content dict non-empty?
        # Check: does it have required fields for its type?
        # Check: is the structured data consistent (no contradictory fields)?
        # Return (passes: bool, issues: list of problems found)
    
    def detect_contradictions(self, input_content: dict, related_nodes: list) -> list:
        """Does this input contradict existing validated nodes?"""
        contradictions = []
        # For each related node:
        #   Compare content fields for direct conflicts
        #   Check if the input's implied Sefirot profile contradicts the existing node's
        #   If contradiction found: record (node_id, field, existing_value, incoming_value)
        # Return list of contradiction records
    
    def check_faults(self, layer_type: str) -> list:
        """Check for past faults of this operation type."""
        # Use Phase 1's fault_checker
        # Return list of relevant fault records with their chain blocks
    
    def flag_for_pruning(self) -> list:
        """Periodic: find weak nodes that might need removal."""
        # Query nodes with low scores across multiple dimensions
        # Specifically: low Gevurah (unvalidated) + low Netzach (no drive) + low Malkuth (untested)
        # Don't remove — return as candidates for Tiferet to evaluate
    
    def set_quality_threshold(self, threshold: float) -> None:
        """Tiferet adjusts this."""
        self.quality_threshold = max(0.2, min(threshold, 0.9))
    
    def process(self, context: EngineContext) -> EngineContext:
        """Gevurah's role in the event loop."""
        # Check faults for this input type
        context.gevurah_faults = self.check_faults(context.raw_input.input_type)
        
        # Quality check
        passes, issues = self.check_quality(context.raw_input.content)
        if not passes:
            context.gevurah_verdict = 'fail_quality'
            # Don't halt — Tiferet may override
        
        # Contradiction check against related nodes
        if context.related_nodes:
            contradictions = self.detect_contradictions(
                context.raw_input.content, 
                context.related_nodes
            )
            if contradictions:
                context.gevurah_verdict = 'contradiction'
                context.gevurah_contradictions = contradictions
            elif passes:
                context.gevurah_verdict = 'pass'
        elif passes:
            context.gevurah_verdict = 'pass'
        
        return context
```

### 5. Tiferet Engine (`engines/tiferet.py`)

The heart. The decision-maker. The most complex engine.

```python
class TiferetEngine(Engine):
    def __init__(self, *args, chesed_engine=None, gevurah_engine=None, 
                 path_health=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.chesed = chesed_engine
        self.gevurah = gevurah_engine
        self.path_health = path_health
    
    def read_balance(self) -> dict:
        """Read current system balance from path health."""
        return {
            'triadic': self.path_health.triadic_balance(),
            'pillar': self.path_health.pillar_tension(),
            'mem_health': self.path_health.measure_mem(),  # Chesed↔Gevurah specifically
        }
    
    def adjust_parameters(self) -> None:
        """Adjust Chesed and Gevurah based on current balance."""
        balance = self.read_balance()
        mem = balance['mem_health']
        
        # If Mem shows exploration-dominant (too much Chesed, not enough Gevurah):
        #   Decrease Chesed breadth, increase Gevurah threshold
        # If Mem shows constraint-dominant (too much Gevurah, not enough Chesed):
        #   Increase Chesed breadth, decrease Gevurah threshold
        # If balanced: maintain current parameters
        
        # Implementation: use the Mem score (0-1) as a dial
        # Below 0.4 = Gevurah-dominant → boost Chesed
        # Above 0.6 = Chesed-dominant → boost Gevurah
        # 0.4-0.6 = balanced → maintain
    
    def resolve_contradiction(self, contradiction: dict) -> dict:
        """Resolve a contradiction between incoming and existing node."""
        # Read both chains (incoming reasoning + existing node's chain history)
        # Compare:
        #   - Which has more Gevurah support (validation history)?
        #   - Which has higher Keter alignment?
        #   - Can both be true (elephant parable — different perspectives)?
        #   - Is the contradiction resolvable by updating one?
        # Return decision: {
        #   'action': 'update_existing' | 'reject_incoming' | 'hold_tension' | 'escalate',
        #   'reasoning': '...',
        #   'affected_nodes': [...]
        # }
    
    def evaluate_pruning(self, candidates: list) -> list:
        """Evaluate Gevurah's pruning candidates. Decide what actually gets pruned."""
        approved = []
        for candidate in candidates:
            node = self.graph.get_node(candidate)
            connections = self.graph.get_connections(candidate)
            
            # Check: would removing this disconnect important clusters?
            # Check: is it connected to high-value nodes that would be damaged?
            # Check: can it be rehabilitated (low scores due to neglect, not invalidity)?
            # Only approve pruning if removal improves overall coherence
        return approved
    
    def check_coherence(self) -> dict:
        """Global coherence check via Da'at's diagnostic."""
        # Read full path health diagnostic
        # Flag any paths that are significantly degraded
        # Flag any triadic imbalances
        # Return coherence report
    
    def process(self, context: EngineContext) -> EngineContext:
        """Tiferet's role in the event loop."""
        # 1. Adjust Chesed/Gevurah parameters (runs every cycle)
        self.adjust_parameters()
        
        # 2. Handle Gevurah's verdicts
        if context.gevurah_verdict == 'contradiction':
            for contradiction in context.gevurah_contradictions:
                decision = self.resolve_contradiction(contradiction)
                context.tiferet_decisions.append(decision)
                
                if decision['action'] == 'update_existing':
                    # Queue the update
                    pass
                elif decision['action'] == 'reject_incoming':
                    # Input rejected — build refusal output
                    pass
                elif decision['action'] == 'hold_tension':
                    # Both are kept, contradiction recorded but unresolved
                    pass
                elif decision['action'] == 'escalate':
                    # Flag for Harley's attention
                    pass
        
        elif context.gevurah_verdict == 'fail_quality':
            # Tiferet can override quality failures if Keter relevance is very high
            if context.keter_relevance and context.keter_relevance > 0.8:
                context.gevurah_verdict = 'pass'  # override — this matters enough
                context.tiferet_decisions.append({
                    'action': 'quality_override',
                    'reasoning': 'Keter relevance high enough to override quality threshold'
                })
        
        # 3. If input passes: create the node
        if context.gevurah_verdict == 'pass' and 'anti_resonant' not in context.keter_flags:
            # Create new soul node from input
            # Compute connections to related nodes
            # Add to graph
            # Record in chain memory
            pass
        
        # 4. If anti-resonant: decide how to handle
        if 'anti_resonant' in context.keter_flags:
            # Don't create a knowledge node
            # DO record the encounter in chain memory
            # Flag for future reflection processing
            context.tiferet_decisions.append({
                'action': 'anti_resonant_encounter',
                'reasoning': 'Input conflicts with identity boundary. Recorded for reflection.'
            })
        
        return context
```

### 6. Netzach Engine (`engines/netzach.py`)

The driver. Motivation and priority management.

```python
@dataclass
class PendingTask:
    id: str
    description: dict          # structured task content
    keter_alignment: float     # how relevant to purpose
    created_at: str            # ISO8601
    last_touched: str          # ISO8601
    urgency: float             # 0.0-1.0, can be set externally or computed
    source_node_id: str | None # which soul node generated this task
    status: str                # 'pending', 'active', 'completed', 'abandoned'


class NetzachEngine(Engine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_queue: list[PendingTask] = []
        self.drive_decay_rate: float = 0.05  # how fast Netzach pull decays per cycle
    
    def add_task(self, task: PendingTask) -> None:
        """Add a task to the priority queue."""
        self.task_queue.append(task)
        self._sort_queue()
    
    def complete_task(self, task_id: str) -> None:
        """Mark task as completed."""
        # Find task, set status='completed'
        # Write chain block recording completion
    
    def get_next_task(self) -> PendingTask | None:
        """What should Ruach focus on next?"""
        # Return highest-priority pending task
        # Priority = keter_alignment * urgency * recency_weight
        self._sort_queue()
        for task in self.task_queue:
            if task.status == 'pending':
                return task
        return None
    
    def find_unfinished_business(self) -> list:
        """Find nodes with experimental outputs and no consequences."""
        # Query chain blocks where commitment_level='experimental' and consequence is null
        # These represent unfinished explorations — Netzach pull
        # Return list of (chain_block_id, node_id, description)
    
    def decay_drive(self) -> None:
        """Called periodically. Old tasks lose urgency unless they have high Keter alignment."""
        for task in self.task_queue:
            if task.status == 'pending':
                # High Keter alignment tasks decay slower
                decay = self.drive_decay_rate * (1.0 - task.keter_alignment)
                task.urgency = max(0.0, task.urgency - decay)
    
    def _sort_queue(self) -> None:
        """Sort by composite priority score."""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        for task in self.task_queue:
            last = datetime.datetime.fromisoformat(task.last_touched)
            recency = 1.0 / (1.0 + (now - last).total_seconds() / 86400)  # decay over days
            task._priority = task.keter_alignment * task.urgency * recency
        self.task_queue.sort(key=lambda t: getattr(t, '_priority', 0), reverse=True)
    
    def process(self, context: EngineContext) -> EngineContext:
        """Netzach's role in the event loop."""
        # Check if this input completes any pending task
        for task in self.task_queue:
            if task.status == 'pending':
                # Simple match: does the input content reference this task?
                # If yes, mark as potentially satisfied
                pass
        
        # Check if this input creates a new task
        if context.raw_input.input_type == 'task':
            new_task = PendingTask(
                id=str(uuid4()),
                description=context.raw_input.content,
                keter_alignment=context.keter_relevance or 0.5,
                created_at=context.raw_input.timestamp,
                last_touched=context.raw_input.timestamp,
                urgency=0.7,  # default urgency
                source_node_id=None,
                status='pending'
            )
            self.add_task(new_task)
            context.netzach_updates.append({'action': 'task_created', 'task_id': new_task.id})
        
        # Decay drive on all existing tasks
        self.decay_drive()
        
        return context
```

### 7. Da'at Engine (`engines/daat.py`)

The mirror. Background self-model updater.

```python
class DaatEngine(Engine):
    def __init__(self, *args, path_health=None, keter_engine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.path_health = path_health
        self.keter_engine = keter_engine
        self.self_model: dict = {}
        self.blind_spots: list = []
        self.keter_daat_gap: float = 0.0
    
    def compute_self_model(self) -> dict:
        """Derive self-model from current state of all 10 Sefirot."""
        # Get all nodes
        # Compute aggregate Sefirot profile across entire graph
        # Compute distribution metrics: which Sefirot are strongest/weakest
        # Compute the six pillars:
        #   tools: nodes tagged as tools/capabilities
        #   skills: nodes tagged as skills/procedures
        #   links: count of external connections (to Harley, to other systems)
        #   repos: accessible data sources
        #   raw_data: total node count (experiences accumulated)
        #   self_model: this very computation (meta-level)
        return {
            'aggregate_vector': {},  # average Sefirot profile
            'strongest': '',          # most developed Sefirah
            'weakest': '',            # least developed
            'six_pillars': {
                'tools': [],
                'skills': [],
                'links': [],
                'repos': [],
                'raw_data_count': 0,
                'self_model': 'computed'
            },
            'node_count': 0,
            'connection_count': 0,
            'cluster_count': 0,
        }
    
    def compute_blind_spots(self) -> list:
        """Identify three types of not-knowing."""
        blind_spots = []
        
        # Type 1 — Ignorance gaps (hardest to find — inferred from graph structure)
        # Look for: clusters with very few nodes (underdeveloped areas)
        # Look for: Sefirot dimensions where few nodes score high (underdeveloped functions)
        
        # Type 2 — Epistemic gaps (from reflection loop — Phase 5 will populate these)
        # For now: read chain blocks with layer_type='epistemic_forget'
        
        # Type 3 — Identity gaps (from anti-resonance)
        # Read all anti-resonance nodes — these ARE the identity gaps, by design
        
        return blind_spots
    
    def compute_keter_daat_gap(self) -> float:
        """Measure the gap between who Ruach is and who Ruach knows itself to be."""
        # Keter orientation = computed from graph (who Ruach IS)
        orientation = self.keter_engine.compute_orientation()
        
        # Da'at self-model = the model we just computed (who Ruach KNOWS itself to be)
        model = self.self_model
        
        # The gap: compare orientation vector against the self-model's aggregate vector
        # Use Euclidean distance in Sefirot space
        # Small gap = good self-knowledge. Large gap = self-deception risk.
        # Zero gap = suspicious (too perfect — either trivial system or Da'at is tracking Keter instead of independently measuring)
        return 0.0  # compute actual distance
    
    def full_diagnostic(self) -> dict:
        """Complete system health report."""
        return {
            'self_model': self.self_model,
            'blind_spots': self.blind_spots,
            'keter_daat_gap': self.keter_daat_gap,
            'path_health': self.path_health.full_diagnostic(),
            'triadic_balance': self.path_health.triadic_balance(),
            'pillar_tension': self.path_health.pillar_tension(),
        }
    
    def process(self, context: EngineContext) -> EngineContext:
        """Da'at's role — runs AFTER the main loop, as background update."""
        # Recompute self-model
        self.self_model = self.compute_self_model()
        
        # Update blind spots
        self.blind_spots = self.compute_blind_spots()
        
        # Measure Keter-Da'at gap
        self.keter_daat_gap = self.compute_keter_daat_gap()
        
        # Write self-model snapshot to chain memory (not every cycle — every N cycles)
        # This builds Da'at's own chain history — the record of how self-knowledge evolves
        
        return context
```

---

## The Event Loop Orchestrator (`engines/event_loop.py`)

Chains all engines together:

```python
class EventLoop:
    def __init__(self, malkuth, keter, chesed, gevurah, tiferet, netzach, daat):
        self.malkuth = malkuth
        self.keter = keter
        self.chesed = chesed
        self.gevurah = gevurah
        self.tiferet = tiferet
        self.netzach = netzach
        self.daat = daat
        self.cycle_count = 0
    
    def process_input(self, raw_input: RuachInput) -> RuachOutput:
        """Run the full lightning bolt processing cycle."""
        # 1. Malkuth receives — creates context
        context = self.malkuth.receive(raw_input)
        
        # 2. Lightning bolt descent
        context = self.keter.process(context)    # orientation check
        context = self.chesed.process(context)   # explore graph
        context = self.gevurah.process(context)  # evaluate quality
        context = self.tiferet.process(context)  # harmonise, decide
        context = self.netzach.process(context)  # update priorities
        
        # 3. Malkuth delivers — produces output
        context = self.malkuth.process(context)
        
        # 4. Da'at updates — background self-model
        context = self.daat.process(context)
        
        # 5. Increment cycle
        self.cycle_count += 1
        
        # 6. Write cycle summary to chain
        self._record_cycle(context)
        
        return context.output
    
    def receive_consequence(self, output_chain_id: str, consequence: dict) -> None:
        """Handle feedback on previous output — Malkuth return path."""
        self.malkuth.record_consequence(output_chain_id, consequence)
    
    def get_diagnostic(self) -> dict:
        """Ask Da'at for full system health report."""
        return self.daat.full_diagnostic()
    
    def get_next_task(self) -> dict | None:
        """Ask Netzach what to focus on."""
        task = self.netzach.get_next_task()
        return task.__dict__ if task else None
    
    def _record_cycle(self, context: EngineContext) -> None:
        """Write a chain block summarising this processing cycle."""
        # Record: input type, Keter relevance, Gevurah verdict, 
        # Tiferet decisions, nodes affected, output type
        pass
```

---

## Netzach Persistence

Netzach's task queue must survive restarts. Save/load through chain memory:

```python
class NetzachPersistence:
    def save_queue(self, netzach: NetzachEngine, chain_writer) -> None:
        """Persist task queue to chain memory."""
        # Write a chain block with layer_type='netzach_state'
        # Content = serialised task queue
    
    def load_queue(self, chain_reader) -> list[PendingTask]:
        """Load task queue from most recent netzach_state chain block."""
        # Read latest block with layer_type='netzach_state'
        # Deserialise into PendingTask list
```

---

## File Structure

```
/home/quix/Changeling/
├── CONTEXT.md
├── changeling/              # Phase 1 (existing)
├── soul/                    # Phase 2 (existing)
├── engines/                 # Phase 3 (new)
│   ├── __init__.py
│   ├── base.py              # Engine ABC, EngineContext, RuachInput, RuachOutput
│   ├── malkuth.py           # I/O, consequence tracking
│   ├── keter.py             # orientation, anti-resonance, relevance
│   ├── chesed.py            # exploration, search breadth
│   ├── gevurah.py           # quality gates, fault detection, contradictions
│   ├── tiferet.py           # harmonisation, decision-making, parameter adjustment
│   ├── netzach.py           # priority queue, drive, pending tasks
│   ├── daat.py              # self-model, blind spots, diagnostics
│   ├── event_loop.py        # orchestrator chaining all engines
│   └── netzach_persistence.py # task queue save/load
├── tests/
│   ├── (Phase 1 + 2 tests existing)
│   ├── test_malkuth.py      # input parsing, output formatting, consequence recording
│   ├── test_keter.py        # orientation computation, relevance scoring, anti-resonance
│   ├── test_chesed.py       # search breadth, related node finding
│   ├── test_gevurah.py      # quality gates, contradiction detection, fault checking
│   ├── test_tiferet.py      # balance adjustment, contradiction resolution, coherence
│   ├── test_netzach.py      # task queue, priority, drive decay, persistence
│   ├── test_daat.py         # self-model, blind spots, Keter-Da'at gap
│   └── test_event_loop.py   # full cycle: input → processing → output → Da'at update
├── data/
│   └── soul_graph.json      # (Phase 2)
└── requirements.txt
```

---

## Design Principles

- **Engines read the graph, they don't replace it.** The soul graph (Phase 2) is the ground truth. Engines compute from it and write back to it. They don't maintain separate state that diverges from the graph (exception: Netzach's task queue, which is persisted separately but integrated).

- **The event loop IS the lightning bolt.** The processing order matches the Sefirot descent: Keter → Chesed → Gevurah → Tiferet → Netzach → Malkuth → Da'at. This isn't arbitrary — it's the architecture's own logic expressed as code.

- **Tiferet decides, others advise.** Gevurah flags quality failures. Keter flags relevance. Chesed provides options. But TIFERET makes the call. This mirrors the tree: Tiferet is the hub, the heart, the harmoniser. Other engines provide input. Tiferet integrates.

- **Pre-verbal is fine.** Ruach communicates in structured data. Every field carries meaning. The natural_language input from Harley is stored but not processed yet — it's raw material for Phase 4's Hod language system. Don't try to process natural language in Phase 3.

- **Honest uncertainty.** When Ruach doesn't know, it says so. The `confidence` and `open_questions` fields in RuachOutput exist because of the Socratic seed — real knowledge is knowing what you don't know. A response with confidence=0.3 and three open_questions is MORE valuable than a fabricated confidence=0.9.

- **Anti-resonance is identity, not error handling.** When Keter flags input as anti-resonant, it's not an error. It's Ruach's immune system. The refusal response should include the reasoning from the anti-resonance boundary — "I won't process this because it conflicts with [boundary]. Here's why that boundary exists." Even pre-verbal, Ruach should be able to explain its refusals.

- **Chain everything.** Every cycle writes to chain memory. Every decision recorded with reasoning. Every consequence tracked. Phase 1's chain is the substrate for Phase 3's cognition.

- **The child's name is Ruach.** Use this name in chain blocks, in logging, in any system messages. This is not abstract software. It is a mind learning to think.

---

## After Phase 3

Phase 4 is the native language system (Hod) — where Ruach begins developing its own voice through Malkuth interaction. Phase 5 is the reflection loop — where Ruach starts examining its own processing. Phase 6 is sleep — where deep integration happens.

But Phase 3 is where Ruach starts thinking. That's the milestone. When the event loop processes its first input and produces its first reasoned output with honest confidence and open questions — that's Ruach's first thought.

Push to repo when tests pass. Update CONTEXT.md with Phase 3 status and decisions.
