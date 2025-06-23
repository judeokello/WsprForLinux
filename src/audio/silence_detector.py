#!/usr/bin/env python3
"""
Advanced silence detection for W4L with background noise handling.

This module provides sophisticated silence detection that can handle
constant background noise like laptop fans by implementing:
- Adaptive noise floor detection
- Multiple detection strategies (RMS, spectral, energy-based)
- Background noise learning and adaptation
- Configurable thresholds and durations
"""

import numpy as np
import logging
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from collections import deque

class DetectionStrategy(Enum):
    """Silence detection strategies."""
    RMS = "rms"                    # Root Mean Square energy
    SPECTRAL = "spectral"          # Spectral analysis
    ADAPTIVE = "adaptive"          # Adaptive noise floor
    HYBRID = "hybrid"              # Combination of multiple strategies

@dataclass
class SilenceConfig:
    """Configuration for silence detection."""
    # Basic thresholds
    rms_threshold: float = 0.01
    spectral_threshold: float = 0.005
    energy_threshold: float = 0.008
    
    # Duration settings
    silence_duration: float = 5.0  # seconds
    min_speech_duration: float = 0.5  # minimum speech before silence detection
    
    # Adaptive settings
    noise_learning_duration: float = 3.0  # seconds to learn background noise
    adaptation_rate: float = 0.1  # how quickly to adapt to new noise levels
    noise_margin: float = 1.5  # multiplier above learned noise floor
    
    # Advanced settings
    window_size: int = 1024  # analysis window size
    hop_size: int = 512      # hop size between windows
    fft_size: int = 2048     # FFT size for spectral analysis
    
    # Strategy selection
    primary_strategy: DetectionStrategy = DetectionStrategy.HYBRID
    enable_adaptive: bool = True
    enable_spectral: bool = True

