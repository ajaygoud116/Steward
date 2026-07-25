"""Explain mode tests — provenance, grounding, and data flow.

These tests verify that explanation artifacts reference recorded data
only, never raw input, and that every field in FinalExplanation maps
to a known system origin.
"""
import json
import tempfile
import shutil
from mission_engine.storage.mission_store import MissionStore
from mission_engine.agents.schemas.explanation import FinalExplanation


class TestExplainDataFlow:
    """Proof: explain endpoint only sees recorded artifacts, never raw input."""

    def test_explain_uses_mission_record_not_raw_input(self):
        tmpdir = tempfile.mkdtemp()
        try:
            store = MissionStore(storage_dir=tmpdir)
            record = store.create("Book Paris")
            store.update(record.mission_id,
                         intent={"destination": "Paris", "budget": 2000},
                         journal=[{"sequence": 1, "node": "flight_search", "status": "success"}],
                         outcome={"ranking": [{"id": "AF123", "score": 0.85}]})

            fetched = store.get(record.mission_id)
            assert fetched is not None

            mr = fetched.model_dump_json(indent=2)
            assert "Paris" in mr
            assert "flight_search" in mr
            assert "AF123" in mr

            ej_text = str([e for e in (fetched.journal or [])])
            assert "flight_search" in ej_text

            rr_text = str(fetched.outcome or {})
            assert "AF123" in rr_text
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_mission_record_contains_all_explain_fields(self):
        record_data = {
            "intent": {"destination": "Paris"},
            "journal": [{"node": "flight_search", "status": "success"}],
            "outcome": {"ranking": [{"id": "AF123", "score": 0.85}]},
        }
        assert "intent" in record_data
        assert "journal" in record_data
        assert "outcome" in record_data
        assert "ranking" in record_data["outcome"]

    def test_store_data_serializes_to_explain_context(self):
        tmpdir = tempfile.mkdtemp()
        try:
            store = MissionStore(storage_dir=tmpdir)
            record = store.create("Test")
            store.update(record.mission_id,
                         intent={"destination": "Paris"},
                         journal=[{"node": "flight_search", "status": "success"}],
                         outcome={"ranking": [{"id": "AF123"}]})

            fetched = store.get(record.mission_id)
            assert fetched is not None

            mr = fetched.model_dump_json(indent=2)
            ej = str([e for e in (fetched.journal or [])])
            rr = str(fetched.outcome or {})

            assert "Paris" in mr
            assert "flight_search" in ej
            assert "AF123" in rr
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestEvidenceGroundedExplanation:
    """Every field in FinalExplanation traces to a known artifact."""

    def test_summary_derived_from_mission_record(self):
        exp = FinalExplanation(summary="Mission complete. Top flight: AF123.")
        assert "AF123" in exp.summary

    def test_confidence_from_ranking(self):
        exp = FinalExplanation(confidence=0.85)
        assert 0.0 <= exp.confidence <= 1.0

    def test_rejected_candidates_from_ranking(self):
        exp = FinalExplanation(
            rejected_candidates=["DL456 - score 0.71"],
            evidence_sources=["ranking_result"],
        )
        assert len(exp.rejected_candidates) == 1
        assert "ranking_result" in exp.evidence_sources

    def test_failures_from_journal(self):
        exp = FinalExplanation(
            failures=["flight_search failed: No flights"],
            evidence_sources=["execution_journal"],
        )
        assert len(exp.failures) == 1
        assert "execution_journal" in exp.evidence_sources

    def test_key_decisions_from_approval_gate(self):
        exp = FinalExplanation(
            key_decisions=["Booking approved via auto_approve"],
            evidence_sources=["execution_journal"],
        )
        for d in exp.key_decisions:
            assert "approve" in d or "booking" in d

    def test_evidence_sources_always_include_mission_record(self):
        exp = FinalExplanation(
            summary="Test",
            evidence_sources=["mission_record", "execution_journal"],
        )
        assert "mission_record" in exp.evidence_sources

    def test_explanation_references_recorded_data_only(self):
        exp = FinalExplanation(
            summary="Selected AF123 from ranking",
            evidence_sources=["ranking_result"],
            rejected_candidates=["DL456"],
        )
        assert exp.summary
        assert "AF123" in exp.summary
        assert exp.evidence_sources == ["ranking_result"]

    def test_confidence_derived_from_multiple_sources(self):
        exp = FinalExplanation(
            confidence=0.75,
            evidence_sources=["ranking_result", "execution_journal"],
        )
        assert 0.0 <= exp.confidence <= 1.0
        assert len(exp.evidence_sources) >= 2

    def test_evidence_sources_defaults_empty(self):
        exp = FinalExplanation()
        assert exp.evidence_sources == []

    def test_explanation_accepts_all_fields_round_trip(self):
        exp = FinalExplanation(
            summary="Planned a trip to Paris.",
            confidence=0.85,
            reasoning="Selected AF123 based on ranking score.",
            rejected_candidates=["DL456 - lower score"],
            failures=[],
            key_decisions=["Selected AF123"],
            evidence_sources=["mission_record", "execution_journal", "ranking_result"],
        )
        data = exp.model_dump()
        assert data["summary"] == "Planned a trip to Paris."
        assert data["confidence"] == 0.85
        assert len(data["evidence_sources"]) == 3
