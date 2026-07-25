# ── Test 2.1 — INTERPRET ──
Write-Host "=== Test 2.1: INTERPRET ===" -ForegroundColor Cyan
$body = @{ message = "Plan a Paris trip" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/mode/interpret" -Method Post -Body $body -ContentType "application/json"

# ── Test 2.2 — PLAN ──
Write-Host "`n=== Test 2.2: PLAN ===" -ForegroundColor Cyan
$body = @{ travel_intent = '{ "destination": "Paris", "missing_fields": ["budget"] }' } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/mode/plan" -Method Post -Body $body -ContentType "application/json"

# ── Test 2.3 — REPLAN ──
Write-Host "`n=== Test 2.3: REPLAN ===" -ForegroundColor Cyan
$body = @{
  failure_evidence = "No flights found from New York to Paris on July 15"
  mission_state    = '{ "destination": "Paris", "budget": 2000 }'
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/mode/replan" -Method Post -Body $body -ContentType "application/json"

# ── Test 2.4 — EXPLAIN ──
Write-Host "`n=== Test 2.4: EXPLAIN ===" -ForegroundColor Cyan
$body = @{
  mission_record    = '{ "destination": "Paris", "budget": 2000 }'
  execution_journal = '[{ "task": "flight_search", "status": "completed" }]'
  ranking_result    = '{ "top_option": "Air France AF1234" }'
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/mode/explain" -Method Post -Body $body -ContentType "application/json"
