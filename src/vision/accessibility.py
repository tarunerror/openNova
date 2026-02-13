"""
Accessibility Inspector - Inspects UI elements using Windows UI Automation.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("Accessibility")


class AccessibilityInspector:
    """Inspects UI elements using Windows UI Automation."""
    
    def __init__(self):
        """Initialize accessibility inspector."""
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if pywinauto is available."""
        try:
            import pywinauto
            logger.info("Accessibility inspector initialized")
            return True
        except ImportError:
            logger.warning("pywinauto not installed. Install with: pip install pywinauto")
            return False
    
    def get_elements_at_point(self, x: int, y: int) -> List[Dict[str, Any]]:
        """
        Get UI elements at a specific point.
        
        Args:
            x, y: Screen coordinates
            
        Returns:
            List of element dictionaries
        """
        if not self.available:
            return []
        
        try:
            from pywinauto import Desktop
            
            # Get element at coordinates
            try:
                desktop = Desktop(backend="uia")
                element = desktop.from_point(x, y)
                
                return [self._element_to_dict(element)]
            except Exception as e:
                logger.debug(f"Could not get element at ({x}, {y}): {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting elements: {e}")
            return []
    
    def get_window_elements(self, window_title: str = None) -> List[Dict[str, Any]]:
        """
        Get all interactive elements in a window.
        
        Args:
            window_title: Window title (or None for foreground window)
            
        Returns:
            List of element dictionaries
        """
        if not self.available:
            return []
        
        try:
            from pywinauto import Desktop
            from pywinauto.findwindows import ElementNotFoundError
            
            desktop = Desktop(backend="uia")
            
            # Get window
            if window_title:
                try:
                    window = desktop.window(title_re=f".*{window_title}.*")
                except ElementNotFoundError:
                    logger.warning(f"Window not found: {window_title}")
                    return []
            else:
                # Get foreground window
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                window = desktop.window(handle=hwnd)
            
            # Get all controls
            elements = []
            try:
                controls = window.descendants()
                
                for ctrl in controls:
                    elem_dict = self._element_to_dict(ctrl)
                    if elem_dict:
                        elements.append(elem_dict)
                
            except Exception as e:
                logger.debug(f"Error getting descendants: {e}")
            
            logger.info(f"Found {len(elements)} UI elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error getting window elements: {e}")
            return []
    
    def _element_to_dict(self, element) -> Optional[Dict[str, Any]]:
        """Convert UI element to dictionary."""
        try:
            # Get element properties
            rect = element.rectangle()
            
            elem_dict = {
                "name": element.window_text(),
                "type": element.element_info.control_type,
                "x": rect.left,
                "y": rect.top,
                "width": rect.width(),
                "height": rect.height(),
                "center_x": rect.mid_point().x,
                "center_y": rect.mid_point().y,
                "enabled": element.is_enabled(),
                "visible": element.is_visible()
            }
            
            return elem_dict
            
        except Exception as e:
            logger.debug(f"Error converting element: {e}")
            return None
    
    def find_element_by_name(self, name: str, window_title: str = None) -> Optional[Dict[str, Any]]:
        """
        Find an element by name.
        
        Args:
            name: Element name (can be partial match)
            window_title: Optional window title
            
        Returns:
            Element dictionary or None
        """
        elements = self.get_window_elements(window_title)
        
        name_lower = name.lower()
        
        for elem in elements:
            elem_name = elem.get("name", "").lower()
            if name_lower in elem_name:
                return elem
        
        return None
    
    def find_buttons(self, window_title: str = None) -> List[Dict[str, Any]]:
        """
        Find all buttons in a window.
        
        Args:
            window_title: Optional window title
            
        Returns:
            List of button elements
        """
        elements = self.get_window_elements(window_title)
        
        buttons = [
            elem for elem in elements
            if "Button" in elem.get("type", "")
            and elem.get("visible", False)
        ]
        
        return buttons
    
    def click_element(self, element: Dict[str, Any]) -> bool:
        """
        Click on an element.
        
        Args:
            element: Element dictionary
            
        Returns:
            True if successful
        """
        try:
            import pyautogui
            
            x = element.get("center_x", 0)
            y = element.get("center_y", 0)
            
            if x > 0 and y > 0:
                pyautogui.click(x, y)
                logger.info(f"Clicked element: {element.get('name')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False


# Global accessibility inspector
accessibility = AccessibilityInspector()
