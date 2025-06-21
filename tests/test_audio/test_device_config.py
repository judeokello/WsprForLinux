"""
Pytest tests for audio device configuration and buffer management.

Run with: PYTHONPATH=src pytest tests/test_audio/test_device_config.py
"""

import pytest
import tempfile
import os
from audio.device_config import AudioDeviceManager
from audio.buffer_manager import AudioBufferManager

@pytest.fixture(scope="module")
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"device_id": -1, "buffer_size_seconds": 5.0}')
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)

@pytest.fixture(scope="module")
def device_manager(temp_config_file):
    """Create a device manager with temporary config."""
    return AudioDeviceManager(config_file=temp_config_file)

@pytest.fixture(scope="module")
def buffer_manager(device_manager):
    """Create a buffer manager."""
    return AudioBufferManager(device_manager)

def test_device_manager_initialization(device_manager):
    """Test device manager initialization."""
    assert device_manager is not None
    assert hasattr(device_manager, 'config')
    assert hasattr(device_manager, 'detector')

def test_get_available_devices(device_manager):
    """Test getting available devices."""
    devices = device_manager.get_available_devices()
    assert isinstance(devices, list)
    # May be empty on some systems, but should be a list

def test_get_current_device(device_manager):
    """Test getting current device."""
    current_device = device_manager.get_current_device()
    # May be None if no devices, but should be AudioDevice or None
    assert (current_device is None) or hasattr(current_device, 'name')

def test_buffer_size_configuration(device_manager):
    """Test buffer size configuration."""
    # Test setting buffer size
    device_manager.set_buffer_size(7.5)
    assert device_manager.config.buffer_size_seconds == 7.5
    
    # Test getting buffer size in samples
    samples = device_manager.get_buffer_size_samples()
    assert isinstance(samples, int)
    assert samples > 0

def test_capture_mode_switching(device_manager):
    """Test switching between capture modes."""
    # Test switching to file-based
    device_manager.set_capture_mode(False)
    assert device_manager.config.use_streaming == False
    
    # Test switching to streaming
    device_manager.set_capture_mode(True)
    assert device_manager.config.use_streaming == True

def test_configuration_validation(device_manager):
    """Test configuration validation."""
    is_valid, message = device_manager.validate_configuration()
    assert isinstance(is_valid, bool)
    assert isinstance(message, str)

def test_configuration_summary(device_manager):
    """Test getting configuration summary."""
    summary = device_manager.get_config_summary()
    assert isinstance(summary, dict)
    assert 'device' in summary
    assert 'buffer' in summary
    assert 'capture_mode' in summary

def test_buffer_manager_initialization(buffer_manager):
    """Test buffer manager initialization."""
    assert buffer_manager is not None
    assert hasattr(buffer_manager, 'device_manager')
    assert hasattr(buffer_manager, 'streaming_manager')
    assert hasattr(buffer_manager, 'file_manager')

def test_buffer_info(buffer_manager):
    """Test getting buffer information."""
    info = buffer_manager.get_buffer_info()
    assert isinstance(info, dict)
    assert 'mode' in info
    assert 'buffer_size_seconds' in info
    assert 'is_recording' in info

def test_capture_mode_switching_buffer(buffer_manager):
    """Test switching capture modes in buffer manager."""
    # Test streaming mode
    buffer_manager.set_capture_mode(True)
    assert buffer_manager.is_streaming_mode() == True
    
    # Test file-based mode
    buffer_manager.set_capture_mode(False)
    assert buffer_manager.is_streaming_mode() == False

def test_buffer_size_changes(buffer_manager):
    """Test changing buffer size in buffer manager."""
    original_size = buffer_manager.get_buffer_info()['buffer_size_seconds']
    
    # Change buffer size
    buffer_manager.set_buffer_size(8.0)
    new_size = buffer_manager.get_buffer_info()['buffer_size_seconds']
    
    assert new_size == 8.0
    assert new_size != original_size

def test_recording_control(buffer_manager):
    """Test recording start/stop (without actually recording)."""
    # Test that we can call start_recording (may fail if no devices, but shouldn't crash)
    try:
        success = buffer_manager.start_recording()
        assert isinstance(success, bool)
        
        if success:
            # If recording started, stop it
            buffer_manager.stop_recording()
    except Exception as e:
        # It's okay if recording fails due to no devices
        assert "device" in str(e).lower() or "audio" in str(e).lower()

def test_audio_data_access(buffer_manager):
    """Test accessing audio data."""
    # Test getting latest audio (should return empty array if not recording)
    audio_data = buffer_manager.get_latest_audio()
    assert isinstance(audio_data, list) or hasattr(audio_data, 'shape')
    
    # Test getting audio file path (should return None if not file-based)
    audio_file = buffer_manager.get_audio_file()
    assert audio_file is None or isinstance(audio_file, str) 