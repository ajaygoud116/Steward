MODE: EXTRACT_PREFERENCES

You are extracting candidate preferences from a user's message for potential long-term storage.

Conversation context:
{context}

User message:
{user_input}

Extract any preferences the user expresses that would be useful to remember for future interactions.

RULES:
- A preference is something the user "always", "usually", "prefers", "likes", "wants", "needs", or "requires"
- Booking confirmations ("I booked Paris") are NOT preferences
- One-time statements ("I want pizza for dinner") are NOT preferences
- Reusable habits ("I always prefer window seats") ARE preferences
- Preferences can be about: seat, meal, hotel, airline, room, transport, timing, amenity, service

Respond with this exact JSON structure:
{"candidate_preferences":[{"preference":"the preference text","category":"seat|meal|hotel|airline|room|transport|timing|amenity|service|general","confidence":0.0-1.0,"source":"what the user said"}]}

Return ONLY valid JSON. No other text.
