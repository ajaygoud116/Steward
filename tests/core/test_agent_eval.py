from eval.scenarios import SCENARIOS, SCENARIO_MAP, SCENARIO_CATEGORIES
from eval.metrics import (
    compute_intent_score,
    compute_missing_fields_score,
    compute_intent_completeness,
    compute_plan_tool_score,
    compute_plan_structure_score,
    compute_approval_score,
    compute_robustness_score,
    compute_overall,
)


class TestEvalScenariosExist:
    """Verify every scenario has valid structure."""

    def test_all_scenarios_have_names(self):
        for s in SCENARIOS:
            assert s.name

    def test_all_scenarios_have_queries(self):
        for s in SCENARIOS:
            assert s.user_query

    def test_all_scenarios_have_intent_truth(self):
        for s in SCENARIOS:
            assert s.intent_truth is not None

    def test_all_scenarios_have_plan_truth(self):
        for s in SCENARIOS:
            assert s.plan_truth is not None

    def test_unique_names(self):
        names = [s.name for s in SCENARIOS]
        assert len(names) == len(set(names))

    def test_scenario_map_consistent(self):
        for s in SCENARIOS:
            assert SCENARIO_MAP[s.name] is s

    def test_exactly_ten_scenarios(self):
        assert len(SCENARIOS) == 10

    def test_all_have_categories(self):
        for s in SCENARIOS:
            assert s.name in SCENARIO_CATEGORIES


class TestEvalMetricsDeterministic:
    """Metrics must be deterministic - same input always same output."""

    def test_intent_score_perfect_match(self):
        ex = {"destination": "Paris", "origin": "New York"}
        tr = {"destination": "Paris", "origin": "New York"}
        assert compute_intent_score(ex, tr) == 1.0

    def test_intent_score_partial_match(self):
        ex = {"destination": "Paris"}
        tr = {"destination": "Paris", "origin": "New York"}
        score = compute_intent_score(ex, tr)
        assert score > 0.0 and score < 1.0

    def test_missing_fields_detected(self):
        ex = {"missing_fields": ["origin", "dates"]}
        tr = {"has_missing_fields": True}
        assert compute_missing_fields_score(ex, tr) == 1.0

    def test_plan_tool_perfect(self):
        ex = {"tasks": [
            {"required_tool": "flight_search"},
            {"required_tool": "hotel_search"},
            {"required_tool": "weather_check"},
        ]}
        tr = {"expected_tools": ["flight_search", "hotel_search", "weather_check"]}
        assert compute_plan_tool_score(ex, tr) == 1.0

    def test_plan_structure_valid(self):
        ex = {"tasks": [
            {"task_id": "t1", "task_name": "A", "required_tool": "flight_search", "depends_on": []},
            {"task_id": "t2", "task_name": "B", "required_tool": "hotel_search", "depends_on": ["t1"]},
        ]}
        assert compute_plan_structure_score(ex) == 1.0

    def test_plan_approval_match(self):
        assert compute_approval_score({"approval_required": False}, {"approval_required": False}) == 1.0
        assert compute_approval_score({"approval_required": True}, {"approval_required": False}) == 0.0

    def test_robustness_scoring(self):
        pipe = {
            "mission_id": "abc123",
            "step_results": [1, 2, 3],
            "candidates": [1, 2, 3, 4, 5],
            "ranking": [1, 2, 3, 4, 5],
            "journal": list(range(12)),
        }
        assert compute_robustness_score(pipe) == 1.0

    def test_determinism_multiple_calls(self):
        ex = {"destination": "Tokyo", "origin": "Osaka"}
        tr = {"destination": "Tokyo", "origin": "New York"}
        first = compute_intent_score(ex, tr)
        second = compute_intent_score(ex, tr)
        assert first == second
        assert first > 0.0 and first < 1.0

    def test_overall_calculation(self):
        results = {
            "s1": {"category": "basic", "overall": 0.9},
            "s2": {"category": "basic", "overall": 0.7},
            "s3": {"category": "failure", "overall": 0.8},
        }
        summary = compute_overall(results)
        assert summary["overall_score"] == 0.8
        assert summary["per_category"]["basic"] == 0.8
        assert summary["per_category"]["failure"] == 0.8
        assert summary["num_scenarios"] == 3


class TestEvalCategories:
    """Scenarios cover all required evaluation domains."""

    def test_required_categories_present(self):
        cats = set(SCENARIO_CATEGORIES.values())
        for required in ["basic", "constraint", "failure", "governance", "memory", "security"]:
            assert required in cats, f"Missing category: {required}"
