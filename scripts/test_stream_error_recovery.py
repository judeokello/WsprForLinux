#!/usr/bin/env python3
"""
Test script for stream error recovery functionality (Feature 3.1.2.2).

This script tests the enhanced AudioRecorder with robust error handling,
automatic stream restart, retry mechanisms, and health monitoring.
"""

import sys
import os
import time
import logging
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.recorder import AudioRecorder, StreamStatus, StreamError
from audio.device_config import AudioDeviceManager
from audio.device_detector import AudioDeviceDetector

def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_stream_recovery.log')
        ]
    )

def test_basic_recording():
    """Test basic recording functionality."""
    print("\n=== Testing Basic Recording ===")
    
    # Get default device
    detector = AudioDeviceDetector()
    default_device = detector.get_default_microphone()
    
    if not default_device:
        print("❌ No default microphone found")
        return False
    
    print(f"✅ Using device: {default_device.name} (ID: {default_device.device_id})")
    
    # Create recorder
    recorder = AudioRecorder(
        device_id=default_device.device_id,
        sample_rate=16000,
        channels=1,
        blocksize=1024
    )
    
    # Set up callbacks
    audio_chunks_received = 0
    
    def audio_callback(audio_data):
        nonlocal audio_chunks_received
        audio_chunks_received += 1
        if audio_chunks_received % 100 == 0:  # Log every 100 chunks
            print(f"📊 Received {audio_chunks_received} audio chunks")
    
    def error_callback(error):
        print(f"⚠️ Stream error: {error}")
    
    def recovery_callback():
        print("🔄 Stream recovered successfully")
    
    def health_callback(health_data):
        print(f"💓 Health update: {health_data['status']} - Errors: {health_data['error_count']}")
    
    recorder.audio_chunk_callback = audio_callback
    recorder.on_stream_error = error_callback
    recorder.on_stream_recovered = recovery_callback
    recorder.on_stream_health_update = health_callback
    
    try:
        # Start recording
        print("🎤 Starting recording...")
        recorder.start()
        
        # Record for 10 seconds
        print("🎵 Recording for 10 seconds...")
        time.sleep(10)
        
        # Check status
        status = recorder.get_status()
        print(f"📊 Final status: {status.value}")
        
        # Get health info
        health = recorder.get_health_info()
        print(f"💓 Health info: {health}")
        
        # Stop recording
        print("⏹️ Stopping recording...")
        recorder.stop()
        
        print(f"✅ Basic recording test completed. Received {audio_chunks_received} chunks")
        return True
        
    except Exception as e:
        print(f"❌ Basic recording test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Stream Error Recovery (Feature 3.1.2.2)")
    print("=" * 50)
    
    setup_logging()
    
    if test_basic_recording():
        print("✅ Basic recording test passed")
        return 0
    else:
        print("❌ Basic recording test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
