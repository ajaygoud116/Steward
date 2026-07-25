import tempfile
import shutil
from mission_engine.storage.mission_store import MissionStore
from mission_engine.services.execution_journal import ExecutionJournal, JournalEntry


class TestExecutionJournal:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = MissionStore(storage_dir=self.tmpdir)
        self.mission = self.store.create("Paris trip")
        self.journal = ExecutionJournal(self.store, self.mission.mission_id)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


class TestAppend(TestExecutionJournal):
    def test_append_returns_entry(self):
        entry = self.journal.append("interpret", "success", summary="Extracted intent")
        assert isinstance(entry, JournalEntry)
        assert entry.sequence == 1
        assert entry.node == "interpret"
        assert entry.status == "success"
        assert entry.summary == "Extracted intent"
        assert entry.timestamp

    def test_second_entry_auto_increments(self):
        self.journal.append("interpret", "success")
        entry = self.journal.append("plan", "success")
        assert entry.sequence == 2
        assert entry.node == "plan"

    def test_append_with_data_and_error(self):
        entry = self.journal.append(
            "flight_search",
            "failed",
            summary="No flights found",
            data={"destination": "Paris"},
            error="API returned 404",
        )
        assert entry.data == {"destination": "Paris"}
        assert entry.error == "API returned 404"


class TestAppendOnly(TestExecutionJournal):
    def test_entries_is_list(self):
        assert self.journal.entries() == []

    def test_entries_returns_all_appended(self):
        self.journal.append("interpret", "success")
        self.journal.append("plan", "success")
        self.journal.append("flight_search", "success")
        entries = self.journal.entries()
        assert len(entries) == 3
        for i, e in enumerate(entries):
            assert e.sequence == i + 1

    def test_cannot_modify_entry(self):
        self.journal.append("interpret", "success", data={"original": True})
        entries = self.journal.entries()
        entry = entries[0]
        entry.data = {"modified": True}
        entries2 = self.journal.entries()
        assert entries2[0].data == {"original": True}


class TestTimelineReconstructsExecution(TestExecutionJournal):
    def test_full_execution_timeline(self):
        self.journal.append("interpret", "success", summary="Extracted Paris, budget 2000")
        self.journal.append("plan", "success", summary="Created 3-task execution plan")
        self.journal.append("flight_search", "success", summary="Found 5 flights", data={"count": 5})
        self.journal.append("hotel_search", "success", summary="Found 5 hotels", data={"count": 5})
        self.journal.append("weather_check", "success", summary="Forecast: sunny")
        self.journal.append("validate", "success", summary="All outputs valid")
        self.journal.append("rank", "success", summary="Top flight: AF123", data={"top_score": 0.85})
        self.journal.append("complete", "success", summary="Mission complete")

        timeline = self.journal.timeline()
        assert len(timeline) == 8

        expected_nodes = [
            "interpret", "plan", "flight_search", "hotel_search",
            "weather_check", "validate", "rank", "complete",
        ]
        for i, entry in enumerate(timeline):
            assert entry.sequence == i + 1
            assert entry.node == expected_nodes[i]
            assert entry.status == "success"
            assert entry.timestamp

    def test_timeline_with_failures(self):
        self.journal.append("interpret", "success")
        self.journal.append("plan", "success")
        self.journal.append("flight_search", "failed", error="No flights", data={"tried": "direct"})
        self.journal.append("replan", "success", summary="Relaxed constraints")
        self.journal.append("flight_search", "success", summary="Found flights on retry")
        self.journal.append("rank", "success")

        timeline = self.journal.timeline()
        assert len(timeline) == 6
        assert timeline[2].node == "flight_search"
        assert timeline[2].status == "failed"
        assert timeline[2].error == "No flights"
        assert timeline[3].node == "replan"
        assert timeline[4].node == "flight_search"
        assert timeline[4].status == "success"

    def test_reconstruct_returns_nodes_grouped(self):
        self.journal.append("interpret", "success")
        self.journal.append("plan", "success")
        self.journal.append("flight_search", "success")

        state = self.journal.reconstruct()
        assert state["mission_id"] == self.mission.mission_id
        assert state["total_entries"] == 3
        assert "interpret" in state["nodes"]
        assert "plan" in state["nodes"]
        assert "flight_search" in state["nodes"]
        assert state["last_status"] == "success"


class TestPersistsWithMission(TestExecutionJournal):
    def test_journal_survives_store_reload(self):
        self.journal.append("interpret", "success", summary="Extracted intent")
        self.journal.append("plan", "success", summary="Created plan")

        new_store = MissionStore(storage_dir=self.tmpdir)
        new_journal = ExecutionJournal(new_store, self.mission.mission_id)
        entries = new_journal.entries()
        assert len(entries) == 2
        assert entries[0].node == "interpret"
        assert entries[1].node == "plan"

    def test_journal_appends_across_instances(self):
        self.journal.append("interpret", "success")

        new_journal = ExecutionJournal(self.store, self.mission.mission_id)
        new_journal.append("plan", "success")

        entries = self.journal.entries()
        assert len(entries) == 2
        assert entries[0].node == "interpret"
        assert entries[1].node == "plan"
        assert entries[1].sequence == 2
