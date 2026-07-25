from pydantic import BaseModel


class ChecklistIntent(BaseModel):
    title: str = ""
    items: list[str] = []
    missing_fields: list[str] = []
