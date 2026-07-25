from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StepOutput:
    task_id: str = ""
    task_name: str = ""
    required_tool: str = ""
    status: str = "pending"
    output: Any = None
    errors: list[str] = field(default_factory=list)


@dataclass
class EvidenceEnvelope:
    step_results: list[StepOutput] = field(default_factory=list)
    validation: list[dict] = field(default_factory=list)
    constraints: list[dict] = field(default_factory=list)
    candidates: list[dict] = field(default_factory=list)
    candidate_rejected: list[dict] = field(default_factory=list)
    ranking: list[dict] = field(default_factory=list)
    ranking_skipped: bool = False
    approval: Optional[dict] = None
    booking: Optional[dict] = None


@dataclass
class ExecutionResult:
    user_input: str = ""
    intent: Optional[dict] = None
    execution_plan: Optional[dict] = None
    mission_id: str = ""
    mission_status: str = ""
    evidence: EvidenceEnvelope = field(default_factory=EvidenceEnvelope)
    journal: list[dict] = field(default_factory=list)
    summary: str = ""
    cognis_preferences: str = ""
    memory_result: Optional[dict] = None
    needs_clarification: bool = False
