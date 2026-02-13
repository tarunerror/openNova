"""
Input Simulator - Controls mouse and keyboard.
"""
import logging
import time
from typing import Tuple, List

logger = logging.getLogger("InputSim")


class InputSimulator:
    """Simulates mouse and keyboard input."""
    
    def __init__(self):
        """Initialize input simulator."""
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if pyautogui is available."""
        try:
            import pyautogui
            # Disable fail-safe for automation
            pyautogui.FAILSAFE = False
            logger.info("Input simulator initialized")
            return True
        except ImportError:
            logger.error("pyautogui not installed. Install with: pip install pyautogui")
            return False
    
    def click(self, x: int, y: int, button: str = "left", clicks: int = 1, interval: float = 0.0):
        """
        Click at coordinates.
        
        Args:
            x, y: Screen coordinates
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks
            interval: Interval between clicks
        """
        if not self.available:
            logger.error("Input simulator not available")
            return
        
        try:
            import pyautogui
            
            logger.info(f"Clicking at ({x}, {y}) with {button} button")
            pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
            
        except Exception as e:
            logger.error(f"Error clicking: {e}")
    
    def move_to(self, x: int, y: int, duration: float = 0.5, smooth: bool = True):
        """
        Move mouse to coordinates.
        
        Args:
            x, y: Target coordinates
            duration: Time to move (seconds)
            smooth: Use smooth movement (bezier curve)
        """
        if not self.available:
            return
        
        try:
            import pyautogui
            
            if smooth:
                # Use tweening for smooth movement
                pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)
            else:
                pyautogui.moveTo(x, y, duration=duration)
            
            logger.debug(f"Moved to ({x}, {y})")
            
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")
    
    def drag_to(self, x: int, y: int, duration: float = 1.0, button: str = "left"):
        """
        Drag mouse to coordinates.
        
        Args:
            x, y: Target coordinates
            duration: Time to drag
            button: Mouse button to hold
        """
        if not self.available:
            return
        
        try:
            import pyautogui
            
            logger.info(f"Dragging to ({x}, {y})")
            pyautogui.dragTo(x, y, duration=duration, button=button)
            
        except Exception as e:
            logger.error(f"Error dragging: {e}")
    
    def type_text(self, text: str, interval: float = 0.05):
        """
        Type text.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
        """
        if not self.available:
            return
        
        try:
            import pyautogui
            
            logger.info(f"Typing text: {text[:50]}...")
            pyautogui.write(text, interval=interval)
            
        except Exception as e:
            logger.error(f"Error typing text: {e}")
    
    def press_key(self, key: str, presses: int = 1, interval: float = 0.0):
        """
        Press a key.
        
        Args:
            key: Key name (e.g., 'enter', 'esc', 'tab')
            presses: Number of presses
            interval: Interval between presses
        """
        if not self.available:
            return
        
        try:
            import pyautogui
            
            logger.info(f"Pressing key: {key}")
            pyautogui.press(key, presses=presses, interval=interval)
            
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
    
    def hotkey(self, *keys):
        """
        Press a combination of keys.
        
        Args:
            keys: Keys to press together (e.g., 'ctrl', 'c')
        """
        if not self.available:
            return
        
        try:
            import pyautogui
            
            logger.info(f"Pressing hotkey: {'+'.join(keys)}")
            pyautogui.hotkey(*keys)
            
        except Exception as e:
            logger.error(f"Error pressing hotkey: {e}")
    
    def scroll(self, clicks: int, direction: str = "down"):
        """
        Scroll mouse wheel.
        
        Args:
            clicks: Number of scroll clicks (positive = up, negative = down)
            direction: 'up' or 'down' (alternative to signed clicks)
        """
        if not self.available:
            return
        
        try:
            import pyautogui
            
            if direction == "down" and clicks > 0:
                clicks = -clicks
            
            logger.info(f"Scrolling {abs(clicks)} clicks {direction}")
            pyautogui.scroll(clicks)
            
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """
        Get current mouse position.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        if not self.available:
            return (0, 0)
        
        try:
            import pyautogui
            return pyautogui.position()
        except:
            return (0, 0)
    
    def screenshot_region(self, x: int, y: int, width: int, height: int, filename: str = None):
        """
        Take a screenshot of a region.
        
        Args:
            x, y: Top-left corner
            width, height: Region size
            filename: Optional save path
            
        Returns:
            Path to screenshot or None
        """
        if not self.available:
            return None
        
        try:
            import pyautogui
            
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            if filename:
                screenshot.save(filename)
                return filename
            
            return screenshot
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None


# Global input simulator instance
input_sim = InputSimulator()
