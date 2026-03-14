import httpx

async def get_coordinates(destination: str) -> dict:
    """Geocode any destination via Nominatim (OpenStreetMap). No API key needed."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": destination, "format": "json", "limit": 1}
    headers = {"User-Agent": "AITripPlanner/3.0 (open-source travel planner)"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params, headers=headers)
            results = r.json()
        if not results:
            return {"lat": None, "lon": None, "display_name": destination}
        res = results[0]
        return {
            "lat": float(res["lat"]),
            "lon": float(res["lon"]),
            "display_name": res.get("display_name", destination),
            "country": res.get("display_name", "").split(",")[-1].strip(),
        }
    except Exception:
        return {"lat": None, "lon": None, "display_name": destination}