"""
Web tools for Jarvis.
Provides live real-time internet search and weather forecasts without requiring extra API keys.
"""

import json
import urllib.parse
import urllib.request


def search_web(query: str, max_results: int = 4) -> str:
    """Search the live web using DuckDuckGo."""
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            return f"No web search results found for '{query}'."

        output = []
        for i, r in enumerate(results, start=1):
            title = r.get("title", "")
            body = r.get("body", "")
            url = r.get("href", "")
            output.append(f"{i}. {title}\n   {body}\n   URL: {url}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Web search failed: {e}"


def get_weather(city: str = "Chennai") -> str:
    """Fetch current weather and forecast for any city in the world."""
    try:
        encoded_city = urllib.parse.quote(city.strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=en&format=json"
        
        import ssl
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ctx = ssl._create_unverified_context()

        req = urllib.request.Request(geo_url, headers={"User-Agent": "Jarvis-Assistant/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))

        if not geo_data.get("results"):
            return f"Could not find coordinates for city '{city}'."

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        city_name = location.get("name", city)
        country = location.get("country", "")

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m"
        )
        req2 = urllib.request.Request(weather_url, headers={"User-Agent": "Jarvis-Assistant/1.0"})
        with urllib.request.urlopen(req2, context=ctx, timeout=8) as resp2:
            data = json.loads(resp2.read().decode("utf-8"))

        cur = data.get("current", {})
        temp = cur.get("temperature_2m", "N/A")
        feels = cur.get("apparent_temperature", "N/A")
        humidity = cur.get("relative_humidity_2m", "N/A")
        wind = cur.get("wind_speed_10m", "N/A")
        code = cur.get("weather_code", 0)

        # WMO Weather interpretation codes
        conditions = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        weather_desc = conditions.get(code, "Clear/Fair")

        return (
            f"Weather for {city_name}, {country}:\n"
            f"- Condition: {weather_desc}\n"
            f"- Temperature: {temp}°C (feels like {feels}°C)\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind} km/h"
        )
    except Exception as e:
        return f"Unable to fetch weather: {e}"


REGISTRY = {
    "search_web": (search_web, False),
    "get_weather": (get_weather, False),
}

SCHEMAS = [
    {
        "name": "search_web",
        "description": "Search the live internet for recent news, technical documentation, facts, or answers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query terms"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get real-time live weather conditions, temperature, and forecast for any city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Chennai', 'London', 'New York'"}
            },
            "required": ["city"],
        },
    },
]
