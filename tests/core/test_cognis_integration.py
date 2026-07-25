"""Integration: preferences flow through SuperFlow pipeline correctly.

These tests verify that stored preferences are loaded before execution,
condition the intent interpretation (when studio available), and survive
the full SuperFlow pipeline.  They complement (do not duplicate) the
unit tests in test_memory_pipeline.py.
"""
from mission_engine.superflow.flow import TravelSuperFlow
from mission_engine.memory.preference_store import PreferenceStore
from mission_engine.memory.policy import CandidatePreference
import tempfile
import shutil


class TestPreferenceInSuperFlow:
    """Preferences stored before run() are available in cognis_preferences."""

    def test_preference_appears_in_cognis(self):
        tmpdir = tempfile.mkdtemp()
        try:
            ps = PreferenceStore(storage_dir=tmpdir)
            ps.store("anna", CandidatePreference(
                preference="always prefers aisle seats", category="seat", confidence=0.9))
            flow = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            result = flow.run("Book a flight", user_id="anna")
            assert "aisle" in result.cognis_preferences
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_no_preferences_returns_none_text(self):
        tmpdir = tempfile.mkdtemp()
        try:
            flow = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            result = flow.run("Book a flight", user_id="new_user")
            assert result.cognis_preferences == "None"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_preferences_not_leaked_between_users(self):
        tmpdir = tempfile.mkdtemp()
        try:
            ps = PreferenceStore(storage_dir=tmpdir)
            ps.store("alice", CandidatePreference(
                preference="prefers window seats", category="seat"))
            ps.store("bob", CandidatePreference(
                preference="prefers hotels with gym", category="hotel"))
            flow = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            r1 = flow.run("Trip", user_id="alice")
            r2 = flow.run("Trip", user_id="bob")
            assert "window" in r1.cognis_preferences
            assert "window" not in r2.cognis_preferences
            assert "gym" in r2.cognis_preferences
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_preferences_survive_superflow_execution(self):
        tmpdir = tempfile.mkdtemp()
        try:
            ps = PreferenceStore(storage_dir=tmpdir)
            ps.store("charlie", CandidatePreference(
                preference="always prefers aisle seats", category="seat", confidence=0.9))
            flow = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            flow.run("Paris trip", user_id="charlie")
            flow2 = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            r2 = flow2.run("Another trip", user_id="charlie")
            assert "aisle" in r2.cognis_preferences
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_journal_records_cognis_retrieval(self):
        tmpdir = tempfile.mkdtemp()
        try:
            ps = PreferenceStore(storage_dir=tmpdir)
            ps.store("dave", CandidatePreference(
                preference="prefers window seats", category="seat"))
            flow = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            result = flow.run("London trip", user_id="dave")
            cognis_entry = [e for e in result.journal if e["node"] == "retrieve_cognis"]
            assert len(cognis_entry) == 1
            assert cognis_entry[0]["status"] == "success"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_multiple_preferences_merged_in_cognis(self):
        tmpdir = tempfile.mkdtemp()
        try:
            ps = PreferenceStore(storage_dir=tmpdir)
            ps.store("eve", CandidatePreference(
                preference="prefers window seats", category="seat"))
            ps.store("eve", CandidatePreference(
                preference="prefers hotels with free breakfast", category="hotel"))
            flow = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            result = flow.run("Paris", user_id="eve")
            assert "window" in result.cognis_preferences
            assert "breakfast" in result.cognis_preferences
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_cognis_retrieved_before_any_step_result(self):
        tmpdir = tempfile.mkdtemp()
        try:
            flow = TravelSuperFlow(studio=None, pref_store=PreferenceStore(storage_dir=tmpdir))
            result = flow.run("Tokyo", user_id="frank")
            assert len(result.journal) > 0
            assert result.journal[0]["node"] == "retrieve_cognis"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
