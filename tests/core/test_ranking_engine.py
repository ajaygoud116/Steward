from mission_engine.services.ranking import RankingEngine, ScoringCriterion


FLIGHTS = [
    {"id": "AF123", "price": 500, "duration": 420, "stops": 1},
    {"id": "DL456", "price": 650, "duration": 360, "stops": 0},
    {"id": "UA789", "price": 400, "duration": 540, "stops": 2},
    {"id": "BA321", "price": 700, "duration": 390, "stops": 0},
]

CRITERIA = [
    ScoringCriterion(name="price", weight=0.5, direction="minimize", min_value=300, max_value=800),
    ScoringCriterion(name="duration", weight=0.3, direction="minimize", min_value=300, max_value=600),
    ScoringCriterion(name="stops", weight=0.2, direction="minimize", min_value=0, max_value=3),
]


class TestRankingEngine:
    def test_rank_high_weight_dominates(self):
        price_heavy = [
            ScoringCriterion(name="price", weight=0.9, direction="minimize", min_value=300, max_value=800),
            ScoringCriterion(name="stops", weight=0.1, direction="minimize", min_value=0, max_value=3),
        ]
        results = RankingEngine.rank(FLIGHTS, price_heavy)
        cheapest = min(FLIGHTS, key=lambda f: f["price"])
        assert results[0].id == cheapest["id"]

    def test_rank_order(self):
        results = RankingEngine.rank(FLIGHTS, CRITERIA)
        scores = [r.total_score for r in results]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    def test_rank_assignments(self):
        results = RankingEngine.rank(FLIGHTS, CRITERIA)
        for r in results:
            assert r.rank >= 1
            assert len(r.scores) == 3
            assert len(r.normalized_scores) == 3
            assert all(0 <= v <= 1 for v in r.normalized_scores.values())

    def test_rank_empty_candidates(self):
        results = RankingEngine.rank([], CRITERIA)
        assert results == []

    def test_rank_empty_criteria(self):
        results = RankingEngine.rank(FLIGHTS, [])
        assert results == []


class TestNormalization:
    def test_maximize_direction(self):
        criterion = ScoringCriterion(name="score", weight=1.0, direction="maximize", min_value=0, max_value=100)
        assert RankingEngine._normalize(80, criterion) == 0.8
        assert RankingEngine._normalize(0, criterion) == 0.0
        assert RankingEngine._normalize(100, criterion) == 1.0

    def test_minimize_direction(self):
        criterion = ScoringCriterion(name="price", weight=1.0, direction="minimize", min_value=0, max_value=100)
        assert RankingEngine._normalize(20, criterion) == 0.8
        assert RankingEngine._normalize(0, criterion) == 1.0
        assert RankingEngine._normalize(100, criterion) == 0.0

    def test_clamps_out_of_range(self):
        criterion = ScoringCriterion(name="score", weight=1.0, direction="maximize", min_value=0, max_value=100)
        assert RankingEngine._normalize(-10, criterion) == 0.0
        assert RankingEngine._normalize(200, criterion) == 1.0

    def test_zero_range(self):
        criterion = ScoringCriterion(name="fixed", weight=1.0, direction="maximize", min_value=50, max_value=50)
        assert RankingEngine._normalize(50, criterion) == 1.0
        assert RankingEngine._normalize(999, criterion) == 1.0


class TestTieBreaking:
    def test_ties_get_same_rank(self):
        candidates = [
            {"id": "A", "price": 500, "rating": 4.0},
            {"id": "B", "price": 500, "rating": 4.0},
        ]
        crit = [
            ScoringCriterion(name="price", weight=0.6, direction="minimize", min_value=0, max_value=1000),
            ScoringCriterion(name="rating", weight=0.4, direction="maximize", min_value=1, max_value=5),
        ]
        results = RankingEngine.rank(candidates, crit)

        assert results[0].rank == 1
        assert results[1].rank == 1
        assert results[0].total_score == results[1].total_score

    def test_tie_breaker_uses_weight_priority(self):
        candidates = [
            {"id": "A", "price": 500, "rating": 4.0},
            {"id": "B", "price": 500, "rating": 4.5},
        ]
        crit = [
            ScoringCriterion(name="price", weight=0.7, direction="minimize", min_value=0, max_value=1000),
            ScoringCriterion(name="rating", weight=0.3, direction="maximize", min_value=1, max_value=5),
        ]
        results = RankingEngine.rank(candidates, crit)

        assert results[0].id == "B"
        assert results[1].id == "A"


class TestDeterminism:
    def test_same_input_same_output(self):
        first = RankingEngine.rank(FLIGHTS, CRITERIA)
        for _ in range(10):
            again = RankingEngine.rank(FLIGHTS, CRITERIA)
            for a, b in zip(first, again):
                assert a.id == b.id
                assert a.total_score == b.total_score
                assert a.rank == b.rank
                assert a.normalized_scores == b.normalized_scores


class TestWeightedScore:
    def test_all_criteria_contribute(self):
        crit = [
            ScoringCriterion(name="price", weight=0.5, direction="minimize", min_value=0, max_value=1000),
            ScoringCriterion(name="comfort", weight=0.5, direction="maximize", min_value=1, max_value=10),
        ]
        cheap_comfortable = {"id": "X", "price": 200, "comfort": 9}
        expensive_uncomfortable = {"id": "Y", "price": 900, "comfort": 2}

        results = RankingEngine.rank([cheap_comfortable, expensive_uncomfortable], crit)
        assert results[0].id == "X"

        cheap_uncomfortable = {"id": "X", "price": 200, "comfort": 2}
        expensive_comfortable = {"id": "Y", "price": 900, "comfort": 9}
        results = RankingEngine.rank([cheap_uncomfortable, expensive_comfortable], crit)
        assert results[0].id == "Y"
        assert results[0].total_score > results[1].total_score
