# Reproduce

## Prerequisites

| Item | Version |
|---|---|
| Python | 3.10.11 |
| OS tested | Windows 10 (x64) |
| pip | 26.0.1 |

## Setup

```powershell
# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate        # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

Copy the example file and fill in values:

```powershell
copy .env.example .env
```

Required variables are documented in `verification/CONFIGURATION.md`.

## Start the Application

```powershell
uvicorn app:app --reload --port 8000
```

The API is available at `http://localhost:8000`.

Health check:

```powershell
curl http://localhost:8000/health
# {"status":"ok"}
```

## Run Tests

```powershell
# Full test suite (314 tests)
pytest

# Core engine tests only
pytest tests/core/

# Architecture constraint tests only
pytest tests/architectural/
```

Expected output:

```
314 passed in ~17s
```

## Run Demo

```powershell
python demo_pipeline.py
```

Expected output (last 5 lines):

```
  14/14 CRITERIA DEMONSTRATED
  TRAVEL WORKFLOW + DUMMY WORKFLOW
  ARCHITECTURE VALIDATED
```

## Run End-to-End Verification

```powershell
python e2e_verify.py
```

Expected output (last line):

```
  Written: E2E_VERIFICATION.md (109 checks, 109 passed, 0 failed)
```

## Verify the DummyWorkflow Extensibility

```powershell
python -c "
from mission_engine.core.runtime import MissionRuntime
from mission_engine.core.workflow_registry import WorkflowRegistry
from mission_engine.workflows.dummy.workflow import DummyWorkflow

WorkflowRegistry.register(DummyWorkflow)
wf = WorkflowRegistry.get('dummy')()
rt = MissionRuntime()
result = rt.run(workflow=wf, user_input='extensibility check')
print('Status:', result.mission_status)
print('Summary:', result.summary)
"
```

Expected output:

```
Status: completed
Summary: Dummy mission complete. Action: extensibility check, priority: 5.
```

## Git Reference

| Field | Value |
|---|---|
| Commit | `0f4f8339a788a3da9c8e3c2b1ed952d0035bb08a` |
| Branch | `master` |
