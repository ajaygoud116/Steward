from typing import Dict, Type
from mission_engine.core.workflow import MissionWorkflow


class WorkflowRegistry:
    _registry: Dict[str, Type[MissionWorkflow]] = {}

    @classmethod
    def register(cls, workflow_cls: Type[MissionWorkflow]) -> Type[MissionWorkflow]:
        cls._registry[workflow_cls.workflow_type] = workflow_cls
        return workflow_cls

    @classmethod
    def get(cls, workflow_type: str) -> Type[MissionWorkflow]:
        if workflow_type not in cls._registry:
            raise KeyError(f"No workflow registered for type: {workflow_type}")
        return cls._registry[workflow_type]

    @classmethod
    def list_types(cls) -> list[str]:
        return list(cls._registry.keys())
