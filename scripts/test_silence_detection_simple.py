#!/usr/bin/env python3
"""
Simple test script for silence detection with background noise handling.

This script demonstrates how the silence detector can learn and adapt to
constant background noise like laptop fans using simulated audio data.
"""

import sys
import time
import logging
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.silence_detector import SilenceDetector, SilenceConfig, DetectionStrategy

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

def test_laptop_fan_scenario():
    """Test silence detection with simulated laptop fan noise."""
    print("🖥️  Testing Silence Detection with Laptop Fan Noise")
    print("=" * 60)
    
    # Create configuration optimized for laptop fan noise
    config = SilenceConfig(
        rms_threshold=0.01,
        spectral_threshold=0.005,
        energy_threshold=0.008,
        silence_duration=3.0,
        min_speech_duration=0.5,
        noise_learning_duration=2.0,
        adaptation_rate=0.1,
        noise_margin=1.8,  # Higher margin for fan noise
        primary_strategy=DetectionStrategy.HYBRID,
        enable_adaptive=True,
        enable_spectral=True
    )
    
    # Create detector
    detector = SilenceDetector(config)
    
    # Set up callbacks
    def on_silence():
        print("\n🔇 SILENCE DETECTED - Recording should stop")
        print_silence_status(detector)
    
    def on_speech():
        print("\n🎤 SPEECH DETECTED - Recording started")
        print_silence_status(detector)
    
    def on_noise(level):
        print(f"\n🎧 NOISE FLOOR LEARNED: {level:.6f}")
        print("✅ The detector has learned your laptop fan noise level!")
        print("🎯 It will now adapt to this level for better silence detection.")
        print_silence_status(detector)
    
    detector.on_silence_detected = on_silence
    detector.on_speech_detected = on_speech
    detector.on_noise_learned = on_noise
    
    # Start detector
    detector.start()
    
    print("\n📊 Simulating audio scenario with laptop fan noise...")
    print("1. Background noise (laptop fan) - 2 seconds")
    print("2. Speech - 1 second")
    print("3. Silence (back to fan noise) - 3 seconds")
    print()
    
    # Phase 1: Background noise (laptop fan)
    print("🖥️  Phase 1: Learning background noise (laptop fan)...")
    for i in range(200):  # 2 seconds of background noise
        # Simulate laptop fan noise (constant, low-frequency)
        fan_noise = np.random.normal(0, 0.008, 1024)  # Constant fan noise
        detector.add_audio_data(fan_noise)
        time.sleep(0.01)
    
    # Phase 2: Speech over background noise
    print("🎤 Phase 2: Speech over background noise...")
    for i in range(100):  # 1 second of speech
        # Speech + background noise
        speech = np.random.normal(0, 0.06, 1024)  # Speech signal
        fan_noise = np.random.normal(0, 0.008, 1024)  # Background fan noise
        combined = speech + fan_noise
        detector.add_audio_data(combined)
        time.sleep(0.01)
    
    # Phase 3: Return to background noise (silence)
    print("🔇 Phase 3: Silence (back to background noise)...")
    for i in range(300):  # 3 seconds of background noise
        fan_noise = np.random.normal(0, 0.008, 1024)  # Back to fan noise
        detector.add_audio_data(fan_noise)
        time.sleep(0.01)
    
    # Stop detector
    detector.stop()
    
    # Print final results
    status = detector.get_status()
    print(f"\n🎯 Final Results:")
    print(f"✅ Detections: {status['detection_count']}")
    print(f"🎧 Learned Noise Floor: {status['learned_noise_floor']:.6f}")
    print(f"🎯 Adaptive Threshold: {status['adaptive_threshold']:.6f}")
    print(f"📊 Noise Margin: {status['adaptive_threshold'] / status['learned_noise_floor']:.2f}x")
    
    return status['detection_count'] > 0

