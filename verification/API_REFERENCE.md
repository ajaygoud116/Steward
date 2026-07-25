# API Reference

Base URL: `http://localhost:8000`

## GET /health

Health check endpoint.

**Response `200`:**

```json
{"status": "ok"}
```

---

## POST /travel/plan

Entry point for the travel planning pipeline.

**Request:**

```json
{
  "message": "I want to fly from New York to Paris next weekend for two people with a reasonable budget",
  "session_id": null
}
```

**Response `200` (Clarification — missing fields):**

```json
{
  "type": "clarification",
  "session_id": "uuid",
  "clarification_question": "",
  "missing_fields": ["destination", "departure_date"],
  "partial_plan": { "...": "..." }
}
```

**Response `200` (Plan — ready to execute):**

```json
{
  "type": "plan",
  "session_id": "uuid",
  "plan": { "...": "..." }
}
```

**Error Response `200`:**

```json
{
  "type": "error",
  "session_id": "uuid"
}
```

---

## POST /mode/interpret

Run the Manager Agent in INTERPRET mode — extracts structured intent from free text.

**Request:**

```json
{
  "message": "I want to fly to Paris",
  "user_id": "default",
  "cognis_preferences": "None",
  "session_id": null
}
```

**Response `200`:**

```json
{
  "destination": "Paris",
  "origin": "",
  "departure_date": "",
  "return_date": "",
  "budget": 0,
  "passengers": 1,
  "missing_fields": ["origin", "departure_date", "return_date", "budget"],
  "preferences": [],
  "explicit_preferences": [],
  "reusable_preferences": [],
  "hard_constraints": [],
  "soft_constraints": [],
  "_cognis_preferences": ""
}
```

**Response `200` (RAI blocked):**

```json
{
  "error": "Input blocked by RAI guardrails",
  "flags": ["injection"]
}
```

---

## POST /mode/plan

Run the Manager Agent in PLAN mode — builds an execution plan from a travel intent JSON string.

**Request:**

```json
{
  "travel_intent": "{\"destination\": \"Paris\", \"origin\": \"New York\"}",
  "session_id": null
}
```

**Response `200`:**

```json
{
  "workflow": "travel",
  "tasks": [
    {"task_id": "t1", "task_name": "Search Flights", "required_tool": "flight_search", "depends_on": []},
    {"task_id": "t2", "task_name": "Search Hotels", "required_tool": "hotel_search", "depends_on": []},
    {"task_id": "t3", "task_name": "Check Weather", "required_tool": "weather_check", "depends_on": []}
  ],
  "approval_required": false
}
```

---

## POST /mode/replan

Run the Manager Agent in REPLAN mode — decides whether to retry, replan, or abort after a failure.

**Request:**

```json
{
  "failure_evidence": "hotel_search failed: TOOL_TIMEOUT",
  "mission_state": "{}",
  "session_id": null
}
```

**Response `200`:**

```json
{
  "decision": "retry",
  "reasoning": "...",
  "modified_plan": null
}
```

---

## POST /mode/explain

Run the Manager Agent in EXPLAIN mode — generates a human-readable explanation grounded in mission record, journal, and ranking.

**Request:**

```json
{
  "mission_id": "abc123",
  "mission_record": "{}",
  "execution_journal": "[]",
  "ranking_result": "{}",
  "session_id": null
}
```

**Response `200`:**

```json
{
  "summary": "Mission completed...",
  "confidence": 0.93,
  "reasoning": "1. Extracted intent...",
  "rejected_candidates": ["DL101 (lower score)"],
  "failures": ["hotel_search timeout -> retry -> success"],
  "key_decisions": ["Selected AF100", "Approved booking"],
  "evidence_sources": ["ExecutionJournal (16 entries)", "RankingResult", "MissionRecord"]
}
```

**Error Response `200` (RAI blocked):**

```json
{
  "error": "Output blocked by RAI guardrails",
  "flags": ["pii"],
  "partial": { "...": "..." }
}
```

---

## GET /memory/preferences/{user_id}

Retrieve stored preferences for a user.

**Response `200`:**

```json
{
  "user_id": "default",
  "preferences": "User prefers window seats, aisle seats"
}
```

---

## POST /memory/process

Process a message through the memory pipeline (same request schema as `/mode/interpret`).

**Request:**

```json
{
  "message": "I always prefer window seats",
  "user_id": "default",
  "session_id": null
}
```

**Response `200`:**

```json
{
  "eligible": [],
  "summary": "..."
}
```

## Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 422 | Validation error (malformed request body) |
| 500 | Internal server error |
