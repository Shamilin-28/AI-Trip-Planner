import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gpt-oss:20b-cloud"

async def itinerary_agent(
    destination: str,
    origin: str,
    days: int,
    budget: str,
    currency: str,
    interests: list,
    travelers: int,
    transport: str,
    requirements: str,
    weather_data: str,
    attraction_data: str,
    hotel_data: str,
):
    """
    Streams a complete personalised itinerary.
    Now departure-aware and currency-locked.
    """
    interests_str = ", ".join(interests) if interests else "general sightseeing"

    # Build the day headers example dynamically so the model sees exactly what's expected
    day_example = "\n".join([f"## Day {i}" for i in range(1, min(days + 1, 4))])
    if days > 3:
        day_example += "\n## Day 4\n..."

    system = f"""You are an elite Travel Concierge AI. You MUST follow the EXACT markdown structure below — no exceptions, no creativity with formatting.

════════════════════════════════════════
MANDATORY MARKDOWN STRUCTURE (copy exactly):
════════════════════════════════════════

# [Destination] {days}-Day Itinerary

## Trip Overview
(2-3 sentence summary)

## Travel to {destination}
(How to get from {origin} to {destination}, with cost in {currency})

{day_example}

### Morning
| Time | Activity | Place | Est. Cost ({currency}) |
|------|----------|-------|------------------------|
| ...  | ...      | ...   | ...                    |

### Afternoon
| Time | Activity | Place | Est. Cost ({currency}) |
|------|----------|-------|------------------------|

### Evening
| Time | Activity | Place | Est. Cost ({currency}) |
|------|----------|-------|------------------------|

## Budget Breakdown
| Category | Est. Cost ({currency}) |
|----------|------------------------|
| Flights/Transport from {origin} | ... |
| Accommodation ({days} nights) | ... |
| Food & Dining | ... |
| Attractions & Activities | ... |
| Miscellaneous | ... |
| **Total per person** | **...** |

## Packing List
- ...

════════════════════════════════════════
STRICT FORMATTING RULES — NEVER BREAK THESE:
════════════════════════════════════════
1. HEADING LEVELS:
   - # (H1): Used ONLY once — the title line at the very top
   - ## (H2): Used ONLY for top-level sections: Trip Overview, Travel to {destination}, Day 1 … Day {days}, Budget Breakdown, Packing List
   - ### (H3): Used ONLY for Morning / Afternoon / Evening inside each day
   - #### and deeper: NEVER USE — strictly forbidden

2. CURRENCY: Every single cost must be in {currency}. Never use $, USD, EUR, or any other currency.

3. TABLES: Every Morning / Afternoon / Evening block MUST have a markdown table with columns: Time | Activity | Place | Est. Cost ({currency})

4. BOLD: Bold only place names using **Place Name** syntax.

5. NO PREAMBLE: Your response MUST start with exactly: # {destination} {days}-Day Itinerary
   Do not write "Sure!", "Here is", "Of course" or any intro text.

6. NO DEVIATIONS: Do not add extra sections, rename sections, or reorder them."""

    prompt = f"""Plan a {days}-day trip to {destination} for {travelers} traveler(s), departing from {origin}.

Trip Details:
- Budget Profile: {budget}
- Preferred Transport: {transport}
- Interests: {interests_str}
- Custom Requirements: {requirements}

--- CONTEXT DATA ---
WEATHER: {weather_data}
ATTRACTIONS: {attraction_data}
HOTELS: {hotel_data}

Remember: Start your response with exactly:
# {destination} {days}-Day Itinerary

Generate the full {days}-day itinerary now:"""

    payload = {
        "model": MODEL,
        "stream": True,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": 0.3,   # Lowered from 0.7 — less randomness = more consistent structure
            "num_predict": 4096,
            "top_p": 0.85         # Slightly tightened for more deterministic output
        }
    }

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"⚠️ Ollama Error {response.status_code}: Could not generate itinerary."
                    return

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

    except httpx.ConnectError:
        yield "❌ Error: Cannot connect to Ollama. Is 'ollama serve' running?"
    except Exception as e:
        yield f"❌ Unexpected Error: {str(e)}"