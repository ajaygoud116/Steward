import os
import uuid
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from lyzr import Studio
from mission_engine.engine import MissionEngine
from mission_engine.models.core import WorkflowType
from mission_engine.agents.manager import run_mode
from mission_engine.agents.schemas.travel_intent import TravelIntent
from mission_engine.agents.schemas.execution_plan import ExecutionPlan
from mission_engine.agents.schemas.replanning import ReplanningDecision
from mission_engine.agents.schemas.explanation import FinalExplanation
from mission_engine.memory.preference_store import PreferenceStore
from mission_engine.memory.pipeline import MemoryPipeline
from mission_engine.guardrails.policies import RAIGuardrails
from workflows.travel.schemas import TravelPlan
from mission_engine.workflows.travel.workflow import TravelWorkflow
from mission_engine.core.workflow_registry import WorkflowRegistry

load_dotenv()

app = FastAPI(title="Mission Engine API")

studio = Studio(api_key=os.getenv("LYZR_API_KEY"))

WorkflowRegistry.register(TravelWorkflow)

engine = MissionEngine(studio=studio)


# ── Existing travel endpoint models ──

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    type: str
    session_id: str

class ClarificationResponse(ChatResponse):
    type: str = "clarification"
    clarification_question: str
    missing_fields: list[str]
    partial_plan: dict

class PlanResponse(ChatResponse):
    type: str = "plan"
    plan: TravelPlan


# ── Mode endpoint models ──

class InterpretRequest(BaseModel):
    message: str
    user_id: str = "default"
    cognis_preferences: str = "None"
    session_id: Optional[str] = None

class PlanRequest(BaseModel):
    travel_intent: str
    session_id: str | None = None

class ReplanRequest(BaseModel):
    failure_evidence: str
    mission_state: str = "{}"
    session_id: str | None = None

class ExplainRequest(BaseModel):
    mission_id: Optional[str] = None
    mission_record: str = "{}"
    execution_journal: str = "[]"
    ranking_result: str = "{}"
    session_id: Optional[str] = None


# ── Root ──

@app.get("/")
def root():
    return {"product": "Mission Engine", "version": "1.0"}


# ── Health ──

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Existing travel plan endpoint ──

@app.post("/travel/plan")
def plan_trip(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    response = engine.process_message(
        message=req.message,
        session_id=session_id,
        workflow_type=WorkflowType.TRAVEL,
    )

    if response.type == "clarification":
        plan = response.data
        return ClarificationResponse(
            clarification_question=plan.clarification_question,
            missing_fields=plan.missing_fields,
            partial_plan=plan.model_dump(exclude={"clarification_question", "missing_fields", "is_complete"}),
            session_id=session_id,
        )

    if response.type == "plan":
        return PlanResponse(plan=response.data, session_id=session_id)

    return ChatResponse(type="error", session_id=session_id)


# ── Phase 2: Manager Agent Modes ──

pref_store = PreferenceStore()
memory_pipeline = MemoryPipeline(studio=studio, store=pref_store)


@app.post("/mode/interpret")
def mode_interpret(req: InterpretRequest):
    rai = RAIGuardrails.check_input(req.message)
    if not rai.passed:
        return {"error": "Input blocked by RAI guardrails", "flags": rai.flags}

    stored = pref_store.as_text(req.user_id)
    cognis = req.cognis_preferences if req.cognis_preferences != "None" else stored

    intent = run_mode(
        studio=studio,
        mode="interpret",
        context={
            "cognis_preferences": cognis,
            "user_input": req.message,
        },
        response_model=TravelIntent,
    )
    result = intent.model_dump()
    result["_cognis_preferences"] = cognis

    memory_pipeline.process(req.message, user_id=req.user_id)

    return result


@app.get("/memory/preferences/{user_id}")
def get_preferences(user_id: str = "default"):
    return {"user_id": user_id, "preferences": pref_store.as_text(user_id)}


@app.post("/memory/process")
def process_memory(req: InterpretRequest):
    result = memory_pipeline.process(req.message, user_id=req.user_id)
    return result


@app.post("/mode/plan")
def mode_plan(req: PlanRequest):
    result = run_mode(
        studio=studio,
        mode="plan",
        context={"travel_intent": req.travel_intent},
        response_model=ExecutionPlan,
    )
    return result.model_dump()


@app.post("/mode/replan")
def mode_replan(req: ReplanRequest):
    result = run_mode(
        studio=studio,
        mode="replan",
        context={
            "failure_evidence": req.failure_evidence,
            "mission_state": req.mission_state,
        },
        response_model=ReplanningDecision,
    )
    return result.model_dump()


@app.post("/mode/explain")
def mode_explain(req: ExplainRequest):
    from mission_engine.storage.mission_store import MissionStore

    if req.mission_id:
        store = MissionStore()
        record = store.get(req.mission_id)
        if record:
            mr = record.model_dump_json(indent=2)
            ej = str([e for e in (record.journal or [])])
            rr = str(record.outcome or {})
        else:
            mr, ej, rr = req.mission_record, req.execution_journal, req.ranking_result
    else:
        mr, ej, rr = req.mission_record, req.execution_journal, req.ranking_result

    result = run_mode(
        studio=studio,
        mode="explain",
        context={
            "mission_record": mr,
            "execution_journal": ej,
            "ranking_result": rr,
        },
        response_model=FinalExplanation,
    )
    output_text = str(result.model_dump())
    rai = RAIGuardrails.check_output(output_text)
    if not rai.passed:
        return {"error": "Output blocked by RAI guardrails", "flags": rai.flags, "partial": result.model_dump()}
    return result.model_dump()


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
