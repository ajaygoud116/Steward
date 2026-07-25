# Extensibility Proof: ChecklistWorkflow

## Domain Independence Confirmed

| Dimension | TravelWorkflow | ChecklistWorkflow |
|---|---|---|
| Domain | Trip planning | Task checklist |
| Intent schema | `TravelIntent` (destination, dates, budget) | `ChecklistIntent` (title, items) |
| Plan schema | `TravelPlan` (legs with transport, hotels) | `ChecklistPlan` (tasks with id, name) |
| Step execution | API calls, preference lookup | Deterministic item-marks-done |
| Evidence | Flights, hotels, ranking | Validation list, constraints, ranking |
| Booking | API call | `{"ok": True}` |

## Zero Core Modifications

```bash
git diff mission_engine/core/        # no output
git diff mission_engine/services/    # no output
git diff mission_engine/storage/     # no output
```

## Registration

```python
WorkflowRegistry.register(ChecklistWorkflow)   # 1 line
wf = WorkflowRegistry.get("checklist")()
result = rt.run(workflow=wf, user_input="buy milk, pick up dry cleaning")
```

## Runtime Trail

```
[retrieve_cognis] success
[interpret]       success
[plan_fallback]   success
[check]           success  (× N items)
[constraint_validation] success
[candidate_generation]  success
[ranking]         success
[approval]        approved
[booking]         success
[mission_record]  success
```

## Files Delivered

| File | Lines | Purpose |
|---|---|---|
| `intent_schema.py` | 8 | `ChecklistIntent` pydantic model |
| `plan_schema.py` | 12 | `ChecklistPlan` / `ChecklistTask` pydantic models |
| `workflow.py` | 61 | `ChecklistWorkflow` — all 7 `MissionWorkflow` methods |

## Summary

ChecklistWorkflow proves the runtime is genuinely domain-agnostic. A new workflow author needs only:

1. Define a schema (2 models, ~20 lines)
2. Implement 7 methods (~60 lines)
3. Register with `WorkflowRegistry.register()`

No engine files, no runtime, no persistence, no approval gate, no retry logic — zero touching of the core.
