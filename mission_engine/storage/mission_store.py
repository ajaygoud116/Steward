import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel


class MissionRecord(BaseModel):
    mission_id: str
    user_input: str = ""
    status: str = "created"
    intent: Optional[dict] = None
    execution_plan: Optional[dict] = None
    journal: List[dict] = []
    outcome: Optional[dict] = None
    created_at: str = ""
    updated_at: str = ""


import logging

logger = logging.getLogger(__name__)


class MissionStore:
    """File-system backed mission persistence. One JSON file per mission.

    State Ownership
    ---------------
    MissionStore is PERSISTENCE ONLY.  It reads and writes MissionRecord
    data from/to the filesystem.  It MUST NOT be called directly to change
    workflow state.  All state transitions MUST go through ApprovalGate.

    Corrupted file behaviour
    ------------------------
    - Malformed JSON (JSONDecodeError)     → return None / skip silently
    - Empty file                           → return None / skip silently
    - Missing fields in JSON               → Pydantic fills defaults
    - Partial write (crash during write)   → atomic write via temp + rename
    """

    def __init__(self, storage_dir: str = "data/missions"):
        self._root = Path(storage_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        return self._root / f"{mission_id}.json"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read_mission(self, path: Path) -> Optional[MissionRecord]:
        """Read and parse a single mission file. Returns None on any failure."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                logger.warning("Empty mission file: %s", path)
                return None
            data = json.loads(content)
            return MissionRecord(**data)
        except json.JSONDecodeError as e:
            logger.warning("Corrupted mission file %s: %s", path, e)
            return None
        except Exception as e:
            logger.warning("Failed to read mission file %s: %s", path, e)
            return None

    def create(self, user_input: str = "") -> MissionRecord:
        mission_id = uuid.uuid4().hex[:12]
        now = self._now()
        record = MissionRecord(
            mission_id=mission_id,
            user_input=user_input,
            status="created",
            created_at=now,
            updated_at=now,
        )
        self._write(record)
        return record

    def get(self, mission_id: str) -> Optional[MissionRecord]:
        path = self._path(mission_id)
        if not path.exists():
            return None
        return self._read_mission(path)

    def save(self, record: MissionRecord) -> MissionRecord:
        record.updated_at = self._now()
        self._write(record)
        return record

    def update(self, mission_id: str, **updates) -> Optional[MissionRecord]:
        record = self.get(mission_id)
        if record is None:
            return None
        for key, value in updates.items():
            if hasattr(record, key) and value is not None:
                setattr(record, key, value)
        return self.save(record)

    def list_all(self) -> List[MissionRecord]:
        results = []
        for path in sorted(self._root.glob("*.json")):
            record = self._read_mission(path)
            if record is not None:
                results.append(record)
        return results

    def delete(self, mission_id: str) -> bool:
        path = self._path(mission_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def _write(self, record: MissionRecord) -> None:
        path = self._path(record.mission_id)
        tmp = path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(record.model_dump_json(indent=2))
            tmp.replace(path)
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise
