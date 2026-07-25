from typing import Optional
from lyzr import Studio
from mission_engine.core.runtime import MissionRuntime
from mission_engine.core.workflow_registry import WorkflowRegistry
from mission_engine.core.workflow import MissionWorkflow
from mission_engine.models.core import WorkflowType, EngineResponse


class MissionEngine:
    """Entry point: resolves workflow from registry and runs it via MissionRuntime."""

    def __init__(self, studio: Studio):
        self.studio = studio
        self.runtime = MissionRuntime()

    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        workflow_type: WorkflowType = WorkflowType.TRAVEL,
    ) -> EngineResponse:
        wf_cls: type[MissionWorkflow] = WorkflowRegistry.get(workflow_type.value)
        workflow = wf_cls(studio=self.studio)
        result = self.runtime.run(workflow=workflow, user_input=message)

        if result.intent:
            from pydantic import BaseModel
            class DummyResult(BaseModel):
                clarification_question: str = ""
                missing_fields: list = []
                is_complete: bool = True

            dummy = DummyResult()
            intent = result.intent
            dummy.clarification_question = ""
            missing = intent.get("missing_fields", [])
            dummy.is_complete = len(missing) == 0

            if not dummy.is_complete:
                return EngineResponse(
                    type="clarification",
                    data=dummy,
                    session_id=session_id,
                )
            return EngineResponse(
                type="plan",
                data=dummy,
                session_id=session_id,
            )

        return EngineResponse(
            type="error",
            error="Unexpected response from agent",
            session_id=session_id,
        )
