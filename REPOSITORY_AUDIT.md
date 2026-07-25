# Repository Audit

> Generated for public release preparation.
> 548 total files scanned, 361 after removing cache/runtime artifacts.

## Classification Legend

| Category | Meaning | Action |
|---|---|---|
| PUBLIC | Source code, public docs, CI config | Keep |
| CACHE | `__pycache__`, `.pytest_cache` | Delete / `.gitignore` |
| SECRET | Contains credentials | Already gitignored |
| RUNTIME | Generated mission data | Delete / `.gitignore` |
| GENERATED | Output of a script | Keep script, delete output |
| REPORT | Internal design/review docs | Delete before public release |
| LEGACY | Backward-compat shims | Keep (harmless) |

---

## 1. Root-level files

| File | Class | Reason | Keep? | Ignore? | Delete? |
|---|---|---|---|---|---|
| `.env` | SECRET | Real API key + Agent ID | No | Yes (already) | N/A |
| `.env.example` | PUBLIC | Placeholder template | Yes | No | No |
| `.gitignore` | PUBLIC | Standard gitignore | Yes | No | No |
| `.github/workflows/ci.yml` | PUBLIC | CI configuration | Yes | No | No |
| `Dockerfile` | PUBLIC | Container build | Yes | No | No |
| `docker-compose.yml` | PUBLIC | Container run | Yes | No | No |
| `requirements.txt` | PUBLIC | Dependencies | Yes | No | No |
| `startup_validator.py` | PUBLIC | Health/validation script | Yes | No | No |
| `app.py` | PUBLIC | FastAPI application | Yes | No | No |
| `demo_pipeline.py` | PUBLIC | Demo pipeline | Yes | No | No |
| `e2e_verify.py` | PUBLIC | E2E verification script | Yes | No | No |
| `lyzr_demo.py` | PUBLIC | Lyzr SDK demo | Yes | No | No |
| `README.md` | PUBLIC | Project readme | Yes | No | No |
| `DEPLOYMENT.md` | PUBLIC | Deployment guide | Yes | No | No |
| ~~`CHECKLIST_BEFORE_PUSH.md`~~ | ~~PUBLIC~~ | ~~Pre-push checklist~~ | ~~Yes~~ | ~~No~~ | ~~Yes (consolidated into PUBLIC_RELEASE_CHECKLIST.md)~~ |
| `ARCHITECTURE_AUDIT.md` | REPORT | Internal audit document | No | Yes | Yes (deleted, gitignored) |
| `BLUEPRINT.md` | REPORT | 100 KB design blueprint | No | Yes | Yes (deleted, gitignored) |
| `BRUTAL_REVIEW.md` | REPORT | Internal code review | No | Yes | Yes (deleted, gitignored) |
| `CODE_VERIFICATION.md` | REPORT | Verification report | No | Yes | Yes (deleted, gitignored) |
| `ENGINEERING_EVIDENCE_REPORT.md` | REPORT | Evidence report | No | Yes | Yes (deleted, gitignored) |
| `FAILURE_MATRIX.md` | REPORT | Failure mode analysis | No | Yes | Yes (deleted, gitignored) |
| `SUPERFLOW_STAGES.md` | REPORT | Superflow stage doc | No | Yes | Yes (deleted, gitignored) |
| `TEST_AUDIT.md` | REPORT | Test audit | No | Yes | Yes (deleted, gitignored) |
| `.pytest_cache/` | CACHE | Pytest cached data | No | Yes | Yes |

---

## 2. `data/` (runtime artifacts)

| File | Class | Reason | Keep? | Ignore? | Delete? |
|---|---|---|---|---|---|
| `data/missions/*.json` (271 files) | RUNTIME | Generated mission records with user queries | No | Yes | Yes |
| `data/preferences/` | RUNTIME | User preference storage (empty) | No | Yes | N/A |

---

## 3. Source code — `mission_engine/`

All files under `mission_engine/` are PUBLIC source code.

