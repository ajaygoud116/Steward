from pydantic import BaseModel, Field
from typing import Optional, List


class ReplanningDecision(BaseModel):
    replan_required: bool = False
    failure_class: Optional[str] = None
    failure_reason: Optional[str] = None
    candidate_relaxations: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
