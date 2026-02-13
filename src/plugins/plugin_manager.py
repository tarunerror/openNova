"""
Plugin manager for loading and managing skills.
"""
import os
import sys
import importlib.util
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .skill_base import Skill

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages loading, unloading, and executing skills.
    """
    
    def __init__(self, skills_dir: str = "./skills"):
        """
        Initialize the plugin manager.
        
        Args:
            skills_dir: Directory containing skill modules
        """
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        logger.info(f"Plugin manager initialized with skills dir: {self.skills_dir}")
    
    def load_all_skills(self):
        """
        Load all skills from the skills directory.
        """
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created skills directory: {self.skills_dir}")
            return
        
        # Find all Python files in the skills directory
        skill_files = list(self.skills_dir.glob("*.py"))
        
        if not skill_files:
            logger.info("No skill files found in skills directory")
            return
        
        for skill_file in skill_files:
            if skill_file.name.startswith("_"):
                continue  # Skip private files
            
            try:
                self._load_skill_from_file(skill_file)
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_file}: {e}")
    
    def _load_skill_from_file(self, file_path: Path):
        """
        Load a skill from a Python file.
        
        Args:
            file_path: Path to the skill Python file
        """
        module_name = file_path.stem
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.error(f"Could not load spec for {file_path}")
            return
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find all Skill subclasses in the module
        skill_classes = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Skill) and 
                attr is not Skill):
                skill_classes.append(attr)
        
        if not skill_classes:
            logger.warning(f"No Skill subclasses found in {file_path}")
            return
        
        # Instantiate all skill classes found
        for skill_class in skill_classes:
            try:
                skill_instance = skill_class()
                skill_instance.on_load()
                self.skills[skill_instance.name] = skill_instance
                logger.info(f"Loaded skill: {skill_instance.name} v{skill_instance.version} by {skill_instance.author}")
            except Exception as e:
                logger.error(f"Failed to instantiate skill {skill_class.__name__}: {e}")
    
    def unload_skill(self, skill_name: str):
        """
        Unload a specific skill.
        
        Args:
            skill_name: Name of the skill to unload
        """
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.on_unload()
            del self.skills[skill_name]
            logger.info(f"Unloaded skill: {skill_name}")
        else:
            logger.warning(f"Skill not found: {skill_name}")
    
    def reload_skill(self, skill_name: str):
        """
        Reload a specific skill.
        
        Args:
            skill_name: Name of the skill to reload
        """
        if skill_name in self.skills:
            self.unload_skill(skill_name)
        self.load_all_skills()
    
    def get_skill_for_input(self, user_input: str) -> Optional[Skill]:
        """
        Find the first skill that can handle the given input.
        
        Args:
            user_input: The user's voice command
            
        Returns:
            The skill that can handle the input, or None
        """
        for skill in self.skills.values():
            if skill.enabled and skill.can_handle(user_input):
                return skill
        return None
    
    def execute_skill(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Find and execute the appropriate skill for the given input.
        
        Args:
            user_input: The user's voice command
            context: Optional context dictionary
            
        Returns:
            Result dictionary from the skill, or None if no skill can handle it
        """
        skill = self.get_skill_for_input(user_input)
        if skill:
            logger.info(f"Executing skill: {skill.name}")
            try:
                result = skill.execute(user_input, context)
                return result
            except Exception as e:
                logger.error(f"Error executing skill {skill.name}: {e}")
                return {
                    "success": False,
                    "response": f"Error executing skill: {str(e)}",
                    "data": None
                }
        return None
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """
        Get information about all loaded skills.
        
        Returns:
            List of dictionaries containing skill information
        """
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "version": skill.version,
                "author": skill.author,
                "enabled": skill.enabled,
                "examples": skill.get_examples()
            }
            for skill in self.skills.values()
        ]
    
    def enable_skill(self, skill_name: str):
        """Enable a skill."""
        if skill_name in self.skills:
            self.skills[skill_name].enabled = True
            logger.info(f"Enabled skill: {skill_name}")
    
    def disable_skill(self, skill_name: str):
        """Disable a skill."""
        if skill_name in self.skills:
            self.skills[skill_name].enabled = False
            logger.info(f"Disabled skill: {skill_name}")
