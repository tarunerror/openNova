"""
Planning Module - Converts user commands into actionable plans.
"""
import json
import logging
from typing import Dict, Any, List
from src.llm.client import llm_client

logger = logging.getLogger("Planner")


SYSTEM_PROMPT = """You are an AI agent that controls a Windows computer. Your job is to convert user commands into actionable plans.

You can perform these actions:
1. CLICK - Click at specific coordinates or on UI elements
2. TYPE - Type text
3. KEY - Press keyboard keys (enter, ctrl+c, etc.)
4. SHELL - Execute PowerShell commands
5. OPEN - Open applications
6. WAIT - Wait for a duration

Return your plan as a JSON array of action objects. Each action should have:
- "action": The action type (click, type, key, shell, open, wait)
- "target": What to interact with (coordinates, element name, command, etc.)
- "value": Additional value if needed (text to type, key to press, etc.)
- "thought": Brief explanation of why this step is needed

Example for "Open Chrome and search for Python":
```json
{
  "plan": [
    {
      "action": "open",
      "target": "chrome",
      "thought": "Open Google Chrome browser"
    },
    {
      "action": "wait",
      "value": 2,
      "thought": "Wait for Chrome to load"
    },
    {
      "action": "type",
      "value": "python tutorial",
      "thought": "Type search query"
    },
    {
      "action": "key",
      "value": "enter",
      "thought": "Submit search"
    }
  ]
}
```

IMPORTANT: 
- Always return valid JSON
- Be specific with targets
- Include thoughts for clarity
- Keep plans simple and direct
- For dangerous operations (delete, format, etc), add a "confirm": true flag
"""


class ActionPlanner:
    """Converts user commands into executable action plans."""
    
    def __init__(self):
        """Initialize the planner."""
        self.llm = llm_client
        self.last_error = ""
    
    def create_plan(self, user_command: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Create an action plan from a user command.
        
        Args:
            user_command: The user's voice command
            context: Optional context (screen info, previous actions, etc.)
            
        Returns:
            List of action dictionaries
        """
        if not self.llm.is_available():
            logger.error("LLM not available for planning")
            self.last_error = "LLM not available for planning"
            return []
        
        try:
            self.last_error = ""

            # Build the prompt
            prompt = f"User command: {user_command}\n\n"
            
            if context:
                prompt += f"Context: {json.dumps(context, indent=2)}\n\n"
            
            prompt += "Generate an action plan to fulfill this command:"
            
            logger.info(f"Planning for command: {user_command}")
            
            # Get response from LLM
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_message=SYSTEM_PROMPT
            )

            if isinstance(response, str) and response.startswith("Error:"):
                self.last_error = response
                logger.error(f"Planner LLM error: {response}")
                return []
            
            # Parse JSON response
            plan = self._parse_plan(response)
            
            logger.info(f"Generated plan with {len(plan)} steps")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            self.last_error = str(e)
            return []
    
    def _parse_plan(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into a plan."""
        try:
            # Try to extract JSON from response
            # Handle cases where LLM wraps JSON in markdown
            response = response.strip()
            
            if "```json" in response:
                # Extract JSON from code block
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                # Generic code block
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            # Parse JSON
            data = json.loads(response)
            
            # Extract plan array
            if isinstance(data, dict) and "plan" in data:
                return data["plan"]
            elif isinstance(data, list):
                return data
            else:
                logger.error(f"Unexpected plan format: {type(data)}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            logger.debug(f"Response was: {response}")
            self.last_error = f"Failed to parse plan JSON: {e}"
            return []
        except Exception as e:
            logger.error(f"Error parsing plan: {e}")
            self.last_error = str(e)
            return []
    
    def validate_plan(self, plan: List[Dict[str, Any]]) -> bool:
        """
        Validate a plan before execution.
        
        Args:
            plan: List of actions
            
        Returns:
            True if plan is valid
        """
        required_fields = ["action"]
        
        for i, action in enumerate(plan):
            if not isinstance(action, dict):
                logger.error(f"Action {i} is not a dict")
                return False
            
            for field in required_fields:
                if field not in action:
                    logger.error(f"Action {i} missing required field: {field}")
                    return False
        
        return True
    
    def needs_confirmation(self, plan: List[Dict[str, Any]]) -> bool:
        """
        Check if plan contains dangerous actions requiring confirmation.
        
        Args:
            plan: List of actions
            
        Returns:
            True if confirmation needed
        """
        dangerous_keywords = [
            "delete", "remove", "format", "rm ", "del ",
            "registry", "regedit", "system32"
        ]
        
        for action in plan:
            # Check if action has confirm flag
            if action.get("confirm", False):
                return True
            
            # Check for dangerous keywords
            action_str = json.dumps(action).lower()
            for keyword in dangerous_keywords:
                if keyword in action_str:
                    logger.warning(f"Dangerous keyword detected: {keyword}")
                    return True
        
        return False


# Global planner instance
planner = ActionPlanner()
