from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime


class ConstraintResult(BaseModel):
    is_satisfied: bool
    violations: List[str]


class ConstraintService:
    """Deterministic constraint checks: budget, dates, availability."""

    @staticmethod
    def check_budget(plan: Dict[str, Any], budget: float) -> ConstraintResult:
        violations: List[str] = []
        estimated_cost = plan.get("estimated_cost", 0)
        if estimated_cost <= 0:
            violations.append("Estimated cost is missing or zero")
        elif estimated_cost > budget:
            violations.append(
                f"Estimated cost {estimated_cost} exceeds budget {budget}"
            )
        return ConstraintResult(is_satisfied=len(violations) == 0, violations=violations)

    @staticmethod
    def check_dates(plan: Dict[str, Any]) -> ConstraintResult:
        violations: List[str] = []
        departure = plan.get("departure_date", "")
        return_date = plan.get("return_date", "")

        if not departure:
            violations.append("Departure date is required")
        else:
            try:
                dep = datetime.strptime(departure, "%Y-%m-%d").date()
                if dep < datetime.now().date():
                    violations.append(f"Departure date {departure} is in the past")
            except ValueError:
                violations.append(f"Invalid departure date: {departure}")

        if not return_date:
            violations.append("Return date is required")
        else:
            try:
                ret = datetime.strptime(return_date, "%Y-%m-%d").date()
                if departure:
                    dep = datetime.strptime(departure, "%Y-%m-%d").date()
                    if ret <= dep:
                        violations.append("Return date must be after departure date")
            except ValueError:
                violations.append(f"Invalid return date: {return_date}")

        if departure and return_date:
            try:
                dep = datetime.strptime(departure, "%Y-%m-%d").date()
                ret = datetime.strptime(return_date, "%Y-%m-%d").date()
                days = (ret - dep).days
                if days > 30:
                    violations.append(f"Trip duration {days} days exceeds maximum 30 days")
            except ValueError:
                pass

        return ConstraintResult(is_satisfied=len(violations) == 0, violations=violations)

    @staticmethod
    def check_availability(plan: Dict[str, Any], inventory: Dict[str, Any]) -> ConstraintResult:
        violations: List[str] = []
        requested_items = plan.get("requested_items", {})

        for item, quantity in requested_items.items():
            available = inventory.get(item, 0)
            if available == 0:
                violations.append(f"'{item}' is unavailable")
            elif isinstance(quantity, (int, float)) and isinstance(available, (int, float)):
                if quantity > available:
                    violations.append(
                        f"'{item}' requested {quantity} but only {available} available"
                    )
            elif isinstance(quantity, str):
                violations.append(f"Cannot check availability for '{item}': non-numeric request")

        return ConstraintResult(is_satisfied=len(violations) == 0, violations=violations)
