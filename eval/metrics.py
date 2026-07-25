INTENT_FIELDS = [
    "destination",
    "origin",
    "departure_date",
    "return_date",
    "budget",
    "passengers",
]


def compute_intent_score(
    extracted: dict,
    ground_truth: dict,
) -> float:
    if not extracted or not ground_truth:
        return 0.0
    matches = 0
    total = 0
    for field in INTENT_FIELDS:
        gv = ground_truth.get(field)
        if gv is None:
            continue
        total += 1
        ev = extracted.get(field)
        if ev is not None and _values_match(ev, gv):
            matches += 1
    if total == 0:
        return 1.0
    return matches / total


def _values_match(extracted_val, ground_val) -> bool:
    extracted_str = str(extracted_val).strip().lower()
    ground_str = str(ground_val).strip().lower()
    if extracted_str == ground_str:
        return True
    return ground_str in extracted_str or extracted_str in ground_str


def compute_missing_fields_score(extracted: dict, ground_truth: dict) -> float:
    gt_has_missing = ground_truth.get("has_missing_fields", False)
    extracted_list = extracted.get("missing_fields", [])
    if not isinstance(extracted_list, list):
        return 0.0
    has_missing = len(extracted_list) > 0
    if gt_has_missing == has_missing:
        return 1.0
    return 0.5 if (gt_has_missing and not has_missing) else 0.0


def compute_intent_completeness(extracted: dict) -> float:
    if not extracted:
        return 0.0
    filled = sum(1 for f in INTENT_FIELDS if extracted.get(f) is not None)
    return filled / len(INTENT_FIELDS)


def compute_plan_tool_score(extracted: dict, ground_truth: dict) -> float:
    gt_tools = set(ground_truth.get("expected_tools", []))
    if not gt_tools:
        return 1.0
    extracted_tasks = extracted.get("tasks", [])
    if not isinstance(extracted_tasks, list):
        return 0.0
    found_tools = set()
    for task in extracted_tasks:
        tool = task.get("required_tool") if isinstance(task, dict) else None
        if tool:
            found_tools.add(tool)
    if not found_tools:
        return 0.0
    overlap = gt_tools & found_tools
    precision = len(overlap) / len(found_tools) if found_tools else 0.0
    recall = len(overlap) / len(gt_tools) if gt_tools else 0.0
    if precision + recall == 0:
        return 0.0
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def compute_plan_structure_score(extracted: dict) -> float:
    tasks = extracted.get("tasks", [])
    if not isinstance(tasks, list) or len(tasks) == 0:
        return 0.0
    score = 0.0
    checks = 0
    for task in tasks:
        if not isinstance(task, dict):
            continue
        checks += 4
        if task.get("task_id"):
            score += 1.0
        if task.get("task_name"):
            score += 1.0
        if task.get("required_tool"):
            score += 1.0
        depends = task.get("depends_on", [])
        if isinstance(depends, list) and len(depends) >= 0:
            score += 1.0
    if checks == 0:
        return 0.0
    return score / checks


def compute_approval_score(extracted: dict, ground_truth: dict) -> float:
    gt_approval = ground_truth.get("approval_required", False)
    plan_approval = extracted.get("approval_required", False)
    return 1.0 if gt_approval == plan_approval else 0.0


def compute_replan_failure_class_score(extracted: dict, ground_truth: dict) -> float:
    gt_class = ground_truth.get("expected_failure_class")
    if gt_class is None:
        return 1.0
    extracted_class = extracted.get("failure_class", "")
    if not extracted_class:
        return 0.3
    return 1.0 if extracted_class == gt_class else 0.5


def compute_replan_decision_score(extracted: dict, ground_truth: dict) -> float:
    gt_replan = ground_truth.get("should_replan", True)
    extracted_replan = extracted.get("replan_required", False)
    return 1.0 if gt_replan == extracted_replan else 0.0


def compute_explain_summary_score(extracted: dict, ground_truth: dict) -> float:
    score = 0.0
    checks = 0
    if ground_truth.get("has_summary"):
        checks += 1
        summary = extracted.get("summary", "")
        if summary and len(summary) > 10:
            score += 1.0
    if ground_truth.get("has_reasoning"):
        checks += 1
        reasoning = extracted.get("reasoning", "")
        if reasoning and len(reasoning) > 20:
            score += 1.0
    if ground_truth.get("has_key_decisions"):
        checks += 1
        decisions = extracted.get("key_decisions", [])
        if isinstance(decisions, list) and len(decisions) > 0:
            score += 1.0
    if ground_truth.get("has_evidence_sources"):
        checks += 1
        evidence = extracted.get("evidence_sources", [])
        if isinstance(evidence, list) and len(evidence) > 0:
            score += 1.0
    if checks == 0:
        return 1.0
    return score / checks


def compute_robustness_score(pipeline_result: dict) -> float:
    score = 0.0
    checks = 5
    if pipeline_result.get("mission_id"):
        score += 1.0
    if pipeline_result.get("step_results") and len(pipeline_result["step_results"]) > 0:
        score += 1.0
    if pipeline_result.get("candidates") and len(pipeline_result["candidates"]) > 0:
        score += 1.0
    if pipeline_result.get("ranking") and len(pipeline_result["ranking"]) > 0:
        score += 1.0
    if pipeline_result.get("journal") and len(pipeline_result["journal"]) > 0:
        score += 1.0
    return score / checks


def compute_overall(eval_results: dict[str, dict]) -> dict:
    categories = {}
    for name, result in eval_results.items():
        cat = result.get("category", "uncategorized")
        categories.setdefault(cat, {"count": 0, "total_scores": []})
        categories[cat]["count"] += 1
        categories[cat]["total_scores"].append(result.get("overall", 0.0))

    per_category = {}
    for cat, data in categories.items():
        per_category[cat] = round(sum(data["total_scores"]) / data["count"], 2) if data["count"] else 0.0

    all_scores = [r.get("overall", 0.0) for r in eval_results.values()]
    overall = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    return {
        "overall_score": overall,
        "per_category": per_category,
        "num_scenarios": len(eval_results),
    }
