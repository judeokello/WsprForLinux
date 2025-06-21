#!/usr/bin/env python3
"""
Test script for device configuration functionality (1.4.1.2).

This script demonstrates:
- Auto-configuring the default microphone
- Testing device recording
- Getting device status
- Resetting configuration

Run with: python scripts/test_device_configuration.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.device_config import AudioDeviceManager
from audio.device_detector import AudioDeviceDetector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    """Demonstrate device configuration functionality."""
    print("=== W4L Device Configuration Test (1.4.1.2) ===\n")
    
    # Create device manager
    print("1. Creating device manager...")
    device_manager = AudioDeviceManager()
    
    # Show available devices
    print("\n2. Available input devices:")
    detector = AudioDeviceDetector()
    devices = detector.get_input_devices()
    
    if not devices:
        print("   No input devices found!")
        return
    
    for device in devices:
        status = " (DEFAULT)" if device.is_default_input else ""
        print(f"   ID {device.device_id}: {device.name}{status}")
    
    # Get initial status
    print("\n3. Initial device status:")
    initial_status = device_manager.get_device_status()
    for key, value in initial_status.items():
        print(f"   {key}: {value}")
    
    # Auto-configure default device
    print("\n4. Auto-configuring default microphone...")
    success = device_manager.auto_configure_default_device()
    
    if success:
        print("   ✅ Auto-configuration successful!")
    else:
        print("   ❌ Auto-configuration failed!")
        return
    
    # Get updated status
    print("\n5. Updated device status:")
    updated_status = device_manager.get_device_status()
    for key, value in updated_status.items():
        print(f"   {key}: {value}")
    
    # Test device recording
    print("\n6. Testing device recording (2 seconds)...")
    print("   Please speak into your microphone...")
    recording_success = device_manager.test_device_recording(duration=2.0)
    
    if recording_success:
        print("   ✅ Device recording test passed!")
    else:
        print("   ❌ Device recording test failed!")
    
    # Show configuration summary
    print("\n7. Configuration summary:")
    summary = device_manager.get_config_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print("\n=== Test Complete ===")
    print("The device is now configured and ready for W4L!")

if __name__ == "__main__":
    main() 