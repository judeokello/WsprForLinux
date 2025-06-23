#!/usr/bin/env python3
"""
Handles real-time audio recording using sounddevice with robust error recovery.
"""

import sounddevice as sd
import numpy as np
import logging
import time
import threading
from typing import Optional, Callable, Dict, Any
from enum import Enum

from .silence_detector import SilenceDetector, SilenceConfig, DetectionStrategy

class StreamStatus(Enum):
    """Audio stream status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RECOVERING = "recovering"

class StreamError(Exception):
    """Custom exception for stream-related errors."""
    pass

class AudioRecorder:
    """
    Manages the audio recording stream from an input device with robust error recovery.

    This class provides a simple interface to start and stop recording and
    invokes a callback with chunks of audio data as they become available.
    Includes comprehensive error handling and automatic recovery mechanisms.
    Now includes integrated silence detection with background noise handling.
    """
    
    def __init__(self, device_id: Optional[int], sample_rate: int = 16000, channels: int = 1, blocksize: int = 1024, silence_config: Optional[SilenceConfig] = None):
        """
        Initialize the AudioRecorder.

        Args:
            device_id (Optional[int]): The ID of the audio device to use. If None, the default device is used.
            sample_rate (int): The sample rate in Hz.
            channels (int): The number of channels.
            blocksize (int): The number of frames per audio block (chunk size).
            silence_config (Optional[SilenceConfig]): Configuration for silence detection.
        """
        self.logger = logging.getLogger("w4l.audio.recorder")
        
        # Use default device if None is provided
        self.device_id = device_id if device_id is not None else sd.default.device[0]
        
        self.sample_rate = sample_rate
        self.channels = channels
        self.blocksize = blocksize
        
        # Stream management
        self.stream: Optional[sd.InputStream] = None
        self.status = StreamStatus.STOPPED
        
        # Error recovery configuration
        self.max_retry_attempts = 5
        self.base_retry_delay = 1.0  # seconds
        self.max_retry_delay = 30.0  # seconds
        self.retry_attempts = 0
        self.last_error_time = 0.0
        
        # Stream health monitoring
        self.stream_start_time = 0.0
        self.total_samples_processed = 0
        self.error_count = 0
        self.underrun_count = 0
        self.overrun_count = 0
        
        # Thread safety
        self._lock = threading.Lock()
        self._recovery_thread: Optional[threading.Thread] = None
        self._stop_recovery = threading.Event()
        
        # This callback will be invoked with new audio chunks
        self.audio_chunk_callback: Optional[Callable[[np.ndarray], None]] = None
        
        # Error callbacks
        self.on_stream_error: Optional[Callable[[Exception], None]] = None
        self.on_stream_recovered: Optional[Callable[[], None]] = None
        self.on_stream_health_update: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Silence detection
        self.silence_detector = SilenceDetector(silence_config)
        self.silence_detector.on_silence_detected = self._on_silence_detected
        self.silence_detector.on_speech_detected = self._on_speech_detected
        self.silence_detector.on_noise_learned = self._on_noise_learned
        
        # Silence detection callbacks
        self.on_silence_detected: Optional[Callable[[], None]] = None
        self.on_speech_detected: Optional[Callable[[], None]] = None
        self.on_noise_learned: Optional[Callable[[float], None]] = None
        
        # Recording state
        self.is_recording = False

    def _stream_callback(self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags):
        """
        This is called (from a separate thread) for each audio block from the stream.
        Includes comprehensive error handling and health monitoring.
        """
        try:
            # Update health metrics
            self.total_samples_processed += frames
            
            # Handle stream status flags
            if status:
                self._handle_stream_status(status, frames)
            
            # Process audio data if callback is available
            if self.audio_chunk_callback and self.status == StreamStatus.RUNNING:
                try:
                    # Pass a copy of the audio data to the callback
                    self.audio_chunk_callback(indata.copy())
                except Exception as e:
                    self.logger.error(f"Error in audio chunk callback: {e}")
                    self._handle_callback_error(e)
            
            # Feed audio data to silence detector
            if self.status == StreamStatus.RUNNING and self.silence_detector.is_active:
                try:
                    # Convert int16 to float32 for silence detection
                    audio_float = indata.astype(np.float32) / 32767.0
                    self.silence_detector.add_audio_data(audio_float)
                except Exception as e:
                    self.logger.error(f"Error feeding audio to silence detector: {e}")
            
        except Exception as e:
            self.logger.error(f"Critical error in stream callback: {e}")
            self._handle_critical_error(e)

    def _handle_stream_status(self, status: sd.CallbackFlags, frames: int):
        """Handle stream status flags and update health metrics."""
        if status.input_underflow:
            self.underrun_count += 1
            self.logger.warning(f"Input underflow detected (frame {frames})")
            
        if status.input_overflow:
            self.overrun_count += 1
            self.logger.warning(f"Input overflow detected (frame {frames})")
            
        # Log periodic health updates
        if self.total_samples_processed % (self.sample_rate * 10) == 0:  # Every 10 seconds
            self._report_health_status()

    def _handle_stream_closure(self):
        """Handle unexpected stream closure."""
        with self._lock:
            if self.status == StreamStatus.RUNNING:
                self.status = StreamStatus.ERROR
                self.logger.error("Stream unexpectedly closed")
                self._schedule_recovery()

    def _handle_callback_error(self, error: Exception):
        """Handle errors in the audio chunk callback."""
        self.error_count += 1
        self.logger.error(f"Audio callback error (count: {self.error_count}): {error}")
        
        # If we have too many callback errors, consider stream unhealthy
        if self.error_count > 10:
            self.logger.error("Too many callback errors, marking stream as unhealthy")
            self._schedule_recovery()

    def _handle_critical_error(self, error: Exception):
        """Handle critical errors that require immediate recovery."""
        with self._lock:
            self.status = StreamStatus.ERROR
            self.error_count += 1
            self.last_error_time = time.time()
            
        self.logger.error(f"Critical stream error: {error}")
        
        # Notify error callback
        if self.on_stream_error:
            try:
                self.on_stream_error(error)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
        
        # Schedule recovery
        self._schedule_recovery()

    def _schedule_recovery(self):
        """Schedule automatic stream recovery."""
        if self._recovery_thread and self._recovery_thread.is_alive():
            return  # Recovery already in progress
            
        self._stop_recovery.clear()
        self._recovery_thread = threading.Thread(target=self._recovery_worker, daemon=True)
        self._recovery_thread.start()

    def _recovery_worker(self):
        """Worker thread for handling stream recovery with exponential backoff."""
        while not self._stop_recovery.is_set():
            try:
                with self._lock:
                    if self.status != StreamStatus.ERROR:
                        break
                    
                    self.status = StreamStatus.RECOVERING
                    self.retry_attempts += 1
                
                self.logger.info(f"Attempting stream recovery (attempt {self.retry_attempts}/{self.max_retry_attempts})")
                
                # Calculate delay with exponential backoff
                delay = min(self.base_retry_delay * (2 ** (self.retry_attempts - 1)), self.max_retry_delay)
                time.sleep(delay)
                
                # Attempt to restart the stream
                if self._attempt_stream_restart():
                    self.logger.info("Stream recovery successful")
                    break
                else:
                    self.logger.warning(f"Stream recovery attempt {self.retry_attempts} failed")
                    
                    if self.retry_attempts >= self.max_retry_attempts:
                        self.logger.error("Maximum recovery attempts reached, giving up")
                        with self._lock:
                            self.status = StreamStatus.ERROR
                        break
                        
            except Exception as e:
                self.logger.error(f"Error during recovery: {e}")
                time.sleep(self.base_retry_delay)

    def _attempt_stream_restart(self) -> bool:
        """Attempt to restart the audio stream."""
        try:
            # Clean up existing stream
            self._cleanup_stream()
            
            # Create new stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                device=self.device_id,
                channels=self.channels,
                dtype='int16',  # 16-bit audio, standard for Whisper
                blocksize=self.blocksize,
                callback=self._stream_callback
            )
            
            # Start the stream
            self.stream.start()
            
            with self._lock:
                self.status = StreamStatus.RUNNING
                self.stream_start_time = time.time()
                self.retry_attempts = 0  # Reset retry counter on success
            
            self.logger.info("Stream restarted successfully")
            
            # Notify recovery callback
            if self.on_stream_recovered:
                try:
                    self.on_stream_recovered()
                except Exception as e:
                    self.logger.error(f"Error in recovery callback: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restart stream: {e}")
            with self._lock:
                self.status = StreamStatus.ERROR
            return False

    def _cleanup_stream(self):
        """Clean up the current stream safely."""
        if self.stream:
            try:
                if self.stream.active:
                    self.stream.stop()
                self.stream.close()
            except Exception as e:
                self.logger.warning(f"Error during stream cleanup: {e}")
            finally:
                self.stream = None

    def _report_health_status(self):
        """Report stream health status."""
        uptime = time.time() - self.stream_start_time if self.stream_start_time > 0 else 0
        
        health_data = {
            'status': self.status.value,
            'uptime_seconds': uptime,
            'total_samples_processed': self.total_samples_processed,
            'error_count': self.error_count,
            'underrun_count': self.underrun_count,
            'overrun_count': self.overrun_count,
            'retry_attempts': self.retry_attempts,
            'device_id': self.device_id,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'blocksize': self.blocksize
        }
        
        self.logger.debug(f"Stream health: {health_data}")
        
        # Notify health callback
        if self.on_stream_health_update:
            try:
                self.on_stream_health_update(health_data)
            except Exception as e:
                self.logger.error(f"Error in health callback: {e}")

    def start(self):
        """Start the audio recording stream with error recovery."""
        with self._lock:
            if self.status in [StreamStatus.RUNNING, StreamStatus.STARTING]:
                self.logger.warning("Recorder is already running or starting.")
                return

            self.status = StreamStatus.STARTING

        self.logger.info(f"Starting audio stream on device {self.device_id} with {self.sample_rate}Hz, {self.channels} channels.")
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                device=self.device_id,
                channels=self.channels,
                dtype='int16',  # 16-bit audio, standard for Whisper
                blocksize=self.blocksize,  # Fixed chunk size for consistent updates
                callback=self._stream_callback
            )
            self.stream.start()
            
            with self._lock:
                self.status = StreamStatus.RUNNING
                self.stream_start_time = time.time()
                self.retry_attempts = 0
                self.error_count = 0
                self.underrun_count = 0
                self.overrun_count = 0
                self.total_samples_processed = 0
                self.is_recording = True
            
            # Start silence detection
            self.silence_detector.start()
            
            self.logger.info("Audio stream started successfully.")
            
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {e}")
            with self._lock:
                self.status = StreamStatus.ERROR
                self.is_recording = False
            self.stream = None
            raise StreamError(f"Failed to start audio stream: {e}")

    def stop(self):
        """Stop the audio recording stream and cleanup resources."""
        with self._lock:
            if self.status == StreamStatus.STOPPED:
                self.logger.warning("Recorder is not running.")
                return

            # Signal recovery thread to stop
            self._stop_recovery.set()
            self.status = StreamStatus.STOPPED
            self.is_recording = False

        # Stop silence detection
        self.silence_detector.stop()

        # Wait for recovery thread to finish
        if self._recovery_thread and self._recovery_thread.is_alive():
            self._recovery_thread.join(timeout=2.0)

        try:
            self._cleanup_stream()
            self.logger.info("Audio stream stopped successfully.")
        except Exception as e:
            self.logger.error(f"Failed to stop audio stream cleanly: {e}")

    def get_status(self) -> StreamStatus:
        """Get the current stream status."""
        with self._lock:
            return self.status

    def get_health_info(self) -> Dict[str, Any]:
        """Get comprehensive health information about the stream."""
        with self._lock:
            uptime = time.time() - self.stream_start_time if self.stream_start_time > 0 else 0
            
            return {
                'status': self.status.value,
                'uptime_seconds': uptime,
                'total_samples_processed': self.total_samples_processed,
                'error_count': self.error_count,
                'underrun_count': self.underrun_count,
                'overrun_count': self.overrun_count,
                'retry_attempts': self.retry_attempts,
                'last_error_time': self.last_error_time,
                'device_id': self.device_id,
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'blocksize': self.blocksize,
                'is_stream_active': self.stream.active if self.stream else False
            }

    def is_healthy(self) -> bool:
        """Check if the stream is in a healthy state."""
        with self._lock:
            if self.status != StreamStatus.RUNNING:
                return False
            
            # Consider stream unhealthy if too many errors
            if self.error_count > 20:
                return False
            
            # Consider stream unhealthy if too many underruns/overruns
            if self.underrun_count > 50 or self.overrun_count > 50:
                return False
            
            return True

    def force_recovery(self):
        """Force a recovery attempt even if not in error state."""
        with self._lock:
            if self.status == StreamStatus.ERROR:
                self._schedule_recovery()
    
    # Silence detection methods
    def start_silence_detection(self) -> None:
        """Start silence detection."""
        if self.is_recording:
            self.silence_detector.start()
            self.logger.info("Silence detection started")
    
    def stop_silence_detection(self) -> None:
        """Stop silence detection."""
        self.silence_detector.stop()
        self.logger.info("Silence detection stopped")
    
    def reset_silence_detection(self) -> None:
        """Reset silence detection state."""
        self.silence_detector.reset()
        self.logger.debug("Silence detection reset")
    
    def update_silence_config(self, config: SilenceConfig) -> None:
        """Update silence detection configuration."""
        self.silence_detector.update_config(config)
        self.logger.info("Silence detection configuration updated")
    
    def get_silence_status(self) -> Dict[str, Any]:
        """Get silence detection status."""
        return self.silence_detector.get_status()
    
    def set_silence_callbacks(self, 
                            on_silence_detected: Optional[Callable[[], None]] = None,
                            on_speech_detected: Optional[Callable[[], None]] = None,
                            on_noise_learned: Optional[Callable[[float], None]] = None) -> None:
        """
        Set silence detection callbacks.
        
        Args:
            on_silence_detected: Callback when silence is detected
            on_speech_detected: Callback when speech is detected
            on_noise_learned: Callback when noise floor is learned
        """
        self.on_silence_detected = on_silence_detected
        self.on_speech_detected = on_speech_detected
        self.on_noise_learned = on_noise_learned
        self.logger.debug("Silence detection callbacks updated")
    
    def _on_silence_detected(self):
        """
        Internal handler for when silence is detected by the SilenceDetector.
        This method stops the recording and invokes the public callback if it's set.
        """
        self.logger.info("Silence detected by SilenceDetector.")
        
        if self.is_recording:
            self.logger.info("Stopping recording due to detected silence.")
            self.stop()
        
        if self.on_silence_detected:
            try:
                self.on_silence_detected()
            except Exception as e:
                self.logger.error(f"Error in on_silence_detected callback: {e}")
    
    def _on_speech_detected(self):
        """Internal callback for speech detection."""
        self.logger.info("Speech detected")
        
        # Forward to external callback
        if self.on_speech_detected:
            try:
                self.on_speech_detected()
            except Exception as e:
                self.logger.error(f"Error in speech detected callback: {e}")
    
    def _on_noise_learned(self, noise_level: float):
        """Internal callback for noise learning."""
        self.logger.info(f"Noise level learned: {noise_level}")
        
        # Forward to external callback
        if self.on_noise_learned:
            try:
                self.on_noise_learned(noise_level)
            except Exception as e:
                self.logger.error(f"Error in noise learned callback: {e}") 
    
    def get_audio_buffer(self) -> Optional[np.ndarray]:
        """
        Get the current audio buffer for transcription.
        
        Returns:
            Audio data as numpy array, or None if no data available
        """
        try:
            # Get audio buffer from silence detector
            if hasattr(self.silence_detector, 'audio_buffer') and self.silence_detector.audio_buffer:
                # Convert deque to numpy array
                audio_data = np.array(list(self.silence_detector.audio_buffer))
                if len(audio_data) > 0:
                    self.logger.debug(f"Retrieved audio buffer with {len(audio_data)} samples")
                    return audio_data
                else:
                    self.logger.debug("Audio buffer is empty")
                    return None
            else:
                self.logger.debug("No audio buffer available")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting audio buffer: {e}")
            return None
    
    def clear_audio_buffer(self) -> None:
        """Clear the audio buffer."""
        try:
            if hasattr(self.silence_detector, 'audio_buffer'):
                self.silence_detector.audio_buffer.clear()
                self.logger.debug("Audio buffer cleared")
        except Exception as e:
            self.logger.error(f"Error clearing audio buffer: {e}") 