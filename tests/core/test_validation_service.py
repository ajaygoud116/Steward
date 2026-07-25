from pydantic import BaseModel
from mission_engine.services.validation import ValidationService


class SampleSchema(BaseModel):
    name: str
    age: int
    email: str


class TestSchemaValidation:
    def test_valid_data(self):
        data = {"name": "Alice", "age": 30, "email": "alice@test.com"}
        result = ValidationService.validate_schema(data, SampleSchema)
        assert result.is_valid
        assert result.errors == []

    def test_missing_field(self):
        data = {"name": "Alice", "age": 30}
        result = ValidationService.validate_schema(data, SampleSchema)
        assert not result.is_valid
        assert any("email" in e for e in result.errors)

    def test_wrong_type(self):
        data = {"name": "Alice", "age": "thirty", "email": "a@b.com"}
        result = ValidationService.validate_schema(data, SampleSchema)
        assert not result.is_valid
        assert any("age" in e for e in result.errors)


class TestBusinessValidation:
    def test_valid_travel_plan(self):
        data = {
            "destination": "Paris",
            "origin": "New York",
            "departure_date": "2026-12-01",
            "return_date": "2026-12-10",
            "budget": 2000,
            "passengers": 2,
        }
        result = ValidationService.validate_business(data)
        assert result.is_valid

    def test_same_origin_destination(self):
        data = {"destination": "Paris", "origin": "Paris"}
        result = ValidationService.validate_business(data)
        assert not result.is_valid
        assert any("different" in e.lower() for e in result.errors)

    def test_departure_in_past(self):
        data = {"departure_date": "2020-01-01"}
        result = ValidationService.validate_business(data)
        assert not result.is_valid
        assert any("future" in e.lower() for e in result.errors)

    def test_return_before_departure(self):
        data = {
            "destination": "Paris",
            "origin": "New York",
            "departure_date": "2026-12-10",
            "return_date": "2026-12-01",
        }
        result = ValidationService.validate_business(data)
        assert not result.is_valid
        assert any("after" in e.lower() for e in result.errors)

    def test_zero_budget(self):
        data = {"budget": 0}
        result = ValidationService.validate_business(data)
        assert not result.is_valid
        assert any("budget" in e.lower() for e in result.errors)

    def test_invalid_passengers(self):
        data = {"passengers": 0}
        result = ValidationService.validate_business(data)
        assert not result.is_valid
        assert any("passenger" in e.lower() for e in result.errors)

    def test_too_many_passengers(self):
        data = {"passengers": 200}
        result = ValidationService.validate_business(data)
        assert not result.is_valid
        assert any("maximum" in e.lower() for e in result.errors)


class TestToolOutputValidation:
    def test_valid_output(self):
        output = {"flights": ["AF123"], "prices": [500]}
        result = ValidationService.validate_tool_output(output, ["flights", "prices"])
        assert result.is_valid

    def test_missing_field(self):
        output = {"flights": ["AF123"]}
        result = ValidationService.validate_tool_output(output, ["flights", "prices"])
        assert not result.is_valid
        assert any("prices" in e for e in result.errors)

    def test_null_field(self):
        output = {"flights": ["AF123"], "prices": None}
        result = ValidationService.validate_tool_output(output, ["flights", "prices"])
        assert not result.is_valid
        assert any("prices" in e for e in result.errors)
