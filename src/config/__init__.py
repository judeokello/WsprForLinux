"""
Configuration management module for W4L.

This module handles all configuration file operations, including:
- Configuration file structure and schema
- Default configuration values
- Configuration loading and saving
- Error handling and recovery
- Access control (user-editable vs system-only settings)
"""

from .config_manager import ConfigManager
from .config_schema import ConfigSchema, SettingDefinition, SettingAccess, SettingType

__all__ = [
    'ConfigManager',
    'ConfigSchema', 
    'SettingDefinition',
    'SettingAccess',
    'SettingType'
] 