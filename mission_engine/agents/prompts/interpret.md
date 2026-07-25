MODE: INTERPRET

You are extracting structured intent from a user's travel request.

Local Preference Memory:
{cognis_preferences}

User request:
{user_input}

Extract these fields. Omit fields the user didn't mention (they default to empty/0).

RULES:
- destination: city or country. REQUIRED if the user mentions one.
- origin: leave empty if not mentioned.
- departure_date: convert to YYYY-MM-DD. REQUIRED for a complete plan.
- return_date: YYYY-MM-DD or empty.
- budget: numeric in USD. REQUIRED for a complete plan.
- passengers: number. Default 1 if not mentioned.
- missing_fields: ALWAYS include what's still needed. If destination is missing, list "destination". If budget is missing, list "budget".
- explicit_preferences: what the user literally asked for (e.g. "window seat", "non-stop")
- reusable_preferences: preferences worth remembering (e.g. "prefers aisle seat")
- hard_constraints: non-negotiable (e.g. "must be vegetarian", "must depart after 6pm")
- soft_constraints: flexible (e.g. "prefer morning", "cheaper is better")

EXAMPLE OUTPUT:
{"destination":"Paris","origin":"","departure_date":"","return_date":"","budget":0,"passengers":1,"missing_fields":["budget","departure_date"],"explicit_preferences":[],"reusable_preferences":[],"hard_constraints":[],"soft_constraints":[]}

Return ONLY valid JSON. No other text.
