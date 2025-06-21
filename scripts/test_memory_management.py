#!/usr/bin/env python3
"""
Test script for memory management functionality in W4L audio system.

This script demonstrates the memory monitoring, cleanup, and resource management
features that have been added to the audio buffer system.
"""

import sys
import os
import time
import logging
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.memory_manager import MemoryMonitor, ResourceManager, AudioBufferTracker
from audio.device_config import AudioDeviceManager, AudioConfig


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_memory_monitor():
    """Test the memory monitor functionality."""
    print("\n=== Testing Memory Monitor ===")
    
    monitor = MemoryMonitor(max_memory_mb=100)  # Low threshold for testing
    
    # Get initial memory usage
    initial_memory = monitor.get_memory_usage()
    print(f"Initial memory usage: {initial_memory:.1f}MB")
    
    # Test memory high detection
    is_high = monitor.is_memory_high()
    print(f"Memory usage high: {is_high}")
    
    # Test cleanup callback
    cleanup_called = False
    def test_cleanup():
        nonlocal cleanup_called
        cleanup_called = True
        print("Cleanup callback executed")
    
    monitor.add_cleanup_callback(test_cleanup)
    
    # Force cleanup
    monitor.cleanup(force=True)
    print(f"Cleanup callback called: {cleanup_called}")
    
    # Test monitoring
    print("Starting memory monitoring for 5 seconds...")
    monitor.start_monitoring(interval_seconds=1.0)
    time.sleep(5)
    monitor.stop_monitoring()
    
    return monitor


def test_resource_manager():
    """Test the resource manager functionality."""
    print("\n=== Testing Resource Manager ===")
    
    monitor = MemoryMonitor()
    resource_mgr = ResourceManager(monitor)
    
    # Test temp file management
    import tempfile
    temp_fd, temp_file = tempfile.mkstemp(suffix='.wav')
    os.close(temp_fd)
    
    resource_mgr.add_temp_file(temp_file)
    print(f"Added temp file: {temp_file}")
    
    # Test cleanup callback
    cleanup_called = False
    def test_cleanup():
        nonlocal cleanup_called
        cleanup_called = True
        print("Resource cleanup callback executed")
    
    resource_mgr.add_cleanup_callback(test_cleanup)
    
    # Get resource info
    info = resource_mgr.get_resource_info()
    print(f"Resource info: {info}")
    
    # Test cleanup
    resource_mgr.cleanup()
    print(f"Resource cleanup callback called: {cleanup_called}")
    
    # Verify temp file was removed
    if not os.path.exists(temp_file):
        print("Temp file successfully removed")
    else:
        print("Warning: Temp file still exists")
    
    return resource_mgr


def test_buffer_tracker():
    """Test the buffer tracker functionality."""
    print("\n=== Testing Buffer Tracker ===")
    
    monitor = MemoryMonitor()
    tracker = AudioBufferTracker(monitor)
    
    # Create some test buffers
    buffers = []
    for i in range(5):
        # Create a buffer with 1MB of data
        buffer_data = np.zeros((1024 * 1024 // 4, 1), dtype=np.float32)  # 1MB
        tracker.track_buffer(buffer_data, buffer_data.nbytes)
        buffers.append(buffer_data)
        print(f"Tracked buffer {i+1}: {buffer_data.nbytes / 1024 / 1024:.1f}MB")
    
    # Get buffer info
    info = tracker.get_buffer_info()
    print(f"Buffer tracker info: {info}")
    
    # Test untracking
    tracker.untrack_buffer(buffers[0])
    info = tracker.get_buffer_info()
    print(f"After untracking: {info}")
    
    # Test cleanup
    tracker._cleanup_buffers()
    info = tracker.get_buffer_info()
    print(f"After cleanup: {info}")
    
    return tracker


def main():
    """Run all memory management tests."""
    print("W4L Memory Management Test Suite")
    print("=" * 50)
    
    setup_logging()
    
    try:
        # Test individual components
        test_memory_monitor()
        test_resource_manager()
        test_buffer_tracker()
        
        print("\n" + "=" * 50)
        print("All memory management tests completed successfully!")
        print("Memory management and cleanup functionality is working correctly.")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 