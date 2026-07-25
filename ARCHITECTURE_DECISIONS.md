# Architecture Decisions

## Decision 1: One AI Agent (Manager), Not Multiple Specialized Agents

**Context.** Multi-agent architectures (planner agent, tool-calling agent, QA agent) are common in
agentic frameworks. Each agent adds latency, cost, and failure modes.

**Decision.** Use a single Manager agent invoked in distinct modes (interpret, plan, replan, explain).
The Manager returns structured JSON per mode; the runtime dispatches.

**Consequence.** Simpler debugging, deterministic orchestration, one LLM call per phase.
Tradeoff: the Manager must be prompted precisely for each mode. No parallel agent execution.

---

## Decision 2: Deterministic Ranking — No AI in Scoring

**Context.** Candidate ranking (e.g., flight options) could use LLM-based scoring or learned
models. Both introduce nondeterminism and opacity.

**Decision.** Ranking is a weighted-sum scoring engine with configurable criteria (price, stops,
duration). The same input always produces the same ranking. No LLM call in the ranking step.

**Consequence.** Verifiable, reproducible, auditable. Tradeoff: cannot capture subjective or
context-dependent preferences beyond explicit criteria weights.

---

## Decision 3: Approval Gate Owns State Transitions

**Context.** Mission lifecycle states (created → ready → running → waiting_approval → booked →
completed → failed) could be managed by the workflow or scattered across services.

**Decision.** A single `ApprovalGate` service maintains the state machine and enforces transition
rules (e.g., cannot book before approval). The runtime and workflow both query `can_book()`.

**Consequence.** State logic is centralized and testable. Tradeoff: the gate is a single point of
control — all state transitions pass through it.

---

## Decision 4: MissionRuntime Owns Execution Semantics

**Context.** The runtime orchestrates workflow execution: calling interpret, validate, build_plan,
execute steps, process results, book, summarize. These lifecycle semantics could be implemented
per workflow.

**Decision.** `MissionRuntime` is the generic orchestrator. It calls the `MissionWorkflow` abstract
methods in a fixed order, handles retry, journaling, persistence, and approval gating.
Workflows implement the contract and do not control the lifecycle.

**Consequence.** Adding a new workflow requires zero changes to the runtime. Tradeoff: workflows
cannot customize the execution order or inject logic between lifecycle phases.

---

## Decision 5: TravelWorkflow Owns Domain Semantics

**Context.** Domain-specific logic (how to search flights, parse hotel results, validate trip
constraints) could be embedded in the runtime or exposed as generic tool definitions.

**Decision.** `TravelWorkflow` implements all travel-specific interpretation, planning, execution,
evidence generation, and booking. The runtime has no travel imports. The workflow package
includes its own schemas, adapters, and injection helpers.

**Consequence.** The travel domain is fully encapsulated. Tradeoff: each new workflow duplicates
domain-specific patterns (schemas, adapters) — no cross-workflow code sharing.

---

## Decision 6: WorkflowRegistry for Extensibility

**Context.** New workflows need to be discoverable by the runtime without modifying core files.

**Decision.** A `WorkflowRegistry` singleton maps workflow type strings to workflow classes.
Registration is a one-liner: `WorkflowRegistry.register(MyWorkflow)`. The runtime accepts
a workflow instance directly.

**Consequence.** Zero-config extensibility. Tradeoff: no dependency injection — workflows
receive the studio instance at construction time.

---

## Decision 7: RAI Guardrails as Pre/Post Filters

**Context.** Input and output safety could be enforced inline in the Manager prompt or as a
separate service layer.

**Decision.** `RAIGuardrails.check_input()` runs before any LLM call; `check_output()` runs
before returning results. Both are stateless filters. Blocked inputs return error responses
without consuming LLM quota.

**Consequence.** Safety is decoupled from business logic. Tradeoff: guardrail rules are
currently keyword-pattern-based, not ML-classifier-based.

---

## Decision 8: Execution Journal as Append-Only Trace

**Context.** Debugging multi-step workflow execution requires knowing what happened, in what
order, and with what outcome.

**Decision.** Every lifecycle phase appends a structured entry (node, status, summary) to an
append-only `ExecutionJournal`. The journal is persisted alongside the mission record.
Reconstruction produces a chronological trace.

**Consequence.** Full audit trail without custom logging per workflow. Tradeoff: journal
entries are textual summaries — detailed tool output is not retained.

---

## Decision 9: Retry with Failure Classification

**Context.** Tool calls can fail in different ways (timeout, auth error, invalid input). A
uniform retry policy is too aggressive for non-retryable failures.

**Decision.** `RetryPolicy.classify_failure()` maps error messages to `FailureClass` enums
(TOOL_TIMEOUT, AUTH_ERROR, INVALID_INPUT, etc.). Only retryable classes trigger retry with
configurable max attempts and delay.

**Consequence.** Precise failure handling without hardcoded retry logic. Tradeoff: error
message parsing is heuristic — unexpected error formats fall through to non-retryable.

---

## Decision 10: EvidenceEnvelope as Standard Result Type

**Context.** Workflows produce different kinds of results (candidates, rankings, rejections,
constraint checks). The runtime needs a uniform interface for post-processing.

**Decision.** All workflow results are wrapped in `EvidenceEnvelope` with typed fields:
`step_results`, `validation`, `constraints`, `candidates`, `candidate_rejected`, `ranking`,
`summary`, `booking`. The runtime reads only these fields.

**Consequence.** Post-processing (journaling, approval, persistence) is workflow-agnostic.
Tradeoff: workflows must populate fields that may be irrelevant to their domain (e.g.,
a checklist workflow populates empty constraints arrays).

---

## Decision 11: Separate Memory / Preference Pipeline

**Context.** User preferences (e.g., window seats, vegetarian meals) could be stored inline in
the workflow or managed externally.

**Decision.** A `PreferenceStore` and `MemoryPipeline` manage preference extraction, storage,
and retrieval independent of any workflow. The runtime loads preferences before interpretation
and passes them as context.

**Consequence.** Preferences survive workflow changes and are reusable across domains.
Tradeoff: preference extraction requires an LLM call per interaction.

---

## Decision 12: Fallback Plan When AI Planning Fails

**Context.** The Manager agent may fail to produce a valid execution plan (schema violation,
timeout, refusal).

**Decision.** The runtime catches plan failures and falls back to a hardcoded default plan
(flight_search → hotel_search → weather_check). The fallback is registered at startup.

**Consequence.** The system degrades gracefully. Tradeoff: the fallback is travel-specific —
new workflows must register their own fallback plans.

---

## Decision 13: Duplicate Prevention at Booking Level

**Context.** The same mission could attempt to book the same item twice (retry, race condition,
user double-click).

**Decision.** `DuplicatePrevention` maintains an in-memory set of executed operation signatures
(action + parameters). `is_duplicate()` returns true for repeat attempts; `mark_executed()`
records completion.

**Consequence.** Prevent accidental double-booking without distributed locks. Tradeoff:
in-memory dedup is per-process — does not survive restart.