def test_different_noise_levels():
    """Test silence detection with different noise levels."""
    print("\n🔊 Testing Different Noise Levels")
    print("=" * 60)
    
    noise_levels = [0.005, 0.01, 0.015, 0.02]  # Different fan noise levels
    
    for noise_level in noise_levels:
        print(f"\n🧪 Testing with noise level: {noise_level:.3f}")
        
        config = SilenceConfig(
            noise_learning_duration=1.0,
            adaptation_rate=0.15,
            noise_margin=1.5,
            primary_strategy=DetectionStrategy.ADAPTIVE
        )
        
        detector = SilenceDetector(config)
        
        def on_silence():
            print(f"  🔇 Silence detected")
        
        def on_speech():
            print(f"  🎤 Speech detected")
        
        def on_noise(level):
            print(f"  🎧 Learned noise: {level:.6f}")
        
        detector.on_silence_detected = on_silence
        detector.on_speech_detected = on_speech
        detector.on_noise_learned = on_noise
        
        detector.start()
        
        # Learn noise
        for i in range(100):
            noise = np.random.normal(0, noise_level, 1024)
            detector.add_audio_data(noise)
            time.sleep(0.01)
        
        # Add speech
        for i in range(50):
            speech = np.random.normal(0, noise_level * 8, 1024)  # 8x louder than noise
            detector.add_audio_data(speech)
            time.sleep(0.01)
        
        # Return to noise
        for i in range(150):
            noise = np.random.normal(0, noise_level, 1024)
            detector.add_audio_data(noise)
            time.sleep(0.01)
        
        detector.stop()
        
        status = detector.get_status()
        print(f"  ✅ Detections: {status['detection_count']}")
        print(f"  🎯 Threshold: {status['adaptive_threshold']:.6f}")

def test_detection_strategies():
    """Test different silence detection strategies."""
    print("\n🎯 Testing Different Detection Strategies")
    print("=" * 60)
    
    strategies = [
        DetectionStrategy.RMS,
        DetectionStrategy.SPECTRAL,
        DetectionStrategy.ADAPTIVE,
        DetectionStrategy.HYBRID
    ]
    
    for strategy in strategies:
        print(f"\n🧪 Testing strategy: {strategy.value}")
        
        config = SilenceConfig(
            primary_strategy=strategy,
            noise_learning_duration=1.0,
            silence_duration=2.0
        )
        
        detector = SilenceDetector(config)
        
        def on_silence():
            print(f"  🔇 Silence detected")
        
        def on_speech():
            print(f"  🎤 Speech detected")
        
        detector.on_silence_detected = on_silence
        detector.on_speech_detected = on_speech
        
        detector.start()
        
        # Background noise
        for i in range(100):
            noise = np.random.normal(0, 0.008, 1024)
            detector.add_audio_data(noise)
            time.sleep(0.01)
        
        # Speech
        for i in range(50):
            speech = np.random.normal(0, 0.05, 1024)
            detector.add_audio_data(speech)
            time.sleep(0.01)
        
        # Silence
        for i in range(200):
            noise = np.random.normal(0, 0.008, 1024)
            detector.add_audio_data(noise)
            time.sleep(0.01)
        
        detector.stop()
        
        status = detector.get_status()
        print(f"  ✅ Detections: {status['detection_count']}")

if __name__ == "__main__":
    print("🎯 W4L Silence Detection - Background Noise Handling Test")
    print("This test demonstrates how the system handles laptop fan noise")
    print()
    
    # Set up logging
    setup_logging()
    
    try:
        # Test main scenario
        success = test_laptop_fan_scenario()
        
        if success:
            print("\n🎉 SUCCESS: Silence detection worked with laptop fan noise!")
        else:
            print("\n❌ FAILED: No silence detections occurred")
        
        # Test different noise levels
        test_different_noise_levels()
        
        # Test different strategies
        test_detection_strategies()
        
        print("\n✅ All tests completed!")
        print("\n💡 Key Features Demonstrated:")
        print("• Adaptive noise floor learning")
        print("• Background noise handling (like laptop fans)")
        print("• Multiple detection strategies")
        print("• Configurable thresholds and margins")
        print("• Real-time audio analysis")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 