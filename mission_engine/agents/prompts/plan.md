MODE: PLAN

You are creating an ordered execution plan based on the intent below.

TravelIntent:
{travel_intent}

RULES:
1. If the intent mentions a city, country, flights, hotels, or travel dates → workflow = "travel"
2. A travel execution plan ALWAYS has these 3 tasks in this order:
   - flight_search (no dependencies)
   - hotel_search (no dependencies)
   - weather_check (no dependencies)
3. If budget > 10000 or the intent mentions "business class" or "first class" → approval_required = true
4. expected_outputs should list what each task produces

EXAMPLE OUTPUT:
{"workflow":"travel","tasks":[{"task_id":"t1","task_name":"Flight Search","required_tool":"flight_search","depends_on":[]},{"task_id":"t2","task_name":"Hotel Search","required_tool":"hotel_search","depends_on":[]},{"task_id":"t3","task_name":"Weather Check","required_tool":"weather_check","depends_on":[]}],"approval_required":false,"expected_outputs":["flight options with prices","hotel options with prices","weather forecast"]}

Return ONLY valid JSON. No other text.
