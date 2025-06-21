#!/usr/bin/env python3
"""
Test script for device selection functionality (1.4.1.4).

This script demonstrates:
- Listing available input devices with detailed information
- Selecting devices by ID or name
- Interactive device selection
- Resetting to default device
- Device selection persistence

Run with: python scripts/test_device_selection.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.device_config import AudioDeviceManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    """Demonstrate device selection functionality."""
    print("=== W4L Device Selection Test (1.4.1.4) ===\n")
    
    # Create device manager
    print("1. Creating device manager...")
    device_manager = AudioDeviceManager()
    
    # Auto-configure device first
    print("\n2. Auto-configuring default device...")
    success = device_manager.auto_configure_default_device()
    if not success:
        print("   ❌ Failed to configure device, but continuing...")
    
    # Show device selection summary
    print("\n3. Current Device Selection Summary:")
    summary = device_manager.get_device_selection_summary()
    for key, value in summary.items():
        if key == "current_device":
            print(f"   {key}:")
            for subkey, subvalue in value.items():
                print(f"     {subkey}: {subvalue}")
        else:
            print(f"   {key}: {value}")
    
    # List available devices
    print("\n4. Available Input Devices:")
    device_manager.print_device_list()
    
    # Get formatted device list
    print("\n5. Formatted Device Information:")
    formatted_devices = device_manager.list_devices_formatted()
    for device in formatted_devices:
        print(f"   ID {device['device_id']}: {device['name']}")
        print(f"     Channels: {device['channels']}, Sample Rate: {device['sample_rate']}")
        print(f"     Status: {device['status']}")
        print(f"     Valid for W4L: {'✅' if device['is_valid_for_w4l'] else '❌'}")
        if not device['is_valid_for_w4l']:
            print(f"     Validation Message: {device['validation_message']}")
        print()
    
    # Test device selection (if devices available)
    if formatted_devices:
        print("6. Testing Device Selection:")
        
        # Find a valid device to test with
        test_device = None
        for device in formatted_devices:
            if device['is_valid_for_w4l'] and not device['is_current']:
                test_device = device
                break
        
        if test_device:
            print(f"   Testing selection of device: {test_device['name']} (ID: {test_device['device_id']})")
            
            # Select the device
            success = device_manager.select_device(test_device['device_id'])
            if success:
                print(f"   ✅ Successfully selected device ID {test_device['device_id']}")
                
                # Show updated summary
                updated_summary = device_manager.get_device_selection_summary()
                print(f"   Current device: {updated_summary['current_device']['name']}")
                print(f"   Selection method: {updated_summary['device_selection_method']}")
                
                # Reset to default
                print("\n   Resetting to default device...")
                reset_success = device_manager.reset_to_default_device()
                if reset_success:
                    print("   ✅ Successfully reset to default device")
                else:
                    print("   ❌ Failed to reset to default device")
            else:
                print(f"   ❌ Failed to select device ID {test_device['device_id']}")
        else:
            print("   No additional valid devices available for testing")
    
    # Test device selection by name
    print("\n7. Testing Device Selection by Name:")
    devices = device_manager.get_available_devices()
    if devices:
        # Try selecting by partial name
        device_name = devices[0].name
        if len(device_name) > 5:
            partial_name = device_name[:5]
            print(f"   Testing selection by partial name: '{partial_name}'")
            success = device_manager.select_device_by_name(partial_name)
            print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Show final configuration
    print("\n8. Final Configuration:")
    device_manager.print_config()
    
    print("\n=== Device Selection Test Complete ===")
    print("The device selection system is ready for integration with CLI and GUI!")

if __name__ == "__main__":
    main() 