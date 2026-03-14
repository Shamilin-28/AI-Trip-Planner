import asyncio
import os
import sys

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

# Environment and Path setup
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

# Agent Imports
from agents.weather_agent import weather_agent
from agents.attraction_agent import attraction_agent
from agents.hotel_agent import hotel_agent
from agents.itinerary_agent import itinerary_agent

app = FastAPI(title="AI Trip Planner Backend", version="3.2")

# Robust CORS configuration for Frontend-Backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health") # ROUTE 
async def health():
    """Check if all agents and data sources are connected."""
    return {
        "status": "ok",
        "version": "3.2",
        "mode": "hybrid-cloud-local-ai",
        "agents": ["weather", "attraction", "hotel", "itinerary"]
    }

@app.get("/stream") # ROUTES FOR AI
async def stream_itinerary(
    destination: str = Query(..., description="Target destination"),
    origin: str = Query(default="Current Location", description="Departure city"),
    days: int = Query(default=5),
    transport: str = Query(default="Mix"),
    budget: str = Query(default="Mid-range"),
    currency: str = Query(default="INR"),
    symbol: str = Query(default="₹"),
    interests: str = Query(default=""),
    travelers: int = Query(default=1),
    requirements: str = Query(default=""),
):
    """
    Orchestrates the live data fetching and streams the AI itinerary
    using Server-Sent Events (SSE).
    """
    interests_list = [i.strip() for i in interests.split(",") if i.strip()]

    async def event_stream():
        try:
            # Step 1: UI Feedback
            yield sse("status", f"🔍 Locating {destination} and calculating route from {origin}...")

            # Step 2: Concurrent Data Fetching (Live APIs)
            weather_data, attraction_data, hotel_data = await asyncio.gather(
                weather_agent(destination),
                attraction_agent(destination, interests_list),
                hotel_agent(destination, budget),
            )

            # Step 3: Stream Live Data Context to Frontend
            yield sse("data", weather_data + "\n\n---\n\n")
            yield sse("data", attraction_data + "\n\n---\n\n")
            yield sse("data", hotel_data + "\n\n---\n\n")

            # Step 4: UI Feedback for AI Phase
            yield sse("status", f"🤖 GPT-OSS is generating your itinerary in {currency}...")

            # Step 5: Execute and Stream Itinerary Agent
            async for chunk in itinerary_agent(
                destination=destination,
                origin=origin,
                days=days,
                budget=budget,
                currency=f"{currency} ({symbol})",
                interests=interests_list,
                travelers=travelers,
                transport=transport,
                requirements=requirements,
                weather_data=weather_data,
                attraction_data=attraction_data,
                hotel_data=hotel_data,
            ):
                yield sse("data", chunk)

            yield sse("done", "Itinerary completed successfully.")

        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            traceback.print_exc()
            yield sse("error", f"❌ Backend Error: {str(e)}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        },
    )


def sse(event: str, data: str) -> str:
    """
    Formats data into a valid Server-Sent Event.

    SSE RULE: A newline inside a `data:` field terminates the event early.
    The browser's EventSource splits on \\n and treats each line as a new field.
    So ANY newline inside `data` must be escaped to a literal \\n so the
    frontend receives a single unbroken `data:` line, then unescapes it back.

    The frontend (itinerary.html) already does:
        chunk = e.data.replace(/\\\\n/g, '\\n')
    so the round-trip is: real \\n → escaped \\\\n (wire) → real \\n (browser).
    """
    # Escape real newlines → literal \n  and  real \r → nothing
    safe_data = data.replace('\r', '').replace('\n', '\\n')
    return f"event: {event}\ndata: {safe_data}\n\n"


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)