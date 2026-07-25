from typing import Optional, Any
from pydantic import BaseModel
from mission_engine.core.workflow import MissionWorkflow
from mission_engine.core.mission_context import MissionContext
from mission_engine.core.evidence import StepOutput, EvidenceEnvelope


class DummyIntent(BaseModel):
    action: str = ""
    priority: int = 5
    missing_fields: list[str] = []


class DummyTask(BaseModel):
    task_id: str = ""
    task_name: str = ""
    required_tool: str = ""


class DummyPlan(BaseModel):
    workflow: str = "dummy"
    tasks: list[DummyTask] = []


class DummyWorkflow(MissionWorkflow):
    workflow_type = "dummy"

    def __init__(self, studio=None):
        self.studio = studio

    def interpret(self, context: MissionContext, override_intent: Any = None) -> DummyIntent:
        if override_intent is not None:
            return override_intent
        return DummyIntent(action=context.user_input, priority=5)

    def validate_intent(self, intent: DummyIntent) -> tuple[bool, list[str]]:
        missing = []
        if not intent.action:
            missing.append("action")
        return len(missing) == 0, missing

    def build_plan(self, intent: DummyIntent) -> DummyPlan:
        return DummyPlan(tasks=[
            DummyTask(task_id="p1", task_name="Process", required_tool="process"),
            DummyTask(task_id="p2", task_name="Verify", required_tool="verify"),
        ])

    def execute_step(self, tool: str, intent: DummyIntent, task_id: str = "", task_name: str = "") -> StepOutput:
        sr = StepOutput(task_id=task_id, task_name=task_name, required_tool=tool)
        sr.output = {"tool": tool, "action": intent.action, "result": "ok"}
        sr.status = "success"
        return sr

    def process_results(self, step_results: list[StepOutput], intent: DummyIntent) -> EvidenceEnvelope:
        evidence = EvidenceEnvelope()
        evidence.step_results = step_results
        evidence.candidates = [{"type": "dummy", "id": "item_1", "score": 1.0}]
        evidence.ranking = [{"id": "item_1", "rank": 1, "score": 1.0}]
        evidence.constraints = [
            {"type": "budget", "is_satisfied": True},
            {"type": "dates", "is_satisfied": True},
        ]
        return evidence

    def book(self, ranking: list[dict], mission_id: str, dedup_check) -> Optional[dict]:
        return {"ok": True, "item": ranking[0]["id"] if ranking else "none", "status": "booked"}

    def summarize(self, evidence: EvidenceEnvelope, intent: DummyIntent) -> str:
        return f"Dummy mission complete. Action: {intent.action}, priority: {intent.priority}."
