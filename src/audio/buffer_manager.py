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
from typing import Optional, Callable, List, Tuple, Any
import logging
from pathlib import Path

from .device_config import AudioDeviceManager, AudioConfig


class AudioBuffer:
    """Manages a circular audio buffer for real-time processing."""
    
    def __init__(self, max_samples: int, channels: int = 1, dtype=np.float32):
        """
        Initialize audio buffer.
        
        Args:
            max_samples: Maximum number of samples to store
            channels: Number of audio channels
            dtype: Data type for audio samples
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
    
    def write(self, data: np.ndarray) -> None:
        """
        Write audio data to the buffer.
        
        Args:
            data: Audio data as numpy array
        """
        with self.lock:
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
            self.buffer.fill(0)
            self.write_index = 0
            self.read_index = 0
            self.samples_written = 0
    
    def get_fill_level(self) -> float:
        """
        Get the buffer fill level as a percentage.
        
        Returns:
            Fill level as percentage (0.0 to 1.0)
        """
        with self.lock:
            return min(self.samples_written / self.max_samples, 1.0)


class StreamingAudioManager:
    """Manages real-time streaming audio capture and buffer management."""
    
    def __init__(self, device_manager: AudioDeviceManager):
        """
        Initialize streaming audio manager.
        
        Args:
            device_manager: Audio device manager for configuration
        """
        self.logger = logging.getLogger("w4l.audio.streaming_manager")
        self.device_manager = device_manager
        self.config = device_manager.config
        
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
            dtype=np.float32
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
            self.processing_thread = threading.Thread(target=self._process_audio_data)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            self.logger.info(f"Started recording from {device.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self) -> None:
        """Stop recording audio."""
        try:
            self.is_recording = False
            
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            # Stop processing thread
            self.stop_processing.set()
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=1.0)
            
            self.logger.info("Stopped recording")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
    
    def _audio_callback(self, indata: np.ndarray, frames: int, 
                       time_info: dict, status: sd.CallbackFlags) -> None:
        """
        Callback for audio data from sounddevice.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Time information
            status: Status flags
        """
        if status:
            self.logger.warning(f"Audio callback status: {status}")
        
        # Put data in queue for processing
        try:
            self.audio_queue.put(indata.copy(), timeout=0.1)
        except queue.Full:
            self.logger.warning("Audio queue full, dropping data")
    
    def _process_audio_data(self) -> None:
        """Process audio data from the queue."""
        while not self.stop_processing.is_set():
            try:
                # Get audio data from queue
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # Write to buffer (ensure buffer exists)
                if self.buffer is not None:
                    self.buffer.write(audio_data)
                    
                    # Call audio data callback
                    if self.on_audio_data:
                        self.on_audio_data(audio_data)
                    
                    # Check if buffer is full enough for processing
                    if self.buffer.get_fill_level() >= 0.8:  # 80% full
                        if self.on_buffer_full:
                            latest_data = self.buffer.get_latest(
                                self.device_manager.get_buffer_size_samples()
                            )
                            self.on_buffer_full(latest_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audio data: {e}")
    
    def get_latest_audio(self, seconds: Optional[float] = None) -> np.ndarray:
        """
        Get the latest audio data.
        
        Args:
            seconds: Number of seconds to get (None for buffer size)
            
        Returns:
            Latest audio data as numpy array
        """
        if self.buffer is None:
            return np.array([])
            
        if seconds is None:
            samples = self.device_manager.get_buffer_size_samples()
        else:
            samples = int(seconds * self.config.sample_rate)
        
        return self.buffer.get_latest(samples)
    
    def set_buffer_size(self, seconds: float) -> None:
        """
        Set buffer size and recreate buffer.
        
        Args:
            seconds: Buffer size in seconds
        """
        self.device_manager.set_buffer_size(seconds)
        self._setup_buffer()
    
    def get_buffer_info(self) -> dict:
        """
        Get information about the current buffer.
        
        Returns:
            Dictionary with buffer information
        """
        if self.buffer is None:
            return {
                "fill_level": 0.0,
                "max_samples": 0,
                "samples_written": 0,
                "buffer_size_seconds": self.config.buffer_size_seconds,
                "is_recording": self.is_recording
            }
        
        return {
            "fill_level": self.buffer.get_fill_level(),
            "max_samples": self.buffer.max_samples,
            "samples_written": self.buffer.samples_written,
            "buffer_size_seconds": self.config.buffer_size_seconds,
            "is_recording": self.is_recording
        }


class FileBasedAudioManager:
    """Manages file-based audio capture as a fallback to streaming."""
    
    def __init__(self, device_manager: AudioDeviceManager):
        """
        Initialize file-based audio manager.
        
        Args:
            device_manager: Audio device manager for configuration
        """
        self.logger = logging.getLogger("w4l.audio.file_manager")
        self.device_manager = device_manager
        self.config = device_manager.config
        
        # File buffer
        self.buffer_file = Path(self.config.file_buffer_path)
        self.is_recording = False
        self.recording_thread = None
        self.stop_recording_event = threading.Event()
        
        # Callbacks
        self.on_file_ready: Optional[Callable[[str], None]] = None
    
    def start_recording(self) -> bool:
        """
        Start recording to file.
        
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
            
            # Start recording thread
            self.stop_recording_event.clear()
            self.recording_thread = threading.Thread(target=self._record_to_file)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            self.is_recording = True
            self.logger.info(f"Started file-based recording from {device.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start file recording: {e}")
            return False
    
    def stop_recording(self) -> None:
        """Stop recording to file."""
        try:
            self.is_recording = False
            self.stop_recording_event.set()
            
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
            
            self.logger.info("Stopped file-based recording")
            
        except Exception as e:
            self.logger.error(f"Error stopping file recording: {e}")
    
    def _record_to_file(self) -> None:
        """Record audio to file in chunks."""
        try:
            device = self.device_manager.get_current_device()
            if device is None:
                self.logger.error("No device available for recording")
                return
                
            buffer_samples = self.device_manager.get_buffer_size_samples()
            
            with sd.InputStream(
                device=device.device_id,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                dtype=np.int16,
                blocksize=buffer_samples
            ) as stream:
                
                while not self.stop_recording_event.is_set():
                    # Record one buffer worth of audio
                    audio_data, overflowed = stream.read(buffer_samples)
                    
                    if overflowed:
                        self.logger.warning("Audio buffer overflow")
                    
                    # Save to file
                    self._save_audio_chunk(audio_data)
                    
                    # Notify that file is ready
                    if self.on_file_ready:
                        self.on_file_ready(str(self.buffer_file))
                    
                    # Wait for buffer duration
                    time.sleep(self.config.buffer_size_seconds)
                    
        except Exception as e:
            self.logger.error(f"Error in file recording: {e}")
    
    def _save_audio_chunk(self, audio_data: np.ndarray) -> None:
        """
        Save audio chunk to file.
        
        Args:
            audio_data: Audio data to save
        """
        try:
            with wave.open(str(self.buffer_file), 'wb') as wav_file:
                wav_file.setnchannels(self.config.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.config.sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
        except Exception as e:
            self.logger.error(f"Error saving audio chunk: {e}")
    
    def get_audio_file(self) -> Optional[str]:
        """
        Get the path to the current audio file.
        
        Returns:
            Path to audio file if it exists, None otherwise
        """
        if self.buffer_file.exists():
            return str(self.buffer_file)
        return None
    
    def clear_buffer_file(self) -> None:
        """Clear the buffer file."""
        try:
            if self.buffer_file.exists():
                self.buffer_file.unlink()
                self.logger.info("Cleared buffer file")
        except Exception as e:
            self.logger.error(f"Error clearing buffer file: {e}")


class AudioBufferManager:
    """
    Main audio buffer manager that handles both streaming and file-based approaches.
    
    Automatically switches between modes based on configuration and provides
    a unified interface for audio capture and buffer management.
    """
    
    def __init__(self, device_manager: AudioDeviceManager):
        """
        Initialize audio buffer manager.
        
        Args:
            device_manager: Audio device manager for configuration
        """
        self.logger = logging.getLogger("w4l.audio.buffer_manager")
        self.device_manager = device_manager
        
        # Create managers for both approaches
        self.streaming_manager = StreamingAudioManager(device_manager)
        self.file_manager = FileBasedAudioManager(device_manager)
        
        # Callbacks (initialize before setting up active manager)
        self.on_audio_data: Optional[Callable[[np.ndarray], None]] = None
        self.on_buffer_ready: Optional[Callable[[Any], None]] = None
        
        # Current active manager
        self.active_manager = None
        self._setup_active_manager()
    
    def _setup_active_manager(self) -> None:
        """Setup the active manager based on configuration."""
        if self.device_manager.config.use_streaming:
            self.active_manager = self.streaming_manager
            self.streaming_manager.on_audio_data = self.on_audio_data
            self.streaming_manager.on_buffer_full = self.on_buffer_ready
        else:
            self.active_manager = self.file_manager
            self.file_manager.on_file_ready = self.on_buffer_ready
    
    def start_recording(self) -> bool:
        """
        Start recording using the active manager.
        
        Returns:
            True if recording started successfully, False otherwise
        """
        if self.active_manager is None:
            self.logger.error("No active manager available")
            return False
        return self.active_manager.start_recording()
    
    def stop_recording(self) -> None:
        """Stop recording."""
        if self.active_manager is not None:
            self.active_manager.stop_recording()
    
    def get_latest_audio(self, seconds: Optional[float] = None) -> np.ndarray:
        """
        Get the latest audio data (streaming mode only).
        
        Args:
            seconds: Number of seconds to get
            
        Returns:
            Latest audio data as numpy array
        """
        if isinstance(self.active_manager, StreamingAudioManager):
            return self.active_manager.get_latest_audio(seconds)
        else:
            return np.array([])
    
    def get_audio_file(self) -> Optional[str]:
        """
        Get the audio file path (file-based mode only).
        
        Returns:
            Path to audio file if available, None otherwise
        """
        if isinstance(self.active_manager, FileBasedAudioManager):
            return self.active_manager.get_audio_file()
        return None
    
    def set_capture_mode(self, use_streaming: bool) -> None:
        """
        Switch between streaming and file-based modes.
        
        Args:
            use_streaming: True for streaming mode, False for file-based
        """
        # Stop current recording
        if self.active_manager and self.active_manager.is_recording:
            self.active_manager.stop_recording()
        
        # Update configuration
        self.device_manager.set_capture_mode(use_streaming)
        
        # Setup new active manager
        self._setup_active_manager()
        
        self.logger.info(f"Switched to {'streaming' if use_streaming else 'file-based'} mode")
    
    def set_buffer_size(self, seconds: float) -> None:
        """
        Set buffer size for both managers.
        
        Args:
            seconds: Buffer size in seconds
        """
        self.device_manager.set_buffer_size(seconds)
        
        # Update streaming manager buffer
        if isinstance(self.active_manager, StreamingAudioManager):
            self.active_manager.set_buffer_size(seconds)
    
    def get_buffer_info(self) -> dict:
        """
        Get information about the current buffer.
        
        Returns:
            Dictionary with buffer information
        """
        info = {
            "mode": "streaming" if self.device_manager.config.use_streaming else "file-based",
            "buffer_size_seconds": self.device_manager.config.buffer_size_seconds,
            "is_recording": self.active_manager.is_recording if self.active_manager else False
        }
        
        if isinstance(self.active_manager, StreamingAudioManager):
            info.update(self.active_manager.get_buffer_info())
        
        return info
    
    def is_streaming_mode(self) -> bool:
        """
        Check if currently in streaming mode.
        
        Returns:
            True if in streaming mode, False if file-based
        """
        return isinstance(self.active_manager, StreamingAudioManager) 