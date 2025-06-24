#!/usr/bin/env python3
"""
Configuration Schema for W4L.

Defines the structure, validation rules, and access control for all configuration settings.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json

class SettingAccess(Enum):
    """Defines who can modify a setting."""
    SYSTEM_ONLY = "system_only"      # Only system can change (read-only for users)
    USER_EDITABLE = "user_editable"  # Users can modify in settings UI
    ADVANCED = "advanced"            # Advanced users only (hidden by default)
    DEPRECATED = "deprecated"        # Legacy setting, will be removed

class SettingType(Enum):
    """Defines the data type of a setting."""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

@dataclass
class SettingDefinition:
    """Definition of a configuration setting."""
    key: str
    type: SettingType
    access: SettingAccess
    default: Any
    description: str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    unit: Optional[str] = None
    category: str = "general"
    deprecated: bool = False
    replacement: Optional[str] = None

class ConfigSchema:
    """Defines the complete configuration schema for W4L."""
    
    def __init__(self):
        """Initialize the configuration schema."""
        self.settings: Dict[str, SettingDefinition] = {}
        self._define_schema()
    
    def _define_schema(self) -> None:
        """Define all configuration settings with their rules."""
        
        # =============================================================================
        # AUDIO SETTINGS
        # =============================================================================
        
        # System-controlled audio settings (not user-editable)
        self._add_setting(SettingDefinition(
            key="audio.sample_rate",
            type=SettingType.INTEGER,
            access=SettingAccess.SYSTEM_ONLY,
            default=16000,
            description="Audio sample rate in Hz (fixed for Whisper compatibility)",
            allowed_values=[16000],  # Only 16kHz supported for Whisper
            unit="Hz",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.channels",
            type=SettingType.INTEGER,
            access=SettingAccess.SYSTEM_ONLY,
            default=1,
            description="Number of audio channels (fixed for Whisper compatibility)",
            allowed_values=[1],  # Only mono supported for Whisper
            unit="channels",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.bit_depth",
            type=SettingType.INTEGER,
            access=SettingAccess.SYSTEM_ONLY,
            default=16,
            description="Audio bit depth (fixed for Whisper compatibility)",
            allowed_values=[16],  # Only 16-bit supported for Whisper
            unit="bits",
            category="audio"
        ))
        
        # User-editable audio settings
        self._add_setting(SettingDefinition(
            key="audio.buffer_size",
            type=SettingType.INTEGER,
            access=SettingAccess.USER_EDITABLE,
            default=5,
            description="Audio buffer size in seconds",
            min_value=1,
            max_value=30,
            unit="seconds",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.capture_mode",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="streaming",
            description="Audio capture mode",
            allowed_values=["streaming", "file_based"],
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.device",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="default",
            description="Default audio input device",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.silence_threshold",
            type=SettingType.FLOAT,
            access=SettingAccess.USER_EDITABLE,
            default=0.01,
            description="Silence detection threshold",
            min_value=0.001,
            max_value=1.0,
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.silence_duration",
            type=SettingType.FLOAT,
            access=SettingAccess.USER_EDITABLE,
            default=5.0,
            description="Silence duration before auto-stop",
            min_value=1.0,
            max_value=30.0,
            unit="seconds",
            category="audio"
        ))
        
        # Advanced silence detection settings
        self._add_setting(SettingDefinition(
            key="audio.silence_strategy",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="hybrid",
            description="Silence detection strategy",
            allowed_values=["rms", "spectral", "adaptive", "hybrid"],
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.noise_learning_duration",
            type=SettingType.FLOAT,
            access=SettingAccess.USER_EDITABLE,
            default=3.0,
            description="Duration to learn background noise",
            min_value=1.0,
            max_value=10.0,
            unit="seconds",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.noise_margin",
            type=SettingType.FLOAT,
            access=SettingAccess.USER_EDITABLE,
            default=1.5,
            description="Multiplier above learned noise floor",
            min_value=1.1,
            max_value=3.0,
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.adaptation_rate",
            type=SettingType.FLOAT,
            access=SettingAccess.ADVANCED,
            default=0.1,
            description="Rate of noise floor adaptation",
            min_value=0.01,
            max_value=0.5,
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.min_speech_duration",
            type=SettingType.FLOAT,
            access=SettingAccess.ADVANCED,
            default=0.5,
            description="Minimum speech duration before silence detection",
            min_value=0.1,
            max_value=2.0,
            unit="seconds",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.enable_adaptive_detection",
            type=SettingType.BOOLEAN,
            access=SettingAccess.USER_EDITABLE,
            default=True,
            description="Enable adaptive noise floor detection",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.enable_spectral_detection",
            type=SettingType.BOOLEAN,
            access=SettingAccess.ADVANCED,
            default=True,
            description="Enable spectral analysis for silence detection",
            category="audio"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio.save_path",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="",
            description="Directory to save audio files in file-based mode",
            category="audio"
        ))
        
        # =============================================================================
        # GUI SETTINGS
        # =============================================================================
        
        self._add_setting(SettingDefinition(
            key="gui.window_position",
            type=SettingType.OBJECT,
            access=SettingAccess.SYSTEM_ONLY,
            default={"x": 100, "y": 100},
            description="Window position (managed by system)",
            category="gui"
        ))
        
        self._add_setting(SettingDefinition(
            key="gui.always_on_top",
            type=SettingType.BOOLEAN,
            access=SettingAccess.USER_EDITABLE,
            default=True,
            description="Keep window always on top",
            category="gui"
        ))
        
        self._add_setting(SettingDefinition(
            key="gui.theme",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="default",
            description="Application theme",
            allowed_values=["default", "dark", "light"],
            category="gui"
        ))
        
        self._add_setting(SettingDefinition(
            key="gui.window_width",
            type=SettingType.INTEGER,
            access=SettingAccess.SYSTEM_ONLY,
            default=400,
            description="Window width (managed by system)",
            min_value=300,
            max_value=800,
            unit="pixels",
            category="gui"
        ))
        
        self._add_setting(SettingDefinition(
            key="gui.window_height",
            type=SettingType.INTEGER,
            access=SettingAccess.SYSTEM_ONLY,
            default=300,
            description="Window height (managed by system)",
            min_value=200,
            max_value=600,
            unit="pixels",
            category="gui"
        ))
        
        # =============================================================================
        # TRANSCRIPTION SETTINGS
        # =============================================================================
        
        self._add_setting(SettingDefinition(
            key="transcription.model",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="tiny",
            description="Whisper model size",
            allowed_values=["tiny", "base", "small", "medium", "large"],
            category="transcription"
        ))
        
        self._add_setting(SettingDefinition(
            key="transcription.language",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="auto",
            description="Transcription language (auto for auto-detect)",
            category="transcription"
        ))
        
        self._add_setting(SettingDefinition(
            key="transcription.auto_paste",
            type=SettingType.BOOLEAN,
            access=SettingAccess.USER_EDITABLE,
            default=True,
            description="Automatically paste transcribed text",
            category="transcription"
        ))
        
        # =============================================================================
        # SYSTEM SETTINGS
        # =============================================================================
        
        self._add_setting(SettingDefinition(
            key="system.autostart",
            type=SettingType.BOOLEAN,
            access=SettingAccess.USER_EDITABLE,
            default=False,
            description="Start W4L automatically on system startup",
            category="system"
        ))
        
        self._add_setting(SettingDefinition(
            key="system.hotkey",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="ctrl+alt+w",
            description="Global hotkey to show window",
            category="system"
        ))
        
        self._add_setting(SettingDefinition(
            key="system.log_level",
            type=SettingType.STRING,
            access=SettingAccess.ADVANCED,
            default="INFO",
            description="Logging level",
            allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            category="system"
        ))
        
        # =============================================================================
        # HOTKEY SETTINGS
        # =============================================================================
        
        self._add_setting(SettingDefinition(
            key="hotkeys.show_window",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="ctrl+alt+w",
            description="Hotkey to show/hide window",
            category="hotkeys"
        ))
        
        self._add_setting(SettingDefinition(
            key="hotkeys.start_recording",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="ctrl+alt+r",
            description="Hotkey to start recording",
            category="hotkeys"
        ))
        
        self._add_setting(SettingDefinition(
            key="hotkeys.stop_recording",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="ctrl+alt+s",
            description="Hotkey to stop recording",
            category="hotkeys"
        ))
        
        self._add_setting(SettingDefinition(
            key="hotkeys.cancel_recording",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="escape",
            description="Hotkey to cancel recording",
            category="hotkeys"
        ))
        
        # =============================================================================
        # AUDIO DEVICE SETTINGS
        # =============================================================================
        
        self._add_setting(SettingDefinition(
            key="audio_devices.preferred_input",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="default",
            description="Preferred audio input device",
            category="audio_devices"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio_devices.preferred_output",
            type=SettingType.STRING,
            access=SettingAccess.USER_EDITABLE,
            default="default",
            description="Preferred audio output device",
            category="audio_devices"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio_devices.available_devices",
            type=SettingType.ARRAY,
            access=SettingAccess.SYSTEM_ONLY,
            default=[],
            description="List of available audio devices (managed by system)",
            category="audio_devices"
        ))
        
        self._add_setting(SettingDefinition(
            key="audio_devices.last_used",
            type=SettingType.STRING,
            access=SettingAccess.SYSTEM_ONLY,
            default="default",
            description="Last used audio device (managed by system)",
            category="audio_devices"
        ))
    
    def _add_setting(self, setting: SettingDefinition) -> None:
        """Add a setting definition to the schema."""
        self.settings[setting.key] = setting
    
    def get_setting(self, key: str) -> Optional[SettingDefinition]:
        """Get a setting definition by key."""
        return self.settings.get(key)
    
    def get_user_editable_settings(self) -> List[SettingDefinition]:
        """Get all user-editable settings."""
        return [
            setting for setting in self.settings.values()
            if setting.access == SettingAccess.USER_EDITABLE
        ]
    
    def get_advanced_settings(self) -> List[SettingDefinition]:
        """Get all advanced settings."""
        return [
            setting for setting in self.settings.values()
            if setting.access == SettingAccess.ADVANCED
        ]
    
    def get_settings_by_category(self, category: str) -> List[SettingDefinition]:
        """Get all settings in a specific category."""
        return [
            setting for setting in self.settings.values()
            if setting.category == category
        ]
    
    def validate_value(self, key: str, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against the schema.
        
        Returns:
            (is_valid, error_message)
        """
        setting = self.get_setting(key)
        if not setting:
            return False, f"Unknown setting: {key}"
        
        # Type validation
        if setting.type == SettingType.INTEGER and not isinstance(value, int):
            return False, f"Setting {key} must be an integer"
        elif setting.type == SettingType.FLOAT and not isinstance(value, (int, float)):
            return False, f"Setting {key} must be a number"
        elif setting.type == SettingType.STRING and not isinstance(value, str):
            return False, f"Setting {key} must be a string"
        elif setting.type == SettingType.BOOLEAN and not isinstance(value, bool):
            return False, f"Setting {key} must be a boolean"
        
        # Range validation (only for numeric types)
        if setting.min_value is not None and isinstance(value, (int, float)):
            if value < setting.min_value:
                return False, f"Setting {key} must be >= {setting.min_value}"
        if setting.max_value is not None and isinstance(value, (int, float)):
            if value > setting.max_value:
                return False, f"Setting {key} must be <= {setting.max_value}"
        
        # Allowed values validation
        if setting.allowed_values is not None and value not in setting.allowed_values:
            return False, f"Setting {key} must be one of: {setting.allowed_values}"
        
        return True, None
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get the complete default configuration."""
        config = {}
        for setting in self.settings.values():
            keys = setting.key.split('.')
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = setting.default
        return config
    
    def is_user_editable(self, key: str) -> bool:
        """Check if a setting is user-editable."""
        setting = self.get_setting(key)
        return setting is not None and setting.access == SettingAccess.USER_EDITABLE
    
    def is_system_only(self, key: str) -> bool:
        """Check if a setting is system-only."""
        setting = self.get_setting(key)
        return setting is not None and setting.access == SettingAccess.SYSTEM_ONLY 