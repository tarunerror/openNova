"""
Example skill: Weather information (mock implementation).
This demonstrates how to create a custom skill.
"""
from src.plugins.skill_base import Skill
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class WeatherSkill(Skill):
    """
    Example skill that provides weather information.
    In a real implementation, this would call a weather API.
    """
    
    @property
    def name(self) -> str:
        return "WeatherSkill"
    
    @property
    def description(self) -> str:
        return "Provides weather information for a given location"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def author(self) -> str:
        return "AI Agent Team"
    
    def can_handle(self, user_input: str) -> bool:
        """
        Check if the input is asking for weather information.
        """
        weather_keywords = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy"]
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in weather_keywords)
    
    def execute(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the weather skill.
        
        This is a mock implementation. In production, you would:
        1. Parse the location from user_input
        2. Call a weather API (OpenWeatherMap, WeatherAPI, etc.)
        3. Return the actual weather data
        """
        logger.info(f"Weather skill executing for input: {user_input}")
        
        # Mock response
        response = "The weather is sunny with a temperature of 72°F. This is a mock response."
        
        return {
            "success": True,
            "response": response,
            "data": {
                "temperature": 72,
                "condition": "sunny",
                "location": "Unknown",
                "mock": True
            }
        }
    
    def get_examples(self) -> List[str]:
        """
        Return example commands for this skill.
        """
        return [
            "What's the weather like?",
            "Tell me the weather forecast",
            "Is it going to rain today?",
            "What's the temperature outside?"
        ]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Configuration schema for the weather skill.
        """
        return {
            "api_key": {
                "type": "string",
                "description": "API key for weather service",
                "required": False
            },
            "default_location": {
                "type": "string",
                "description": "Default location for weather queries",
                "required": False,
                "default": "New York"
            },
            "units": {
                "type": "string",
                "description": "Temperature units (fahrenheit or celsius)",
                "required": False,
                "default": "fahrenheit",
                "options": ["fahrenheit", "celsius"]
            }
        }
