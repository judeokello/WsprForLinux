"""
Audio buffer management for W4L.

Handles both streaming and file-based audio buffer management
with configurable buffer sizes for real-time transcription.
"""

import numpy as np
import sounddevice as sd
import wave
import threading
import time
import queue
import gc
import psutil
import os
from typing import Optional, Callable, List, Tuple, Any
import logging
from pathlib import Path
import weakref

from .device_config import AudioDeviceManager, AudioConfig
from .memory_manager import MemoryMonitor, ResourceManager, AudioBufferTracker


class AudioBuffer:
    """Manages a circular audio buffer for real-time processing."""
    
    def __init__(self, max_samples: int, channels: int = 1, dtype=np.float32, 
                 buffer_tracker: Optional[AudioBufferTracker] = None):
        """
        Initialize audio buffer.
        
        Args:
            max_samples: Maximum number of samples to store
            channels: Number of audio channels
            dtype: Data type for audio samples
            buffer_tracker: Optional buffer tracker for memory monitoring
        """
        self.max_samples = max_samples
        self.channels = channels
        self.dtype = dtype
        
        # Circular buffer
        self.buffer = np.zeros((max_samples, channels), dtype=dtype)
        self.write_index = 0
        self.read_index = 0
        self.samples_written = 0
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Memory tracking
        self._buffer_size_bytes = self.buffer.nbytes
        self.buffer_tracker = buffer_tracker
        self.logger = logging.getLogger("w4l.audio.buffer")
        
        # Track this buffer if tracker is provided
        if self.buffer_tracker:
            self.buffer_tracker.track_buffer(self, self._buffer_size_bytes)
        
        self.logger.debug(f"Created buffer with {self._buffer_size_bytes / 1024:.1f}KB")
    
    def write(self, data: np.ndarray) -> None:
        """
        Write audio data to the buffer.
        
        Args:
            data: Audio data as numpy array
        """
        with self.lock:
            if self.buffer is None:
                return
                
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            
            samples_to_write = len(data)
            
            # Write data in chunks if it wraps around the buffer
            remaining_space = self.max_samples - self.write_index
            if samples_to_write <= remaining_space:
                # All data fits in remaining space
                self.buffer[self.write_index:self.write_index + samples_to_write] = data
                self.write_index = (self.write_index + samples_to_write) % self.max_samples
            else:
                # Data wraps around the buffer
                self.buffer[self.write_index:] = data[:remaining_space]
                self.buffer[:samples_to_write - remaining_space] = data[remaining_space:]
                self.write_index = samples_to_write - remaining_space
            
            self.samples_written += samples_to_write
    
    def read(self, num_samples: int) -> np.ndarray:
        """
        Read audio data from the buffer.
        
        Args:
            num_samples: Number of samples to read
            
        Returns:
            Audio data as numpy array
        """
        with self.lock:
            if self.buffer is None:
                return np.array([])
                
            if self.samples_written < num_samples:
                # Not enough data available
                return np.array([])
            
            # Calculate read index
            read_start = (self.write_index - num_samples) % self.max_samples
            
            if read_start + num_samples <= self.max_samples:
                # Data is contiguous
                return self.buffer[read_start:read_start + num_samples].copy()
            else:
                # Data wraps around the buffer
                first_part = self.buffer[read_start:]
                second_part = self.buffer[:num_samples - len(first_part)]
                return np.vstack([first_part, second_part])
    
    def get_latest(self, num_samples: int) -> np.ndarray:
        """
        Get the latest audio data (most recent samples).
        
        Args:
            num_samples: Number of samples to get
            
        Returns:
            Latest audio data as numpy array
        """
        return self.read(num_samples)
    
    def clear(self) -> None:
        """Clear the buffer."""
        with self.lock:
            if self.buffer is not None:
                self.buffer.fill(0)
            self.write_index = 0
            self.read_index = 0
            self.samples_written = 0
            self.logger.debug("Buffer cleared")
    
    def get_fill_level(self) -> float:
        """
        Get the buffer fill level as a percentage.
        
        Returns:
            Fill level as percentage (0.0 to 1.0)
        """
        with self.lock:
            return min(self.samples_written / self.max_samples, 1.0)
    
    def cleanup(self) -> None:
        """Clean up buffer resources."""
        with self.lock:
            # Untrack from buffer tracker
            if self.buffer_tracker:
                self.buffer_tracker.untrack_buffer(self)
            
            self.buffer = None
            self.samples_written = 0
            self.logger.debug("Buffer resources cleaned up")


