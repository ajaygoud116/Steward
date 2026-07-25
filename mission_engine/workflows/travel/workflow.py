from typing import Optional, Any
from mission_engine.core.workflow import MissionWorkflow
from mission_engine.core.mission_context import MissionContext
from mission_engine.core.evidence import StepOutput, EvidenceEnvelope
from mission_engine.core.workflow_registry import WorkflowRegistry
from mission_engine.workflows.travel.intent_schema import TravelIntent
from mission_engine.workflows.travel.plan_schema import ExecutionPlan, ExecutionTask
from mission_engine.workflows.travel.adapters import ToolExecutor
from mission_engine.workflows.travel.injection import should_fail, inject_malformed_output
from mission_engine.services.validation import ValidationService
from mission_engine.services.constraints import ConstraintService
from mission_engine.services.ranking import RankingEngine, ScoringCriterion
from mission_engine.agents.manager import run_mode


_DEFAULT_FLIGHT_CRITERIA = [
    ScoringCriterion(name="price", weight=0.5, direction="minimize", min_value=200, max_value=1200),
    ScoringCriterion(name="stops", weight=0.3, direction="minimize", min_value=0, max_value=3),
    ScoringCriterion(name="duration_min", weight=0.2, direction="minimize", min_value=200, max_value=600),
]

_DEFAULT_HOTEL_CRITERIA = [
    ScoringCriterion(name="price_per_night", weight=0.4, direction="minimize", min_value=50, max_value=300),
    ScoringCriterion(name="rating", weight=0.4, direction="maximize", min_value=1, max_value=5),
    ScoringCriterion(name="distance_km", weight=0.2, direction="minimize", min_value=0, max_value=5),
]


