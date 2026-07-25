from mission_engine.superflow.flow import (
    TravelSuperFlow,
    SuperFlowResult,
    ToolExecutor,
    StepResult,
    RankingCriteria,
)
from mission_engine.agents.schemas.travel_intent import TravelIntent
from mission_engine.agents.schemas.execution_plan import ExecutionPlan, ExecutionTask
from mission_engine.services.ranking import ScoringCriterion


PARIS_INTENT = TravelIntent(
    destination="Paris", origin="New York",
    departure_date="2026-12-01", return_date="2026-12-10",
    budget=2000, passengers=2,
)
TOKYO_INTENT = TravelIntent(
    destination="Tokyo", origin="New York",
    departure_date="2026-12-01", return_date="2026-12-10",
    budget=2000, passengers=2,
)
LONDON_INTENT = TravelIntent(
    destination="London", origin="New York",
    departure_date="2026-12-01", return_date="2026-12-10",
    budget=2000, passengers=2,
)


class TestSuperFlowNoStudio:
    """Vertical slice: SuperFlow without Studio (uses deterministic fallback)."""

    def test_run_completes_all_phases(self):
        flow = TravelSuperFlow(studio=None)
        result = flow.run("I want to go to Paris from New York", override_intent=PARIS_INTENT)

        assert isinstance(result, SuperFlowResult)
        assert result.user_input == "I want to go to Paris from New York"

        assert result.intent is not None
        assert result.intent["destination"] == "Paris"
        assert result.intent["origin"] == "New York"

        assert result.execution_plan is not None
        assert result.execution_plan["workflow"] == "travel"

        assert len(result.step_results) == 3
        for sr in result.step_results:
            assert isinstance(sr, StepResult)
            assert sr.status == "success"
            assert sr.output is not None

        assert len(result.validation_results) == 3
        for vr in result.validation_results:
            assert vr["is_valid"] is True

        assert len(result.ranking) > 0
        assert "summary" in result.model_dump()

    def test_step_order(self):
        flow = TravelSuperFlow(studio=None)
        result = flow.run("Paris trip", override_intent=PARIS_INTENT)

        tools = [sr.required_tool for sr in result.step_results]
        assert tools == ["flight_search", "hotel_search", "weather_check"]

    def test_flight_search_output_shape(self):
        flow = TravelSuperFlow(studio=None)
        result = flow.run("Tokyo", override_intent=TOKYO_INTENT)

        flight_step = result.step_results[0]
        flights = flight_step.output
        assert isinstance(flights, list)
        assert len(flights) == 5
        for f in flights:
            assert "id" in f
            assert "airline" in f
            assert "price" in f
            assert "stops" in f
            assert "duration_min" in f

    def test_hotel_search_output_shape(self):
        flow = TravelSuperFlow(studio=None)
        result = flow.run("London", override_intent=LONDON_INTENT)

        hotel_step = result.step_results[1]
        hotels = hotel_step.output
        assert isinstance(hotels, list)
        assert len(hotels) == 5
        for h in hotels:
            assert "id" in h
            assert "name" in h
            assert "price_per_night" in h
            assert "rating" in h

    def test_weather_check_output_shape(self):
        flow = TravelSuperFlow(studio=None)
        result = flow.run("Paris", override_intent=PARIS_INTENT)

        weather_step = result.step_results[2]
        weather = weather_step.output
        assert isinstance(weather, dict)
        assert "destination" in weather
        assert "forecast" in weather
        assert "temperature_c" in weather

    def test_ranking_includes_both_domains(self):
        flow = TravelSuperFlow(studio=None)
        result = flow.run("Paris", override_intent=PARIS_INTENT)

        ranked_ids = [r["id"] for r in result.ranking]
        assert any("AF" in rid or "DL" in rid or "UA" in rid for rid in ranked_ids)
        assert any("hotel" in rid for rid in ranked_ids)

    def test_ranking_sorted_by_score(self):
        flow = TravelSuperFlow(studio=None)
        result = flow.run("Paris", override_intent=PARIS_INTENT)

        flight_ranked = [r for r in result.ranking if "hotel" not in r["id"]]
        for i in range(len(flight_ranked) - 1):
            assert flight_ranked[i]["total_score"] >= flight_ranked[i + 1]["total_score"]


class TestDeterminism:
    def test_same_input_same_output_no_studio(self):
        flow = TravelSuperFlow(studio=None)
        first = flow.run("Paris from New York", override_intent=PARIS_INTENT)
        for _ in range(5):
            again = flow.run("Paris from New York", override_intent=PARIS_INTENT)
            assert first.intent == again.intent
            assert first.execution_plan == again.execution_plan
            for a, b in zip(first.step_results, again.step_results):
                assert a.output == b.output
            assert first.ranking == again.ranking


class TestToolExecutor:
    def test_flight_search_deterministic(self):
        intent = TravelIntent(destination="Paris", origin="New York")
        a = ToolExecutor(intent).flight_search()
        b = ToolExecutor(intent).flight_search()
        assert a == b

    def test_hotel_search_deterministic(self):
        intent = TravelIntent(destination="Paris")
        a = ToolExecutor(intent).hotel_search()
        b = ToolExecutor(intent).hotel_search()
        assert a == b

    def test_weather_check_deterministic(self):
        intent = TravelIntent(destination="Paris", departure_date="2026-08-01")
        a = ToolExecutor(intent).weather_check()
        b = ToolExecutor(intent).weather_check()
        assert a == b

    def test_unknown_tool_raises(self):
        import pytest
        executor = ToolExecutor(TravelIntent())
        with pytest.raises(ValueError, match="Unknown tool"):
            executor.execute("nonexistent_tool")

    def test_flight_search_respects_seed(self):
        paris = ToolExecutor(TravelIntent(destination="Paris", origin="New York"))
        tokyo = ToolExecutor(TravelIntent(destination="Tokyo", origin="New York"))
        assert paris.flight_search() != tokyo.flight_search()


class TestEdgeCases:
    def test_different_destinations_different_results(self):
        a = ToolExecutor(TravelIntent(destination="Paris")).flight_search()
        b = ToolExecutor(TravelIntent(destination="Tokyo")).flight_search()
        assert a != b
        assert all(f["destination"] == "Paris" for f in a)
        assert all(f["destination"] == "Tokyo" for f in b)

    def test_custom_ranking_criteria(self):
        criteria = RankingCriteria(
            flight_criteria=[
                ScoringCriterion(name="price", weight=1.0, direction="minimize", min_value=0, max_value=2000),
            ],
        )
        flow = TravelSuperFlow(studio=None)
        result = flow.run("Paris", ranking_criteria=criteria, override_intent=PARIS_INTENT)
        assert len(result.ranking) > 0
        flight_ranked = [r for r in result.ranking if "hotel" not in r["id"]]
        if flight_ranked:
            assert flight_ranked[0]["total_score"] >= flight_ranked[-1]["total_score"]
