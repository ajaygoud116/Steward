# Runtime Behavior

## Request Lifecycle

```
User sends natural language request
  → Manager Agent extracts structured intent (AI)
  → Intent validated for completeness
  → Execution plan built (AI-assisted)
  → MissionRuntime executes plan deterministically
  → Tools called, results validated, candidates filtered
  → Candidates ranked by weighted criteria
  → Approval gate enforces state machine
  → Booking executed through workflow domain logic
  → Mission record persisted to store
  → Manager Agent generates explanation grounded in evidence
  → Response returned
```

## State Machine

The approval gate has 7 states:

```
CREATED → READY → RUNNING → WAITING_APPROVAL → BOOKED → COMPLETED
                                              ↘ FAILED
```

Of 56 possible (from, to) transition pairs, only **12 are allowed**:

| From | To |
|---|---|
| `created` | `waiting_information`, `ready`, `failed` |
| `waiting_information` | `created`, `ready`, `failed` |
| `ready` | `running`, `failed` |
| `running` | `waiting_approval`, `failed` |
| `waiting_approval` | `booked`, `failed` |
| `booked` | `completed`, `failed` |

Transitions to `completed` or `booked` from any state other than the correct predecessor are rejected.

## Retry

When a tool execution step fails:

1. The error message is classified via `RetryPolicy.classify_failure()` into one of:
   - `NO_FLIGHTS_FOUND` (retryable)
   - `NO_HOTELS_FOUND` (retryable)
   - `TOOL_TIMEOUT` (retryable)
   - `TOOL_UNAVAILABLE` (not retryable)
   - `BUDGET_EXCEEDED` (not retryable)
   - `INVALID_DATES` (not retryable)
   - `INVALID_DESTINATION` (not retryable)
   - `SCHEMA_ERROR` (not retryable)
   - `UNKNOWN` (not retryable)
2. If retryable, the step is re-executed once.
3. The journal records both the original failure and the retry outcome.
4. Original errors are preserved in the `StepOutput` after retry.

## Approval

- `auto_approve=True` (default): transitions WAITING_APPROVAL → BOOKED automatically after approval is requested.
- `auto_approve=False`: pauses at WAITING_APPROVAL until an explicit approval call.
- `book()` enforces `current == WAITING_APPROVAL` — all other states reject booking.
- Invalid dates and infeasible budgets block the approval gate entirely (skip to `waiting_information` with `ranking_skipped=True`).

## Journal

- Every execution step, constraint check, candidate generation, ranking, approval, and booking event is appended to an in-memory journal.
- Entries are append-only: once recorded they cannot be modified or deleted.
- Each entry contains: `sequence` (auto-increment), `node` (string identifier), `status` (success/failed/skipped), `summary`, optional `data`, optional `error`.
- The journal supports timeline reconstruction: `reconstruct()` groups entries by node and preserves order.
- When an `ExecutionJournal` service is provided, entries are also persisted to the mission store.

## Ranking

- Ranking uses multi-criteria weighted scoring.
- Each criterion specifies: name, weight, direction (minimize or maximize), min_value, max_value.
- Scores are normalized to [0, 1] and clamped at bounds.
- Ties receive the same rank.
- The ranking is deterministic: same input always produces the same ranked output (seeded hash).
- Default flight criteria: price (50%), stops (30%), duration (20%).
- Default hotel criteria: price per night (40%), rating (40%), distance (20%).

## Memory

- Per-user preferences are stored as JSON files in a local directory.
- Each preference is checked for eligibility before storage: must have sufficient confidence, a valid category, and must not contain transient keywords (e.g., "booked", "price").
- Eligible preferences are loaded before intent interpretation and passed to the Manager Agent as context.
- Preferences survive process restarts (file-based persistence).
- Without a Lyzr Studio, memory extraction is skipped but stored preferences can still be read.

## Evidence Grounding

All explanations reference only recorded data:
- Execution journal entries (step-by-step trace)
- Ranking results (candidate scores and order)
- Mission record (persisted outcome)
- Approval gate history (state transitions)
- Rejected candidates (with reasons)
- Failures (with classification and recovery outcome)

The summary is derived from the mission record, not from raw user input. Confidence scores are derived from ranking data, not from LLM introspection.
