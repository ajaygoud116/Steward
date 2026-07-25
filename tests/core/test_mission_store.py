import json
import tempfile
import shutil
from pathlib import Path
from mission_engine.storage.mission_store import MissionStore, MissionRecord


class TestMissionStore:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = MissionStore(storage_dir=self.tmpdir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


class TestCreateAndGet(TestMissionStore):
    def test_create_returns_record_with_id(self):
        record = self.store.create("Paris trip")
        assert record.mission_id
        assert record.user_input == "Paris trip"
        assert record.status == "created"
        assert record.created_at
        assert record.updated_at

    def test_get_returns_none_for_missing(self):
        assert self.store.get("nonexistent") is None

    def test_get_returns_saved_record(self):
        created = self.store.create("London")
        fetched = self.store.get(created.mission_id)
        assert fetched is not None
        assert fetched.mission_id == created.mission_id
        assert fetched.user_input == "London"


class TestUpdate(TestMissionStore):
    def test_update_intent(self):
        record = self.store.create("Paris")
        updated = self.store.update(record.mission_id, intent={"destination": "Paris"})
        assert updated is not None
        assert updated.intent == {"destination": "Paris"}
        assert updated.updated_at != record.updated_at

    def test_update_full_pipeline(self):
        record = self.store.create("Paris")
        self.store.update(record.mission_id, status="planning")
        self.store.update(record.mission_id, execution_plan={"workflow": "travel"})
        self.store.update(record.mission_id, journal=[{"step": "flight_search", "status": "ok"}])
        self.store.update(record.mission_id, outcome={"ranking": []})
        self.store.update(record.mission_id, status="completed")

        final = self.store.get(record.mission_id)
        assert final is not None
        assert final.status == "completed"
        assert final.execution_plan == {"workflow": "travel"}
        assert len(final.journal) == 1
        assert final.outcome == {"ranking": []}


class TestListAndDelete(TestMissionStore):
    def test_list_all_empty(self):
        assert self.store.list_all() == []

    def test_list_all_returns_all(self):
        self.store.create("Paris")
        self.store.create("London")
        self.store.create("Tokyo")
        assert len(self.store.list_all()) == 3

    def test_delete_removes_record(self):
        record = self.store.create("Paris")
        assert self.store.get(record.mission_id) is not None
        assert self.store.delete(record.mission_id) is True
        assert self.store.get(record.mission_id) is None

    def test_delete_nonexistent_returns_false(self):
        assert self.store.delete("nonexistent") is False


class TestSurvivesRestart(TestMissionStore):
    def test_mission_survives_new_store_instance(self):
        record = self.store.create("Paris")
        self.store.update(record.mission_id,
                          intent={"destination": "Paris", "budget": 2000},
                          status="completed",
                          outcome={"ranking": [{"id": "AF123", "score": 0.9}]})

        new_store = MissionStore(storage_dir=self.tmpdir)
        restored = new_store.get(record.mission_id)
        assert restored is not None
        assert restored.user_input == "Paris"
        assert restored.intent == {"destination": "Paris", "budget": 2000}
        assert restored.status == "completed"
        assert restored.outcome == {"ranking": [{"id": "AF123", "score": 0.9}]}

    def test_all_missions_survive_restart(self):
        ids = []
        for city in ["Paris", "London", "Tokyo"]:
            r = self.store.create(city)
            ids.append(r.mission_id)

        new_store = MissionStore(storage_dir=self.tmpdir)
        restored = new_store.list_all()
        assert len(restored) == 3
        restored_ids = [r.mission_id for r in restored]
        for mid in ids:
            assert mid in restored_ids


class TestSave(TestMissionStore):
    def test_save_replaces_existing(self):
        record = self.store.create("Paris")
        record.status = "completed"
        record.outcome = {"result": "ok"}
        self.store.save(record)

        fetched = self.store.get(record.mission_id)
        assert fetched is not None
        assert fetched.status == "completed"
        assert fetched.outcome == {"result": "ok"}

    def test_save_updates_timestamp(self):
        record = self.store.create("Paris")
        original = record.updated_at
        record.status = "completed"
        self.store.save(record)
        assert record.updated_at != original


class TestCorruptedData(TestMissionStore):
    def test_corrupted_json_returns_none(self):
        record = self.store.create("Paris")
        path = Path(self.tmpdir) / f"{record.mission_id}.json"
        path.write_text("{invalid json!!!}", encoding="utf-8")
        assert self.store.get(record.mission_id) is None

    def test_empty_file_returns_none(self):
        record = self.store.create("Paris")
        path = Path(self.tmpdir) / f"{record.mission_id}.json"
        path.write_text("", encoding="utf-8")
        assert self.store.get(record.mission_id) is None

    def test_partial_write_does_not_corrupt(self):
        record = self.store.create("Paris")
        mid = record.mission_id
        self.store.update(mid, status="completed", intent={"destination": "Paris"})
        path = Path(self.tmpdir) / f"{mid}.json"
        content = path.read_text(encoding="utf-8")
        assert json.loads(content)["status"] == "completed"
        assert json.loads(content)["intent"]["destination"] == "Paris"

    def test_missing_fields_default_gracefully(self):
        mid = "test-missing-fields"
        path = Path(self.tmpdir) / f"{mid}.json"
        path.write_text(json.dumps({"mission_id": mid}), encoding="utf-8")
        fetched = self.store.get(mid)
        assert fetched is not None
        assert fetched.mission_id == mid
        assert fetched.status == "created"
        assert fetched.user_input == ""

    def test_corrupted_file_skipped_in_list(self):
        self.store.create("Paris")
        bad_path = Path(self.tmpdir) / "corrupted.json"
        bad_path.write_text("{bad", encoding="utf-8")
        missions = self.store.list_all()
        assert len(missions) == 1
        assert missions[0].user_input == "Paris"

    def test_empty_file_skipped_in_list(self):
        self.store.create("London")
        empty_path = Path(self.tmpdir) / "empty.json"
        empty_path.write_text("", encoding="utf-8")
        missions = self.store.list_all()
        assert len(missions) == 1
        assert missions[0].user_input == "London"
