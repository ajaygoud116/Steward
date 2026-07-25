from enum import Enum
from pydantic import BaseModel
from typing import Optional, Any


class WorkflowType(str, Enum):
    TRAVEL = "travel"
    SCHEDULING = "scheduling"
    RESEARCH = "research"
    SHOPPING = "shopping"
    LOCAL_SERVICES = "local_services"
    DOCUMENT_ASSIST = "document_assist"
    EMAIL_COMMS = "email_comms"
    TASK_MANAGEMENT = "task_management"


class MissionStatus(str, Enum):
    CREATED = "created"
    WAITING_INFORMATION = "waiting_information"
    READY = "ready"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    BOOKED = "booked"
    COMPLETED = "completed"
    FAILED = "failed"


class EngineResponse(BaseModel):
    type: str
    data: Any = None
    error: Optional[str] = None
    session_id: Optional[str] = None
