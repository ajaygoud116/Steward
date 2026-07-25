from pydantic import BaseModel
from typing import Optional


class CandidatePreference(BaseModel):
    preference: str
    category: str = "general"
    confidence: float = 1.0
    source: str = ""
    context: str = ""


_ELIGIBLE_CATEGORIES = {
    "seat", "meal", "hotel", "airline", "room",
    "transport", "timing", "amenity", "service", "general",
}

_TRANSIENT_KEYWORDS = [
    "booked", "bought", "paid", "reserved", "confirmed",
    "today", "tomorrow", "yesterday",
    "price", "cost", "budget",
    "destination", "origin",
    "departure", "return",
    "flight number", "confirmation",
]

_PREFERENCE_KEYWORDS = [
    "prefer", "always", "usually", "like", "love", "want",
    "need", "must have", "requirement", "important",
    "favorite", "best", "better", "rather",
    "habit", "usually do", "normally",
]


class MemoryPolicy:
    """Deterministic rules that decide which preferences are stored."""

    @staticmethod
    def is_eligible(candidate: CandidatePreference) -> tuple[bool, str]:
        prefs = [candidate.preference.lower()]

        if candidate.confidence < 0.5:
            return False, f"Confidence {candidate.confidence} below 0.5 threshold"

        if candidate.category not in _ELIGIBLE_CATEGORIES:
            return False, f"Category '{candidate.category}' not eligible"

        if len(candidate.preference.strip()) < 10:
            return False, f"Preference too short ({len(candidate.preference.strip())} chars)"

        for kw in _TRANSIENT_KEYWORDS:
            for p in prefs:
                if kw in p:
                    return False, f"Contains transient keyword '{kw}'"

        for kw in _PREFERENCE_KEYWORDS:
            for p in prefs:
                if kw in p:
                    return True, "Eligible preference"

        return False, "Not a stated preference (no preference keyword found)"
