from pydantic import BaseModel
from typing import List, Dict, Literal


class ScoringCriterion(BaseModel):
    name: str
    weight: float
    direction: Literal["maximize", "minimize"]
    min_value: float
    max_value: float


class RankedCandidate(BaseModel):
    id: str
    scores: Dict[str, float]
    normalized_scores: Dict[str, float]
    total_score: float
    rank: int


class RankingEngine:
    """Deterministic weighted-scoring ranker. No LLM, no randomness."""

    @staticmethod
    def rank(
        candidates: List[Dict[str, float]],
        criteria: List[ScoringCriterion],
        id_field: str = "id",
    ) -> List[RankedCandidate]:
        if not candidates or not criteria:
            return []

        ranked: List[RankedCandidate] = []
        for raw in candidates:
            cid = str(raw.get(id_field, ""))
            raw_scores: Dict[str, float] = {}
            norm_scores: Dict[str, float] = {}

            for c in criteria:
                val = raw.get(c.name, 0.0)
                raw_scores[c.name] = val
                norm_scores[c.name] = RankingEngine._normalize(val, c)

            total = sum(norm_scores[c.name] * c.weight for c in criteria)
            ranked.append(RankedCandidate(
                id=cid,
                scores=raw_scores,
                normalized_scores=norm_scores,
                total_score=round(total, 6),
                rank=0,
            ))

        RankingEngine._sort_and_rank(ranked, criteria)
        return ranked

    @staticmethod
    def _normalize(value: float, criterion: ScoringCriterion) -> float:
        rng = criterion.max_value - criterion.min_value
        if rng == 0:
            return 1.0
        normalized = (value - criterion.min_value) / rng
        normalized = max(0.0, min(1.0, normalized))
        if criterion.direction == "minimize":
            normalized = 1.0 - normalized
        return round(normalized, 6)

    @staticmethod
    def _sort_and_rank(
        ranked: List[RankedCandidate],
        criteria: List[ScoringCriterion],
    ) -> None:
        sorted_criteria = sorted(criteria, key=lambda c: c.weight, reverse=True)

        def tie_breaker(c: RankedCandidate) -> tuple:
            primary = (-c.total_score,)
            for sc in sorted_criteria:
                primary = primary + (-c.normalized_scores.get(sc.name, 0),)
            return primary

        ranked.sort(key=tie_breaker)

        for i, rc in enumerate(ranked):
            if i == 0:
                rc.rank = 1
            else:
                prev = ranked[i - 1]
                if rc.total_score == prev.total_score:
                    rc.rank = prev.rank
                else:
                    rc.rank = i + 1