| Path | Class | Reason | Keep? | Ignore? | Delete? |
|---|---|---|---|---|---|
| `mission_engine/__init__.py` | PUBLIC | Package init | Yes | No | No |
| `mission_engine/engine.py` | PUBLIC | Core engine | Yes | No | No |
| `mission_engine/agents/*.py` | PUBLIC | Agent manager | Yes | No | No |
| `mission_engine/agents/prompts/*.md` | PUBLIC | LLM prompts | Yes | No | No |
| `mission_engine/agents/schemas/*.py` | PUBLIC | Pydantic schemas | Yes | No | No |
| `mission_engine/core/*.py` | PUBLIC | Runtime, workflow, registry | Yes | No | No |
| `mission_engine/guardrails/*.py` | PUBLIC | RAI policies | Yes | No | No |
| `mission_engine/memory/*.py` | PUBLIC | Memory/preference pipeline | Yes | No | No |
| `mission_engine/models/*.py` | PUBLIC | Model enums | Yes | No | No |
| `mission_engine/observability/*.py` | PUBLIC | Tracing | Yes | No | No |
| `mission_engine/services/*.py` | PUBLIC | Approval, retry, ranking, etc. | Yes | No | No |
| `mission_engine/storage/*.py` | PUBLIC | Mission store | Yes | No | No |
| `mission_engine/superflow/*.py` | PUBLIC | Tool executor | Yes | No | No |
| `mission_engine/workflows/travel/*.py` | PUBLIC | TravelWorkflow | Yes | No | No |
| `mission_engine/workflows/dummy/*.py` | PUBLIC | DummyWorkflow | Yes | No | No |
| `mission_engine/workflows/checklist/*.py` | PUBLIC | ChecklistWorkflow | Yes | No | No |
| `mission_engine/workflows/checklist/EXTENSIBILITY_PROOF.md` | PUBLIC | Extensibility doc | Yes | No | No |
| `mission_engine/**/__pycache__/` | CACHE | Bytecode cache | No | Yes | Yes |

---

## 4. Backward-compat shims (LEGACY)

These files are thin re-exports from `mission_engine/`. They are source code and harmless.

| Path | Class | Reason | Keep? | Ignore? | Delete? |
|---|---|---|---|---|---|
| `workflows/__init__.py` | LEGACY | Empty | Yes | No | No |
| `workflows/base.py` | LEGACY | Re-exports MissionWorkflow | Yes | No | No |
| `workflows/registry.py` | LEGACY | Re-exports WorkflowRegistry | Yes | No | No |
| `workflows/travel/__init__.py` | LEGACY | Empty | Yes | No | No |
| `workflows/travel/schemas.py` | LEGACY | TravelPlan schema | Yes | No | No |
| `workflows/travel/workflow.py` | LEGACY | Re-exports TravelWorkflow | Yes | No | No |
| `models/__init__.py` | LEGACY | Empty | Yes | No | No |
| `models/enums.py` | LEGACY | Re-exports MissionStatus | Yes | No | No |
| `models/schemas.py` | LEGACY | Re-exports TravelPlan | Yes | No | No |
| `agents/__init__.py` | LEGACY | Empty | Yes | No | No |
| `agents/manager.py` | LEGACY | Re-exports get_agent | Yes | No | No |
| `services/__init__.py` | LEGACY | Empty | Yes | No | No |
| `adapters/__init__.py` | LEGACY | Empty | Yes | No | No |
| `guardrails/__init__.py` | LEGACY | Empty | Yes | No | No |
| `workflows/**/__pycache__/` | CACHE | Bytecode cache | No | Yes | Yes |
| `models/**/__pycache__/` | CACHE | Bytecode cache | No | Yes | Yes |
| `agents/**/__pycache__/` | CACHE | Bytecode cache | No | Yes | Yes |

---

## 5. `tests/`

All PUBLIC — source code.

| Path | Class | Reason | Keep? | Ignore? | Delete? |
|---|---|---|---|---|---|
| `tests/__init__.py` | PUBLIC | Package init | Yes | No | No |
| `tests/core/*.py` (14 files) | PUBLIC | Core engine tests | Yes | No | No |
| `tests/architectural/test_architecture.py` | PUBLIC | Architecture tests | Yes | No | No |
| `tests/workflows/travel/__init__.py` | PUBLIC | Travel test init | Yes | No | No |
| `tests/**/__pycache__/` | CACHE | Bytecode cache | No | Yes | Yes |

