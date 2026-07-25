from typing import Optional, Any
from mission_engine.core.workflow import MissionWorkflow
from mission_engine.core.mission_context import MissionContext
from mission_engine.core.evidence import StepOutput, EvidenceEnvelope
from mission_engine.workflows.checklist.intent_schema import ChecklistIntent
from mission_engine.workflows.checklist.plan_schema import ChecklistPlan, ChecklistTask


class ChecklistWorkflow(MissionWorkflow):
    workflow_type = "checklist"

    def __init__(self, studio=None):
        self.studio = studio

    def interpret(self, context: MissionContext, override_intent: Any = None) -> ChecklistIntent:
        if override_intent is not None:
            return override_intent
        lines = [l.strip() for l in context.user_input.split(",") if l.strip()]
        return ChecklistIntent(title=lines[0] if lines else "untitled", items=lines)

    def validate_intent(self, intent: ChecklistIntent) -> tuple[bool, list[str]]:
        missing = []
        if len(intent.items) == 0:
            missing.append("items")
        return len(missing) == 0, missing

    def build_plan(self, intent: ChecklistIntent) -> ChecklistPlan:
        return ChecklistPlan(tasks=[
            ChecklistTask(task_id=f"c{i}", task_name=item, required_tool="check")
            for i, item in enumerate(intent.items)
        ])

    def execute_step(self, tool: str, intent: ChecklistIntent, task_id: str = "", task_name: str = "") -> StepOutput:
        sr = StepOutput(task_id=task_id, task_name=task_name, required_tool=tool)
        sr.output = {"item": task_name, "status": "done"}
        sr.status = "success"
        return sr

    def process_results(self, step_results: list[StepOutput], intent: ChecklistIntent) -> EvidenceEnvelope:
        evidence = EvidenceEnvelope()
        evidence.step_results = step_results
        evidence.validation = [
            {"task_id": sr.task_id, "tool": sr.required_tool, "is_valid": sr.status == "success", "errors": sr.errors}
            for sr in step_results
        ]
        evidence.constraints = [
            {"type": "budget", "is_satisfied": True},
            {"type": "dates", "is_satisfied": True},
        ]
        evidence.candidates = [{"type": "checklist", "id": f"item_{i}"} for i in range(len(step_results))]
        evidence.ranking = [{"id": f"item_{i}", "rank": i + 1, "score": 1.0} for i in range(len(step_results))]
        return evidence

    def book(self, ranking: list[dict], mission_id: str, dedup_check) -> Optional[dict]:
        return {"ok": True, "items": len(ranking), "status": "checked"}

    def summarize(self, evidence: EvidenceEnvelope, intent: ChecklistIntent) -> str:
        done = sum(1 for sr in evidence.step_results if sr.status == "success")
        total = len(evidence.step_results)
        return f"Checklist '{intent.title}': {done}/{total} items checked."
