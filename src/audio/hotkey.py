"""
Global Hotkey Handler
Listens for keyboard combinations to trigger the agent.
"""
import logging
from threading import Thread
from typing import Callable

logger = logging.getLogger("Hotkey")


class HotkeyHandler:
    """Handles global hotkey detection."""
    
    def __init__(self, hotkey="<ctrl>+<space>", callback: Callable = None):
        """
        Initialize hotkey handler.
        
        Args:
            hotkey: Hotkey combination (e.g., "<ctrl>+<space>")
            callback: Function to call when hotkey is pressed
        """
        self.hotkey = hotkey
        self.callback = callback
        self.listener = None
        self.running = False
        
        self._parse_hotkey()
    
    def _parse_hotkey(self):
        """Parse hotkey string into pynput format."""
        # Convert common formats
        self.hotkey_parsed = self.hotkey.replace("<", "").replace(">", "")
        
        logger.info(f"Hotkey configured: {self.hotkey}")
    
    def start(self):
        """Start listening for hotkey."""
        if self.running:
            logger.warning("Hotkey listener already running")
            return
        
        try:
            from pynput import keyboard
            
            # Parse hotkey combination
            def on_activate():
                """Called when hotkey is activated."""
                logger.info("Hotkey activated")
                if self.callback:
                    self.callback()
            
            # Create hotkey listener
            self.listener = keyboard.GlobalHotKeys({
                self.hotkey: on_activate
            })
            
            self.running = True
            self.listener.start()
            
            logger.info("Hotkey listener started")
            
        except ImportError:
            logger.error("pynput not installed. Install with: pip install pynput")
        except Exception as e:
            logger.error(f"Error starting hotkey listener: {e}")
    
    def stop(self):
        """Stop listening for hotkey."""
        if self.listener:
            self.listener.stop()
            self.running = False
            logger.info("Hotkey listener stopped")
    
    def __del__(self):
        """Destructor."""
        self.stop()
