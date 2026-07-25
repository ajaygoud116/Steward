from typing import Optional

from lyzr import Studio

from mission_engine.core.runtime import MissionRuntime
from mission_engine.core.workflow import MissionWorkflow
from mission_engine.core.workflow_registry import WorkflowRegistry
from mission_engine.models.core import WorkflowType, EngineResponse


class MissionEngine:
    """
    Thin adapter between FastAPI and MissionRuntime.

    Responsibilities:
    - Resolve the workflow
    - Execute the runtime
    - Convert ExecutionResult into EngineResponse

    It MUST NOT contain travel logic.
    """

    def __init__(self, studio: Studio):
        self.studio = studio
        self.runtime = MissionRuntime()

    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        workflow_type: WorkflowType = WorkflowType.TRAVEL,
    ) -> EngineResponse:

        workflow_cls: type[MissionWorkflow] = WorkflowRegistry.get(
            workflow_type.value
        )

        workflow = workflow_cls(studio=self.studio)

        result = self.runtime.run(
            workflow=workflow,
            user_input=message,
        )

        if result is None:
            return EngineResponse(
                type="error",
                error="Runtime returned no result.",
                session_id=session_id,
            )

        intent = result.intent or {}

        missing = intent.get("missing_fields", [])

        if missing:
            return EngineResponse(
                type="clarification",
                data={
                    "clarification_question": self._build_question(missing),
                    "missing_fields": missing,
                    "partial_plan": intent,
                    "runtime": result,
                },
                session_id=session_id,
            )

        return EngineResponse(
            type="plan",
            data={
                "intent": result.intent,
                "execution_plan": result.execution_plan,
                "evidence": result.evidence,
                "summary": result.summary,
                "journal": result.journal,
                "mission_id": result.mission_id,
                "mission_status": result.mission_status,
                "cognis_preferences": result.cognis_preferences,
            },
            session_id=session_id,
        )

    @staticmethod
    def _build_question(missing_fields: list[str]) -> str:
        """
        Creates a simple clarification prompt.
        """

        if not missing_fields:
            return ""

        if len(missing_fields) == 1:
            return f"Please provide your {missing_fields[0].replace('_',' ')}."

        fields = ", ".join(
            field.replace("_", " ")
            for field in missing_fields[:-1]
        )

        last = missing_fields[-1].replace("_", " ")

        return f"Please provide your {fields} and {last}."