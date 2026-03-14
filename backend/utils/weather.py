import httpx

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 80: "Rain showers",
    81: "Moderate showers", 82: "Violent showers", 95: "Thunderstorm",
}

async def get_weather(lat: float, lon: float) -> dict:
    """Fetch live weather + 5-day forecast from Open-Meteo. No API key."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "forecast_days": 5, "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        data = r.json()
    cur = data.get("current", {})
    daily = data.get("daily", {})
    forecast = []
    for i, date in enumerate(daily.get("time", [])[:5]):
        forecast.append({
            "date": date,
            "max": daily["temperature_2m_max"][i],
            "min": daily["temperature_2m_min"][i],
            "rain_mm": daily["precipitation_sum"][i],
            "condition": WMO_CODES.get(daily["weather_code"][i], "Variable"),
        })
    return {
        "temp_c": cur.get("temperature_2m"),
        "feels_like": cur.get("apparent_temperature"),
        "humidity": cur.get("relative_humidity_2m"),
        "wind_kph": cur.get("wind_speed_10m"),
        "condition": WMO_CODES.get(cur.get("weather_code", 0), "Clear"),
        "forecast": forecast,
    }