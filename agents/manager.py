from mission_engine.agents.manager import get_agent
from workflows.travel.schemas import TravelPlan

_manager_agent = None


def get_manager_agent(studio):
    global _manager_agent
    if _manager_agent is not None:
        return _manager_agent
    _manager_agent = get_agent(studio=studio, response_model=TravelPlan)
    return _manager_agent
