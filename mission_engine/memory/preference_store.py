import json
from pathlib import Path
from typing import List, Optional
from mission_engine.memory.policy import CandidatePreference


class PreferenceStore:
    """File-backed persistent preference storage. One file per user."""

    def __init__(self, storage_dir: str = "data/preferences"):
        self._root = Path(storage_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, user_id: str) -> Path:
        return self._root / f"{user_id}.json"

    def _load_all(self, user_id: str) -> List[dict]:
        path = self._path(user_id)
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_all(self, user_id: str, entries: List[dict]) -> None:
        path = self._path(user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)

    def store(self, user_id: str, preference: CandidatePreference) -> CandidatePreference:
        entries = self._load_all(user_id)
        new = preference.model_dump()
        if any(e == new for e in entries):
            return preference
        entries.append(new)
        self._write_all(user_id, entries)
        return preference

    def get_all(self, user_id: str) -> List[CandidatePreference]:
        return [CandidatePreference(**e) for e in self._load_all(user_id)]

    def as_text(self, user_id: str) -> str:
        prefs = self.get_all(user_id)
        if not prefs:
            return "None"
        return "; ".join(f"{p.preference}" for p in prefs)
