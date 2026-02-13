"""
Shell Executor - Executes system commands.
"""
import logging
import subprocess
from typing import Tuple, List, Optional
from src.core.config import config

logger = logging.getLogger("Shell")


class ShellExecutor:
    """Executes shell commands with safety checks."""
    
    def __init__(self):
        """Initialize shell executor."""
        self.blacklist = config.get("safety.blacklist_commands", [])
        logger.info("Shell executor initialized")
    
    def is_dangerous(self, command: str) -> bool:
        """
        Check if a command is dangerous.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is blacklisted
        """
        command_lower = command.lower()
        
        for blacklisted in self.blacklist:
            if blacklisted.lower() in command_lower:
                logger.warning(f"Dangerous command detected: {command}")
                return True
        
        return False
    
    def execute_powershell(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        Execute a PowerShell command.
        
        Args:
            command: PowerShell command
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if self.is_dangerous(command):
            logger.error(f"Blocked dangerous PowerShell command: {command}")
            return (-1, "", "Command blocked for safety")
        
        try:
            logger.info(f"Executing PowerShell: {command}")
            
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.info(f"PowerShell completed with code: {result.returncode}")
            
            return (result.returncode, result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            logger.error(f"PowerShell command timed out: {command}")
            return (-1, "", "Command timed out")
        except Exception as e:
            logger.error(f"Error executing PowerShell: {e}")
            return (-1, "", str(e))
    
    def execute_cmd(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        Execute a CMD command.
        
        Args:
            command: Cmd command
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if self.is_dangerous(command):
            logger.error(f"Blocked dangerous CMD command: {command}")
            return (-1, "", "Command blocked for safety")
        
        try:
            logger.info(f"Executing CMD: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.info(f"CMD completed with code: {result.returncode}")
            
            return (result.returncode, result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            logger.error(f"CMD command timed out: {command}")
            return (-1, "", "Command timed out")
        except Exception as e:
            logger.error(f"Error executing CMD: {e}")
            return (-1, "", str(e))
    
    def open_application(self, app_name: str) -> bool:
        """
        Open an application.
        
        Args:
            app_name: Application name (e.g., 'chrome', 'notepad')
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Opening application: {app_name}")
            
            # Try to start the application
            result = subprocess.Popen(
                app_name,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening application: {e}")
            return False
    
    def execute_python(self, code: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        Execute Python code.
        
        Args:
            code: Python code to execute
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if self.is_dangerous(code):
            logger.error("Blocked dangerous Python code")
            return (-1, "", "Code blocked for safety")
        
        try:
            logger.info("Executing Python code")
            
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return (result.returncode, result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            logger.error("Python code timed out")
            return (-1, "", "Code timed out")
        except Exception as e:
            logger.error(f"Error executing Python: {e}")
            return (-1, "", str(e))
    
    def get_system_info(self) -> dict:
        """
        Get system information.
        
        Returns:
            Dictionary with system info
        """
        try:
            import platform
            
            return {
                "os": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
        except:
            return {}


# Global shell executor instance
shell_executor = ShellExecutor()
