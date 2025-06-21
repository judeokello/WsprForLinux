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

# New tests for 1.4.1.2 Device Configuration

def test_auto_configure_default_device(device_manager):
    """Test automatic configuration of default microphone."""
    # Test auto-configuration
    success = device_manager.auto_configure_default_device()
    assert isinstance(success, bool)
    
    # If successful, verify device is configured
    if success:
        status = device_manager.get_device_status()
        assert status["device_configured"] == True
        assert status["sample_rate"] == 16000  # Should be set to 16kHz
        assert status["channels"] == 1  # Should be set to mono
        assert status["capture_mode"] == "streaming"  # Should default to streaming

def test_configure_device_for_w4l(device_manager):
    """Test configuring a specific device for W4L."""
    # Get a device to configure
    devices = device_manager.get_available_devices()
    if not devices:
        pytest.skip("No input devices available for testing")
    
    device = devices[0]
    success = device_manager.configure_device_for_w4l(device)
    assert isinstance(success, bool)
    
    if success:
        # Verify configuration was applied
        assert device_manager.config.device_id == device.device_id
        assert device_manager.config.device_name == device.name
        assert device_manager.config.sample_rate == 16000
        assert device_manager.config.channels == 1
        assert device_manager.config.use_streaming == True

def test_test_device_recording(device_manager):
    """Test device recording functionality."""
    # Test recording (may fail if no devices, but shouldn't crash)
    try:
        success = device_manager.test_device_recording(duration=1.0)
        assert isinstance(success, bool)
    except Exception as e:
        # It's okay if recording fails due to no devices
        assert "device" in str(e).lower() or "audio" in str(e).lower()

def test_get_device_status(device_manager):
    """Test getting comprehensive device status."""
    status = device_manager.get_device_status()
    assert isinstance(status, dict)
    
    # Check required status fields
    required_fields = [
        "device_configured", "device_name", "device_id", 
        "configuration_valid", "validation_message", "sample_rate",
        "channels", "buffer_size_seconds", "capture_mode"
    ]
    
    for field in required_fields:
        assert field in status, f"Missing status field: {field}"
    
    # Check data types
    assert isinstance(status["device_configured"], bool)
    assert isinstance(status["device_name"], str)
    assert isinstance(status["device_id"], int)
    assert isinstance(status["configuration_valid"], bool)
    assert isinstance(status["validation_message"], str)
    assert isinstance(status["sample_rate"], int)
    assert isinstance(status["channels"], int)
    assert isinstance(status["buffer_size_seconds"], float)
    assert isinstance(status["capture_mode"], str)

def test_reset_device_configuration(device_manager):
    """Test resetting device configuration to defaults."""
    # Test reset functionality
    success = device_manager.reset_device_configuration()
    assert isinstance(success, bool)
    
    # Verify configuration was reset
    if success:
        status = device_manager.get_device_status()
        assert status["configuration_valid"] == True

def test_device_configuration_workflow(device_manager):
    """Test complete device configuration workflow."""
    # 1. Get initial status
    initial_status = device_manager.get_device_status()
    
    # 2. Auto-configure device
    success = device_manager.auto_configure_default_device()
    assert isinstance(success, bool)
    
    # 3. Get updated status
    updated_status = device_manager.get_device_status()
    
    # 4. Verify configuration improved
    if success:
        assert updated_status["device_configured"] == True
        assert updated_status["sample_rate"] == 16000
        assert updated_status["channels"] == 1
        assert updated_status["capture_mode"] == "streaming"
    
    # 5. Test device recording
    try:
        recording_success = device_manager.test_device_recording(duration=1.0)
        assert isinstance(recording_success, bool)
    except Exception:
        # Recording test may fail, but shouldn't crash
        pass

def test_device_configuration_persistence(device_manager):
    """Test that device configuration persists across manager instances."""
    # Configure a device
    devices = device_manager.get_available_devices()
    if not devices:
        pytest.skip("No input devices available for testing")
    
    device = devices[0]
    success = device_manager.configure_device_for_w4l(device)
    
    if success:
        # Create a new manager instance
        new_manager = AudioDeviceManager(config_file=device_manager.config_file)
        
        # Verify configuration persisted
        assert new_manager.config.device_id == device.device_id
        assert new_manager.config.device_name == device.name
        assert new_manager.config.sample_rate == 16000
        assert new_manager.config.channels == 1

# New tests for 1.4.1.3 Device Permissions

def test_test_device_permissions(device_manager):
    """Test device permission checking functionality."""
    # Test permission checking
    permission_status = device_manager.test_device_permissions()
    assert isinstance(permission_status, dict)
    
    # Check required fields
    required_fields = ["has_permissions", "device_name", "device_id", "details"]
    for field in required_fields:
        assert field in permission_status, f"Missing permission status field: {field}"
    
    # Check data types
    assert isinstance(permission_status["has_permissions"], bool)
    assert isinstance(permission_status["device_name"], str)
    assert isinstance(permission_status["device_id"], int)
    assert isinstance(permission_status["details"], dict)

