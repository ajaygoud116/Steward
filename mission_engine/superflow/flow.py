"""Backward-compatible shim — delegates to MissionRuntime + TravelWorkflow.

All original public names are preserved.
"""
from pydantic import BaseModel
from typing import List, Optional, Any
from lyzr import Studio

from mission_engine.core.runtime import MissionRuntime
from mission_engine.core.evidence import StepOutput, EvidenceEnvelope, ExecutionResult
from mission_engine.workflows.travel.workflow import TravelWorkflow, _DEFAULT_FLIGHT_CRITERIA, _DEFAULT_HOTEL_CRITERIA
from mission_engine.workflows.travel.adapters import ToolExecutor
from mission_engine.workflows.travel.intent_schema import TravelIntent
from mission_engine.workflows.travel.plan_schema import ExecutionPlan, ExecutionTask
from mission_engine.workflows.travel.injection import inject_tool_failure, clear_injection, should_fail, inject_malformed_output
from mission_engine.services.ranking import ScoringCriterion, RankingEngine
from mission_engine.services.retry import RetryPolicy, FailureClass
from mission_engine.services.validation import ValidationService
from mission_engine.services.constraints import ConstraintService
from mission_engine.services.approval import ApprovalGate
from mission_engine.services.dedup import DuplicatePrevention
from mission_engine.storage.mission_store import MissionStore
from mission_engine.services.execution_journal import ExecutionJournal
from mission_engine.memory.preference_store import PreferenceStore
from mission_engine.memory.pipeline import MemoryPipeline
from mission_engine.memory.policy import CandidatePreference
from mission_engine.agents.manager import run_mode


class StepResult(BaseModel):
    task_id: str = ""
    task_name: str = ""
    required_tool: str = ""
    status: str = "pending"
    output: Any = None
    errors: List[str] = []


class SuperFlowResult(BaseModel):
    user_input: str = ""
    cognis_preferences: str = ""
    intent: Optional[dict] = None
    execution_plan: Optional[dict] = None
    mission_id: str = ""
    mission_status: str = ""
    step_results: List[StepResult] = []
    validation_results: List[dict] = []
    constraint_results: List[dict] = []
    candidates: List[dict] = []
    candidate_rejected: List[dict] = []
    ranking: List[dict] = []
    ranking_skipped: bool = False
    approval: Optional[dict] = None
    booking: Optional[dict] = None
    journal: List[dict] = []
    memory_result: Optional[dict] = None
    summary: str = ""


class RankingCriteria(BaseModel):
    flight_criteria: List[ScoringCriterion] = []
    hotel_criteria: List[ScoringCriterion] = []


def _execution_to_superflow(er: ExecutionResult, studio) -> SuperFlowResult:
    e = er.evidence
    step_results = [
        StepResult(
            task_id=sr.task_id,
            task_name=sr.task_name,
            required_tool=sr.required_tool,
            status=sr.status,
            output=sr.output,
            errors=list(sr.errors),
        )
        for sr in e.step_results
    ]
    return SuperFlowResult(
        user_input=er.user_input,
        cognis_preferences=er.cognis_preferences,
        intent=er.intent,
        execution_plan=er.execution_plan,
        mission_id=er.mission_id,
        mission_status=er.mission_status,
        step_results=step_results,
        validation_results=e.validation,
        constraint_results=e.constraints,
        candidates=e.candidates,
        candidate_rejected=e.candidate_rejected,
        ranking=e.ranking,
        ranking_skipped=e.ranking_skipped,
        approval=e.approval,
        booking=e.booking,
        journal=er.journal,
        memory_result=er.memory_result,
        summary=er.summary,
    )


class TravelSuperFlow:
    """Backward-compatible shim — delegates to MissionRuntime + TravelWorkflow."""

    def __init__(
        self,
        studio: Optional[Studio] = None,
        store: Optional[MissionStore] = None,
        journal: Optional[ExecutionJournal] = None,
        gate: Optional[ApprovalGate] = None,
        memory_pipeline: Optional[MemoryPipeline] = None,
        pref_store: Optional[PreferenceStore] = None,
        dedup: Optional[DuplicatePrevention] = None,
    ):
        self.studio = studio
        self.store = store or MissionStore()
        self.journal = journal
        self.gate = gate or ApprovalGate(self.store)
        self.pref_store = pref_store or PreferenceStore()
        self.memory_pipeline = memory_pipeline or MemoryPipeline(studio=studio, store=self.pref_store)
        self.dedup = dedup or DuplicatePrevention()
        self._workflow = TravelWorkflow(studio=studio)
        self._runtime = MissionRuntime(
            store=self.store,
            journal=self.journal,
            gate=self.gate,
            dedup=self.dedup,
            pref_store=self.pref_store,
        )

    def run(
        self,
        user_input: str,
        user_id: str = "default",
        auto_approve: bool = True,
        ranking_criteria: Optional[RankingCriteria] = None,
        override_intent: Optional[TravelIntent] = None,
    ) -> SuperFlowResult:
        er = self._runtime.run(
            workflow=self._workflow,
            user_input=user_input,
            user_id=user_id,
            auto_approve=auto_approve,
            override_intent=override_intent,
        )

        result = _execution_to_superflow(er, self.studio)

        if self.studio:
            mem = self.memory_pipeline.process(user_input, user_id=user_id)
            result.memory_result = mem
            result.journal.append({"node": "memory_pipeline", "status": "success",
                                    "summary": f"Stored {len(mem.get('eligible', []))} preferences"})
        else:
            result.journal.append({"node": "memory_pipeline", "status": "skipped",
                                    "summary": "No studio, memory skipped"})

        clear_injection()
        return result
