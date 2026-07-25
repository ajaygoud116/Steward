from typing import Optional, Any
from mission_engine.core.workflow import MissionWorkflow
from mission_engine.core.mission_context import MissionContext
from mission_engine.core.evidence import ExecutionResult, EvidenceEnvelope, StepOutput
from mission_engine.storage.mission_store import MissionStore
from mission_engine.services.approval import ApprovalGate
from mission_engine.services.execution_journal import ExecutionJournal
from mission_engine.services.dedup import DuplicatePrevention
from mission_engine.services.retry import RetryPolicy, FailureClass
from mission_engine.memory.preference_store import PreferenceStore


class MissionRuntime:
    """Generic workflow orchestrator. Knows NOTHING about travel."""

    def __init__(
        self,
        store: Optional[MissionStore] = None,
        journal: Optional[ExecutionJournal] = None,
        gate: Optional[ApprovalGate] = None,
        dedup: Optional[DuplicatePrevention] = None,
        pref_store: Optional[PreferenceStore] = None,
    ):
        self.store = store or MissionStore()
        self.journal = journal
        self.gate = gate or ApprovalGate(self.store)
        self.dedup = dedup or DuplicatePrevention()
        self.pref_store = pref_store or PreferenceStore()

    def run(
        self,
        workflow: MissionWorkflow,
        user_input: str,
        user_id: str = "default",
        auto_approve: bool = True,
        override_intent: Any = None,
        **kwargs,
    ) -> ExecutionResult:
        ctx = MissionContext(
            user_input=user_input,
            user_id=user_id,
            auto_approve=auto_approve,
        )
        j_entries: list[dict] = []

        def journal(node: str, status: str, summary: str = "", data: Any = None, error: str = ""):
            j_entries.append({"node": node, "status": status, "summary": summary, "data": data, "error": error})

        cognis = self.pref_store.as_text(user_id)
        journal("retrieve_cognis", "success", summary=f"Loaded preferences: {cognis}")

        is_override = override_intent is not None
        intent = workflow.interpret(ctx, override_intent=override_intent)
        intent_dict = intent.model_dump() if hasattr(intent, "model_dump") else (intent if isinstance(intent, dict) else {})
        intent_valid, intent_missing = workflow.validate_intent(intent)
        if is_override:
            journal("interpret_override", "success", summary="Override intent provided")
        else:
            journal("interpret", "success" if intent_valid else "partial",
                    summary="Intent interpreted")

        plan = workflow.build_plan(intent)
        plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else (plan if isinstance(plan, dict) else {})

        if is_override:
            journal("plan_override", "success", summary="Override plan used")
        elif plan_dict.get("workflow"):
            journal("plan_fallback", "success", summary="Fallback plan used")
        else:
            journal("plan", "skipped", summary="Planning skipped — no valid intent")

        record = self.store.create(user_input)
        mid = record.mission_id
        self.store.update(mid, intent=intent_dict, execution_plan=plan_dict)

        step_results: list[StepOutput] = []
        for task in (plan.tasks if hasattr(plan, "tasks") else plan_dict.get("tasks", [])):
            tool = task.required_tool if hasattr(task, "required_tool") else task.get("required_tool", "")
            tid = task.task_id if hasattr(task, "task_id") else task.get("task_id", "")
            tname = task.task_name if hasattr(task, "task_name") else task.get("task_name", "")

            sr = workflow.execute_step(tool, intent, task_id=tid, task_name=tname)

            inject_error = sr.errors[0] if sr.errors and sr.status == "failed" else None
            if inject_error:
                fc = RetryPolicy.classify_failure(inject_error)
                if RetryPolicy.is_retryable(fc):
                    sr = workflow.execute_step(tool, intent, task_id=tid, task_name=tname)
                    sr.status = "success" if sr.output is not None else sr.status

            if sr.errors:
                journal(tool, sr.status,
                        summary=f"{'Retry succeeded' if sr.status == 'success' else 'Failed'}: {sr.errors[0] if sr.errors else ''}",
                        error=sr.errors[0] if sr.errors else "")
            else:
                count = len(sr.output) if isinstance(sr.output, list) else (1 if sr.output else 0)
                journal(tool, sr.status, summary=f"Found {count} results")

            step_results.append(sr)

        evidence = workflow.process_results(step_results, intent)

        journal("constraint_validation", "success",
                summary=f"Budget ok: {evidence.constraints[0].get('is_satisfied', False) if evidence.constraints else '?'}, "
                        f"Dates ok: {evidence.constraints[1].get('is_satisfied', False) if len(evidence.constraints) > 1 else '?'}")
        journal("candidate_generation", "success",
                summary=f"Generated {len(evidence.candidates)} candidates, {len(evidence.candidate_rejected)} rejected")

        dates_invalid = any(
            c.get("type") == "dates" and not c.get("is_satisfied", True)
            for c in evidence.constraints
        )
        no_feasible = len(evidence.candidates) == 0 and not dates_invalid

        if dates_invalid:
            self.gate.mark_waiting_information(mid)
            evidence.ranking_skipped = True
            journal("date_check", "failed", summary="Invalid dates — waiting for clarification")

        if not dates_invalid and not no_feasible:
            journal("ranking", "success", summary=f"Ranked {len(evidence.ranking)} options")
        else:
            evidence.ranking_skipped = True
            journal("ranking", "skipped",
                    summary="Ranking skipped — no feasible candidates or invalid dates")

        should_block = dates_invalid or no_feasible
        if not should_block:
            self.gate.mark_ready(mid)
            self.gate.mark_running(mid)
            if auto_approve:
                self.gate.request_approval(mid)
                ap = self.gate.book(mid)
                evidence.approval = {"status": "auto_approved", "detail": ap}
                journal("approval", "approved", summary="Auto-approved")
            else:
                self.gate.request_approval(mid)
                evidence.approval = {"status": "waiting_approval", "detail": {"ok": True, "to": "waiting_approval"}}
                journal("approval", "waiting", summary="Awaiting user approval")
        else:
            journal("approval", "blocked", summary="Approval skipped — constraints not satisfied")

        if not should_block and evidence.approval and evidence.approval.get("status") == "auto_approved":
            booking = workflow.book(evidence.ranking, mid, self.dedup)
            evidence.booking = booking
            if booking and booking.get("ok"):
                journal("booking", "success", summary="Booking confirmed")
                self.gate.complete(mid)
            elif booking and not booking.get("ok"):
                journal("booking", "skipped", summary=booking.get("error", "Booking failed"))
            else:
                journal("booking", "skipped", summary="No booking result")

        summary = workflow.summarize(evidence, intent)
        journal("mission_record", "success", summary="Mission record saved")

        mission_status = self.gate.get_status(mid) if hasattr(self.gate, "get_status") else record.status
        needs_clarification = len(intent_dict.get("missing_fields", [])) > 0
        result = ExecutionResult(
            user_input=user_input,
            intent=intent_dict,
            execution_plan=plan_dict,
            mission_id=mid,
            mission_status=mission_status,
            evidence=evidence,
            journal=j_entries,
            summary=summary,
            cognis_preferences=cognis,
            needs_clarification=needs_clarification,
        )

        outcome = {
            "ranking": evidence.ranking,
            "booking": evidence.booking,
            "candidates": evidence.candidates,
            "constraints": evidence.constraints,
            "validation": evidence.validation,
        }
        self.store.update(mid, outcome=outcome)
        saved = self.store.get(mid)
        if saved:
            self.store.save(saved)

        if self.journal:
            for e in j_entries:
                self.journal.append(e["node"], e["status"], summary=e.get("summary", ""),
                                    data=e.get("data"), error=e.get("error", ""))
        return result
