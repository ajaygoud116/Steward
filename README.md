# Steward is an Autonomous Personal Operations Agent that converts high-level goals into safe, explainable, multi-step task execution.

## Users describe what they want. Steward decides how to accomplish it through structured planning, deterministic execution, approval for irreversible actions, and evidence-backed explanations.

### What Steward Does

Example: "Book me a trip to Goa next weekend under ₹20,000."

Steward:

Understands the request.
Detects missing information.
Builds an execution plan.
Searches flights and hotels.
Validates constraints.
Ranks alternatives.
Requests approval.
Executes booking.
Explains every decision.

That's far more compelling than another architecture diagram.





# Mission Engine — Reusable Workflow Runtime

A deterministic execution runtime that separates **engine** from **workflow**.
`MissionRuntime` depends only on the `MissionWorkflow` contract — domain-specific
behavior is implemented by workflow implementations such as `TravelWorkflow`.
`TravelWorkflow` is the first complete implementation.

## Architecture (Structure)

```
                      ┌─────────────────────────┐
                      │      MissionRuntime      │
                      │                         │
                      │  ├─ State Machine       │
                      │  ├─ Retry Engine        │
                      │  ├─ Journal             │
                      │  ├─ Approval            │
                      │  ├─ Persistence         │
                      │  ├─ Workflow Executor   │
                      │  └─ Evidence Collector  │
                      └─────────┬───────────────┘
                                │
                                ▼
                      ┌─────────────────────────┐
                      │     MissionWorkflow      │
                      │  (ABC — 7 methods)       │
                      └─────────┬───────────────┘
                                │
                                ▼
                      ┌─────────────────────────┐
                      │      TravelWorkflow      │
                      │  (first implementation)  │
                      └─────────┬───────────────┘
                                │
                                ▼
                      ┌─────────────────────────┐
                      │  Deterministic Services  │
                      │  Ranking, Validation,    │
                      │  Constraints, Retry,     │
                      │  State Machine, Dedup,   │
                      │  Journal                 │
                      └─────────┬───────────────┘
                                │
                                ▼
                      ┌─────────────────────────┐
                      │       Evidence           │
                      │  Journal, Constraints,   │
                      │  Ranking, Booking        │
                      └─────────────────────────┘
```

## Request Flow (Sequence)

```
User
  │
  ▼
Manager Agent          ←  AI: interpret request
  │
  ▼
TravelIntent           ←  structured fields (destination, budget, ...)
  │
  ▼
ExecutionPlan          ←  structured plan produced by Manager Agent
  │                        (validated by deterministic layer)
  ▼
MissionRuntime         ←  deterministic orchestrator
  │
  ├── TravelWorkflow   ──  domain logic: execute tools
  │   │
  │   ├── Flight Tool     (deterministic search)
  │   ├── Hotel Tool      (deterministic search)
  │   └── Weather Tool    (deterministic lookup)
  │
  ├── Validation       ──  schema + field-presence checks
  ├── Constraint Check ──  budget / date rules
  ├── Candidate Filter ──  reject out-of-budget items
  ├── Ranking          ──  weighted multi-criteria scoring
  │
  ▼
Approval Gate          ←  state machine: READY → RUNNING → WAITING_APPROVAL → BOOKED
  │
  ├── (auto)           ──  proceeds to booking
  └── (manual)         ──  pauses until user approves
  │
  ▼
Mission Record         ←  persisted to JSON store
  │
  ▼
Manager Explanation   ←  AI: grounded in journal + ranking + booking
  │
  ▼
Response
```

## Autonomous Execution

The Manager Agent interprets a high-level user goal, identifies missing
information, constructs a structured execution plan, and delegates execution
to MissionRuntime. MissionRuntime then completes the workflow without further
user intervention unless an approval gate or missing information requires
explicit interaction.

## Key Design Principles

