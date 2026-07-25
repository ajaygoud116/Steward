import tempfile
import shutil
from mission_engine.memory.policy import MemoryPolicy, CandidatePreference
from mission_engine.memory.preference_store import PreferenceStore
from mission_engine.memory.pipeline import MemoryPipeline


class TestMemoryPolicy:
    def test_eligible_window_seats(self):
        cand = CandidatePreference(
            preference="I always prefer window seats",
            category="seat",
            confidence=0.9,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is True

    def test_eligible_aisle_seats(self):
        cand = CandidatePreference(
            preference="I usually prefer aisle seats",
            category="seat",
            confidence=0.8,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is True

    def test_rejected_booked_paris(self):
        cand = CandidatePreference(
            preference="I booked Paris",
            category="general",
            confidence=0.7,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is False
        assert "transient" in reason.lower() or "preference" in reason.lower()

    def test_rejected_low_confidence(self):
        cand = CandidatePreference(
            preference="I prefer window seats",
            category="seat",
            confidence=0.3,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is False
        assert "confidence" in reason.lower()

    def test_rejected_transient_price(self):
        cand = CandidatePreference(
            preference="The price was too high",
            category="general",
            confidence=0.9,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is False

    def test_rejected_short_preference(self):
        cand = CandidatePreference(
            preference="OK",
            category="general",
            confidence=0.9,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is False

    def test_eligible_hotel_preference(self):
        cand = CandidatePreference(
            preference="I always prefer hotels with free breakfast",
            category="hotel",
            confidence=0.85,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is True

    def test_rejected_invalid_category(self):
        cand = CandidatePreference(
            preference="I always prefer window seats",
            category="weather",
            confidence=0.9,
        )
        eligible, reason = MemoryPolicy.is_eligible(cand)
        assert eligible is False
        assert "category" in reason.lower()


class TestPreferenceStore:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = PreferenceStore(storage_dir=self.tmpdir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_store_and_retrieve(self):
        pref = CandidatePreference(preference="I prefer window seats", category="seat")
        self.store.store("user1", pref)
        prefs = self.store.get_all("user1")
        assert len(prefs) == 1
        assert prefs[0].preference == "I prefer window seats"

    def test_as_text_empty(self):
        assert self.store.as_text("user1") == "None"

    def test_as_text_with_preferences(self):
        self.store.store("user1", CandidatePreference(preference="window seats", category="seat"))
        self.store.store("user1", CandidatePreference(preference="aisle seats", category="seat"))
        text = self.store.as_text("user1")
        assert "window seats" in text
        assert "aisle seats" in text

    def test_multiple_users_isolated(self):
        self.store.store("user1", CandidatePreference(preference="window seats", category="seat"))
        self.store.store("user2", CandidatePreference(preference="aisle seats", category="seat"))
        assert len(self.store.get_all("user1")) == 1
        assert len(self.store.get_all("user2")) == 1

    def test_survives_store_reload(self):
        self.store.store("user1", CandidatePreference(preference="window seats", category="seat"))
        new_store = PreferenceStore(storage_dir=self.tmpdir)
        prefs = new_store.get_all("user1")
        assert len(prefs) == 1
        assert prefs[0].preference == "window seats"


class TestMemoryPipelineNoStudio:
    def test_pipeline_no_studio_returns_empty(self):
        pipeline = MemoryPipeline(studio=None)
        result = pipeline.process("I always prefer window seats", user_id="test")
        assert result["candidates_extracted"] == []
        assert result["eligible"] == []
        assert result["rejected"] == []

    def test_store_survives_restart(self):
        tmpdir = tempfile.mkdtemp()
        try:
            store = PreferenceStore(storage_dir=tmpdir)
            store.store("survive", CandidatePreference(preference="window seats", category="seat"))
            store2 = PreferenceStore(storage_dir=tmpdir)
            prefs = store2.get_all("survive")
            assert len(prefs) == 1
            assert prefs[0].preference == "window seats"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
