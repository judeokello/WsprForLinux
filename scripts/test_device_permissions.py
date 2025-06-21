#!/usr/bin/env python3
"""
Test script for device permission checking functionality (1.4.1.3).

This script demonstrates:
- Testing device permissions across different Linux environments
- Checking PulseAudio, ALSA, and PipeWire access
- Detecting sandboxed environments (Flatpak, Snap, containers)
- Providing permission fix suggestions

Run with: python scripts/test_device_permissions.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.device_config import AudioDeviceManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    """Demonstrate device permission checking functionality."""
    print("=== W4L Device Permission Test (1.4.1.3) ===\n")
    
    # Create device manager
    print("1. Creating device manager...")
    device_manager = AudioDeviceManager()
    
    # Auto-configure device first
    print("\n2. Auto-configuring default device...")
    success = device_manager.auto_configure_default_device()
    if not success:
        print("   ❌ Failed to configure device, but continuing with permission test...")
    
    # Test device permissions
    print("\n3. Testing device permissions...")
    permission_status = device_manager.test_device_permissions()
    
    # Display permission status
    print("\n4. Permission Status:")
    print(f"   Device: {permission_status['device_name']} (ID: {permission_status['device_id']})")
    print(f"   Has Permissions: {'✅ Yes' if permission_status['has_permissions'] else '❌ No'}")
    
    if not permission_status['has_permissions'] and 'error' in permission_status:
        print(f"   Error: {permission_status['error']}")
    
    # Display detailed permission information
    print("\n5. Detailed Permission Information:")
    details = permission_status.get('details', {})
    
    for key, value in details.items():
        if isinstance(value, bool):
            status = "✅ Yes" if value else "❌ No"
            print(f"   {key.replace('_', ' ').title()}: {status}")
        elif isinstance(value, str):
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Get permission requirements
    print("\n6. Permission Requirements:")
    requirements = device_manager.get_permission_requirements()
    
    for environment, info in requirements.items():
        print(f"   {environment.replace('_', ' ').title()}:")
        if isinstance(info, dict):
            for key, value in info.items():
                print(f"     {key}: {value}")
        else:
            print(f"     {info}")
    
    # Get permission fix suggestions
    if not permission_status['has_permissions']:
        print("\n7. Suggested Fixes:")
        suggestions = device_manager.suggest_permission_fix(permission_status)
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
        else:
            print("   No specific suggestions available")
    
    # Summary
    print("\n=== Permission Test Summary ===")
    if permission_status['has_permissions']:
        print("✅ Device permissions are working correctly!")
        print("   W4L should be able to access the microphone.")
    else:
        print("❌ Device permissions need to be configured.")
        print("   Please follow the suggested fixes above.")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 