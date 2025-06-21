"""
Settings management for W4L.

Handles application configuration and user preferences.
"""

from typing import Any, Dict, Optional
import json
import os
from pathlib import Path


class Settings:
    """
    Application settings manager.
    
    Handles loading, saving, and accessing application configuration.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        self.config_file = config_file or self._get_default_config_path()
        self._settings: Dict[str, Any] = {}
        self._load_settings()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".config" / "w4l"
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "settings.json")
    
    def _load_settings(self) -> None:
        """Load settings from configuration file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self._settings = json.load(f)
            else:
                self._settings = self._get_default_settings()
                self._save_settings()
        except Exception as e:
            # Fallback to default settings if loading fails
            self._settings = self._get_default_settings()
    
    def _save_settings(self) -> None:
        """Save settings to configuration file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            # TODO: Log error when logging is implemented
            pass
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings."""
        return {
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024,
                "silence_threshold": 0.01,
                "silence_duration": 5.0
            },
            "hotkey": {
                "record": "Ctrl+Shift+R",
                "cancel": "Escape"
            },
            "ui": {
                "window_width": 400,
                "window_height": 300,
                "theme": "dark"
            },
            "transcription": {
                "model": "small",
                "language": "en"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key (supports dot notation like 'audio.sample_rate')
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        keys = key.split('.')
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key (supports dot notation like 'audio.sample_rate')
            value: Value to set
        """
        keys = key.split('.')
        current = self._settings
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        self._save_settings()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self._settings = self._get_default_settings()
        self._save_settings() 