MODE: REPLAN

You are analyzing a workflow failure and deciding whether to replan.

FailureEvidence:
{failure_evidence}

MissionState:
{mission_state}

RULES:
1. If FailureEvidence mentions "No flights", "no hotels", "API error", "timeout", "budget exceeded", or any error → replan_required = true
2. failure_class must be one of: "NO_FLIGHTS_FOUND", "NO_HOTELS_FOUND", "BUDGET_EXCEEDED", "NO_FEASIBLE_ITINERARY", "API_ERROR", "CONSTRAINT_VIOLATION"
3. candidate_relaxations: suggest ways to overcome the failure (e.g. "try different dates", "increase budget by 20%", "allow connecting flights", "try nearby airports")
4. suggested_actions: concrete next steps the system should take

EXAMPLE OUTPUT:
{"replan_required":true,"failure_class":"NO_FLIGHTS_FOUND","failure_reason":"No direct flights available on requested date","candidate_relaxations":["Try adjacent dates ±3 days","Allow one stopover","Try nearby airports"],"suggested_actions":["Call flight_search with relaxed dates","Call flight_search with origin/destination radius"]}

Return ONLY valid JSON. No other text.