- **Autonomous execution** — Manager Agent interprets a goal, builds a plan, then MissionRuntime completes the workflow without further user intervention
- **One AI Agent** — Only the Manager performs reasoning; everything else is deterministic
- **Deterministic recovery** — Failures are classified and retried by RetryPolicy without AI involvement
- **Human approval before irreversible actions** — State machine gates booking behind WAITING_APPROVAL
- **Evidence-grounded explanations** — Summaries reference journal entries, ranking results, and mission records

## Repository Structure

```
mission_engine/
    core/                   ← Generic, reusable engine
        workflow.py         ← MissionWorkflow(ABC) — the contract
        workflow_registry.py← Registry: "travel" → TravelWorkflow
        runtime.py          ← MissionRuntime — orchestrates any MissionWorkflow
        mission_context.py  ← Execution context (user input, user_id, auto_approve)
        evidence.py         ← Generic result envelopes
    workflows/
        travel/             ← TravelWorkflow — first implementation
            workflow.py     ← TravelWorkflow(MissionWorkflow)
            intent_schema.py← TravelIntent
            plan_schema.py  ← ExecutionPlan
            adapters.py     ← ToolExecutor (flight, hotel, weather)
            injection.py    ← Test injection helpers
    services/               ← Deterministic, domain-agnostic services
        ranking.py, validation.py, constraints.py, retry.py,
        approval.py, execution_journal.py, dedup.py
    storage/
        mission_store.py    ← Mission persistence (local JSON, atomic writes)
    memory/
        preference_store.py ← Cross-session preference storage
        policy.py           ← Memory eligibility policy
        pipeline.py         ← Memory processing pipeline
    guardrails/
        policies.py         ← RAI guardrails (injection, PII, toxicity detection)
    agents/
        manager.py          ← Lyzr Manager Agent wrapper
        schemas/            ← Backward-compatible re-exports
```

## Reference Implementation: TravelWorkflow

TravelWorkflow implements the complete travel-planning pipeline:
1. **Local Preference Memory** — Load user preferences from memory
2. **Intent Interpretation** — Parse user request into TravelIntent
3. **Planning** — Build execution plan (flight → hotel → weather)
4. **Tool Execution** — Deterministic flight search, hotel search, weather check
5. **Validation** — Schema + field-presence validation on all tool outputs
6. **Constraint Checking** — Budget and date validity
7. **Candidate Generation** — Filter candidates by budget
8. **Ranking** — Multi-criteria weighted scoring (price, stops, rating, distance)
9. **Approval Gate** — State machine: READY → RUNNING → WAITING_APPROVAL → BOOKED
10. **Booking** — With SHA-256 duplicate prevention
11. **Mission Record** — Persist outcome to MissionStore
12. **Summary** — Human-readable execution summary

## Evidence

| Category | What | Result |
|---|---|---|
| **Functional tests** | 300 tests across approval, ranking, retry, validation, constraints, journal, store, memory, guardrails, eval, superflow | All passed |
| **Architectural tests** | 14 tests: runtime imports only MissionWorkflow, contract enforced, dependency direction, no circular imports | All passed |
| **End-to-end demo** | `demo_pipeline.py` — 14 steps incl. injected failure + recovery + DummyWorkflow extensibility proof | 14/14 criteria |
| **End-to-end verification** | `e2e_verify.py` — 109 checks across FastAPI, RAI, Manager, SuperFlow, services | 109/109 passed |
| **Failure recovery** | Injected hotel timeout → TOOL_TIMEOUT classification → retry → success (TestScenario5, demo step 5) | Demonstrated |
| **State machine** | 56 (from, to) transition pairs — only 12 allowed, 44 rejected; verified by 82 parametrized tests | Verified |

```bash
pytest                     # All 314 tests
```

## Why Only One AI Agent?

Only the Manager Agent performs reasoning. Validation, ranking, retry,
approval, persistence, and tool execution are all deterministic — they
follow fixed rules, compute scores, check constraints, or enforce state
transitions. No AI is needed for any of these steps.

Additional AI agents would increase complexity — orchestration, prompt
engineering, failure handling, cost, latency — without improving reasoning
quality, because the non-reasoning steps do not benefit from language
understanding. Every additional agent introduces another reasoning boundary
that requires prompt coordination, state synchronization, and failure
handling.

