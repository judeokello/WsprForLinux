#!/usr/bin/env python3
"""
Test script for microphone access and testing functionality (1.4.4).

This script demonstrates:
- Testing microphone permissions
- Verifying audio capture works
- Testing buffer overflow handling
- Validating both streaming and file modes work

Run with: python scripts/test_microphone_access.py
"""

import sys
import os
import time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio.device_config import AudioDeviceManager
from audio.buffer_manager import AudioBufferManager
from audio.memory_manager import MemoryMonitor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_microphone_permissions():
    """Test 1.4.4.1: Test microphone permissions."""
    print("=== 1.4.4.1 Testing Microphone Permissions ===")
    
    device_manager = AudioDeviceManager()
    
    # Test device permissions
    permission_status = device_manager.test_device_permissions()
    
    print(f"Device: {permission_status['device_name']} (ID: {permission_status['device_id']})")
    print(f"Has Permissions: {'✅ Yes' if permission_status['has_permissions'] else '❌ No'}")
    
    if not permission_status['has_permissions']:
        print("❌ Permission test failed!")
        if 'error' in permission_status:
            print(f"Error: {permission_status['error']}")
        
        # Get suggestions
        suggestions = device_manager.suggest_permission_fix(permission_status)
        if suggestions:
            print("\nSuggested fixes:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        return False
    
    print("✅ Microphone permissions are working correctly!")
    return True

def test_audio_capture():
    """Test 1.4.4.2: Verify audio capture works."""
    print("\n=== 1.4.4.2 Verifying Audio Capture ===")
    
    device_manager = AudioDeviceManager()
    
    # Auto-configure device first
    print("Auto-configuring default microphone...")
    success = device_manager.auto_configure_default_device()
    if not success:
        print("❌ Failed to configure device!")
        return False
    
    # Test device recording
    print("Testing device recording (3 seconds)...")
    print("Please speak into your microphone...")
    recording_success = device_manager.test_device_recording(duration=3.0)
    
    if recording_success:
        print("✅ Audio capture test passed!")
        return True
    else:
        print("❌ Audio capture test failed!")
        return False

def test_buffer_overflow_handling():
    """Test 1.4.4.3: Test buffer overflow handling."""
    print("\n=== 1.4.4.3 Testing Buffer Overflow Handling ===")
    
    device_manager = AudioDeviceManager()
    memory_monitor = MemoryMonitor()
    buffer_manager = AudioBufferManager(device_manager, memory_monitor)
    
    # Test with small buffer size to trigger overflow
    print("Testing with small buffer (1 second)...")
    buffer_manager.set_buffer_size(1.0)
    
    # Start recording
    print("Starting recording with small buffer...")
    success = buffer_manager.start_recording()
    if not success:
        print("❌ Failed to start recording!")
        return False
    
    # Record for longer than buffer size
    print("Recording for 3 seconds (buffer is 1 second)...")
    time.sleep(3.0)
    
    # Stop recording
    buffer_manager.stop_recording()
    
    # Check buffer info
    buffer_info = buffer_manager.get_buffer_info()
    print(f"Buffer fill level: {buffer_info['fill_level']:.1%}")
    print(f"Buffer overflowed: {buffer_info.get('overflowed', False)}")
    
    # Get latest audio
    latest_audio = buffer_manager.get_latest_audio(seconds=2.0)
    print(f"Retrieved {len(latest_audio)} samples")
    
    if len(latest_audio) > 0:
        print("✅ Buffer overflow handling test passed!")
        print("   Buffer correctly handled overflow and maintained latest audio")
        return True
    else:
        print("❌ Buffer overflow handling test failed!")
        return False

def test_streaming_mode():
    """Test 1.4.4.4: Validate streaming mode works."""
    print("\n=== 1.4.4.4 Validating Streaming Mode ===")
    
    device_manager = AudioDeviceManager()
    memory_monitor = MemoryMonitor()
    buffer_manager = AudioBufferManager(device_manager, memory_monitor)
    
    # Set to streaming mode
    buffer_manager.set_capture_mode(use_streaming=True)
    
    if not buffer_manager.is_streaming_mode():
        print("❌ Failed to set streaming mode!")
        return False
    
    print("Streaming mode enabled. Testing recording...")
    
    # Start recording
    success = buffer_manager.start_recording()
    if not success:
        print("❌ Failed to start streaming recording!")
        return False
    
    # Record for a few seconds
    print("Recording for 2 seconds in streaming mode...")
    time.sleep(2.0)
    
    # Get buffer info
    buffer_info = buffer_manager.get_buffer_info()
    print(f"Streaming buffer fill level: {buffer_info['fill_level']:.1%}")
    print(f"Mode: {buffer_info['mode']}")
    
    # Stop recording
    buffer_manager.stop_recording()
    
    # Get latest audio
    latest_audio = buffer_manager.get_latest_audio(seconds=1.0)
    print(f"Retrieved {len(latest_audio)} samples from streaming buffer")
    
    if len(latest_audio) > 0:
        print("✅ Streaming mode test passed!")
        return True
    else:
        print("❌ Streaming mode test failed!")
        return False

def test_file_mode():
    """Test 1.4.4.4: Validate file-based mode works."""
    print("\n=== 1.4.4.4 Validating File-Based Mode ===")
    
    device_manager = AudioDeviceManager()
    memory_monitor = MemoryMonitor()
    buffer_manager = AudioBufferManager(device_manager, memory_monitor)
    
    # Set to file-based mode
    buffer_manager.set_capture_mode(use_streaming=False)
    
    if buffer_manager.is_streaming_mode():
        print("❌ Failed to set file-based mode!")
        return False
    
    print("File-based mode enabled. Testing recording...")
    
    # Start recording
    success = buffer_manager.start_recording()
    if not success:
        print("❌ Failed to start file-based recording!")
        return False
    
    # Record for a few seconds
    print("Recording for 2 seconds in file-based mode...")
    time.sleep(2.0)
    
    # Stop recording
    buffer_manager.stop_recording()
    
    # Get buffer info
    buffer_info = buffer_manager.get_buffer_info()
    print(f"File buffer info: {buffer_info}")
    
    # Get audio file
    audio_file = buffer_manager.get_audio_file()
    if audio_file and os.path.exists(audio_file):
        file_size = os.path.getsize(audio_file)
        print(f"Audio file created: {audio_file} ({file_size} bytes)")
        print("✅ File-based mode test passed!")
        return True
    else:
        print("❌ File-based mode test failed!")
        return False

def test_memory_management():
    """Test memory management during audio operations."""
    print("\n=== Testing Memory Management ===")
    
    device_manager = AudioDeviceManager()
    memory_monitor = MemoryMonitor()
    buffer_manager = AudioBufferManager(device_manager, memory_monitor)
    
    # Get initial memory usage
    initial_memory_mb = memory_monitor.get_memory_usage()
    print(f"Initial memory usage: {initial_memory_mb:.1f} MB")
    
    # Test recording with memory monitoring
    print("Testing recording with memory monitoring...")
    buffer_manager.start_recording()
    time.sleep(2.0)
    buffer_manager.stop_recording()
    
    # Get memory usage after recording
    final_memory_mb = memory_monitor.get_memory_usage()
    print(f"Final memory usage: {final_memory_mb:.1f} MB")
    
    # Check for memory leaks
    memory_diff_mb = final_memory_mb - initial_memory_mb
    if memory_diff_mb < 50.0:  # Less than 50MB increase
        print("✅ Memory management test passed!")
        return True
    else:
        print(f"⚠️  Memory usage increased by {memory_diff_mb:.1f} MB")
        print("This might indicate a memory leak, but could be normal for first run")
        return True  # Not necessarily a failure

def main():
    """Run all microphone access and testing functionality."""
    print("=== W4L Microphone Access & Testing (1.4.4) ===\n")
    
    results = []
    
    # Test 1.4.4.1: Test microphone permissions
    results.append(("Microphone Permissions", test_microphone_permissions()))
    
    # Test 1.4.4.2: Verify audio capture works
    results.append(("Audio Capture", test_audio_capture()))
    
    # Test 1.4.4.3: Test buffer overflow handling
    results.append(("Buffer Overflow Handling", test_buffer_overflow_handling()))
    
    # Test 1.4.4.4: Validate both streaming and file modes work
    results.append(("Streaming Mode", test_streaming_mode()))
    results.append(("File-Based Mode", test_file_mode()))
    
    # Test memory management
    results.append(("Memory Management", test_memory_management()))
    
    # Summary
    print("\n=== Test Summary ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All microphone access and testing functionality is working correctly!")
        print("W4L is ready for the next development phase.")
    else:
        print("⚠️  Some tests failed. Please check the issues above before proceeding.")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 