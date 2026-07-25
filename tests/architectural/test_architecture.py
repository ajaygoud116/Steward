"""Architectural constraint tests — enforce separation of concerns."""

import importlib
import inspect
import re


class TestEngineHasNoTravelAssumptions:
    """MissionRuntime and core engine must NOT reference travel concepts."""

    FORBIDDEN_TERMS = [
        "destination", "airport", "hotel", "flight", "weather",
        "TravelIntent", "TravelPlan", "FlightOption",
        "HotelOption", "travel_constraints", "travel_ranking",
        "travel_memory", "travel_validation",
        "ToolExecutor", "RankingCriteria",
        "TravelWorkflow",
    ]

    def _get_source(self, module_name: str) -> str:
        mod = importlib.import_module(module_name)
        return inspect.getsource(mod)

    def test_runtime_no_travel_imports(self):
        source = self._get_source("mission_engine.core.runtime")
        for term in self.FORBIDDEN_TERMS:
            assert term not in source, (
                f"Runtime must not reference '{term}'"
            )

    def test_mission_context_no_travel(self):
        source = self._get_source("mission_engine.core.mission_context")
        for term in self.FORBIDDEN_TERMS:
            if term == "travel_":
                continue
            assert term not in source

    def test_evidence_envelope_no_travel(self):
        source = self._get_source("mission_engine.core.evidence")
        travel_terms = [t for t in self.FORBIDDEN_TERMS
                        if t not in ("booking",)]
        for term in travel_terms:
            assert term not in source

    def test_workflow_contract_no_travel(self):
        source = self._get_source("mission_engine.core.workflow")
        for term in self.FORBIDDEN_TERMS:
            if term == "travel_":
                continue
            assert term not in source

    def test_workflow_registry_no_travel(self):
        source = self._get_source("mission_engine.core.workflow_registry")
        for term in self.FORBIDDEN_TERMS:
            if term == "travel_":
                continue
            assert term not in source


class TestMissionWorkflowContract:
    """Verify the MissionWorkflow contract exists and is enforced."""

    def test_mission_workflow_is_abstract(self):
        from mission_engine.core.workflow import MissionWorkflow
        assert inspect.isabstract(MissionWorkflow)
        assert MissionWorkflow.workflow_type == ""

    def test_all_abstract_methods_defined(self):
        from mission_engine.core.workflow import MissionWorkflow
        methods = [
            "interpret", "validate_intent", "build_plan",
            "execute_step", "process_results", "book", "summarize",
        ]
        for m in methods:
            assert hasattr(MissionWorkflow, m), f"Missing abstract method: {m}"
            assert getattr(MissionWorkflow, m).__isabstractmethod__, (
                f"{m} must be abstract"
            )

    def test_travel_workflow_implements_contract(self):
        from mission_engine.core.workflow import MissionWorkflow
        from mission_engine.workflows.travel.workflow import TravelWorkflow
        assert issubclass(TravelWorkflow, MissionWorkflow)
        assert TravelWorkflow.workflow_type == "travel"
        # Instantiation should not raise (all abstract methods implemented)
        instance = TravelWorkflow()
        for m in ["interpret", "validate_intent", "build_plan",
                   "execute_step", "process_results", "book", "summarize"]:
            assert hasattr(instance, m)
            assert callable(getattr(instance, m))


class TestWorkflowRegistry:
    """Verify the registry resolves workflows correctly."""

    def test_registry_resolves_travel(self):
        from mission_engine.core.workflow_registry import WorkflowRegistry
        from mission_engine.workflows.travel.workflow import TravelWorkflow
        resolved = WorkflowRegistry.get("travel")
        assert resolved is TravelWorkflow

    def test_registry_unknown_raises(self):
        from mission_engine.core.workflow_registry import WorkflowRegistry
        import pytest
        with pytest.raises(KeyError):
            WorkflowRegistry.get("nonexistent")

    def test_registry_list_types(self):
        from mission_engine.core.workflow_registry import WorkflowRegistry
        types = WorkflowRegistry.list_types()
        assert "travel" in types
        assert len(types) == 1  # only travel should exist

    def test_engine_imports_workflow_not_travel(self):
        """MissionRuntime imports MissionWorkflow, never TravelWorkflow."""
        source = inspect.getsource(
            importlib.import_module("mission_engine.core.runtime")
        )
        assert "MissionWorkflow" in source
        assert "TravelWorkflow" not in source


class TestDependencyDirection:
    """Verify one-directional dependency: Engine → Workflow → Services."""

    def test_core_modules_dont_import_workflows(self):
        core_modules = [
            "mission_engine.core.mission_context",
            "mission_engine.core.evidence",
        ]
        for mod_name in core_modules:
            mod = importlib.import_module(mod_name)
            source = inspect.getsource(mod)
            assert "workflows" not in source, (
                f"{mod_name} must not import from workflows"
            )

    def test_no_circular_imports(self):
        """All modules should load without circular import errors."""
        modules = [
            "mission_engine.core.workflow",
            "mission_engine.core.workflow_registry",
            "mission_engine.core.mission_context",
            "mission_engine.core.evidence",
            "mission_engine.core.runtime",
            "mission_engine.workflows.travel.intent_schema",
            "mission_engine.workflows.travel.plan_schema",
            "mission_engine.workflows.travel.adapters",
            "mission_engine.workflows.travel.workflow",
            "mission_engine.superflow.flow",
        ]
        for mod in modules:
            importlib.import_module(mod)
