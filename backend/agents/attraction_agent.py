import asyncio
import httpx
from utils.geo import get_coordinates

OVERPASS = "https://overpass-api.de/api/interpreter"

async def _query(lat: float, lon: float, tag_filter: str, radius: int = 5000, limit: int = 12) -> list:
    query = f"""[out:json][timeout:20];
(node{tag_filter}(around:{radius},{lat},{lon});
 way{tag_filter}(around:{radius},{lat},{lon}););
out center {limit};"""
    try:
        async with httpx.AsyncClient(timeout=25) as c:
            r = await c.post(OVERPASS, data={"data": query})
            data = r.json()
    except Exception:
        return []
    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if not name:
            continue
        results.append({
            "name": name,
            "type": tags.get("tourism") or tags.get("leisure") or tags.get("amenity") or "place",
            "hours": tags.get("opening_hours", ""),
            "website": tags.get("website", ""),
            "description": tags.get("description", ""),
        })
    return results


async def attraction_agent(destination: str, interests: list) -> str:
    """Fetches LIVE attractions from OpenStreetMap via Overpass API."""
    coords = await get_coordinates(destination)
    if coords["lat"] is None:
        return f"## 🗺️ Attractions\n⚠️ Could not find attractions for '{destination}'.\n"

    lat, lon = coords["lat"], coords["lon"]

    # Run all category queries in parallel
    tourism, leisure, food, art = await asyncio.gather(
        _query(lat, lon, '[tourism~"attraction|museum|gallery|viewpoint|zoo|aquarium|theme_park|monument"]', 6000, 14),
        _query(lat, lon, '[leisure~"park|nature_reserve|garden|beach"]', 6000, 8),
        _query(lat, lon, '[amenity~"restaurant|cafe|bar|marketplace|food_court"]', 3000, 10),
        _query(lat, lon, '[historic~"monument|castle|ruins|temple|church|mosque"]', 6000, 8),
    )

    lines = [f"## 🗺️ Live Attractions in {destination}\n_Data fetched live from OpenStreetMap_\n"]

    if tourism:
        lines.append("### 🏛️ Landmarks & Attractions")
        for p in tourism[:8]:
            h = f" *(Hours: {p['hours']})*" if p["hours"] else ""
            lines.append(f"- **{p['name']}** — _{p['type']}_{h}")
        lines.append("")

    if art:
        lines.append("### 🏯 Historic & Cultural Sites")
        for p in art[:6]:
            lines.append(f"- **{p['name']}** — _{p['type']}_")
        lines.append("")

    if leisure:
        lines.append("### 🌿 Parks & Nature")
        for p in leisure[:5]:
            lines.append(f"- **{p['name']}** — _{p['type']}_")
        lines.append("")

    if food:
        lines.append("### 🍽️ Restaurants & Cafés")
        for p in food[:7]:
            lines.append(f"- **{p['name']}** — _{p['type']}_")
        lines.append("")

    if not (tourism or leisure or food or art):
        lines.append("_No OSM data available — AI will plan using general knowledge._\n")

    return "\n".join(lines)