class StreamingAudioManager:
    """Manages real-time streaming audio capture and buffer management."""
    
    def __init__(self, device_manager: AudioDeviceManager, memory_monitor: Optional[MemoryMonitor] = None):
        """
        Initialize streaming audio manager.
        
        Args:
            device_manager: Audio device manager for configuration
            memory_monitor: Optional memory monitor for cleanup
        """
        self.logger = logging.getLogger("w4l.audio.streaming_manager")
        self.device_manager = device_manager
        self.config = device_manager.config
        self.memory_monitor = memory_monitor or MemoryMonitor()
        
        # Resource management
        self.resource_manager = ResourceManager(self.memory_monitor)
        self.buffer_tracker = AudioBufferTracker(self.memory_monitor)
        
        # Audio buffer
        self.buffer = None
        self._setup_buffer()
        
        # Streaming state
        self.is_recording = False
        self.stream = None
        self.audio_queue = queue.Queue()
        
        # Callbacks
        self.on_audio_data: Optional[Callable[[np.ndarray], None]] = None
        self.on_buffer_full: Optional[Callable[[np.ndarray], None]] = None
        
        # Thread for processing audio data
        self.processing_thread = None
        self.stop_processing = threading.Event()
    
    def _setup_buffer(self) -> None:
        """Setup the audio buffer based on current configuration."""
        buffer_samples = self.device_manager.get_buffer_size_samples()
        self.buffer = AudioBuffer(
            max_samples=buffer_samples,
            channels=self.config.channels,
            dtype=np.float32,
            buffer_tracker=self.buffer_tracker
        )
        self.logger.info(f"Setup buffer with {buffer_samples} samples")
    
    def start_recording(self) -> bool:
        """
        Start recording audio.
        
        Returns:
            True if recording started successfully, False otherwise
        """
        try:
            if self.is_recording:
                self.logger.warning("Already recording")
                return True
            
            # Get current device
            device = self.device_manager.get_current_device()
            if not device:
                self.logger.error("No valid audio device selected")
                return False
            
            # Setup stream
            self.stream = sd.InputStream(
                device=device.device_id,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=1024  # Small blocks for low latency
            )
            
            self.stream.start()
            self.is_recording = True
            
            # Start processing thread
            self.stop_processing.clear()
            self.processing_thread = threading.Thread(target=self._process_audio_data, daemon=True)
            self.processing_thread.start()
            
            self.logger.info("Started audio recording")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self._cleanup_resources()
            return False
    
    def stop_recording(self) -> None:
        """Stop recording audio."""
        try:
            self.is_recording = False
            self.stop_processing.set()
            
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
            
            self.logger.info("Stopped audio recording")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
        finally:
            # Clean up any temporary resources
            self.resource_manager.cleanup_temp_files()
    
    def _audio_callback(self, indata: np.ndarray, frames: int, 
                       time_info: dict, status: sd.CallbackFlags) -> None:
        """Callback for audio stream data."""
        if status:
            self.logger.warning(f"Audio callback status: {status}")
        
        if self.is_recording:
            # Put data in queue for processing
            try:
                self.audio_queue.put_nowait(indata.copy())
            except queue.Full:
                self.logger.warning("Audio queue full, dropping data")
    
    def _process_audio_data(self) -> None:
        """Process audio data from the queue."""
        while not self.stop_processing.is_set():
            try:
                # Get data with timeout
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # Write to buffer
                if self.buffer:
                    self.buffer.write(audio_data)
                    
                    # Call audio data callback
                    if self.on_audio_data:
                        self.on_audio_data(audio_data)
                    
                # Check memory usage periodically
                if self.memory_monitor.is_memory_high():
                    self.memory_monitor.cleanup()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audio data: {e}")
    
    def get_latest_audio(self, seconds: Optional[float] = None) -> np.ndarray:
        """
        Get the latest audio data.
        
        Args:
            seconds: Number of seconds to get (None for all available)
            
        Returns:
            Audio data as numpy array
        """
        if not self.buffer:
            return np.array([])
            
        if seconds is None:
            # Get all available data
            return self.buffer.get_latest(self.buffer.samples_written)
        else:
            # Get specific number of seconds
            samples = int(seconds * self.config.sample_rate)
        return self.buffer.get_latest(samples)
    
    def set_buffer_size(self, seconds: float) -> None:
        """
        Set buffer size in seconds.
        
        Args:
            seconds: Buffer size in seconds
        """
        buffer_samples = int(seconds * self.config.sample_rate)
        
        # Clean up old buffer
        if self.buffer:
            self.buffer.cleanup()
        
        # Create new buffer
        self.buffer = AudioBuffer(
            max_samples=buffer_samples,
            channels=self.config.channels,
            dtype=np.float32,
            buffer_tracker=self.buffer_tracker
        )
        
        self.logger.info(f"Buffer size set to {seconds} seconds ({buffer_samples} samples)")
    
    def get_buffer_info(self) -> dict:
        """
        Get buffer information.
        
        Returns:
            Dictionary with buffer information
        """
        info = {
            "max_samples": self.buffer.max_samples if self.buffer else 0,
            "samples_written": self.buffer.samples_written if self.buffer else 0,
            "fill_level": self.buffer.get_fill_level() if self.buffer else 0.0,
            "buffer_size_mb": self.buffer._buffer_size_bytes / 1024 / 1024 if self.buffer else 0.0,
            "memory_usage_mb": self.memory_monitor.get_memory_usage()
        }
        
        # Add buffer tracker info
        info.update(self.buffer_tracker.get_buffer_info())
        
        return info
    
    def _cleanup_resources(self) -> None:
        """Clean up resources to free memory."""
        try:
            # Clear audio queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Clear buffer if it's getting full
            if self.buffer and self.buffer.get_fill_level() > 0.8:
                self.buffer.clear()
            
            # Clean up resources
            self.resource_manager.cleanup()
            
            self.logger.debug("Resources cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")
    
    def cleanup(self) -> None:
        """Complete cleanup of all resources."""
        self.stop_recording()
        self._cleanup_resources()
        
        if self.buffer:
            self.buffer.cleanup()
            self.buffer = None
        
        self.resource_manager.cleanup()
        self.logger.info("Streaming audio manager cleaned up")