---

## 6. `demo/` and `verification/`

| Path | Class | Reason | Keep? | Ignore? | Delete? |
|---|---|---|---|---|---|
| `demo/EXPECTED_SCREENSHOTS.md` | PUBLIC | Demo judge guide | Yes | No | No |
| `demo/FAILURE_INJECTION.md` | PUBLIC | Failure injection guide | Yes | No | No |
| `demo/JUDGE_QA.md` | PUBLIC | Judge Q&A | Yes | No | No |
| `demo/JUDGE_SCENARIOS.md` | PUBLIC | Judge scenarios | Yes | No | No |
| `demo/LIVE_DEMO.md` | PUBLIC | Live demo script | Yes | No | No |
| `verification/API_REFERENCE.md` | PUBLIC | API docs | Yes | No | No |
| `verification/CLAIM_CODE_TEST_MATRIX.md` | PUBLIC | Claim mapping | Yes | No | No |
| `verification/CONFIGURATION.md` | PUBLIC | Config docs | Yes | No | No |
| `verification/PROJECT_STRUCTURE.md` | PUBLIC | Structure docs | Yes | No | No |
| `verification/RAW_TEST_RESULTS.md` | PUBLIC | Raw test output | Yes | No | No |
| `verification/REPRODUCE.md` | PUBLIC | Reproduce guide | Yes | No | No |
| `verification/RUNTIME_BEHAVIOR.md` | PUBLIC | Runtime behavior docs | Yes | No | No |

---

## 7. `eval/` and `scripts/`

| Path | Class | Reason | Keep? | Ignore? | Delete? |
|---|---|---|---|---|---|
| `eval/__init__.py` | PUBLIC | Package init | Yes | No | No |
| `eval/metrics.py` | PUBLIC | Evaluation metrics | Yes | No | No |
| `eval/runner.py` | PUBLIC | Evaluation runner | Yes | No | No |
| `eval/scenarios.py` | PUBLIC | Evaluation scenarios | Yes | No | No |
| `scripts/test_modes.ps1` | PUBLIC | Manual test script | Yes | No | No |
| `eval/**/__pycache__/` | CACHE | Bytecode cache | No | Yes | Yes |

---

## Summary

| Category | Files | Action |
|---|---|---|
| PUBLIC (keep) | ~195 | Commit as-is |
| CACHE (delete/ignore) | ~120 `__pycache__` + `.pytest_cache` | Already gitignored |
| RUNTIME (delete/ignore) | 271 JSON files in `data/missions/` | Add to `.gitignore` |
| REPORT (delete) | 8 files (BLUEPRINT.md, BRUTAL_REVIEW.md, AUDIT docs, etc.) | Recommend delete |
| GENERATED (delete) | 1 file (E2E_VERIFICATION.md) | Recommend delete |
| SECRET (ignore) | `.env` | Already gitignored |

**Recommended deletions for public release:** 8 files (all REPORT type)
**Cached/ignored automatically:** ~391 files

## Recommendations

### Should be deleted before public push:

1. `BLUEPRINT.md` — 100 KB internal design document, not relevant to consumers
2. `BRUTAL_REVIEW.md` — Internal code review, contains subjective criticism
3. `ARCHITECTURE_AUDIT.md` — Internal audit
4. `CODE_VERIFICATION.md` — Internal verification report
5. `ENGINEERING_EVIDENCE_REPORT.md` — Internal evidence report
6. `FAILURE_MATRIX.md` — Internal failure analysis
7. `SUPERFLOW_STAGES.md` — Internal design doc
8. `TEST_AUDIT.md` — Internal test audit
9. `CHECKLIST_BEFORE_PUSH.md` — Deleted (consolidated into PUBLIC_RELEASE_CHECKLIST.md)

### Already ignored (no action needed):

- `.env` — gitignored with real API key
- All `__pycache__/` — gitignored
- `.pytest_cache/` — now gitignored
- `data/missions/` — now gitignored
- `data/preferences/` — now gitignored


