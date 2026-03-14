import httpx
import asyncio
from utils.geo import get_coordinates

OVERPASS = "https://overpass-api.de/api/interpreter"

async def hotel_agent(destination: str, budget: str) -> str:
    """Fetches LIVE hotel data with retry logic to handle 429 rate limits."""
    coords = await get_coordinates(destination)
    if coords["lat"] is None:
        return f"## 🏨 Hotels\n⚠️ Could not find hotels for '{destination}'.\n"

    lat, lon = coords["lat"], coords["lon"]
    
    # Combined nodes and ways into 'nwr' for efficiency
    query = f"""[out:json][timeout:25];
    (
      nwr[tourism~"hotel|hostel|guest_house|resort"](around:8000,{lat},{lon});
    );
    out center 30;"""

    data = None
    # Retry logic for 429 errors
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                # descriptive User-Agent helps avoid blocks
                headers = {"User-Agent": "AITripPlanner/1.0 (contact: your@email.com)"}
                r = await c.post(OVERPASS, data={"data": query}, headers=headers)
                
                if r.status_code == 429:
                    wait_time = (attempt + 1) * 2
                    await asyncio.sleep(wait_time)
                    continue
                
                r.raise_for_status()
                data = r.json()
                break
        except Exception as e:
            if attempt == 2:
                return f"## 🏨 Hotels in {destination}\n⚠️ Map service busy. AI will suggest accommodations based on knowledge.\n"
            await asyncio.sleep(1)

    if not data or "elements" not in data:
        return f"## 🏨 Hotels in {destination}\n⚠️ No live data available right now.\n"

    # Define preference based on user budget
    budget_pref = {
        "Budget": ["hostel", "guest_house", "motel"],
        "Mid-range": ["hotel", "apartment", "guest_house"],
        "Luxury": ["hotel", "resort"],
    }.get(budget, ["hotel"])

    hotels = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if not name: continue
        
        hotels.append({
            "name": name,
            "type": tags.get("tourism", "hotel").replace("_", " ").title(),
            "stars": tags.get("stars", ""),
            "addr": tags.get("addr:street", tags.get("addr:full", "Local Area")),
            "phone": tags.get("phone", ""),
            "web": tags.get("website", "")
        })

    # Sort: Preferred types first
    preferred = [h for h in hotels if h["type"].lower() in budget_pref]
    other = [h for h in hotels if h["type"].lower() not in budget_pref]
    final_list = (preferred + other)[:12]

    # Build Markdown Table
    lines = [
        f"## 🏨 Live Accommodations in {destination} ({budget})",
        "_Data fetched live from OpenStreetMap_\n",
        "| Name | Type | Stars | Contact & Address |",
        "|:--- |:--- |:--- |:--- |"
    ]

    for h in final_list:
        # Star emoji logic
        stars_val = str(h["stars"])
        stars_display = "⭐" * int(stars_val) if stars_val.isdigit() else "—"
        
        # Format contact info
        contact = h["addr"]
        if h["phone"]: contact += f"<br>📞 {h['phone']}"
        if h["web"]: contact += f"<br>[🌐 Website]({h['web']})"
        
        lines.append(f"| **{h['name']}** | {h['type']} | {stars_display} | {contact} |")

    if not final_list:
        return f"## 🏨 Hotels in {destination}\n_No specific live data found. AI will generate recommendations._\n"

    return "\n".join(lines) + "\n"