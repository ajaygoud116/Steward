# Configuration

## Environment Variables

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

## Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `LYZR_API_KEY` | **Yes** | — | Lyzr API key for the Manager Agent (LLM). Required for AI-powered interpret/plan/explain endpoints. Without it, fallback mode produces empty intents and no ranking/booking. |
| `Mission_Manager_AGENT_ID` | No | — | Agent ID for the Lyzr Manager. Used internally by `lyzr-adk`. |
| `FLIGHT_API_KEY` | No | — | External flight API key (not used in current deterministic mock). |
| `HOTEL_API_KEY` | No | — | External hotel API key (not used in current deterministic mock). |
| `WEATHER_API_KEY` | No | — | External weather API key (not used in current deterministic mock). |

## Example `.env`

```
LYZR_API_KEY=sk-your-key-here
Mission_Manager_AGENT_ID=
FLIGHT_API_KEY=
HOTEL_API_KEY=
WEATHER_API_KEY=
```

## Notes

- Without `LYZR_API_KEY`, the `TravelWorkflow` falls back to producing an empty `TravelIntent` with `missing_fields` populated. The deterministic pipeline still executes (flight search, hotel search, weather check all produce mock data), but ranking/booking are skipped because missing fields block approval.
- The three `*_API_KEY` variables are reserved for future real API integrations. The current `ToolExecutor` generates deterministic mock results using `hashlib.md5()` seeded on (destination, origin).
