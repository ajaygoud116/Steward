from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from mission_engine.storage.mission_store import MissionStore


class JournalEntry(BaseModel):
    sequence: int
    node: str
    status: str
    timestamp: str
    summary: str = ""
    data: Optional[dict] = None
    error: Optional[str] = None


class ExecutionJournal:
    """Append-only execution journal. Entries are never modified or deleted."""

    def __init__(self, store: MissionStore, mission_id: str):
        self._store = store
        self._mission_id = mission_id

    def append(
        self,
        node: str,
        status: str,
        summary: str = "",
        data: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> JournalEntry:
        record = self._store.get(self._mission_id)
        if record is None:
            raise ValueError(f"Mission {self._mission_id} not found")

        sequence = len(record.journal) + 1
        entry = JournalEntry(
            sequence=sequence,
            node=node,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            data=data,
            error=error,
        )
        record.journal.append(entry.model_dump())
        self._store.save(record)
        return entry

    def entries(self) -> List[JournalEntry]:
        record = self._store.get(self._mission_id)
        if record is None:
            return []
        return [JournalEntry(**e) for e in record.journal]

    def timeline(self) -> List[JournalEntry]:
        return self.entries()

    def reconstruct(self) -> dict:
        entries = self.entries()
        nodes = {}
        for e in entries:
            if e.node not in nodes:
                nodes[e.node] = []
            nodes[e.node].append(e.model_dump())
        return {
            "mission_id": self._mission_id,
            "total_entries": len(entries),
            "nodes": nodes,
            "last_status": entries[-1].status if entries else "none",
        }
