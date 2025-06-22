#!/usr/bin/env python3
"""
Configuration Manager for W4L.

Handles configuration file operations, directory structure, and error recovery.
Now uses a unified schema-based approach to prevent configuration duplication.
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .config_schema import ConfigSchema, SettingAccess

class ConfigManager:
    """Manages W4L configuration files and directory structure."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.logger = logging.getLogger("w4l.config")
        
        # Initialize schema
        self.schema = ConfigSchema()
        
        # Configuration directory structure - UNIFIED LOCATION
        self.config_dir = os.path.expanduser("~/.config/w4l/")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.logs_dir = os.path.join(self.config_dir, "logs/")
        
        # Single configuration data structure
        self.config: Dict[str, Any] = {}
        
        # Initialize configuration
        self._ensure_directory_structure()
        self.load_or_create_config()
    
    def _ensure_directory_structure(self) -> None:
        """Create the configuration directory structure if it doesn't exist."""
        try:
            # Create main config directory
            os.makedirs(self.config_dir, mode=0o755, exist_ok=True)
            self.logger.info(f"Config directory ensured: {self.config_dir}")
            
            # Create logs subdirectory
            os.makedirs(self.logs_dir, mode=0o755, exist_ok=True)
            self.logger.info(f"Logs directory ensured: {self.logs_dir}")
            
            # Set proper permissions
            os.chmod(self.config_dir, 0o755)
            os.chmod(self.logs_dir, 0o755)
            
        except PermissionError as e:
            self.logger.error(f"Permission denied creating config directory: {e}")
            raise
        except OSError as e:
            self.logger.error(f"Failed to create config directory structure: {e}")
            raise
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration structure from schema."""
        return self.schema.get_default_config()
    
    def load_or_create_config(self) -> None:
        """Load existing configuration or create new one with defaults."""
        try:
            if os.path.exists(self.config_file):
                self.load_config()
            else:
                self.create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load or create config: {e}")
            self.create_default_config()
    
    def create_default_config(self) -> None:
        """Create configuration file with default values from schema."""
        try:
            # Create main config from schema
            self.config = self.get_default_config()
            self.save_config()
            
            self.logger.info("Default configuration file created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create default config: {e}")
            raise
    
    def load_config(self) -> None:
        """Load configuration from file with error handling."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Validate and repair configuration
            self.validate_and_repair_config()
            
            self.logger.info("Configuration loaded successfully")
            
        except FileNotFoundError:
            self.logger.warning("Config file not found, creating default")
            self.create_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            self.backup_corrupted_file(self.config_file)
            self.create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.create_default_config()
    
    def save_config(self) -> None:
        """Save configuration to file with atomic write."""
        try:
            # Create temporary file for atomic write
            temp_file = f"{self.config_file}.tmp"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            shutil.move(temp_file, self.config_file)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
    
    def validate_and_repair_config(self) -> None:
        """Validate configuration and repair missing/invalid values using schema."""
        default_config = self.get_default_config()
        
        # Check if all required sections exist
        for section, defaults in default_config.items():
            if section not in self.config:
                self.config[section] = defaults.copy()
                self.logger.info(f"Added missing section: {section}")
            else:
                # Check if all required keys exist in section
                for key, default_value in defaults.items():
                    if key not in self.config[section]:
                        self.config[section][key] = default_value
                        self.logger.info(f"Added missing key: {section}.{key}")
                    else:
                        # Validate the value against schema
                        full_key = f"{section}.{key}"
                        is_valid, error_msg = self.schema.validate_value(full_key, self.config[section][key])
                        if not is_valid:
                            self.logger.warning(f"Invalid value for {full_key}: {error_msg}, using default")
                            self.config[section][key] = default_value
    
    def backup_corrupted_file(self, file_path: str) -> None:
        """Create a backup of a corrupted configuration file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup of corrupted file: {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
    
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value safely."""
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception as e:
            self.logger.error(f"Failed to get config value {section}.{key}: {e}")
            return default
    
    def set_config_value(self, section: str, key: str, value: Any) -> bool:
        """
        Set a configuration value and save.
        
        Returns:
            bool: True if value was set successfully, False if validation failed or setting is system-only
        """
        try:
            full_key = f"{section}.{key}"
            
            # Check if setting is user-editable
            if not self.schema.is_user_editable(full_key):
                self.logger.warning(f"Cannot set system-only setting: {full_key}")
                return False
            
            # Validate the value
            is_valid, error_msg = self.schema.validate_value(full_key, value)
            if not is_valid:
                self.logger.error(f"Invalid value for {full_key}: {error_msg}")
                return False
            
            # Set the value
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
            self.save_config()
            
            self.logger.info(f"Set config value: {full_key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set config value {section}.{key}: {e}")
            return False
    
    def get_user_editable_settings(self) -> Dict[str, Any]:
        """Get all user-editable settings for the settings UI."""
        editable_settings = {}
        
        for setting in self.schema.get_user_editable_settings():
            keys = setting.key.split('.')
            section, key = keys[0], keys[1]
            
            if section not in editable_settings:
                editable_settings[section] = {}
            
            editable_settings[section][key] = {
                'value': self.get_config_value(section, key, setting.default),
                'definition': setting
            }
        
        return editable_settings
    
    def get_advanced_settings(self) -> Dict[str, Any]:
        """Get all advanced settings for the advanced settings UI."""
        advanced_settings = {}
        
        for setting in self.schema.get_advanced_settings():
            keys = setting.key.split('.')
            section, key = keys[0], keys[1]
            
            if section not in advanced_settings:
                advanced_settings[section] = {}
            
            advanced_settings[section][key] = {
                'value': self.get_config_value(section, key, setting.default),
                'definition': setting
            }
        
        return advanced_settings
    
    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a specific category."""
        category_settings = {}
        
        for setting in self.schema.get_settings_by_category(category):
            keys = setting.key.split('.')
            section, key = keys[0], keys[1]
            
            if section not in category_settings:
                category_settings[section] = {}
            
            category_settings[section][key] = {
                'value': self.get_config_value(section, key, setting.default),
                'definition': setting
            }
        
        return category_settings
    
    def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """Reset settings to defaults, optionally for a specific category."""
        if category:
            # Reset specific category
            category_settings = self.schema.get_settings_by_category(category)
            for setting in category_settings:
                keys = setting.key.split('.')
                section, key = keys[0], keys[1]
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = setting.default
            self.logger.info(f"Reset {category} settings to defaults")
        else:
            # Reset all settings
            self.config = self.get_default_config()
            self.logger.info("Reset all settings to defaults")
        
        self.save_config()
    
    def get_config_dir(self) -> str:
        """Get the configuration directory path."""
        return self.config_dir
    
    def get_logs_dir(self) -> str:
        """Get the logs directory path."""
        return self.logs_dir
    
    def get_schema(self) -> ConfigSchema:
        """Get the configuration schema."""
        return self.schema
    
    # Legacy compatibility methods (for existing code)
    def get_audio_devices(self) -> Dict[str, Any]:
        """Get audio devices configuration (legacy compatibility)."""
        return self.get_settings_by_category("audio_devices")
    
    def get_hotkeys(self) -> Dict[str, Any]:
        """Get hotkeys configuration (legacy compatibility)."""
        return self.get_settings_by_category("hotkeys") 