def test_get_permission_requirements(device_manager):
    """Test getting permission requirements information."""
    requirements = device_manager.get_permission_requirements()
    assert isinstance(requirements, dict)
    
    # Check that we have requirements for different environments
    expected_environments = ["linux_desktop", "flatpak", "snap", "container"]
    for env in expected_environments:
        assert env in requirements, f"Missing requirements for {env}"
    
    # Check that each environment has setup information
    for env, info in requirements.items():
        assert isinstance(info, dict), f"Requirements for {env} should be a dict"
        assert len(info) > 0, f"Requirements for {env} should not be empty"

def test_suggest_permission_fix(device_manager):
    """Test permission fix suggestion functionality."""
    # Test with a mock permission status that indicates no permissions
    mock_permission_status = {
        "has_permissions": False,
        "device_name": "test_device",
        "device_id": 0,
        "details": {
            "direct_access": False,
            "pulseaudio_access": False,
            "alsa_access": False,
            "sandboxed": True,
            "sandbox_type": "flatpak"
        }
    }
    
    suggestions = device_manager.suggest_permission_fix(mock_permission_status)
    assert isinstance(suggestions, list)
    
    # Should have suggestions for the issues
    assert len(suggestions) > 0
    
    # Check that suggestions are strings
    for suggestion in suggestions:
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0

def test_permission_workflow(device_manager):
    """Test complete permission checking workflow."""
    # 1. Test device permissions
    permission_status = device_manager.test_device_permissions()
    assert isinstance(permission_status, dict)
    
    # 2. Get permission requirements
    requirements = device_manager.get_permission_requirements()
    assert isinstance(requirements, dict)
    
    # 3. If permissions failed, get suggestions
    if not permission_status.get("has_permissions", True):
        suggestions = device_manager.suggest_permission_fix(permission_status)
        assert isinstance(suggestions, list)
        
        # Log the suggestions for debugging
        print(f"Permission suggestions: {suggestions}")

def test_permission_status_structure(device_manager):
    """Test that permission status has the expected structure."""
    permission_status = device_manager.test_device_permissions()
    
    # Check top-level structure
    assert "has_permissions" in permission_status
    assert "device_name" in permission_status
    assert "device_id" in permission_status
    assert "details" in permission_status
    
    # Check details structure
    details = permission_status["details"]
    expected_detail_keys = [
        "direct_access", "pulseaudio_access", "alsa_access", 
        "pipewire_access", "sandboxed"
    ]
    
    for key in expected_detail_keys:
        assert key in details, f"Missing detail key: {key}"
        assert isinstance(details[key], bool), f"Detail {key} should be boolean"

def test_permission_error_handling(device_manager):
    """Test permission checking error handling."""
    # Test with a device that doesn't exist
    # We'll test by temporarily modifying the detector to return None
    original_get_default_microphone = device_manager.detector.get_default_microphone
    
    try:
        # Mock the detector to return None for default microphone
        device_manager.detector.get_default_microphone = lambda: None
        
        permission_status = device_manager.test_device_permissions()
        assert isinstance(permission_status, dict)
        assert permission_status["has_permissions"] == False
        
        # When no device is selected, the structure is different
        if "error" in permission_status:
            # No device selected case
            assert permission_status["error"] == "No device selected"
            assert "details" in permission_status
        else:
            # Device exists but has permission issues
            assert "device_id" in permission_status
            assert "device_name" in permission_status
            assert "details" in permission_status
    finally:
        # Restore original method
        device_manager.detector.get_default_microphone = original_get_default_microphone

# New tests for 1.4.1.4 Device Selection

def test_list_devices_formatted(device_manager):
    """Test formatted device listing functionality."""
    formatted_devices = device_manager.list_devices_formatted()
    assert isinstance(formatted_devices, list)
    
    if formatted_devices:
        # Check structure of first device
        device = formatted_devices[0]
        required_fields = [
            "device_id", "name", "channels", "sample_rate", 
            "is_current", "is_default", "is_valid_for_w4l", 
            "validation_message", "status"
        ]
        
        for field in required_fields:
            assert field in device, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(device["device_id"], int)
        assert isinstance(device["name"], str)
        assert isinstance(device["channels"], int)
        assert isinstance(device["sample_rate"], float)
        assert isinstance(device["is_current"], bool)
        assert isinstance(device["is_default"], bool)
        assert isinstance(device["is_valid_for_w4l"], bool)
        assert isinstance(device["validation_message"], str)
        assert isinstance(device["status"], str)

def test_get_device_status_string(device_manager):
    """Test device status string generation."""
    # Test different combinations
    status1 = device_manager._get_device_status_string(True, False, True)   # Current
    status2 = device_manager._get_device_status_string(False, True, True)   # Default
    status3 = device_manager._get_device_status_string(False, False, False) # Invalid
    status4 = device_manager._get_device_status_string(False, False, True)  # Available
    status5 = device_manager._get_device_status_string(True, True, True)    # Current + Default
    
    assert "CURRENT" in status1
    assert "DEFAULT" in status2
    assert "INVALID" in status3
    assert status4 == "AVAILABLE"
    assert "CURRENT" in status5 and "DEFAULT" in status5

