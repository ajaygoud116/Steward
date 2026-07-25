from pydantic import BaseModel, ValidationError
from typing import Type, List, Dict, Any
from datetime import datetime


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]


class ValidationService:
    """Deterministic validation: schema conformance, business rules, tool output."""

    @staticmethod
    def validate_schema(data: Dict[str, Any], model: Type[BaseModel]) -> ValidationResult:
        try:
            model(**data)
            return ValidationResult(is_valid=True, errors=[])
        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()],
            )

    @staticmethod
    def validate_business(data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []

        destination = data.get("destination", "")
        origin = data.get("origin", "")
        departure = data.get("departure_date", "")
        return_date = data.get("return_date", "")
        budget = data.get("budget", 0)
        passengers = data.get("passengers", 0)

        if destination and origin and destination.lower() == origin.lower():
            errors.append("Destination and origin must be different")

        if departure:
            try:
                dep = datetime.strptime(departure, "%Y-%m-%d").date()
                if dep < datetime.now().date():
                    errors.append("Departure date must be today or in the future")
            except ValueError:
                errors.append(f"Invalid departure date format: {departure} (expected YYYY-MM-DD)")

        if return_date:
            try:
                ret = datetime.strptime(return_date, "%Y-%m-%d").date()
                if departure:
                    dep = datetime.strptime(departure, "%Y-%m-%d").date()
                    if ret <= dep:
                        errors.append("Return date must be after departure date")
            except ValueError:
                errors.append(f"Invalid return date format: {return_date} (expected YYYY-MM-DD)")

        budget_float = float(budget) if not isinstance(budget, float) else budget
        if budget_float <= 0:
            errors.append("Budget must be greater than zero")

        if passengers < 1:
            errors.append("Passengers must be at least 1")
        elif passengers > 100:
            errors.append("Passengers exceeds maximum group size of 100")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    @staticmethod
    def validate_tool_output(output: Dict[str, Any], expected_fields: List[str]) -> ValidationResult:
        errors: List[str] = []
        for field in expected_fields:
            if field not in output:
                errors.append(f"Missing required field '{field}' in tool output")
            elif output[field] is None:
                errors.append(f"Required field '{field}' is null in tool output")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
