"""
Audio device configuration for W4L.

Handles device selection, buffer management, and configuration persistence.
Supports both streaming and file-based audio capture approaches.
"""

import json
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

from .device_detector import AudioDeviceDetector, AudioDevice


@dataclass
class AudioConfig:
    """Configuration for audio capture and processing."""
    
    # Device settings
    device_id: int = -1  # -1 means use default
    device_name: str = ""
    
    # Buffer settings
    buffer_size_seconds: float = 5.0  # Default 5 seconds
    sample_rate: int = 16000  # 16kHz for Whisper
    channels: int = 1  # Mono for speech recognition
    
    # Capture mode
    use_streaming: bool = True  # True for real-time, False for file-based
    file_buffer_path: str = "/tmp/w4l_audio_buffer.wav"  # Fallback file path
    
    # Processing settings
    enable_noise_reduction: bool = False
    enable_auto_gain: bool = True
    
    # UI settings
    show_waveform: bool = True
    waveform_update_rate: float = 30.0  # Hz


class AudioDeviceManager:
    """
    Manages audio device selection and configuration.
    
    Provides functionality to:
    - Select and configure audio devices
    - Manage buffer settings
    - Persist configuration
    - Switch between streaming and file-based modes
    """
    
    def __init__(self, config_file: str = "~/.w4l/audio_config.json"):
        """
        Initialize the audio device manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.logger = logging.getLogger("w4l.audio.device_manager")
        self.detector = AudioDeviceDetector()
        self.config_file = Path(config_file).expanduser()
        self.config = AudioConfig()
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing configuration
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update config with loaded data
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                self.logger.info(f"Loaded configuration from {self.config_file}")
            else:
                self.logger.info("No existing configuration found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            config_data = asdict(self.config)
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Saved configuration to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def get_available_devices(self) -> List[AudioDevice]:
        """Get list of available input devices."""
        return self.detector.get_input_devices()
    
    def get_current_device(self) -> Optional[AudioDevice]:
        """Get the currently selected device."""
        if self.config.device_id >= 0:
            devices = self.detector.list_devices()
            for device in devices:
                if device.device_id == self.config.device_id:
                    return device
        
        # Fallback to default microphone
        return self.detector.get_default_microphone()
    
    def select_device(self, device_id: int) -> bool:
        """
        Select an audio device by ID.
        
        Args:
            device_id: ID of the device to select
            
        Returns:
            True if device was successfully selected, False otherwise
        """
        try:
            # Validate the device
            is_valid, message = self.detector.validate_device_for_w4l(device_id)
            if not is_valid:
                self.logger.error(f"Device {device_id} is not valid: {message}")
                return False
            
            # Get device info
            devices = self.detector.list_devices()
            selected_device = None
            for device in devices:
                if device.device_id == device_id:
                    selected_device = device
                    break
            
            if not selected_device:
                self.logger.error(f"Device {device_id} not found")
                return False
            
            # Update configuration
            self.config.device_id = device_id
            self.config.device_name = selected_device.name
            
            # Save configuration
            self.save_config()
            
            self.logger.info(f"Selected device: {selected_device.name} (ID: {device_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to select device {device_id}: {e}")
            return False
    
    def select_device_by_name(self, name: str) -> bool:
        """
        Select an audio device by name.
        
        Args:
            name: Name or partial name of the device
            
        Returns:
            True if device was successfully selected, False otherwise
        """
        device = self.detector.get_device_by_name(name)
        if device:
            return self.select_device(device.device_id)
        else:
            self.logger.error(f"No device found matching '{name}'")
            return False
    
    def set_buffer_size(self, seconds: float) -> None:
        """
        Set the buffer size in seconds.
        
        Args:
            seconds: Buffer size in seconds (1.0 to 30.0 recommended)
        """
        if 0.1 <= seconds <= 60.0:
            self.config.buffer_size_seconds = seconds
            self.save_config()
            self.logger.info(f"Buffer size set to {seconds} seconds")
        else:
            self.logger.warning(f"Buffer size {seconds} seconds is outside recommended range (0.1-60.0)")
    
    def set_capture_mode(self, use_streaming: bool) -> None:
        """
        Set the capture mode (streaming vs file-based).
        
        Args:
            use_streaming: True for real-time streaming, False for file-based
        """
        self.config.use_streaming = use_streaming
        self.save_config()
        mode = "streaming" if use_streaming else "file-based"
        self.logger.info(f"Capture mode set to {mode}")
    
    def get_buffer_size_samples(self) -> int:
        """
        Get buffer size in samples.
        
        Returns:
            Number of samples for the current buffer size
        """
        return int(self.config.buffer_size_seconds * self.config.sample_rate)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        current_device = self.get_current_device()
        
        return {
            "device": {
                "id": self.config.device_id,
                "name": current_device.name if current_device else "None",
                "is_default": self.config.device_id == -1
            },
            "buffer": {
                "size_seconds": self.config.buffer_size_seconds,
                "size_samples": self.get_buffer_size_samples(),
                "sample_rate": self.config.sample_rate,
                "channels": self.config.channels
            },
            "capture_mode": "streaming" if self.config.use_streaming else "file-based",
            "processing": {
                "noise_reduction": self.config.enable_noise_reduction,
                "auto_gain": self.config.enable_auto_gain
            },
            "ui": {
                "show_waveform": self.config.show_waveform,
                "waveform_update_rate": self.config.waveform_update_rate
            }
        }
    
    def print_config(self) -> None:
        """Print current configuration in a readable format."""
        summary = self.get_config_summary()
        
        print("\n=== W4L Audio Configuration ===")
        print(f"Device: {summary['device']['name']} (ID: {summary['device']['id']})")
        print(f"Buffer Size: {summary['buffer']['size_seconds']}s ({summary['buffer']['size_samples']} samples)")
        print(f"Sample Rate: {summary['buffer']['sample_rate']} Hz")
        print(f"Channels: {summary['buffer']['channels']}")
        print(f"Capture Mode: {summary['capture_mode']}")
        print(f"Noise Reduction: {summary['processing']['noise_reduction']}")
        print(f"Auto Gain: {summary['processing']['auto_gain']}")
        print(f"Show Waveform: {summary['ui']['show_waveform']}")
        print("=" * 35)
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = AudioConfig()
        self.save_config()
        self.logger.info("Configuration reset to defaults")
    
    def validate_configuration(self) -> tuple[bool, str]:
        """
        Validate the current configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if device is valid
            current_device = self.get_current_device()
            if not current_device:
                return False, "No valid input device selected"
            
            # Validate device
            is_valid, message = self.detector.validate_device_for_w4l(current_device.device_id)
            if not is_valid:
                return False, f"Selected device is not valid: {message}"
            
            # Check buffer size
            if self.config.buffer_size_seconds < 0.1:
                return False, "Buffer size too small (minimum 0.1 seconds)"
            
            if self.config.buffer_size_seconds > 60.0:
                return False, "Buffer size too large (maximum 60.0 seconds)"
            
            # Check sample rate
            if self.config.sample_rate < 8000:
                return False, "Sample rate too low (minimum 8000 Hz)"
            
            if self.config.sample_rate > 48000:
                return False, "Sample rate too high (maximum 48000 Hz)"
            
            return True, "Configuration is valid"
            
        except Exception as e:
            return False, f"Configuration validation error: {e}" 