def test_reset_to_default_device(device_manager):
    """Test resetting to default device functionality."""
    # Store original device ID
    original_device_id = device_manager.config.device_id
    
    # Test reset functionality
    success = device_manager.reset_to_default_device()
    assert isinstance(success, bool)
    
    if success:
        # The reset should either set device_id to -1 OR configure the default device
        # Since auto_configure_default_device() is called, it might set a specific device ID
        # So we check that either it's -1 (default) or it's a valid device that was auto-configured
        assert device_manager.config.device_id == -1 or device_manager.config.device_id >= 0
        
        # If it's not -1, it should have a device name
        if device_manager.config.device_id != -1:
            assert device_manager.config.device_name != ""
    
    # Restore original configuration for other tests
    device_manager.config.device_id = original_device_id
    device_manager.save_config()

def test_get_device_selection_summary(device_manager):
    """Test device selection summary functionality."""
    summary = device_manager.get_device_selection_summary()
    assert isinstance(summary, dict)
    
    # Check required fields
    required_fields = [
        "current_device", "available_devices_count", 
        "is_using_default", "has_custom_selection", "device_selection_method"
    ]
    
    for field in required_fields:
        assert field in summary, f"Missing summary field: {field}"
    
    # Check current_device structure
    current_device = summary["current_device"]
    assert "id" in current_device
    assert "name" in current_device
    assert "is_default" in current_device
    
    # Check data types
    assert isinstance(summary["available_devices_count"], int)
    assert isinstance(summary["is_using_default"], bool)
    assert isinstance(summary["has_custom_selection"], bool)
    assert isinstance(summary["device_selection_method"], str)
    assert summary["device_selection_method"] in ["default", "custom"]

def test_device_selection_workflow(device_manager):
    """Test complete device selection workflow."""
    # 1. Get initial device selection summary
    initial_summary = device_manager.get_device_selection_summary()
    assert isinstance(initial_summary, dict)
    
    # 2. List available devices
    formatted_devices = device_manager.list_devices_formatted()
    assert isinstance(formatted_devices, list)
    
    # 3. If we have devices, test selection
    if formatted_devices:
        # Get first available device
        test_device = formatted_devices[0]
        device_id = test_device["device_id"]
        
        # Select the device
        success = device_manager.select_device(device_id)
        assert isinstance(success, bool)
        
        if success:
            # 4. Verify selection was applied
            updated_summary = device_manager.get_device_selection_summary()
            assert updated_summary["current_device"]["id"] == device_id
            assert updated_summary["has_custom_selection"] == True
            assert updated_summary["device_selection_method"] == "custom"
            
            # 5. Reset to default
            reset_success = device_manager.reset_to_default_device()
            assert isinstance(reset_success, bool)

def test_device_selection_persistence(device_manager):
    """Test that device selection persists across manager instances."""
    # Get available devices
    formatted_devices = device_manager.list_devices_formatted()
    if not formatted_devices:
        pytest.skip("No devices available for testing")
    
    # Select a device
    test_device = formatted_devices[0]
    device_id = test_device["device_id"]
    success = device_manager.select_device(device_id)
    
    if success:
        # Create a new manager instance
        new_manager = AudioDeviceManager(config_file=device_manager.config_file)
        
        # Verify selection persisted
        assert new_manager.config.device_id == device_id
        assert new_manager.config.device_name == test_device["name"]

def test_device_selection_validation(device_manager):
    """Test device selection validation."""
    # Test selecting an invalid device ID
    success = device_manager.select_device(99999)  # Invalid device ID
    assert success == False  # Should fail
    
    # Test selecting a valid device (if available)
    formatted_devices = device_manager.list_devices_formatted()
    if formatted_devices:
        valid_device = None
        for device in formatted_devices:
            if device["is_valid_for_w4l"]:
                valid_device = device
                break
        
        if valid_device:
            success = device_manager.select_device(valid_device["device_id"])
            assert isinstance(success, bool)

def test_device_selection_by_name(device_manager):
    """Test device selection by name functionality."""
    # Get available devices
    devices = device_manager.get_available_devices()
    if not devices:
        pytest.skip("No devices available for testing")
    
    # Test selection by exact name
    device_name = devices[0].name
    success = device_manager.select_device_by_name(device_name)
    assert isinstance(success, bool)
    
    # Test selection by partial name
    if len(device_name) > 5:
        partial_name = device_name[:5]
        success = device_manager.select_device_by_name(partial_name)
        assert isinstance(success, bool)
    
    # Test selection by non-existent name
    success = device_manager.select_device_by_name("NON_EXISTENT_DEVICE_12345")
    assert success == False 