## AI vs Deterministic Responsibilities

```
AI (Manager Agent)                Deterministic (MissionRuntime + Services)
─────────────────────────          ─────────────────────────────────────────
Interpretation                    Retry (classification + recovery)
Missing information detection     Validation (schema + business rules)
Planning                          Ranking (weighted multi-criteria scoring)
Explanation                       Approval (state machine)
                                  State transitions (56 → 12 allowed)
                                  Persistence (atomic JSON store)
                                  Journaling (append-only)
```

The AI handles only what requires language understanding — extracting intent
from free text, deciding when information is insufficient, constructing a
plan, and summarizing results. Everything else — retry logic, validation,
ranking, state enforcement, storage, and audit trails — is deterministic
Python.

## Why the Runtime Stays Unchanged

**MissionRuntime owns execution semantics.** State transitions, retry logic,
journal append, approval gating, persistence, evidence collection — these are
identical whether the domain is travel, meal planning, or logistics.

**MissionWorkflow owns domain semantics.** How a user request becomes a
structured intent, what tools execute in what order, how results are ranked,
what constitutes a "booking" — these differ per domain.

The seven-stage pipeline (`interpret → validate → plan → execute → process →
book → summarize`) is the same shape for every workflow. Only the
domain-specific implementations of those stages change. Adding a new workflow
does not require modifying `MissionRuntime`, `ApprovalGate`,
`ExecutionJournal`, or `MissionStore`.

## Contract: MissionWorkflow

```python
class MissionWorkflow(ABC):
    workflow_type: ClassVar[str] = ""

    @abstractmethod
    def interpret(self, context, override_intent=None) -> Intent: ...
    @abstractmethod
    def validate_intent(self, intent) -> tuple[bool, list[str]]: ...
    @abstractmethod
    def build_plan(self, intent) -> Plan: ...
    @abstractmethod
    def execute_step(self, tool, intent, task_id="", task_name="") -> StepOutput: ...
    @abstractmethod
    def process_results(self, step_results, intent) -> EvidenceEnvelope: ...
    @abstractmethod
    def book(self, ranking, mission_id, dedup_check) -> Optional[dict]: ...
    @abstractmethod
    def summarize(self, evidence, intent) -> str: ...
```

## Register a New Workflow

```python
from mission_engine.core.workflow import MissionWorkflow

class ResearchWorkflow(MissionWorkflow):
    workflow_type = "research"

    def interpret(self, context, override_intent=None):
        ...   # domain logic here
    def validate_intent(self, intent):
        ...
    # ... 5 more methods

WorkflowRegistry.register(ResearchWorkflow)

# Resolve by string key
wf_cls = WorkflowRegistry.get("research")
MissionRuntime().run(workflow=wf_cls(studio=None), ...)

# See mission_engine/workflows/dummy/ for a complete minimal example
```

## Deployment

### Quick Start

```bash
# Local
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000

# Docker
docker compose up --build
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions (local, Docker, cloud, troubleshooting).

---

## Future Workflows (Not Implemented)

### MissionRuntime is workflow-independent. TravelWorkflow is the reference implementation used to validate the architecture.
Only `TravelWorkflow` exists. The following workflows are candidates that
would implement the same `MissionWorkflow` contract without modifying the
runtime:

- `SchedulingWorkflow` — schedule meetings across calendars
- `ResearchWorkflow` — multi-source research synthesis
- `ShoppingWorkflow` — compare products across vendors
- `EmailWorkflow` — draft, review, send emails
- `MeetingWorkflow` — agenda building, minute taking

Adding any of these requires only a new `workflow.py` file and a
`WorkflowRegistry.register()` call.

## Test Results

| Suite | Count | Status |
|-------|-------|--------|
| Core engine tests | 300 |  All passed |
| Architectural tests | 14 |  All passed |
| Warnings | 5 | Benign Pydantic v1 deprecations |

## Project Status

**Architecture frozen.** Current prototype contains one complete workflow
(Travel) implementing the `MissionWorkflow` contract.