class FileBasedAudioManager:
    """Manages file-based audio recording and buffer management."""
    
    def __init__(self, device_manager: AudioDeviceManager, memory_monitor: Optional[MemoryMonitor] = None):
        """
        Initialize file-based audio manager.
        
        Args:
            device_manager: Audio device manager for configuration
            memory_monitor: Optional memory monitor for cleanup
        """
        self.logger = logging.getLogger("w4l.audio.file_manager")
        self.device_manager = device_manager
        self.config = device_manager.config
        self.memory_monitor = memory_monitor or MemoryMonitor()
        
        # Resource management
        self.resource_manager = ResourceManager(self.memory_monitor)
        
        # Recording state
        self.is_recording = False
        self.audio_file = None
        self.recording_thread = None
        self.stop_recording_event = threading.Event()
    
    def start_recording(self) -> bool:
        """
        Start recording audio to file.
        
        Returns:
            True if recording started successfully, False otherwise
        """
        try:
            if self.is_recording:
                self.logger.warning("Already recording")
                return True
            
            # Get current device
            device = self.device_manager.get_current_device()
            if not device:
                self.logger.error("No valid audio device selected")
                return False
            
            # Create temporary file
            import tempfile
            temp_fd, self.audio_file = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            self.resource_manager.add_temp_file(self.audio_file)
            
            # Start recording thread
            self.stop_recording_event.clear()
            self.recording_thread = threading.Thread(target=self._record_to_file, daemon=True)
            self.recording_thread.start()
            
            self.is_recording = True
            self.logger.info(f"Started recording to {self.audio_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self._cleanup_resources()
            return False
    
    def stop_recording(self) -> None:
        """Stop recording audio."""
        try:
            self.is_recording = False
            self.stop_recording_event.set()
            
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
            
            self.logger.info("Stopped audio recording")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
    
    def _record_to_file(self) -> None:
        """Record audio to file."""
        try:
            device = self.device_manager.get_current_device()
            if not device:
                self.logger.error("No valid audio device selected")
                return
            
            with sd.InputStream(
                device=device.device_id,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                dtype=np.float32,
                blocksize=1024
            ) as stream:
                
                if self.audio_file:
                    with wave.open(self.audio_file, 'wb') as wav_file:
                        wav_file.setnchannels(self.config.channels)
                        wav_file.setsampwidth(2)  # 16-bit
                        wav_file.setframerate(self.config.sample_rate)
                        
                        while self.is_recording and not self.stop_recording_event.is_set():
                            try:
                                audio_data, _ = stream.read(1024)
                                self._save_audio_chunk(audio_data, wav_file)
                    
                                # Check memory usage periodically
                                if self.memory_monitor.is_memory_high():
                                    self.memory_monitor.cleanup()
                                    
                            except Exception as e:
                                self.logger.error(f"Error reading audio: {e}")
                                break
                    
        except Exception as e:
            self.logger.error(f"Error in recording thread: {e}")
    
    def _save_audio_chunk(self, audio_data: np.ndarray, wav_file) -> None:
        """
        Save audio chunk to WAV file.
        
        Args:
            audio_data: Audio data to save
            wav_file: WAV file object
        """
        # Convert float32 to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())
    
    def get_audio_file(self) -> Optional[str]:
        """
        Get the path to the recorded audio file.
        
        Returns:
            Path to audio file or None if not available
        """
        if self.audio_file and os.path.exists(self.audio_file):
            return self.audio_file
        return None
    
    def clear_buffer_file(self) -> None:
        """Clear the buffer file."""
        if self.audio_file and os.path.exists(self.audio_file):
            try:
                os.remove(self.audio_file)
                self.resource_manager.remove_temp_file(self.audio_file)
                self.logger.debug(f"Removed buffer file: {self.audio_file}")
            except Exception as e:
                self.logger.warning(f"Could not remove buffer file: {e}")
        
        self.audio_file = None
    
    def get_latest_audio(self, seconds: Optional[float] = None) -> np.ndarray:
        """
        Get the latest audio data (file-based mode returns empty array).
        
        Args:
            seconds: Number of seconds to get (ignored in file-based mode)
            
        Returns:
            Empty array for file-based mode
        """
        # File-based mode doesn't provide real-time audio access
        return np.array([])
    
    def get_buffer_info(self) -> dict:
        """
        Get buffer information for file-based mode.
        
        Returns:
            Dictionary with buffer information
        """
        return {
            "mode": "file-based",
            "audio_file": self.audio_file,
            "is_recording": self.is_recording,
            "memory_usage_mb": self.memory_monitor.get_memory_usage(),
            "memory_limit_mb": self.memory_monitor.max_memory_mb
        }
    
    def _cleanup_resources(self) -> None:
        """Clean up resources to free memory."""
        try:
            self.resource_manager.cleanup()
            self.logger.debug("File-based resources cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")
    
    def cleanup(self) -> None:
        """Complete cleanup of all resources."""
        self.stop_recording()
        self._cleanup_resources()
        self.clear_buffer_file()
        self.logger.info("File-based audio manager cleaned up")


class AudioBufferManager:
    """Main audio buffer manager that coordinates streaming and file-based modes."""
    
    def __init__(self, device_manager: AudioDeviceManager, memory_monitor: Optional[MemoryMonitor] = None):
        """
        Initialize audio buffer manager.
        
        Args:
            device_manager: Audio device manager for configuration
            memory_monitor: Optional memory monitor for cleanup
        """
        self.logger = logging.getLogger("w4l.audio.buffer_manager")
        self.device_manager = device_manager
        self.memory_monitor = memory_monitor or MemoryMonitor()
        
        # Audio managers
        self.streaming_manager = None
        self.file_manager = None
        self.active_manager = None
        
        # Mode configuration
        self.use_streaming = True
        
        self._setup_active_manager()
    
    def _setup_active_manager(self) -> None:
        """Setup the active audio manager based on current mode."""
        if self.use_streaming:
            if not self.streaming_manager:
                self.streaming_manager = StreamingAudioManager(self.device_manager, self.memory_monitor)
            self.active_manager = self.streaming_manager
        else:
            if not self.file_manager:
                self.file_manager = FileBasedAudioManager(self.device_manager, self.memory_monitor)
            self.active_manager = self.file_manager
    
    def start_recording(self) -> bool:
        """
        Start recording audio.
        
        Returns:
            True if recording started successfully, False otherwise
        """
        if not self.active_manager:
            self._setup_active_manager()
        
        if self.active_manager:
            return self.active_manager.start_recording()
        return False
    
    def stop_recording(self) -> None:
        """Stop recording audio."""
        if self.active_manager:
            self.active_manager.stop_recording()
    
    def get_latest_audio(self, seconds: Optional[float] = None) -> np.ndarray:
        """
        Get the latest audio data.
        
        Args:
            seconds: Number of seconds to get (None for all available)
            
        Returns:
            Audio data as numpy array
        """
        if not self.active_manager:
            return np.array([])
        
        if hasattr(self.active_manager, 'get_latest_audio'):
            return self.active_manager.get_latest_audio(seconds)
        
        return np.array([])
    
    def get_audio_file(self) -> Optional[str]:
        """
        Get the path to the recorded audio file (file-based mode only).
        
        Returns:
            Path to audio file or None if not available
        """
        if self.file_manager:
            return self.file_manager.get_audio_file()
        return None
    
    def set_capture_mode(self, use_streaming: bool) -> None:
        """
        Set the capture mode.
        
        Args:
            use_streaming: True for streaming mode, False for file-based mode
        """
        if self.use_streaming != use_streaming:
            # Stop current recording if active
            if self.active_manager and hasattr(self.active_manager, 'is_recording'):
                if self.active_manager.is_recording:
                    self.active_manager.stop_recording()
        
            self.use_streaming = use_streaming
        self._setup_active_manager()
        
        self.logger.info(f"Switched to {'streaming' if use_streaming else 'file-based'} mode")
    
    def set_buffer_size(self, seconds: float) -> None:
        """
        Set buffer size in seconds (streaming mode only).
        
        Args:
            seconds: Buffer size in seconds
        """
        if self.streaming_manager:
            self.streaming_manager.set_buffer_size(seconds)
    
    def get_buffer_info(self) -> dict:
        """
        Get buffer information.
        
        Returns:
            Dictionary with buffer information
        """
        info = {
            "mode": "streaming" if self.use_streaming else "file-based",
            "memory_usage_mb": self.memory_monitor.get_memory_usage(),
            "memory_limit_mb": self.memory_monitor.max_memory_mb
        }
        
        if self.active_manager and hasattr(self.active_manager, 'get_buffer_info'):
            info.update(self.active_manager.get_buffer_info())
        
        return info
    
    def is_streaming_mode(self) -> bool:
        """
        Check if currently in streaming mode.
        
        Returns:
            True if in streaming mode
        """
        return self.use_streaming
    
    def cleanup(self) -> None:
        """Complete cleanup of all resources."""
        self.logger.info("Starting audio buffer manager cleanup")
        
        # Stop recording if active
        if self.active_manager and hasattr(self.active_manager, 'is_recording'):
            if self.active_manager.is_recording:
                self.active_manager.stop_recording()
        
        # Clean up managers
        if self.streaming_manager:
            self.streaming_manager.cleanup()
            self.streaming_manager = None
        
        if self.file_manager:
            self.file_manager.cleanup()
            self.file_manager = None
        
        self.active_manager = None
        
        # Force memory cleanup
        self.memory_monitor.cleanup(force=True)
        
        self.logger.info("Audio buffer manager cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass 