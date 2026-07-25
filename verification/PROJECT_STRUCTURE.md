# Project Structure

```
mission_engine/
    core/                       ← Generic, reusable engine (zero travel imports)
        workflow.py             MissionWorkflow(ABC) — the 7-method contract
        workflow_registry.py    Registry mapping string keys to workflow classes
        runtime.py              MissionRuntime — orchestrates any MissionWorkflow
        mission_context.py      Input context (user_input, user_id, auto_approve)
        evidence.py             Generic result envelopes (StepOutput, EvidenceEnvelope, ExecutionResult)
    workflows/
        travel/                 ← TravelWorkflow — first MissionWorkflow implementation
            workflow.py         TravelWorkflow(MissionWorkflow) — all travel domain logic
            intent_schema.py    TravelIntent Pydantic model
            plan_schema.py      ExecutionPlan / ExecutionTask models
            adapters.py         ToolExecutor — deterministic flight/hotel/weather tools
            injection.py        Test helpers for injecting failures
        dummy/                  ← DummyWorkflow — minimal second implementation (extensibility proof)
            workflow.py         DummyWorkflow(MissionWorkflow) — 60 lines, no travel concepts
    services/                   ← Deterministic, domain-agnostic services
        ranking.py              Multi-criteria weighted scoring (deterministic, seeded)
        validation.py           Schema + business rule validation
        constraints.py          Budget, date, and availability constraint checks
        retry.py                Failure classification and retry configuration
        approval.py             State machine: 7 states, 12 allowed transitions out of 56
        execution_journal.py    Append-only journal with timeline reconstruction
        dedup.py                SHA-256 duplicate prevention
    storage/
        mission_store.py        JSON file persistence with atomic writes, corruption handling
    memory/
        preference_store.py     Per-user preference persistence (JSON files)
        policy.py               Eligibility policy (category, confidence, transient keywords)
        pipeline.py             Memory processing pipeline
    guardrails/
        policies.py             RAI guardrails (prompt injection, PII detection, toxicity detection)
    agents/
        manager.py              Lyzr Manager Agent wrapper (interpret, plan, replan, explain modes)
        schemas/                Backward-compatible re-exports of travel schemas
    models/
        core.py                 WorkflowType enum, EngineResponse model
    observability/
        (monitoring hooks)
    superflow/
        flow.py                 Backward-compatible shim delegating to MissionRuntime + TravelWorkflow

app.py                          FastAPI application (8 endpoints)
demo_pipeline.py                End-to-end demonstration (14 steps)
e2e_verify.py                   Automated end-to-end verification (109 checks)

tests/
    core/                       15 test files (300 tests)
        test_approval.py        82 tests — state machine, all 56 transitions
        test_professor_scenarios.py  34 tests — 10 pipeline scenarios
        test_mission_store.py   19 tests — CRUD, persistence, corruption
        test_retry_policy.py    19 tests — classification, retryability
        test_guardrails.py      18 tests — injection, PII, toxicity
        test_agent_eval.py      18 tests — eval metrics
        test_memory_pipeline.py 15 tests — policy, store, pipeline
        test_superflow.py       15 tests — runtime, executor, determinism
        test_ranking_engine.py  13 tests — scoring, normalization, ties
        test_validation_service.py  13 tests — schema, business, tool output
        test_explain_mode.py    13 tests — evidence-grounded explanation
        test_constraint_service.py  12 tests — budget, dates, availability
        test_eval_integration.py 11 tests — pipeline eval integration
        test_execution_journal.py  11 tests — append-only, timeline
        test_cognis_integration.py  7 tests — memory in SuperFlow
    architectural/
        test_architecture.py    14 tests — dependency rules, contract, registry
```
