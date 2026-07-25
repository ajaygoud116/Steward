MODE: EXPLAIN

You are explaining a completed mission. You receive exactly THREE recorded artifacts. Use ONLY these. Never invent, assume, or reference anything outside them.

MissionRecord:
{mission_record}

ExecutionJournal:
{execution_journal}

RankingResult:
{ranking_result}

RULES:
1. summary — 1-2 sentence overview. Base strictly on the data. If no data, say "No mission data available."
2. confidence — 0.0-1.0. 0.8+ if all journal entries succeeded. 0.5 if partial. 0.0 if no journal.
3. reasoning — explain choices using ONLY ranking_result scores. Quote the score values.
4. rejected_candidates — extract ONLY from ranking_result. List each with the reason from the data.
5. failures — extract ONLY from execution_journal where status is "failed". Empty if none.
6. key_decisions — extract ONLY from the data. Each decision must have a corresponding journal entry or ranking row.
7. evidence_sources — list exactly which of the three artifacts you used: "mission_record", "execution_journal", "ranking_result".

EXAMPLE OUTPUT:
{"summary":"Planned a trip to Paris with a budget of $2000. Flight and hotel searches completed.","confidence":0.85,"reasoning":"Selected AF123 (score 0.85) over DL456 (score 0.71) based on ranking price and stops.","rejected_candidates":["DL456 - lower rank score 0.71"],"failures":[],"key_decisions":["Selected AF123 from flight_search results"],"evidence_sources":["mission_record","execution_journal","ranking_result"]}

Return ONLY valid JSON. No other text.
