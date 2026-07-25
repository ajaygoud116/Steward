from mission_engine.services.constraints import ConstraintService


class TestBudgetConstraint:
    def test_within_budget(self):
        plan = {"estimated_cost": 1500}
        result = ConstraintService.check_budget(plan, 2000)
        assert result.is_satisfied

    def test_exceeds_budget(self):
        plan = {"estimated_cost": 2500}
        result = ConstraintService.check_budget(plan, 2000)
        assert not result.is_satisfied
        assert any("exceed" in v.lower() for v in result.violations)

    def test_missing_estimated_cost(self):
        plan = {"estimated_cost": 0}
        result = ConstraintService.check_budget(plan, 2000)
        assert not result.is_satisfied
        assert any("missing" in v.lower() for v in result.violations)


class TestDateConstraint:
    def test_valid_dates(self):
        plan = {"departure_date": "2026-12-01", "return_date": "2026-12-10"}
        result = ConstraintService.check_dates(plan)
        assert result.is_satisfied

    def test_missing_departure(self):
        plan = {"return_date": "2026-12-10"}
        result = ConstraintService.check_dates(plan)
        assert not result.is_satisfied
        assert any("departure" in v.lower() for v in result.violations)

    def test_missing_return(self):
        plan = {"departure_date": "2026-12-01"}
        result = ConstraintService.check_dates(plan)
        assert not result.is_satisfied
        assert any("return" in v.lower() for v in result.violations)

    def test_return_before_departure(self):
        plan = {"departure_date": "2026-12-10", "return_date": "2026-12-01"}
        result = ConstraintService.check_dates(plan)
        assert not result.is_satisfied
        assert any("after" in v.lower() for v in result.violations)

    def test_exceeds_max_duration(self):
        plan = {"departure_date": "2026-01-01", "return_date": "2026-03-01"}
        result = ConstraintService.check_dates(plan)
        assert not result.is_satisfied
        assert any("exceed" in v.lower() for v in result.violations)

    def test_invalid_date_format(self):
        plan = {"departure_date": "01-01-2026", "return_date": "2026-12-01"}
        result = ConstraintService.check_dates(plan)
        assert not result.is_satisfied
        assert any("invalid" in v.lower() or "format" in v.lower() for v in result.violations)


class TestAvailabilityConstraint:
    def test_all_available(self):
        plan = {"requested_items": {"flights": 2, "hotels": 1}}
        inventory = {"flights": 10, "hotels": 5}
        result = ConstraintService.check_availability(plan, inventory)
        assert result.is_satisfied

    def test_item_unavailable(self):
        plan = {"requested_items": {"flights": 2}}
        inventory = {"flights": 0}
        result = ConstraintService.check_availability(plan, inventory)
        assert not result.is_satisfied
        assert any("unavail" in v.lower() for v in result.violations)

    def test_insufficient_quantity(self):
        plan = {"requested_items": {"flights": 10}}
        inventory = {"flights": 3}
        result = ConstraintService.check_availability(plan, inventory)
        assert not result.is_satisfied
        assert any("only" in v.lower() for v in result.violations)
