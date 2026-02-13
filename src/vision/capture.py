"""
Screen Capture Module - Captures screenshots efficiently using MSS.
"""
import logging
from pathlib import Path
import tempfile
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger("Capture")


class ScreenCapture:
    """Handles screen capture operations."""
    
    def __init__(self):
        """Initialize screen capture."""
        self.sct = None
        self._init_capture()
    
    def _init_capture(self):
        """Initialize MSS screen capture."""
        try:
            import mss
            self.sct = mss.mss()
            logger.info("Screen capture initialized")
        except ImportError:
            logger.error("mss not installed. Install with: pip install mss")
            self.sct = None
        except Exception as e:
            logger.error(f"Error initializing screen capture: {e}")
            self.sct = None
    
    def capture_screen(self, monitor: int = 1) -> Optional[np.ndarray]:
        """
        Capture the screen.
        
        Args:
            monitor: Monitor number (1 = primary monitor, 0 = all monitors)
            
        Returns:
            Screenshot as numpy array (RGB)
        """
        if not self.sct:
            logger.error("Screen capture not available")
            return None
        
        try:
            # Capture
            sct_img = self.sct.grab(self.sct.monitors[monitor])
            
            # Convert to numpy array
            img = np.array(sct_img)
            
            # Convert from BGRA to RGB
            img = img[:, :, :3]
            img = img[:, :, ::-1]  # BGR to RGB
            
            logger.debug(f"Captured screen: {img.shape}")
            return img
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """
        Capture a specific region of the screen.
        
        Args:
            x, y: Top-left corner coordinates
            width, height: Region dimensions
            
        Returns:
            Screenshot as numpy array (RGB)
        """
        if not self.sct:
            return None
        
        try:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            sct_img = self.sct.grab(monitor)
            
            # Convert to numpy array
            img = np.array(sct_img)
            img = img[:, :, :3]
            img = img[:, :, ::-1]  # BGR to RGB
            
            return img
            
        except Exception as e:
            logger.error(f"Error capturing region: {e}")
            return None
    
    def save_screenshot(self, filename: str = None, monitor: int = 1) -> str:
        """
        Capture and save screenshot to file.
        
        Args:
            filename: Output filename (auto-generated if None)
            monitor: Monitor number
            
        Returns:
            Path to saved file
        """
        img = self.capture_screen(monitor)
        
        if img is None:
            return ""
        
        try:
            from PIL import Image
            
            if filename is None:
                temp_dir = Path(tempfile.gettempdir()) / "ai_agent_screenshots"
                temp_dir.mkdir(exist_ok=True)
                filename = str(temp_dir / f"screenshot_{int(Path().stat().st_mtime * 1000)}.png")
            
            # Save
            Image.fromarray(img).save(filename)
            logger.info(f"Screenshot saved: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return ""
    
    def get_screen_size(self, monitor: int = 1) -> Tuple[int, int]:
        """
        Get screen dimensions.
        
        Args:
            monitor: Monitor number
            
        Returns:
            Tuple of (width, height)
        """
        if not self.sct:
            return (0, 0)
        
        try:
            mon = self.sct.monitors[monitor]
            return (mon["width"], mon["height"])
        except:
            return (0, 0)
    
    def get_monitor_count(self) -> int:
        """Get number of monitors."""
        if not self.sct:
            return 0
        
        return len(self.sct.monitors) - 1  # -1 because index 0 is all monitors
    
    def __del__(self):
        """Cleanup."""
        if self.sct:
            try:
                self.sct.close()
            except:
                pass


# Global screen capture instance
screen_capture = ScreenCapture()
