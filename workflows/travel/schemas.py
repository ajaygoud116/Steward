from pydantic import BaseModel, Field
from typing import List


class TravelPlan(BaseModel):
    destination: str = Field(description="City, airport code, or location name of the trip destination")
    origin: str = Field(description="City, airport code, or location name of departure")
    departure_date: str = Field(description="Departure date in ISO 8601 date format (YYYY-MM-DD)")
    return_date: str = Field(description="Return date in ISO 8601 date format (YYYY-MM-DD)")
    budget: float = Field(ge=0, description="Total budget for the trip in the specified currency, non-negative")
    passengers: int = Field(ge=1, description="Number of passengers (must be at least 1)")
    preferences: List[str] = Field(min_length=0, description="List of traveler preferences (e.g., 'window seat', 'no layovers')")
    missing_fields: List[str] = Field(min_length=0, description="Fields still needed to complete the plan")
    clarification_question: str = Field(description="A single question to clarify missing or ambiguous information")
    is_complete: bool = Field(description="Whether the plan has all essential fields")
