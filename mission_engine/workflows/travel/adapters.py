from typing import List, Any
from mission_engine.workflows.travel.intent_schema import TravelIntent


class ToolExecutor:
    """Pure Python simulated travel tool executors. No real APIs, no LLM calls."""

    def __init__(self, intent: TravelIntent):
        self.intent = intent
        import hashlib
        raw = f"{intent.destination}_{intent.origin}".encode()
        self._seed = int(hashlib.md5(raw).hexdigest()[:8], 16) & 0xFFFF

    def flight_search(self) -> List[dict]:
        dest = self.intent.destination or "Unknown"
        orig = self.intent.origin or "Unknown"
        airlines = ["AF", "DL", "UA", "BA", "LH"]
        results = []
        for i, code in enumerate(airlines):
            base_price = 400 + (i * 50) + (self._seed % 100)
            results.append({
                "id": f"{code}{100 + i}",
                "airline": code,
                "origin": orig,
                "destination": dest,
                "price": float(base_price),
                "duration_min": 360 + (i * 30),
                "stops": i % 3,
                "departure": f"{self.intent.departure_date or '2026-08-01'}T06:00",
            })
        return results

    def hotel_search(self) -> List[dict]:
        dest = self.intent.destination or "Unknown"
        names = ["Grand Palace", "City Center Inn", "Riverside Lodge", "Skyline Hotel", "Budget Stay"]
        results = []
        for i, name in enumerate(names):
            base_price = 80 + (i * 40) + (self._seed % 30)
            results.append({
                "id": f"hotel_{i + 1}",
                "name": name,
                "destination": dest,
                "price_per_night": float(base_price),
                "rating": round(3.0 + (i * 0.4), 1),
                "distance_km": 1.0 + (i * 0.8),
            })
        return results

    def weather_check(self) -> dict:
        dest = self.intent.destination or "Unknown"
        dep = self.intent.departure_date or ""
        season = "summer" if any(m in dep for m in ["06", "07", "08"]) else "mild"
        temp = 30 if season == "summer" else 18
        return {
            "destination": dest,
            "forecast": "sunny" if season == "summer" else "partly cloudy",
            "temperature_c": temp + (self._seed % 6),
            "humidity_pct": 50 + (self._seed % 30),
            "advisory": "none",
        }

    def execute(self, tool_name: str) -> Any:
        tool_map = {
            "flight_search": self.flight_search,
            "hotel_search": self.hotel_search,
            "weather_check": self.weather_check,
        }
        fn = tool_map.get(tool_name)
        if fn is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return fn()