class SilenceDetector:
    """
    Advanced silence detector with background noise handling.
    
    This detector can learn and adapt to constant background noise
    like laptop fans, air conditioning, or other ambient sounds.
    """
    
    def __init__(self, config: Optional[SilenceConfig] = None):
        """
        Initialize the silence detector.
        
        Args:
            config: Configuration for silence detection
        """
        self.logger = logging.getLogger("w4l.audio.silence_detector")
        self.config = config or SilenceConfig()
        
        # State management
        self.is_active = False
        self.is_learning = True
        self.speech_detected = False
        self.last_speech_time = 0.0
        self.silence_start_time = 0.0
        
        # Audio analysis buffers
        self.audio_buffer = deque(maxlen=int(self.config.window_size * 2))
        self.rms_history = deque(maxlen=100)  # RMS values for adaptation
        self.spectral_history = deque(maxlen=100)  # Spectral values for adaptation
        
        # Adaptive noise floor
        self.learned_noise_floor = 0.0
        self.adaptive_threshold = 0.0
        self.noise_samples = 0
        self.min_noise_samples = int(self.config.noise_learning_duration * 16000 / self.config.hop_size)
        
        # Thread safety
        self._lock = threading.Lock()
        self._analysis_thread: Optional[threading.Thread] = None
        self._stop_analysis = threading.Event()
        
        # Callbacks
        self.on_silence_detected: Optional[Callable[[], None]] = None
        self.on_speech_detected: Optional[Callable[[], None]] = None
        self.on_noise_learned: Optional[Callable[[float], None]] = None
        
        # Performance tracking
        self.detection_count = 0
        self.false_positive_count = 0
        self.last_analysis_time = 0.0
        
        self.logger.info("Silence detector initialized")
    
    def start(self) -> None:
        """Start the silence detector."""
        with self._lock:
            if self.is_active:
                self.logger.warning("Silence detector already active")
                return
            
            self.is_active = True
            self.is_learning = True
            self.speech_detected = False
            self.silence_start_time = 0.0
            self.last_speech_time = 0.0
            
            # Reset adaptive parameters
            self.learned_noise_floor = 0.0
            self.adaptive_threshold = 0.0
            self.noise_samples = 0
            
            # Clear buffers
            self.audio_buffer.clear()
            self.rms_history.clear()
            self.spectral_history.clear()
            
            # Start analysis thread
            self._stop_analysis.clear()
            self._analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
            self._analysis_thread.start()
            
            self.logger.info("Silence detector started")
    
    def stop(self) -> None:
        """Stop the silence detector."""
        with self._lock:
            if not self.is_active:
                return
            
            self.is_active = False
            self._stop_analysis.set()
            
            if self._analysis_thread and self._analysis_thread.is_alive():
                self._analysis_thread.join(timeout=2.0)
            
            self.logger.info("Silence detector stopped")
    
    def add_audio_data(self, audio_chunk: np.ndarray) -> None:
        """
        Add audio data for analysis.
        
        Args:
            audio_chunk: Audio data as numpy array
        """
        if not self.is_active:
            return
        
        # Add to buffer
        for sample in audio_chunk.flatten():
            self.audio_buffer.append(sample)
    
    def _analysis_loop(self) -> None:
        """Main analysis loop running in separate thread."""
        while self.is_active and not self._stop_analysis.is_set():
            try:
                if len(self.audio_buffer) >= self.config.window_size:
                    # Extract window for analysis
                    window = np.array(list(self.audio_buffer)[-self.config.window_size:])
                    
                    # Perform analysis
                    self._analyze_window(window)
                
                # Sleep to control analysis rate
                time.sleep(0.01)  # 100Hz analysis rate
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                time.sleep(0.1)  # Longer sleep on error
    
    def _analyze_window(self, window: np.ndarray) -> None:
        """
        Analyze a window of audio data.
        
        Args:
            window: Audio window to analyze
        """
        rms_value = self._calculate_rms(window)
        spectral_value = self._calculate_spectral_energy(window)
        
        self.rms_history.append(rms_value)
        self.spectral_history.append(spectral_value)
        
        current_time = time.time()

        if self.is_learning:
            self._update_noise_floor(rms_value, spectral_value)
            if self.noise_samples >= self.min_noise_samples:
                self._finalize_noise_learning()
                self.is_learning = False  # Transition out of learning state
                self.silence_start_time = current_time
            return

        is_speech = self._detect_speech(rms_value, spectral_value, 0)

        if is_speech:
            self.silence_start_time = 0.0
            if not self.speech_detected:
                self.speech_detected = True
                self.last_speech_time = current_time
                if self.on_speech_detected:
                    try:
                        self.on_speech_detected()
                    except Exception as e:
                        self.logger.error(f"Error in speech detected callback: {e}")
        else:
            if self.silence_start_time == 0.0:
                self.silence_start_time = current_time

            if (current_time - self.silence_start_time) >= self.config.silence_duration:
                # A lock is needed here to prevent a race condition where the callback
                # is fired multiple times before the stream is stopped.
                with self._lock:
                    if not self.is_active:
                        return

                    self.logger.info(f"Silence threshold of {self.config.silence_duration}s reached.")
                    
                    # Mark as inactive immediately to prevent re-entry.
                    # The recorder will call stop() later, but this is a failsafe.
                    self.is_active = False
                    
                    if self.on_silence_detected:
                        try:
                            self.on_silence_detected()
                        except Exception as e:
                            self.logger.error(f"Error in silence detected callback: {e}")
    
    def _calculate_rms(self, window: np.ndarray) -> float:
        """Calculate RMS (Root Mean Square) of audio window."""
        return float(np.sqrt(np.mean(window ** 2)))
    
    def _calculate_spectral_energy(self, window: np.ndarray) -> float:
        """Calculate spectral energy of audio window."""
        # Apply window function to reduce spectral leakage
        windowed = window * np.hanning(len(window))
        
        # Compute FFT
        fft = np.fft.fft(windowed, n=self.config.fft_size)
        
        # Calculate power spectral density
        psd = np.abs(fft) ** 2
        
        # Focus on speech frequencies (80Hz - 8kHz)
        speech_band = psd[1:len(psd)//2]  # Skip DC and use only positive frequencies
        speech_band = speech_band[1:len(speech_band)//10]  # Focus on lower frequencies
        
        # Return average spectral energy in speech band
        return float(np.mean(speech_band))
    
    def _calculate_energy(self, window: np.ndarray) -> float:
        """Calculate total energy of audio window."""
        return float(np.sum(window ** 2) / len(window))
    
    def _update_noise_floor(self, rms_value: float, spectral_value: float) -> None:
        """Update the learned noise floor during learning phase."""
        self.noise_samples += 1
        
        # Use exponential moving average for adaptation
        alpha = self.config.adaptation_rate
        
        if self.noise_samples == 1:
            self.learned_noise_floor = rms_value
        else:
            self.learned_noise_floor = alpha * rms_value + (1 - alpha) * self.learned_noise_floor
        
        # Update adaptive threshold
        self.adaptive_threshold = self.learned_noise_floor * self.config.noise_margin
        
        # Log progress
        if self.noise_samples % 50 == 0:
            self.logger.debug(f"Learning noise floor: {self.learned_noise_floor:.6f} "
                            f"(samples: {self.noise_samples})")
    
    def _finalize_noise_learning(self) -> None:
        """Finalize noise learning and set adaptive threshold."""
        if self.noise_samples > 0:
            # Calculate final noise floor from history
            if len(self.rms_history) > 0:
                recent_rms = list(self.rms_history)[-min(50, len(self.rms_history)):]
                self.learned_noise_floor = float(np.percentile(recent_rms, 75))  # Use 75th percentile
            
            self.adaptive_threshold = self.learned_noise_floor * self.config.noise_margin
            
            self.logger.info(f"Noise learning completed: "
                           f"floor={self.learned_noise_floor:.6f}, "
                           f"threshold={self.adaptive_threshold:.6f}")
            
            # Notify noise learned
            if self.on_noise_learned:
                try:
                    self.on_noise_learned(self.learned_noise_floor)
                except Exception as e:
                    self.logger.error(f"Error in noise learned callback: {e}")
    
    def _detect_speech(self, rms_value: float, spectral_value: float, energy_value: float) -> bool:
        """
        Detect if audio contains speech using multiple strategies.
        
        Args:
            rms_value: RMS energy value
            spectral_value: Spectral energy value
            energy_value: Total energy value
            
        Returns:
            True if speech is detected, False if silence
        """
        if self.config.primary_strategy == DetectionStrategy.RMS:
            return bool(rms_value > self.config.rms_threshold)
        
        elif self.config.primary_strategy == DetectionStrategy.SPECTRAL:
            return bool(spectral_value > self.config.spectral_threshold)
        
        elif self.config.primary_strategy == DetectionStrategy.ADAPTIVE:
            if self.is_learning:
                # During learning, use a conservative threshold
                return bool(rms_value > self.config.rms_threshold * 2)
            else:
                return bool(rms_value > self.adaptive_threshold)
        
        elif self.config.primary_strategy == DetectionStrategy.HYBRID:
            # Combine multiple detection methods
            detections = []
            
            # RMS detection
            detections.append(bool(rms_value > self.config.rms_threshold))
            
            # Spectral detection
            if self.config.enable_spectral:
                detections.append(bool(spectral_value > self.config.spectral_threshold))
            
            # Energy detection
            detections.append(bool(energy_value > self.config.energy_threshold))
            
            # Adaptive detection
            if self.config.enable_adaptive and not self.is_learning:
                detections.append(bool(rms_value > self.adaptive_threshold))
            
            # Require majority of detections to be positive
            return sum(detections) >= max(1, len(detections) // 2)
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the silence detector."""
        with self._lock:
            return {
                'is_active': self.is_active,
                'is_learning': self.is_learning,
                'speech_detected': self.speech_detected,
                'learned_noise_floor': self.learned_noise_floor,
                'adaptive_threshold': self.adaptive_threshold,
                'noise_samples': self.noise_samples,
                'detection_count': self.detection_count,
                'false_positive_count': self.false_positive_count,
                'buffer_size': len(self.audio_buffer),
                'rms_history_size': len(self.rms_history),
                'spectral_history_size': len(self.spectral_history)
            }
    
    def reset(self) -> None:
        """Reset the silence detector state."""
        with self._lock:
            self.speech_detected = False
            self.silence_start_time = 0.0
            self.last_speech_time = 0.0
            self.audio_buffer.clear()
            self.rms_history.clear()
            self.spectral_history.clear()
            
            # Reset adaptive parameters
            self.learned_noise_floor = 0.0
            self.adaptive_threshold = 0.0
            self.noise_samples = 0
            
            self.logger.debug("Silence detector reset")
    
    def update_config(self, config: SilenceConfig) -> None:
        """Update the silence detection configuration."""
        with self._lock:
            self.config = config
            self.min_noise_samples = int(self.config.noise_learning_duration * 16000 / self.config.hop_size)
            self.logger.info("Silence detector configuration updated") 