from typing import Optional
from mission_engine.models.core import MissionStatus
from mission_engine.storage.mission_store import MissionStore


_TRANSITIONS = {
    MissionStatus.CREATED: {MissionStatus.WAITING_INFORMATION, MissionStatus.READY},
    MissionStatus.WAITING_INFORMATION: {MissionStatus.READY, MissionStatus.FAILED},
    MissionStatus.READY: {MissionStatus.RUNNING, MissionStatus.FAILED},
    MissionStatus.RUNNING: {MissionStatus.WAITING_APPROVAL, MissionStatus.FAILED},
    MissionStatus.WAITING_APPROVAL: {MissionStatus.BOOKED, MissionStatus.FAILED},
    MissionStatus.BOOKED: {MissionStatus.COMPLETED, MissionStatus.FAILED},
    MissionStatus.COMPLETED: set(),
    MissionStatus.FAILED: set(),
}


class ApprovalGate:
    """State machine: CREATED → READY → RUNNING → WAITING_APPROVAL → BOOKED → COMPLETED.

    STATE OWNERSHIP
    ---------------
    ApprovalGate is the SINGLE AUTHORITY for all mission state transitions.
    MissionStore MUST NOT be called directly to change workflow state.
    MissionStore provides persistence only — it reads and writes records.
    All status changes MUST go through ApprovalGate.transition().

    This invariant is enforced by documentation, not by code.
    Future contributors must respect the boundary:
        ApprovalGate  → owns state
        MissionStore  → owns persistence

    FAILED and COMPLETED are terminal states — no transitions out.
    """

    def __init__(self, store: MissionStore):
        self._store = store

    def _transition(self, mission_id: str, to: MissionStatus) -> dict:
        record = self._store.get(mission_id)
        if record is None:
            return {"ok": False, "error": "Mission not found"}

        current = MissionStatus(record.status)
        allowed = _TRANSITIONS.get(current, set())
        if to not in allowed:
            return {
                "ok": False,
                "error": f"Cannot transition from {current.value} to {to.value}",
            }

        self._store.update(mission_id, status=to.value)
        return {"ok": True, "from": current.value, "to": to.value}

    def mark_waiting_information(self, mission_id: str) -> dict:
        return self._transition(mission_id, MissionStatus.WAITING_INFORMATION)

    def mark_ready(self, mission_id: str) -> dict:
        return self._transition(mission_id, MissionStatus.READY)

    def mark_running(self, mission_id: str) -> dict:
        return self._transition(mission_id, MissionStatus.RUNNING)

    def request_approval(self, mission_id: str) -> dict:
        return self._transition(mission_id, MissionStatus.WAITING_APPROVAL)

    def book(self, mission_id: str) -> dict:
        record = self._store.get(mission_id)
        if record is None:
            return {"ok": False, "error": "Mission not found"}
        current = MissionStatus(record.status)
        if current != MissionStatus.WAITING_APPROVAL:
            return {"ok": False, "error": f"Cannot book in state {current.value}. Must be waiting_approval first."}
        return self._transition(mission_id, MissionStatus.BOOKED)

    def complete(self, mission_id: str) -> dict:
        return self._transition(mission_id, MissionStatus.COMPLETED)

    def fail(self, mission_id: str) -> dict:
        return self._transition(mission_id, MissionStatus.FAILED)

    def can_book(self, mission_id: str) -> bool:
        record = self._store.get(mission_id)
        if record is None:
            return False
        return MissionStatus(record.status) == MissionStatus.WAITING_APPROVAL

    def get_status(self, mission_id: str) -> Optional[str]:
        record = self._store.get(mission_id)
        return record.status if record else None