class TravelWorkflow(MissionWorkflow):
    workflow_type = "travel"

    def __init__(self, studio=None):
        self.studio = studio

    def interpret(self, context: MissionContext, override_intent: Any = None) -> TravelIntent:
        if override_intent is not None:
            return override_intent
        if self.studio:
            try:
                return run_mode(
                    studio=self.studio, mode="interpret",
                    context={"cognis_preferences": "", "user_input": context.user_input},
                    response_model=TravelIntent,
                )
            except Exception:
                intent = TravelIntent()
                intent.missing_fields = ["destination", "origin", "departure_date", "return_date", "budget", "passengers"]
                return intent
        intent = TravelIntent()
        intent.missing_fields = ["destination", "origin", "departure_date", "return_date", "budget", "passengers"]
        return intent

    def validate_intent(self, intent: TravelIntent) -> tuple[bool, list[str]]:
        missing = []
        if not intent.destination:
            missing.append("destination")
        if not intent.origin:
            missing.append("origin")
        if not intent.departure_date:
            missing.append("departure_date")
        if not intent.return_date:
            missing.append("return_date")
        return len(missing) == 0, missing

    def build_plan(self, intent: TravelIntent) -> ExecutionPlan:
        if not self.studio:
            return ExecutionPlan(workflow="travel", tasks=[
                ExecutionTask(task_id="t1", task_name="Flight Search", required_tool="flight_search"),
                ExecutionTask(task_id="t2", task_name="Hotel Search", required_tool="hotel_search"),
                ExecutionTask(task_id="t3", task_name="Weather Check", required_tool="weather_check"),
            ])
        if intent.missing_fields and len(intent.missing_fields) > 3:
            return ExecutionPlan(workflow="", tasks=[])
        return ExecutionPlan(workflow="travel", tasks=[
            ExecutionTask(task_id="t1", task_name="Flight Search", required_tool="flight_search"),
            ExecutionTask(task_id="t2", task_name="Hotel Search", required_tool="hotel_search"),
            ExecutionTask(task_id="t3", task_name="Weather Check", required_tool="weather_check"),
        ])

    def execute_step(self, tool: str, intent: TravelIntent, task_id: str = "", task_name: str = "") -> StepOutput:
        sr = StepOutput(task_id=task_id, task_name=task_name, required_tool=tool)
        executor = ToolExecutor(intent)

        inject_error = should_fail(tool)
        if inject_error:
            sr.status = "failed"
            sr.errors = [inject_error]
            from mission_engine.services.retry import RetryPolicy, FailureClass
            fc = RetryPolicy.classify_failure(inject_error)
            if RetryPolicy.is_retryable(fc):
                try:
                    output = executor.execute(tool)
                    sr.output = output
                    sr.status = "success"
                except Exception as e:
                    sr.errors.append(f"retry also failed: {e}")
                    sr.status = "failed"
            return sr

        try:
            output = executor.execute(tool)
            output = inject_malformed_output(tool, output)
            sr.output = output

            if isinstance(output, list):
                expected = ["id", "price"] if "flight" in tool else ["id", "name", "price_per_night"]
            else:
                expected = list(output.keys())

            v = ValidationService.validate_tool_output(
                output if isinstance(output, dict) else {"items": output},
                ["items"] if isinstance(output, list) else expected,
            )

            if v.is_valid:
                sr.status = "success"
            else:
                sr.status = "failed"
                sr.errors = v.errors
        except Exception as e:
            sr.status = "failed"
            sr.errors = [str(e)]

        return sr

    def process_results(self, step_results: list[StepOutput], intent: TravelIntent) -> EvidenceEnvelope:
        evidence = EvidenceEnvelope()
        evidence.step_results = step_results

        validation_results: list[dict] = []
        for sr in step_results:
            validation_results.append({
                "task_id": sr.task_id,
                "tool": sr.required_tool,
                "is_valid": sr.status == "success",
                "errors": sr.errors,
            })
        evidence.validation = validation_results

        plan_dict = intent.model_dump() if hasattr(intent, "model_dump") else {}
        hard_budget = plan_dict.get("budget", None)
        cr = ConstraintService.check_budget({"estimated_cost": hard_budget or 0}, hard_budget or 0)
        dr = ConstraintService.check_dates(plan_dict)
        evidence.constraints = [
            {"type": "budget", **cr.model_dump()},
            {"type": "dates", **dr.model_dump()},
        ]

        candidates: list[dict] = []
        candidate_rejected: list[dict] = []
        for sr in step_results:
            if sr.required_tool == "flight_search" and sr.output and sr.status == "success":
                for f in sr.output:
                    if not all(k in f for k in ("id", "price", "stops", "duration_min", "airline")):
                        continue
                    price = f["price"]
                    if hard_budget is not None and price > hard_budget:
                        candidate_rejected.append({"type": "flight", "id": f["id"], "reason": "exceeds budget"})
                        continue
                    candidates.append({"type": "flight", "id": f["id"], "price": price,
                                       "stops": f["stops"], "duration_min": f["duration_min"],
                                       "airline": f["airline"]})
            if sr.required_tool == "hotel_search" and sr.output and sr.status == "success":
                for h in sr.output:
                    if not all(k in h for k in ("id", "name", "price_per_night", "rating", "distance_km")):
                        continue
                    est_total = h["price_per_night"] * 3
                    if hard_budget is not None and est_total > hard_budget:
                        candidate_rejected.append({"type": "hotel", "id": h["id"], "reason": "exceeds budget"})
                        continue
                    candidates.append({"type": "hotel", "id": h["id"], "name": h["name"],
                                       "price_per_night": h["price_per_night"],
                                       "rating": h["rating"], "distance_km": h["distance_km"]})
        evidence.candidates = candidates
        evidence.candidate_rejected = candidate_rejected

        dates_invalid = not dr.is_satisfied
        no_feasible = len(candidates) == 0 and not dates_invalid
        ranking_results: list[dict] = []
        if not dates_invalid and not no_feasible:
            for sr in step_results:
                if sr.required_tool == "flight_search" and sr.output and sr.status == "success":
                    ranked = RankingEngine.rank(
                        [{"id": f["id"], "price": f["price"], "stops": f["stops"], "duration_min": f["duration_min"]}
                         for f in sr.output if not (hard_budget is not None and f["price"] > hard_budget)],
                        _DEFAULT_FLIGHT_CRITERIA,
                    )
                    ranking_results.extend([r.model_dump() for r in ranked])
                if sr.required_tool == "hotel_search" and sr.output and sr.status == "success":
                    ranked = RankingEngine.rank(
                        [{"id": h["id"], "price_per_night": h["price_per_night"], "rating": h["rating"], "distance_km": h["distance_km"]}
                         for h in sr.output if not (hard_budget is not None and h["price_per_night"] * 3 > hard_budget)],
                        _DEFAULT_HOTEL_CRITERIA,
                    )
                    ranking_results.extend([r.model_dump() for r in ranked])
        else:
            evidence.ranking_skipped = True
        evidence.ranking = ranking_results

        return evidence

    def book(self, ranking: list[dict], mission_id: str, dedup_check) -> Optional[dict]:
        best = ranking[0]["id"] if ranking else "none"
        if dedup_check.is_duplicate("book_flight", flight=best, mission=mission_id):
            return {"ok": False, "error": "Duplicate booking prevented"}
        dedup_check.mark_executed("book_flight", flight=best, mission=mission_id)
        return {"ok": True, "flight": best, "status": "booked"}

    def summarize(self, evidence: EvidenceEnvelope, intent: TravelIntent) -> str:
        step_results = evidence.step_results
        all_ok = all(sr.status == "success" for sr in step_results)
        top = evidence.ranking[0]["id"] if evidence.ranking else "none"

        dates_invalid = any(
            c.get("type") == "dates" and not c.get("is_satisfied", True)
            for c in evidence.constraints
        )
        no_feasible = len(evidence.candidates) == 0 and not dates_invalid

        if evidence.booking and evidence.booking.get("ok"):
            return (
                f"Mission complete. Top flight: {top}. "
                f"Steps: {len(step_results)} total, {sum(1 for s in step_results if s.status == 'success')} succeeded."
            )
        elif dates_invalid:
            return "Invalid dates. Workflow paused — waiting for date clarification."
        elif no_feasible:
            return f"No feasible itinerary within budget. {len(evidence.candidate_rejected)} candidates rejected."
        elif evidence.approval and evidence.approval.get("status") == "waiting_approval":
            return "Mission planned. Waiting approval."
        else:
            failed = sum(1 for s in step_results if s.status == "failed")
            return f"Mission failed or incomplete. Steps: {failed} failed."


WorkflowRegistry.register(TravelWorkflow)
