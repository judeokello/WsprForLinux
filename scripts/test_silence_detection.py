#!/usr/bin/env python3
"""
Test script for silence detection with background noise handling.

This script demonstrates how the silence detector can learn and adapt to
constant background noise like laptop fans, air conditioning, etc.
"""

import sys
import os
import time
import logging
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.silence_detector import SilenceDetector, SilenceConfig, DetectionStrategy
from audio.recorder import AudioRecorder, StreamError
import sounddevice as sd

def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def print_silence_status(detector: SilenceDetector):
    """Print current silence detection status."""
    status = detector.get_status()
    print(f"\n=== Silence Detection Status ===")
    print(f"Active: {status['is_active']}")
    print(f"Learning: {status['is_learning']}")
    print(f"Speech Detected: {status['speech_detected']}")
    print(f"Learned Noise Floor: {status['learned_noise_floor']:.6f}")
    print(f"Adaptive Threshold: {status['adaptive_threshold']:.6f}")
    print(f"Noise Samples: {status['noise_samples']}")
    print(f"Detection Count: {status['detection_count']}")
    print(f"Buffer Size: {status['buffer_size']}")
    print("=" * 35)

def test_silence_detection():
    """Test the silence detection system."""
    print("🎤 Testing Silence Detection with Background Noise Handling")
    print("=" * 60)
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger("test_silence")
    
    # Create silence detection configuration
    config = SilenceConfig(
        rms_threshold=0.01,
        spectral_threshold=0.005,
        energy_threshold=0.008,
        silence_duration=3.0,  # Shorter for testing
        min_speech_duration=0.5,
        noise_learning_duration=2.0,  # Shorter for testing
        adaptation_rate=0.1,
        noise_margin=1.5,
        primary_strategy=DetectionStrategy.HYBRID,
        enable_adaptive=True,
        enable_spectral=True
    )
    
    # Create silence detector
    detector = SilenceDetector(config)
    
    # Set up callbacks
    def on_silence_detected():
        print("\n🔇 SILENCE DETECTED - Recording should stop")
        print_silence_status(detector)
    
    def on_speech_detected():
        print("\n🎤 SPEECH DETECTED - Recording started")
        print_silence_status(detector)
    
    def on_noise_learned(noise_level: float):
        print(f"\n🎧 NOISE FLOOR LEARNED: {noise_level:.6f}")
        print("The detector has learned your background noise level.")
        print("It will now adapt to this level for better silence detection.")
        print_silence_status(detector)
    
    detector.on_silence_detected = on_silence_detected
    detector.on_speech_detected = on_speech_detected
    detector.on_noise_learned = on_noise_learned
    
    # Get available audio devices
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        try:
            # Check if device has input capabilities
            if device.get('max_inputs', 0) > 0:  # type: ignore
                input_devices.append((i, device))
        except (KeyError, TypeError):
            continue
    
    print(f"\n📱 Available input devices:")
    for device_id, device in input_devices:
        print(f"  {device_id}: {device.get('name', 'Unknown')}")  # type: ignore
    
    # Select device (use default if available)
    if input_devices:
        device_id = input_devices[0][0]  # Use first available device
        device_name = input_devices[0][1].get('name', 'Unknown')  # type: ignore
    else:
        device_id = 0
        device_name = "Default"
    
    print(f"\n🎯 Using device: {device_name} (ID: {device_id})")
    
    # Create audio recorder with silence detection
    try:
        recorder = AudioRecorder(
            device_id=device_id,
            sample_rate=16000,
            channels=1,
            blocksize=1024,
            silence_config=config
        )
        
        # Set up recorder callbacks
        recorder.set_silence_callbacks(
            on_silence_detected=on_silence_detected,
            on_speech_detected=on_speech_detected,
            on_noise_learned=on_noise_learned
        )
        
        print("\n🚀 Starting audio recording with silence detection...")
        print("The system will:")
        print("1. Learn your background noise (like laptop fan) for 2 seconds")
        print("2. Start detecting speech when you speak")
        print("3. Automatically stop after 3 seconds of silence")
        print("\nPress Ctrl+C to stop the test")
        
        # Start recording
        recorder.start()
        
        # Monitor status
        start_time = time.time()
        while True:
            time.sleep(1)
            
            # Print periodic status
            if int(time.time() - start_time) % 5 == 0:
                silence_status = recorder.get_silence_status()
                print(f"\n⏱️  Runtime: {int(time.time() - start_time)}s")
                print(f"Learning: {silence_status['is_learning']}")
                print(f"Speech: {silence_status['speech_detected']}")
                print(f"Noise Floor: {silence_status['learned_noise_floor']:.6f}")
                print(f"Threshold: {silence_status['adaptive_threshold']:.6f}")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping test...")
    except StreamError as e:
        print(f"\n❌ Stream error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clean up
        if 'recorder' in locals():
            recorder.stop()
        detector.stop()
        print("✅ Test completed")

def test_standalone_detector():
    """Test the silence detector with simulated audio data."""
    print("\n🧪 Testing Standalone Silence Detector with Simulated Audio")
    print("=" * 60)
    
    # Create configuration
    config = SilenceConfig(
        silence_duration=2.0,
        noise_learning_duration=1.0,
        primary_strategy=DetectionStrategy.ADAPTIVE
    )
    
    # Create detector
    detector = SilenceDetector(config)
    
    # Set up callbacks
    def on_silence():
        print("🔇 Silence detected in simulated audio")
    
    def on_speech():
        print("🎤 Speech detected in simulated audio")
    
    def on_noise(level):
        print(f"🎧 Noise floor learned: {level:.6f}")
    
    detector.on_silence_detected = on_silence
    detector.on_speech_detected = on_speech
    detector.on_noise_learned = on_noise
    
    # Start detector
    detector.start()
    
    # Simulate background noise (constant low-level noise)
    print("Simulating background noise (like laptop fan)...")
    for i in range(100):  # 1 second of background noise
        noise = np.random.normal(0, 0.005, 1024)  # Low-level noise
        detector.add_audio_data(noise)
        time.sleep(0.01)
    
    # Simulate speech
    print("Simulating speech...")
    for i in range(50):  # 0.5 seconds of speech
        speech = np.random.normal(0, 0.05, 1024)  # Higher level
        detector.add_audio_data(speech)
        time.sleep(0.01)
    
    # Simulate silence
    print("Simulating silence...")
    for i in range(200):  # 2 seconds of silence
        silence = np.random.normal(0, 0.005, 1024)  # Back to low-level noise
        detector.add_audio_data(silence)
        time.sleep(0.01)
    
    # Stop detector
    detector.stop()
    
    # Print final status
    status = detector.get_status()
    print(f"\nFinal Status:")
    print(f"Detections: {status['detection_count']}")
    print(f"Learned Noise: {status['learned_noise_floor']:.6f}")
    print(f"Adaptive Threshold: {status['adaptive_threshold']:.6f}")

if __name__ == "__main__":
    print("🎯 W4L Silence Detection Test")
    print("This test demonstrates how the system handles background noise like laptop fans")
    print()
    
    try:
        # Test standalone detector first
        test_standalone_detector()
        
        # Test with real audio
        print("\n" + "="*60)
        test_silence_detection()
        
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 