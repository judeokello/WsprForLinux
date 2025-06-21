#!/usr/bin/env python3
"""
Debug script to understand sounddevice device information.
"""

import sounddevice as sd
import json

def debug_devices():
    """Debug the device information returned by sounddevice."""
    print("Debugging sounddevice device information")
    print("=" * 50)
    
    # Get all devices
    devices = sd.query_devices()
    print(f"Total devices found: {len(devices)}")
    
    print("\nRaw device information:")
    for i, device in enumerate(devices):
        print(f"\nDevice {i}:")
        print(f"  Raw data: {device}")
        print(f"  Type: {type(device)}")
        
        # Check if device is a dictionary-like object
        if hasattr(device, 'keys') and callable(getattr(device, 'keys', None)):
            print(f"  Keys: {list(device.keys())}")
            
            # Try to access common fields
            try:
                print(f"  name: {device.get('name', 'N/A')}")
                print(f"  max_inputs: {device.get('max_inputs', 'N/A')}")
                print(f"  max_outputs: {device.get('max_outputs', 'N/A')}")
                print(f"  default_samplerate: {device.get('default_samplerate', 'N/A')}")
            except Exception as e:
                print(f"  Error accessing fields: {e}")
        else:
            print(f"  Keys: No keys (not a dictionary-like object)")
            print(f"  Device data: {device}")
    
    print("\n" + "=" * 50)
    print("Default devices:")
    try:
        print(f"Default input device: {sd.default.device[0]}")
        print(f"Default output device: {sd.default.device[1]}")
    except Exception as e:
        print(f"Error getting defaults: {e}")
    
    print("\n" + "=" * 50)
    print("Testing specific device queries:")
    for i in range(min(5, len(devices))):
        try:
            device_info = sd.query_devices(i)
            print(f"Device {i} info: {device_info}")
        except Exception as e:
            print(f"Error querying device {i}: {e}")

if __name__ == "__main__":
    debug_devices() 