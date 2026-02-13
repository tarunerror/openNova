"""
Vision Analyzer - Uses vision models to understand screenshots.
"""
import logging
from pathlib import Path
import base64
from typing import Dict, Any, List, Optional
from src.llm.client import llm_client
from src.vision.capture import screen_capture

logger = logging.getLogger("Vision")


class VisionAnalyzer:
    """Analyzes screenshots using vision-language models."""
    
    def __init__(self):
        """Initialize vision analyzer."""
        self.llm = llm_client
    
    def analyze_screenshot(self, prompt: str, screenshot_path: str = None) -> str:
        """
        Analyze a screenshot with a prompt.
        
        Args:
            prompt: Question or instruction about the screenshot
            screenshot_path: Path to screenshot (or None to capture current screen)
            
        Returns:
            Model's response
        """
        if not self.llm.is_available():
            logger.error("LLM not available for vision analysis")
            return ""
        
        try:
            # Capture screenshot if not provided
            if screenshot_path is None:
                screenshot_path = screen_capture.save_screenshot()
            
            if not screenshot_path or not Path(screenshot_path).exists():
                logger.error("Screenshot not available")
                return ""
            
            # Encode image to base64
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Create message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            logger.info(f"Analyzing screenshot with prompt: {prompt}")
            
            # Get response
            response = self.llm.chat(messages)
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot: {e}")
            return ""
    
    def find_element_in_screenshot(self, element_description: str) -> Optional[Dict[str, Any]]:
        """
        Find an element's coordinates in a screenshot.
        
        Args:
            element_description: Description of the element to find
            
        Returns:
            Dictionary with coordinates or None
        """
        prompt = f"""Look at this screenshot and find the {element_description}.
        
Return ONLY a JSON object with the coordinates like this:
{{
    "found": true/false,
    "x": <x coordinate of center>,
    "y": <y coordinate of center>,
    "description": "<what you see>"
}}

Be precise with the coordinates."""
        
        response = self.analyze_screenshot(prompt)
        
        try:
            import json
            
            # Try to extract JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            data = json.loads(response)
            
            if data.get("found", False):
                return data
            else:
                logger.warning(f"Element not found: {element_description}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing vision response: {e}")
            logger.debug(f"Response was: {response}")
            return None
    
    def describe_screen(self) -> str:
        """
        Get a description of what's on the screen.
        
        Returns:
            Description of the screen
        """
        prompt = """Describe what you see on this screen. 
        Focus on:
        - Active window/application
        - Main UI elements (buttons, text boxes, etc.)
        - Current state or activity
        
Be concise and factual."""
        
        return self.analyze_screenshot(prompt)
    
    def get_clickable_elements(self) -> List[Dict[str, Any]]:
        """
        Get a list of clickable elements visible on screen.
        
        Returns:
            List of element dictionaries with coordinates
        """
        prompt = """List all clickable elements visible on this screen (buttons, links, icons, etc.).

For each element, return JSON like:
{{
    "elements": [
        {{"name": "element name", "x": <x>, "y": <y>, "type": "button/link/icon"}},
        ...
    ]
}}"""
        
        response = self.analyze_screenshot(prompt)
        
        try:
            import json
            
            # Extract JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            
            data = json.loads(response)
            return data.get("elements", [])
            
        except Exception as e:
            logger.error(f"Error parsing elements: {e}")
            return []


# Global vision analyzer
vision_analyzer = VisionAnalyzer()
