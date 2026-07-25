from pydantic import BaseModel, Field
from typing import Optional, List


# ── Provenance Map ─────────────────────────────────────────────────────
# Every field in FinalExplanation documents its origin within the system.
# This map is documentation only — the schema and API are unchanged.
#
# Field              │ Source                                            │ Format
# ───────────────────┼───────────────────────────────────────────────────┼───────────
# summary            │ MissionRecord.user_input + outcome + step_results │ Free text
#                    │   Derived from: user_input, execution status,
#                    │   top ranked candidate ID, mission_status
#                    │
# confidence         │ Ranking metadata (top score) + validation outcome  │ 0.0 – 1.0
#                    │   Derived from: ranking[0].total_score if ranking
#                    │   else 0.0; reduced by failed step ratio
#                    │
# reasoning          │ RankingResult + ConstraintResults + JournalEntries │ Free text
#                    │   Derived from: ranking scores, business rule
#                    │   violations, journal execution path
#                    │
# rejected_candidates│ RankingService (all ranked items not selected)     │ List[str]
#                    │   Derived from: ranking[1:] items, each formatted
#                    │   as "{id} - score {score}"
#                    │
# failures           │ ExecutionJournal entries with status == "failed"   │ List[str]
#                    │   Derived from: journal entries where
#                    │   entry.status == "failed", formatted with node
#                    │   name and error message
#                    │
# key_decisions      │ ApprovalGate (approval/bookings)                   │ List[str]
#                    │   RetryPolicy (retry decisions)
#                    │   StateMachine (transition path)
#                    │   Derived from: approval status, booking result,
#                    │   retry attempts, mission status history
#                    │
# evidence_sources   │ Explicit references to artifacts used              │ List[str]
#                    │   Always includes: "mission_record"
#                    │   Conditionally: "execution_journal",
#                    │   "ranking_result", "constraint_results",
#                    │   "validation_results"
# ───────────────────┴───────────────────────────────────────────────────┴───────────


class FinalExplanation(BaseModel):
    summary: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    rejected_candidates: List[str] = Field(default_factory=list)
    failures: List[str] = Field(default_factory=list)
    key_decisions: List[str] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)
