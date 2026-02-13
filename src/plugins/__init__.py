"""
Plugin system for extending the AI agent with custom skills.
"""
from .skill_base import Skill
from .plugin_manager import PluginManager

__all__ = ["Skill", "PluginManager"]
