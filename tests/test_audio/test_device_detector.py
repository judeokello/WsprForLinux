"""
Pytest tests for audio device detection.

Run with: PYTHONPATH=src pytest tests/test_audio/test_device_detector.py
"""

import pytest
from audio.device_detector import AudioDeviceDetector, AudioDevice

@pytest.fixture(scope="module")
def detector():
    """Create a device detector fixture."""
    return AudioDeviceDetector()

def test_list_devices(detector):
    """Test listing all audio devices."""
    devices = detector.list_devices()
    assert isinstance(devices, list)
    assert all(isinstance(d, AudioDevice) for d in devices)
    # There should be at least one device (virtual or real)
    assert len(devices) > 0

def test_get_input_devices(detector):
    """Test getting only input devices."""
    input_devices = detector.get_input_devices()
    assert isinstance(input_devices, list)
    assert all(isinstance(d, AudioDevice) for d in input_devices)
    # Input devices may be empty on some systems, but should be a list

def test_get_default_microphone(detector):
    """Test getting the default microphone."""
    default_mic = detector.get_default_microphone()
    # Default mic may be None if no input devices, but should be AudioDevice or None
    assert (default_mic is None) or isinstance(default_mic, AudioDevice)

def test_get_device_by_name(detector):
    """Test finding device by name."""
    devices = detector.list_devices()
    if devices:
        name_fragment = devices[0].name.split()[0]
        found = detector.get_device_by_name(name_fragment)
        assert found is not None
        assert name_fragment.lower() in found.name.lower()
    else:
        pytest.skip("No devices to test name search")

def test_validate_device_for_w4l(detector):
    """Test device validation for W4L."""
    input_devices = detector.get_input_devices()
    if not input_devices:
        pytest.skip("No input devices to validate")
    for device in input_devices:
        is_valid, message = detector.validate_device_for_w4l(device.device_id)
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)

def test_print_device_list(detector, capsys):
    """Test printing device list."""
    detector.print_device_list()
    captured = capsys.readouterr()
    assert "Available Audio Devices" in captured.out

def test_device_properties(detector):
    """Test that AudioDevice objects have expected properties."""
    devices = detector.list_devices()
    if devices:
        device = devices[0]
        assert hasattr(device, 'device_id')
        assert hasattr(device, 'name')
        assert hasattr(device, 'channels')
        assert hasattr(device, 'sample_rate')
        assert hasattr(device, 'is_input')
        assert hasattr(device, 'is_output')
        assert hasattr(device, 'is_default_input')
        assert hasattr(device, 'is_default_output') 