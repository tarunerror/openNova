"""
Configuration management for the AI Agent.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Central configuration manager."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".ai_agent"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)
        
        self.settings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "llm": {
                "provider": "ollama",  # ollama, openai, anthropic, google
                "model": "llama3.2-vision",
                "api_key": "",
                "base_url": "http://localhost:11434"
            },
            "audio": {
                "wake_word_enabled": True,
                "wake_word": "hey agent",
                "hotkey": "ctrl+space",
                "stt_model": "base",  # tiny, base, small, medium, large
                "tts_voice": "en-US-AriaNeural"
            },
            "vision": {
                "primary_method": "accessibility",  # accessibility, vision, hybrid
                "fallback_to_vision": True
            },
            "ui": {
                "theme": "dark",
                "position": "top-right",
                "opacity": 0.95
            },
            "safety": {
                "confirm_dangerous_actions": True,
                "blacklist_commands": [
                    "format",
                    "rm -rf /",
                    "del /f /s /q C:\\",
                    "Format-Volume"
                ]
            },
            "memory": {
                "enabled": True,
                "max_history": 1000
            },
            "scheduler": {
                "enabled": True
            }
        }
    
    def save(self):
        """Save current configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        config = self.settings
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()


# Global configuration instance
config = Config()
