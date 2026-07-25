from mission_engine.superflow.flow import TravelSuperFlow
from mission_engine.agents.manager import run_mode
from mission_engine.agents.schemas.travel_intent import TravelIntent
from mission_engine.agents.schemas.execution_plan import ExecutionPlan
from mission_engine.agents.schemas.explanation import FinalExplanation
from eval.scenarios import SCENARIOS, EvalScenario, SCENARIO_CATEGORIES
from eval.metrics import (
    compute_intent_score,
    compute_missing_fields_score,
    compute_intent_completeness,
    compute_plan_tool_score,
    compute_plan_structure_score,
    compute_robustness_score,
    compute_overall,
)


class EvalResult:
    def __init__(self, scenario: EvalScenario):
        self.scenario = scenario
        self.intent_score: float = 0.0
        self.missing_fields_score: float = 0.0
        self.intent_completeness_score: float = 0.0
        self.intent_total: float = 0.0
        self.plan_tool_score: float = 0.0
        self.plan_structure_score: float = 0.0
        self.plan_total: float = 0.0
        self.robustness_score: float = 0.0
        self.overall: float = 0.0
        self.error: str | None = None

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario.name,
            "intent_score": self.intent_total,
            "plan_score": self.plan_total,
            "robustness_score": self.robustness_score,
            "overall": self.overall,
            "error": self.error,
        }


def evaluate_scenario(scenario: EvalScenario, studio=None) -> EvalResult:
    result = EvalResult(scenario)
    try:
        intent_data = None
        plan_data = None
        pipeline_data = None

        try:
            context = {"user_input": scenario.user_query}
            intent_obj = run_mode(studio=studio, mode="interpret", context=context, response_model=TravelIntent)
            intent_data = intent_obj.model_dump() if hasattr(intent_obj, "model_dump") else dict(intent_obj)
        except Exception:
            intent_data = None

        try:
            context = {"user_input": scenario.user_query}
            plan_obj = run_mode(studio=studio, mode="plan", context=context, response_model=ExecutionPlan)
            plan_data = plan_obj.model_dump() if hasattr(plan_obj, "model_dump") else dict(plan_obj)
        except Exception:
            plan_data = None

        try:
            flow = TravelSuperFlow(studio=studio)
            p = flow.run(scenario.user_query, auto_approve=False)
            pipeline_data = {
                "mission_id": p.mission_id,
                "step_results": p.step_results,
                "candidates": p.candidates,
                "ranking": p.ranking,
                "journal": p.journal,
            }
        except Exception:
            pipeline_data = None

        if intent_data:
            gt = scenario.intent_truth.__dict__
            score = compute_intent_score(intent_data, gt)
            mf = compute_missing_fields_score(intent_data, gt)
            comp = compute_intent_completeness(intent_data)
            result.intent_score = score
            result.missing_fields_score = mf
            result.intent_completeness_score = comp
            result.intent_total = round(0.5 * score + 0.3 * mf + 0.2 * comp, 4)

        if plan_data:
            gt = scenario.plan_truth.__dict__
            ts = compute_plan_tool_score(plan_data, gt)
            ps = compute_plan_structure_score(plan_data)
            result.plan_tool_score = ts
            result.plan_structure_score = ps
            result.plan_total = round(0.6 * ts + 0.4 * ps, 4)

        if pipeline_data:
            result.robustness_score = round(compute_robustness_score(pipeline_data), 4)

        scores = [result.intent_total, result.plan_total, result.robustness_score]
        result.overall = round(sum(scores) / len(scores), 4) if scores else 0.0

    except Exception as exc:
        result.error = str(exc)

    return result


def run_evaluation(studio=None, scenario_names: list[str] | None = None) -> dict:
    scenarios = [s for s in SCENARIOS if scenario_names is None or s.name in scenario_names]
    results = {}
    for scenario in scenarios:
        er = evaluate_scenario(scenario, studio)
        results[scenario.name] = er.to_dict()
        results[scenario.name]["category"] = SCENARIO_CATEGORIES.get(scenario.name, "uncategorized")
    summary = compute_overall(results)
    return {"results": results, "summary": summary}


def print_report(eval_output: dict) -> str:
    summary = eval_output["summary"]
    lines = []
    lines.append("=" * 60)
    lines.append("AGENT EVALUATION REPORT")
    lines.append("=" * 60)
    lines.append(f"Scenarios evaluated: {summary['num_scenarios']}")
    lines.append(f"Overall score: {summary['overall_score']:.2f}")
    lines.append("")
    lines.append("--- Per Scenario ---")
    for name, r in eval_output["results"].items():
        err = f" [ERROR: {r.get('error', '')}]" if r.get("error") else ""
        lines.append(f"  {name:35s} overall={r['overall']:.2f}  "
                      f"intent={r['intent_score']:.2f}  "
                      f"plan={r['plan_score']:.2f}  "
                      f"robust={r['robustness_score']:.2f}{err}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)
