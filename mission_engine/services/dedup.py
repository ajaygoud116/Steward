import hashlib
import json
from typing import Set


class DuplicatePrevention:
    """Tracks action hashes to prevent duplicate execution."""

    def __init__(self):
        self._executed: Set[str] = set()

    def _hash(self, action: str, **params) -> str:
        raw = json.dumps({"action": action, **params}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def is_duplicate(self, action: str, **params) -> bool:
        h = self._hash(action, **params)
        return h in self._executed

    def mark_executed(self, action: str, **params) -> str:
        h = self._hash(action, **params)
        self._executed.add(h)
        return h

    def clear(self) -> None:
        self._executed.clear()
