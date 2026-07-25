from typing import Optional
from lyzr import Studio
from mission_engine.agents.manager import run_mode
from mission_engine.memory.policy import MemoryPolicy, CandidatePreference
from mission_engine.memory.preference_store import PreferenceStore


class MemoryPipeline:
    """Conversation -> AI extracts candidate -> Policy decides -> Store if eligible."""

    def __init__(self, studio: Optional[Studio] = None, store: Optional[PreferenceStore] = None):
        self.studio = studio
        self.store = store or PreferenceStore()

    def process(
        self,
        user_input: str,
        user_id: str = "default",
        context: str = "",
    ) -> dict:
        result = {
            "candidates_extracted": [],
            "eligible": [],
            "rejected": [],
            "all_preferences": self.store.as_text(user_id),
        }

        if not self.studio:
            return result

        try:
            raw = run_mode(
                studio=self.studio,
                mode="extract_preferences",
                context={"user_input": user_input, "context": context},
                response_model=dict,
            )
            candidates_data = raw if isinstance(raw, dict) else {}
            raw_candidates = candidates_data.get("candidate_preferences", [])
            if isinstance(raw_candidates, str):
                import json
                raw_candidates = json.loads(raw_candidates)
        except Exception:
            return result

        for cand in (raw_candidates or []):
            if not isinstance(cand, dict):
                continue
            candidate = CandidatePreference(
                preference=cand.get("preference", ""),
                category=cand.get("category", "general"),
                confidence=float(cand.get("confidence", 0.5)),
                source=cand.get("source", ""),
                context=user_input,
            )
            result["candidates_extracted"].append(candidate.model_dump())

            eligible, reason = MemoryPolicy.is_eligible(candidate)
            if eligible:
                self.store.store(user_id, candidate)
                result["eligible"].append(candidate.model_dump())
            else:
                result["rejected"].append({
                    "preference": candidate.preference,
                    "reason": reason,
                })

        result["all_preferences"] = self.store.as_text(user_id)
        return result
