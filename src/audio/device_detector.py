"""
Audio device detection for W4L.

Handles discovery and management of audio input devices.
"""

import sounddevice as sd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging
from dataclasses import dataclass


@dataclass
class AudioDevice:
    """
    Represents an audio device with its properties.

    Attributes:
        device_id (int): Index of the device in the sounddevice list.
        name (str): Human-readable name of the device.
        channels (int): Number of input channels supported.
        sample_rate (float): Default sample rate for the device.
        is_input (bool): True if device can capture audio.
        is_output (bool): True if device can play audio.
        is_default_input (bool): True if this is the default input device.
        is_default_output (bool): True if this is the default output device.
    """
    device_id: int
    name: str
    channels: int
    sample_rate: float
    is_input: bool
    is_output: bool
    is_default_input: bool
    is_default_output: bool


class AudioDeviceDetector:
    """
    Detects and manages audio devices for W4L.
    
    Provides functionality to list available devices, detect defaults,
    and validate device capabilities.
    
    Typical usage:
        detector = AudioDeviceDetector()
        devices = detector.list_devices()
        default_mic = detector.get_default_microphone()
    """
    
    def __init__(self):
        """Initialize the audio device detector."""
        self.logger = logging.getLogger("w4l.audio.device_detector")
        self._devices_cache: Optional[List[AudioDevice]] = None
    
    def list_devices(self) -> List[AudioDevice]:
        """
        List all available audio devices.
        
        Returns:
            List[AudioDevice]: List of AudioDevice objects representing available devices.
        """
        try:
            devices = sd.query_devices()
            audio_devices = []
            
            for device_id, device_info in enumerate(devices):
                # Create AudioDevice object
                audio_device = AudioDevice(
                    device_id=device_id,
                    name=str(device_info.get('name', f'Device {device_id}')),
                    channels=int(device_info.get('max_input_channels', 0)),
                    sample_rate=float(device_info.get('default_samplerate', 44100)),
                    is_input=int(device_info.get('max_input_channels', 0)) > 0,
                    is_output=int(device_info.get('max_output_channels', 0)) > 0,
                    is_default_input=device_id == sd.default.device[0],
                    is_default_output=device_id == sd.default.device[1]
                )
                
                audio_devices.append(audio_device)
            
            self._devices_cache = audio_devices
            self.logger.info(f"Found {len(audio_devices)} audio devices")
            return audio_devices
            
        except Exception as e:
            self.logger.error(f"Failed to list audio devices: {e}")
            return []
    
    def get_input_devices(self) -> List[AudioDevice]:
        """
        Get only input devices (microphones).
        
        Returns:
            List[AudioDevice]: List of AudioDevice objects that can capture audio.
        """
        devices = self.list_devices()
        return [device for device in devices if device.is_input]
    
    def get_default_microphone(self) -> Optional[AudioDevice]:
        """
        Get the default microphone device.
        
        Returns:
            Optional[AudioDevice]: AudioDevice object for default microphone, or None if not found.
        """
        try:
            default_input_id = sd.default.device[0]
            devices = self.list_devices()
            
            for device in devices:
                if device.device_id == default_input_id and device.is_input:
                    self.logger.info(f"Default microphone: {device.name}")
                    return device
            
            # Fallback: find first input device
            input_devices = self.get_input_devices()
            if input_devices:
                self.logger.warning(f"No default input device found, using first available: {input_devices[0].name}")
                return input_devices[0]
            
            self.logger.error("No input devices found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get default microphone: {e}")
            return None
    
    def get_device_by_name(self, name: str) -> Optional[AudioDevice]:
        """
        Find a device by its name (case-insensitive substring match).
        
        Args:
            name (str): Device name to search for.
        Returns:
            Optional[AudioDevice]: AudioDevice object if found, None otherwise.
        """
        devices = self.list_devices()
        for device in devices:
            if name.lower() in device.name.lower():
                return device
        return None
    
    def test_device(self, device_id: int, duration: float = 1.0) -> bool:
        """
        Test if a device can capture audio by recording a short sample.
        
        Args:
            device_id (int): ID of the device to test.
            duration (float): Duration of test recording in seconds.
        Returns:
            bool: True if device works, False otherwise.
        """
        try:
            self.logger.info(f"Testing device {device_id} for {duration} seconds")
            
            # Record a short test sample
            test_audio = sd.rec(
                int(16000 * duration),  # 16kHz sample rate
                samplerate=16000,
                channels=1,
                dtype=np.int16,
                device=device_id
            )
            sd.wait()  # Wait for recording to complete
            
            # Check if we got any audio data
            if test_audio is not None and len(test_audio) > 0:
                # Check if audio has any non-zero samples
                has_audio = bool(np.any(test_audio != 0))
                self.logger.info(f"Device {device_id} test {'passed' if has_audio else 'failed'}")
                return has_audio
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to test device {device_id}: {e}")
            return False
    
    def get_device_info(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific device.
        
        Args:
            device_id (int): ID of the device.
        Returns:
            Optional[Dict[str, Any]]: Dictionary with device information, or None if not found.
        """
        try:
            device_info = sd.query_devices(device_id)
            return dict(device_info) if device_info else None
        except Exception as e:
            self.logger.error(f"Failed to get device info for {device_id}: {e}")
            return None
    
    def print_device_list(self) -> None:
        """
        Print a formatted list of all audio devices, including their status and properties.
        """
        devices = self.list_devices()
        
        print("\n=== Available Audio Devices ===")
        for device in devices:
            status = []
            if device.is_default_input:
                status.append("DEFAULT INPUT")
            if device.is_default_output:
                status.append("DEFAULT OUTPUT")
            
            status_str = f" [{', '.join(status)}]" if status else ""
            
            print(f"ID {device.device_id}: {device.name}{status_str}")
            print(f"  Channels: {device.channels}, Sample Rate: {device.sample_rate}")
            print(f"  Input: {device.is_input}, Output: {device.is_output}")
            print()
        
        # Show default microphone
        default_mic = self.get_default_microphone()
        if default_mic:
            print(f"Default Microphone: {default_mic.name} (ID: {default_mic.device_id})")
        else:
            print("No default microphone found!")
        print("=" * 35)
    
    def validate_device_for_w4l(self, device_id: int) -> Tuple[bool, str]:
        """
        Validate if a device is suitable for W4L (input, sample rate, test recording).
        
        Args:
            device_id (int): ID of the device to validate.
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            device_info = sd.query_devices(device_id)
            if not device_info:
                return False, "Device not found"
            
            # Convert to dict for easier access
            device_dict = dict(device_info)
            
            # Check if it's an input device
            max_inputs = int(device_dict.get('max_input_channels', 0))
            if max_inputs == 0:
                return False, "Device is not an input device"
            
            # Check sample rate support
            sample_rate = float(device_dict.get('default_samplerate', 44100))
            if sample_rate < 16000:
                return False, f"Sample rate too low: {sample_rate}Hz (need 16kHz+)"
            
            # Test the device
            if not self.test_device(device_id):
                return False, "Device test failed - no audio detected"
            
            return True, "Device is valid for W4L"
            
        except Exception as e:
            return False, f"Validation error: {e}" 