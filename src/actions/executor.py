"""
Action Executor - Executes action plans.
"""
import logging
import time
from typing import List, Dict, Any
from src.actions.input_simulator import input_sim
from src.actions.shell import shell_executor
from src.vision.accessibility import accessibility
from src.vision.analyzer import vision_analyzer

logger = logging.getLogger("Executor")


class ActionExecutor:
    """Executes action plans from the planner."""
    
    def __init__(self):
        """Initialize action executor."""
        self.input_sim = input_sim
        self.shell = shell_executor
        self.accessibility = accessibility
        self.vision = vision_analyzer
        
        logger.info("Action executor initialized")
    
    def execute_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute an action plan.
        
        Args:
            plan: List of action dictionaries
            
        Returns:
            Execution result dictionary
        """
        if not plan:
            logger.warning("Empty plan provided")
            return {"success": False, "message": "Empty plan"}
        
        logger.info(f"Executing plan with {len(plan)} steps")
        
        results = []
        
        for i, action in enumerate(plan):
            logger.info(f"Step {i+1}/{len(plan)}: {action.get('action', 'unknown')}")
            
            try:
                result = self._execute_action(action)
                results.append(result)
                
                if not result.get("success", False):
                    logger.warning(f"Step {i+1} failed: {result.get('message', 'Unknown error')}")
                    # Continue anyway unless it's critical
                
                # Brief delay between actions
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error executing step {i+1}: {e}")
                results.append({"success": False, "message": str(e)})
        
        # Summarize results
        success_count = sum(1 for r in results if r.get("success", False))
        
        return {
            "success": success_count == len(results),
            "total_steps": len(results),
            "successful_steps": success_count,
            "results": results
        }
    
    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single action.
        
        Args:
            action: Action dictionary
            
        Returns:
            Result dictionary
        """
        action_type = action.get("action", "").lower()
        
        if action_type == "click":
            return self._action_click(action)
        
        elif action_type == "type":
            return self._action_type(action)
        
        elif action_type == "key":
            return self._action_key(action)
        
        elif action_type == "shell":
            return self._action_shell(action)
        
        elif action_type == "open":
            return self._action_open(action)
        
        elif action_type == "wait":
            return self._action_wait(action)
        
        elif action_type == "move":
            return self._action_move(action)
        
        elif action_type == "scroll":
            return self._action_scroll(action)
        
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return {"success": False, "message": f"Unknown action: {action_type}"}
    
    def _action_click(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute click action."""
        target = action.get("target", "")
        
        # Try to find element by name using accessibility API
        if isinstance(target, str):
            element = self.accessibility.find_element_by_name(target)
            
            if element:
                x = element.get("center_x", 0)
                y = element.get("center_y", 0)
            else:
                # Fall back to vision
                result = self.vision.find_element_in_screenshot(target)
                if result:
                    x = result.get("x", 0)
                    y = result.get("y", 0)
                else:
                    return {"success": False, "message": f"Could not find: {target}"}
        
        elif isinstance(target, (list, tuple)) and len(target) >= 2:
            x, y = target[0], target[1]
        
        else:
            return {"success": False, "message": "Invalid click target"}
        
        # Click
        self.input_sim.click(x, y)
        
        return {
            "success": True,
            "message": f"Clicked at ({x}, {y})",
            "coordinates": [x, y]
        }
    
    def _action_type(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute type action."""
        text = action.get("value", "")
        
        if not text:
            return {"success": False, "message": "No text to type"}
        
        self.input_sim.type_text(text)
        
        return {"success": True, "message": f"Typed: {text}"}
    
    def _action_key(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute key press action."""
        key = action.get("value", "")
        
        if not key:
            return {"success": False, "message": "No key specified"}
        
        # Handle key combinations (e.g., "ctrl+c")
        if "+" in key:
            keys = key.split("+")
            self.input_sim.hotkey(*keys)
        else:
            self.input_sim.press_key(key)
        
        return {"success": True, "message": f"Pressed: {key}"}
    
    def _action_shell(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command action."""
        command = action.get("target", "") or action.get("value", "")
        
        if not command:
            return {"success": False, "message": "No command specified"}
        
        # Execute via PowerShell
        code, stdout, stderr = self.shell.execute_powershell(command)
        
        success = (code == 0)
        
        return {
            "success": success,
            "message": f"Executed: {command}",
            "output": stdout,
            "error": stderr,
            "return_code": code
        }
    
    def _action_open(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute open application action."""
        app = action.get("target", "") or action.get("value", "")
        
        if not app:
            return {"success": False, "message": "No application specified"}
        
        success = self.shell.open_application(app)
        
        return {
            "success": success,
            "message": f"Opened: {app}" if success else f"Failed to open: {app}"
        }
    
    def _action_wait(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wait action."""
        duration = action.get("value", 1)
        
        try:
            duration = float(duration)
        except:
            duration = 1.0
        
        time.sleep(duration)
        
        return {"success": True, "message": f"Waited {duration} seconds"}
    
    def _action_move(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mouse move action."""
        target = action.get("target", "")
        
        if isinstance(target, (list, tuple)) and len(target) >= 2:
            x, y = target[0], target[1]
            self.input_sim.move_to(x, y)
            return {"success": True, "message": f"Moved to ({x}, {y})"}
        
        return {"success": False, "message": "Invalid move target"}
    
    def _action_scroll(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scroll action."""
        clicks = action.get("value", 3)
        direction = action.get("direction", "down")
        
        try:
            clicks = int(clicks)
        except:
            clicks = 3
        
        self.input_sim.scroll(clicks, direction)
        
        return {"success": True, "message": f"Scrolled {clicks} clicks {direction}"}


# Global action executor
action_executor = ActionExecutor()
