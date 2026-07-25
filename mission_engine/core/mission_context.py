from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MissionContext:
    user_input: str = ""
    user_id: str = "default"
    auto_approve: bool = True
    extra: dict = field(default_factory=dict)
