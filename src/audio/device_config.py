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
import subprocess
import sys

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
            # Check if we have a valid device
            current_device = self.get_current_device()
            if not current_device:
                return False, "No input device available"
            
            # Validate the device
            is_valid, message = self.detector.validate_device_for_w4l(current_device.device_id)
            if not is_valid:
                return False, f"Device validation failed: {message}"
            
            # Check buffer settings
            if self.config.buffer_size_seconds < 0.1 or self.config.buffer_size_seconds > 60.0:
                return False, "Buffer size must be between 0.1 and 60.0 seconds"
            
            # Check sample rate
            if self.config.sample_rate < 8000 or self.config.sample_rate > 48000:
                return False, "Sample rate must be between 8000 and 48000 Hz"
            
            return True, "Configuration is valid"
            
        except Exception as e:
            return False, f"Configuration validation error: {e}"
    
    def auto_configure_default_device(self) -> bool:
        """
        Automatically select and configure the default microphone for W4L.
        
        This method:
        1. Finds the default microphone
        2. Validates it works with W4L
        3. Configures it with optimal settings
        4. Tests that it can actually record audio
        
        Returns:
            True if device was successfully configured, False otherwise
        """
        try:
            self.logger.info("Auto-configuring default microphone for W4L")
            
            # Get the default microphone
            default_device = self.detector.get_default_microphone()
            if not default_device:
                self.logger.error("No default microphone found")
                return False
            
            # Validate the device for W4L
            is_valid, message = self.detector.validate_device_for_w4l(default_device.device_id)
            if not is_valid:
                self.logger.error(f"Default microphone validation failed: {message}")
                return False
            
            # Configure the device
            success = self.configure_device_for_w4l(default_device)
            if not success:
                self.logger.error("Failed to configure default microphone")
                return False
            
            # Test the device can actually record
            if not self.test_device_recording():
                self.logger.error("Device recording test failed")
                return False
            
            self.logger.info(f"Successfully configured default microphone: {default_device.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Auto-configuration failed: {e}")
            return False
    
    def configure_device_for_w4l(self, device: AudioDevice) -> bool:
        """
        Configure a device with optimal settings for W4L.
        
        Args:
            device: AudioDevice to configure
            
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.logger.info(f"Configuring device {device.name} for W4L")
            
            # Update configuration with device info
            self.config.device_id = device.device_id
            self.config.device_name = device.name
            
            # Set optimal audio settings for Whisper
            self.config.sample_rate = 16000  # Whisper expects 16kHz
            self.config.channels = 1  # Mono for speech recognition
            
            # Set reasonable buffer size
            if self.config.buffer_size_seconds < 1.0:
                self.config.buffer_size_seconds = 5.0
            
            # Enable streaming mode by default
            self.config.use_streaming = True
            
            # Save the configuration
            self.save_config()
            
            self.logger.info(f"Device {device.name} configured with: "
                           f"16kHz, mono, {self.config.buffer_size_seconds}s buffer")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure device {device.name}: {e}")
            return False
    
    def test_device_recording(self, duration: float = 2.0) -> bool:
        """
        Test that the current device can actually record audio.
        
        Args:
            duration: Duration of test recording in seconds
            
        Returns:
            True if device can record audio, False otherwise
        """
        try:
            current_device = self.get_current_device()
            if not current_device:
                self.logger.error("No device selected for testing")
                return False
            
            self.logger.info(f"Testing recording on device {current_device.name}")
            
            # Test recording using the detector's test method
            success = self.detector.test_device(current_device.device_id, duration)
            
            if success:
                self.logger.info("Device recording test passed")
            else:
                self.logger.error("Device recording test failed - no audio detected")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Device recording test failed: {e}")
            return False
    
    def get_device_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the current device configuration.
        
        Returns:
            Dictionary with device status information
        """
        try:
            current_device = self.get_current_device()
            is_valid, validation_message = self.validate_configuration()
            
            status = {
                "device_configured": current_device is not None,
                "device_name": current_device.name if current_device else "None",
                "device_id": current_device.device_id if current_device else -1,
                "configuration_valid": is_valid,
                "validation_message": validation_message,
                "sample_rate": self.config.sample_rate,
                "channels": self.config.channels,
                "buffer_size_seconds": self.config.buffer_size_seconds,
                "capture_mode": "streaming" if self.config.use_streaming else "file-based",
                "is_default_device": current_device.is_default_input if current_device else False
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get device status: {e}")
            return {"error": str(e)}
    
    def reset_device_configuration(self) -> bool:
        """
        Reset device configuration to defaults and auto-configure.
        
        Returns:
            True if reset and reconfiguration was successful, False otherwise
        """
        try:
            self.logger.info("Resetting device configuration to defaults")
            
            # Reset to default configuration
            self.reset_to_defaults()
            
            # Auto-configure the default device
            success = self.auto_configure_default_device()
            
            if success:
                self.logger.info("Device configuration reset and auto-configured successfully")
            else:
                self.logger.error("Failed to auto-configure device after reset")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to reset device configuration: {e}")
            return False

    def test_device_permissions(self) -> Dict[str, Any]:
        """
        Test if the application has microphone access permissions.
        
        Checks permissions across different Linux distributions and desktop environments.
        
        Returns:
            Dictionary with permission status and details
        """
        try:
            current_device = self.get_current_device()
            if not current_device:
                return {
                    "has_permissions": False,
                    "error": "No device selected",
                    "details": {}
                }
            
            self.logger.info(f"Testing device permissions for {current_device.name}")
            
            permission_status = {
                "has_permissions": False,
                "device_name": current_device.name,
                "device_id": current_device.device_id,
                "details": {}
            }
            
            # Test 1: Check if we can access the audio device directly
            try:
                # Try to open the device for a brief test recording
                test_success = self.detector.test_device(current_device.device_id, duration=0.1)
                permission_status["details"]["direct_access"] = test_success
                if test_success:
                    permission_status["has_permissions"] = True
                    self.logger.info("Direct device access test passed")
            except Exception as e:
                permission_status["details"]["direct_access"] = False
                permission_status["details"]["direct_access_error"] = str(e)
                self.logger.warning(f"Direct device access test failed: {e}")
            
            # Test 2: Check PulseAudio permissions (if available)
            try:
                result = subprocess.run(
                    ["pactl", "list", "short", "sources"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    permission_status["details"]["pulseaudio_access"] = True
                    self.logger.info("PulseAudio access confirmed")
                else:
                    permission_status["details"]["pulseaudio_access"] = False
                    permission_status["details"]["pulseaudio_error"] = result.stderr
            except (subprocess.TimeoutExpired, FileNotFoundError):
                permission_status["details"]["pulseaudio_access"] = False
                permission_status["details"]["pulseaudio_error"] = "PulseAudio not available"
            
            # Test 3: Check ALSA permissions (if available)
            try:
                result = subprocess.run(
                    ["amixer", "scontrols"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    permission_status["details"]["alsa_access"] = True
                    self.logger.info("ALSA access confirmed")
                else:
                    permission_status["details"]["alsa_access"] = False
                    permission_status["details"]["alsa_error"] = result.stderr
            except (subprocess.TimeoutExpired, FileNotFoundError):
                permission_status["details"]["alsa_access"] = False
                permission_status["details"]["alsa_error"] = "ALSA not available"
            
            # Test 4: Check PipeWire permissions (if available)
            try:
                result = subprocess.run(
                    ["pw-cli", "list-objects"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    permission_status["details"]["pipewire_access"] = True
                    self.logger.info("PipeWire access confirmed")
                else:
                    permission_status["details"]["pipewire_access"] = False
                    permission_status["details"]["pipewire_error"] = result.stderr
            except (subprocess.TimeoutExpired, FileNotFoundError):
                permission_status["details"]["pipewire_access"] = False
                permission_status["details"]["pipewire_error"] = "PipeWire not available"
            
            # Test 5: Check if we're in a sandboxed environment
            sandbox_indicators = [
                "/proc/1/cgroup",  # Check for containerization
                "/.flatpak-info",  # Flatpak
                "/run/host/container-manager",  # Snap
                "/run/snapd/ns",  # Snap
            ]
            
            sandboxed = False
            sandbox_type = None
            
            for indicator in sandbox_indicators:
                if os.path.exists(indicator):
                    sandboxed = True
                    if "flatpak" in indicator:
                        sandbox_type = "flatpak"
                    elif "snap" in indicator:
                        sandbox_type = "snap"
                    else:
                        sandbox_type = "container"
                    break
            
            permission_status["details"]["sandboxed"] = sandboxed
            if sandboxed:
                permission_status["details"]["sandbox_type"] = sandbox_type
                self.logger.info(f"Running in {sandbox_type} sandbox")
            
            # Determine overall permission status
            if permission_status["has_permissions"]:
                self.logger.info("Device permission test passed")
            else:
                self.logger.warning("Device permission test failed - may need additional permissions")
            
            return permission_status
            
        except Exception as e:
            self.logger.error(f"Failed to test device permissions: {e}")
            return {
                "has_permissions": False,
                "error": str(e),
                "details": {}
            }
    
    def get_permission_requirements(self) -> Dict[str, Any]:
        """
        Get information about permission requirements for different environments.
        
        Returns:
            Dictionary with permission requirements and setup instructions
        """
        requirements = {
            "linux_desktop": {
                "pulseaudio": "Usually works out of the box",
                "alsa": "May need user in 'audio' group",
                "pipewire": "Usually works out of the box"
            },
            "flatpak": {
                "description": "Requires microphone permission in Flatpak settings",
                "setup": "Run: flatpak override --user org.w4l.app --talk-name=org.freedesktop.portal.PermissionStore"
            },
            "snap": {
                "description": "Requires microphone permission in Snap settings",
                "setup": "Run: snap connect w4l:audio-record"
            },
            "container": {
                "description": "May require additional volume mounts and permissions",
                "setup": "Mount /dev/snd and add --privileged or --device=/dev/snd"
            }
        }
        
        return requirements
    
    def suggest_permission_fix(self, permission_status: Dict[str, Any]) -> List[str]:
        """
        Suggest fixes based on permission test results.
        
        Args:
            permission_status: Result from test_device_permissions()
            
        Returns:
            List of suggested fixes
        """
        suggestions = []
        
        if not permission_status.get("has_permissions", False):
            details = permission_status.get("details", {})
            
            if details.get("sandboxed"):
                sandbox_type = details.get("sandbox_type", "unknown")
                if sandbox_type == "flatpak":
                    suggestions.append("Flatpak: Run 'flatpak override --user org.w4l.app --talk-name=org.freedesktop.portal.PermissionStore'")
                elif sandbox_type == "snap":
                    suggestions.append("Snap: Run 'snap connect w4l:audio-record'")
                else:
                    suggestions.append("Container: Ensure audio devices are properly mounted and permissions granted")
            
            if not details.get("pulseaudio_access", True):
                suggestions.append("PulseAudio: Ensure PulseAudio is running and user has access")
            
            if not details.get("alsa_access", True):
                suggestions.append("ALSA: Add user to 'audio' group: 'sudo usermod -a -G audio $USER'")
            
            if not details.get("direct_access", True):
                suggestions.append("Direct access: Check if microphone is not being used by another application")
        
        return suggestions
    
    def list_devices_formatted(self) -> List[Dict[str, Any]]:
        """
        Get a formatted list of available input devices with additional information.
        
        Returns:
            List of dictionaries with device information
        """
        devices = self.get_available_devices()
        formatted_devices = []
        
        for device in devices:
            # Check if this is the currently selected device
            is_current = (device.device_id == self.config.device_id)
            
            # Check if this is the default device
            is_default = device.is_default_input
            
            # Validate device for W4L
            is_valid, validation_message = self.detector.validate_device_for_w4l(device.device_id)
            
            device_info = {
                "device_id": device.device_id,
                "name": device.name,
                "channels": device.channels,
                "sample_rate": device.sample_rate,
                "is_current": is_current,
                "is_default": is_default,
                "is_valid_for_w4l": is_valid,
                "validation_message": validation_message,
                "status": self._get_device_status_string(is_current, is_default, is_valid)
            }
            
            formatted_devices.append(device_info)
        
        return formatted_devices
    
    def _get_device_status_string(self, is_current: bool, is_default: bool, is_valid: bool) -> str:
        """Get a human-readable status string for a device."""
        status_parts = []
        
        if is_current:
            status_parts.append("CURRENT")
        if is_default:
            status_parts.append("DEFAULT")
        if not is_valid:
            status_parts.append("INVALID")
        
        return " | ".join(status_parts) if status_parts else "AVAILABLE"
    
    def print_device_list(self) -> None:
        """Print a formatted list of available input devices."""
        devices = self.list_devices_formatted()
        
        if not devices:
            print("No input devices found!")
            return
        
        print("\n=== Available Input Devices ===")
        print(f"{'ID':<4} {'Name':<40} {'Channels':<8} {'Sample Rate':<12} {'Status':<20}")
        print("-" * 90)
        
        for device in devices:
            status_color = ""
            if device["is_current"]:
                status_color = "🟢 "  # Green for current
            elif device["is_default"]:
                status_color = "🔵 "  # Blue for default
            elif not device["is_valid_for_w4l"]:
                status_color = "🔴 "  # Red for invalid
            else:
                status_color = "⚪ "  # White for available
            
            print(f"{device['device_id']:<4} {device['name']:<40} {device['channels']:<8} "
                  f"{device['sample_rate']:<12} {status_color}{device['status']:<20}")
        
        print("-" * 90)
        print("Legend: 🟢 Current | 🔵 Default | 🔴 Invalid | ⚪ Available")
        print("=" * 90)
    
    def select_device_interactive(self) -> bool:
        """
        Interactive device selection with user input.
        
        Returns:
            True if device was successfully selected, False otherwise
        """
        try:
            # Show available devices
            self.print_device_list()
            
            # Get user input
            print("\nEnter device ID to select (or 'q' to quit): ", end="")
            user_input = input().strip()
            
            if user_input.lower() == 'q':
                print("Device selection cancelled.")
                return False
            
            try:
                device_id = int(user_input)
            except ValueError:
                print("Invalid input. Please enter a number.")
                return False
            
            # Select the device
            success = self.select_device(device_id)
            
            if success:
                print(f"✅ Successfully selected device ID {device_id}")
                # Show updated device list
                self.print_device_list()
            else:
                print(f"❌ Failed to select device ID {device_id}")
            
            return success
            
        except KeyboardInterrupt:
            print("\nDevice selection cancelled.")
            return False
        except Exception as e:
            self.logger.error(f"Interactive device selection failed: {e}")
            return False
    
    def select_device_by_name_interactive(self) -> bool:
        """
        Interactive device selection by name with fuzzy matching.
        
        Returns:
            True if device was successfully selected, False otherwise
        """
        try:
            devices = self.get_available_devices()
            
            if not devices:
                print("No input devices found!")
                return False
            
            # Show available devices
            print("\n=== Available Input Devices ===")
            for i, device in enumerate(devices, 1):
                status = " (CURRENT)" if device.device_id == self.config.device_id else ""
                status += " (DEFAULT)" if device.is_default_input else ""
                print(f"{i}. {device.name}{status}")
            
            # Get user input
            print("\nEnter device name or number to select (or 'q' to quit): ", end="")
            user_input = input().strip()
            
            if user_input.lower() == 'q':
                print("Device selection cancelled.")
                return False
            
            # Try to parse as number first
            try:
                device_index = int(user_input) - 1
                if 0 <= device_index < len(devices):
                    selected_device = devices[device_index]
                    success = self.select_device(selected_device.device_id)
                else:
                    print("Invalid device number.")
                    return False
            except ValueError:
                # Try to find by name
                success = self.select_device_by_name(user_input)
            
            if success:
                print(f"✅ Successfully selected device: {self.config.device_name}")
            else:
                print(f"❌ Failed to select device: {user_input}")
            
            return success
            
        except KeyboardInterrupt:
            print("\nDevice selection cancelled.")
            return False
        except Exception as e:
            self.logger.error(f"Interactive device selection by name failed: {e}")
            return False
    
    def reset_to_default_device(self) -> bool:
        """
        Reset device selection to use the system default microphone.
        
        Returns:
            True if reset was successful, False otherwise
        """
        try:
            self.logger.info("Resetting to default microphone")
            
            # Reset device configuration
            self.config.device_id = -1
            self.config.device_name = ""
            
            # Save configuration
            self.save_config()
            
            # Auto-configure the default device
            success = self.auto_configure_default_device()
            
            if success:
                self.logger.info("Successfully reset to default microphone")
            else:
                self.logger.warning("Reset to default microphone, but auto-configuration failed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset to default device: {e}")
            return False
    
    def get_device_selection_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current device selection.
        
        Returns:
            Dictionary with device selection information
        """
        current_device = self.get_current_device()
        available_devices = self.get_available_devices()
        
        return {
            "current_device": {
                "id": current_device.device_id if current_device else -1,
                "name": current_device.name if current_device else "None",
                "is_default": current_device.is_default_input if current_device else False
            },
            "available_devices_count": len(available_devices),
            "is_using_default": self.config.device_id == -1,
            "has_custom_selection": self.config.device_id >= 0,
            "device_selection_method": "default" if self.config.device_id == -1 else "custom"
        } 