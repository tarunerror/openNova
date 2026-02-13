"""
Base class for all skills/plugins.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class Skill(ABC):
    """
    Base class for all skills. Each skill can respond to voice commands
    and execute custom logic.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the skill.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.enabled = True
        logger.info(f"Initialized skill: {self.name}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this skill."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what this skill does."""
        pass
    
    @property
    def version(self) -> str:
        """Return the version of this skill."""
        return "1.0.0"
    
    @property
    def author(self) -> str:
        """Return the author of this skill."""
        return "Unknown"
    
    @abstractmethod
    def can_handle(self, user_input: str) -> bool:
        """
        Determine if this skill can handle the given user input.
        
        Args:
            user_input: The user's voice command (text)
            
        Returns:
            True if this skill can handle the input, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the skill's main logic.
        
        Args:
            user_input: The user's voice command (text)
            context: Optional context dictionary (screen data, memory, etc.)
            
        Returns:
            Dictionary containing:
                - success: bool
                - response: str (what to say back to user)
                - data: Any additional data
        """
        pass
    
    def on_load(self):
        """Called when the skill is first loaded."""
        pass
    
    def on_unload(self):
        """Called when the skill is unloaded."""
        pass
    
    def get_examples(self) -> List[str]:
        """
        Return example commands that this skill can handle.
        
        Returns:
            List of example user inputs
        """
        return []
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return the configuration schema for this skill.
        
        Returns:
            Dictionary describing expected configuration keys and types
        """
        return {}
