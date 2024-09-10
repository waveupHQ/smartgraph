# smartgraph/tools/weather_toolkit.py

from typing import Any, Dict, List

from .base_toolkit import Toolkit


class WeatherToolkit(Toolkit):
    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "weather_toolkit"

    @property
    def description(self) -> str:
        return "A toolkit for fetching weather information"

    @property
    def functions(self) -> Dict[str, Any]:
        return {"get_temperature": self.get_temperature}

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_temperature",
                    "description": "Get the current temperature for a specific location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and country, e.g., 'London, UK'",
                            }
                        },
                        "required": ["location"],
                    },
                },
            }
        ]

    async def get_temperature(self, location: str) -> Dict[str, Any]:
        # Simulated API call
        # In a real implementation, you would make an API call to OpenWeatherMap here
        return {"temperature": 22.5, "unit": "Celsius", "location": location}
