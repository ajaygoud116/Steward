from pydantic import BaseModel


class ChecklistTask(BaseModel):
    task_id: str = ""
    task_name: str = ""
    required_tool: str = ""


class ChecklistPlan(BaseModel):
    workflow: str = "checklist"
    tasks: list[ChecklistTask] = []
