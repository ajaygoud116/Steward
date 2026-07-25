from pydantic import BaseModel, Field
from typing import Optional, List


class ExecutionTask(BaseModel):
    task_id: str = ""
    task_name: str = ""
    required_tool: str = ""


class ExecutionPlan(BaseModel):
    workflow: str = "travel"
    tasks: List[ExecutionTask] = []
