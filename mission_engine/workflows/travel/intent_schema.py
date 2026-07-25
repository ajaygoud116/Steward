from pydantic import BaseModel, Field
from typing import Optional, List


class TravelIntent(BaseModel):
    destination: Optional[str] = None
    origin: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    budget: Optional[float] = None
    passengers: Optional[int] = None
    preferences: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    explicit_preferences: List[str] = Field(default_factory=list)
    reusable_preferences: List[str] = Field(default_factory=list)
    hard_constraints: List[str] = Field(default_factory=list)
    soft_constraints: List[str] = Field(default_factory=list)
