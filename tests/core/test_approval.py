import tempfile
import shutil
import pytest
from mission_engine.models.core import MissionStatus
from mission_engine.storage.mission_store import MissionStore
from mission_engine.services.approval import ApprovalGate


# ── State machine definition ──────────────────────────────────────────
# CREATED
#   → WAITING_INFORMATION
#   → READY
# WAITING_INFORMATION
#   → READY
#   → FAILED
# READY
#   → RUNNING
#   → FAILED
# RUNNING
#   → WAITING_APPROVAL
#   → FAILED
# WAITING_APPROVAL
#   → BOOKED          (via book())
#   → FAILED
# BOOKED
#   → COMPLETED
#   → FAILED
# COMPLETED → ∅
# FAILED → ∅

_ALL_STATES = [
    MissionStatus.CREATED,
    MissionStatus.WAITING_INFORMATION,
    MissionStatus.READY,
    MissionStatus.RUNNING,
    MissionStatus.WAITING_APPROVAL,
    MissionStatus.BOOKED,
    MissionStatus.COMPLETED,
    MissionStatus.FAILED,
]

_ALLOWED = {
    (MissionStatus.CREATED, MissionStatus.WAITING_INFORMATION),
    (MissionStatus.CREATED, MissionStatus.READY),
    (MissionStatus.WAITING_INFORMATION, MissionStatus.READY),
    (MissionStatus.WAITING_INFORMATION, MissionStatus.FAILED),
    (MissionStatus.READY, MissionStatus.RUNNING),
    (MissionStatus.READY, MissionStatus.FAILED),
    (MissionStatus.RUNNING, MissionStatus.WAITING_APPROVAL),
    (MissionStatus.RUNNING, MissionStatus.FAILED),
    (MissionStatus.WAITING_APPROVAL, MissionStatus.BOOKED),
    (MissionStatus.WAITING_APPROVAL, MissionStatus.FAILED),
    (MissionStatus.BOOKED, MissionStatus.COMPLETED),
    (MissionStatus.BOOKED, MissionStatus.FAILED),
}

# All other pairs must be rejected
_FORBIDDEN = {
    (f, t)
    for f in _ALL_STATES
    for t in _ALL_STATES
    if f != t and (f, t) not in _ALLOWED
}


# ── Helpers ────────────────────────────────────────────────────────────

ALL_TRANSITIONS = len(_ALLOWED) + len(_FORBIDDEN)  # total = 56


def _transition_fn(gate, to: MissionStatus):
    """Return the ApprovalGate method that transitions *to* the given status.
    CREATED has no public method (you cannot transition *to* CREATED).
    """
    if to is MissionStatus.CREATED:
        return lambda mid: {"ok": False, "error": "Cannot transition to created"}
    mapping = {
        MissionStatus.WAITING_INFORMATION: gate.mark_waiting_information,
        MissionStatus.READY: gate.mark_ready,
        MissionStatus.RUNNING: gate.mark_running,
        MissionStatus.WAITING_APPROVAL: gate.request_approval,
        MissionStatus.BOOKED: gate.book,
        MissionStatus.COMPLETED: gate.complete,
        MissionStatus.FAILED: gate.fail,
    }
    return mapping[to]


# ── Fixture ────────────────────────────────────────────────────────────

class ApprovalFixture:
    """One mission, shared across tests in a class."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = MissionStore(storage_dir=self.tmpdir)
        self.gate = ApprovalGate(self.store)
        self.mission = self.store.create("Paris trip")
        self.mid = self.mission.mission_id

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def put_in_state(self, status: MissionStatus):
        """Drive the state machine into *status* using public methods only."""
        s = MissionStatus
        if status == s.CREATED:
            return
        path = {
            s.WAITING_INFORMATION: [s.WAITING_INFORMATION],
            s.READY: [s.READY],
            s.RUNNING: [s.READY, s.RUNNING],
            s.WAITING_APPROVAL: [s.READY, s.RUNNING, s.WAITING_APPROVAL],
            s.BOOKED: [s.READY, s.RUNNING, s.WAITING_APPROVAL, s.BOOKED],
            s.COMPLETED: [s.READY, s.RUNNING, s.WAITING_APPROVAL, s.BOOKED, s.COMPLETED],
            s.FAILED: [s.READY, s.FAILED],
        }[status]
        for step in path:
            r = _transition_fn(self.gate, step)(self.mid)
            assert r["ok"] is True, f"put_in_state({status}) failed at step {step}: {r}"


# ── Every possible transition ─────────────────────────────────────────

class TestEveryTransition(ApprovalFixture):
    """One test per (from, to) pair — 56 total."""

    @pytest.mark.parametrize("from_s", _ALL_STATES, ids=lambda s: s.value)
    @pytest.mark.parametrize("to_s", _ALL_STATES, ids=lambda s: s.value)
    def test_transition(self, from_s, to_s):
        if from_s is to_s:
            return  # self-transitions are not tested (no public method stays in place)
        self.put_in_state(from_s)
        r = _transition_fn(self.gate, to_s)(self.mid)
        expected_ok = (from_s, to_s) in _ALLOWED
        assert r["ok"] is expected_ok, (
            f"Transition {from_s.value} → {to_s.value}: "
            f"expected ok={expected_ok}, got {r}"
        )
        if expected_ok:
            assert r["from"] == from_s.value
            assert r["to"] == to_s.value


# ── Professor's two specific questions ─────────────────────────────────

class TestProfessorQuestions(ApprovalFixture):

    def test_READY_cannot_skip_to_COMPLETED(self):
        """Professor: Can READY → COMPLETED happen?  Shouldn't."""
        self.put_in_state(MissionStatus.READY)
        r = self.gate.complete(self.mid)
        assert r["ok"] is False, f"READY→COMPLETED should be forbidden: {r}"
        assert "transition" in r["error"].lower()

    def test_FAILED_cannot_recover_to_BOOKED(self):
        """Professor: Can FAILED → BOOKED happen?  Shouldn't."""
        self.put_in_state(MissionStatus.FAILED)
        r = self.gate.book(self.mid)
        assert r["ok"] is False, f"FAILED→BOOKED should be forbidden: {r}"
        assert "waiting" in r["error"].lower() or "transition" in r["error"].lower()

    def test_FAILED_is_terminal_no_transitions_out(self):
        """FAILED is a sink — nothing allowed out."""
        self.put_in_state(MissionStatus.FAILED)
        for to in _ALL_STATES:
            if to is MissionStatus.FAILED:
                continue
            r = _transition_fn(self.gate, to)(self.mid)
            assert r["ok"] is False, f"FAILED→{to.value} should be forbidden: {r}"

    def test_COMPLETED_is_terminal_no_transitions_out(self):
        """COMPLETED is a sink — nothing allowed out."""
        self.put_in_state(MissionStatus.COMPLETED)
        for to in _ALL_STATES:
            if to is MissionStatus.COMPLETED:
                continue
            r = _transition_fn(self.gate, to)(self.mid)
            assert r["ok"] is False, f"COMPLETED→{to.value} should be forbidden: {r}"


