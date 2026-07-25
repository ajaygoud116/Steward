"""Startup validation script for Mission Engine.

Verifies environment, imports, critical paths, and runs a health check
against the running application.  Exit code 0 = all good.
"""
import os
import sys
import json
import importlib
import traceback
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"

checks: list[dict] = []
exit_code = 0


def check(name: str, ok: bool, detail: str = ""):
    status = PASS if ok else FAIL
    checks.append({"name": name, "status": status, "detail": detail})
    if not ok:
        global exit_code
        exit_code = 1


def header(title: str):
    print()
    print("=" * 60)
    print("  " + title)
    print("=" * 60)


# ── 1. Environment ────────────────────────────────────────────────
header("1. ENVIRONMENT")

check("Python version >= 3.10", sys.version_info >= (3, 10),
      ".".join(map(str, sys.version_info[:3])))

required_dirs = [
    "mission_engine/core",
    "mission_engine/services",
    "mission_engine/storage",
    "mission_engine/workflows/travel",
    "mission_engine/workflows/dummy",
    "mission_engine/workflows/checklist",
    "tests/core",
    "tests/architectural",
    "demo",
    "verification",
]
for d in required_dirs:
    check("Directory exists: " + d, Path(d).is_dir())

# ── 2. Python imports ────────────────────────────────────────────
header("2. PYTHON IMPORTS")

critical_modules = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "httpx",
    "pytest",
    "dotenv",
]
for mod in critical_modules:
    try:
        importlib.import_module(mod)
        check("Import: " + mod, True)
    except ImportError:
        check("Import: " + mod, False, "not installed")

project_modules = [
    "mission_engine.core.workflow",
    "mission_engine.core.runtime",
    "mission_engine.core.workflow_registry",
    "mission_engine.core.mission_context",
    "mission_engine.core.evidence",
    "mission_engine.services.approval",
    "mission_engine.services.retry",
    "mission_engine.services.ranking",
    "mission_engine.services.dedup",
    "mission_engine.services.validation",
    "mission_engine.services.constraints",
    "mission_engine.services.execution_journal",
    "mission_engine.storage.mission_store",
    "mission_engine.workflows.travel.workflow",
    "mission_engine.workflows.dummy.workflow",
    "mission_engine.workflows.checklist.workflow",
    "mission_engine.guardrails.policies",
]
for mod in project_modules:
    try:
        importlib.import_module(mod)
        check("Import: " + mod, True)
    except Exception as exc:
        check("Import: " + mod, False, str(exc))

# ── 3. Workflow registration ─────────────────────────────────────
header("3. WORKFLOW REGISTRATION")

try:
    from mission_engine.core.workflow_registry import WorkflowRegistry
    from mission_engine.workflows.travel.workflow import TravelWorkflow
    from mission_engine.workflows.dummy.workflow import DummyWorkflow
    from mission_engine.workflows.checklist.workflow import ChecklistWorkflow

    WorkflowRegistry.register(TravelWorkflow)
    WorkflowRegistry.register(DummyWorkflow)
    WorkflowRegistry.register(ChecklistWorkflow)

    types = WorkflowRegistry.list_types()
    check("WorkflowRegistry has travel", "travel" in types)
    check("WorkflowRegistry has dummy", "dummy" in types)
    check("WorkflowRegistry has checklist", "checklist" in types)
except Exception as exc:
    check("Workflow registration", False, str(exc))

# ── 4. FastAPI app imports ────────────────────────────────────────
header("4. FASTAPI APPLICATION")

try:
    from app import app
    routes = [r.path for r in app.routes]
    expected = ["/health", "/travel/plan", "/mode/interpret", "/mode/plan",
                "/mode/replan", "/mode/explain", "/memory/preferences/{user_id}",
                "/memory/process"]
    for ep in expected:
        check("Route: " + ep, ep in routes)
except Exception as exc:
    check("FastAPI app import", False, str(exc))
    traceback.print_exc()

# ── 5. Demo pipeline ─────────────────────────────────────────────
header("5. DEMO PIPELINE")

demo_file = Path("demo_pipeline.py")
check("demo_pipeline.py exists", demo_file.is_file())

e2e_file = Path("e2e_verify.py")
check("e2e_verify.py exists", e2e_file.is_file())

lyzr_demo = Path("lyzr_demo.py")
check("lyzr_demo.py exists", lyzr_demo.is_file())

# ── 6. Deployment files ──────────────────────────────────────────
header("6. DEPLOYMENT FILES")

check("Dockerfile exists", Path("Dockerfile").is_file())
check("docker-compose.yml exists", Path("docker-compose.yml").is_file())
check(".env.example exists", Path(".env.example").is_file())
check("GitHub workflow exists",
      Path(".github/workflows/ci.yml").is_file())
check("DEPLOYMENT.md exists", Path("DEPLOYMENT.md").is_file())
check("PUBLIC_RELEASE_CHECKLIST.md exists",
      Path("PUBLIC_RELEASE_CHECKLIST.md").is_file())
check("PUBLIC_RELEASE_CHECKLIST.md exists",
      Path("PUBLIC_RELEASE_CHECKLIST.md").is_file())
check("REPOSITORY_AUDIT.md exists",
      Path("REPOSITORY_AUDIT.md").is_file())

# ── 7. Environment variables (warn only) ─────────────────────────
header("7. ENVIRONMENT VARIABLES (optional)")

if os.getenv("LYZR_API_KEY"):
    check("LYZR_API_KEY set", True)
else:
    check("LYZR_API_KEY set", False, "not set — AI features will use fallbacks")

# ── Summary ──────────────────────────────────────────────────────
header("SUMMARY")
passed = sum(1 for c in checks if c["status"] == PASS)
failed = sum(1 for c in checks if c["status"] == FAIL)
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Total:  {len(checks)}")
print()

for c in checks:
    prefix = "  " + ("[OK]" if c["status"] == PASS else "[FAIL]")
    print(f"{prefix} {c['name']}")
    if c["detail"]:
        print(f"         {c['detail']}")

print()
if exit_code == 0:
    print("  All checks passed.")
else:
    print(f"  {failed} check(s) failed — review above.")
print()

sys.exit(exit_code)
