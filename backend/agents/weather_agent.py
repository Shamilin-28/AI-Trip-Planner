from utils.geo import get_coordinates
from utils.weather import get_weather

async def weather_agent(destination: str) -> str:
    """Fetches LIVE real-time weather using Open-Meteo + Nominatim geocoding."""
    coords = await get_coordinates(destination)
    if coords["lat"] is None:
        return f"## 🌤️ Weather\n⚠️ Could not geocode '{destination}' — weather unavailable.\n"

    w = await get_weather(coords["lat"], coords["lon"])

    lines = [
        f"## 🌤️ Live Weather — {coords['display_name'].split(',')[0]}",
        f"- **Right now:** {w['condition']}, **{w['temp_c']}°C** (feels like {w['feels_like']}°C)",
        f"- **Humidity:** {w['humidity']}% | **Wind:** {w['wind_kph']} km/h",
        "",
        "### 5-Day Forecast",
    ]
    for d in w["forecast"]:
        rain = f" | 🌧 {d['rain_mm']}mm rain" if d["rain_mm"] and d["rain_mm"] > 0 else ""
        lines.append(f"- **{d['date']}** — {d['condition']}, {d['min']}°C → {d['max']}°C{rain}")

    return "\n".join(lines) + "\n"