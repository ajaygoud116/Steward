from abc import ABC, abstractmethod
from typing import ClassVar, Any, Optional
from mission_engine.core.mission_context import MissionContext
from mission_engine.core.evidence import StepOutput, EvidenceEnvelope


class MissionWorkflow(ABC):
    workflow_type: ClassVar[str] = ""

    @abstractmethod
    def interpret(self, context: MissionContext, override_intent: Any = None) -> Any:
        ...

    @abstractmethod
    def validate_intent(self, intent: Any) -> tuple[bool, list[str]]:
        ...

    @abstractmethod
    def build_plan(self, intent: Any) -> Any:
        ...

    @abstractmethod
    def execute_step(self, tool: str, intent: Any, task_id: str = "", task_name: str = "") -> StepOutput:
        ...

    @abstractmethod
    def process_results(self, step_results: list[StepOutput], intent: Any) -> EvidenceEnvelope:
        ...

    @abstractmethod
    def book(self, ranking: list[dict], mission_id: str, dedup_check) -> Optional[dict]:
        ...

    @abstractmethod
    def summarize(self, evidence: EvidenceEnvelope, intent: Any) -> str:
        ...