# ── Existing flow tests (preserved) ────────────────────────────────────

class TestFullApprovalFlow(ApprovalFixture):
    def test_full_flow(self):
        assert self.gate.mark_ready(self.mid)["ok"] is True
        assert self.gate.mark_running(self.mid)["ok"] is True
        assert self.gate.request_approval(self.mid)["ok"] is True
        assert self.gate.book(self.mid)["ok"] is True
        assert self.gate.complete(self.mid)["ok"] is True

    def test_can_book_only_when_waiting_approval(self):
        assert self.gate.can_book(self.mid) is False
        self.gate.mark_ready(self.mid)
        assert self.gate.can_book(self.mid) is False
        self.gate.mark_running(self.mid)
        assert self.gate.can_book(self.mid) is False
        self.gate.request_approval(self.mid)
        assert self.gate.can_book(self.mid) is True


class TestNoApprovalNoBooking(ApprovalFixture):
    def test_book_without_any_approval_fails(self):
        r = self.gate.book(self.mid)
        assert r["ok"] is False

    def test_book_before_waiting_fails(self):
        self.gate.mark_ready(self.mid)
        self.gate.mark_running(self.mid)
        r = self.gate.book(self.mid)
        assert r["ok"] is False

    def test_cannot_book_twice(self):
        self.put_in_state(MissionStatus.WAITING_APPROVAL)
        assert self.gate.book(self.mid)["ok"] is True
        r = self.gate.book(self.mid)
        assert r["ok"] is False


class TestInvalidTransitions(ApprovalFixture):
    def test_cannot_mark_running_from_created(self):
        r = self.gate.mark_running(self.mid)
        assert r["ok"] is False

    def test_cannot_book_from_ready(self):
        self.gate.mark_ready(self.mid)
        r = self.gate.book(self.mid)
        assert r["ok"] is False

    def test_cannot_complete_without_book(self):
        r = self.gate.complete(self.mid)
        assert r["ok"] is False

    def test_cannot_go_back(self):
        self.gate.mark_ready(self.mid)
        r = self.gate.mark_running(self.mid)
        assert r["ok"] is True
        r = self.gate.mark_ready(self.mid)
        assert r["ok"] is False


class TestFailurePath(ApprovalFixture):
    def test_fail_from_running(self):
        self.gate.mark_ready(self.mid)
        self.gate.mark_running(self.mid)
        r = self.gate.fail(self.mid)
        assert r["ok"] is True
        assert r["to"] == "failed"

    def test_fail_from_waiting_approval(self):
        self.put_in_state(MissionStatus.WAITING_APPROVAL)
        r = self.gate.fail(self.mid)
        assert r["ok"] is True


class TestStatusTracking(ApprovalFixture):
    def test_status_updates(self):
        assert self.gate.get_status(self.mid) == "created"
        self.gate.mark_ready(self.mid)
        assert self.gate.get_status(self.mid) == "ready"
        self.gate.mark_running(self.mid)
        assert self.gate.get_status(self.mid) == "running"
        self.gate.request_approval(self.mid)
        assert self.gate.get_status(self.mid) == "waiting_approval"
        self.gate.book(self.mid)
        assert self.gate.get_status(self.mid) == "booked"
        self.gate.complete(self.mid)
        assert self.gate.get_status(self.mid) == "completed"

    def test_status_persists(self):
        self.put_in_state(MissionStatus.BOOKED)
        new_gate = ApprovalGate(MissionStore(storage_dir=self.tmpdir))
        assert new_gate.get_status(self.mid) == "booked"

    def test_missing_mission(self):
        assert self.gate.can_book("nonexistent") is False
        assert self.gate.get_status("nonexistent") is None
